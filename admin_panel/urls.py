from django.urls import path
from .views import (
    PlatformSettingsViewSet,
    CommissionRuleViewSet,
    AuditLogViewSet,
    DisputeViewSet,
    SystemNotificationViewSet,
    AdminDashboardStatsView,
    AdminMetricsView
)

urlpatterns = [
    # Dashboard
    path('dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('metrics/', AdminMetricsView.as_view(), name='admin-metrics'),
    
    # Settings
    path('settings/', PlatformSettingsViewSet.as_view({'get': 'list', 'post': 'create'}), name='platform-settings'),
    path('settings/<int:pk>/', PlatformSettingsViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='platform-settings-detail'),
    path('settings/by-key/<str:key>/', PlatformSettingsViewSet.as_view({'get': 'by_key'}), name='platform-settings-by-key'),
    
    # Commission Rules
    path('commission-rules/', CommissionRuleViewSet.as_view({'get': 'list', 'post': 'create'}), name='commission-rules'),
    path('commission-rules/<int:pk>/', CommissionRuleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='commission-rules-detail'),
    path('commission-rules/active/', CommissionRuleViewSet.as_view({'get': 'get_active_rule'}), name='commission-rules-active'),
    
    # Audit Logs
    path('audit-logs/', AuditLogViewSet.as_view({'get': 'list'}), name='audit-logs'),
    path('audit-logs/<int:pk>/', AuditLogViewSet.as_view({'get': 'retrieve'}), name='audit-logs-detail'),
    
    # Disputes
    path('disputes/', DisputeViewSet.as_view({'get': 'list', 'post': 'create'}), name='disputes'),
    path('disputes/<int:pk>/', DisputeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='disputes-detail'),
    path('disputes/<int:pk>/resolve/', DisputeViewSet.as_view({'post': 'resolve'}), name='dispute-resolve'),
    
    # System Notifications
    path('notifications/', SystemNotificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='notifications'),
    path('notifications/<int:pk>/', SystemNotificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='notifications-detail'),
    path('notifications/active/', SystemNotificationViewSet.as_view({'get': 'get_active_notifications'}), name='active-notifications'),
]