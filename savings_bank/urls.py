from django.urls import path
from savings_bank.views import AccountView, TransactionView

urlpatterns = [
    path("accounts/<int:account_id>", view=AccountView.as_view(), name="account_api"),
    path("transactions/<int:account_id>", view=TransactionView.as_view(), name="transaction_api"),
]
