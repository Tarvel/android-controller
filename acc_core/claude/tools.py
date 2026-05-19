"""Tool definitions for the Anthropic tool-use API.

19 tools exposed to Claude: observation (3), input (6), app management (3),
system (6), terminal (1).
"""

TOOL_SCREEN_SCREENSHOT = {
    "name": "screen_screenshot",
    "description": "Take a screenshot of the device screen. Returns a base64-encoded JPEG image showing exactly what the user sees. Use when you need visual context — image-heavy apps, maps, games, or when UI dump is confusing.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

TOOL_UI_DUMP_HIERARCHY = {
    "name": "ui_dump_hierarchy",
    "description": "Dump the current UI hierarchy as structured text. Returns all visible elements with their text, class, bounds (coordinates), clickable state, and resource IDs. Use this for text-heavy UIs like Settings, lists, and forms. Much more token-efficient than screenshots. Provides exact element coordinates for tapping.",
    "input_schema": {
        "type": "object",
        "properties": {
            "max_elements": {
                "type": "integer",
                "description": "Maximum number of UI elements to return (default 80). Increase for complex screens, decrease to save tokens.",
            }
        },
    },
}

TOOL_APP_CURRENT = {
    "name": "app_current",
    "description": "Get the currently foreground app's package name and activity. Useful to verify which app is open before interacting.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

TOOL_INPUT_TAP = {
    "name": "input_tap",
    "description": "Tap at precise screen coordinates. Coordinates are in pixels from top-left. Always read coordinates from ui_dump_hierarchy element bounds, never estimate. Tap the CENTER of an element: x = (left+right)/2, y = (top+bottom)/2.",
    "input_schema": {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate in pixels (0 = left edge)"},
            "y": {"type": "integer", "description": "Y coordinate in pixels (0 = top edge)"},
        },
        "required": ["x", "y"],
    },
}

TOOL_INPUT_LONG_PRESS = {
    "name": "input_long_press",
    "description": "Long press at coordinates. Use for context menus, drag handles, or long-press interactions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "duration_ms": {
                "type": "integer",
                "description": "Press duration in milliseconds (default 1000 = 1 second)",
            },
        },
        "required": ["x", "y"],
    },
}

TOOL_INPUT_SWIPE = {
    "name": "input_swipe",
    "description": "Swipe gesture from (x1,y1) to (x2,y2). To scroll UP (move content down), swipe from lower to higher Y. To scroll DOWN, swipe from higher to lower Y.",
    "input_schema": {
        "type": "object",
        "properties": {
            "x1": {"type": "integer", "description": "Start X coordinate"},
            "y1": {"type": "integer", "description": "Start Y coordinate"},
            "x2": {"type": "integer", "description": "End X coordinate"},
            "y2": {"type": "integer", "description": "End Y coordinate"},
            "duration_ms": {
                "type": "integer",
                "description": "Swipe duration in milliseconds (default 300)",
            },
        },
        "required": ["x1", "y1", "x2", "y2"],
    },
}

TOOL_INPUT_TYPE = {
    "name": "input_type",
    "description": "Type text into the currently focused input field. Always tap on a text field first to focus it, wait 200ms, then type.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to type"},
        },
        "required": ["text"],
    },
}

TOOL_INPUT_KEYEVENT = {
    "name": "input_keyevent",
    "description": "Press a hardware or system key. Common keys: HOME, BACK, RECENT_APPS, ENTER, DEL, VOLUME_UP, VOLUME_DOWN, POWER, DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT, DPAD_CENTER.",
    "input_schema": {
        "type": "object",
        "properties": {
            "keycode": {
                "type": "string",
                "description": "Key name (HOME, BACK, RECENT_APPS, ENTER, DEL, etc.) or numeric keycode",
            },
        },
        "required": ["keycode"],
    },
}

TOOL_WAIT = {
    "name": "wait",
    "description": "Wait/pause for the UI to settle. Use after actions that trigger animations, loading, or screen transitions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "seconds": {
                "type": "number",
                "description": "Seconds to wait (0.1 to 10). Default 1.0.",
            },
        },
        "required": [],
    },
}

TOOL_APP_LIST = {
    "name": "app_list",
    "description": "List installed application packages. Optionally filter by name.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filter": {
                "type": "string",
                "description": "Filter packages containing this string",
            },
            "include_system": {
                "type": "boolean",
                "description": "Include system apps (default false, shows only user-installed)",
            },
        },
    },
}

