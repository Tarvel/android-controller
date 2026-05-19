from abc import ABC


class AgentCallbacks(ABC):
    """Abstract callbacks invoked during the agent loop.

    Implement this to stream progress to CLI (Rich), Django (Celery + Redis),
    or any other UI.
    """

    async def on_loop_start(self, goal: str):
        pass

    async def on_step_start(self, step: int):
        pass

    async def on_observe(self, observation):
        pass

    async def on_assistant_message(self, text: str):
        pass

    async def on_tool_call(self, tool_name: str, tool_input: dict):
        pass

    async def on_tool_result(self, tool_name: str, result: dict):
        pass

    async def on_verification(self, tool_name: str, changed: bool):
        pass

    async def request_confirmation(self, tool_name: str, tool_input: dict,
                                   risk_level: str, reason: str) -> bool:
        """Request user confirmation for a dangerous action.
        Return True to proceed, False to block.
        """
        return False

    async def on_task_complete(self, success: bool, summary: str, steps: int):
        pass

    async def on_error(self, error: Exception):
        pass
