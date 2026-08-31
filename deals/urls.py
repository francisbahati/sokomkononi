from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DealRoomViewSet,
    NegotiationMessageViewSet,
    DealDocumentViewSet,
    DealActivityViewSet,
    DealActionView,
    MyDealsView,
    AdminDealListView,
    OfferViewSet,
)

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    # Admin deals (outside router)
    path('admin/deals/', AdminDealListView.as_view(), name='admin-deals-list'),

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

    # Offers (nested under deal room ? we'll add with deal_pk later)
    # We'll use the router for global offers, but we also need per-deal offers list/create.
    # Better: we can add nested routes manually.
]

# Add nested offer routes
urlpatterns += [
    path('<int:deal_pk>/offers/', OfferViewSet.as_view({'get': 'list', 'post': 'create'}), name='deal-offers'),
    path('offers/<int:pk>/', OfferViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='offer-detail'),
    path('offers/<int:pk>/accept/', OfferViewSet.as_view({'post': 'accept'}), name='offer-accept'),
    path('offers/<int:pk>/reject/', OfferViewSet.as_view({'post': 'reject'}), name='offer-reject'),
]