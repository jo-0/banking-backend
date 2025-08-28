import json

from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from savings_bank.models import AuthToken, Account
from savings_bank.services import TransactionService

User = get_user_model()


class SavingsBankAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "strongpass123"
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

        # Create a token for the test user and simulate authentication
        self.auth_token = AuthToken.objects.create(user=self.user, is_active=True)
        self.auth_headers = {
            "AUTHORIZATION": f"Token {self.auth_token.key}",
            "Content-Type": "application/json",
        }

        # Common URLs
        self.login_url = reverse("login_api")
        self.user_create_url = reverse("user_api")
        self.account_create_url = reverse("account_api")
        self.deposit_url = reverse("deposit_api")
        self.withdrawal_url = reverse("withdrawal_api")
        self.transfer_url = reverse("transfer_api")

        # Create an initial account for the user to be used in balance, deposit,
        # withdrawal, transfer tests
        account_creation_data = {
            "bank_name": "Test Savings Bank",
            "branch": "Test Branch",
        }
        # Simulate authenticated request to create the account
        response = self.client.post(
            self.account_create_url,
            data=json.dumps(account_creation_data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(
            response.status_code,
            201,
            f"Failed to set up initial account: {response.json()}",
        )
        self.user_account = Account.objects.get(user=self.user)
        self.account_id = self.user_account.id

        # Add initial deposit to ensure balance is not zero
        TransactionService.create_deposit(
            self.user_account, Decimal("1000.00"), "Initial Deposit"
        )
        self.user_account.refresh_from_db()  # Refresh balance after transaction


class LoginViewTests(SavingsBankAPITestCase):
    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({"username": self.username, "password": self.password}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())
        self.assertIn("user_id", response.json())
        self.assertEqual(response.json()["username"], self.username)
        # Ensure a new token is not created if an active one exists
        self.assertEqual(
            AuthToken.objects.filter(user=self.user, is_active=True).count(), 1
        )

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({"username": self.username, "password": "wrongpassword"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.json()["error"])

    def test_login_missing_fields(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({"username": self.username}),  # Missing password
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username and password are required", response.json()["error"])


class UserCreateViewTests(SavingsBankAPITestCase):
    def test_create_user_success(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123",
        }
        response = self.client.post(
            self.user_create_url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["username"], data["username"])
        self.assertTrue(User.objects.filter(username=data["username"]).exists())

    def test_create_user_existing_username(self):
        data = {
            "username": self.username,  # Use existing username
            "email": "another@example.com",
            "password": "pass",
        }
        response = self.client.post(
            self.user_create_url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already exists", response.json()["error"])

    def test_create_user_missing_fields(self):
        data = {
            "username": "incompleteuser",
            "email": "incomplete@example.com",
            # Missing password
        }
        response = self.client.post(
            self.user_create_url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Password is required", response.json()["error"])


class AccountCreateViewTests(SavingsBankAPITestCase):
    def test_create_account_success_for_new_user(self):
        """Ensure a user can create an account if one does not exist."""
        # Create a new user and authenticate them for this test
        new_user = User.objects.create_user(
            username="newuser_acc", password="newpass_acc"
        )
        new_token = AuthToken.objects.create(user=new_user)
        new_auth_headers = {
            "AUTHORIZATION": f"Token {new_token.key}",
            "Content-Type": "application/json",
        }

        data = {"bank_name": "New Bank for User", "branch": "New Branch"}
        response = self.client.post(
            self.account_create_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=new_auth_headers,
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["user_id"], new_user.id)
        self.assertTrue(Account.objects.filter(user=new_user).exists())

    def test_create_account_already_exists_for_user(self):
        """Ensure a user cannot create more than one account."""
        # self.user already has an account from setUp.
        # This mirrors the 'account_creation_data' in setUp.
        attempt_data = {
            "bank_name": "Attempted Second Bank",
            "branch": "Attempted Second Branch",
        }

        response = self.client.post(
            self.account_create_url,
            data=json.dumps(attempt_data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("User may already have an account.", response.json()["error"])

    def test_create_account_unauthenticated(self):
        """Ensure unauthenticated users cannot create accounts."""
        data = {"bank_name": "Public Bank", "branch": "Public Branch"}
        response = self.client.post(
            self.account_create_url,
            data=json.dumps(data),
            content_type="application/json",  # No auth headers
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])


class AccountDetailsViewTests(SavingsBankAPITestCase):
    def test_get_account_details_success(self):
        """Ensure authenticated user can retrieve their own account details."""
        url = reverse(
            "account_api", kwargs={"account_id": self.account_id}
        )  # Named 'account_api' for single account
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json())
        self.assertEqual(response.json()["bank"], self.user_account.bank_name)

    def test_get_account_details_unauthenticated(self):
        """Ensure unauthenticated users cannot retrieve account details."""
        unauthenticated_client = Client()
        url = reverse("account_api", kwargs={"account_id": self.account_id})
        response = unauthenticated_client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])

    def test_get_account_details_not_found(self):
        """Ensure requesting a non-existent account returns 404."""
        non_existent_id = self.account_id + 999
        url = reverse("account_api", kwargs={"account_id": non_existent_id})
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 404)
        # Note: get_object_or_404 returns a default Django 404 response in HTML,
        # unless explicitly caught and converted to JSON. Your view may return HTML.


class AccountListViewTests(SavingsBankAPITestCase):
    def test_list_accounts_success(self):
        """Ensure authenticated user can retrieve a list of all accounts."""
        url = reverse("accounts_api")  # Named 'accounts_api' for all accounts
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))
        # Ensure at least the setUp account is present
        self.assertGreaterEqual(len(response.json()), 1)

    def test_list_accounts_unauthenticated(self):
        """Ensure unauthenticated users cannot retrieve a list of accounts."""
        unauthenticated_client = Client()
        url = reverse("accounts_api")
        response = unauthenticated_client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])


