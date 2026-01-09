"""Test file 2 for HITL 6+ files validation."""
import sys  # F401: unused import - intentional lint error


def create_order(user_id: int, items: list) -> dict:
    """Create a new order."""
    return {"user_id": user_id, "items": items, "status": "pending"}
