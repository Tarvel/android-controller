"""Rich display helpers for CLI output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich import box

console = Console()


def device_table(devices: list[dict]) -> Table:
    table = Table(title="Connected Devices", box=box.ROUNDED)
    table.add_column("Serial", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("State", style="yellow")
    table.add_column("Android")
    for d in devices:
        table.add_row(
            d.get("serial", "?"),
            d.get("model", "?"),
            d.get("state", "?"),
            d.get("android", "?"),
        )
    return table


def step_header(step: int, max_steps: int, device: str, mode: str) -> Panel:
    title = f"Step {step}/{max_steps}  |  Device: {device}  |  Mode: {mode}"
    return Panel("", title=title, border_style="blue")


def tool_call_panel(name: str, params: dict) -> Panel:
    from rich.syntax import Syntax
    import json
    return Panel(
        Syntax(json.dumps(params, indent=2), "json", theme="monokai"),
        title=f"🛠  {name}",
        border_style="green",
    )


def agent_result_panel(success: bool, summary: str, steps: int) -> Panel:
    icon = ":check_mark:" if success else ":cross_mark:"
    style = "green" if success else "red"
    return Panel(
        f"{summary}\n\nCompleted in {steps} steps.",
        title=f"{icon} {'Success' if success else 'Failed'}",
        border_style=style,
    )


def session_banner(session_id: str, device: str, mode: str, cost: float = 0.0):
    return Panel(
        f"Device: {device}  |  Mode: {mode}  |  Session: {session_id[:8]}...  |  Cost: ${cost:.2f}",
        title="Android Claude Controller Chat",
        border_style="magenta",
    )
