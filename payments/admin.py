from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Payment, 
    PaymentMethod, 
    Commission, 
    CommissionRule, 
    Transaction, 
    Escrow,
    Refund,
    PaymentLog
)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'deal_room_link',
        'buyer_link',
        'seller_link',
        'amount_display',
        'commission_display',
        'net_amount_display',
        'payment_method',
        'status_badge',
        'transaction_id',
        'created_at'
    )
    
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'transaction_id',
        'deal_room__listing__title',
        'buyer__username',
        'seller__username'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Payment Details', {
            'fields': (
                'deal_room',
                'buyer',
                'seller',
            )
        }),
        ('Amounts', {
            'fields': (
                'amount',
                'commission',
                'net_amount',
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_method',
                'transaction_id',
                'status',
                'payment_date',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'completed_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_refunded']
    
    def deal_room_link(self, obj):
        url = reverse('admin:deals_dealroom_change', args=[obj.deal_room.id])
        return format_html('<a href="{}">Deal #{}</a>', url, obj.deal_room.id)
    deal_room_link.short_description = 'Deal Room'
    
    def buyer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.buyer.id])
        return format_html('<a href="{}">{}</a>', url, obj.buyer.username)
    buyer_link.short_description = 'Buyer'
    
    def seller_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.seller.id])
        return format_html('<a href="{}">{}</a>', url, obj.seller.username)
    seller_link.short_description = 'Seller'
    
    def amount_display(self, obj):
        return f"TSh {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def commission_display(self, obj):
        return f"TSh {obj.commission:,.2f}"
    commission_display.short_description = 'Commission'
    
    def net_amount_display(self, obj):
        return f"TSh {obj.net_amount:,.2f}"
    net_amount_display.short_description = 'Net Amount'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#ff9800',
            'PROCESSING': '#2196f3',
            'COMPLETED': '#4caf50',
            'FAILED': '#f44336',
            'REFUNDED': '#9e9e9e'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_as_completed.short_description = 'Mark selected payments as completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='FAILED')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = 'Mark selected payments as failed'
    
    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(status='REFUNDED')
        self.message_user(request, f'{updated} payments marked as refunded.')
    mark_as_refunded.short_description = 'Mark selected payments as refunded'

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    list_editable = ('is_active',)

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount_display', 'rate', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('payment__transaction_id',)
    readonly_fields = ('created_at',)
    
    def amount_display(self, obj):
        return f"TSh {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'

@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('rate', 'is_active')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'transaction_id', 'status', 'amount_display', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction_id', 'payment__deal_room__listing__title')
    readonly_fields = ('created_at',)
    
    def amount_display(self, obj):
        return f"TSh {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ('id', 'deal_room_link', 'buyer_link', 'seller_link', 'amount_display', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('deal_room__listing__title',)
    readonly_fields = ('created_at', 'updated_at')
    
    def amount_display(self, obj):
        return f"TSh {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def deal_room_link(self, obj):
        url = reverse('admin:deals_dealroom_change', args=[obj.deal_room.id])
        return format_html('<a href="{}">Deal #{}</a>', url, obj.deal_room.id)
    deal_room_link.short_description = 'Deal Room'
    
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
            'PENDING': '#ff9800',
            'HELD': '#2196f3',
            'RELEASED': '#4caf50',
            'REFUNDED': '#9e9e9e'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount_display', 'reason', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__transaction_id', 'reason')
    readonly_fields = ('created_at',)
    
    def amount_display(self, obj):
        return f"TSh {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('payment', 'action', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('payment__transaction_id', 'user__username')
    readonly_fields = ('created_at',)