from rest_framework import serializers
from .models import (
    Payment, PaymentMethod, Commission, CommissionRule,
    Transaction, Escrow, Refund, PaymentLog,
    Payout, PayoutAccount,
    Wallet, WalletTransaction, WithdrawalRequest
)
from deals.serializers import DealRoomSerializer
from accounts.serializers import UserProfileSerializer


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'code', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    buyer_details = UserProfileSerializer(source='buyer', read_only=True)
    seller_details = UserProfileSerializer(source='seller', read_only=True)
    deal_room_details = DealRoomSerializer(source='deal_room', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'deal_room', 'deal_room_details', 'buyer', 'buyer_details',
            'seller', 'seller_details', 'amount', 'commission', 'net_amount',
            'payment_method', 'transaction_id', 'status', 'payment_date',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'commission', 'net_amount', 'created_at', 'updated_at']


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['deal_room', 'buyer', 'seller', 'amount', 'payment_method']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

    def validate(self, attrs):
        if attrs.get('buyer') == attrs.get('seller'):
            raise serializers.ValidationError("Buyer and seller cannot be the same")
        rule = CommissionRule.objects.filter(is_active=True).first()
        rate = float(rule.rate) if rule else 5.0
        amount = attrs.get('amount')
        commission = (amount * rate) / 100
        attrs['commission'] = commission
        attrs['net_amount'] = amount - commission
        return attrs


class PaymentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['status', 'transaction_id', 'payment_date']

    def validate_status(self, value):
        if value not in ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED']:
            raise serializers.ValidationError("Invalid status")
        return value


class AdminTransactionSerializer(serializers.ModelSerializer):
    ref = serializers.IntegerField(source='id')
    deal_id = serializers.IntegerField(source='deal_room.id')
    buyer_name = serializers.CharField(source='buyer.username')
    seller_name = serializers.CharField(source='seller.username')
    date = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Payment
        fields = ['ref', 'deal_id', 'buyer_name', 'seller_name', 'amount', 'status', 'date']


class AdminFeeSerializer(serializers.ModelSerializer):
    deal_id = serializers.IntegerField(source='payment.deal_room.id')
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    status = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Commission
        fields = ['deal_id', 'amount', 'status', 'date']

    def get_status(self, obj):
        if obj.payment.status == Payment.Status.COMPLETED:
            return 'Paid'
        return 'Pending'


# ---------- Payout Serializers ----------
class PayoutSerializer(serializers.ModelSerializer):
    seller_details = UserProfileSerializer(source='seller', read_only=True)

    class Meta:
        model = Payout
        fields = [
            'id', 'deal', 'seller', 'seller_details', 'payment',
            'amount', 'status', 'reference', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']


class PayoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['deal', 'seller', 'payment', 'amount']


class AdminPayoutListSerializer(serializers.ModelSerializer):
    ref = serializers.IntegerField(source='id')
    dalali_name = serializers.CharField(source='seller.username')
    date = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Payout
        fields = ['ref', 'dalali_name', 'amount', 'status', 'date']


class PayoutAccountSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)

    class Meta:
        model = PayoutAccount
        fields = [
            'id', 'user', 'user_details', 'method', 'account_number',
            'account_holder', 'bank_name', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'created_at', 'updated_at']


class PayoutAccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutAccount
        fields = ['method', 'account_number', 'account_holder', 'bank_name']


# ---------- Wallet Serializers ----------
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'status', 'description', 'deal', 'reference', 'created_at']


class WalletTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_method = serializers.CharField()  # e.g., 'M_PESA'


class WalletPaySerializer(serializers.Serializer):
    deal_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)


# ---------- Withdrawal Request Serializers ----------
class WithdrawalRequestSerializer(serializers.ModelSerializer):
    seller_details = UserProfileSerializer(source='seller', read_only=True)

    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'seller', 'seller_details', 'amount', 'method', 'account_details', 'status', 'admin_notes', 'processed_at', 'created_at']
        read_only_fields = ['id', 'seller', 'status', 'processed_at', 'created_at']


class WithdrawalRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = ['amount', 'method', 'account_details']


class WithdrawalRequestActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False)


# ---------- Existing Commission/Transaction/Escrow/Refund Serializers ----------
class CommissionSerializer(serializers.ModelSerializer):
    payment_details = PaymentSerializer(source='payment', read_only=True)

    class Meta:
        model = Commission
        fields = ['id', 'payment', 'payment_details', 'amount', 'rate', 'is_paid', 'paid_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'payment', 'transaction_id', 'amount', 'status', 'response_data', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EscrowSerializer(serializers.ModelSerializer):
    buyer_details = UserProfileSerializer(source='buyer', read_only=True)
    seller_details = UserProfileSerializer(source='seller', read_only=True)
    payment_details = PaymentSerializer(source='payment', read_only=True)

    class Meta:
        model = Escrow
        fields = [
            'id', 'deal_room', 'buyer', 'buyer_details', 'seller', 'seller_details',
            'payment', 'payment_details', 'amount', 'status',
            'held_at', 'released_at', 'refunded_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EscrowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escrow
        fields = ['status']


class RefundSerializer(serializers.ModelSerializer):
    processed_by_details = UserProfileSerializer(source='processed_by', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'reason', 'status',
            'processed_by', 'processed_by_details', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'processed_by', 'created_at', 'updated_at']


class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['payment', 'amount', 'reason']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class PaymentLogSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)

    class Meta:
        model = PaymentLog
        fields = ['id', 'payment', 'user', 'user_details', 'action', 'details', 'ip_address', 'created_at']
        read_only_fields = ['id', 'created_at']