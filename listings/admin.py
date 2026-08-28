from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Category, Listing, ListingImage, SavedSearch, ListingView

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'listing_count', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}  # If you have slug field
    
    def listing_count(self, obj):
        return obj.listings.count()
    listing_count.short_description = 'Listings'

class ListingImageInline(admin.TabularInline):
    """Inline admin for listing images"""
    model = ListingImage
    extra = 3
    fields = ('image', 'caption', 'is_primary', 'order', 'image_preview')
    readonly_fields = ('image_preview', 'created_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """Complete admin for Listing model"""
    
    # List view configuration
    list_display = (
    'listing_id',
    'title_preview',
    'seller_info',
    'price_display',
    'property_type',
    'status_badge',
    'is_featured',          # actual field
    'is_featured_badge',    # (optional) keep for display
    'view_count',
    'created_at'
)
    
    list_filter = (
        'status',
        'property_type',
        'is_featured',
        'created_at',
        'category'
    )
    
    search_fields = (
        'listing_id',
        'title',
        'description',
        'location',
        'seller__username',
        'seller__email',
        'seller__phone_number'
    )
    
    list_per_page = 20
    ordering = ('-created_at',)
    
    # Fields that can be edited from list view
    list_editable = ('is_featured',)
    
    # Inline images
    inlines = [ListingImageInline]
    
    # Fieldsets for detail page
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'listing_id',
                'title',
                'description',
                'category',
                'property_type',
            )
        }),
        ('Location & Details', {
            'fields': (
                'location',
                'latitude',
                'longitude',
                'price',
                'size',
                'bedrooms',
                'bathrooms',
            )
        }),
        ('Commission & Status', {
            'fields': (
                'commission_rate',
                'status',
                'is_featured',
            )
        }),
        ('Media', {
            'fields': ('main_image',),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': (
                'seller',
                'verified_by',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'verified_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'listing_id',
        'created_at',
        'updated_at',
        'verified_at',
        'view_count'
    )
    
    # Custom methods for display
    def title_preview(self, obj):
        """Short preview of title"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'
    
    def price_display(self, obj):
        """Display price in TZS"""
        return f"TSh {obj.price:,.2f}"
    price_display.short_description = 'Price'
    
    def seller_info(self, obj):
        """Display seller information with link"""
        url = reverse('admin:accounts_user_change', args=[obj.seller.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.seller.username
        )
    seller_info.short_description = 'Seller'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'PENDING': '#ff9800',
            'VERIFIED': '#2196f3',
            'ACTIVE': '#4caf50',
            'SOLD': '#9e9e9e',
            'REJECTED': '#f44336',
            'INACTIVE': '#795548'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def is_featured_badge(self, obj):
        """Display featured status as badge"""
        if obj.is_featured:
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 4px;">⭐ Featured</span>'
            )
        return format_html(
            '<span style="background-color: #e0e0e0; color: #666; padding: 3px 8px; border-radius: 4px;">Normal</span>'
        )
    is_featured_badge.short_description = 'Featured'
    
    # Admin actions
    actions = ['verify_listings', 'reject_listings', 'mark_as_sold', 'feature_listings']
    
    def verify_listings(self, request, queryset):
        """Admin action to verify listings"""
        updated = queryset.update(
            status=Listing.Status.VERIFIED,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} listings were verified.')
    verify_listings.short_description = 'Verify selected listings'
    
    def reject_listings(self, request, queryset):
        """Admin action to reject listings"""
        updated = queryset.update(status=Listing.Status.REJECTED)
        self.message_user(request, f'{updated} listings were rejected.')
    reject_listings.short_description = 'Reject selected listings'
    
    def mark_as_sold(self, request, queryset):
        """Admin action to mark listings as sold"""
        updated = queryset.update(status=Listing.Status.SOLD)
        self.message_user(request, f'{updated} listings marked as sold.')
    mark_as_sold.short_description = 'Mark as sold'
    
    def feature_listings(self, request, queryset):
        """Admin action to feature listings"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} listings marked as featured.')
    feature_listings.short_description = 'Feature selected listings'
    
    def save_model(self, request, obj, form, change):
        """Custom save with verification tracking"""
        if 'status' in form.changed_data and obj.status == Listing.Status.VERIFIED:
            if not obj.verified_at:
                obj.verified_by = request.user
                obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'image_preview', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('listing__title', 'caption')
    readonly_fields = ('created_at',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'search_params', 'created_at')
    search_fields = ('user__username', 'name')
    list_filter = ('created_at',)

@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ('listing', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('listing__title', 'user__username', 'ip_address')
    readonly_fields = ('viewed_at',)
    ordering = ('-viewed_at',)