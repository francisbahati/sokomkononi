from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Payment, PaymentMethod, Commission, CommissionRule,
    Transaction, Escrow, Refund, PaymentLog,
    Payout, PayoutAccount  # new
)


# Existing admin registrations (unchanged)...

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'amount', 'status', 'reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('seller__username', 'reference')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PayoutAccount)
class PayoutAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'account_number', 'is_verified', 'created_at')
    list_filter = ('method', 'is_verified')
    search_fields = ('user__username', 'account_number')