"""ADB device abstraction — unified interface for Android Debug Bridge operations."""

from acc_core.adb.client import AdbClient
from acc_core.adb.device import DeviceInfo
from acc_core.adb.screen import ScreenManager
from acc_core.adb.input import InputController
from acc_core.adb.ui import UiAutomator
from acc_core.adb.app import AppManager
from acc_core.adb.shell import ShellExecutor
from acc_core.adb.files import FileManager


class AdbDevice:
    """Facade providing a unified interface to all ADB submodules for a single device."""

    def __init__(self, serial: str, adb_path: str = "adb"):
        self.serial = serial
        self._client = AdbClient(adb_path=adb_path)
        self.device = DeviceInfo(self._client, serial)
        self.screen = ScreenManager(self._client, serial)
        self.input = InputController(self._client, serial)
        self.ui = UiAutomator(self._client, serial)
        self.app = AppManager(self._client, serial)
        self.shell = ShellExecutor(self._client, serial)
        self.files = FileManager(self._client, serial)

    def reconnect(self):
        """Attempt to reconnect the ADB device (e.g. after connection loss)."""
        self._client._run("-s", self.serial, "wait-for-device", timeout=15)
