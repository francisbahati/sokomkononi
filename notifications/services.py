from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import (
    Notification,
    UserNotification,
    NotificationTemplate,
    EmailLog,
    SMSLog,
    PushNotificationLog
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationService:
    """Service for sending notifications"""
    
    @classmethod
    def send_notification(cls, notification):
        """Send a notification to all targeted users"""
        target_users = cls.get_target_users(notification)
        
        for user in target_users:
            user_notif = UserNotification.objects.create(
                user=user,
                notification=notification
            )
            
            pref = user.notification_preferences if hasattr(user, 'notification_preferences') else None
            
            if pref and pref.email_enabled:
                cls.send_email(user, notification)
            if pref and pref.sms_enabled:
                cls.send_sms(user, notification)
            if pref and pref.push_enabled:
                cls.send_push(user, notification)
        
        notification.sent_at = timezone.now()
        notification.save()
    
    @classmethod
    def get_target_users(cls, notification):
        users = set()
        for user in notification.target_users.all():
            users.add(user)
        for role in notification.target_roles:
            users.update(User.objects.filter(role=role))
        return list(users)
    
    @classmethod
    def send_email(cls, user, notification):
        try:
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            EmailLog.objects.create(
                recipient=user.email,
                subject=notification.title,
                body=notification.message,
                status='SENT',
                sent_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            EmailLog.objects.create(
                recipient=user.email,
                subject=notification.title,
                body=notification.message,
                status='FAILED',
                error_message=str(e)
            )
    
    @classmethod
    def send_sms(cls, user, notification):
        try:
            SMSLog.objects.create(
                phone_number=user.phone_number,
                message=notification.message,
                status='SENT',
                sent_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to send SMS to {user.phone_number}: {str(e)}")
            SMSLog.objects.create(
                phone_number=user.phone_number,
                message=notification.message,
                status='FAILED',
                error_message=str(e)
            )
    
    @classmethod
    def send_push(cls, user, notification):
        try:
            PushNotificationLog.objects.create(
                user=user,
                title=notification.title,
                body=notification.message,
                status='SENT',
                sent_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to send push to {user.username}: {str(e)}")
            PushNotificationLog.objects.create(
                user=user,
                title=notification.title,
                body=notification.message,
                status='FAILED',
                error_message=str(e)
            )
    
    @classmethod
    def send_notification_to_user(cls, user, notification_type, context):
        try:
            template = NotificationTemplate.objects.get(notification_type=notification_type, is_active=True)
            rendered = template.render(context)
            notification = Notification.objects.create(
                title=rendered['subject'],
                message=rendered['body'],
                notification_type=notification_type.split('_')[0] if '_' in notification_type else 'GENERAL'
            )
            notification.target_users.add(user)
            notification.send()
            return notification
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template for {notification_type} not found")
            return None