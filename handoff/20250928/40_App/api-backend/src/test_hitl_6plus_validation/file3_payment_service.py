"""Test file 3 for HITL 6+ files validation."""
import sys  # F401: unused import - intentional lint error


def process_payment(order_id: int, amount: float) -> dict:
    """Process payment for an order."""
    return {"order_id": order_id, "amount": amount, "status": "completed"}
