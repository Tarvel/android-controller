from click.testing import CliRunner
from cli.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "goal" in result.output
    assert "chat" in result.output
    assert "device" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_device_list_no_devices():
    runner = CliRunner()
    result = runner.invoke(cli, ["device", "list"])
    # May succeed or fail depending on ADB availability
    assert result.exit_code in (0, 1)


def test_config_show():
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert "max_steps" in result.output


def test_screenshot_no_device():
    runner = CliRunner()
    result = runner.invoke(cli, ["screenshot", "-o", "/tmp/test.png"])
    assert result.exit_code == 1  # No device found


def test_ui_dump_no_device():
    runner = CliRunner()
    result = runner.invoke(cli, ["ui-dump"])
    assert result.exit_code == 1  # No device found
