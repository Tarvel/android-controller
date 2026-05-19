"""Django-specific agent callbacks using Redis pub/sub for real-time updates."""

import json
import redis
from django.conf import settings
from web.controller.models import Session, Message, Screenshot, SafetyApproval


class DjangoRedisCallbacks:
    """Agent callbacks that persist to Django models and notify via Redis."""

    def __init__(self, session_id: str):
        self.session = Session.objects.get(pk=session_id)
        try:
            self.redis = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        except Exception:
            self.redis = None

    async def on_step_start(self, step: int):
        self.session.agent_state = {**self.session.agent_state, "current_step": step}
        self.session.save(update_fields=["agent_state"])
        self._publish({"event": "step_start", "step": step})

    async def on_tool_call(self, tool_name: str, tool_input: dict):
        msg = Message.objects.create(
            session=self.session,
            role="assistant",
            content=f"Calling {tool_name}",
            metadata={"tool_name": tool_name, "tool_input": tool_input},
            step_number=self.session.agent_state.get("current_step"),
        )
        self._publish({
            "event": "tool_call",
            "message_id": msg.pk,
            "tool_name": tool_name,
            "tool_input": tool_input,
        })

    async def on_tool_result(self, tool_name: str, result: dict):
        msg = Message.objects.create(
            session=self.session,
            role="tool",
            content=json.dumps(result, default=str)[:500],
            metadata={"tool_name": tool_name, "tool_output": result},
            step_number=self.session.agent_state.get("current_step"),
        )
        self._publish({
            "event": "tool_result",
            "message_id": msg.pk,
            "tool_name": tool_name,
            "success": result.get("success"),
        })

    async def request_confirmation(self, tool_name: str, tool_input: dict,
                                   risk_level: str, reason: str) -> bool:
        approval = SafetyApproval.objects.create(
            session=self.session,
            tool_name=tool_name,
            tool_input=tool_input,
            risk_level=risk_level,
            status="pending",
        )
        self._publish({
            "event": "confirmation_needed",
            "approval_id": approval.pk,
            "tool_name": tool_name,
            "risk_level": risk_level,
            "reason": reason,
        })
        # Wait for approval (poll DB)
        import asyncio
        for _ in range(60):  # 60 second timeout
            await asyncio.sleep(1)
            approval.refresh_from_db()
            if approval.status == "approved":
                return True
            elif approval.status == "denied":
                return False
        return False

    async def on_task_complete(self, success: bool, summary: str, steps: int):
        self.session.status = "completed" if success else "error"
        self.session.agent_state = {**self.session.agent_state, "final_step": steps}
        self.session.save(update_fields=["status", "agent_state"])
        Message.objects.create(
            session=self.session, role="system", content=summary, step_number=steps,
        )
        self._publish({"event": "task_complete", "success": success, "summary": summary})

    def _publish(self, data: dict):
        if self.redis:
            try:
                self.redis.publish(f"session:{self.session.pk}", json.dumps(data, default=str))
            except Exception:
                pass
