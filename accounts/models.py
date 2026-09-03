from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DALALI = 'DALALI', 'Dalali'
        MTEJA = 'MTEJA', 'Mteja'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PENDING = 'pending', 'Pending'
        SUSPENDED = 'suspended', 'Suspended'
        BLOCKED = 'blocked', 'Blocked'

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_permissions_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MTEJA)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    is_verified = models.BooleanField(default=False)
    id_card_number = models.CharField(max_length=20, blank=True, null=True)
    id_card_photo = models.ImageField(upload_to='kyc/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # Email verification flag
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role', 'status']),
            models.Index(fields=['phone_number']),
        ]

    @classmethod
    def get_by_contact(cls, contact):
        if not contact:
            return None
        user = cls.objects.filter(phone_number=contact).first()
        if user:
            return user
        return cls.objects.filter(email=contact).first()


class OTP(models.Model):
    PURPOSE_CHOICES = [
        ('login', 'Login'),
        ('verify', 'Verify Email'),
        ('reset', 'Reset Password'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email} - {self.purpose}"


class UserFavorite(models.Model):
    """Wishlist / favorites for listings."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} fav {self.listing.title}"