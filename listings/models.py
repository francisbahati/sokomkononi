from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import datetime


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Listing(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        ACTIVE = 'ACTIVE', 'Active'
        SOLD = 'SOLD', 'Sold'
        REJECTED = 'REJECTED', 'Rejected'
        INACTIVE = 'INACTIVE', 'Inactive'

    class PropertyType(models.TextChoices):
        LAND = 'LAND', 'Land'
        HOUSE = 'HOUSE', 'House'
        APARTMENT = 'APARTMENT', 'Apartment'
        COMMERCIAL = 'COMMERCIAL', 'Commercial'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='listings')

    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    price = models.DecimalField(max_digits=15, decimal_places=2)
    size = models.DecimalField(max_digits=10, decimal_places=2, help_text="Size in square meters")
    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)

    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_featured = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)   # <-- NEW

    main_image = models.ImageField(upload_to='listings/main/', blank=True, null=True)

    view_count = models.PositiveIntegerField(default=0)

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_listings'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    listing_id = models.CharField(max_length=20, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.listing_id:
            year = datetime.datetime.now().year
            random_num = random.randint(1000, 9999)
            self.listing_id = f"LIST-{year}-{random_num}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.listing_id} - {self.title}"

    def get_primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary.image
        return self.main_image

    def get_all_images(self):
        return self.images.all().order_by('order')

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'property_type']),
            models.Index(fields=['price']),
            models.Index(fields=['listing_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['seller', 'status']),
        ]


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/gallery/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.listing.title}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ListingImage.objects.filter(
                listing=self.listing,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order', 'created_at']


class SavedSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    search_params = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    class Meta:
        ordering = ['-created_at']


class ListingView(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.listing.listing_id} viewed by {self.ip_address}"

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['listing', 'viewed_at']),
        ]