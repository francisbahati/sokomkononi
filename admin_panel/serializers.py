from rest_framework import serializers
from django.utils import timezone
from .models import (
    PlatformSettings, CommissionRule, AuditLog, Dispute,
    SystemNotification, AdminActivity,
    Region, Content
)
from accounts.serializers import UserProfileSerializer


class PlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSettings
        fields = ['id', 'setting_key', 'setting_value', 'setting_type', 'description', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class CommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRule
        fields = ['id', 'name', 'rate', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    user_details = UserProfileSerializer(source='user', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_details', 'action', 'model_name',
                  'object_id', 'data', 'ip_address', 'created_at']
        read_only_fields = ['id', 'user', 'user_details', 'action', 'model_name',
                            'object_id', 'data', 'ip_address', 'created_at']


class DisputeSerializer(serializers.ModelSerializer):
    raised_by_details = UserProfileSerializer(source='raised_by', read_only=True)
    resolved_by_details = UserProfileSerializer(source='resolved_by', read_only=True)

    class Meta:
        model = Dispute
        fields = ['id', 'deal_room', 'raised_by', 'raised_by_details', 'description',
                  'status', 'resolved_by', 'resolved_by_details', 'resolution_notes',
                  'created_at', 'resolved_at']
        read_only_fields = ['id', 'raised_by', 'created_at']


class DisputeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = ['status', 'resolution_notes']

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.resolution_notes = validated_data.get('resolution_notes', instance.resolution_notes)
        if instance.status == 'RESOLVED' and not instance.resolved_at:
            instance.resolved_at = timezone.now()
            instance.resolved_by = self.context.get('request').user
        instance.save()
        return instance


class SystemNotificationSerializer(serializers.ModelSerializer):
    created_by_details = UserProfileSerializer(source='created_by', read_only=True)

    class Meta:
        model = SystemNotification
        fields = ['id', 'title', 'message', 'notification_type', 'is_active',
                  'start_date', 'end_date', 'created_by', 'created_by_details', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class AdminActivitySerializer(serializers.ModelSerializer):
    admin_details = UserProfileSerializer(source='admin', read_only=True)

    class Meta:
        model = AdminActivity
        fields = ['id', 'admin', 'admin_details', 'action', 'target_model',
                  'target_id', 'details', 'ip_address', 'created_at']
        read_only_fields = ['id', 'admin', 'admin_details', 'action', 'target_model',
                            'target_id', 'details', 'ip_address', 'created_at']


# ---------- NEW SERIALIZERS ----------
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ContentSerializer(serializers.ModelSerializer):
    updated_by_details = UserProfileSerializer(source='updated_by', read_only=True)

    class Meta:
        model = Content
        fields = ['content_type', 'content', 'updated_at', 'updated_by', 'updated_by_details']
        read_only_fields = ['updated_at', 'updated_by']


# PaymentMethod serializer – we'll import from payments app in views
# But we define a placeholder to avoid circular imports
class PlatformPaymentMethodSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
    is_active = serializers.BooleanField()


# Report serializers (used for validation/documentation)
class OverviewReportSerializer(serializers.Serializer):
    active_users = serializers.IntegerField()
    active_brokers = serializers.IntegerField()
    transactions_this_week = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)


class RevenueByMonthSerializer(serializers.Serializer):
    month = serializers.CharField()
    commission = serializers.DecimalField(max_digits=15, decimal_places=2)
    deals = serializers.IntegerField()


class TopListingSerializer(serializers.Serializer):
    name = serializers.CharField()
    views = serializers.IntegerField()


class TopRegionSerializer(serializers.Serializer):
    region = serializers.CharField()
    pct = serializers.FloatField()