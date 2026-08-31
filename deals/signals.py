from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .models import DealRoom


@receiver(post_save, sender=DealRoom)
def handle_deal_completion(sender, instance, created, **kwargs):
    """
    When a deal is marked as COMPLETED, create a Payment and a Payout record.
    Uses apps.get_model() to avoid import errors if the payment models don't exist yet.
    """
    if not created and instance.status == DealRoom.Status.COMPLETED:
        # Dynamically get the Payment model
        Payment = apps.get_model('payments', 'Payment')
        # Avoid duplicate creation
        if Payment.objects.filter(deal=instance).exists():
            return

        # Create Payment (buyer → platform)
        Payment.objects.create(
            deal=instance,
            buyer=instance.buyer,
            seller=instance.seller,
            amount=instance.final_price,
            commission=instance.commission_amount,
            status='COMPLETED',
            completed_at=instance.completed_at
        )

        # Create Payout (platform → seller)
        Payout = apps.get_model('payments', 'Payout')
        Payout.objects.create(
            deal=instance,
            seller=instance.seller,
            amount=instance.final_price - instance.commission_amount,
            status='PENDING',
            created_at=instance.completed_at
        )