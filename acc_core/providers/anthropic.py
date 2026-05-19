"""Anthropic Claude provider."""

import time
import anthropic
from acc_core.providers.base import BaseProvider, ProviderResponse, ToolCall
from acc_core.providers.factory import register_provider
from acc_core.claude.history import ConversationHistory
from acc_core.claude.prompts import SYSTEM_PROMPT
from acc_core.claude.tools import TOOL_DEFINITIONS
from acc_core.exceptions import (
    ClaudeAuthError, ClaudeRateLimitError, ClaudeOverloadedError,
    ContextLimitError, ClaudeError,
)
from acc_core.utils.logging import LOGGER


@register_provider("anthropic")
class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        super().__init__(api_key, model)
        self.client = anthropic.Anthropic(api_key=api_key)

    def send_message(
        self,
        conversation: ConversationHistory,
        new_content: str | list | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        messages = conversation.to_api_format()

        if new_content:
            if isinstance(new_content, str):
                messages.append({"role": "user", "content": new_content})
            else:
                messages.append({"role": "user", "content": new_content})

        system = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        tools = tools if tools is not None else TOOL_DEFINITIONS

        # Cache first user message
        if messages and messages[0]["role"] == "user" and isinstance(messages[0]["content"], str):
            messages[0] = dict(messages[0])
            messages[0]["content"] = [
                {
                    "type": "text",
                    "text": messages[0]["content"],
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        return self._call_with_retry(messages, system, tools, max_tokens)

    def _call_with_retry(self, messages, system, tools, max_tokens) -> ProviderResponse:
        delays = [1, 2, 4, 8]

        for attempt, delay in enumerate(delays + [None]):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                    tools=tools,
                )
                return self._parse_response(response)

            except anthropic.AuthenticationError:
                raise ClaudeAuthError("Invalid Anthropic API key.")
            except anthropic.RateLimitError as e:
                LOGGER.warning(f"Rate limited (attempt {attempt + 1})")
                if delay is not None:
                    time.sleep(delay)
                else:
                    raise ClaudeRateLimitError("Rate limited after max retries")
            except anthropic.InternalServerError as e:
                LOGGER.warning(f"API overloaded (attempt {attempt + 1})")
                if delay is not None:
                    time.sleep(delay + 5)
                else:
                    raise ClaudeOverloadedError("API overloaded after max retries")
            except anthropic.BadRequestError as e:
                msg = str(e)
                if "context" in msg.lower() or "token" in msg.lower():
                    raise ContextLimitError(f"Context too large: {msg}")
                raise ClaudeError(f"Bad request: {msg}")

        raise ClaudeError("Unexpected error")

    def _parse_response(self, raw) -> ProviderResponse:
        resp = ProviderResponse(stop_reason=raw.stop_reason, usage=dict(raw.usage) if raw.usage else {})
        for block in raw.content:
            if block.type == "text":
                resp.text += block.text
            elif block.type == "tool_use":
                resp.tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    input=dict(block.input),
                ))
        return resp
