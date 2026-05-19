"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from acc_core.claude.history import ConversationHistory
from acc_core.claude.tools import TOOL_DEFINITIONS


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class ProviderResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    usage: dict = field(default_factory=dict)

    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def first_tool(self) -> ToolCall | None:
        return self.tool_calls[0] if self.tool_calls else None


class BaseProvider(ABC):
    """Abstract LLM provider that both Anthropic and DeepSeek implement."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def send_message(
        self,
        conversation: ConversationHistory,
        new_content: str | list | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        """Get tool definitions in the provider's native format."""
        return TOOL_DEFINITIONS
