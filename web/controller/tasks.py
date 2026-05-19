"""Celery tasks for async agent execution."""

import json
from celery import shared_task
from django.conf import settings

from web.controller.models import Session, Message


@shared_task(bind=True, time_limit=settings.CELERY_TASK_TIME_LIMIT)
def run_agent_task(self, session_id: str, goal: str):
    """Run the agent loop as a Celery background task."""
    try:
        session = Session.objects.get(pk=session_id)
    except Session.DoesNotExist:
        return {"error": "Session not found"}

    from acc_core.adb import AdbDevice
    from acc_core.providers import create_provider
    from acc_core.agent import AgentLoop, AgentCallbacks
    from asgiref.sync import sync_to_async
    import asyncio
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        session.status = "error"
        session.save()
        Message.objects.create(session=session, role="system", content="API key not configured")
        return {"error": "API key missing"}

    serial = session.device.serial if session.device else None
    if not serial:
        session.status = "error"
        session.save()
        return {"error": "No device"}

    adb = AdbDevice(serial)

    class CeleryCallbacks(AgentCallbacks):
        async def on_step_start(self, step: int):
            session.agent_state = {**session.agent_state, "current_step": step}
            await sync_to_async(session.save)(update_fields=["agent_state"])

        async def on_tool_call(self, tool_name: str, tool_input: dict):
            await sync_to_async(Message.objects.create)(
                session=session, role="assistant",
                content=f"Calling {tool_name}",
                metadata={"tool_name": tool_name, "tool_input": tool_input},
                step_number=session.agent_state.get("current_step"),
            )

        async def on_tool_result(self, tool_name: str, result: dict):
            await sync_to_async(Message.objects.create)(
                session=session, role="tool",
                content=json.dumps(result, default=str)[:1000],
                metadata={"tool_name": tool_name, "output": result},
                step_number=session.agent_state.get("current_step"),
            )

        async def on_assistant_message(self, text: str):
            await sync_to_async(Message.objects.create)(
                session=session, role="assistant",
                content=text,
                step_number=session.agent_state.get("current_step"),
            )

        async def on_task_complete(self, success: bool, summary: str, steps: int):
            session.status = "completed" if success else "error"
            await sync_to_async(session.save)(update_fields=["status"])

        async def on_error(self, error: Exception):
            session.status = "error"
            await sync_to_async(session.save)(update_fields=["status"])
            await sync_to_async(Message.objects.create)(session=session, role="system", content=str(error))

    provider = create_provider()
    loop = AgentLoop()
    result = asyncio.run(loop.run(
        goal=goal,
        adb=adb,
        provider=provider,
        mode=session.mode,
        callbacks=CeleryCallbacks(),
        safe_mode=settings.ACC_SAFE_MODE,
        max_steps=settings.ACC_MAX_STEPS,
    ))
    return {"success": result.success, "summary": result.summary, "steps": result.steps}
