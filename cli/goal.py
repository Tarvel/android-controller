"""`acc goal` — single-shot goal execution."""

import asyncio
import os
import click
from rich.live import Live
from rich.panel import Panel

from acc_core.config import get
from acc_core.adb import AdbDevice, AdbClient
from acc_core.claude import ConversationHistory
from acc_core.providers import create_provider
from acc_core.agent import AgentLoop, AgentCallbacks, RiskLevel
from cli.display import console, agent_result_panel, tool_call_panel


class RichGoalCallbacks(AgentCallbacks):
    def __init__(self, live: Live):
        self.live = live

    async def on_step_start(self, step: int):
        self.live.update(Panel(f"Thinking...", title=f"Step {step}", border_style="blue"))

    async def on_tool_call(self, tool_name: str, tool_input: dict):
        self.live.update(tool_call_panel(tool_name, tool_input))

    async def on_tool_result(self, tool_name: str, result: dict):
        if result.get("success"):
            self.live.update(Panel(f"OK — {tool_name}", border_style="green"))
        else:
            self.live.update(Panel(f"Failed — {tool_name}: {result.get('error', '')}", border_style="red"))

    async def on_assistant_message(self, text: str):
        self.live.update(Panel(text[:500], title="Claude", border_style="cyan"))

    async def request_confirmation(self, tool_name: str, tool_input: dict,
                                   risk_level: str, reason: str) -> bool:
        import json
        self.live.stop()
        console.print(f"[bold red]⚠️  {risk_level.upper()} RISK:[/] {reason}")
        console.print(f"Tool: {tool_name} — {json.dumps(tool_input, default=str)[:300]}")
        result = click.confirm("Proceed?", default=False)
        self.live.start()
        return result

    async def on_error(self, error: Exception):
        self.live.update(Panel(str(error), title="Error", border_style="red"))


@click.command()
@click.argument("goal_text")
@click.option("--device", "-d", "serial", help="Target device serial")
@click.option("--mode", "-m", default="auto", type=click.Choice(["auto", "vision", "text"]))
@click.option("--max-steps", "-s", default=None, type=int, help="Max agent steps")
@click.option("--safe/--unsafe", default=None, help="Require/skip confirmations")
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def goal_cmd(ctx, goal_text, serial, mode, max_steps, safe, verbose):
    """Execute a GOAL on an Android device using Claude AI.

    Example: acc goal "open Chrome and search for weather"
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        console.print("[bold red]No API key set.[/] Export ANTHROPIC_API_KEY or DEEPSEEK_API_KEY, or add to .env.")
        raise SystemExit(1)

    # Device selection
    client = AdbClient()
    devices = client.devices()
    if not devices:
        console.print("[bold red]No ADB devices found.[/] Connect a device or start ADB.")
        raise SystemExit(1)

    if serial:
        target = next((d for d in devices if d["serial"] == serial), None)
        if not target:
            console.print(f"[bold red]Device {serial} not found.[/]")
            raise SystemExit(1)
    elif len(devices) == 1:
        target = devices[0]
    else:
        console.print("Multiple devices found. Use -d to specify one:")
        for d in devices:
            console.print(f"  {d['serial']} ({d.get('state', '?')})")
        raise SystemExit(1)

    serial = target["serial"]
    console.print(f"Device: {serial} ({target.get('state', '?')})")

    adb = AdbDevice(serial)
    provider = create_provider()

    loop = AgentLoop()
    max_s = max_steps or get("max_steps")
    safe_m = safe if safe is not None else get("safe_mode")

    console.print(f"Goal: {goal_text}")
    console.print(f"Mode: {mode} | Max steps: {max_s} | Safe: {safe_m}")

    async def run():
        with Live(Panel("Starting..."), console=console, refresh_per_second=4) as live:
            callbacks = RichGoalCallbacks(live)
            result = await loop.run(
                goal=goal_text,
                adb=adb,
                provider=provider,
                mode=mode,
                max_steps=max_s,
                safe_mode=safe_m,
                callbacks=callbacks,
            )
        console.print(agent_result_panel(result.success, result.summary, result.steps))
        return result

    asyncio.run(run())
