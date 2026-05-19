import asyncio
from acc_core.agent.executor import execute_tool


def test_execute_input_tap(mock_adb_device):
    result = asyncio.run(execute_tool(
        mock_adb_device, {"name": "input_tap", "input": {"x": 100, "y": 200}}
    ))
    assert result["success"] is True
    assert result["output"]["tapped"] == [100, 200]


def test_execute_app_current(mock_adb_device):
    result = asyncio.run(execute_tool(
        mock_adb_device, {"name": "app_current", "input": {}}
    ))
    assert result["success"] is True
    assert result["output"]["package"] == "com.test"


def test_execute_device_info(mock_adb_device):
    result = asyncio.run(execute_tool(
        mock_adb_device, {"name": "device_info", "input": {}}
    ))
    assert result["success"] is True
    assert "model" in result["output"]


def test_execute_unknown_tool(mock_adb_device):
    result = asyncio.run(execute_tool(
        mock_adb_device, {"name": "nonexistent_tool", "input": {}}
    ))
    assert result["success"] is False


def test_execute_task_complete(mock_adb_device):
    result = asyncio.run(execute_tool(
        mock_adb_device, {"name": "task_complete", "input": {"success": True, "summary": "done"}}
    ))
    assert result["success"] is True
