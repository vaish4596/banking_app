from rest_framework import serializers
from .models import Account, Transaction, Bill, Payee

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"

class PayeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payee
        fields = "__all__"
