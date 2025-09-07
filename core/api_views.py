from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Account, Transaction, Bill, Payee
from .serializers import AccountSerializer, TransactionSerializer, BillSerializer, PayeeSerializer

# Ensure users only access their own data
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'user', None) == request.user or getattr(obj, 'from_account', None) and obj.from_account.user == request.user

# Accounts API
class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

# Transactions API
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Include transactions where user is sender or receiver
        user_accounts = self.request.user.accounts.all()
        return Transaction.objects.filter(
            from_account__in=user_accounts
        ) | Transaction.objects.filter(
            to_account__in=user_accounts
        )

# Bills API
class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        bill = self.get_object()
        account_id = request.data.get("account")
        account = Account.objects.get(id=account_id, user=request.user)
        if account.balance >= bill.amount:
            account.balance -= bill.amount
            account.save()
            bill.status = Bill.STATUS_PAID
            bill.paid_at = timezone.now()
            bill.save()
            Transaction.objects.create(
                from_account=account,
                to_account=None,
                amount=bill.amount,
                type=Transaction.TYPE_BILL,
                status=Transaction.STATUS_COMPLETED,
                created_by=request.user,
                description=f"Bill payment to {bill.payee.name}"
            )
            return Response({"status": "Bill paid successfully"})
        return Response({"error": "Insufficient balance"}, status=400)

# Payees API
class PayeeViewSet(viewsets.ModelViewSet):
    serializer_class = PayeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payee.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
