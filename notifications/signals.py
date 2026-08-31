from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import NotificationPreference, NotificationTemplate, SystemNotificationSetting
from .services import NotificationService

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.create(user=instance)


@receiver(post_migrate)
def create_default_notification_templates(sender, **kwargs):
    from .models import NotificationTemplate

    templates = {
        'DEAL_CREATED': {
            'name': 'Deal Created',
            'subject': 'New Deal Created: {{ listing_title }}',
            'body': 'A new deal has been created for {{ listing_title }}. You are the {{ role }}.'
        },
        'DEAL_ACCEPTED': {
            'name': 'Deal Accepted',
            'subject': 'Deal Accepted: {{ listing_title }}',
            'body': 'Your deal for {{ listing_title }} has been accepted.'
        },
        'DEAL_COMPLETED': {
            'name': 'Deal Completed',
            'subject': 'Deal Completed: {{ listing_title }}',
            'body': 'Congratulations! The deal for {{ listing_title }} has been completed.'
        },
        'PAYMENT_RECEIVED': {
            'name': 'Payment Received',
            'subject': 'Payment Received: {{ amount }}',
            'body': 'A payment of {{ amount }} has been received for deal {{ listing_title }}.'
        },
        'ESCROW_RELEASED': {
            'name': 'Escrow Released',
            'subject': 'Escrow Released for {{ listing_title }}',
            'body': 'The escrow for {{ listing_title }} has been released.'
        },
        'LISTING_VERIFIED': {
            'name': 'Listing Verified',
            'subject': 'Listing Verified: {{ listing_title }}',
            'body': 'Your listing "{{ listing_title }}" has been verified and is now active.'
        },
        'KYC_VERIFIED': {
            'name': 'KYC Verified',
            'subject': 'KYC Verification Approved',
            'body': 'Your KYC verification has been approved. You can now list properties.'
        },
        'NEW_MESSAGE': {
            'name': 'New Message',
            'subject': 'New Message in Deal: {{ listing_title }}',
            'body': 'You have a new message from {{ sender }} in the deal for {{ listing_title }}.'
        },
        'NEW_OFFER': {
            'name': 'New Offer',
            'subject': 'New Offer for {{ listing_title }}',
            'body': 'You have a new offer of {{ amount }} for {{ listing_title }}.'
        }
    }

    for key, data in templates.items():
        NotificationTemplate.objects.get_or_create(
            notification_type=key,
            defaults={
                'name': data['name'],
                'subject': data['subject'],
                'body': data['body'],
                'is_active': True
            }
        )

    # Create default system notification settings
    channels = ['email', 'sms', 'push', 'in_app']
    for channel in channels:
        SystemNotificationSetting.objects.get_or_create(
            channel=channel,
            defaults={'is_enabled': True}
        )