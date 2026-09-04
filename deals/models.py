from django.db import models
from django.conf import settings
from django.utils import timezone
from listings.models import Listing


class DealRoom(models.Model):
    class Status(models.TextChoices):
        NEGOTIATING = 'NEGOTIATING', 'Negotiating'
        AGREEMENT = 'AGREEMENT', 'Agreement Reached'
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
        PAYMENT_COMPLETED = 'PAYMENT_COMPLETED', 'Payment Completed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        DISPUTED = 'DISPUTED', 'Disputed'

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='deals')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deals_as_buyer')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deals_as_seller')

    original_price = models.DecimalField(max_digits=15, decimal_places=2)
    final_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    buyer_offer = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    seller_counter = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEGOTIATING)
    commission_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Deal: {self.listing.listing_id} - {self.buyer.username}"

    def get_final_price(self):
        return self.final_price or self.original_price

    def calculate_commission(self, rate=5.0):
        price = self.get_final_price()
        return (price * rate) / 100

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        # Calculate commission using current platform rate
        from admin_panel.models import PlatformSettings
        rate = PlatformSettings.get_commission_rate()
        self.commission_amount = self.calculate_commission(rate)
        self.save()

    def mark_as_cancelled(self):
        self.status = self.Status.CANCELLED
        self.save()

    def mark_as_disputed(self):
        self.status = self.Status.DISPUTED
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['buyer', 'seller']),
        ]


class Offer(models.Model):
    """Individual offer made by either party in a deal room."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    deal_room = models.ForeignKey(DealRoom, on_delete=models.CASCADE, related_name='offers')
    made_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def accept(self):
        self.status = self.Status.ACCEPTED
        self.save()
        # Update deal room with final price and status
        deal = self.deal_room
        deal.final_price = self.amount
        deal.status = DealRoom.Status.AGREEMENT
        deal.save()

    def reject(self):
        self.status = self.Status.REJECTED
        self.save()

    def __str__(self):
        return f"Offer {self.amount} by {self.made_by.username} on {self.deal_room}"


class NegotiationMessage(models.Model):
    deal_room = models.ForeignKey(DealRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_offer = models.BooleanField(default=False)
    offer_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} in {self.deal_room}"

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['deal_room', 'created_at']),
            models.Index(fields=['sender']),
        ]


class DealDocument(models.Model):
    DOCUMENT_TYPES = [
        ('CONTRACT', 'Contract'),
        ('AGREEMENT', 'Agreement'),
        ('INVOICE', 'Invoice'),
        ('RECEIPT', 'Receipt'),
        ('OTHER', 'Other'),
    ]
    deal_room = models.ForeignKey(DealRoom, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='OTHER')
    file = models.FileField(upload_to='deal_documents/')
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.deal_room}"

    class Meta:
        ordering = ['-uploaded_at']


class DealActivity(models.Model):
    ACTION_TYPES = [
        ('MESSAGE', 'Message'),
        ('OFFER', 'Offer'),
        ('COUNTER', 'Counter Offer'),
        ('ACCEPT', 'Accept'),
        ('REJECT', 'Reject'),
        ('PAYMENT', 'Payment'),
        ('COMPLETE', 'Complete'),
        ('CANCEL', 'Cancel'),
        ('DISPUTE', 'Dispute'),
    ]
    deal_room = models.ForeignKey(DealRoom, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.deal_room}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deal_room', 'created_at']),
        ]