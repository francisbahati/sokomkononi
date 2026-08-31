from django.contrib import admin
from .models import (
    PlatformSettings, CommissionRule, AuditLog, Dispute,
    SystemNotification, AdminActivity,
    Region, Content
)


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ('setting_key', 'setting_value', 'setting_type', 'updated_at')
    search_fields = ('setting_key', 'setting_value')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('rate', 'is_active')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'ip_address', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'action', 'model_name', 'object_id', 'ip_address')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('id', 'deal_room', 'raised_by', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'resolved_at')
    search_fields = ('raised_by__username', 'deal_room__listing__title', 'description')
    readonly_fields = ('created_at',)


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    list_editable = ('is_active',)


@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target_model', 'target_id', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('admin__username', 'action', 'target_model', 'target_id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'updated_at', 'updated_by')
    readonly_fields = ('updated_at',)