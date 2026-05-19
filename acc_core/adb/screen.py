from acc_core.adb.client import AdbClient
from acc_core.utils.image import screenshot_to_b64
from acc_core.config import get


class ScreenManager:
    """Screenshot capture and screen recording."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial

    def screenshot(self) -> bytes:
        """Capture screenshot as raw PNG bytes."""
        result = self.client._run(
            "-s", self.serial, "exec-out", "screencap", "-p",
            timeout=15
        )
        return result.stdout.encode("latin-1") if isinstance(result.stdout, str) else result.stdout

    def screenshot_b64(self) -> str:
        """Capture screenshot and return as base64 JPEG string."""
        raw = self.screenshot()
        quality = get("screenshot_quality")
        max_dim = get("max_screenshot_dimension")
        return screenshot_to_b64(raw, max_dimension=max_dim, quality=quality)

    def screenshot_b64_full(self) -> dict:
        """Capture screenshot and return base64 + dimensions."""
        raw = self.screenshot()
        quality = get("screenshot_quality")
        max_dim = get("max_screenshot_dimension")
        b64 = screenshot_to_b64(raw, max_dimension=max_dim, quality=quality)
        from acc_core.adb.device import DeviceInfo
        info = DeviceInfo(self.client, self.serial)
        w, h = info.screen_size()
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            w, h = int(w * ratio), int(h * ratio)
        return {"base64": b64, "width": w, "height": h}
