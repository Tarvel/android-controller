from acc_core.adb.client import AdbClient


class FileManager:
    """File operations on the device: read, write, list, push, pull."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial

    def _sh(self, cmd: str, timeout: int = 10) -> str:
        result = self.client._run("-s", self.serial, "shell", cmd, timeout=timeout)
        return result.stdout

    def read(self, path: str, max_lines: int = 200) -> str:
        """Read text content from a file on the device."""
        out = self._sh(f"head -n {max_lines} '{path}' 2>/dev/null")
        return out

    def write(self, path: str, content: str, append: bool = False):
        """Write text content to a file on the device."""
        op = ">>" if append else ">"
        # Use base64 to safely handle special characters
        import base64
        encoded = base64.b64encode(content.encode()).decode()
        self._sh(f"echo '{encoded}' | base64 -d {op} '{path}'")

    def list_dir(self, path: str) -> str:
        """List directory contents."""
        return self._sh(f"ls -la '{path}' 2>/dev/null")

    def push(self, local_path: str, remote_path: str) -> str:
        """Push a file from the host to the device."""
        result = self.client._run(
            "-s", self.serial, "push", local_path, remote_path, timeout=60
        )
        return result.stdout.strip()

    def pull(self, remote_path: str, local_path: str) -> str:
        """Pull a file from the device to the host."""
        result = self.client._run(
            "-s", self.serial, "pull", remote_path, local_path, timeout=60
        )
        return result.stdout.strip()

    def exists(self, path: str) -> bool:
        out = self._sh(f"test -e '{path}' && echo 'EXISTS' || echo 'NOT_FOUND'")
        return "EXISTS" in out
