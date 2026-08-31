from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PayoutAccount

User = get_user_model()


@receiver(post_save, sender=User)
def create_payout_account(sender, instance, created, **kwargs):
    """Create a payout account for new Dalali users."""
    if created and instance.role == 'DALALI':
        PayoutAccount.objects.get_or_create(user=instance)