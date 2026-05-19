from acc_core.claude.history import ConversationHistory


def test_add_user_message():
    h = ConversationHistory(max_tokens=100000)
    h.add_user("Hello")
    assert len(h) == 1


def test_add_assistant_message():
    h = ConversationHistory()
    h.add_user("Hi")
    h.add_assistant("Hello!")
    assert len(h) == 2


def test_add_tool_result():
    h = ConversationHistory()
    h.add_user("Do something")
    h.add_tool_result("tool_1", {"success": True, "output": "done"})
    assert len(h) == 2  # tool result is a user message


def test_to_api_format():
    h = ConversationHistory()
    h.add_user("Test")
    msgs = h.to_api_format()
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Test"


def test_context_trimming():
    h = ConversationHistory(max_tokens=100)  # Very small limit
    for i in range(50):
        h.add_user(f"Message {i} " * 20)  # Lots of tokens
        h.add_assistant(f"Response {i} " * 20)
    h._trim_if_needed()
    assert len(h) < 50 * 2  # Should have trimmed


def test_last_n_turns():
    h = ConversationHistory()
    for i in range(10):
        h.add_user(f"Q{i}")
        h.add_assistant(f"A{i}")
    last = h.last_n_turns(3)
    assert len(last) >= 4  # At least 3 turns' worth
