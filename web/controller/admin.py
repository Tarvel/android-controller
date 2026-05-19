from django.contrib import admin
from web.controller.models import Device, Session, Message, Screenshot, SafetyApproval


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["serial", "model", "android_version", "is_connected", "last_seen"]
    search_fields = ["serial", "model"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["id_short", "title", "device", "status", "mode", "updated_at"]
    list_filter = ["status", "mode"]
    search_fields = ["title", "goal"]

    def id_short(self, obj):
        return str(obj.id)[:8]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["session_id_short", "role", "content_short", "step_number", "created_at"]
    list_filter = ["role"]

    def session_id_short(self, obj):
        return str(obj.session_id)[:8]

    def content_short(self, obj):
        return obj.content[:100]


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ["session_id_short", "step_number", "mode", "width", "height", "created_at"]

    def session_id_short(self, obj):
        return str(obj.session_id)[:8]


@admin.register(SafetyApproval)
class SafetyApprovalAdmin(admin.ModelAdmin):
    list_display = ["session_id_short", "tool_name", "risk_level", "status", "created_at"]
    list_filter = ["risk_level", "status"]

    def session_id_short(self, obj):
        return str(obj.session_id)[:8]
