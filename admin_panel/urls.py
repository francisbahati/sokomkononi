from django.urls import path
from .views import (
    PlatformSettingsViewSet,
    CommissionRuleViewSet,
    AuditLogViewSet,
    DisputeViewSet,
    SystemNotificationViewSet,
    AdminDashboardStatsView,
    AdminMetricsView,
    CommissionRateView,
    OverviewReportView,
    RevenueByMonthView,
    TopListingsView,
    TopRegionsView,
    PlatformPaymentMethodListView,
    PlatformPaymentMethodToggleView,
    RegionListView,
    RegionDeleteView,
    ContentListView,
    ContentUpdateView,
    # Subscription Plans (Admin)
    SubscriptionPlanListView,
    SubscriptionPlanDetailView,
    SubscriptionPlanToggleView,
    SubscriptionPlanSetStartView,
    # NEW: Seller subscription
    PublicSubscriptionPlanListView,
    SellerSubscriptionView,
    SubscribeToPlanView,
    # NEW: User disputes
    UserDisputeListView,
    UserDisputeCreateView,
)

urlpatterns = [
    # Commission Rate
    path('settings/commission-rate/', CommissionRateView.as_view(), name='commission-rate'),

    # Dashboard
    path('admin/dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('admin/metrics/', AdminMetricsView.as_view(), name='admin-metrics'),

    # Settings
    path('admin/settings/', PlatformSettingsViewSet.as_view({'get': 'list', 'post': 'create'}), name='platform-settings'),
    path('admin/settings/<int:pk>/', PlatformSettingsViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='platform-settings-detail'),
    path('admin/settings/by-key/<str:key>/', PlatformSettingsViewSet.as_view({'get': 'by_key'}), name='platform-settings-by-key'),

    # Commission Rules
    path('admin/commission-rules/', CommissionRuleViewSet.as_view({'get': 'list', 'post': 'create'}), name='commission-rules'),
    path('admin/commission-rules/<int:pk>/', CommissionRuleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='commission-rules-detail'),
    path('admin/commission-rules/active/', CommissionRuleViewSet.as_view({'get': 'get_active_rule'}), name='commission-rules-active'),

    # Audit Logs
    path('admin/audit-logs/', AuditLogViewSet.as_view({'get': 'list'}), name='audit-logs'),
    path('admin/audit-logs/<int:pk>/', AuditLogViewSet.as_view({'get': 'retrieve'}), name='audit-logs-detail'),

    # Disputes (Admin)
    path('admin/disputes/', DisputeViewSet.as_view({'get': 'list', 'post': 'create'}), name='disputes'),
    path('admin/disputes/<int:pk>/', DisputeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='disputes-detail'),
    path('admin/disputes/<int:pk>/resolve/', DisputeViewSet.as_view({'post': 'resolve'}), name='dispute-resolve'),

    # System Notifications
    path('admin/notifications/', SystemNotificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='notifications'),
    path('admin/notifications/<int:pk>/', SystemNotificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='notifications-detail'),
    path('admin/notifications/active/', SystemNotificationViewSet.as_view({'get': 'get_active_notifications'}), name='active-notifications'),

    # Reports
    path('admin/reports/overview/', OverviewReportView.as_view(), name='reports-overview'),
    path('admin/reports/revenue-by-month/', RevenueByMonthView.as_view(), name='reports-revenue-month'),
    path('admin/reports/top-listings/', TopListingsView.as_view(), name='reports-top-listings'),
    path('admin/reports/top-regions/', TopRegionsView.as_view(), name='reports-top-regions'),

    # Payment Methods (platform-wide)
    path('admin/payment-methods/', PlatformPaymentMethodListView.as_view(), name='admin-payment-methods'),
    path('admin/payment-methods/<str:name>/toggle/', PlatformPaymentMethodToggleView.as_view(), name='admin-payment-method-toggle'),

    # Regions
    path('admin/regions/', RegionListView.as_view(), name='admin-regions'),
    path('admin/regions/<str:name>/', RegionDeleteView.as_view(), name='admin-region-delete'),

    # Content (Policies)
    path('content/policies/', ContentListView.as_view(), name='content-policies'),
    path('content/policies/', ContentUpdateView.as_view(), name='content-policies-update'),

    # ---------- Subscription Plans (Admin) ----------
    path('admin/packages/', SubscriptionPlanListView.as_view(), name='subscription-plans-list'),
    path('admin/packages/<int:pk>/', SubscriptionPlanDetailView.as_view(), name='subscription-plans-detail'),
    path('admin/packages/<str:name>/toggle/', SubscriptionPlanToggleView.as_view(), name='subscription-plans-toggle'),
    path('admin/packages/<str:name>/set-start/', SubscriptionPlanSetStartView.as_view(), name='subscription-plans-set-start'),

    # ---------- NEW: Public/Seller Subscription ----------
    path('packages/', PublicSubscriptionPlanListView.as_view(), name='public-packages'),
    path('packages/my-subscription/', SellerSubscriptionView.as_view(), name='my-subscription'),
    path('packages/subscribe/', SubscribeToPlanView.as_view(), name='subscribe-plan'),

    # ---------- NEW: User Disputes ----------
    path('disputes/my/', UserDisputeListView.as_view(), name='my-disputes'),
    path('disputes/create/', UserDisputeCreateView.as_view(), name='create-dispute'),
]