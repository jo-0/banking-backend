from django.urls import path
from savings_bank.views import AccountView, AccountBalanceView, TransactionView

urlpatterns = [
    path(route="accounts/<int:account_id>", view=AccountView.as_view(), name="account_api"),
    path(
        route="accounts/<int:account_id>/balance",
        view=AccountBalanceView.as_view(),
        name="account_balance_api",
    ),
    path(
        route="transactions/<int:account_id>",
        view=TransactionView.as_view(),
        name="transaction_api",
    ),
]
