import subprocess
import shlex
from acc_core.exceptions import AdbConnectionError, AdbTimeoutError


class AdbClient:
    """Manages ADB server and device connections."""

    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path

    def _run(self, *args, timeout: int = 10) -> subprocess.CompletedProcess:
        cmd = [self.adb_path, *args]
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutError:
            raise AdbTimeoutError(f"ADB command timed out: {' '.join(cmd)}")
        except FileNotFoundError:
            raise AdbConnectionError(
                f"ADB not found at '{self.adb_path}'. Install Android SDK platform-tools."
            )

    def devices(self) -> list[dict]:
        """List connected devices. Returns [{'serial': str, 'state': str}, ...]."""
        result = self._run("devices", "-l")
        devices = []
        for line in result.stdout.strip().splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                state = parts[1]
                info = {}
                for part in parts[2:]:
                    if ":" in part:
                        k, v = part.split(":", 1)
                        info[k] = v
                devices.append({"serial": serial, "state": state, **info})
        return devices

    def connect(self, address: str) -> bool:
        """Connect to a remote ADB device via TCP/IP."""
        result = self._run("connect", address)
        return "connected" in result.stdout.lower()

    def disconnect(self, address: str = None) -> bool:
        """Disconnect from a remote ADB device."""
        args = ["disconnect"]
        if address:
            args.append(address)
        result = self._run(*args)
        return "disconnected" in result.stdout.lower()

    def start_server(self):
        self._run("start-server")

    def kill_server(self):
        self._run("kill-server")
