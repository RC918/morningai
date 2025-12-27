"""
Flow Controller v3 - LLM Response Safety Utilities

Shared module for JSON safety checks and LLM response parsing.
Used by both RouterNode and HybridRouter to ensure DRY compliance.

CTO Directive: "DRY (Don't Repeat Yourself) is the highest guiding principle."

This module provides:
- JSON size and nesting depth validation (DoS prevention)
- Safe JSON extraction from LLM responses (handles markdown code blocks)
- Consistent error handling across all router components

Usage:
    from core.flow.llm_safety import (
        check_json_safety,
        extract_json_from_response,
        JSONSafetyError,
        MAX_RESPONSE_SIZE,
        MAX_NESTING_DEPTH,
    )

    # Check safety before parsing
    check_json_safety(response)

    # Extract JSON from potentially markdown-wrapped response
    json_str = extract_json_from_response(response)
    data = json.loads(json_str)
"""
import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


MAX_RESPONSE_SIZE = 10000
MAX_NESTING_DEPTH = 10


class JSONSafetyError(Exception):
    """Raised when JSON response fails safety checks.

    This exception indicates that the LLM response either:
    - Exceeds the maximum allowed size (DoS prevention)
    - Contains excessively nested structures (memory exhaustion prevention)
    """

    pass


def check_json_safety(response: str) -> None:
    """Check JSON response for size and nesting depth limits.

    This prevents DoS attacks via deeply nested payloads or memory exhaustion.
    Should be called BEFORE json.loads() to ensure safe parsing.

    Args:
        response: The raw JSON string to check

    Raises:
        JSONSafetyError: If response exceeds size or nesting limits
    """
    if len(response) > MAX_RESPONSE_SIZE:
        raise JSONSafetyError(
            f"Response size {len(response)} exceeds limit {MAX_RESPONSE_SIZE}"
        )

    depth = 0
    max_depth = 0
    in_string = False
    escape_next = False

    for char in response:
        if escape_next:
            escape_next = False
            continue

        if char == '\\' and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char in '{[':
            depth += 1
            max_depth = max(max_depth, depth)
            if max_depth > MAX_NESTING_DEPTH:
                raise JSONSafetyError(
                    f"Nesting depth {max_depth} exceeds limit {MAX_NESTING_DEPTH}"
                )
        elif char in '}]':
            depth -= 1


def extract_json_from_response(response: str) -> str:
    """Extract JSON string from LLM response, handling markdown code blocks.

    LLMs often wrap JSON in markdown code blocks like:
    ```json
    {"key": "value"}
    ```

    This function extracts the raw JSON string for parsing.

    Args:
        response: Raw LLM response (may contain markdown)

    Returns:
        Cleaned JSON string ready for json.loads()
    """
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if json_match:
        return json_match.group(1)
    return response.strip()


def parse_json_safely(
    response: str,
    log_prefix: str = "[LLMSafety]"
) -> Optional[Dict[str, Any]]:
    """Parse JSON response with full safety checks.

    Combines safety checking and JSON extraction into a single operation.
    Returns None on any failure (caller should handle fallback).

    Args:
        response: Raw LLM response
        log_prefix: Prefix for log messages (e.g., "[RouterNode]", "[HybridRouter]")

    Returns:
        Parsed dict if successful, None if any check fails
    """
    try:
        check_json_safety(response)
        json_str = extract_json_from_response(response)
        data = json.loads(json_str)

        if not isinstance(data, dict):
            logger.warning(
                f"{log_prefix} LLM response is not a dict: {type(data).__name__}"
            )
            return None

        return data

    except JSONSafetyError as e:
        logger.warning(f"{log_prefix} JSON safety check failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"{log_prefix} Failed to parse JSON: {e}")
        return None
