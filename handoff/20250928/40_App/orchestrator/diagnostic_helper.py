"""
Diagnostic logging helper for 422 debugging.

This module provides a centralized helper function for formatting diagnostic data
as JSON in log messages. It handles:
- JSON serialization with fallback for non-serializable objects
- Size limits to prevent log truncation
- Consistent formatting with | delimiter
- Version tracking for diagnostic data format

Usage:
    from diagnostic_helper import format_diagnostic
    logger.info(f"[Reviewer] DIAGNOSTIC: LLM raw comment output{format_diagnostic(data)}")

Version History:
    v1.0.0 - Initial implementation with format_diagnostic()
    v1.1.0 - Added DIAGNOSTIC_VERSION for tracking format changes
    v1.2.0 - Added _ts timestamp field for log correlation
"""
import json
import hashlib
import time
from typing import Any, Dict, List, Optional

# Diagnostic format version - increment when changing output structure
DIAGNOSTIC_VERSION = "1.2.0"


# Maximum number of items to include in array samples
MAX_SAMPLE_SIZE = 10
# Maximum length of the JSON string before truncation warning is added
MAX_JSON_LENGTH = 2000


def _safe_serialize(obj: Any) -> Any:
    """Convert non-serializable objects to string representation."""
    if isinstance(obj, set):
        return sorted(list(obj))
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    return str(obj)


def format_commit_id_for_display(commit_id: Optional[str], max_length: int = 8) -> str:
    """
    Format a commit ID for display in logs and diagnostics.

    This function safely truncates a commit SHA for human-readable display
    while preserving enough characters for identification.

    Args:
        commit_id: Full 40-character commit SHA, or None
        max_length: Maximum length to display (default: 8 chars)

    Returns:
        Truncated commit ID or "null" if commit_id is None

    Example:
        >>> format_commit_id_for_display("abc123def456...")
        'abc123de'
        >>> format_commit_id_for_display(None)
        'null'
    """
    if commit_id is None:
        return "null"
    if not isinstance(commit_id, str):
        return "invalid"
    return commit_id[:max_length] if len(commit_id) > max_length else commit_id


def _sample_array(arr: List, max_size: int = MAX_SAMPLE_SIZE) -> Dict:
    """
    Sample an array to reduce size while preserving diagnostic value.

    Returns a dict with:
    - count: total number of items
    - sample: first N items
    - hash: SHA256 hash of full array for comparison (first 8 chars)
    """
    if not arr or not isinstance(arr, list):
        return {"count": 0, "sample": [], "hash": None}

    try:
        # Create hash of full array for comparison
        full_json = json.dumps(arr, default=_safe_serialize, sort_keys=True)
        arr_hash = hashlib.sha256(full_json.encode()).hexdigest()[:8]
    except Exception:
        arr_hash = "error"

    return {
        "count": len(arr),
        "sample": arr[:max_size] if len(arr) > max_size else arr,
        "hash": arr_hash
    }


def format_diagnostic(
    data: Dict[str, Any],
    *,
    sample_keys: Optional[List[str]] = None,
    max_length: int = MAX_JSON_LENGTH
) -> str:
    """
    Format diagnostic data as JSON string for log messages.

    The output JSON always includes two metadata fields:
    - _v: Diagnostic format version (e.g., "1.2.0") for tracking schema changes
    - _ts: Unix timestamp (seconds since epoch) for log correlation across services

    Args:
        data: Dictionary of diagnostic data to format
        sample_keys: List of keys that contain arrays to be sampled
                    (default: raw_comment_structures, payload_structures, allowed_lines_sample)
        max_length: Maximum length of JSON string before adding truncation warning

    Returns:
        String in format " | {json_data}" or " | {fallback_error}" on failure

    Example:
        >>> format_diagnostic({"pr_number": 123, "items": [1,2,3]})
        ' | {"_v":"1.2.0","_ts":1735278000,"pr_number":123,"items":[1,2,3]}'
    """
    if sample_keys is None:
        sample_keys = ["raw_comment_structures", "payload_structures"]

    try:
        # Create a copy to avoid modifying the original
        # Include diagnostic version and timestamp for tracking and correlation
        output_data = {
            "_v": DIAGNOSTIC_VERSION,
            "_ts": int(time.time())
        }

        for key, value in data.items():
            if key in sample_keys and isinstance(value, list):
                # Sample large arrays
                output_data[key] = _sample_array(value)
            elif key == "allowed_lines_sample" and isinstance(value, list):
                # allowed_lines_sample is already sampled, just limit further if needed
                if len(value) > MAX_SAMPLE_SIZE:
                    output_data[key] = value[:MAX_SAMPLE_SIZE]
                    output_data["allowed_lines_total"] = len(value)
                else:
                    output_data[key] = value
            else:
                output_data[key] = value

        # Serialize to JSON
        json_str = json.dumps(output_data, default=_safe_serialize, separators=(',', ':'))

        # Add truncation warning if too long
        if len(json_str) > max_length:
            # Truncate and add warning
            json_str = json_str[:max_length] + '..."_truncated":true}'

        return f" | {json_str}"

    except Exception as e:
        # Fallback: output error info without exposing sensitive data
        fallback = {
            "_diagnostic_error": str(type(e).__name__),
            "_error_message": str(e)[:100],
            "_keys": list(data.keys()) if isinstance(data, dict) else "not_a_dict"
        }
        try:
            return f" | {json.dumps(fallback, separators=(',', ':'))}"
        except Exception:
            return " | {\"_diagnostic_error\":\"serialization_failed\"}"
