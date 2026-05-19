import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView, TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from web.controller.models import Device, Session, Message, Screenshot, SafetyApproval
from web.controller.forms import SessionForm
from acc_core.adb import AdbClient


class DashboardView(TemplateView):
    template_name = "controller/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["devices"] = self._get_devices()
        ctx["active_sessions"] = Session.objects.filter(status="active").order_by("-updated_at")[:10]
        ctx["recent_sessions"] = Session.objects.exclude(status="active").order_by("-updated_at")[:10]
        return ctx

    def _get_devices(self):
        try:
            client = AdbClient()
            return client.devices()
        except Exception:
            return []


class DeviceListView(ListView):
    model = Device
    template_name = "controller/device_list.html"
    context_object_name = "devices"


class DeviceDetailView(DetailView):
    model = Device
    template_name = "controller/device_detail.html"
    context_object_name = "device"
    slug_field = "serial"
    slug_url_kwarg = "serial"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sessions"] = Session.objects.filter(device=self.object).order_by("-updated_at")[:20]
        return ctx


class SessionListView(ListView):
    model = Session
    template_name = "controller/session_list.html"
    context_object_name = "sessions"
    paginate_by = 25


class SessionCreateView(CreateView):
    model = Session
    form_class = SessionForm
    template_name = "controller/session_create.html"
    success_url = reverse_lazy("session_list")

    def form_valid(self, form):
        form.instance.goal = self.request.POST.get("goal", "")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("session_chat", kwargs={"pk": self.object.pk})


class SessionChatView(DetailView):
    model = Session
    template_name = "controller/session_chat.html"
    context_object_name = "session"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["messages"] = self.object.messages.all()
        ctx["screenshots"] = self.object.screenshots.all()
        ctx["pending_approvals"] = self.object.safetyapproval_set.filter(status="pending")
        return ctx


class SessionDeleteView(DeleteView):
    model = Session
    template_name = "controller/session_confirm_delete.html"
    success_url = reverse_lazy("session_list")


# ── API Endpoints ──

@csrf_exempt
@require_POST
def api_session_send(request, pk):
    """Send a message to an active session. Triggers the agent loop."""
    session = get_object_or_404(Session, pk=pk)
    if session.status != "active":
        return JsonResponse({"error": "Session not active"}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not user_message.strip():
        return JsonResponse({"error": "Empty message"}, status=400)

    # Save user message
    msg = Message.objects.create(
        session=session,
        role="user",
        content=user_message,
    )

    # Try Celery first, fall back to inline
    try:
        from web.controller.tasks import run_agent_task
        run_agent_task.delay(str(session.pk), user_message)
        return JsonResponse({"status": "queued", "message_id": msg.pk})
    except Exception:
        pass

    # Inline execution (synchronous — slow but works without Celery)
    try:
        result = _run_agent_inline(session, user_message)
        return JsonResponse({"status": "completed", "result": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def api_session_messages(request, pk):
    """Poll for new messages in a session."""
    session = get_object_or_404(Session, pk=pk)
    after_id = request.GET.get("after", "0")
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    messages = session.messages.filter(pk__gt=after_id).order_by("pk")
    data = {
        "session_status": session.status,
        "messages": [
            {
                "id": m.pk,
                "role": m.role,
                "content": m.content,
                "metadata": m.metadata,
                "step_number": m.step_number,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
    return JsonResponse(data)


@csrf_exempt
@require_POST
def api_approve_action(request, pk, approval_id):
    """Approve or deny a pending safety approval."""
    approval = get_object_or_404(SafetyApproval, pk=approval_id, session_id=pk)
    try:
        data = json.loads(request.body)
        approved = data.get("approved", False)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    approval.status = "approved" if approved else "denied"
    approval.approved_at = timezone.now()
    approval.save()
    return JsonResponse({"status": approval.status})


def _run_agent_inline(session, goal):
    """Run the agent synchronously (fallback when Celery unavailable)."""
    from acc_core.adb import AdbDevice
    from acc_core.providers import create_provider
    from acc_core.agent import AgentLoop, AgentCallbacks

    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return {"success": False, "summary": "No API key configured"}

    serial = session.device.serial if session.device else None
    if not serial:
        return {"success": False, "summary": "No device selected"}

    adb = AdbDevice(serial)

    class DjangoCallbacks(AgentCallbacks):
        async def on_step_start(self, step: int):
            session.agent_state = {**session.agent_state, "current_step": step}
            session.save(update_fields=["agent_state"])

        async def on_tool_call(self, tool_name: str, tool_input: dict):
            Message.objects.create(
                session=session, role="assistant",
                content=f"Calling {tool_name}",
                metadata={"tool_name": tool_name, "tool_input": tool_input},
                step_number=session.agent_state.get("current_step"),
            )

        async def on_tool_result(self, tool_name: str, result: dict):
            Message.objects.create(
                session=session, role="tool",
                content=json.dumps(result, default=str)[:500],
                metadata={"tool_name": tool_name, "tool_output": result},
                step_number=session.agent_state.get("current_step"),
            )

        async def on_task_complete(self, success: bool, summary: str, steps: int):
            session.status = "completed" if success else "error"
            session.save(update_fields=["status"])
            Message.objects.create(
                session=session, role="system",
                content=summary,
                step_number=steps,
            )

    provider = create_provider()
    loop = AgentLoop()
    import asyncio
    result = asyncio.run(loop.run(
        goal=goal,
        adb=adb,
        provider=provider,
        mode=session.mode,
        callbacks=DjangoCallbacks(),
        safe_mode=settings.ACC_SAFE_MODE,
    ))
    return {"success": result.success, "summary": result.summary, "steps": result.steps}
