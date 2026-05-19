"""`acc device` — device management commands."""

import click
from rich.panel import Panel
from acc_core.adb import AdbClient, AdbDevice
from cli.display import console, device_table


@click.group()
def device_group():
    """Manage connected Android devices."""
    pass


@device_group.command("list")
def device_list():
    """List connected ADB devices."""
    client = AdbClient()
    devs = client.devices()
    if not devs:
        console.print("[dim]No devices connected.[/] Use [bold]acc device scan[/] to find network devices.")
        return
    enriched = []
    for d in devs:
        try:
            adb = AdbDevice(d["serial"])
            info = adb.device
            enriched.append({
                "serial": d["serial"],
                "model": info.model(),
                "state": d.get("state", "?"),
                "android": info.android_version(),
            })
        except Exception:
            enriched.append({**d, "model": "?", "android": "?"})
    console.print(device_table(enriched))


@device_group.command("info")
@click.argument("serial", required=False)
def device_info(serial):
    """Show detailed device information."""
    client = AdbClient()
    if not serial:
        devs = client.devices()
        if len(devs) == 1:
            serial = devs[0]["serial"]
        else:
            console.print("[red]Specify a device serial.[/]")
            return

    adb = AdbDevice(serial)
    info = adb.device.summary()
    import json
    console.print(Panel(json.dumps(info, indent=2, default=str), title=f"Device: {serial}"))


@device_group.command("scan")
def device_scan():
    """Scan local network for ADB devices (port 5555)."""
    import subprocess
    console.print("Scanning network for ADB devices on port 5555...")
    try:
        result = subprocess.run(["adb", "mdns", "discover"], capture_output=True, text=True, timeout=5)
        console.print(result.stdout or "[dim]No mDNS devices found[/]")
    except FileNotFoundError:
        console.print("[red]adb not found[/]")
    except subprocess.TimeoutError:
        console.print("[dim]Scan timed out[/]")
