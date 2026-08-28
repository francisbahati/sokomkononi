from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, Escrow, CommissionRule, Commission

@receiver(post_save, sender=Payment)
def create_commission(sender, instance, created, **kwargs):
    """Create commission record when payment is created"""
    if created:
        rule = CommissionRule.objects.filter(is_active=True).first()
        rate = rule.rate if rule else 5.0
        
        Commission.objects.create(
            payment=instance,
            amount=instance.commission,
            rate=rate
        )

@receiver(pre_save, sender=Payment)
def update_payment_timestamps(sender, instance, **kwargs):
    """Update completed_at when status changes to COMPLETED"""
    if instance.pk:
        old = sender.objects.get(pk=instance.pk)
        if old.status != instance.status and instance.status == 'COMPLETED':
            if not instance.completed_at:
                instance.completed_at = timezone.now()

@receiver(post_save, sender=Escrow)
def update_deal_status_on_escrow(sender, instance, created, **kwargs):
    """Update deal status when escrow changes"""
    if not created:
        if instance.status == 'RELEASED':
            instance.deal_room.status = 'PAYMENT_COMPLETED'
            instance.deal_room.save()
        elif instance.status == 'REFUNDED':
            instance.deal_room.status = 'CANCELLED'
            instance.deal_room.save()