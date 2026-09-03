from rest_framework import generics, status, permissions, viewsets, mixins, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.utils import timezone
from .models import (
    Notification,
    UserNotification,
    NotificationTemplate,
    NotificationPreference,
    SystemNotificationSetting,
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
    SystemNotificationSettingSerializer,
    EmailLogSerializer,
    SMSLogSerializer,
    PushNotificationLogSerializer
)
from .permissions import IsNotificationOwner, CanManageNotifications
from .services import NotificationService

# ---------- Dummy serializer for schema ----------
class EmptySerializer(serializers.Serializer):
    pass


# ---------- Admin System Notification Settings ----------
class SystemNotificationSettingListView(generics.ListAPIView):
    queryset = SystemNotificationSetting.objects.all()
    serializer_class = SystemNotificationSettingSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]


class SystemNotificationSettingToggleView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]
    serializer_class = SystemNotificationSettingSerializer

    def patch(self, request, channel):
        try:
            setting = SystemNotificationSetting.objects.get(channel=channel)
        except SystemNotificationSetting.DoesNotExist:
            return Response({'error': 'Setting not found'}, status=status.HTTP_404_NOT_FOUND)

        setting.is_enabled = not setting.is_enabled
        setting.updated_by = request.user
        setting.save()
        serializer = self.get_serializer(setting)
        return Response(serializer.data)


# ---------- Notification Views ----------
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def perform_create(self, serializer):
        notification = serializer.save()
        if self.request.data.get('send_now', False):
            notification.send()

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        notification = self.get_object()
        notification.send()
        return Response({'status': 'Notification sent'})


class UserNotificationViewSet(viewsets.GenericViewSet,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin):
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
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by('-created_at')


class UnreadCountView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer

    def get(self, request):
        count = UserNotification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class MarkAllReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer

    def post(self, request):
        UserNotification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': 'All notifications marked as read'})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]


class NotificationPreferenceViewSet(viewsets.GenericViewSet,
                                    mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]


class SMSLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SMSLog.objects.all()
    serializer_class = SMSLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]


class PushNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PushNotificationLog.objects.all()
    serializer_class = PushNotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]


class SendNotificationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, CanManageNotifications]
    serializer_class = NotificationCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        notification.send()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)