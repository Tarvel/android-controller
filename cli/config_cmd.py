"""`acc config` — configuration management."""

import os
import click
from acc_core.config import CONFIG_DIR, CONFIG_FILE, DEFAULTS, get
from cli.display import console


@click.group()
def config_group():
    """Manage ACC configuration."""
    pass


@config_group.command("show")
def config_show():
    """Show current configuration."""
    from rich.table import Table
    table = Table(title="ACC Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")

    for key, default in DEFAULTS.items():
        env_key = f"ACC_{key.upper()}"
        val = get(key)
        source = "env" if os.environ.get(env_key) else "default"
        table.add_row(key, str(val), source)

    table.add_row("ANTHROPIC_API_KEY", "****" if os.environ.get("ANTHROPIC_API_KEY") else "(not set)", "env")
    console.print(table)


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value (saves to config.toml)."""
    import toml
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        data = toml.loads(CONFIG_FILE.read_text())
    else:
        data = {}

    # Type coercion
    default = DEFAULTS.get(key)
    if isinstance(default, bool):
        value = value.lower() in ("true", "1", "yes")
    elif isinstance(default, int):
        value = int(value)

    data[key] = value
    CONFIG_FILE.write_text(toml.dumps(data))
    console.print(f"[green]{key} = {value}[/] saved to {CONFIG_FILE}")


@config_group.command("init")
def config_init():
    """Interactive first-time setup."""
    console.print("[bold]Android Claude Controller — First-Time Setup[/]\n")

    api_key = click.prompt("Anthropic API Key", default=os.environ.get("ANTHROPIC_API_KEY", ""))
    if api_key:
        # Suggest they use env var instead
        console.print("[dim]Set ANTHROPIC_API_KEY in your .env file or shell profile.[/]")
        console.print(f"[dim]export ANTHROPIC_API_KEY={api_key[:8]}...[/]\n")

    model = click.prompt("Default model", default=get("model"))
    max_steps = click.prompt("Max agent steps", default=str(get("max_steps")))

    console.print("\n[green]Setup complete![/]")
    console.print(f"Config directory: {CONFIG_DIR}")


@config_group.command("path")
def config_path():
    """Show config file path."""
    console.print(f"Config dir: {CONFIG_DIR}")
    console.print(f"Config file: {CONFIG_FILE}")
