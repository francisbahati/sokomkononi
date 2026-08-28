from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Notification,
    UserNotification,
    NotificationTemplate,
    NotificationPreference,
    EmailLog,
    SMSLog,
    PushNotificationLog
)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('Targeting', {
            'fields': ('target_roles', 'target_users'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'notification__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'subject_preview', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active', 'created_at')
    search_fields = ('name', 'subject')
    list_editable = ('is_active',)
    
    def subject_preview(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Subject'

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled')
    list_filter = ('email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient', 'subject')
    readonly_fields = ('sent_at',)
    ordering = ('-sent_at',)

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'message_preview', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('phone_number',)
    readonly_fields = ('sent_at',)
    ordering = ('-sent_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('user__username', 'title')
    readonly_fields = ('sent_at',)
    ordering = ('-sent_at',)