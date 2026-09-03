from rest_framework import generics, status, permissions, viewsets, filters, serializers
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
    AdminListingListSerializer,
    PublicListingDetailSerializer,
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
from admin_panel.permissions import IsPlatformAdmin
from django.utils import timezone

# ---------- Dummy serializer for schema ----------
class EmptySerializer(serializers.Serializer):
    pass


# ---------- Admin Category Management ----------
class AdminCategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get_queryset(self):
        return super().get_queryset().annotate(listing_count=Count('listings'))


# ---------- Admin Listing Management ----------
class AdminListingListView(generics.ListAPIView):
    serializer_class = AdminListingListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'description', 'location', 'listing_id']

    def get_queryset(self):
        return Listing.objects.all().order_by('-created_at')


class AdminListingApproveView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = Listing.objects.all()
    serializer_class = EmptySerializer

    def patch(self, request, pk):
        listing = self.get_object()
        listing.status = Listing.Status.VERIFIED
        listing.verified_by = request.user
        listing.verified_at = timezone.now()
        listing.rejection_reason = None
        listing.save()
        return Response({'status': 'approved', 'listing': AdminListingListSerializer(listing).data})


class AdminListingRejectView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = Listing.objects.all()
    serializer_class = EmptySerializer

    def patch(self, request, pk):
        listing = self.get_object()
        reason = request.data.get('reason')
        if not reason:
            return Response({'error': 'Reason is required.'}, status=status.HTTP_400_BAD_REQUEST)
        listing.status = Listing.Status.REJECTED
        listing.rejection_reason = reason
        listing.save()
        return Response({'status': 'rejected', 'listing': AdminListingListSerializer(listing).data})


class AdminListingDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = Listing.objects.all()
    serializer_class = AdminListingListSerializer


# ---------- Regular Listing Views ----------
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
        elif self.action == 'retrieve':
            if self.request.user.is_authenticated and (self.get_object().seller == self.request.user or self.request.user.role == 'ADMIN'):
                return ListingSerializer
            return PublicListingDetailSerializer
        return ListingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated and user.role == 'ADMIN':
            return queryset

        if user.is_authenticated:
            return queryset.filter(
                Q(status__in=['ACTIVE', 'VERIFIED']) | Q(seller=user)
            )

        return queryset.filter(status='ACTIVE')

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        listing = self.get_object()
        if request.user == listing.seller:
            new_status = request.data.get('status')
            if new_status == 'PENDING' and listing.status == Listing.Status.REJECTED:
                listing.status = Listing.Status.PENDING
                listing.rejection_reason = None
                listing.save()
                return Response(ListingSerializer(listing).data)
            return Response({'error': 'Only admin can change status or only allowed to resubmit if rejected.'},
                            status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'ADMIN':
            new_status = request.data.get('status')
            if new_status in [Listing.Status.VERIFIED, Listing.Status.REJECTED, Listing.Status.ACTIVE]:
                listing.status = new_status
                if new_status == Listing.Status.REJECTED:
                    reason = request.data.get('reason')
                    if not reason:
                        return Response({'error': 'Reason required for rejection.'}, status=status.HTTP_400_BAD_REQUEST)
                    listing.rejection_reason = reason
                else:
                    listing.rejection_reason = None
                listing.save()
                return Response(ListingSerializer(listing).data)
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

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
        if getattr(self, 'swagger_fake_view', False):
            return Listing.objects.none()
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
        if getattr(self, 'swagger_fake_view', False):
            return SavedSearch.objects.none()
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)