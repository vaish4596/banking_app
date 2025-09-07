# core/services.py
from decimal import Decimal
from django.db import transaction
from django.db.models import F

from .models import Account, Transaction
import uuid


class InsufficientFunds(Exception):
    pass


def deposit(account: Account, amount: Decimal, created_by=None, description: str = "") -> Transaction:
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Deposit amount must be > 0")

    with transaction.atomic():
        acc = Account.objects.select_for_update().get(pk=account.pk)
        acc.balance = F("balance") + amount
        acc.save(update_fields=["balance"])
        acc.refresh_from_db(fields=["balance"])

        txn = Transaction.objects.create(
            reference_id=uuid.uuid4().hex,
            from_account=None,
            to_account=acc,
            amount=amount,
            type=Transaction.TYPE_DEPOSIT,
            status=Transaction.STATUS_COMPLETED,
            description=description,
            created_by=created_by,
            currency=acc.currency,
        )
    return txn


def withdraw(account: Account, amount: Decimal, created_by=None, description: str = "") -> Transaction:
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Withdraw amount must be > 0")

    with transaction.atomic():
        acc = Account.objects.select_for_update().get(pk=account.pk)
        if acc.balance < amount:
            raise InsufficientFunds("Insufficient balance")
        acc.balance = F("balance") - amount
        acc.save(update_fields=["balance"])
        acc.refresh_from_db(fields=["balance"])

        txn = Transaction.objects.create(
            reference_id=uuid.uuid4().hex,
            from_account=acc,
            to_account=None,
            amount=amount,
            type=Transaction.TYPE_WITHDRAW,
            status=Transaction.STATUS_COMPLETED,
            description=description,
            created_by=created_by,
            currency=acc.currency,
        )
    return txn


def transfer(from_account: Account, to_account: Account, amount: Decimal, created_by=None, description: str = "") -> Transaction:
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Transfer amount must be > 0")
    if from_account.pk == to_account.pk:
        raise ValueError("Cannot transfer to the same account")

    with transaction.atomic():
        # Lock both rows (select_for_update) to prevent race conditions
        # Order the selects deterministically to avoid deadlocks
        accounts = Account.objects.select_for_update().filter(pk__in=[from_account.pk, to_account.pk]).order_by("pk")
        # After the query, fetch the locked instances
        locked_from = next((a for a in accounts if a.pk == from_account.pk), None)
        locked_to = next((a for a in accounts if a.pk == to_account.pk), None)

        if locked_from is None or locked_to is None:
            raise ValueError("Account not found")

        if locked_from.balance < amount:
            raise InsufficientFunds("Insufficient balance")

        # Apply updates using F() expressions
        locked_from.balance = F("balance") - amount
        locked_to.balance = F("balance") + amount
        locked_from.save(update_fields=["balance"])
        locked_to.save(update_fields=["balance"])

        # Refresh so Python sees new decimals
        locked_from.refresh_from_db(fields=["balance"])
        locked_to.refresh_from_db(fields=["balance"])

        txn = Transaction.objects.create(
            reference_id=uuid.uuid4().hex,
            from_account=locked_from,
            to_account=locked_to,
            amount=amount,
            type=Transaction.TYPE_TRANSFER,
            status=Transaction.STATUS_COMPLETED,
            description=description,
            created_by=created_by,
            currency=locked_from.currency,
        )
    return txn
