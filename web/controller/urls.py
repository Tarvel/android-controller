from django.urls import path
from web.controller import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("devices/", views.DeviceListView.as_view(), name="device_list"),
    path("devices/<str:serial>/", views.DeviceDetailView.as_view(), name="device_detail"),
    path("sessions/", views.SessionListView.as_view(), name="session_list"),
    path("sessions/new/", views.SessionCreateView.as_view(), name="session_create"),
    path("sessions/<uuid:pk>/", views.SessionChatView.as_view(), name="session_chat"),
    path("sessions/<uuid:pk>/delete/", views.SessionDeleteView.as_view(), name="session_delete"),
    # API endpoints
    path("api/sessions/<uuid:pk>/send/", views.api_session_send, name="api_session_send"),
    path("api/sessions/<uuid:pk>/messages/", views.api_session_messages, name="api_session_messages"),
    path("api/sessions/<uuid:pk>/approve/<int:approval_id>/", views.api_approve_action, name="api_approve_action"),
]
