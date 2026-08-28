from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AuditLog, AdminActivity
from django.utils import timezone

User = get_user_model()

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Log user creation"""
    if created:
        AuditLog.objects.create(
            user=instance,
            action='CREATE',
            model_name='User',
            object_id=instance.id,
            data={'username': instance.username, 'role': instance.role}
        )

@receiver(post_save, sender=User)
def log_user_update(sender, instance, created, **kwargs):
    """Log user updates"""
    if not created:
        AuditLog.objects.create(
            user=instance,
            action='UPDATE',
            model_name='User',
            object_id=instance.id,
            data={'username': instance.username, 'is_verified': instance.is_verified}
        )