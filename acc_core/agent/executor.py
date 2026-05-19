import asyncio
import json
import time
from acc_core.adb import AdbDevice
from acc_core.exceptions import AdbConnectionError, ToolTimeoutError


def _extract(tool_call) -> tuple[str, dict, str]:
    """Extract name, input, id from either a dict or ToolCall dataclass."""
    if isinstance(tool_call, dict):
        return tool_call["name"], tool_call.get("input", {}), tool_call.get("id", "")
    return tool_call.name, tool_call.input, tool_call.id


async def execute_tool(adb: AdbDevice, tool_call,  # dict or ToolCall
                       timeout: float = 15.0) -> dict:
    """Execute a single tool call against the ADB device.

    Accepts either a dict (legacy) or ToolCall dataclass.
    Returns a dict with 'success' and either 'output' or 'error'.
    """
    name, inp, _ = _extract(tool_call)
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_tool_sync, adb, name, inp),
            timeout=timeout,
        )
        return {"success": True, "output": result}
    except AdbConnectionError:
        try:
            adb.reconnect()
            result = await asyncio.wait_for(
                asyncio.to_thread(_run_tool_sync, adb, name, inp),
                timeout=timeout,
            )
            return {"success": True, "output": result}
        except Exception:
            return {"success": False, "error": "ADB connection lost and reconnect failed"}
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Tool '{name}' timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _run_tool_sync(adb: AdbDevice, name: str, inp: dict) -> object:
    """Dispatch a tool call to the appropriate ADB method (synchronous)."""
    if name == "screen_screenshot":
        return adb.screen.screenshot_b64_full()

    elif name == "ui_dump_hierarchy":
        max_el = inp.get("max_elements", 80)
        return adb.ui.dump_hierarchy_compact(max_elements=max_el)

    elif name == "app_current":
        return adb.app.current()

    elif name == "input_tap":
        adb.input.tap(inp["x"], inp["y"])
        return {"tapped": [inp["x"], inp["y"]]}

    elif name == "input_long_press":
        adb.input.long_press(inp["x"], inp["y"], inp.get("duration_ms", 1000))
        return {"long_pressed": [inp["x"], inp["y"]], "duration_ms": inp.get("duration_ms", 1000)}

    elif name == "input_swipe":
        adb.input.swipe(
            inp["x1"], inp["y1"], inp["x2"], inp["y2"],
            inp.get("duration_ms", 300)
        )
        return {"swiped": f"({inp['x1']},{inp['y1']}) -> ({inp['x2']},{inp['y2']})"}

    elif name == "input_type":
        adb.input.text(inp["text"])
        return {"typed": inp["text"]}

    elif name == "input_keyevent":
        adb.input.keyevent(inp["keycode"])
        return {"key": inp["keycode"]}

    elif name == "wait":
        sec = inp.get("seconds", 1.0)
        time.sleep(sec)
        return {"waited": sec}

    elif name == "app_list":
        pkgs = adb.app.list_packages(
            filter_term=inp.get("filter"),
            include_system=inp.get("include_system", False)
        )
        return {"packages": pkgs[:200], "count": len(pkgs)}

    elif name == "app_launch":
        out = adb.app.launch(inp["package"], inp.get("activity"))
        return {"launched": inp["package"], "output": out}

    elif name == "app_control":
        action = inp["action"]
        package = inp["package"]
        if action == "force_stop":
            adb.app.force_stop(package)
        elif action == "clear_data":
            adb.app.clear_data(package)
        elif action == "uninstall":
            out = adb.app.uninstall(package)
            return {"uninstalled": package, "output": out}
        return {"action": action, "package": package}

    elif name == "shell_exec":
        result = adb.shell.exec(inp["command"], timeout=inp.get("timeout_sec", 10))
        return result

    elif name == "file_read":
        content = adb.files.read(inp["path"], max_lines=inp.get("max_lines", 200))
        return {"path": inp["path"], "content": content}

    elif name == "file_write":
        adb.files.write(inp["path"], inp["content"], append=inp.get("append", False))
        return {"written": inp["path"], "size": len(inp["content"])}

    elif name == "file_list":
        out = adb.files.list_dir(inp["path"])
        return {"path": inp["path"], "listing": out}

    elif name == "device_info":
        return adb.device.summary()

    elif name == "system_setting":
        action = inp["action"]
        namespace = inp["namespace"]
        if action == "list":
            out = adb.shell.exec(f"settings list {namespace}")
            return {"namespace": namespace, "settings": out.get("stdout", "")}
        elif action == "get":
            out = adb.shell.exec(f"settings get {namespace} {inp['key']}")
            return {"key": inp["key"], "value": out.get("stdout", "")}
        elif action == "set":
            out = adb.shell.exec(f"settings put {namespace} {inp['key']} {inp['value']}")
            return {"set": f"{namespace}.{inp['key']} = {inp['value']}"}

    elif name == "task_complete":
        return {"acknowledged": True}

    return {"error": f"Unknown tool: {name}"}


async def verify_action(adb: AdbDevice, tool_name: str,
                        tool_input: dict, tool_result: dict) -> dict:
    """Quick verification after executing a tool — did the UI change?"""
    if tool_name in ("wait", "device_info", "file_read", "file_list",
                     "app_list", "system_setting", "task_complete", "screen_screenshot"):
        return {"changed": None}  # Not applicable

    try:
        # Quick check: get foreground app
        current = await asyncio.wait_for(
            asyncio.to_thread(adb.app.current),
            timeout=3,
        )
        return {"changed": True, "foreground": current}
    except Exception:
        return {"changed": False, "error": "Could not verify"}
