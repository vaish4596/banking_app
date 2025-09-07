# core/admin.py
from django.contrib import admin
from .models import UserProfile, Account, Transaction, Payee, Bill


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "kyc_status", "is_2fa_enabled", "created_at")
    search_fields = ("user__username", "phone")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "user", "account_type", "balance", "currency", "is_active", "created_at")
    search_fields = ("account_number", "user__username", "user__email")
    list_filter = ("account_type", "is_active")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("reference_id", "type", "amount", "status", "created_at", "from_account", "to_account")
    search_fields = ("reference_id", "from_account__account_number", "to_account__account_number")
    list_filter = ("type", "status")


@admin.register(Payee)
class PayeeAdmin(admin.ModelAdmin):
    list_display = ("name", "account_number", "user", "bank_name", "created_at")
    search_fields = ("name", "account_number", "user__username")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "payee", "amount", "status", "due_date", "created_at")
    list_filter = ("status",)
