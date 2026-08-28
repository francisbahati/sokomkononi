from django.urls import path
from .views import (
    DealRoomViewSet,
    NegotiationMessageViewSet,
    DealDocumentViewSet,
    DealActivityViewSet,
    DealActionView,
    MyDealsView
)

urlpatterns = [
    # Deals
    path('', DealRoomViewSet.as_view({'get': 'list', 'post': 'create'}), name='deals-list'),
    path('<int:pk>/', DealRoomViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='deals-detail'),
    path('<int:pk>/status/', DealRoomViewSet.as_view({'patch': 'update_status'}), name='deals-status'),
    
    # My Deals
    path('my-deals/', MyDealsView.as_view(), name='my-deals'),
    
    # Messages
    path('<int:pk>/messages/', NegotiationMessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='deal-messages'),
    path('messages/<int:pk>/', NegotiationMessageViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='deal-message-detail'),
    
    # Documents
    path('<int:pk>/documents/', DealDocumentViewSet.as_view({'get': 'list', 'post': 'create'}), name='deal-documents'),
    path('documents/<int:pk>/', DealDocumentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='deal-document-detail'),
    
    # Activities
    path('<int:pk>/activities/', DealActivityViewSet.as_view({'get': 'list'}), name='deal-activities'),
    
    # Actions
    path('<int:pk>/action/', DealActionView.as_view(), name='deal-action'),
]