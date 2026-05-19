"""JSON-based session persistence for CLI mode."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from acc_core.config import SESSIONS_DIR, SCREENSHOTS_DIR


def create_session(device_serial: str, goal: str = "", mode: str = "auto") -> str:
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "title": goal[:100] or "Interactive chat",
        "device_serial": device_serial,
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "steps": 0,
        "messages": [],
        "screenshots": [],
    }
    _write(session_id, session)
    return session_id


def load_session(session_id: str) -> dict | None:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_session(session_id: str, session: dict):
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write(session_id, session)


def add_message(session_id: str, role: str, content: str,
                metadata: dict | None = None, step: int | None = None):
    session = load_session(session_id)
    if not session:
        return
    msg = {"role": role, "content": content, "step": step}
    if metadata:
        msg["metadata"] = metadata
    session["messages"].append(msg)
    save_session(session_id, session)


def list_sessions() -> list[dict]:
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            s = json.loads(f.read_text())
            sessions.append({
                "id": s["id"],
                "title": s.get("title", ""),
                "device": s.get("device_serial", ""),
                "status": s.get("status", ""),
                "steps": s.get("steps", 0),
                "updated": s.get("updated_at", ""),
            })
        except (json.JSONDecodeError, KeyError):
            pass
    return sessions


def get_screenshot_dir(session_id: str) -> Path:
    d = SCREENSHOTS_DIR / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write(session_id: str, data: dict):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{session_id}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
