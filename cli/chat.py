"""`acc chat` — interactive multi-turn chat session."""

import asyncio
import os
import click
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from acc_core.config import get
from acc_core.adb import AdbDevice, AdbClient
from acc_core.claude import ConversationHistory
from acc_core.providers import create_provider
from acc_core.agent import AgentLoop, AgentCallbacks
from cli.display import console, session_banner, tool_call_panel, agent_result_panel
from cli.session_store import create_session, load_session, save_session


HELP_TEXT = """
[bold]Chat commands:[/]
  /help          Show this help
  /screenshot    Toggle to vision mode for next step
  /text          Switch to text-only mode
  /auto          Switch to auto mode
  /device        Show device info
  /sessions      List saved sessions
  /resume <id>   Resume a previous session
  /save          Save current session
  /exit, /quit   Exit chat
"""


class RichChatCallbacks(AgentCallbacks):
    async def on_step_start(self, step: int):
        console.print(f"  [dim]🔍 [Step {step}] Observing...[/]")

    async def on_tool_call(self, tool_name: str, tool_input: dict):
        import json
        console.print(f"  [green]▶️  {tool_name}[/] [dim]{json.dumps(tool_input, default=str)[:120]}[/]")

    async def on_tool_result(self, tool_name: str, result: dict):
        if tool_name == "task_complete":
            return
        if result.get("success"):
            console.print("  [green]✅ OK[/]")
        else:
            console.print(f"  [red]❌ {result.get('error', '')}[/]")

    async def on_assistant_message(self, text: str):
        console.print(f"  [cyan]🤖 Claude:[/] {text[:500]}")

    async def request_confirmation(self, tool_name: str, tool_input: dict,
                                   risk_level: str, reason: str) -> bool:
        import json
        console.print(f"  [bold red]⚠️  {risk_level.upper()} — {reason}[/]")
        console.print(f"  [dim]{json.dumps(tool_input, default=str)[:200]}[/]")
        return click.confirm("  Proceed?", default=False)

    async def on_task_complete(self, success: bool, summary: str, steps: int):
        icon = "🎉" if success else "❌"
        console.print(f"  {icon} [bold]{summary}[/] (in {steps} steps)")


@click.command()
@click.option("--device", "-d", "serial", help="Target device serial")
@click.option("--mode", "-m", default="auto", type=click.Choice(["auto", "vision", "text"]))
@click.option("--resume", "session_id", help="Resume a previous session ID")
@click.pass_context
def chat_cmd(ctx, serial, mode, session_id):
    """Start an interactive chat session to control an Android device."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        console.print("[bold red]No API key set.[/] Export ANTHROPIC_API_KEY or DEEPSEEK_API_KEY.")
        raise SystemExit(1)

    # Device selection
    client = AdbClient()
    devices = client.devices()
    if not devices:
        console.print("[bold red]No ADB devices found.[/]")
        raise SystemExit(1)

    if serial:
        target = next((d for d in devices if d["serial"] == serial), None)
    elif len(devices) == 1:
        target = devices[0]
    else:
        console.print("Multiple devices. Use -d to pick one:")
        for d in devices:
            console.print(f"  {d['serial']}")
        raise SystemExit(1)

    if not target:
        console.print(f"[bold red]Device {serial} not found.[/]")
        raise SystemExit(1)

    serial = target["serial"]

    # Resume or create session
    if session_id:
        sess = load_session(session_id)
        if not sess:
            console.print(f"[bold red]Session {session_id} not found.[/]")
            raise SystemExit(1)
        mode = sess.get("mode", mode)
        console.print(f"Resumed session: {sess['title'][:80]}")
    else:
        session_id = create_session(serial, mode=mode)

    adb = AdbDevice(serial)
    provider = create_provider()
    loop = AgentLoop()
    conversation = ConversationHistory()

    console.print(session_banner(session_id, serial, mode))
    console.print("[dim]Type /help for commands, or just describe what you want to do.[/]")
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold green]👤 You[/]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting...[/]")
            break

        if not user_input.strip():
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd in ("/exit", "/quit"):
                break
            elif cmd == "/help":
                console.print(HELP_TEXT)
                continue
            elif cmd == "/screenshot":
                mode = "vision"
                console.print("[dim]Switched to vision mode for next step.[/]")
                continue
            elif cmd == "/text":
                mode = "text"
                console.print("[dim]Switched to text-only mode.[/]")
                continue
            elif cmd == "/auto":
                mode = "auto"
                console.print("[dim]Switched to auto mode.[/]")
                continue
            elif cmd == "/device":
                info = adb.device.summary()
                console.print(Panel(str(info)[:500], title="Device Info"))
                continue
            elif cmd == "/save":
                save_session(session_id, {
                    "id": session_id, "title": "Chat session",
                    "device_serial": serial, "mode": mode,
                    "status": "active", "steps": 0,
                })
                console.print(f"[dim]Session {session_id[:8]} saved.[/]")
                continue
            else:
                console.print(f"[dim]Unknown command: {cmd}. /help for list.[/]")
                continue

        # Run goal
        async def run_goal():
            callbacks = RichChatCallbacks()
            result = await loop.run(
                goal=user_input,
                adb=adb,
                provider=provider,
                conversation=conversation,
                mode=mode,
                callbacks=callbacks,
                safe_mode=get("safe_mode"),
            )
            return result

        result = asyncio.run(run_goal())
        if result.summary:
            console.print(agent_result_panel(result.success, result.summary, result.steps))
        console.print()

    # Save on exit
    console.print(f"[dim]Session saved: {session_id[:8]}[/]")
