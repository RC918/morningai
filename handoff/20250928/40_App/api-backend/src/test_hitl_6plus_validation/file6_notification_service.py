"""Test file 6 for HITL 6+ files validation."""
import sys  # F401: unused import - intentional lint error


def send_notification(user_id: int, message: str) -> dict:
    """Send notification to user."""
    return {"user_id": user_id, "message": message, "sent": True}
