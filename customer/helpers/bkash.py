"""bKash Payment Gateway Integration Helper."""

import os
import requests
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class BKashPayment:
    """Helper class for bKash payment gateway integration."""

    # bKash API endpoints (sandbox for testing, production for live)
    SANDBOX_BASE_URL = "https://tokenized.sandbox.bka.sh/v1.2.0-beta"
    PRODUCTION_BASE_URL = "https://tokenized.pay.bka.sh/v1.2.0-beta"

    def __init__(self):
        """Initialize bKash payment with credentials from environment."""
        self.app_key = os.environ.get("BKASH_APP_KEY", "")
        self.app_secret = os.environ.get("BKASH_APP_SECRET", "")
        self.username = os.environ.get("BKASH_USERNAME", "")
        self.password = os.environ.get("BKASH_PASSWORD", "")
        self.is_sandbox = os.environ.get("BKASH_SANDBOX", "True").lower() == "true"
        self.base_url = (
            self.SANDBOX_BASE_URL if self.is_sandbox else self.PRODUCTION_BASE_URL
        )
        self._access_token = None
        self._refresh_token = None

    def get_grant_token(self) -> Optional[str]:
        """
        Get grant token from bKash.

        Returns:
            str: Grant token or None if failed
        """
        url = f"{self.base_url}/tokenized/checkout/token/grant"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": self.username,
            "password": self.password,
        }
        data = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("statusCode") == "0000":
                self._access_token = result.get("id_token")
                self._refresh_token = result.get("refresh_token")
                return self._access_token
            else:
                logger.error(f"bKash grant token error: {result}")
                return None
        except Exception as e:
            logger.error(f"Error getting bKash grant token: {str(e)}")
            return None

    def refresh_access_token(self) -> Optional[str]:
        """
        Refresh the access token using refresh token.

        Returns:
            str: New access token or None if failed
        """
        if not self._refresh_token:
            return self.get_grant_token()

        url = f"{self.base_url}/tokenized/checkout/token/refresh"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self._access_token or "",
            "X-App-Key": self.app_key,
        }
        data = {"refresh_token": self._refresh_token}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("statusCode") == "0000":
                self._access_token = result.get("id_token")
                self._refresh_token = result.get("refresh_token")
                return self._access_token
            else:
                logger.error(f"bKash refresh token error: {result}")
                return self.get_grant_token()  # Fallback to grant token
        except Exception as e:
            logger.error(f"Error refreshing bKash token: {str(e)}")
            return self.get_grant_token()  # Fallback to grant token

    def create_payment(self, amount: float, merchant_invoice_number: str, callback_url: str = None) -> Tuple[bool, Dict]:
        """
        Create a payment request in bKash.

        Args:
            amount: Payment amount
            merchant_invoice_number: Unique invoice number for this payment
            callback_url: Callback URL for payment confirmation (optional)

        Returns:
            tuple: (success: bool, response_data: dict)
        """
        access_token = self._access_token or self.get_grant_token()
        if not access_token:
            return False, {"error": "Failed to get access token"}

        url = f"{self.base_url}/tokenized/checkout/payment/create"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": access_token,
            "X-App-Key": self.app_key,
        }
        data = {
            "mode": "0011",  # Payment mode
            "payerReference": merchant_invoice_number,
            "callbackURL": callback_url or f"{os.environ.get('BKASH_CALLBACK_URL', '')}/api/v1/customers/payments/bkash/callback",
            "amount": str(amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": merchant_invoice_number,
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("statusCode") == "0000":
                return True, {
                    "payment_id": result.get("paymentID"),
                    "bkash_trx_id": result.get("bkashTrxID"),
                    "redirect_url": result.get("bkashURL"),
                    "status": result.get("statusMessage"),
                }
            else:
                logger.error(f"bKash create payment error: {result}")
                return False, {"error": result.get("statusMessage", "Payment creation failed")}
        except Exception as e:
            logger.error(f"Error creating bKash payment: {str(e)}")
            return False, {"error": str(e)}

    def execute_payment(self, payment_id: str) -> Tuple[bool, Dict]:
        """
        Execute/verify a payment in bKash.

        Args:
            payment_id: Payment ID from bKash

        Returns:
            tuple: (success: bool, response_data: dict)
        """
        access_token = self._access_token or self.get_grant_token()
        if not access_token:
            return False, {"error": "Failed to get access token"}

        url = f"{self.base_url}/tokenized/checkout/payment/execute"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": access_token,
            "X-App-Key": self.app_key,
        }
        data = {"paymentID": payment_id}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("statusCode") == "0000":
                return True, {
                    "payment_id": result.get("paymentID"),
                    "bkash_trx_id": result.get("trxID"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency"),
                    "transaction_status": result.get("transactionStatus"),
                    "merchant_invoice_number": result.get("merchantInvoiceNumber"),
                }
            else:
                logger.error(f"bKash execute payment error: {result}")
                return False, {"error": result.get("statusMessage", "Payment execution failed")}
        except Exception as e:
            logger.error(f"Error executing bKash payment: {str(e)}")
            return False, {"error": str(e)}

    def query_payment(self, payment_id: str) -> Tuple[bool, Dict]:
        """
        Query payment status from bKash.

        Args:
            payment_id: Payment ID from bKash

        Returns:
            tuple: (success: bool, response_data: dict)
        """
        access_token = self._access_token or self.get_grant_token()
        if not access_token:
            return False, {"error": "Failed to get access token"}

        url = f"{self.base_url}/tokenized/checkout/payment/query"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": access_token,
            "X-App-Key": self.app_key,
        }
        data = {"paymentID": payment_id}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("statusCode") == "0000":
                return True, {
                    "payment_id": result.get("paymentID"),
                    "bkash_trx_id": result.get("trxID"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency"),
                    "transaction_status": result.get("transactionStatus"),
                    "merchant_invoice_number": result.get("merchantInvoiceNumber"),
                }
            else:
                logger.error(f"bKash query payment error: {result}")
                return False, {"error": result.get("statusMessage", "Payment query failed")}
        except Exception as e:
            logger.error(f"Error querying bKash payment: {str(e)}")
            return False, {"error": str(e)}

