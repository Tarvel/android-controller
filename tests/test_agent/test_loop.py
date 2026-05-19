import asyncio
from unittest.mock import MagicMock, patch
from acc_core.agent.loop import AgentLoop
from acc_core.claude.history import ConversationHistory


def test_agent_result_attributes():
    from acc_core.agent import AgentResult
    r = AgentResult(success=True, summary="Done", steps=3)
    assert r.success is True
    assert r.summary == "Done"
    assert r.steps == 3


def test_loop_has_safety_manager():
    loop = AgentLoop()
    assert loop.safety is not None


def test_observe_returns_text_parts(mock_adb_device):
    loop = AgentLoop()
    parts = asyncio.run(loop._observe(mock_adb_device, "text", 1, []))
    assert len(parts) >= 2
    assert parts[0]["type"] == "text"
    assert "Step 1" in parts[0]["text"]


def test_observe_vision_mode(mock_adb_device):
    loop = AgentLoop()
    parts = asyncio.run(loop._observe(mock_adb_device, "vision", 1, []))
    assert any(p.get("type") == "image" for p in parts)


def test_auto_mode_uses_text_initially(mock_adb_device):
    loop = AgentLoop()
    parts = asyncio.run(loop._observe(mock_adb_device, "auto", 1, []))
    assert not any(p.get("type") == "image" for p in parts)


def test_auto_mode_escalates_to_vision_after_stalemate(mock_adb_device):
    loop = AgentLoop()
    stalemate = [
        {"tool": "input_tap", "result": {"success": True}, "verification": {"changed": False}},
        {"tool": "input_tap", "result": {"success": True}, "verification": {"changed": False}},
        {"tool": "input_tap", "result": {"success": True}, "verification": {"changed": False}},
    ]
    parts = asyncio.run(loop._observe(mock_adb_device, "auto", 5, stalemate))
    assert any(p.get("type") == "image" for p in parts)
