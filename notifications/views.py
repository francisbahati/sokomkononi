from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import (
    Notification,
    UserNotification,
    NotificationTemplate,
    NotificationPreference,
    EmailLog,
    SMSLog,
    PushNotificationLog
)
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    UserNotificationSerializer,
    UserNotificationUpdateSerializer,
    NotificationTemplateSerializer,
    NotificationPreferenceSerializer,
    EmailLogSerializer,
    SMSLogSerializer,
    PushNotificationLogSerializer
)
from .permissions import IsNotificationOwner, CanManageNotifications
from .services import NotificationService

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for system notifications"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    def perform_create(self, serializer):
        notification = serializer.save()
        # Optionally send immediately
        if self.request.data.get('send_now', False):
            notification.send()
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send notification to users"""
        notification = self.get_object()
        notification.send()
        return Response({'status': 'Notification sent'})

class UserNotificationViewSet(viewsets.GenericViewSet,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin):
    """ViewSet for user-specific notifications"""
    queryset = UserNotification.objects.all()
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotificationOwner]
    
    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserNotificationUpdateSerializer
        return UserNotificationSerializer

class MyNotificationsView(generics.ListAPIView):
    """Get all notifications for current user"""
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by('-created_at')

class UnreadCountView(generics.GenericAPIView):
    """Get unread notification count"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        count = UserNotification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

class MarkAllReadView(generics.GenericAPIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        UserNotification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': 'All notifications marked as read'})

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for notification templates"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]

class NotificationPreferenceViewSet(viewsets.GenericViewSet,
                                    mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin):
    """ViewSet for user notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj

class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for email logs (admin only)"""
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]

class SMSLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SMS logs (admin only)"""
    queryset = SMSLog.objects.all()
    serializer_class = SMSLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]

class PushNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for push notification logs (admin only)"""
    queryset = PushNotificationLog.objects.all()
    serializer_class = PushNotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]

class SendNotificationView(generics.GenericAPIView):
    """Send notification to users (admin only)"""
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]
    serializer_class = NotificationCreateSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        notification.send()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)