class AccountBalanceViewTests(SavingsBankAPITestCase):
    def test_get_account_balance_success(self):
        """Ensure authenticated user can retrieve their own account balance."""
        url = reverse("account_balance_api", kwargs={"account_id": self.account_id})
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("balance", response.json())
        self.assertEqual(Decimal(response.json()["balance"]), self.user_account.balance)

    def test_get_account_balance_unauthenticated(self):
        """Ensure unauthenticated users cannot retrieve account balance."""
        unauthenticated_client = Client()
        url = reverse("account_balance_api", kwargs={"account_id": self.account_id})
        response = unauthenticated_client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])

    def test_get_account_balance_not_found(self):
        """Ensure requesting a non-existent account balance returns 404."""
        non_existent_id = self.account_id + 999
        url = reverse("account_balance_api", kwargs={"account_id": non_existent_id})
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 404)


class TransactionViewTests(SavingsBankAPITestCase):
    def setUp(self):
        super().setUp()
        # Create a few transactions for the test account
        TransactionService.create_deposit(
            self.user_account, Decimal("200.00"), "Test Deposit"
        )
        TransactionService.create_withdrawal(
            self.user_account, Decimal("50.00"), "Test Withdrawal"
        )
        self.user_account.refresh_from_db()

    def test_get_transactions_success(self):
        """Ensure authenticated user can retrieve their account transactions."""
        url = reverse("transaction_api", kwargs={"account_id": self.account_id})
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))
        # Account should have at least 3 transactions (initial + 2 more)
        self.assertGreaterEqual(len(response.json()), 3)

    def test_get_transactions_unauthenticated(self):
        """Ensure unauthenticated users cannot retrieve transactions."""
        unauthenticated_client = Client()
        url = reverse("transaction_api", kwargs={"account_id": self.account_id})
        response = unauthenticated_client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])

    def test_get_transactions_not_found(self):
        """Ensure requesting transactions for a non-existent account returns 404."""
        non_existent_id = self.account_id + 999
        url = reverse("transaction_api", kwargs={"account_id": non_existent_id})
        response = self.client.get(url, headers=self.auth_headers)
        self.assertEqual(response.status_code, 404)


