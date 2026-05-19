import json
import re
from acc_core.adb.client import AdbClient


class DeviceInfo:
    """Retrieve device properties, battery, screen info."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial

    def _sh(self, cmd: str, timeout: int = 10) -> str:
        result = self.client._run("-s", self.serial, "shell", cmd, timeout=timeout)
        return result.stdout.strip()

    def get_properties(self) -> dict:
        """Get all device build properties."""
        out = self._sh("getprop")
        props = {}
        for line in out.splitlines():
            m = re.match(r"\[(.+?)\]:\s*\[(.*)\]", line)
            if m:
                props[m.group(1)] = m.group(2)
        return props

    def model(self) -> str:
        return self._sh("getprop ro.product.model")

    def manufacturer(self) -> str:
        return self._sh("getprop ro.product.manufacturer")

    def android_version(self) -> str:
        return self._sh("getprop ro.build.version.release")

    def sdk_level(self) -> str:
        return self._sh("getprop ro.build.version.sdk")

    def screen_size(self) -> tuple[int, int]:
        """Returns (width, height) in pixels."""
        out = self._sh("wm size")
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))

        # Fallback for older devices
        out = self._sh("dumpsys window displays")
        m = re.search(r"cur=(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))

        return 0, 0

    def screen_density(self) -> int:
        out = self._sh("wm density")
        m = re.search(r"(\d+)", out)
        return int(m.group(1)) if m else 0

    def battery(self) -> dict:
        """Returns battery level, status, health, temperature."""
        out = self._sh("dumpsys battery")
        info = {}
        for line in out.splitlines():
            m = re.match(r"\s*(\w+):\s*(.+)", line)
            if m:
                info[m.group(1).lower()] = m.group(2).strip()
        return info

    def storage(self) -> dict:
        """Returns storage usage for /data in bytes."""
        out = self._sh("df /data")
        parts = out.splitlines()[-1].split()
        if len(parts) >= 4:
            return {
                "total": int(parts[1]) * 1024,
                "used": int(parts[2]) * 1024,
                "free": int(parts[3]) * 1024,
            }
        return {}

    def summary(self) -> dict:
        """All device info in one call."""
        return {
            "model": self.model(),
            "manufacturer": self.manufacturer(),
            "android_version": self.android_version(),
            "sdk_level": self.sdk_level(),
            "screen_width": self.screen_size()[0],
            "screen_height": self.screen_size()[1],
            "screen_density": self.screen_density(),
            "battery": self.battery(),
            "storage": self.storage(),
        }
