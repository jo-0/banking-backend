# Banking Backend

A Django-based banking system that allows users to manage accounts, perform transactions (deposits, withdrawals, transfers), and track balances computed from transaction history.

## Features

- ✅ User account management with authentication
- ✅ Real-time balance calculation from transaction history
- ✅ Secure money transfers between users
- ✅ Deposit and withdrawal operations
- ✅ Complete transaction audit trail
- ✅ Token-based authentication
- ✅ Admin panel for staff operations
- ✅ Historical balance queries (bonus feature)

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run migrations:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

3. **Start server:**
```bash
python manage.py runserver
```

## API Documentation

All endpoints except user creation and login require authentication. Include the token in the Authorization header:
```
Authorization: Token <your_token_here>
```

### Authentication Endpoints

#### Create User
```http
POST /users
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "testpass123",
  "first_name": "Test",
  "last_name": "User"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User",
  "date_joined": "2025-08-16T10:30:00Z",
  "is_active": true
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "testpass123"
}
```

**Response:**
```json
{
  "token": "abc123def456...",
  "user_id": 1,
  "username": "testuser",
  "message": "Login successful"
}
```

#### Logout
```http
POST /auth/logout
Authorization: Token abc123def456...
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### Account Management

#### Create Account
```http
POST /accounts
Authorization: Token abc123def456...
Content-Type: application/json

{
  "bank_name": "Savings Bank",
  "branch": "Main Branch"
}
```

**Response:**
```json
{
  "id": 1,
  "bank_name": "Savings Bank",
  "branch": "Main Branch",
  "user_id": 1,
  "username": "testuser",
  "balance": "0.00",
  "created_at": "2025-08-16T10:30:00Z"
}
```

#### Get Account Details
```http
GET /accounts/{account_id}
Authorization: Token abc123def456...
```

**Response:**
```json
{
  "name": "Test User",
  "bank": "Savings Bank",
  "branch": "Main Branch",
  "balance": "1000.00"
}
```

#### List All Accounts
```http
GET /accounts/all
Authorization: Token abc123def456...
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "bank_name": "Savings Bank",
    "branch": "Main Branch",
    "created_at": "2025-08-16T10:30:00Z"
  }
]
```

#### Get Account Balance
```http
GET /accounts/{account_id}/balance
Authorization: Token abc123def456...
```

**Response:**
```json
{
  "balance": "1000.00"
}
```

### Transaction Operations

#### Deposit Money
```http
POST /transactions/deposit
Authorization: Token abc123def456...
Content-Type: application/json

{
  "account_id": 1,
  "amount": "100.00",
  "note": "Initial deposit"
}
```

**Response:**
```json
{
  "id": 1,
  "account_id": 1,
  "amount": "100.00",
  "transaction_type": "DEPOSIT",
  "status": "SUCCESS",
  "note": "Initial deposit",
  "created_at": "2025-08-16T10:30:00Z",
  "new_balance": "100.00"
}
```

#### Withdraw Money
```http
POST /transactions/withdraw
Authorization: Token abc123def456...
Content-Type: application/json

{
  "account_id": 1,
  "amount": "50.00",
  "note": "ATM withdrawal"
}
```

**Response:**
```json
{
  "id": 2,
  "account_id": 1,
  "amount": "50.00",
  "transaction_type": "WITHDRAWAL",
  "status": "SUCCESS",
  "note": "ATM withdrawal",
  "created_at": "2025-08-16T10:35:00Z",
  "new_balance": "50.00"
}
```

#### Transfer Money
```http
POST /transactions/transfer
Authorization: Token abc123def456...
Content-Type: application/json

{
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": "25.00",
  "note": "Payment for services"
}
```

**Response:**
```json
{
  "debit_transaction": {
    "id": 3,
    "account_id": 1,
    "amount": "25.00",
    "transaction_type": "TRANSFER",
    "status": "SUCCESS",
    "note": "Transfer to user2: Payment for services",
    "created_at": "2025-08-16T10:40:00Z"
  },
  "credit_transaction": {
    "id": 4,
    "account_id": 2,
    "amount": "25.00",
    "transaction_type": "TRANSFER",
    "status": "SUCCESS",
    "note": "Transfer from testuser: Payment for services",
    "created_at": "2025-08-16T10:40:00Z"
  },
  "from_account_balance": "25.00",
  "to_account_balance": "25.00",
  "transfer_amount": "25.00"
}
```

#### Get Transaction History
```http
GET /transactions/{account_id}
Authorization: Token abc123def456...
```

**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "amount": "100.00",
    "transaction_type": "DEPOSIT",
    "status": "SUCCESS",
    "note": "Initial deposit",
    "created_at": "2025-08-16T10:30:00Z"
  }
]
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `400` - Bad Request (validation errors, insufficient balance)
- `401` - Unauthorized (missing or invalid token)
- `404` - Not Found (account/user doesn't exist)
- `500` - Internal Server Error

## Example Usage Flow

1. **Create a user account:**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "pass123", "first_name": "Alice", "last_name": "Smith"}'
```

2. **Login to get token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass123"}'
```

3. **Create bank account:**
```bash
curl -X POST http://localhost:8000/accounts \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"bank_name": "My Bank", "branch": "Downtown"}'
```

4. **Make a deposit:**
```bash
curl -X POST http://localhost:8000/transactions/deposit \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"account_id": 1, "amount": "1000.00", "note": "Initial deposit"}'
```

5. **Check balance:**
```bash
curl -X GET http://localhost:8000/accounts/1/balance \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```
