from django.urls import path
from savings_bank.views import AccountView, AccountBalanceView, TransactionView

urlpatterns = [
    path("accounts/<int:account_id>", view=AccountView.as_view(), name="account_api"),
    path("accounts/<int:account_id>/balance", view=AccountBalanceView.as_view(), name="account_balance_api"),
    path("transactions/<int:account_id>", view=TransactionView.as_view(), name="transaction_api"),
]
