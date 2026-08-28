from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Define roles using TextChoices
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DALALI = 'DALALI', 'Dalali'
        MTEJA = 'MTEJA', 'Mteja'
    
    # Fix reverse accessor clash
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
    
    # Required fields from project specification
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MTEJA)
    
    # KYC fields
    is_verified = models.BooleanField(default=False)
    id_card_number = models.CharField(max_length=20, blank=True, null=True)
    id_card_photo = models.ImageField(upload_to='kyc/', blank=True, null=True)
    
    # Account status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional profile fields
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role', 'is_verified']),
            models.Index(fields=['phone_number']),
        ]