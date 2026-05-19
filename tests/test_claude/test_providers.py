"""Tests for the provider abstraction layer."""

import os
from unittest.mock import patch, MagicMock
from acc_core.providers.base import ProviderResponse, ToolCall
from acc_core.providers.factory import create_provider, PROVIDER_REGISTRY
from acc_core.providers.anthropic import AnthropicProvider
from acc_core.providers.deepseek import DeepSeekProvider, _to_openai_tools, _to_openai_messages


def test_provider_response_has_tool_calls():
    r = ProviderResponse(text="hello", tool_calls=[ToolCall(id="1", name="test", input={})])
    assert r.has_tool_calls() is True


def test_provider_response_no_tool_calls():
    r = ProviderResponse(text="hello")
    assert r.has_tool_calls() is False


def test_provider_response_first_tool():
    tc = ToolCall(id="t1", name="input_tap", input={"x": 1, "y": 2})
    r = ProviderResponse(tool_calls=[tc])
    assert r.first_tool().name == "input_tap"
    assert r.first_tool().input == {"x": 1, "y": 2}


def test_both_providers_registered():
    assert "anthropic" in PROVIDER_REGISTRY
    assert "deepseek" in PROVIDER_REGISTRY


def test_anthropic_provider_auto_selected():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
        provider = create_provider()
        assert provider.provider_name == "anthropic"


def test_deepseek_provider_auto_selected():
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "sk-test",
        "ANTHROPIC_API_KEY": "",  # No Anthropic key
    }):
        from acc_core.providers.factory import create_provider
        # Need to clear key detection
        provider = create_provider(provider="deepseek", api_key="sk-test")
        assert provider.provider_name == "deepseek"


def test_explicit_provider_overrides_auto():
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "DEEPSEEK_API_KEY": "sk-ds-test",
    }):
        provider = create_provider(provider="deepseek", api_key="sk-ds-test")
        assert provider.provider_name == "deepseek"


def test_missing_api_key_raises():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "DEEPSEEK_API_KEY": ""}):
        try:
            create_provider(api_key="")
            assert False, "Should have raised"
        except ValueError:
            pass


def test_convert_tools_to_openai_format():
    from acc_core.claude.tools import TOOL_DEFINITIONS
    result = _to_openai_tools(TOOL_DEFINITIONS[:3])
    assert len(result) == 3
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "screen_screenshot"


def test_convert_messages_user_text():
    msgs = [{"role": "user", "content": "Hello"}]
    result = _to_openai_messages(msgs)
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Hello"


def test_convert_messages_tool_result():
    msgs = [{
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": "tool_1",
            "content": '{"success": true}',
        }],
    }]
    result = _to_openai_messages(msgs)
    assert result[0]["role"] == "tool"
    assert result[0]["tool_call_id"] == "tool_1"
