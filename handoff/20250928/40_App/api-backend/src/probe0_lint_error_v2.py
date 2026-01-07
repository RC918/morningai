# handoff/20250928/40_App/api-backend/src/probe0_lint_error_v2.py

from django.utils import timezone
from django.core.exceptions import ValidationError

def validate_timestamp(timestamp):
    if timestamp > timezone.now():
        raise ValidationError("Timestamp cannot be in the future.")
    return timestamp