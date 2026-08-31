from django.urls import path
from .views import (
    CategoryViewSet,
    ListingViewSet,
    ListingImageViewSet,
    SavedSearchViewSet,
    ListingSearchView,
    ListingFilterView,
    FeaturedListingsView,
    MyListingsView,
    AdminCategoryViewSet,
    AdminListingListView,
    AdminListingApproveView,
    AdminListingRejectView,
    AdminListingDeleteView,
)

urlpatterns = [
    # ---------- Admin endpoints ----------
    path('admin/categories/', AdminCategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='admin-categories'),
    path('admin/categories/<int:pk>/', AdminCategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='admin-category-detail'),

    path('admin/listings/', AdminListingListView.as_view(), name='admin-listings'),
    path('admin/listings/<int:pk>/approve/', AdminListingApproveView.as_view(), name='admin-listing-approve'),
    path('admin/listings/<int:pk>/reject/', AdminListingRejectView.as_view(), name='admin-listing-reject'),
    path('admin/listings/<int:pk>/', AdminListingDeleteView.as_view(), name='admin-listing-delete'),

    # ---------- Public/Seller endpoints ----------
    path('categories/', CategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='categories'),
    path('categories/<int:pk>/', CategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='category-detail'),

    path('', ListingViewSet.as_view({'get': 'list', 'post': 'create'}), name='listings-list'),
    path('<int:pk>/', ListingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='listings-detail'),
    path('<int:pk>/status/', ListingViewSet.as_view({'patch': 'update_status'}), name='listings-status'),
    path('<int:pk>/view/', ListingViewSet.as_view({'post': 'add_view'}), name='listings-view'),

    path('my-listings/', MyListingsView.as_view(), name='my-listings'),

    path('search/', ListingSearchView.as_view(), name='listings-search'),
    path('filter/', ListingFilterView.as_view(), name='listings-filter'),
    path('featured/', FeaturedListingsView.as_view(), name='featured-listings'),

    path('<int:pk>/images/', ListingImageViewSet.as_view({'get': 'list', 'post': 'create'}), name='listing-images'),
    path('images/<int:pk>/', ListingImageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='listing-image-detail'),

    path('saved-searches/', SavedSearchViewSet.as_view({'get': 'list', 'post': 'create'}), name='saved-searches'),
    path('saved-searches/<int:pk>/', SavedSearchViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='saved-search-detail'),
]