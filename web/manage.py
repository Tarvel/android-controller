#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    # Ensure the project root is in Python's path so 'web' namespace can be resolved.
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    web_dir = Path(__file__).resolve().parent
    
    # Remove web_dir from sys.path to prevent it from shadowing the 'web' namespace package.
    sys.path = [p for p in sys.path if Path(p).resolve() != web_dir]
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Install with: pip install android-claude-controller[web]"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
