from acc_core.claude.tools import TOOL_DEFINITIONS, TOOLS_BY_NAME


def test_all_19_tools_defined():
    assert len(TOOL_DEFINITIONS) == 19


def test_every_tool_has_name_and_schema():
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert "type" in tool["input_schema"]


def test_tools_by_name_lookup():
    for tool in TOOL_DEFINITIONS:
        assert TOOLS_BY_NAME[tool["name"]] == tool


def test_required_tools_exist():
    required = [
        "screen_screenshot", "ui_dump_hierarchy", "app_current",
        "input_tap", "input_swipe", "input_type", "input_keyevent",
        "app_launch", "app_list", "shell_exec", "device_info",
        "task_complete",
    ]
    for name in required:
        assert name in TOOLS_BY_NAME, f"Missing tool: {name}"


def test_tool_schemas_valid_json():
    import json
    for tool in TOOL_DEFINITIONS:
        json.dumps(tool)  # Should not raise
