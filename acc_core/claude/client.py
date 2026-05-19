import time
import anthropic
from acc_core.claude.prompts import SYSTEM_PROMPT
from acc_core.claude.tools import TOOL_DEFINITIONS
from acc_core.claude.history import ConversationHistory
from acc_core.exceptions import (
    ClaudeAuthError, ClaudeRateLimitError, ClaudeOverloadedError,
    ContextLimitError, ClaudeError,
)
from acc_core.utils.logging import LOGGER


class ClaudeResponse:
    """Parsed response from Claude."""

    def __init__(self, raw: anthropic.types.Message):
        self.raw = raw
        self.text = ""
        self.tool_calls: list[dict] = []
        self.stop_reason = raw.stop_reason
        self.usage = raw.usage

        for block in raw.content:
            if block.type == "text":
                self.text += block.text
            elif block.type == "tool_use":
                self.tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": dict(block.input),
                })

    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def first_tool(self) -> dict | None:
        return self.tool_calls[0] if self.tool_calls else None


class ClaudeClient:
    """Async Anthropic Claude API client with prompt caching and retry logic."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def send_message(
        self,
        conversation: ConversationHistory,
        new_content: str | list | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> ClaudeResponse:
        messages = conversation.to_api_format()

        # Add new user content if provided
        if new_content:
            if isinstance(new_content, str):
                messages.append({"role": "user", "content": new_content})
            else:
                messages.append({"role": "user", "content": new_content})

        # Build system with prompt caching
        system = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        tools = tools if tools is not None else TOOL_DEFINITIONS

        # Apply cache control to first user message for prefix caching
        if messages:
            first_user = messages[0]
            if first_user["role"] == "user" and isinstance(first_user["content"], str):
                first_user = dict(first_user)
                first_user["content"] = [
                    {
                        "type": "text",
                        "text": first_user["content"],
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
                messages[0] = first_user

        return self._call_with_retry(messages, system, tools, max_tokens)

    def _call_with_retry(
        self,
        messages: list,
        system: list,
        tools: list,
        max_tokens: int,
    ) -> ClaudeResponse:
        last_error = None
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
                return ClaudeResponse(response)

            except anthropic.AuthenticationError:
                raise ClaudeAuthError("Invalid API key. Check ANTHROPIC_API_KEY.")

            except anthropic.RateLimitError as e:
                LOGGER.warning(f"Rate limited (attempt {attempt + 1}): {e}")
                last_error = e
                if delay is not None:
                    time.sleep(delay)
                else:
                    raise ClaudeRateLimitError("Rate limited after max retries")

            except anthropic.InternalServerError as e:
                LOGGER.warning(f"API overloaded (attempt {attempt + 1}): {e}")
                last_error = e
                if delay is not None:
                    time.sleep(delay + 5)
                else:
                    raise ClaudeOverloadedError("API overloaded after max retries")

            except anthropic.BadRequestError as e:
                msg = str(e)
                if "context" in msg.lower() or "token" in msg.lower():
                    raise ContextLimitError(f"Context too large: {msg}")
                raise ClaudeError(f"Bad request: {msg}")

        raise ClaudeError(f"Unexpected: {last_error}")
