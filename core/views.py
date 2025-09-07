import random
from .models import Bill, Account, Transaction, Payee   # ✅ added Payee
from django.conf import settings
import uuid
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm


# Signup view
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically create a default savings account for the new user
            Account.objects.create(user=user)
            messages.success(
                request,
                "Account created successfully! A default savings account has been created. You can now log in.",
            )
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "core/signup.html", {"form": form})


# Home page
def home(request):
    return render(request, "core/home.html")


# Accounts list
@login_required
def accounts(request):
    user_accounts = request.user.accounts.all()
    return render(request, "core/accounts.html", {"accounts": user_accounts})


# Account details + transactions
@login_required
def account_detail(request, account_id):
    account = get_object_or_404(Account, id=account_id, user=request.user)
    transactions = (
        account.outgoing_transactions.all() | account.incoming_transactions.all()
    )
    transactions = transactions.order_by("-created_at")
    return render(
        request,
        "core/account_detail.html",
        {"account": account, "transactions": transactions},
    )


# Deposit
@login_required
def deposit(request):
    if request.method == "POST":
        account_id = request.POST.get("account")
        amount = Decimal(request.POST.get("amount", 0))
        account = get_object_or_404(Account, id=account_id, user=request.user)
        account.balance += amount
        account.save()
        # Record transaction
        Transaction.objects.create(
            from_account=None,
            to_account=account,
            amount=amount,
            type=Transaction.TYPE_DEPOSIT,
            status=Transaction.STATUS_COMPLETED,
            created_by=request.user,
            description="Deposit",
        )
        messages.success(request, f"Deposited {amount} to {account.account_number}")
        return redirect("accounts")
    user_accounts = request.user.accounts.all()
    return render(request, "core/deposit.html", {"accounts": user_accounts})


# Withdraw
@login_required
def withdraw(request):
    if request.method == "POST":
        account_id = request.POST.get("account")
        amount = Decimal(request.POST.get("amount", 0))
        account = get_object_or_404(Account, id=account_id, user=request.user)
        if account.balance >= amount:
            account.balance -= amount
            account.save()
            # Record transaction
            Transaction.objects.create(
                from_account=account,
                to_account=None,
                amount=amount,
                type=Transaction.TYPE_WITHDRAW,
                status=Transaction.STATUS_COMPLETED,
                created_by=request.user,
                description="Withdraw",
            )
            messages.success(request, f"Withdrew {amount} from {account.account_number}")
        else:
            messages.error(request, "Insufficient balance")
        return redirect("accounts")
    user_accounts = request.user.accounts.all()
    return render(request, "core/withdraw.html", {"accounts": user_accounts})


# Transfer
@login_required
def transfer(request):
    if request.method == "POST":
        from_id = request.POST.get("from_account")
        to_id = request.POST.get("to_account")
        amount = Decimal(request.POST.get("amount", 0))
        from_acc = get_object_or_404(Account, id=from_id, user=request.user)
        to_acc = get_object_or_404(Account, id=to_id)
        if from_acc.balance >= amount:
            from_acc.balance -= amount
            to_acc.balance += amount
            from_acc.save()
            to_acc.save()
            # Record transaction
            Transaction.objects.create(
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                type=Transaction.TYPE_TRANSFER,
                status=Transaction.STATUS_COMPLETED,
                created_by=request.user,
                description="Transfer",
            )
            messages.success(
                request,
                f"Transferred {amount} from {from_acc.account_number} to {to_acc.account_number}",
            )
        else:
            messages.error(request, "Insufficient balance")
        return redirect("accounts")
    user_accounts = request.user.accounts.all()
    all_accounts = Account.objects.exclude(user=request.user)
    return render(
        request,
        "core/transfer.html",
        {"accounts": user_accounts, "all_accounts": all_accounts},
    )


# Bills List
@login_required
def bills(request):
    bills = Bill.objects.filter(user=request.user)
    return render(request, "core/bills.html", {"bills": bills})



@login_required
def create_sample_bills(request):
    """
    Creates sample Payee objects and Bill objects for the logged-in user.
    Uses Payee.objects.get_or_create to avoid FK errors.
    """
    if request.method == "POST":
        # create or fetch payees for the logged-in user
        p1, _ = Payee.objects.get_or_create(
            user=request.user,
            name="Electricity Board",
            account_number="1111111111",
            bank_name="Utility Bank",
            ifsc="UTIL0001"
        )
        p2, _ = Payee.objects.get_or_create(
            user=request.user,
            name="Water Supply",
            account_number="2222222222",
            bank_name="Utility Bank",
            ifsc="UTIL0002"
        )

        # create bills linked to these payees
        Bill.objects.create(
            user=request.user,
            payee=p1,
            amount=Decimal('500.00'),
            due_date=timezone.now() + timezone.timedelta(days=7),
            status=Bill.STATUS_PENDING,
        )
        Bill.objects.create(
            user=request.user,
            payee=p2,
            amount=Decimal('300.00'),
            due_date=timezone.now() + timezone.timedelta(days=10),
            status=Bill.STATUS_PENDING,
        )

        messages.success(request, "Sample bills created!")
        return redirect("bills")

    return redirect("bills")

@login_required
def pay_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, user=request.user)
    user_accounts = Account.objects.filter(user=request.user, is_active=True)

    if request.method == "POST":
        account_id = request.POST.get("account")
        account = get_object_or_404(Account, id=account_id, user=request.user)

        if account.balance >= bill.amount:
            if getattr(settings, "USE_MOCK_RAZORPAY", True):
                # ✅ simulate Razorpay random outcome
                fake_payment_id = f"mock_pay_{uuid.uuid4().hex[:10]}"
                success = random.choice([True, True, True, False])  # 75% success

                if success:
                    bill.status = Bill.STATUS_PAID
                    bill.paid_at = timezone.now()
                    bill.save()

                    account.balance -= bill.amount
                    account.save()

                    Transaction.objects.create(
                        from_account=account,
                        to_account=None,
                        amount=bill.amount,
                        type=Transaction.TYPE_BILL,
                        status=Transaction.STATUS_COMPLETED,
                        created_by=request.user,
                        description=f"Bill payment SUCCESS (Mock Razorpay ID: {fake_payment_id})"
                    )
                    messages.success(request, f"Bill {bill.id} paid successfully!")
                else:
                    Transaction.objects.create(
                        from_account=account,
                        to_account=None,
                        amount=bill.amount,
                        type=Transaction.TYPE_BILL,
                        status=Transaction.STATUS_FAILED,
                        created_by=request.user,
                        description=f"Bill payment FAILED (Mock Razorpay ID: {fake_payment_id})"
                    )
                    messages.error(request, f"Bill {bill.id} payment FAILED (Mock Razorpay)")
                return redirect("bills")

            else:
                messages.info(request, "Real Razorpay not configured.")
                return redirect("bills")
        else:
            messages.error(request, "Insufficient balance in selected account.")
            return redirect("bills")

    return render(request, "core/pay_bill.html", {"bill": bill, "accounts": user_accounts})