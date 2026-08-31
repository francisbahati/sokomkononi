from django.db import models
from django.conf import settings
from django.utils import timezone
from deals.models import DealRoom


class PlatformSettings(models.Model):
    SETTING_TYPES = [
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('DECIMAL', 'Decimal'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON'),
        ('TEXT', 'Text'),
    ]

    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='STRING')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.setting_key} = {self.setting_value}"

    class Meta:
        verbose_name = 'Platform Setting'
        verbose_name_plural = 'Platform Settings'
        ordering = ['setting_key']

    @classmethod
    def get_commission_rate(cls):
        try:
            setting = cls.objects.get(setting_key='commission_rate')
            return float(setting.setting_value)
        except cls.DoesNotExist:
            return 5.0

    @classmethod
    def set_commission_rate(cls, rate):
        setting, created = cls.objects.get_or_create(
            setting_key='commission_rate',
            defaults={
                'setting_value': str(rate),
                'setting_type': 'DECIMAL',
                'description': 'Platform commission rate (%)'
            }
        )
        if not created:
            setting.setting_value = str(rate)
            setting.save()
        return setting


class CommissionRule(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.rate}%"

    class Meta:
        verbose_name = 'Commission Rule'
        verbose_name_plural = 'Commission Rules'
        ordering = ['-is_active', 'name']


class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VERIFY', 'Verify'),
        ('SUSPEND', 'Suspend'),
        ('REJECT', 'Reject'),
        ('APPROVE', 'Approve'),
        ('PAYMENT', 'Payment'),
        ('REFUND', 'Refund'),
        ('DISPUTE', 'Dispute'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
        ]


class Dispute(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected'),
        ('ESCALATED', 'Escalated'),
    ]

    deal_room = models.ForeignKey('deals.DealRoom', on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='raised_disputes')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_disputes'
    )
    resolution_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    def resolve(self, admin_user, notes):
        self.status = 'RESOLVED'
        self.resolved_by = admin_user
        self.resolution_notes = notes
        self.resolved_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Dispute #{self.id} - {self.deal_room} - {self.status}"

    class Meta:
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
        ordering = ['-created_at']


class SystemNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('GENERAL', 'General'),
        ('MAINTENANCE', 'Maintenance'),
        ('UPDATE', 'Update'),
        ('POLICY', 'Policy Change'),
        ('PROMOTION', 'Promotion'),
        ('ALERT', 'Alert'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='GENERAL')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'System Notification'
        verbose_name_plural = 'System Notifications'
        ordering = ['-created_at']


class AdminActivity(models.Model):
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_activities')
    action = models.CharField(max_length=255)
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin}: {self.action} on {self.target_model}"

    class Meta:
        verbose_name = 'Admin Activity'
        verbose_name_plural = 'Admin Activities'
        ordering = ['-created_at']


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Content(models.Model):
    class ContentType(models.TextChoices):
        PRIVACY_POLICY = 'privacy_policy', 'Privacy Policy'
        TERMS = 'terms', 'Terms and Conditions'

    content_type = models.CharField(max_length=20, choices=ContentType.choices, unique=True)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_content'
    )

    def __str__(self):
        return self.get_content_type_display()

    class Meta:
        verbose_name = 'Content'
        verbose_name_plural = 'Content'