TOOL_APP_LAUNCH = {
    "name": "app_launch",
    "description": "Launch an application by package name. Use app_list to find available packages first.",
    "input_schema": {
        "type": "object",
        "properties": {
            "package": {"type": "string", "description": "Package name to launch"},
            "activity": {
                "type": "string",
                "description": "Specific activity to launch (optional, auto-detected if omitted)",
            },
        },
        "required": ["package"],
    },
}

TOOL_APP_CONTROL = {
    "name": "app_control",
    "description": "Control an application: force stop, clear data, or uninstall. WARNING: uninstall and clear_data are destructive and require user confirmation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["force_stop", "clear_data", "uninstall"],
                "description": "Action to perform on the app",
            },
            "package": {"type": "string", "description": "Package name to act on"},
        },
        "required": ["action", "package"],
    },
}

TOOL_SHELL_EXEC = {
    "name": "shell_exec",
    "description": "Execute an arbitrary shell command on the Android device. Use for system operations not covered by other tools. WARNING: destructive commands (rm, dd, mkfs, reboot) require user confirmation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "timeout_sec": {
                "type": "integer",
                "description": "Timeout in seconds (default 10, max 60)",
            },
        },
        "required": ["command"],
    },
}

TOOL_FILE_READ = {
    "name": "file_read",
    "description": "Read text content from a file on the device.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Full path to the file on the device"},
            "max_lines": {
                "type": "integer",
                "description": "Maximum lines to read (default 200)",
            },
        },
        "required": ["path"],
    },
}

TOOL_FILE_WRITE = {
    "name": "file_write",
    "description": "Write text content to a file on the device. Creates the file if it doesn't exist.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Full path to the file on the device"},
            "content": {"type": "string", "description": "Content to write"},
            "append": {
                "type": "boolean",
                "description": "Append to file instead of overwriting (default false)",
            },
        },
        "required": ["path", "content"],
    },
}

TOOL_FILE_LIST = {
    "name": "file_list",
    "description": "List files and directories at a path on the device.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to list"},
        },
        "required": ["path"],
    },
}

TOOL_DEVICE_INFO = {
    "name": "device_info",
    "description": "Get comprehensive device information: model, manufacturer, Android version, screen size, battery level, and storage usage.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

TOOL_SYSTEM_SETTING = {
    "name": "system_setting",
    "description": "Read or write Android system settings (global, secure, or system namespaces).",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "set", "list"],
                "description": "Action: get a setting value, set a setting, or list all settings in a namespace",
            },
            "namespace": {
                "type": "string",
                "enum": ["global", "secure", "system"],
                "description": "Settings namespace",
            },
            "key": {
                "type": "string",
                "description": "Setting key name (for get/set actions)",
            },
            "value": {
                "type": "string",
                "description": "Setting value (for set action)",
            },
        },
        "required": ["action", "namespace"],
    },
}

TOOL_TASK_COMPLETE = {
    "name": "task_complete",
    "description": "Signal that the goal has been achieved or definitively cannot be achieved. Call this as soon as the task is finished.",
    "input_schema": {
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "description": "True if the goal was achieved, false if it's impossible",
            },
            "summary": {
                "type": "string",
                "description": "Brief summary of what was done and the final result",
            },
        },
        "required": ["success", "summary"],
    },
}

# Full list of all tool definitions
TOOL_DEFINITIONS: list[dict] = [
    # Observation
    TOOL_SCREEN_SCREENSHOT,
    TOOL_UI_DUMP_HIERARCHY,
    TOOL_APP_CURRENT,
    # Input
    TOOL_INPUT_TAP,
    TOOL_INPUT_LONG_PRESS,
    TOOL_INPUT_SWIPE,
    TOOL_INPUT_TYPE,
    TOOL_INPUT_KEYEVENT,
    TOOL_WAIT,
    # App management
    TOOL_APP_LIST,
    TOOL_APP_LAUNCH,
    TOOL_APP_CONTROL,
    # System
    TOOL_SHELL_EXEC,
    TOOL_FILE_READ,
    TOOL_FILE_WRITE,
    TOOL_FILE_LIST,
    TOOL_DEVICE_INFO,
    TOOL_SYSTEM_SETTING,
    # Terminal
    TOOL_TASK_COMPLETE,
]

# Lookup for fast access
TOOLS_BY_NAME: dict[str, dict] = {t["name"]: t for t in TOOL_DEFINITIONS}
