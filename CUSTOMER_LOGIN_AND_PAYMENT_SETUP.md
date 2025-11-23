# Customer Login and bKash Payment Integration Guide

This document explains how to use the customer login and bKash payment integration that has been implemented in the billing backend.

## Overview

The system now allows organization customers to:
1. **Login** using their phone number and password
2. **View their profile** and account information
3. **View their payment history**
4. **Make payments via bKash** payment gateway

## Setup Instructions

### 1. Database Migration

Run the migration to add the `login_password` field to the Customer model:

```bash
python manage.py migrate customer
```

### 2. Environment Variables for bKash

Add the following environment variables to your `.env` file:

```env
# bKash Payment Gateway Configuration
BKASH_APP_KEY=your_bkash_app_key
BKASH_APP_SECRET=your_bkash_app_secret
BKASH_USERNAME=your_bkash_username
BKASH_PASSWORD=your_bkash_password
BKASH_SANDBOX=True  # Set to False for production
BKASH_CALLBACK_URL=https://your-domain.com/api/v1/customers/auth/payments/bkash/callback
```

**Note:** Get these credentials from bKash merchant portal.

### 3. Setting Customer Login Passwords

When creating a customer through the admin API, you can optionally provide a `login_password`. If not provided, the system will use the customer's phone number as the default password.

**Example API Request:**
```json
POST /api/v1/customers
{
  "name": "John Doe",
  "phone": "01712345678",
  "email": "john@example.com",
  "package_id": 1,
  "login_password": "secure_password_123"  // Optional
}
```

## API Endpoints

### Customer Authentication

#### 1. Customer Login
```http
POST /api/v1/customers/auth/login
Content-Type: application/json

{
  "phone": "01712345678",
  "password": "customer_password"
}
```

**Response:**
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "access_token_exp": 1234567890,
  "refresh_token_exp": 1234567890,
  "customer": {
    "customer_id": 1,
    "customer_uid": "uuid",
    "name": "John Doe",
    "phone": "01712345678",
    "email": "john@example.com",
    "organization": {
      "id": 1,
      "name": "Organization Name"
    }
  }
}
```

#### 2. Refresh Access Token
```http
POST /api/v1/customers/auth/login/refresh
Content-Type: application/json

{
  "refresh_token": "jwt_refresh_token"
}
```

### Customer Profile and Information

#### 3. Get Customer Profile
```http
GET /api/v1/customers/auth/me
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 1,
  "uid": "uuid",
  "name": "John Doe",
  "phone": "01712345678",
  "email": "john@example.com",
  "package": {
    "id": 1,
    "name": "Premium Package",
    "speed_mbps": 50,
    "price": "1000.00"
  },
  "subscription_end_date": "2024-12-31",
  "is_active": true
}
```

### Customer Payments

#### 4. List Customer Payments
```http
GET /api/v1/customers/auth/payments
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `paid` (optional): Filter by payment status (`true`/`false`)
- `month` (optional): Filter by billing month (e.g., `JANUARY`)
- `year` (optional): Filter by billing year (defaults to current year)

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "uid": "uuid",
      "customer": {...},
      "bill_amount": "1000.00",
      "amount": "1000.00",
      "billing_month": "JANUARY",
      "billing_year": 2024,
      "payment_method": "BKASH",
      "paid": true,
      "transaction_id": "bkash_trx_id",
      "payment_date": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 5. Get Payment Detail
```http
GET /api/v1/customers/auth/payments/{payment_uid}
Authorization: Bearer {access_token}
```

#### 6. Create Payment via bKash
```http
POST /api/v1/customers/auth/payments/create
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "payment_uid": "existing-payment-uid",  // Optional: if paying existing bill
  "amount": 1000.00,
  "billing_month": "JANUARY",  // Optional: for monthly billing
  "billing_year": 2024  // Optional: defaults to current year
}
```

**Response:**
```json
{
  "message": "Payment request created successfully",
  "payment_uid": "payment-uuid",
  "bkash_payment_id": "bkash_payment_id",
  "redirect_url": "https://checkout.bkash.com/...",
  "amount": "1000.00"
}
```

**Next Steps:**
1. Redirect the customer to the `redirect_url` to complete payment
2. After payment, bKash will call the callback endpoint
3. Customer can also manually verify payment using the verify endpoint

#### 7. Verify Payment Status
```http
POST /api/v1/customers/auth/payments/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "payment_id": "bkash_payment_id"
}
```

**Response:**
```json
{
  "payment_uid": "payment-uuid",
  "paid": true,
  "transaction_status": "COMPLETED",
  "amount": "1000.00"
}
```

## Payment Flow

1. **Customer initiates payment:**
   - Customer calls `/api/v1/customers/auth/payments/create`
   - System creates payment record and bKash payment request
   - Returns `redirect_url` to customer

2. **Customer completes payment:**
   - Customer is redirected to bKash checkout page
   - Customer completes payment on bKash

3. **Payment verification:**
   - bKash calls callback endpoint: `/api/v1/customers/auth/payments/bkash/callback`
   - System verifies payment with bKash
   - Payment record is updated as paid
   - Customer account is activated if needed

4. **Manual verification (optional):**
   - Customer can manually verify payment using `/api/v1/customers/auth/payments/verify`

## Security Notes

1. **JWT Tokens:** Customer authentication uses JWT tokens with 7-day access token and 30-day refresh token lifetime.

2. **Password Security:** Customer passwords are hashed using Django's password hashing system.

3. **Token Type:** Customer tokens use `customer_access` and `customer_refresh` token types to distinguish from admin/staff tokens.

4. **Permissions:** All customer endpoints (except login and callback) require customer authentication via `IsCustomer` permission class.

## Testing

### Test Customer Login
1. Create a customer via admin API with a login password
2. Use the customer's phone and password to login
3. Use the returned access token for subsequent requests

### Test bKash Payment (Sandbox)
1. Use bKash sandbox credentials in environment variables
2. Create a payment request
3. Use bKash sandbox test credentials to complete payment
4. Verify payment status

## Troubleshooting

### Customer cannot login
- Check if customer has a `login_password` set
- Verify phone number matches exactly
- Check if customer account is active (`is_active=True`)

### bKash payment fails
- Verify bKash credentials in environment variables
- Check if callback URL is accessible from bKash servers
- Review bKash API logs for error messages
- Ensure payment amount is valid (positive number)

### Payment not updating
- Check bKash callback endpoint is accessible
- Verify payment_id matches between request and callback
- Check database for payment record

## Additional Notes

- Customers can only view and manage their own payments
- Payment creation automatically handles subscription extension for day-based billing
- Customer accounts are automatically activated when payment is completed
- All customer endpoints are prefixed with `/api/v1/customers/auth/` to distinguish from admin endpoints

