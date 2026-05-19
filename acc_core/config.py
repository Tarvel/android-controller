import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "acc"
CONFIG_FILE = CONFIG_DIR / "config.toml"
SESSIONS_DIR = Path.home() / ".config" / "acc" / "sessions"
SCREENSHOTS_DIR = Path.home() / ".config" / "acc" / "screenshots"
CACHE_DIR = Path.home() / ".cache" / "acc"

DEFAULTS = {
    "max_steps": 20,
    "default_mode": "auto",
    "safe_mode": True,
    "screenshot_quality": 70,
    "max_screenshot_dimension": 1280,
    "tool_timeout_seconds": 15,
    "shell_timeout_seconds": 10,
    "max_ui_elements": 80,
    "provider": "auto",
    "model": "claude-sonnet-4-5-20250929",
    "deepseek_model": "deepseek-chat",
}


def get(key: str):
    env_key = f"ACC_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        if isinstance(DEFAULTS.get(key), bool):
            return env_val.lower() in ("true", "1", "yes")
        if isinstance(DEFAULTS.get(key), int):
            return int(env_val)
        return env_val
    return DEFAULTS.get(key)


def ensure_dirs():
    for d in [CONFIG_DIR, SESSIONS_DIR, SCREENSHOTS_DIR, CACHE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
