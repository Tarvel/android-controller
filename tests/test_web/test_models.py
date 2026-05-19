import pytest
from web.controller.models import Device, Session, Message, Screenshot, SafetyApproval


@pytest.mark.django_db
def test_create_device():
    d = Device.objects.create(serial="test123", model="TestPhone", android_version="14")
    assert str(d) == "TestPhone"
    assert d.is_connected is False


@pytest.mark.django_db
def test_create_session():
    d = Device.objects.create(serial="test123")
    s = Session.objects.create(device=d, title="Test session", mode="auto")
    assert s.status == "active"
    assert str(s.pk).count("-") == 4  # UUID format


@pytest.mark.django_db
def test_create_message():
    d = Device.objects.create(serial="test123")
    s = Session.objects.create(device=d, title="Test")
    m = Message.objects.create(session=s, role="user", content="Hello", step_number=1)
    assert m.role == "user"
    assert s.messages.count() == 1


@pytest.mark.django_db
def test_screenshot_model():
    d = Device.objects.create(serial="test123")
    s = Session.objects.create(device=d, title="Test")
    ss = Screenshot.objects.create(session=s, mode="vision", step_number=1, width=1080, height=2400)
    assert ss.mode == "vision"
    assert s.screenshots.count() == 1


@pytest.mark.django_db
def test_safety_approval():
    d = Device.objects.create(serial="test123")
    s = Session.objects.create(device=d, title="Test")
    sa = SafetyApproval.objects.create(
        session=s, tool_name="app_control",
        tool_input={"action": "uninstall"}, risk_level="high"
    )
    assert sa.status == "pending"
