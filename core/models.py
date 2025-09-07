# core/models.py
import uuid
import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

def generate_reference_id():
    import uuid
    return uuid.uuid4().hex


User = settings.AUTH_USER_MODEL  # use get_user_model indirectly via settings


class UserProfile(models.Model):
    KYC_PENDING = "PENDING"
    KYC_VERIFIED = "VERIFIED"
    KYC_REJECTED = "REJECTED"
    KYC_CHOICES = [
        (KYC_PENDING, "Pending"),
        (KYC_VERIFIED, "Verified"),
        (KYC_REJECTED, "Rejected"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    kyc_status = models.CharField(max_length=10, choices=KYC_CHOICES, default=KYC_PENDING)
    is_2fa_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # if AUTH_USER_MODEL is a string, ensure the related user is readable in admin
        return f"Profile: {getattr(self.user, 'username', str(self.user))}"


class Account(models.Model):
    SAVINGS = "SAV"
    CURRENT = "CUR"
    ACCOUNT_TYPE_CHOICES = [
        (SAVINGS, "Savings"),
        (CURRENT, "Current"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    account_number = models.CharField(max_length=24, unique=True, db_index=True)
    account_type = models.CharField(max_length=3, choices=ACCOUNT_TYPE_CHOICES, default=SAVINGS)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="INR")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_account_number():
        # Example: AC + 10 hex chars -> AC3F7A1B9C
        return "AC" + secrets.token_hex(6).upper()

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)

    def __str__(self):
        # Keep representation readable in admin
        username = getattr(self.user, "username", str(self.user))
        return f"{self.account_number} — {username}"


class Transaction(models.Model):
    TYPE_DEPOSIT = "DEPOSIT"
    TYPE_WITHDRAW = "WITHDRAW"
    TYPE_TRANSFER = "TRANSFER"
    TYPE_BILL = "BILL_PAYMENT"
    TYPE_CHOICES = [
        (TYPE_DEPOSIT, "Deposit"),
        (TYPE_WITHDRAW, "Withdraw"),
        (TYPE_TRANSFER, "Transfer"),
        (TYPE_BILL, "Bill Payment"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(max_length=64, unique=True, default=generate_reference_id) 
    from_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outgoing_transactions",
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_transactions",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    fee = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="INR")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_id} | {self.type} | {self.amount}"


class Payee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payees")
    name = models.CharField(max_length=120)
    account_number = models.CharField(max_length=24)
    bank_name = models.CharField(max_length=120, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.account_number})"


class Bill(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_OVERDUE = "OVERDUE"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_OVERDUE, "Overdue"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bills")
    payee = models.ForeignKey(Payee, on_delete=models.CASCADE, related_name="bills")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bill {self.id} — {self.user} — {self.amount}"
