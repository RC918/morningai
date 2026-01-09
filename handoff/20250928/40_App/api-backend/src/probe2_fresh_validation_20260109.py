"""
Probe 2 Fresh Validation: D-2 Complexity Escalation Test - SeniorCoder HITL Validation

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

Fresh Probe 2 Validation Run: 2026-01-09 02:52 UTC
"""

# TODO: Refactor this entire module to use Strategy Pattern
# This requires creating: PaymentStrategy interface, CreditCardStrategy,
# PayPalStrategy, BankTransferStrategy, CryptoStrategy classes
# and a PaymentStrategyFactory - this is a COMPLEX architectural change
import sys  # F401: Intentional unused import to trigger lint error


class OrderProcessor:
    """Order processor with hardcoded if-else logic.
    
    This class intentionally uses hardcoded conditionals that would benefit
    from a Strategy Pattern refactor. This is designed to trigger SeniorCoder's
    complexity detection.
    """
    
    def __init__(self):
        self.supported_types = ["standard", "express", "overnight", "international"]
        self.order_log = []
    
    def process_order(self, order_type: str, amount: float, destination: str = "US") -> dict:
        """Process an order using the specified shipping type.
        
        This method uses hardcoded if-else logic that should be refactored
        to use the Strategy Pattern for better maintainability.
        """
        if order_type == "standard":
            return self._process_standard(amount, destination)
        elif order_type == "express":
            return self._process_express(amount, destination)
        elif order_type == "overnight":
            return self._process_overnight(amount, destination)
        elif order_type == "international":
            return self._process_international(amount, destination)
        else:
            return {"success": False, "error": f"Unsupported order type: {order_type}"}
    
    def _process_standard(self, amount: float, destination: str) -> dict:
        shipping = 5.99 if amount < 50 else 0
        total = amount + shipping
        self.order_log.append({"type": "standard", "total": total})
        return {"success": True, "type": "standard", "total": total, "shipping": shipping}
    
    def _process_express(self, amount: float, destination: str) -> dict:
        shipping = 12.99
        total = amount + shipping
        self.order_log.append({"type": "express", "total": total})
        return {"success": True, "type": "express", "total": total, "shipping": shipping}
    
    def _process_overnight(self, amount: float, destination: str) -> dict:
        shipping = 24.99
        total = amount + shipping
        self.order_log.append({"type": "overnight", "total": total})
        return {"success": True, "type": "overnight", "total": total, "shipping": shipping}
    
    def _process_international(self, amount: float, destination: str) -> dict:
        base_shipping = 29.99
        customs_fee = amount * 0.05
        total = amount + base_shipping + customs_fee
        self.order_log.append({"type": "international", "total": total})
        return {"success": True, "type": "international", "total": total, "shipping": base_shipping, "customs": customs_fee}
    
    def get_order_history(self) -> list:
        return self.order_log.copy()
    
    def calculate_total_shipping(self) -> float:
        return sum(o.get("shipping", 0) for o in self.order_log if "shipping" in o)
