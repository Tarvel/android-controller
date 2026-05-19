"""`acc web` — Django web server management."""

import os
import click
from cli.display import console


@click.group()
def web_group():
    """Manage the Django web interface."""
    pass


@web_group.command("serve")
@click.option("--host", "-h", default="127.0.0.1", help="Bind address")
@click.option("--port", "-p", default=8000, type=int, help="Port")
@click.option("--noreload", is_flag=True, help="Disable auto-reload")
def web_serve(host, port, noreload):
    """Run the Django development server."""
    try:
        import django
    except ImportError:
        console.print("[red]Django not installed.[/] Install with: pip install android-claude-controller[web]")
        raise SystemExit(1)

    # Ensure the project root is in Python's path so 'web' namespace can be resolved
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    web_dir = project_root / "web"
    
    # Remove web_dir from sys.path to prevent it from shadowing the 'web' namespace package
    sys.path = [p for p in sys.path if Path(p).resolve() != web_dir]
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.web.settings")
    django.setup()

    from django.core.management import call_command
    argv = ["manage.py", "runserver"]
    if noreload:
        argv.append("--noreload")
    argv.append(f"{host}:{port}")
    call_command("runserver", *argv[2:])


@web_group.command("migrate")
def web_migrate():
    """Run Django migrations."""
    # Ensure the project root is in Python's path so 'web' namespace can be resolved
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    web_dir = project_root / "web"
    
    # Remove web_dir from sys.path to prevent it from shadowing the 'web' namespace package
    sys.path = [p for p in sys.path if Path(p).resolve() != web_dir]
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.web.settings")
    try:
        import django
        django.setup()
        from django.core.management import call_command
        call_command("migrate")
    except ImportError as e:
        console.print(f"[red]Django not installed or import error: {e}[/]")
        raise SystemExit(1)
