"""
Probe 2 Re-validation: D-2 Complexity Escalation Test - SeniorCoder HITL Validation

This file tests the fix from PR #3722 which allows SeniorCoder to be invoked
for single-file CI failures.

When AutoFixer processes this lint error, the NEW flow should be:
1. [SENIOR_CODER_GATE_CI_FAILURE] - CI failure trigger detected
2. [SENIOR_CODER_GATE_PASS] - Gate passes
3. [SENIOR_CODER_SINGLE_FILE_CI_FAILURE] - NEW: Single file CI failure, SeniorCoder invoked
4. [SENIOR_CODER_PLAN_ATTEMPT] - SeniorCoder planning starts
5. If complex: [SENIOR_CODER_HITL_ESCALATION] - HITL gate triggered

Expected outcome after PR #3722 fix:
- SeniorCoder should now be invoked for single-file CI failures
- [SENIOR_CODER_PLAN_ATTEMPT] should appear in logs (was missing before)

Probe 2 Re-validation Run: 2026-01-09
"""

# TODO: Refactor this entire module to use Strategy Pattern
# This requires creating: PaymentStrategy interface, CreditCardStrategy,
# PayPalStrategy, BankTransferStrategy, CryptoStrategy classes
# and a PaymentStrategyFactory - this is a COMPLEX architectural change
import sys  # F401: Intentional unused import to trigger lint error


class PaymentProcessor:
    """Payment processor with hardcoded if-else logic.
    
    This class intentionally uses hardcoded conditionals that would benefit
    from a Strategy Pattern refactor. This is designed to trigger SeniorCoder's
    complexity detection.
    """
    
    def __init__(self):
        self.supported_methods = ["credit_card", "paypal", "bank_transfer", "crypto"]
        self.transaction_log = []
    
    def process_payment(self, method: str, amount: float, currency: str = "USD") -> dict:
        """Process a payment using the specified method.
        
        This method uses hardcoded if-else logic that should be refactored
        to use the Strategy Pattern for better maintainability.
        """
        if method == "credit_card":
            return self._process_credit_card(amount, currency)
        elif method == "paypal":
            return self._process_paypal(amount, currency)
        elif method == "bank_transfer":
            return self._process_bank_transfer(amount, currency)
        elif method == "crypto":
            return self._process_crypto(amount, currency)
        else:
            return {"success": False, "error": f"Unsupported payment method: {method}"}
    
    def _process_credit_card(self, amount: float, currency: str) -> dict:
        fee = amount * 0.029 + 0.30
        total = amount + fee
        self.transaction_log.append({"method": "credit_card", "amount": total})
        return {"success": True, "method": "credit_card", "total": total, "fee": fee}
    
    def _process_paypal(self, amount: float, currency: str) -> dict:
        fee = amount * 0.034 + 0.49
        total = amount + fee
        self.transaction_log.append({"method": "paypal", "amount": total})
        return {"success": True, "method": "paypal", "total": total, "fee": fee}
    
    def _process_bank_transfer(self, amount: float, currency: str) -> dict:
        fee = 25.00 if amount > 1000 else 15.00
        total = amount + fee
        self.transaction_log.append({"method": "bank_transfer", "amount": total})
        return {"success": True, "method": "bank_transfer", "total": total, "fee": fee}
    
    def _process_crypto(self, amount: float, currency: str) -> dict:
        fee = amount * 0.01
        total = amount + fee
        self.transaction_log.append({"method": "crypto", "amount": total})
        return {"success": True, "method": "crypto", "total": total, "fee": fee}
    
    def get_transaction_history(self) -> list:
        return self.transaction_log.copy()
    
    def calculate_total_fees(self) -> float:
        return sum(t.get("fee", 0) for t in self.transaction_log if "fee" in t)
