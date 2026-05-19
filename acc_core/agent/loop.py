import json
import asyncio
from dataclasses import dataclass, field

from acc_core.adb import AdbDevice
from acc_core.claude import ConversationHistory, TOOL_DEFINITIONS
from acc_core.providers.base import BaseProvider
from acc_core.agent.executor import execute_tool, verify_action
from acc_core.agent.safety import SafetyManager
from acc_core.agent.callbacks import AgentCallbacks
from acc_core.utils.logging import LOGGER


@dataclass
class AgentResult:
    success: bool
    summary: str
    steps: int
    history: ConversationHistory = field(default_factory=ConversationHistory)


@dataclass
class AgentLoop:
    safety: SafetyManager = field(default_factory=SafetyManager)

    async def run(
        self,
        goal: str,
        adb: AdbDevice,
        provider: BaseProvider,
        conversation: ConversationHistory | None = None,
        mode: str = "auto",
        max_steps: int = 20,
        safe_mode: bool = True,
        callbacks: AgentCallbacks | None = None,
    ) -> AgentResult:
        """Execute a goal against the Android device using an LLM provider as the decision engine."""
        if conversation is None:
            conversation = ConversationHistory()

        if callbacks is None:
            callbacks = _NoopCallbacks()

        await callbacks.on_loop_start(goal)

        # Add the goal as the first user message
        conversation.add_user(f"Goal: {goal}\n\nPlease observe the device and work toward this goal step by step.")

        stalemate_count = 0
        recent_results: list[dict] = []

        for step in range(1, max_steps + 1):
            await callbacks.on_step_start(step)

            # ─── OBSERVE ───
            observation_parts = await self._observe(adb, mode, step, recent_results)
            await callbacks.on_observe(observation_parts)

            # ─── PLAN + EXECUTE (Claude decides) ───
            try:
                response = provider.send_message(
                    conversation=conversation,
                    new_content=observation_parts,
                    tools=TOOL_DEFINITIONS,
                )
            except Exception as e:
                await callbacks.on_error(e)
                return AgentResult(success=False, summary=str(e), steps=step, history=conversation)

            if response.text:
                await callbacks.on_assistant_message(response.text)

            if response.has_tool_calls():
                # Save the assistant's reasoning text and tool calls to history so subsequent tool responses have a parent message
                content_blocks = []
                if response.text:
                    content_blocks.append({"type": "text", "text": response.text})
                for tc in response.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    })
                conversation.add_assistant(content_blocks)

                for tc in response.tool_calls:
                    tool_name = tc.name
                    tool_input = tc.input
                    tool_id = tc.id

                    await callbacks.on_tool_call(tool_name, tool_input)
                    LOGGER.info(f"Step {step}: {tool_name}({json.dumps(tool_input, default=str)[:200]})")

                    # ─── SAFETY CHECK ───
                    risk, reason = self.safety.assess(tool_name, tool_input)
                    if self.safety.requires_confirmation(tool_name, tool_input, safe_mode):
                        approved = await callbacks.request_confirmation(
                            tool_name, tool_input, risk.value, reason
                        )
                        if not approved:
                            tool_result = {"success": False, "error": "User denied this action"}
                            await callbacks.on_tool_result(tool_name, tool_result)
                            conversation.add_tool_result(tool_id, tool_result)
                            continue

                    # ─── EXECUTE ───
                    tool_result = await execute_tool(adb, tc)

                    # ─── VERIFY ───
                    verification = await verify_action(adb, tool_name, tool_input, tool_result)
                    tool_result["_verification"] = verification

                    recent_results.append({"tool": tool_name, "result": tool_result, "verification": verification})
                    if len(recent_results) > 5:
                        recent_results = recent_results[-5:]

                    conversation.add_tool_result(tool_id, tool_result)
                    await callbacks.on_tool_result(tool_name, tool_result)

                    # Track stalemate for auto vision escalation
                    if verification.get("changed") is False:
                        stalemate_count += 1
                    else:
                        stalemate_count = 0

                    # ─── TERMINAL CHECK ───
                    if tool_name == "task_complete":
                        success = tool_input.get("success", False)
                        summary = tool_input.get("summary", "Done.")
                        await callbacks.on_task_complete(success, summary, step)
                        return AgentResult(success=success, summary=summary, steps=step, history=conversation)
            else:
                # Claude replied text-only — nudge to use tools
                conversation.add_assistant(response.text)
                # If Claude seems done, ask for explicit task_complete
                if any(word in response.text.lower() for word in ["done", "complete", "finished", "achieved"]):
                    conversation.add_user(
                        "If you've completed the goal, call task_complete to confirm. "
                        "Otherwise, what tool would you like to use next?"
                    )

        # Max steps reached
        conversation.add_user(f"Max steps ({max_steps}) reached. Summarize what was done and call task_complete.")
        try:
            response = provider.send_message(conversation=conversation, tools=TOOL_DEFINITIONS)
            return AgentResult(
                success=False,
                summary=response.text or f"Goal not achieved within {max_steps} steps.",
                steps=max_steps,
                history=conversation,
            )
        except Exception:
            return AgentResult(
                success=False,
                summary=f"Goal not achieved within {max_steps} steps.",
                steps=max_steps,
                history=conversation,
            )

    async def _observe(self, adb: AdbDevice, mode: str, step: int,
                       recent_results: list[dict]) -> list:
        """Gather device observation: current app, UI dump or screenshot."""
        parts = []
        parts.append({"type": "text", "text": f"--- Step {step} ---"})

        # Always get current foreground app (cheap)
        try:
            current = await asyncio.wait_for(
                asyncio.to_thread(adb.app.current),
                timeout=5,
            )
            parts.append({"type": "text", "text": f"Foreground app: {json.dumps(current)}"})
        except Exception:
            parts.append({"type": "text", "text": "Foreground app: (could not determine)"})

        should_screenshot = False

        if mode == "vision":
            should_screenshot = True
        elif mode == "text":
            should_screenshot = False
        elif mode == "auto":
            # Auto mode: escalate to vision after stalemate
            no_progress = all(
                r.get("verification", {}).get("changed") is False
                for r in recent_results[-3:]
            ) if len(recent_results) >= 3 else False
            should_screenshot = no_progress and step > 3

        if should_screenshot:
            try:
                ss = adb.screen.screenshot_b64_full()
                parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": ss["base64"],
                    },
                })
                parts.append({
                    "type": "text",
                    "text": f"Screenshot ({ss['width']}x{ss['height']}) attached above.",
                })
            except Exception as e:
                parts.append({"type": "text", "text": f"Screenshot failed: {e}"})
        else:
            try:
                ui = adb.ui.dump_hierarchy_compact(max_elements=80)
                parts.append({"type": "text", "text": f"Current UI elements:\n{ui}"})
            except Exception as e:
                parts.append({"type": "text", "text": f"UI dump failed: {e}"})

        # Summarize last tool results
        if recent_results:
            last = recent_results[-1]
            summary = {
                "tool": last["tool"],
                "success": last["result"].get("success"),
            }
            if not last["result"].get("success"):
                summary["error"] = last["result"].get("error")
            parts.append({"type": "text", "text": f"Last action: {json.dumps(summary)}"})

        return parts


class _NoopCallbacks(AgentCallbacks):
    """Default no-op callbacks for when none are provided."""
    pass
