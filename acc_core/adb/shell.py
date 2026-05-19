from acc_core.adb.client import AdbClient
from acc_core.config import get


class ShellExecutor:
    """Execute arbitrary shell commands on the device."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial

    def exec(self, command: str, timeout: int = None) -> dict:
        """Execute a shell command. Returns {rc, stdout, stderr}."""
        timeout = timeout or get("shell_timeout_seconds")
        result = self.client._run(
            "-s", self.serial, "shell", command, timeout=timeout
        )
        return {
            "rc": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
