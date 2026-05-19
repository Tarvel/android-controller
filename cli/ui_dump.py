"""`acc ui-dump` — quick UI hierarchy inspection."""

from pathlib import Path
import click
from acc_core.adb import AdbClient, AdbDevice
from cli.display import console


@click.command("ui-dump")
@click.option("--device", "-d", "serial", help="Target device serial")
@click.option("--output", "-o", "output_path", help="Save XML to file")
@click.option("--filter", "-f", "filter_text", help="Show only elements containing this text")
def ui_dump_cmd(serial, output_path, filter_text):
    """Dump the current UI hierarchy as text."""
    client = AdbClient()
    devs = client.devices()
    if not devs:
        console.print("[red]No devices connected.[/]")
        raise SystemExit(1)

    if serial:
        target = next((d for d in devs if d["serial"] == serial), None)
    elif len(devs) == 1:
        target = devs[0]
    else:
        console.print("[red]Use -d to specify a device.[/]")
        raise SystemExit(1)

    if not target:
        console.print(f"[red]Device {serial} not found.[/]")
        raise SystemExit(1)

    adb = AdbDevice(target["serial"])
    if output_path:
        full_xml = adb.ui.dump_hierarchy()
        Path(output_path).write_text(full_xml)
        console.print(f"[green]UI dump saved: {output_path}[/] ({len(full_xml)} chars)")
        return

    compact = adb.ui.dump_hierarchy_compact(max_elements=100)

    if filter_text:
        for line in compact.splitlines():
            if filter_text.lower() in line.lower():
                console.print(line)
    else:
        from rich.syntax import Syntax
        console.print(Syntax(compact[:5000], "text", theme="monokai"))
