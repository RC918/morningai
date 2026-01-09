"""Test file 4 for HITL 6+ files validation."""
import sys  # F401: unused import - intentional lint error


def check_inventory(product_id: int) -> dict:
    """Check inventory for a product."""
    return {"product_id": product_id, "quantity": 100, "available": True}
