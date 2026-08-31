from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import (
    PlatformSettings, CommissionRule, AuditLog, Dispute,
    SystemNotification, AdminActivity,
    Region, Content
)
from .serializers import (
    PlatformSettingsSerializer, CommissionRuleSerializer,
    AuditLogSerializer, DisputeSerializer, DisputeUpdateSerializer,
    SystemNotificationSerializer, AdminActivitySerializer,
    RegionSerializer, ContentSerializer,
    PlatformPaymentMethodSerializer,
)
from .permissions import IsPlatformAdmin, CanManageDisputes, CanViewAuditLogs
from accounts.models import User
from listings.models import Listing, ListingView
from deals.models import DealRoom
from payments.models import Payment, PaymentMethod, Payout


# ---------- Commission Rate ----------
class CommissionRateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rate = PlatformSettings.get_commission_rate()
        return Response({'rate': rate})

    def put(self, request):
        if not request.user.role == 'ADMIN':
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        new_rate = request.data.get('rate')
        if new_rate is None:
            return Response({'error': 'Rate is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rate_val = float(new_rate)
            if rate_val < 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({'error': 'Rate must be a non-negative number.'}, status=status.HTTP_400_BAD_REQUEST)
        PlatformSettings.set_commission_rate(rate_val)
        return Response({'rate': rate_val})


# ---------- Dashboard Stats ----------
class AdminDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    @extend_schema(responses={200: OpenApiResponse(description="Dashboard statistics")})
    def get(self, request):
        total_users = User.objects.count()
        total_dalali = User.objects.filter(role='DALALI').count()
        total_mteja = User.objects.filter(role='MTEJA').count()
        pending_verification = User.objects.filter(role='DALALI', is_verified=False).count()

        total_listings = Listing.objects.count()
        pending_listings = Listing.objects.filter(status='PENDING').count()
        active_listings = Listing.objects.filter(status='ACTIVE').count()
        sold_listings = Listing.objects.filter(status='SOLD').count()

        total_deals = DealRoom.objects.count()
        active_deals = DealRoom.objects.filter(status__in=['NEGOTIATING', 'AGREEMENT', 'PAYMENT_PENDING']).count()
        completed_deals = DealRoom.objects.filter(status='COMPLETED').count()
        disputed_deals = DealRoom.objects.filter(status='DISPUTED').count()

        total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(
            total=Sum('commission')
        )['total'] or 0

        total_transactions = Payment.objects.filter(status='COMPLETED').count()

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


# ---------- Metrics ----------
class AdminMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    @extend_schema(responses={200: OpenApiResponse(description="Metrics for charts")})
    def get(self, request):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_users = User.objects.filter(created_at__gte=thirty_days_ago).count()
        new_listings = Listing.objects.filter(created_at__gte=thirty_days_ago).count()
        completed_deals = DealRoom.objects.filter(
            completed_at__gte=thirty_days_ago,
            status='COMPLETED'
        ).count()
        revenue = Payment.objects.filter(
            completed_at__gte=thirty_days_ago,
            status='COMPLETED'
        ).aggregate(total=Sum('commission'))['total'] or 0

        return Response({
            'new_users': new_users,
            'new_listings': new_listings,
            'completed_deals': completed_deals,
            'revenue': float(revenue)
        })


# ---------- ViewSets ----------
class PlatformSettingsViewSet(viewsets.ModelViewSet):
    queryset = PlatformSettings.objects.all()
    serializer_class = PlatformSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    @action(detail=False, methods=['get'])
    def by_key(self, request):
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
    queryset = CommissionRule.objects.all()
    serializer_class = CommissionRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    @action(detail=False, methods=['get'])
    def get_active_rule(self, request):
        rule = CommissionRule.objects.filter(is_active=True).first()
        if rule:
            return Response(CommissionRuleSerializer(rule).data)
        return Response({'error': 'No active commission rule found'}, status=status.HTTP_404_NOT_FOUND)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAuditLogs]

    def get_queryset(self):
        queryset = super().get_queryset()
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        model_name = self.request.query_params.get('model_name')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset[:100]


class DisputeViewSet(viewsets.ModelViewSet):
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
    queryset = SystemNotification.objects.all()
    serializer_class = SystemNotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def get_active_notifications(self, request):
        now = timezone.now()
        notifications = SystemNotification.objects.filter(
            is_active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
        return Response(SystemNotificationSerializer(notifications, many=True).data)


# ---------- NEW: Reports ----------
class OverviewReportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        active_users = User.objects.filter(is_active=True, status__in=['ACTIVE', 'VERIFIED']).count()
        active_brokers = User.objects.filter(role='DALALI', is_active=True, status__in=['ACTIVE', 'VERIFIED']).count()
        transactions_this_week = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=week_ago
        ).count()
        total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(
            total=Sum('commission')
        )['total'] or 0
        return Response({
            'active_users': active_users,
            'active_brokers': active_brokers,
            'transactions_this_week': transactions_this_week,
            'total_revenue': float(total_revenue)
        })


class RevenueByMonthView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        today = timezone.now()
        results = []
        for i in range(12):
            month = today - timedelta(days=30*i)
            start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = (start + timedelta(days=32)).replace(day=1)
            payments = Payment.objects.filter(
                status='COMPLETED',
                completed_at__gte=start,
                completed_at__lt=end
            )
            commission = payments.aggregate(total=Sum('commission'))['total'] or 0
            deals = payments.count()
            results.append({
                'month': start.strftime('%B %Y'),
                'commission': float(commission),
                'deals': deals
            })
        return Response(results)


class TopListingsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        listings = Listing.objects.order_by('-view_count')[:10]
        return Response([
            {'name': l.title, 'views': l.view_count} for l in listings
        ])


class TopRegionsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        total = Listing.objects.count()
        if total == 0:
            return Response([])
        regions = Listing.objects.values('location').annotate(count=Count('id')).order_by('-count')[:10]
        return Response([
            {'region': r['location'], 'pct': round((r['count'] / total) * 100, 2)}
            for r in regions
        ])


# ---------- NEW: Payment Methods (platform-wide) ----------
class PlatformPaymentMethodListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    serializer_class = PlatformPaymentMethodSerializer
    queryset = PaymentMethod.objects.all()


class PlatformPaymentMethodToggleView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    serializer_class = PlatformPaymentMethodSerializer

    def patch(self, request, name):
        method = get_object_or_404(PaymentMethod, code=name)
        method.is_active = not method.is_active
        method.save()
        serializer = self.get_serializer(method)
        return Response(serializer.data)


# ---------- NEW: Regions ----------
class RegionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class RegionDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    lookup_field = 'name'


# ---------- NEW: Content (Privacy Policy & Terms) ----------
class ContentListView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        privacy = Content.objects.filter(content_type='privacy_policy').first()
        terms = Content.objects.filter(content_type='terms').first()
        return Response({
            'privacy_policy': privacy.content if privacy else '',
            'terms': terms.content if terms else ''
        })


class ContentUpdateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def put(self, request):
        privacy = request.data.get('privacy_policy')
        terms = request.data.get('terms')
        if privacy is None and terms is None:
            return Response({'error': 'At least one field required'}, status=status.HTTP_400_BAD_REQUEST)
        updated = []
        if privacy is not None:
            obj, _ = Content.objects.get_or_create(content_type='privacy_policy')
            obj.content = privacy
            obj.updated_by = request.user
            obj.save()
            updated.append('privacy_policy')
        if terms is not None:
            obj, _ = Content.objects.get_or_create(content_type='terms')
            obj.content = terms
            obj.updated_by = request.user
            obj.save()
            updated.append('terms')
        return Response({'status': 'updated', 'fields': updated})