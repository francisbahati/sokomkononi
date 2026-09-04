from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Payment, PaymentMethod, Commission, CommissionRule,
    Transaction, Escrow, Refund, PaymentLog,
    Payout, PayoutAccount,
    Wallet, WalletTransaction, WithdrawalRequest
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    list_editable = ('is_active',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'deal_room_link', 'buyer_link', 'seller_link', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'buyer__username', 'seller__username', 'deal_room__listing__title')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    list_editable = ('status',)
    fieldsets = (
        ('Deal Information', {
            'fields': ('deal_room', 'buyer', 'seller')
        }),
        ('Amounts', {
            'fields': ('amount', 'commission', 'net_amount')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'transaction_id', 'status', 'payment_date', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('payment_link', 'amount', 'rate', 'is_paid', 'paid_at', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('payment__deal_room__listing__title',)

    def payment_link(self, obj):
        url = reverse('admin:payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">Payment #{}</a>', url, obj.payment.id)
    payment_link.short_description = 'Payment'


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    list_editable = ('rate', 'is_active')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'payment_link', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction_id',)
    readonly_fields = ('created_at', 'updated_at')

    def payment_link(self, obj):
        url = reverse('admin:payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">Payment #{}</a>', url, obj.payment.id)
    payment_link.short_description = 'Payment'


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ('deal_room_link', 'buyer_link', 'seller_link', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('deal_room__listing__title', 'buyer__username', 'seller__username')
    readonly_fields = ('created_at', 'updated_at', 'held_at', 'released_at', 'refunded_at')

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


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment_link', 'amount', 'status', 'processed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__deal_room__listing__title', 'reason')
    readonly_fields = ('created_at', 'updated_at')

    def payment_link(self, obj):
        url = reverse('admin:payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">Payment #{}</a>', url, obj.payment.id)
    payment_link.short_description = 'Payment'


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('payment_link', 'user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('payment__deal_room__listing__title', 'user__username')
    readonly_fields = ('created_at',)

    def payment_link(self, obj):
        url = reverse('admin:payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">Payment #{}</a>', url, obj.payment.id)
    payment_link.short_description = 'Payment'


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller_link', 'amount', 'status', 'reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('seller__username', 'reference')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

    def seller_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.seller.id])
        return format_html('<a href="{}">{}</a>', url, obj.seller.username)
    seller_link.short_description = 'Seller'


@admin.register(PayoutAccount)
class PayoutAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'account_number', 'is_verified', 'created_at')
    list_filter = ('method', 'is_verified')
    search_fields = ('user__username', 'account_number')
    list_editable = ('is_verified',)


# ---------- NEW: Wallet & Withdrawal Requests ----------
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_link', 'amount', 'transaction_type', 'status', 'description', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('wallet__user__username', 'description', 'reference')
    readonly_fields = ('created_at', 'updated_at')

    def wallet_link(self, obj):
        url = reverse('admin:payments_wallet_change', args=[obj.wallet.id])
        return format_html('<a href="{}">{}</a>', url, obj.wallet.user.username)
    wallet_link.short_description = 'Wallet'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller_link', 'amount', 'method', 'status', 'created_at')
    list_filter = ('status', 'method', 'created_at')
    search_fields = ('seller__username', 'account_details')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

    def seller_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.seller.id])
        return format_html('<a href="{}">{}</a>', url, obj.seller.username)
    seller_link.short_description = 'Seller'