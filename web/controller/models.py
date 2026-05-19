import uuid
from django.db import models


class Device(models.Model):
    serial = models.CharField(max_length=100, unique=True, primary_key=True)
    model = models.CharField(max_length=200, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    android_version = models.CharField(max_length=50, blank=True)
    screen_width = models.IntegerField(null=True, blank=True)
    screen_height = models.IntegerField(null=True, blank=True)
    is_connected = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.model or self.serial}"


class Session(models.Model):
    MODE_CHOICES = [
        ("auto", "Auto (hybrid)"),
        ("vision", "Vision (always screenshot)"),
        ("text", "Text (UI dump only)"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=500, blank=True)
    goal = models.TextField(blank=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="auto")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    agent_state = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or str(self.id)[:8]


class Message(models.Model):
    ROLE_CHOICES = [
        ("system", "System"),
        ("user", "User"),
        ("assistant", "Assistant"),
        ("tool", "Tool Result"),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    step_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["session", "step_number"]),
        ]

    def __str__(self):
        return f"{self.role} — {self.content[:80]}"


class Screenshot(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="screenshots")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to="screenshots/%Y/%m/%d/", blank=True)
    ui_hierarchy_xml = models.TextField(blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    mode = models.CharField(max_length=10, default="text")
    step_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class SafetyApproval(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    tool_name = models.CharField(max_length=100)
    tool_input = models.JSONField(default=dict)
    risk_level = models.CharField(max_length=20, default="medium")
    status = models.CharField(max_length=20, default="pending")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
