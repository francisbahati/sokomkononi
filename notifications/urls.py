from django.urls import path
from .views import (
    NotificationViewSet,
    UserNotificationViewSet,
    NotificationTemplateViewSet,
    NotificationPreferenceViewSet,
    SystemNotificationSettingListView,
    SystemNotificationSettingToggleView,
    EmailLogViewSet,
    SMSLogViewSet,
    PushNotificationLogViewSet,
    SendNotificationView,
    MyNotificationsView,
    MarkAllReadView,
    UnreadCountView
)

urlpatterns = [
    # System notification settings (admin)
    path('admin/settings/', SystemNotificationSettingListView.as_view(), name='system-notification-settings'),
    path('admin/settings/<str:channel>/toggle/', SystemNotificationSettingToggleView.as_view(), name='system-notification-setting-toggle'),

    # Notifications
    path('', NotificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='notifications-list'),
    path('<int:pk>/', NotificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='notifications-detail'),
    path('<int:pk>/send/', NotificationViewSet.as_view({'post': 'send'}), name='notification-send'),

    # User Notifications
    path('user/', UserNotificationViewSet.as_view({'get': 'list'}), name='user-notifications'),
    path('user/<int:pk>/', UserNotificationViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='user-notification-detail'),

    # My Notifications (current user)
    path('my/', MyNotificationsView.as_view(), name='my-notifications'),
    path('my/unread-count/', UnreadCountView.as_view(), name='unread-count'),
    path('my/mark-all-read/', MarkAllReadView.as_view(), name='mark-all-read'),

    # Templates
    path('templates/', NotificationTemplateViewSet.as_view({'get': 'list', 'post': 'create'}), name='templates'),
    path('templates/<int:pk>/', NotificationTemplateViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='template-detail'),

    # Preferences
    path('preferences/', NotificationPreferenceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='preferences'),

    # Send notification (action)
    path('send/', SendNotificationView.as_view(), name='send-notification'),

    # Logs (admin only)
    path('logs/email/', EmailLogViewSet.as_view({'get': 'list'}), name='email-logs'),
    path('logs/sms/', SMSLogViewSet.as_view({'get': 'list'}), name='sms-logs'),
    path('logs/push/', PushNotificationLogViewSet.as_view({'get': 'list'}), name='push-logs'),
]