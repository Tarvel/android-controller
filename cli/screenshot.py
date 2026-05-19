"""`acc screenshot` — quick screenshot capture."""

from pathlib import Path
import click
from acc_core.adb import AdbClient, AdbDevice
from cli.display import console


@click.command()
@click.option("--device", "-d", "serial", help="Target device serial")
@click.option("--output", "-o", "output_path", default="screenshot.png", help="Output file path")
def screenshot_cmd(serial, output_path):
    """Capture and save a screenshot from the device."""
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
    raw = adb.screen.screenshot()
    Path(output_path).write_bytes(raw)
    w, h = adb.device.screen_size()
    console.print(f"[green]Screenshot saved: {output_path}[/] ({w}x{h})")
