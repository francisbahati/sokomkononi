from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import DealRoom, NegotiationMessage, DealDocument, DealActivity

@admin.register(DealRoom)
class DealRoomAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'listing_link',
        'buyer_link',
        'seller_link',
        'status_badge',
        'final_price_display',
        'created_at'
    )
    
    list_filter = ('status', 'created_at')
    search_fields = (
        'listing__title',
        'buyer__username',
        'seller__username',
        'listing__listing_id'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Deal Information', {
            'fields': (
                'listing',
                'buyer',
                'seller',
            )
        }),
        ('Pricing', {
            'fields': (
                'original_price',
                'buyer_offer',
                'seller_counter',
                'final_price',
                'commission_amount',
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'completed_at',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    def listing_link(self, obj):
        url = reverse('admin:listings_listing_change', args=[obj.listing.id])
        return format_html('<a href="{}">{}</a>', url, obj.listing.listing_id)
    listing_link.short_description = 'Listing'
    
    def buyer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.buyer.id])
        return format_html('<a href="{}">{}</a>', url, obj.buyer.username)
    buyer_link.short_description = 'Buyer'
    
    def seller_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.seller.id])
        return format_html('<a href="{}">{}</a>', url, obj.seller.username)
    seller_link.short_description = 'Seller'
    
    def status_badge(self, obj):
        colors = {
            'NEGOTIATING': '#ff9800',
            'AGREEMENT': '#2196f3',
            'PAYMENT_PENDING': '#9c27b0',
            'PAYMENT_COMPLETED': '#4caf50',
            'COMPLETED': '#00897b',
            'CANCELLED': '#f44336',
            'DISPUTED': '#d32f2f'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def final_price_display(self, obj):
        if obj.final_price:
            return f"TSh {obj.final_price:,.2f}"
        return "-"
    final_price_display.short_description = 'Final Price'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} deals marked as completed.')
    mark_as_completed.short_description = 'Mark selected deals as completed'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} deals marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected deals as cancelled'

@admin.register(NegotiationMessage)
class NegotiationMessageAdmin(admin.ModelAdmin):
    list_display = ('deal_room', 'sender', 'message_preview', 'is_offer', 'offer_amount', 'created_at')
    list_filter = ('is_offer', 'created_at')
    search_fields = ('deal_room__listing__title', 'sender__username', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(DealDocument)
class DealDocumentAdmin(admin.ModelAdmin):
    list_display = ('deal_room', 'title', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'deal_room__listing__title', 'uploaded_by__username')
    readonly_fields = ('uploaded_at',)

@admin.register(DealActivity)
class DealActivityAdmin(admin.ModelAdmin):
    list_display = ('deal_room', 'user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('deal_room__listing__title', 'user__username', 'action')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)