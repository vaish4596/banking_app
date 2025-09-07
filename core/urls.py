# core/urls.py
from django.urls import path, include
from rest_framework import routers
from . import views
from .api_views import AccountViewSet, TransactionViewSet, BillViewSet, PayeeViewSet
from django.contrib.auth import views as auth_views

router = routers.DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="api-accounts")
router.register(r"transactions", TransactionViewSet, basename="api-transactions")
router.register(r"bills", BillViewSet, basename="api-bills")
router.register(r"payees", PayeeViewSet, basename="api-payees")

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("accounts/", views.accounts, name="accounts"),
    path("accounts/<uuid:account_id>/", views.account_detail, name="account_detail"),
    path("deposit/", views.deposit, name="deposit"),
    path("withdraw/", views.withdraw, name="withdraw"),
    path("transfer/", views.transfer, name="transfer"),
    # Bills
    path("bills/", views.bills, name="bills"),
    path("bills/create-test/", views.create_sample_bills, name="create_sample_bills"),
    path("bills/pay/<uuid:bill_id>/", views.pay_bill, name="pay_bill"),

]

# Mount APIs under /api/ so they don’t interfere with templates
urlpatterns += [
    path("api/", include(router.urls)),
    
]

