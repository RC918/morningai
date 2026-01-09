"""Test file 5 for HITL 6+ files validation."""
import sys  # F401: unused import - intentional lint error


def calculate_shipping(address: str, weight: float) -> dict:
    """Calculate shipping cost."""
    return {"address": address, "weight": weight, "cost": 9.99}
