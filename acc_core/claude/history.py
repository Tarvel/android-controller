import copy
from acc_core.utils.text import estimate_tokens


class ConversationHistory:
    """Manages the conversation message list with automatic context trimming."""

    def __init__(self, max_tokens: int = 180_000):
        self.messages: list[dict] = []
        self.max_tokens = max_tokens
        self._token_estimate = 0

    def add_user(self, content: str | list):
        msg = {"role": "user", "content": content}
        self.messages.append(msg)
        self._estimate()

    def add_assistant(self, content: str | list, tool_calls: list | None = None):
        msg = {"role": "assistant", "content": content}
        if tool_calls:
            msg["content"] = tool_calls  # API format: tool_use blocks in content list
        self.messages.append(msg)
        self._estimate()

    def add_tool_result(self, tool_use_id: str, result: dict):
        import json
        content_str = json.dumps(result, default=str)
        msg = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content_str[:8000],  # Cap very large results
                }
            ],
        }
        self.messages.append(msg)
        self._estimate()

    def to_api_format(self) -> list[dict]:
        return list(self.messages)

    def last_n_turns(self, n: int) -> list[dict]:
        """Get the last n user-assistant turn pairs."""
        turns = []
        count = 0
        for msg in reversed(self.messages):
            turns.insert(0, msg)
            if msg.get("role") in ("user", "assistant"):
                count += 1
            if count >= n * 2:
                break
        return turns

    def _estimate(self):
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += estimate_tokens(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text", "") or block.get("content", "") or str(block)
                        total += estimate_tokens(str(text))
        self._token_estimate = total

    def _trim_if_needed(self):
        """Trim old messages when approaching context limit."""
        if self._token_estimate < self.max_tokens * 0.85:
            return

        # Remove oldest screenshot content blocks first,
        # then summarize oldest turns into a single summary.
        # Always keep the most recent 5 user/assistant interactions intact.
        kept = []
        turn_count = 0
        for msg in reversed(self.messages):
            if msg["role"] in ("user", "assistant"):
                turn_count += 1
            if turn_count <= 10:  # keep last 5 turns
                kept.insert(0, msg)
                continue
            # Drop screenshots from old messages, keep text
            if isinstance(msg.get("content"), list):
                filtered = [
                    b for b in msg["content"]
                    if b.get("type") != "image"
                ]
                if filtered:
                    msg = copy.deepcopy(msg)
                    msg["content"] = filtered
                    kept.insert(0, msg)

        self.messages = kept
        self._estimate()

    def __len__(self):
        return len(self.messages)

    def __bool__(self):
        return bool(self.messages)
