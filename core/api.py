from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Account
from .services import deposit, withdraw, transfer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deposit_api(request):
    account = get_object_or_404(Account, user=request.user)
    amount = float(request.data.get("amount", 0))
    txn = deposit(account, amount, created_by=request.user, description="API deposit")
    return Response({"message": "Deposit successful", "balance": account.balance, "txn": txn.reference_id})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def withdraw_api(request):
    account = get_object_or_404(Account, user=request.user)
    amount = float(request.data.get("amount", 0))
    txn = withdraw(account, amount, created_by=request.user, description="API withdraw")
    return Response({"message": "Withdraw successful", "balance": account.balance, "txn": txn.reference_id})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transfer_api(request):
    from_account = get_object_or_404(Account, user=request.user)
    to_user = request.data.get("to_user")
    amount = float(request.data.get("amount", 0))

    to_account = get_object_or_404(Account, user__username=to_user)
    txn = transfer(from_account, to_account, amount, created_by=request.user, description="API transfer")

    return Response({"message": "Transfer successful", "from_balance": from_account.balance, "to_balance": to_account.balance, "txn": txn.reference_id})
