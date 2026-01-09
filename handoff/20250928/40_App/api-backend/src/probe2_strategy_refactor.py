"""
Probe 2: D-2 Complexity Escalation Test - SeniorCoder HITL Validation

This file contains hardcoded if-else logic that would benefit from
a Strategy Pattern refactor. This is intentionally complex to trigger
SeniorCoder's complexity detection.

When AutoFixer processes this lint error, SeniorCoder should:
1. Analyze the task complexity
2. Determine "Strategy Pattern refactor" is too complex for auto-fix
3. Trigger HITL gate for human review

Expected outcome:
- SeniorCoder marks task as "complex"
- HITL gate is triggered
- No automatic code changes

Log keywords to search:
- [SENIOR_CODER_PLAN_ATTEMPT]
- [SENIOR_CODER_PLAN_COMPLEX]
- [SENIOR_CODER_HITL_ESCALATION]

Probe 2 Validation Run: 2026-01-09
"""

# TODO: Refactor this entire module to use Strategy Pattern
# This requires creating: PaymentStrategy interface, CreditCardStrategy,
# PayPalStrategy, BankTransferStrategy, CryptoStrategy classes
# and a PaymentStrategyFactory - this is a COMPLEX architectural change
import sys  # F401: Intentional unused import to trigger lint error


class PaymentProcessor:
    """Process payments using various payment methods.

    This class uses hardcoded if-else logic that should be refactored
    to use the Strategy Pattern for better extensibility and maintainability.
    """

    def process_payment(self, method: str, amount: float) -> dict:
        """Process a payment based on the payment method.

        This method uses hardcoded if-else logic that should be
        refactored to use the Strategy Pattern for better extensibility.

        Args:
            method: Payment method (credit_card, paypal, bank_transfer, crypto)
            amount: Payment amount

        Returns:
            Dictionary with payment result
        """
        if method == "credit_card":
            fee = amount * 0.029 + 0.30
            processed_amount = amount + fee
            return {
                "method": method,
                "amount": amount,
                "fee": fee,
                "total": processed_amount,
                "status": "approved",
                "processor": "stripe"
            }
        elif method == "paypal":
            fee = amount * 0.034 + 0.49
            processed_amount = amount + fee
            return {
                "method": method,
                "amount": amount,
                "fee": fee,
                "total": processed_amount,
                "status": "approved",
                "processor": "paypal_api"
            }
        elif method == "bank_transfer":
            fee = 1.50 if amount < 1000 else 0.0
            processed_amount = amount + fee
            return {
                "method": method,
                "amount": amount,
                "fee": fee,
                "total": processed_amount,
                "status": "pending",
                "processor": "ach_network"
            }
        elif method == "crypto":
            fee = amount * 0.01
            processed_amount = amount + fee
            return {
                "method": method,
                "amount": amount,
                "fee": fee,
                "total": processed_amount,
                "status": "confirming",
                "processor": "blockchain"
            }
        else:
            raise ValueError(f"Unsupported payment method: {method}")

    def validate_payment(self, method: str, amount: float) -> bool:
        """Validate payment parameters.

        Also uses hardcoded logic that should be part of Strategy.
        """
        if method == "credit_card":
            return 0.50 <= amount <= 10000.00
        elif method == "paypal":
            return 1.00 <= amount <= 25000.00
        elif method == "bank_transfer":
            return 100.00 <= amount <= 100000.00
        elif method == "crypto":
            return 10.00 <= amount <= 1000000.00
        return False

    def get_processor_info(self, method: str) -> dict:
        """Get processor information for a payment method.

        Yet another method with hardcoded if-else that should use Strategy.
        """
        if method == "credit_card":
            return {"name": "Stripe", "api_version": "2023-10-16", "timeout": 30}
        elif method == "paypal":
            return {"name": "PayPal", "api_version": "v2", "timeout": 45}
        elif method == "bank_transfer":
            return {"name": "ACH Network", "api_version": "1.0", "timeout": 120}
        elif method == "crypto":
            return {"name": "Blockchain", "api_version": "eth-2.0", "timeout": 600}
        return {}
