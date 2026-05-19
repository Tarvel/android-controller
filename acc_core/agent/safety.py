import re
from enum import Enum


class RiskLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyManager:
    """Classifies tool call risk and enforces confirmation requirements."""

    TOOL_RISK = {
        "screen_screenshot": RiskLevel.SAFE,
        "ui_dump_hierarchy": RiskLevel.SAFE,
        "app_current": RiskLevel.SAFE,
        "app_list": RiskLevel.SAFE,
        "device_info": RiskLevel.SAFE,
        "file_list": RiskLevel.SAFE,
        "file_read": RiskLevel.SAFE,
        "input_tap": RiskLevel.SAFE,
        "input_swipe": RiskLevel.SAFE,
        "input_type": RiskLevel.SAFE,
        "input_keyevent": RiskLevel.SAFE,
        "input_long_press": RiskLevel.SAFE,
        "wait": RiskLevel.SAFE,
        "app_launch": RiskLevel.LOW,
        "file_write": RiskLevel.LOW,
        "system_setting": RiskLevel.MEDIUM,
        "shell_exec": RiskLevel.MEDIUM,
        "app_control": RiskLevel.HIGH,
    }

    DANGEROUS_SHELL_PATTERNS = [
        (re.compile(r"\brm\s+(-[rRf]+\s+)*[/]"), RiskLevel.HIGH),
        (re.compile(r"\bdd\s+if="), RiskLevel.HIGH),
        (re.compile(r"\bmkfs\b"), RiskLevel.HIGH),
        (re.compile(r"\breboot\b"), RiskLevel.MEDIUM),
        (re.compile(r">\s*/dev/"), RiskLevel.MEDIUM),
        (re.compile(r"\bchmod\s+777"), RiskLevel.MEDIUM),
        (re.compile(r":/system/"), RiskLevel.MEDIUM),
        (re.compile(r":/vendor/"), RiskLevel.MEDIUM),
        (re.compile(r":/data/data/"), RiskLevel.MEDIUM),
    ]

    def assess(self, tool_name: str, tool_input: dict) -> tuple[RiskLevel, str]:
        base_risk = self.TOOL_RISK.get(tool_name, RiskLevel.MEDIUM)

        if tool_name == "shell_exec":
            return self._assess_shell(tool_input.get("command", ""))
        elif tool_name == "system_setting":
            if tool_input.get("action") == "get":
                return RiskLevel.SAFE, ""
            return RiskLevel.MEDIUM, f"Modifying system setting: {tool_input.get('key', 'unknown')}"
        elif tool_name == "app_control":
            action = tool_input.get("action", "")
            package = tool_input.get("package", "unknown")
            if action == "uninstall":
                return RiskLevel.HIGH, f"Uninstalling app: {package}"
            elif action == "clear_data":
                return RiskLevel.MEDIUM, f"Clearing app data: {package}"
        elif tool_name == "file_write":
            path = tool_input.get("path", "")
            if "/system/" in path or "/vendor/" in path:
                return RiskLevel.HIGH, f"Writing to protected path: {path}"

        return base_risk, ""

    def _assess_shell(self, command: str) -> tuple[RiskLevel, str]:
        highest = RiskLevel.SAFE
        matched = None
        for pattern, risk in self.DANGEROUS_SHELL_PATTERNS:
            if pattern.search(command):
                if risk.value > highest.value:
                    highest = risk
                    matched = pattern.pattern
        reason = f"Dangerous command pattern detected: {matched}" if matched else ""
        return highest, reason

    def requires_confirmation(self, tool_name: str, tool_input: dict,
                              safe_mode: bool = True) -> bool:
        if not safe_mode:
            return False
        risk, _ = self.assess(tool_name, tool_input)
        return risk != RiskLevel.SAFE
