from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User


from savings_bank.models import Account, Transaction


class AccountView(View):
    def get(self, request, account_id) -> JsonResponse:
        account = get_object_or_404(Account, id=account_id)
        user = User.objects.filter(id=account.user.pk).first()  # type: ignore
        if not user:
            raise
        account_dict = {}
        account_dict["name"] = f"{user.first_name} {user.last_name}"
        account_dict["bank"] = account.bank_name
        account_dict["branch"] = account.branch
        account_dict["balance"] = account.balance
        return JsonResponse(account_dict)


class AccountBalanceView(View):
    def get(self, request, account_id) -> JsonResponse:
        account = get_object_or_404(Account, id=account_id)
        return JsonResponse({"balance": account.balance})


class TransactionView(View):
    def get(self, request, account_id) -> JsonResponse:
        transactions = Transaction.objects.filter(
            Q(from_account=account_id) | Q(to_account=account_id),
            status=Transaction.TransactionStatus.SUCCESS,
        ).values()
        return JsonResponse(list(transactions), safe=False)
