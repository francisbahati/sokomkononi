from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Sum, Count
from django.utils import timezone
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
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
    PaymentMethodSerializer,
    CommissionSerializer,
    CommissionRuleSerializer,
    TransactionSerializer,
    EscrowSerializer,
    EscrowUpdateSerializer,
    RefundSerializer,
    RefundCreateSerializer,
    PaymentLogSerializer
)
from .permissions import (
    IsPaymentParticipant,
    IsPaymentBuyer,
    IsPaymentSeller,
    CanProcessPayment
)

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for payments"""
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
        
        # Admin can see all payments
        if user.role == 'ADMIN':
            return queryset
        
        # Users can only see their own payments
        return queryset.filter(Q(buyer=user) | Q(seller=user))
    
    def perform_create(self, serializer):
        payment = serializer.save()
        
        # Create commission record
        Commission.objects.create(
            payment=payment,
            amount=payment.commission,
            rate=5.00  # Will be dynamic based on rule
        )
        
        # Create escrow
        Escrow.objects.create(
            deal_room=payment.deal_room,
            buyer=payment.buyer,
            seller=payment.seller,
            payment=payment,
            amount=payment.amount,
            status='PENDING'
        )
        
        # Log the payment
        PaymentLog.objects.create(
            payment=payment,
            user=self.request.user,
            action='CREATE',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update payment status"""
        payment = self.get_object()
        
        # Only admin can update status
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admin can update payment status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_status = payment.status
        payment = serializer.save()
        
        # Handle status transitions
        if payment.status == 'COMPLETED' and old_status != 'COMPLETED':
            # Release escrow
            escrow = payment.deal_room.escrow
            escrow.release_funds()
            
            # Update deal status
            payment.deal_room.status = 'PAYMENT_COMPLETED'
            payment.deal_room.save()
        
        # Log the status change
        PaymentLog.objects.create(
            payment=payment,
            user=request.user,
            action='PROCESS' if payment.status == 'PROCESSING' else 'COMPLETE' if payment.status == 'COMPLETED' else 'FAIL',
            details={'old_status': old_status, 'new_status': payment.status},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(PaymentSerializer(payment).data)

class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for payment methods (read-only)"""
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]

class CommissionRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for commission rules"""
    queryset = CommissionRule.objects.all()
    serializer_class = CommissionRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanProcessPayment()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def get_active_rule(self, request):
        """Get the active commission rule"""
        rule = CommissionRule.objects.filter(is_active=True).first()
        if rule:
            return Response(CommissionRuleSerializer(rule).data)
        return Response(
            {'error': 'No active commission rule found'},
            status=status.HTTP_404_NOT_FOUND
        )

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for transactions (read-only)"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role != 'ADMIN':
            # Only show transactions for user's payments
            queryset = queryset.filter(
                Q(payment__buyer=user) | Q(payment__seller=user)
            )
        
        return queryset

class EscrowViewSet(viewsets.ModelViewSet):
    """ViewSet for escrow"""
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
        """Release escrow funds to seller"""
        escrow = self.get_object()
        
        # Check permission
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
        """Refund escrow funds to buyer"""
        escrow = self.get_object()
        
        # Check permission
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
    """ViewSet for refunds"""
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated, CanProcessPayment]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RefundCreateSerializer
        return RefundSerializer
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process a refund"""
        refund = self.get_object()
        
        if refund.status != 'PENDING':
            return Response(
                {'error': 'Refund is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund.processed_by = request.user
        refund.mark_as_completed()
        
        # Update payment status
        refund.payment.mark_as_refunded()
        
        return Response(RefundSerializer(refund).data)

class PaymentWebhookView(generics.GenericAPIView):
    """Webhook for payment providers"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle payment webhook from provider"""
        # Implementation depends on payment provider
        # This is a placeholder
        return Response({'status': 'received'})

class PaymentStatisticsView(generics.GenericAPIView):
    """Get payment statistics"""
    permission_classes = [permissions.IsAuthenticated, CanProcessPayment]
    
    def get(self, request):
        # Total revenue
        total_revenue = Payment.objects.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('commission'))['total'] or 0
        
        # Total payments
        total_payments = Payment.objects.filter(status='COMPLETED').count()
        
        # Payments by method
        payments_by_method = Payment.objects.filter(
            status='COMPLETED'
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Monthly revenue (last 6 months)
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