import json

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, ListView

from savings_bank.models import Account, Transaction


@method_decorator(csrf_exempt, name="dispatch")
class UserCreateView(View):
    def post(self, request) -> JsonResponse:
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)

            # Extract user data with validation
            username = data.get("username")
            email = data.get("email")
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            password = data.get("password")

            # Validate required fields
            if not username:
                return JsonResponse({"error": "Username is required."}, status=400)

            if not email:
                return JsonResponse({"error": "Email is required."}, status=400)

            if not password:
                return JsonResponse({"error": "Password is required."}, status=400)

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists."}, status=400)

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists."}, status=400)

            # Create the new user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )

            # Return success response with user details
            return JsonResponse(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "date_joined": user.date_joined.isoformat(),
                    "is_active": user.is_active,
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except IntegrityError:
            return JsonResponse(
                {"error": "User creation failed. Username or email may already exist."},
                status=400,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class AccountCreateView(View):
    def post(self, request) -> JsonResponse:
        # Ensure the user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=403)

        try:
            # Check if the user already has an account
            if hasattr(request.user, "account"):
                return JsonResponse(
                    {"error": "This user already has an account."},
                    status=400,
                )

            # Parse the incoming JSON data from the request body
            data = json.loads(request.body)
            bank_name = data.get("bank_name", "Savings Bank")  # Default value
            branch = data.get("branch", "Main Branch")  # Default value

            # Create the new account, linking it to the authenticated user
            account = Account.objects.create(
                user=request.user, bank_name=bank_name, branch=branch
            )

            # Return a success JSON response with the new account's details
            return JsonResponse(
                {
                    "id": account.id,
                    "bank_name": account.bank_name,
                    "branch": account.branch,
                    "user_id": account.user.id,
                    "username": account.user.username,
                    "balance": str(
                        account.balance
                    ),  # Convert Decimal to string for JSON
                    "created_at": account.created_at.isoformat(),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except IntegrityError:
            return JsonResponse(
                {"error": "Account creation failed. User may already have an account."},
                status=400,
            )
        except Exception as e:
            # Handle other potential errors gracefully
            return JsonResponse({"error": str(e)}, status=500)


class AccountDetailsView(DeleteView):
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


class AccountListView(ListView):
    def get(self, request) -> JsonResponse:
        accounts = Account.objects.all().values()
        return JsonResponse(list(accounts), safe=False)


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
