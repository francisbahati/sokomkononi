from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Listing, ListingImage, SavedSearch, ListingView
from .serializers import (
    CategorySerializer,
    ListingSerializer,
    ListingCreateSerializer,
    ListingUpdateSerializer,
    ListingListSerializer,
    ListingImageSerializer,
    SavedSearchSerializer,
    ListingViewSerializer
)
from .permissions import (
    IsListingOwner,
    IsVerifiedDalali,
    CanManageListing,
    CanViewListing
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['name', 'description']
    filter_backends = [filters.SearchFilter]

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'status', 'is_featured', 'category']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price', 'created_at', 'view_count']

    def get_serializer_class(self):
        if self.action == 'create':
            return ListingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ListingUpdateSerializer
        elif self.action == 'list':
            return ListingListSerializer
        return ListingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Admin sees all listings
        if user.is_authenticated and user.role == 'ADMIN':
            return queryset

        # Authenticated users see active/verified, plus their own (any status)
        if user.is_authenticated:
            return queryset.filter(
                Q(status__in=['ACTIVE', 'VERIFIED']) | Q(seller=user)
            )

        # Unauthenticated users only see active listings
        return queryset.filter(status='ACTIVE')

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        listing = self.get_object()
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admin can update listing status'},
                status=status.HTTP_403_FORBIDDEN
            )
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        listing.status = new_status
        listing.save()
        return Response(ListingSerializer(listing).data)

    @action(detail=True, methods=['post'])
    def add_view(self, request, pk=None):
        listing = self.get_object()
        ip_address = request.META.get('REMOTE_ADDR')
        ListingView.objects.create(
            listing=listing,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address
        )
        listing.increment_view_count()
        return Response({'status': 'view recorded'})

class ListingSearchView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Listing.objects.filter(status='ACTIVE')
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q)
            )
        # Other filters: property_type, category, min_price, max_price, etc.
        property_type = self.request.query_params.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        # Add more filters as needed (size, bedrooms, bathrooms, location)
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        return queryset

class ListingFilterView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Listing.objects.filter(status='ACTIVE')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = {
            'property_types': list(queryset.values_list('property_type', flat=True).distinct()),
            'categories': list(queryset.values_list('category__id', 'category__name').distinct()),
            'locations': list(queryset.values_list('location', flat=True).distinct()),
            'price_range': {
                'min': queryset.aggregate(min_price=models.Min('price'))['min_price'],
                'max': queryset.aggregate(max_price=models.Max('price'))['max_price'],
            },
            'size_range': {
                'min': queryset.aggregate(min_size=models.Min('size'))['min_size'],
                'max': queryset.aggregate(max_size=models.Max('size'))['max_size'],
            }
        }
        return Response(data)

class FeaturedListingsView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Listing.objects.filter(status='ACTIVE', is_featured=True)[:10]

class MyListingsView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Listing.objects.filter(seller=self.request.user)

class ListingImageViewSet(viewsets.ModelViewSet):
    queryset = ListingImage.objects.all()
    serializer_class = ListingImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        listing_pk = self.kwargs.get('pk')
        if listing_pk:
            return ListingImage.objects.filter(listing_id=listing_pk)
        return ListingImage.objects.none()

    def perform_create(self, serializer):
        listing_pk = self.kwargs.get('pk')
        listing = Listing.objects.get(id=listing_pk)
        if self.request.user != listing.seller and self.request.user.role != 'ADMIN':
            raise permissions.PermissionDenied("You don't own this listing")
        serializer.save(listing=listing)

class SavedSearchViewSet(viewsets.ModelViewSet):
    serializer_class = SavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)