from acc_core.adb.input import InputController, _KEYCODES


def test_keycodes_have_common_keys():
    assert "HOME" in _KEYCODES
    assert "BACK" in _KEYCODES
    assert "ENTER" in _KEYCODES
    assert "POWER" in _KEYCODES
    assert "VOLUME_UP" in _KEYCODES
    assert "VOLUME_DOWN" in _KEYCODES


def test_keyevent_string_lookup(mock_subprocess, mock_adb_device):
    ctrl = InputController(mock_adb_device._client, "test")
    ctrl.keyevent("HOME")
    call_args = mock_subprocess.call_args[0][0]
    assert "3" in call_args  # HOME keycode


def test_tap_formats_coordinates(mock_subprocess, mock_adb_device):
    ctrl = InputController(mock_adb_device._client, "test")
    ctrl.tap(540, 960)
    call_args = str(mock_subprocess.call_args)
    assert "540" in call_args
    assert "960" in call_args
