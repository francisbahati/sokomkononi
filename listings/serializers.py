from rest_framework import serializers
from .models import Category, Listing, ListingImage, SavedSearch, ListingView
from accounts.serializers import UserProfileSerializer


class CategorySerializer(serializers.ModelSerializer):
    listing_count = serializers.IntegerField(source='listings.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'listing_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'caption', 'is_primary', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ListingImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['image', 'caption', 'is_primary', 'order']


# ---------- Public Listing Detail (hides seller phone) ----------
class PublicUserProfileSerializer(serializers.ModelSerializer):
    """Minimal user serializer that excludes phone number."""
    class Meta:
        model = UserProfileSerializer.Meta.model
        fields = ['id', 'username', 'email', 'profile_photo', 'bio', 'is_verified', 'role']
        # Explicitly omit phone_number


class PublicListingDetailSerializer(serializers.ModelSerializer):
    seller_details = PublicUserProfileSerializer(source='seller', read_only=True)
    primary_image = serializers.SerializerMethodField()
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'listing_id', 'title', 'description', 'property_type',
            'category', 'location', 'latitude', 'longitude', 'price',
            'size', 'bedrooms', 'bathrooms', 'status', 'is_featured',
            'main_image', 'view_count', 'seller', 'seller_details',
            'created_at', 'updated_at', 'primary_image', 'images'
        ]
        read_only_fields = [
            'id', 'listing_id', 'view_count', 'created_at', 'updated_at'
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return self.context.get('request').build_absolute_uri(primary.image.url) if primary.image else None
        if obj.main_image:
            return self.context.get('request').build_absolute_uri(obj.main_image.url) if obj.main_image else None
        return None


# ---------- Full Listing (for owner/admin) ----------
class ListingSerializer(serializers.ModelSerializer):
    seller_details = UserProfileSerializer(source='seller', read_only=True)
    primary_image = serializers.SerializerMethodField()
    images = ListingImageSerializer(many=True, read_only=True)
    images_count = serializers.IntegerField(source='images.count', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'listing_id', 'title', 'description', 'property_type',
            'category', 'location', 'latitude', 'longitude', 'price',
            'size', 'bedrooms', 'bathrooms', 'commission_rate', 'status',
            'is_featured', 'rejection_reason', 'main_image', 'view_count',
            'seller', 'seller_details', 'verified_by', 'created_at',
            'updated_at', 'verified_at', 'primary_image', 'images', 'images_count'
        ]
        read_only_fields = [
            'id', 'listing_id', 'view_count', 'verified_by',
            'created_at', 'updated_at', 'verified_at'
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return self.context.get('request').build_absolute_uri(primary.image.url) if primary.image else None
        if obj.main_image:
            return self.context.get('request').build_absolute_uri(obj.main_image.url) if obj.main_image else None
        return None


class ListingCreateSerializer(serializers.ModelSerializer):
    images = ListingImageCreateSerializer(many=True, required=False)

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'property_type', 'category',
            'location', 'latitude', 'longitude', 'price',
            'size', 'bedrooms', 'bathrooms', 'commission_rate',
            'main_image', 'images'
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than 0")
        return value

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        validated_data['seller'] = self.context['request'].user
        validated_data['status'] = Listing.Status.PENDING

        listing = Listing.objects.create(**validated_data)

        for image_data in images_data:
            ListingImage.objects.create(listing=listing, **image_data)

        return listing


class ListingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'property_type', 'category',
            'location', 'latitude', 'longitude', 'price',
            'size', 'bedrooms', 'bathrooms', 'commission_rate',
            'main_image', 'is_featured'
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


# ---------- Admin Listing List (includes rejection reason) ----------
class AdminListingListSerializer(serializers.ModelSerializer):
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'listing_id', 'title', 'price', 'location',
            'property_type', 'status', 'is_featured', 'rejection_reason',
            'view_count', 'created_at', 'seller_username', 'category_name'
        ]


# ---------- Listing List (public) ----------
class ListingListSerializer(serializers.ModelSerializer):
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'listing_id', 'title', 'price', 'location',
            'property_type', 'status', 'is_featured', 'view_count',
            'created_at', 'seller_username', 'primary_image',
            'category_name', 'size', 'bedrooms', 'bathrooms'
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return self.context.get('request').build_absolute_uri(primary.image.url) if primary.image else None
        if obj.main_image:
            return self.context.get('request').build_absolute_uri(obj.main_image.url) if obj.main_image else None
        return None


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = ['id', 'name', 'search_params', 'created_at']
        read_only_fields = ['id', 'created_at']


class ListingViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingView
        fields = ['id', 'listing', 'user', 'ip_address', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']