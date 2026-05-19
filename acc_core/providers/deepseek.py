"""DeepSeek provider — OpenAI-compatible API."""

import time
import json
from openai import OpenAI
from acc_core.providers.base import BaseProvider, ProviderResponse, ToolCall
from acc_core.providers.factory import register_provider
from acc_core.claude.history import ConversationHistory
from acc_core.claude.prompts import SYSTEM_PROMPT
from acc_core.utils.logging import LOGGER


# Convert Anthropic-format tools to OpenAI function-calling format
def _to_openai_tools(anthropic_tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool schemas to OpenAI function-calling format."""
    openai_tools = []
    for tool in anthropic_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        })
    return openai_tools


# Convert Anthropic-format messages to OpenAI format
def _to_openai_messages(anthropic_messages: list[dict]) -> list[dict]:
    """Convert Anthropic message format to OpenAI chat format."""
    openai_msgs = []

    for msg in anthropic_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "tool":
            continue  # Handled differently

        if role == "user" and isinstance(content, str):
            openai_msgs.append({"role": "user", "content": content})
        elif role == "user" and isinstance(content, list):
            # Handle multimodal content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif block.get("type") == "tool_result":
                        openai_msgs.append({
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": block["content"][:4000],
                        })
                    # Skip images for DeepSeek (it supports vision on some models)
                elif isinstance(block, str):
                    text_parts.append(block)
            if text_parts:
                openai_msgs.append({"role": "user", "content": "\n".join(text_parts)})
        elif role == "assistant":
            if isinstance(content, str):
                openai_msgs.append({"role": "assistant", "content": content})
            elif isinstance(content, list):
                # Tool calls in assistant content
                tool_calls = []
                text_content = ""
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            tool_calls.append({
                                "id": block.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json.dumps(block.get("input", {})),
                                },
                            })
                        elif block.get("type") == "text":
                            text_content += block.get("text", "")
                msg = {"role": "assistant", "content": text_content or None}
                if tool_calls:
                    msg["tool_calls"] = tool_calls
                openai_msgs.append(msg)

    return openai_msgs


@register_provider("deepseek")
class DeepSeekProvider(BaseProvider):
    """Provider for DeepSeek models via OpenAI-compatible API."""

    provider_name = "deepseek"

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(api_key, model)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        )

    def send_message(
        self,
        conversation: ConversationHistory,
        new_content: str | list | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        from acc_core.claude.tools import TOOL_DEFINITIONS

        anthropic_tools = tools if tools is not None else TOOL_DEFINITIONS
        openai_tools = _to_openai_tools(anthropic_tools)

        # Build messages
        raw_messages = conversation.to_api_format()

        if new_content:
            if isinstance(new_content, str):
                raw_messages.append({"role": "user", "content": new_content})
            else:
                raw_messages.append({"role": "user", "content": new_content})

        openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        openai_messages += _to_openai_messages(raw_messages)

        return self._call_with_retry(openai_messages, openai_tools, max_tokens)

    def _call_with_retry(self, messages, tools, max_tokens) -> ProviderResponse:
        delays = [1, 2, 4, 8]

        for attempt, delay in enumerate(delays + [None]):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    max_tokens=max_tokens,
                    temperature=0.7,
                )
                return self._parse_response(response)

            except Exception as e:
                msg = str(e).lower()
                if "rate" in msg or "429" in msg:
                    LOGGER.warning(f"DeepSeek rate limited (attempt {attempt + 1})")
                    if delay is not None:
                        time.sleep(delay)
                        continue
                elif "auth" in msg or "401" in msg or "403" in msg:
                    from acc_core.exceptions import ClaudeAuthError
                    raise ClaudeAuthError(f"DeepSeek auth error: {e}")
                raise

        from acc_core.exceptions import ClaudeError
        raise ClaudeError("DeepSeek API failed after max retries")

    def _parse_response(self, raw) -> ProviderResponse:
        choice = raw.choices[0]
        resp = ProviderResponse(
            stop_reason=choice.finish_reason or "",
            usage=raw.usage.model_dump() if raw.usage else {},
        )

        if choice.message.content:
            resp.text = choice.message.content

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    inp = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    inp = {}
                resp.tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    input=inp,
                ))

        return resp
