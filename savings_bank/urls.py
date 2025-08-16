from django.urls import path
from savings_bank.views import (
    UserCreateView,
    AccountCreateView,
    AccountDetailsView,
    AccountListView,
    AccountBalanceView,
    TransactionView,
)

urlpatterns = [
    path(
        route="users",
        view=UserCreateView.as_view(),
        name="user_api",
    ),
    path(
        route="accounts",
        view=AccountCreateView.as_view(),
        name="account_api",
    ),
    path(
        route="accounts",
        view=AccountListView.as_view(),
        name="accounts_api",
    ),
    path(
        route="accounts/<int:account_id>",
        view=AccountDetailsView.as_view(),
        name="account_api",
    ),
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
