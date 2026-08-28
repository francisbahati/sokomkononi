from django.urls import path
from .views import (
    PaymentViewSet,
    PaymentMethodViewSet,
    CommissionRuleViewSet,
    TransactionViewSet,
    EscrowViewSet,
    RefundViewSet,
    PaymentWebhookView,
    PaymentStatisticsView
)

urlpatterns = [
    # Payments
    path('', PaymentViewSet.as_view({'get': 'list', 'post': 'create'}), name='payments-list'),
    path('<int:pk>/', PaymentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='payments-detail'),
    path('<int:pk>/status/', PaymentViewSet.as_view({'patch': 'update_status'}), name='payments-status'),
    
    # Payment Methods
    path('methods/', PaymentMethodViewSet.as_view({'get': 'list'}), name='payment-methods'),
    
    # Commission Rules
    path('commission-rules/', CommissionRuleViewSet.as_view({'get': 'list', 'post': 'create'}), name='commission-rules'),
    path('commission-rules/<int:pk>/', CommissionRuleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='commission-rules-detail'),
    path('commission-rules/active/', CommissionRuleViewSet.as_view({'get': 'get_active_rule'}), name='commission-rules-active'),
    
    # Transactions
    path('transactions/', TransactionViewSet.as_view({'get': 'list'}), name='transactions'),
    path('transactions/<int:pk>/', TransactionViewSet.as_view({'get': 'retrieve'}), name='transaction-detail'),
    
    # Escrow
    path('escrow/', EscrowViewSet.as_view({'get': 'list', 'post': 'create'}), name='escrow-list'),
    path('escrow/<int:pk>/', EscrowViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='escrow-detail'),
    path('escrow/<int:pk>/release/', EscrowViewSet.as_view({'post': 'release'}), name='escrow-release'),
    path('escrow/<int:pk>/refund/', EscrowViewSet.as_view({'post': 'refund'}), name='escrow-refund'),
    
    # Refunds
    path('refunds/', RefundViewSet.as_view({'get': 'list', 'post': 'create'}), name='refunds-list'),
    path('refunds/<int:pk>/', RefundViewSet.as_view({'get': 'retrieve'}), name='refunds-detail'),
    path('refunds/<int:pk>/process/', RefundViewSet.as_view({'post': 'process'}), name='refunds-process'),
    
    # Webhook (for payment providers)
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    
    # Statistics
    path('statistics/', PaymentStatisticsView.as_view(), name='payment-statistics'),
]