class DepositViewTests(SavingsBankAPITestCase):
    def test_deposit_success(self):
        """Ensure a user can successfully deposit funds into their own account."""
        initial_balance = self.user_account.balance
        deposit_amount = Decimal("500.00")
        data = {
            "account_id": self.account_id,
            "amount": str(deposit_amount),
            "note": "Online Deposit",
        }

        response = self.client.post(
            self.deposit_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 201)  # 201 Created

        self.user_account.refresh_from_db()
        expected_balance = initial_balance + deposit_amount
        self.assertEqual(self.user_account.balance, expected_balance)
        self.assertEqual(response.json()["new_balance"], str(expected_balance))
        self.assertEqual(response.json()["transaction_type"], "DEPOSIT")
        self.assertEqual(
            response.json()["status"], "SUCCESS"
        )  # Assuming service marks success

    def test_deposit_unauthenticated(self):
        """Ensure unauthenticated users cannot make deposits."""
        data = {"account_id": self.account_id, "amount": "100.00"}
        response = self.client.post(
            self.deposit_url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])

    def test_deposit_invalid_amount(self):
        """Ensure deposits fail with an invalid (non-positive) amount."""
        data = {"account_id": self.account_id, "amount": "-100.00"}
        response = self.client.post(
            self.deposit_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Amount must be positive", response.json()["error"])

    def test_deposit_account_not_found(self):
        """Ensure deposits fail if the target account does not exist."""
        non_existent_id = self.account_id + 999
        data = {"account_id": non_existent_id, "amount": "100.00"}
        response = self.client.post(
            self.deposit_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Account not found", response.json()["error"])

    def test_deposit_other_user_account_forbidden(self):
        """Ensure a user cannot deposit into another user's account."""
        other_user = User.objects.create_user(username="otherdepuser", password="pass")
        other_account = Account.objects.create(
            user=other_user, bank_name="Other Bank", branch="Other Branch"
        )
        other_account_id = other_account.id

        data = {"account_id": other_account_id, "amount": "100.00"}
        response = self.client.post(
            self.deposit_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(
            response.status_code, 403
        )  # This assumes you have the authorization check in your view!
        self.assertIn(
            "You do not have permission", response.json()["error"]
        )  # This message should come from your view's 403 response.
        other_account.refresh_from_db()
        self.assertEqual(
            other_account.balance, Decimal("0.00")
        )  # Ensure balance didn't change


class WithdrawalViewTests(SavingsBankAPITestCase):
    def test_withdrawal_success(self):
        """Ensure a user can successfully withdraw funds from their account."""
        initial_balance = self.user_account.balance
        withdrawal_amount = Decimal("100.00")
        data = {
            "account_id": self.account_id,
            "amount": str(withdrawal_amount),
            "note": "ATM Withdrawal",
        }

        response = self.client.post(
            self.withdrawal_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 201)

        self.user_account.refresh_from_db()
        expected_balance = initial_balance - withdrawal_amount
        self.assertEqual(self.user_account.balance, expected_balance)
        self.assertEqual(response.json()["new_balance"], str(expected_balance))
        self.assertEqual(response.json()["transaction_type"], "WITHDRAWAL")
        self.assertEqual(response.json()["status"], "SUCCESS")

    def test_withdrawal_insufficient_balance(self):
        """Ensure withdrawal fails if account has insufficient balance."""
        withdrawal_amount = self.user_account.balance + Decimal(
            "100.00"
        )  # More than current balance
        data = {"account_id": self.account_id, "amount": str(withdrawal_amount)}
        response = self.client.post(
            self.withdrawal_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient balance", response.json()["error"])
        # Ensure balance did not change
        self.user_account.refresh_from_db()
        self.assertNotEqual(
            self.user_account.balance, Decimal("0.00")
        )  # Still has initial deposit

    def test_withdrawal_unauthenticated(self):
        """Ensure unauthenticated users cannot make withdrawals."""
        data = {"account_id": self.account_id, "amount": "100.00"}
        response = self.client.post(
            self.withdrawal_url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])

    def test_withdrawal_other_user_account_forbidden(self):
        """Ensure a user cannot withdraw from another user's account."""
        other_user = User.objects.create_user(username="otherwithuser", password="pass")
        other_account = Account.objects.create(
            user=other_user, bank_name="Other Bank", branch="Other Branch"
        )
        # Add initial balance to other account so it has something to withdraw
        TransactionService.create_deposit(
            other_account, Decimal("500.00"), "Other User Initial"
        )
        other_account.refresh_from_db()

        data = {"account_id": other_account.id, "amount": "100.00"}
        response = self.client.post(
            self.withdrawal_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission", response.json()["error"])
        other_account.refresh_from_db()
        self.assertEqual(
            other_account.balance, Decimal("500.00")
        )  # Balance should be unchanged


class TransferViewTests(SavingsBankAPITestCase):
    def setUp(self):
        super().setUp()
        # Create a second user and account for transfer tests
        self.second_user = User.objects.create_user(
            username="seconduser", password="pass"
        )
        self.second_account = Account.objects.create(
            user=self.second_user, bank_name="Second Bank", branch="Second Branch"
        )

    def test_transfer_success(self):
        """Ensure a user can successfully transfer funds between accounts."""
        initial_balance_sender = self.user_account.balance
        initial_balance_receiver = self.second_account.balance
        transfer_amount = Decimal("50.00")

        data = {
            "from_account_id": self.account_id,
            "to_account_id": self.second_account.id,
            "amount": str(transfer_amount),
            "note": "Funds Transfer",
        }
        response = self.client.post(
            self.transfer_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 201)

        self.user_account.refresh_from_db()
        self.second_account.refresh_from_db()

        expected_balance_sender = initial_balance_sender - transfer_amount
        expected_balance_receiver = initial_balance_receiver + transfer_amount

        self.assertEqual(self.user_account.balance, expected_balance_sender)
        self.assertEqual(self.second_account.balance, expected_balance_receiver)
        self.assertIn("debit_transaction", response.json())
        self.assertIn("credit_transaction", response.json())
        self.assertEqual(response.json()["transfer_amount"], str(transfer_amount))

    def test_transfer_insufficient_balance(self):
        """Ensure transfer fails if sender account has insufficient balance."""
        transfer_amount = self.user_account.balance + Decimal(
            "100.00"
        )  # More than current balance
        data = {
            "from_account_id": self.account_id,
            "to_account_id": self.second_account.id,
            "amount": str(transfer_amount),
        }
        response = self.client.post(
            self.transfer_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient balance", response.json()["error"])

    def test_transfer_to_same_account(self):
        """Ensure transfer fails if from and to accounts are the same."""
        data = {
            "from_account_id": self.account_id,
            "to_account_id": self.account_id,
            "amount": "10.00",
        }
        response = self.client.post(
            self.transfer_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot transfer to the same account", response.json()["error"])

    def test_transfer_unauthenticated(self):
        """Ensure unauthenticated users cannot make transfers."""
        data = {
            "from_account_id": self.account_id,
            "to_account_id": self.second_account.id,
            "amount": "10.00",
        }
        response = self.client.post(
            self.transfer_url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])

    def test_transfer_from_other_user_account_forbidden(self):
        """Ensure a user cannot transfer from another user's account."""
        other_user = User.objects.create_user(username="otherfromuser", password="pass")
        other_account = Account.objects.create(
            user=other_user, bank_name="Other From", branch="Branch"
        )
        TransactionService.create_deposit(
            other_account, Decimal("500.00"), "Other User Initial"
        )
        other_account.refresh_from_db()

        data = {
            "from_account_id": other_account.id,  # Attempt to transfer from other user's account
            "to_account_id": self.second_account.id,
            "amount": "10.00",
        }
        response = self.client.post(
            self.transfer_url,
            data=json.dumps(data),
            content_type="application/json",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission", response.json()["error"])
        # Ensure balances did not change
        other_account.refresh_from_db()
        self.assertEqual(other_account.balance, Decimal("500.00"))
        self.second_account.refresh_from_db()
        self.assertEqual(self.second_account.balance, Decimal("0.00"))


class LogoutViewTests(SavingsBankAPITestCase):
    def test_logout_success(self):
        """Ensure an authenticated user can successfully log out (deactivate token)."""
        logout_url = reverse("logout_api")
        response = self.client.post(
            logout_url, content_type="application/json", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully logged out", response.json()["message"])
        # Verify the token is now inactive in the database
        self.auth_token.refresh_from_db()
        self.assertFalse(self.auth_token.is_active)

    def test_logout_unauthenticated(self):
        """Ensure unauthenticated users cannot log out (no token to deactivate)."""
        logout_url = reverse("logout_api")
        response = self.client.post(logout_url, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication token required", response.json()["error"])
