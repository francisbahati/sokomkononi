from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import DealRoom, NegotiationMessage, DealActivity

@receiver(post_save, sender=NegotiationMessage)
def handle_negotiation_message(sender, instance, created, **kwargs):
    """Handle actions after a negotiation message is created"""
    if created:
        # Update deal room based on offers
        if instance.is_offer:
            deal = instance.deal_room
            if instance.sender == deal.buyer:
                deal.buyer_offer = instance.offer_amount
            elif instance.sender == deal.seller:
                deal.seller_counter = instance.offer_amount
            deal.save()
        
        # Create activity log
        DealActivity.objects.create(
            deal_room=instance.deal_room,
            user=instance.sender,
            action='OFFER' if instance.is_offer else 'MESSAGE',
            details={
                'message': instance.message,
                'offer_amount': str(instance.offer_amount) if instance.is_offer else None
            }
        )

@receiver(pre_save, sender=DealRoom)
def track_deal_status_changes(sender, instance, **kwargs):
    """Track status changes for deals"""
    if instance.pk:
        old = sender.objects.get(pk=instance.pk)
        if old.status != instance.status:
            # Status is changing
            pass