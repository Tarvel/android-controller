import pytest


@pytest.fixture
def mock_subprocess(mocker):
    return mocker.patch("subprocess.run")


@pytest.fixture
def mock_adb_device(mocker):
    device = mocker.MagicMock()
    device.serial = "test-device-001"
    device.device.summary.return_value = {
        "model": "TestPhone", "android_version": "14",
        "screen_width": 1080, "screen_height": 2400,
    }
    device.screen.screenshot_b64.return_value = "base64test=="
    device.screen.screenshot_b64_full.return_value = {
        "base64": "base64test==", "width": 1080, "height": 2400,
    }
    device.ui.dump_hierarchy.return_value = '<hierarchy><node text="Test" bounds="[0,0][100,100]"/></hierarchy>'
    device.ui.dump_hierarchy_compact.return_value = "{'text': 'Test', 'bounds': '[0,0][100,100]'}"
    device.app.current.return_value = {"package": "com.test", "activity": ".MainActivity"}
    device.app.list_packages.return_value = ["com.test", "com.example"]
    device.shell.exec.return_value = {"rc": 0, "stdout": "ok", "stderr": ""}
    return device
