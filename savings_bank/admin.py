from django.contrib import admin
from savings_bank.models import Account, Transaction


admin.site.register(Account)
admin.site.register(Transaction)
