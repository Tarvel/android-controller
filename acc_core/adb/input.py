from acc_core.adb.client import AdbClient

_KEYCODES = {
    "HOME": 3, "BACK": 4, "CALL": 5, "ENDCALL": 6,
    "VOLUME_UP": 24, "VOLUME_DOWN": 25, "POWER": 26,
    "CAMERA": 27, "CLEAR": 28,
    "MENU": 82, "NOTIFICATION": 83, "SEARCH": 84,
    "DPAD_UP": 19, "DPAD_DOWN": 20, "DPAD_LEFT": 21, "DPAD_RIGHT": 22,
    "DPAD_CENTER": 23, "ENTER": 66, "DEL": 67,
    "TAB": 61, "SPACE": 62,
    "MEDIA_PLAY_PAUSE": 85, "MEDIA_STOP": 86, "MEDIA_NEXT": 87,
    "MEDIA_PREVIOUS": 88, "MEDIA_REWIND": 89, "MEDIA_FAST_FORWARD": 90,
    "RECENT_APPS": 187,
}


class InputController:
    """Touch, key, and text input on the device."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial

    def _sh(self, cmd: str, timeout: int = 10) -> str:
        result = self.client._run("-s", self.serial, "shell", cmd, timeout=timeout)
        return result.stdout.strip()

    def tap(self, x: int, y: int):
        self._sh(f"input tap {x} {y}")

    def long_press(self, x: int, y: int, duration_ms: int = 1000):
        self._sh(f"input swipe {x} {y} {x} {y} {duration_ms}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        self._sh(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    def text(self, text: str):
        # Escape special characters for input text
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        escaped = escaped.replace("&", "\\&").replace("<", "\\<").replace(">", "\\>")
        escaped = escaped.replace("|", "\\|").replace(";", "\\;")
        escaped = escaped.replace("$", "\\$").replace("`", "\\`")
        escaped = escaped.replace("'", "\\'")
        # Handle spaces
        escaped = escaped.replace(" ", "%s")
        self._sh(f"input text '{escaped}'")

    def keyevent(self, key: int | str):
        """Send a key event. Accepts integer keycode or string name like 'HOME'."""
        if isinstance(key, str):
            key = _KEYCODES.get(key.upper(), key)
        self._sh(f"input keyevent {key}")

    def wake(self):
        """Wake the screen if asleep."""
        self.keyevent("POWER")

    def home(self):
        self.keyevent("HOME")

    def back(self):
        self.keyevent("BACK")

    def recent_apps(self):
        self.keyevent("RECENT_APPS")
