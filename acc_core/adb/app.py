from acc_core.adb.client import AdbClient


class AppManager:
    """Application management: list, launch, stop, install, uninstall."""

    def __init__(self, client: AdbClient, serial: str):
        self.client = client
        self.serial = serial

    def _sh(self, cmd: str, timeout: int = 10) -> str:
        result = self.client._run("-s", self.serial, "shell", cmd, timeout=timeout)
        return result.stdout.strip()

    def list_packages(self, filter_term: str = None, include_system: bool = False) -> list[str]:
        """List installed package names."""
        cmd = "pm list packages"
        if filter_term:
            cmd += f" | grep {filter_term}"
        if not include_system:
            cmd += " -3"
        out = self._sh(cmd)
        pkgs = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkgs.append(line.replace("package:", ""))
        return pkgs

    def current(self) -> dict:
        """Get the foreground app's package and activity."""
        out = self._sh("dumpsys window | grep mCurrentFocus")
        import re
        m = re.search(r"(\S+)/(\S+)\}", out)
        if m:
            return {"package": m.group(1), "activity": m.group(2)}
        # Fallback for newer Android
        out2 = self._sh("dumpsys activity activities | grep mResumedActivity")
        m = re.search(r"(\S+)/(\S+)\s", out2)
        if m:
            return {"package": m.group(1), "activity": m.group(2)}
        return {"package": "", "activity": ""}

    def launch(self, package: str, activity: str = None) -> str:
        """Launch an app. Returns output from am start."""
        if activity:
            cmd = f"am start -n {package}/{activity}"
        else:
            cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
        return self._sh(cmd)

    def force_stop(self, package: str):
        self._sh(f"am force-stop {package}")

    def clear_data(self, package: str):
        self._sh(f"pm clear {package}")

    def uninstall(self, package: str):
        result = self.client._run("-s", self.serial, "uninstall", package, timeout=30)
        return result.stdout.strip()

    def install(self, apk_path: str) -> str:
        result = self.client._run("-s", self.serial, "install", apk_path, timeout=120)
        return result.stdout.strip()

    def package_info(self, package: str) -> dict:
        """Get package path and version info."""
        out = self._sh(f"dumpsys package {package} | grep -E 'versionName|versionCode|dataDir|apk'")
        return {"info": out}
