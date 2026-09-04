from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import JSONField


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        DEAL = 'DEAL', 'Deal Update'
        PAYMENT = 'PAYMENT', 'Payment Update'
        LISTING = 'LISTING', 'Listing Update'
        KYC = 'KYC', 'KYC Update'
        PROMOTION = 'PROMOTION', 'Promotion'
        ALERT = 'ALERT', 'Alert'
        SYSTEM = 'SYSTEM', 'System'

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.GENERAL)
    is_active = models.BooleanField(default=True)

    target_roles = JSONField(default=list, blank=True, help_text="List of user roles to target")
    target_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='targeted_notifications')

    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def send(self):
        from .services import NotificationService
        NotificationService.send_notification(self)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type', 'is_active']),
            models.Index(fields=['created_at']),
        ]


class UserNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='user_notifications')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['user', 'notification']


class NotificationTemplate(models.Model):
    class NotificationType(models.TextChoices):
        DEAL_CREATED = 'DEAL_CREATED', 'Deal Created'
        DEAL_ACCEPTED = 'DEAL_ACCEPTED', 'Deal Accepted'
        DEAL_REJECTED = 'DEAL_REJECTED', 'Deal Rejected'
        DEAL_COMPLETED = 'DEAL_COMPLETED', 'Deal Completed'
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
        PAYMENT_COMPLETED = 'PAYMENT_COMPLETED', 'Payment Completed'
        ESCROW_RELEASED = 'ESCROW_RELEASED', 'Escrow Released'
        LISTING_VERIFIED = 'LISTING_VERIFIED', 'Listing Verified'
        LISTING_REJECTED = 'LISTING_REJECTED', 'Listing Rejected'
        KYC_VERIFIED = 'KYC_VERIFIED', 'KYC Verified'
        KYC_REJECTED = 'KYC_REJECTED', 'KYC Rejected'
        DISPUTE_RAISED = 'DISPUTE_RAISED', 'Dispute Raised'
        DISPUTE_RESOLVED = 'DISPUTE_RESOLVED', 'Dispute Resolved'
        NEW_MESSAGE = 'NEW_MESSAGE', 'New Message'
        NEW_OFFER = 'NEW_OFFER', 'New Offer'

    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def render(self, context):
        from django.template import Template, Context
        subject_template = Template(self.subject)
        body_template = Template(self.body)
        context = Context(context)
        return {
            'subject': subject_template.render(context),
            'body': body_template.render(context)
        }

    class Meta:
        ordering = ['name']


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')

    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)

    deal_updates = models.BooleanField(default=True)
    payment_updates = models.BooleanField(default=True)
    listing_updates = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    promotions = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"


class SystemNotificationSetting(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        PUSH = 'push', 'Push'
        IN_APP = 'in_app', 'In-App'

    channel = models.CharField(max_length=10, choices=Channel.choices, unique=True)
    is_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_notification_settings'
    )

    def __str__(self):
        return f"{self.get_channel_display()}: {'Enabled' if self.is_enabled else 'Disabled'}"

    class Meta:
        verbose_name = 'System Notification Setting'
        verbose_name_plural = 'System Notification Settings'


class EmailLog(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email to {self.recipient} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class SMSLog(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class PushNotificationLog(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_logs')
    title = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push to {self.user.username} - {self.status}"

    class Meta:
        ordering = ['-created_at']