from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict


from savings_bank.models import Account, Transaction


class AccountView(View):
    def get(self, request, account_id) -> JsonResponse:
        account = get_object_or_404(Account, id=account_id)
        return JsonResponse(model_to_dict(account), safe=False)


class TransactionView(View):
    def get(self, request, account_id):
        # account = get_object_or_404(Account, id=account_id)
        transactions = Transaction.objects.filter(
            from_account=account_id, status=Transaction.TransactionStatus.SUCCESS
        ).values()
        return JsonResponse(list(transactions), safe=False)
