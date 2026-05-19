class ACCError(Exception):
    """Base exception for Android Claude Controller."""


class AdbError(ACCError):
    """ADB-related errors."""


class AdbConnectionError(AdbError):
    """ADB device connection lost or unavailable."""


class AdbTimeoutError(AdbError):
    """ADB command timed out."""


class AdbPermissionError(AdbError):
    """ADB command denied due to permissions."""


class ToolError(ACCError):
    """Tool execution error."""


class ToolTimeoutError(ToolError):
    """Tool execution timed out."""


class SafetyError(ACCError):
    """Safety check blocked an action."""


class ClaudeError(ACCError):
    """Claude API errors."""


class ClaudeAuthError(ClaudeError):
    """Authentication failed with Claude API."""


class ClaudeRateLimitError(ClaudeError):
    """Claude API rate limited."""


class ClaudeOverloadedError(ClaudeError):
    """Claude API overloaded."""


class ContextLimitError(ClaudeError):
    """Conversation context too large."""
