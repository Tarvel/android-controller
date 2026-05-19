from acc_core.agent.safety import SafetyManager, RiskLevel


def test_safe_tools_require_no_confirmation():
    sm = SafetyManager()
    for name in ["screen_screenshot", "ui_dump_hierarchy", "input_tap", "wait"]:
        assert sm.requires_confirmation(name, {}) is False, f"{name} should be safe"


def test_high_risk_tools_require_confirmation():
    sm = SafetyManager()
    assert sm.requires_confirmation("app_control", {"action": "uninstall", "package": "com.test"}) is True


def test_safe_mode_off_skips_confirmation():
    sm = SafetyManager()
    assert sm.requires_confirmation("app_control", {"action": "uninstall"}, safe_mode=False) is False


def test_dangerous_shell_commands():
    sm = SafetyManager()
    risk, reason = sm._assess_shell("rm -rf /data/data/com.test")
    assert risk == RiskLevel.HIGH
    assert reason


def test_get_system_setting_is_safe():
    sm = SafetyManager()
    risk, _ = sm.assess("system_setting", {"action": "get", "namespace": "global", "key": "test"})
    assert risk == RiskLevel.SAFE


def test_set_system_setting_is_medium():
    sm = SafetyManager()
    risk, _ = sm.assess("system_setting", {"action": "set", "namespace": "global", "key": "test", "value": "x"})
    assert risk == RiskLevel.MEDIUM
