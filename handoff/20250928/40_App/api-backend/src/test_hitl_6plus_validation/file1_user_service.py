"""Test file 1 for HITL 6+ files validation."""
import sys  # F401: unused import - intentional lint error


def get_user(user_id: int) -> dict:
    """Get user by ID."""
    return {"id": user_id, "name": "Test User"}
