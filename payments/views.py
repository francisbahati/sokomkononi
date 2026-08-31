from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import (
    Payment, PaymentMethod, Commission, CommissionRule,
    Transaction, Escrow, Refund, PaymentLog,
    Payout, PayoutAccount  # new
)
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, PaymentUpdateSerializer,
    PaymentMethodSerializer,
    AdminTransactionSerializer,
    AdminFeeSerializer,
    AdminPayoutListSerializer,
    PayoutSerializer, PayoutCreateSerializer,
    PayoutAccountSerializer, PayoutAccountUpdateSerializer,
    CommissionSerializer, CommissionRuleSerializer,
    TransactionSerializer, EscrowSerializer, EscrowUpdateSerializer,
    RefundSerializer, RefundCreateSerializer, PaymentLogSerializer
)
from .permissions import (
    IsPaymentParticipant, IsPaymentBuyer, IsPaymentSeller,
    CanProcessPayment
)
from admin_panel.permissions import IsPlatformAdmin  # reuse admin permission


# ---------- Admin Views ----------
class AdminTransactionListView(generics.ListAPIView):
    """Admin: list all payments (transactions) with filters."""
    serializer_class = AdminTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['transaction_id', 'buyer__username', 'seller__username']

    def get_queryset(self):
        queryset = Payment.objects.all().order_by('-created_at')
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class AdminFeeListView(generics.ListAPIView):
    """Admin: list all commissions (fees) with status."""
    serializer_class = AdminFeeSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get_queryset(self):
        return Commission.objects.select_related('payment__deal_room').all().order_by('-created_at')


class AdminPayoutListView(generics.ListAPIView):
    """Admin: list all payouts with filters."""
    serializer_class = AdminPayoutListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get_queryset(self):
        queryset = Payout.objects.all().order_by('-created_at')
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


# ---------- Seller Views ----------
class SellerPayoutListView(generics.ListAPIView):
    """Seller: list their own payouts."""
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(seller=self.request.user).order_by('-created_at')


class SellerPayoutAccountView(generics.RetrieveUpdateAPIView):
    """Seller: get/update their payout account."""
    serializer_class = PayoutAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = PayoutAccount.objects.get_or_create(user=self.request.user)
        return obj

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PayoutAccountUpdateSerializer
        return PayoutAccountSerializer


# ---------- Existing Views (unchanged) ----------
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['update', 'partial_update', 'update_status']:
            return PaymentUpdateSerializer
        return PaymentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'ADMIN':
            return queryset
        return queryset.filter(Q(buyer=user) | Q(seller=user))

    def perform_create(self, serializer):
        payment = serializer.save()
        Commission.objects.create(
            payment=payment,
            amount=payment.commission,
            rate=5.00
        )
        Escrow.objects.create(
            deal_room=payment.deal_room,
            buyer=payment.buyer,
            seller=payment.seller,
            payment=payment,
            amount=payment.amount,
            status='PENDING'
        )
        PaymentLog.objects.create(
            payment=payment,
            user=self.request.user,
            action='CREATE',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        payment = self.get_object()
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admin can update payment status'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_status = payment.status
        payment = serializer.save()
        if payment.status == 'COMPLETED' and old_status != 'COMPLETED':
            escrow = payment.deal_room.escrow
            escrow.release_funds()
            payment.deal_room.status = 'PAYMENT_COMPLETED'
            payment.deal_room.save()
        PaymentLog.objects.create(
            payment=payment,
            user=request.user,
            action='PROCESS' if payment.status == 'PROCESSING' else 'COMPLETE' if payment.status == 'COMPLETED' else 'FAIL',
            details={'old_status': old_status, 'new_status': payment.status},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response(PaymentSerializer(payment).data)


class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]


class CommissionRuleViewSet(viewsets.ModelViewSet):
    queryset = CommissionRule.objects.all()
    serializer_class = CommissionRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanProcessPayment()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def get_active_rule(self, request):
        rule = CommissionRule.objects.filter(is_active=True).first()
        if rule:
            return Response(CommissionRuleSerializer(rule).data)
        return Response({'error': 'No active commission rule found'}, status=status.HTTP_404_NOT_FOUND)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role != 'ADMIN':
            queryset = queryset.filter(Q(payment__buyer=user) | Q(payment__seller=user))
        return queryset


class EscrowViewSet(viewsets.ModelViewSet):
    queryset = Escrow.objects.all()
    serializer_class = EscrowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return EscrowUpdateSerializer
        return EscrowSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role != 'ADMIN':
            queryset = queryset.filter(Q(buyer=user) | Q(seller=user))
        return queryset

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        escrow = self.get_object()
        if request.user.role != 'ADMIN' and request.user != escrow.buyer:
            return Response(
                {'error': 'Only buyer or admin can release funds'},
                status=status.HTTP_403_FORBIDDEN
            )
        if escrow.status != 'HELD':
            return Response(
                {'error': 'Escrow must be in HELD status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        escrow.release_funds()
        PaymentLog.objects.create(
            payment=escrow.payment,
            user=request.user,
            action='RELEASE',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response(EscrowSerializer(escrow).data)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        escrow = self.get_object()
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admin can process refunds'},
                status=status.HTTP_403_FORBIDDEN
            )
        if escrow.status not in ['PENDING', 'HELD']:
            return Response(
                {'error': 'Escrow must be in PENDING or HELD status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        escrow.refund_funds()
        PaymentLog.objects.create(
            payment=escrow.payment,
            user=request.user,
            action='REFUND',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response(EscrowSerializer(escrow).data)


class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated, CanProcessPayment]

    def get_serializer_class(self):
        if self.action == 'create':
            return RefundCreateSerializer
        return RefundSerializer

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        refund = self.get_object()
        if refund.status != 'PENDING':
            return Response(
                {'error': 'Refund is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        refund.processed_by = request.user
        refund.mark_as_completed()
        refund.payment.mark_as_refunded()
        return Response(RefundSerializer(refund).data)


class PaymentWebhookView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Placeholder for payment provider webhook
        return Response({'status': 'received'})


class PaymentStatisticsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, CanProcessPayment]

    def get(self, request):
        total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('commission'))['total'] or 0
        total_payments = Payment.objects.filter(status='COMPLETED').count()
        payments_by_method = Payment.objects.filter(status='COMPLETED').values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        monthly_revenue = []
        for i in range(6):
            month = timezone.now() - timezone.timedelta(days=30*i)
            revenue = Payment.objects.filter(
                status='COMPLETED',
                completed_at__month=month.month,
                completed_at__year=month.year
            ).aggregate(total=Sum('commission'))['total'] or 0
            monthly_revenue.append({
                'month': month.strftime('%B %Y'),
                'revenue': float(revenue)
            })
        return Response({
            'total_revenue': float(total_revenue),
            'total_payments': total_payments,
            'payments_by_method': list(payments_by_method),
            'monthly_revenue': monthly_revenue
        })