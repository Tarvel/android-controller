import subprocess
from acc_core.adb.client import AdbClient
from acc_core.exceptions import AdbTimeoutError, AdbConnectionError


def test_devices_parsing(mock_subprocess):
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=["adb", "devices", "-l"],
        returncode=0,
        stdout="List of devices attached\nRFC123  device usb:1-1 product:raven\n\n",
        stderr="",
    )
    client = AdbClient()
    devices = client.devices()
    assert len(devices) == 1
    assert devices[0]["serial"] == "RFC123"
    assert devices[0]["state"] == "device"


def test_devices_empty(mock_subprocess):
    mock_subprocess.return_value = subprocess.CompletedProcess(
        args=["adb", "devices", "-l"],
        returncode=0,
        stdout="List of devices attached\n\n",
        stderr="",
    )
    client = AdbClient()
    assert client.devices() == []


def test_timeout(mock_subprocess):
    mock_subprocess.side_effect = subprocess.TimeoutError("timed out")
    client = AdbClient()
    try:
        client.devices()
        assert False, "Should have raised"
    except AdbTimeoutError:
        pass


def test_adb_not_found(mock_subprocess):
    mock_subprocess.side_effect = FileNotFoundError()
    client = AdbClient(adb_path="/nonexistent/adb")
    try:
        client.devices()
        assert False, "Should have raised"
    except AdbConnectionError:
        pass
