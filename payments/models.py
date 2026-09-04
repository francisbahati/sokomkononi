from django.db import models
from django.conf import settings
from django.utils import timezone
from deals.models import DealRoom


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    class PaymentMethodChoice(models.TextChoices):
        M_PESA = 'M_PESA', 'M-Pesa'
        TIGO_PESA = 'TIGO_PESA', 'Tigo Pesa'
        AIRTEL_MONEY = 'AIRTEL_MONEY', 'Airtel Money'
        BANK = 'BANK', 'Bank Transfer'
        CARD = 'CARD', 'Card Payment'

    deal_room = models.ForeignKey(DealRoom, on_delete=models.CASCADE, related_name='payments')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_as_buyer')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_as_seller')

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    commission = models.DecimalField(max_digits=15, decimal_places=2)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PaymentMethodChoice.choices)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.deal_room} - {self.amount}"

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self):
        self.status = self.Status.FAILED
        self.save()

    def mark_as_refunded(self):
        self.status = self.Status.REFUNDED
        self.save()

    def calculate_commission(self, rate=5.0):
        return (self.amount * rate) / 100

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['buyer', 'seller']),
        ]


class Commission(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='commission_record')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission for {self.payment} - {self.amount}"

    class Meta:
        ordering = ['-created_at']


class CommissionRule(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.rate}%"

    class Meta:
        verbose_name = 'Commission Rule'
        verbose_name_plural = 'Commission Rules'
        ordering = ['-is_active', 'name']


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    response_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]


class Escrow(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        HELD = 'HELD', 'Held'
        RELEASED = 'RELEASED', 'Released'
        REFUNDED = 'REFUNDED', 'Refunded'

    deal_room = models.OneToOneField(DealRoom, on_delete=models.CASCADE, related_name='escrow')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escrow_as_buyer')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escrow_as_seller')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='escrow_payments')

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    held_at = models.DateTimeField(blank=True, null=True)
    released_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Escrow for {self.deal_room} - {self.amount}"

    def hold_funds(self):
        self.status = self.Status.HELD
        self.held_at = timezone.now()
        self.save()

    def release_funds(self):
        self.status = self.Status.RELEASED
        self.released_at = timezone.now()
        self.save()

    def refund_funds(self):
        self.status = self.Status.REFUNDED
        self.refunded_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]


class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='processed_refunds')
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund for {self.payment} - {self.amount}"

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']


class PaymentLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        PROCESS = 'PROCESS', 'Process'
        COMPLETE = 'COMPLETE', 'Complete'
        FAIL = 'FAIL', 'Fail'
        REFUND = 'REFUND', 'Refund'
        RELEASE = 'RELEASE', 'Release'
        HOLD = 'HOLD', 'Hold'

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment} - {self.action} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'action']),
            models.Index(fields=['created_at']),
        ]


# ---------- NEW: Payout (platform → seller) ----------
class Payout(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        PROCESSING = 'PROCESSING', 'Processing'

    deal = models.ForeignKey(DealRoom, on_delete=models.CASCADE, related_name='payouts')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payouts')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='payouts', null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout for {self.seller.username} - {self.amount}"

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self):
        self.status = self.Status.FAILED
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['seller']),
        ]


# ---------- NEW: Seller's payout account ----------
class PayoutAccount(models.Model):
    class Method(models.TextChoices):
        M_PESA = 'M_PESA', 'M-Pesa'
        TIGO_PESA = 'TIGO_PESA', 'Tigo Pesa'
        AIRTEL_MONEY = 'AIRTEL_MONEY', 'Airtel Money'
        BANK = 'BANK', 'Bank Transfer'
        HALOPESA = 'HALOPESA', 'HaloPesa'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payout_account')
    method = models.CharField(max_length=20, choices=Method.choices)
    account_number = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=200, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)  # for bank transfers
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.method}"

    class Meta:
        ordering = ['-created_at']


# ---------- NEW: Wallet (In-App Wallet) ----------
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.balance}"

    def deposit(self, amount):
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='DEPOSIT',
            status='COMPLETED',
            description='Deposit to wallet'
        )

    def withdraw(self, amount):
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            status='COMPLETED',
            description='Withdrawal from wallet'
        )

    def pay(self, amount, deal):
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='PAYMENT',
            status='COMPLETED',
            description=f'Payment for deal {deal.id}',
            deal=deal
        )


class WalletTransaction(models.Model):
    class Type(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        PAYMENT = 'PAYMENT', 'Payment'
        REFUND = 'REFUND', 'Refund'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.CharField(max_length=255, blank=True, null=True)
    deal = models.ForeignKey(DealRoom, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.status}"


# ---------- NEW: Withdrawal Requests ----------
class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        PROCESSED = 'PROCESSED', 'Processed'

    class Method(models.TextChoices):
        M_PESA = 'M_PESA', 'M-Pesa'
        TIGO_PESA = 'TIGO_PESA', 'Tigo Pesa'
        AIRTEL_MONEY = 'AIRTEL_MONEY', 'Airtel Money'
        BANK = 'BANK', 'Bank Transfer'
        HALOPESA = 'HALOPESA', 'HaloPesa'

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    account_details = models.JSONField(default=dict)  # store phone number or bank details
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.seller.username} - {self.amount} - {self.status}"