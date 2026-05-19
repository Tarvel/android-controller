"""Claude API integration — client, tools, prompts, and conversation history."""

from acc_core.claude.client import ClaudeClient, ClaudeResponse
from acc_core.claude.tools import TOOL_DEFINITIONS, TOOLS_BY_NAME
from acc_core.claude.prompts import SYSTEM_PROMPT
from acc_core.claude.history import ConversationHistory
