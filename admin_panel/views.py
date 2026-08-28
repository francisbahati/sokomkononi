from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import (
    PlatformSettings, 
    CommissionRule, 
    AuditLog, 
    Dispute,
    SystemNotification,
    AdminActivity
)
from .serializers import (
    PlatformSettingsSerializer,
    CommissionRuleSerializer,
    AuditLogSerializer,
    DisputeSerializer,
    DisputeUpdateSerializer,
    SystemNotificationSerializer,
    AdminActivitySerializer
)
from .permissions import IsPlatformAdmin, CanManageDisputes, CanViewAuditLogs
from accounts.models import User
from listings.models import Listing
from deals.models import DealRoom
from payments.models import Payment

class AdminDashboardStatsView(generics.GenericAPIView):
    """Get admin dashboard statistics"""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    
    def get(self, request):
        # User statistics
        total_users = User.objects.count()
        total_dalali = User.objects.filter(role='DALALI').count()
        total_mteja = User.objects.filter(role='MTEJA').count()
        pending_verification = User.objects.filter(role='DALALI', is_verified=False).count()
        
        # Listing statistics
        total_listings = Listing.objects.count()
        pending_listings = Listing.objects.filter(status='PENDING').count()
        active_listings = Listing.objects.filter(status='ACTIVE').count()
        sold_listings = Listing.objects.filter(status='SOLD').count()
        
        # Deal statistics
        total_deals = DealRoom.objects.count()
        active_deals = DealRoom.objects.filter(status__in=['NEGOTIATING', 'AGREEMENT', 'PAYMENT_PENDING']).count()
        completed_deals = DealRoom.objects.filter(status='COMPLETED').count()
        disputed_deals = DealRoom.objects.filter(status='DISPUTED').count()
        
        # Payment statistics
        total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(
            total=Sum('commission')
        )['total'] or 0
        
        total_transactions = Payment.objects.filter(status='COMPLETED').count()
        
        # Recent disputes
        recent_disputes = Dispute.objects.filter(status__in=['OPEN', 'INVESTIGATING']).order_by('-created_at')[:5]
        
        return Response({
            'users': {
                'total': total_users,
                'dalali': total_dalali,
                'mteja': total_mteja,
                'pending_verification': pending_verification
            },
            'listings': {
                'total': total_listings,
                'pending': pending_listings,
                'active': active_listings,
                'sold': sold_listings
            },
            'deals': {
                'total': total_deals,
                'active': active_deals,
                'completed': completed_deals,
                'disputed': disputed_deals
            },
            'payments': {
                'total_revenue': float(total_revenue),
                'total_transactions': total_transactions
            },
            'recent_disputes': DisputeSerializer(recent_disputes, many=True).data
        })

class AdminMetricsView(generics.GenericAPIView):
    """Get admin metrics for charts"""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    
    def get(self, request):
        # Get metrics for the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        # New users per day
        new_users = User.objects.filter(created_at__gte=thirty_days_ago)
        
        # New listings per day
        new_listings = Listing.objects.filter(created_at__gte=thirty_days_ago)
        
        # Completed deals per day
        completed_deals = DealRoom.objects.filter(
            completed_at__gte=thirty_days_ago,
            status='COMPLETED'
        )
        
        # Revenue per day
        revenue = Payment.objects.filter(
            completed_at__gte=thirty_days_ago,
            status='COMPLETED'
        )
        
        return Response({
            'new_users': new_users.count(),
            'new_listings': new_listings.count(),
            'completed_deals': completed_deals.count(),
            'revenue': float(revenue.aggregate(total=Sum('commission'))['total'] or 0)
        })

class PlatformSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for platform settings"""
    queryset = PlatformSettings.objects.all()
    serializer_class = PlatformSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    
    @action(detail=False, methods=['get'])
    def by_key(self, request):
        """Get setting by key"""
        key = request.query_params.get('key')
        if not key:
            return Response({'error': 'Key parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            setting = PlatformSettings.objects.get(setting_key=key)
            serializer = self.get_serializer(setting)
            return Response(serializer.data)
        except PlatformSettings.DoesNotExist:
            return Response({'error': 'Setting not found'}, status=status.HTTP_404_NOT_FOUND)

class CommissionRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for commission rules"""
    queryset = CommissionRule.objects.all()
    serializer_class = CommissionRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    
    @action(detail=False, methods=['get'])
    def get_active_rule(self, request):
        """Get the active commission rule"""
        rule = CommissionRule.objects.filter(is_active=True).first()
        if rule:
            return Response(CommissionRuleSerializer(rule).data)
        return Response({'error': 'No active commission rule found'}, status=status.HTTP_404_NOT_FOUND)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit logs (read-only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAuditLogs]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by model
        model_name = self.request.query_params.get('model_name')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset[:100]  # Limit to 100 most recent

class DisputeViewSet(viewsets.ModelViewSet):
    """ViewSet for disputes"""
    queryset = Dispute.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanManageDisputes]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return DisputeUpdateSerializer
        return DisputeSerializer
    
    def perform_create(self, serializer):
        serializer.save(raised_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a dispute"""
        dispute = self.get_object()
        serializer = DisputeUpdateSerializer(
            dispute, 
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Dispute resolved successfully',
            'dispute': DisputeSerializer(dispute).data
        })

class SystemNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for system notifications"""
    queryset = SystemNotification.objects.all()
    serializer_class = SystemNotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def get_active_notifications(self, request):
        """Get active notifications for users"""
        now = timezone.now()
        notifications = SystemNotification.objects.filter(
            is_active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
        return Response(SystemNotificationSerializer(notifications, many=True).data)