from rest_framework import serializers
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
from accounts.serializers import UserProfileSerializer

class NotificationSerializer(serializers.ModelSerializer):
    target_users_details = UserProfileSerializer(source='target_users', many=True, read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'is_active',
            'target_roles', 'target_users', 'target_users_details',
            'sent_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sent_at', 'created_at', 'updated_at']

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'target_roles', 'target_users']
    
    def validate(self, attrs):
        # Ensure at least one target is specified
        if not attrs.get('target_roles') and not attrs.get('target_users'):
            raise serializers.ValidationError(
                "At least one target (roles or users) must be specified"
            )
        return attrs

class UserNotificationSerializer(serializers.ModelSerializer):
    notification_details = NotificationSerializer(source='notification', read_only=True)
    user_details = UserProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = UserNotification
        fields = [
            'id', 'user', 'user_details', 'notification', 'notification_details',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserNotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = ['is_read']
    
    def update(self, instance, validated_data):
        if validated_data.get('is_read') and not instance.is_read:
            instance.read_at = timezone.now()
        return super().update(instance, validated_data)

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'name', 'notification_type', 'subject', 'body', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_details',
            'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
            'deal_updates', 'payment_updates', 'listing_updates',
            'system_alerts', 'promotions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = ['id', 'recipient', 'subject', 'body', 'status', 'error_message', 'sent_at', 'created_at']
        read_only_fields = ['id', 'created_at']

class SMSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSLog
        fields = ['id', 'phone_number', 'message', 'status', 'error_message', 'sent_at', 'created_at']
        read_only_fields = ['id', 'created_at']

class PushNotificationLogSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)
    
    class Meta:
        model = PushNotificationLog
        fields = ['id', 'user', 'user_details', 'title', 'body', 'status', 'error_message', 'sent_at', 'created_at']
        read_only_fields = ['id', 'created_at']