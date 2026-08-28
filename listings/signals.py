from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Listing, ListingView
from admin_panel.models import AuditLog

@receiver(pre_save, sender=Listing)
def set_verification_status(sender, instance, **kwargs):
    """Auto-set verification fields when status changes"""
    if instance.pk:
        old = sender.objects.get(pk=instance.pk)
        if old.status != instance.status and instance.status == 'VERIFIED':
            if not instance.verified_at:
                instance.verified_at = timezone.now()

@receiver(post_save, sender=Listing)
def log_listing_changes(sender, instance, created, **kwargs):
    """Log listing changes for audit"""
    if created:
        AuditLog.objects.create(
            user=instance.seller,
            action='CREATE',
            model_name='Listing',
            object_id=instance.id,
            data={'listing_id': instance.listing_id, 'title': instance.title}
        )