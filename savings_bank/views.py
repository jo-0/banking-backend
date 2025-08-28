import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, ListView

from savings_bank.models import Account, AuthToken, Transaction
from savings_bank.services import TransactionService


def authenticate_token(request):
    """Helper function to authenticate token and return user or error response"""
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    if not auth_header or not auth_header.startswith("Token "):
        return None, JsonResponse(
            {
                "error": (
                    "Authentication token required. Include 'Authorization: Token "
                    "<your_token>' in headers."
                )
            },
            status=401,
        )

    token_key = auth_header.split(" ")[1]
    try:
        token = AuthToken.objects.get(key=token_key, is_active=True)
        # Update last used timestamp
        token.last_used = timezone.now()
        token.save()
        return token.user, None
    except AuthToken.DoesNotExist:
        return None, JsonResponse(
            {"error": "Invalid authentication token."}, status=401
        )


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    def post(self, request) -> JsonResponse:
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse(
                    {"error": "Username and password are required."}, status=400
                )

            user = authenticate(username=username, password=password)
            if user:
                # Create or get existing active token
                token = AuthToken.objects.filter(user=user, is_active=True).first()
                if not token:
                    token = AuthToken.objects.create(user=user)

                # Update last used timestamp
                token.last_used = timezone.now()
                token.save()

                return JsonResponse(
                    {
                        "token": token.key,
                        "user_id": user.id,
                        "username": user.username,
                        "message": "Login successful",
                    }
                )
            else:
                return JsonResponse({"error": "Invalid credentials."}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


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
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

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
                user=user, bank_name=bank_name, branch=branch
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
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        account = get_object_or_404(Account, id=account_id)
        user = User.objects.filter(id=account.user.pk).first()
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
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        accounts = Account.objects.all().values()
        return JsonResponse(list(accounts), safe=False)


class AccountBalanceView(View):
    def get(self, request, account_id) -> JsonResponse:
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        account = get_object_or_404(Account, id=account_id)
        return JsonResponse({"balance": account.balance})


class TransactionView(View):
    def get(self, request, account_id) -> JsonResponse:
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        # Check if account exists
        account = get_object_or_404(Account, id=account_id)

        transactions = Transaction.objects.filter(
            Q(account=account_id)
            | Q(from_account=account_id)
            | Q(to_account=account_id),
            status=Transaction.TransactionStatus.SUCCESS,
        ).values()
        return JsonResponse(list(transactions), safe=False)


@method_decorator(csrf_exempt, name="dispatch")
class DepositView(View):
    def post(self, request) -> JsonResponse:
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        try:
            # Parse JSON data
            data = json.loads(request.body)
            account_id = data.get("account_id")
            amount = data.get("amount")
            note = data.get("note", "")

            # Validate required fields
            if not account_id:
                return JsonResponse({"error": "Account ID is required."}, status=400)

            if not amount:
                return JsonResponse({"error": "Amount is required."}, status=400)

            # Convert amount to Decimal and validate
            try:
                from decimal import Decimal

                amount = Decimal(str(amount))
                if amount <= 0:
                    return JsonResponse(
                        {"error": "Amount must be positive."}, status=400
                    )
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid amount format."}, status=400)

            # Get the account
            try:
                account = Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                return JsonResponse({"error": "Account not found"}, status=404)

            # Check if user owns the account
            if account.user != user:
                return JsonResponse(
                    {"error": "You do not have permission to deposit to this account."},
                    status=403,
                )

            # Create deposit transaction using service
            transaction = TransactionService.create_deposit(account, amount, note)

            return JsonResponse(
                {
                    "id": transaction.id,
                    "account_id": account.id,
                    "amount": str(transaction.amount),
                    "transaction_type": transaction.transaction_type,
                    "status": transaction.status,
                    "note": transaction.note,
                    "created_at": transaction.created_at.isoformat(),
                    "new_balance": str(account.balance),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class WithdrawalView(View):
    def post(self, request) -> JsonResponse:
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        try:
            # Parse JSON data
            data = json.loads(request.body)
            account_id = data.get("account_id")
            amount = data.get("amount")
            note = data.get("note", "")

            # Validate required fields
            if not account_id:
                return JsonResponse({"error": "Account ID is required."}, status=400)

            if not amount:
                return JsonResponse({"error": "Amount is required."}, status=400)

            # Convert amount to Decimal and validate
            try:
                from decimal import Decimal

                amount = Decimal(str(amount))
                if amount <= 0:
                    return JsonResponse(
                        {"error": "Amount must be positive."}, status=400
                    )
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid amount format."}, status=400)

            # Get the account
            account = get_object_or_404(Account, id=account_id)

            # Check if user owns the account
            if account.user != user:
                return JsonResponse(
                    {
                        "error": "You do not have permission to withdraw from this account."
                    },
                    status=403,
                )

            # Create withdrawal transaction using service (includes balance check)
            try:
                transaction = TransactionService.create_withdrawal(
                    account, amount, note
                )
            except ValidationError as e:
                return JsonResponse({"error": str(e)}, status=400)

            return JsonResponse(
                {
                    "id": transaction.id,
                    "account_id": account.id,
                    "amount": str(transaction.amount),
                    "transaction_type": transaction.transaction_type,
                    "status": transaction.status,
                    "note": transaction.note,
                    "created_at": transaction.created_at.isoformat(),
                    "new_balance": str(account.balance),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class TransferView(View):
    def post(self, request) -> JsonResponse:
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        try:
            # Parse JSON data
            data = json.loads(request.body)
            from_account_id = data.get("from_account_id")
            to_account_id = data.get("to_account_id")
            amount = data.get("amount")
            note = data.get("note", "")

            # Validate required fields
            if not from_account_id:
                return JsonResponse(
                    {"error": "From account ID is required."}, status=400
                )

            if not to_account_id:
                return JsonResponse({"error": "To account ID is required."}, status=400)

            if not amount:
                return JsonResponse({"error": "Amount is required."}, status=400)

            # Convert amount to Decimal and validate
            try:
                from decimal import Decimal

                amount = Decimal(str(amount))
                if amount <= 0:
                    return JsonResponse(
                        {"error": "Amount must be positive."}, status=400
                    )
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid amount format."}, status=400)

            # Validate accounts are different
            if from_account_id == to_account_id:
                return JsonResponse(
                    {"error": "Cannot transfer to the same account."}, status=400
                )

            # Get the accounts
            from_account = get_object_or_404(Account, id=from_account_id)
            to_account = get_object_or_404(Account, id=to_account_id)

            # Check if user owns the from_account
            if from_account.user != user:
                return JsonResponse(
                    {
                        "error": "You do not have permission to transfer from this account."
                    },
                    status=403,
                )

            # Create transfer using service (includes all validations)
            try:
                debit_transaction, credit_transaction = (
                    TransactionService.create_transfer(
                        from_account, to_account, amount, note
                    )
                )
            except ValidationError as e:
                return JsonResponse({"error": str(e)}, status=400)

            return JsonResponse(
                {
                    "debit_transaction": {
                        "id": debit_transaction.id,
                        "account_id": from_account.id,
                        "amount": str(debit_transaction.amount),
                        "transaction_type": debit_transaction.transaction_type,
                        "status": debit_transaction.status,
                        "note": debit_transaction.note,
                        "created_at": debit_transaction.created_at.isoformat(),
                    },
                    "credit_transaction": {
                        "id": credit_transaction.id,
                        "account_id": to_account.id,
                        "amount": str(credit_transaction.amount),
                        "transaction_type": credit_transaction.transaction_type,
                        "status": credit_transaction.status,
                        "note": credit_transaction.note,
                        "created_at": credit_transaction.created_at.isoformat(),
                    },
                    "from_account_balance": str(from_account.balance),
                    "to_account_balance": str(to_account.balance),
                    "transfer_amount": str(amount),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):
    def post(self, request) -> JsonResponse:
        # Authenticate user
        user, error_response = authenticate_token(request)
        if error_response:
            return error_response

        try:
            # Deactivate all user tokens
            AuthToken.objects.filter(user=user, is_active=True).update(is_active=False)
            return JsonResponse({"message": "Successfully logged out"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
