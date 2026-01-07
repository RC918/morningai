"""
Schema Drift Test Helpers - D-1.3.2

Issue #3249: Refactor schema drift tests with helper abstractions
Parent Issue #3214: Automated Schema/Prompt Drift Detection
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family

This module provides helper functions to abstract common operations in
schema drift tests, reducing test/design over-binding and providing a
single point of change when prompt structure changes.
"""
from typing import Optional, Set

from coder.simple_coder import (
    CODER_LLM_RESPONSE_FIELDS,
    CODER_SYSTEM_ADDED_FIELDS,
)


# Anchor text used to locate JSON schema section in prompts
# Updated for P5 prompt strengthening - the anchor is now in the CRITICAL section
PROMPT_JSON_SCHEMA_ANCHOR = "REQUIRED JSON FORMAT"


def extract_prompt_schema_section(prompt: str) -> Optional[str]:
    """Extract the JSON schema section from a prompt string.

    The JSON schema section is identified by finding the anchor text
    that introduces the schema definition. This is more robust than
    regex matching braces.

    Args:
        prompt: The full prompt string containing a JSON schema section.

    Returns:
        The portion of the prompt starting from the JSON schema anchor,
        or None if the anchor is not found.

    Example:
        >>> prompt = "Some text... You MUST respond with ONLY a JSON object..."
        >>> section = extract_prompt_schema_section(prompt)
        >>> "schema_version" not in section  # System fields shouldn't be here
        True
    """
    anchor_pos = prompt.find(PROMPT_JSON_SCHEMA_ANCHOR)
    if anchor_pos == -1:
        return None
    return prompt[anchor_pos:]


def get_expected_output_keys(output_type: str) -> Set[str]:
    """Get expected keys for a given output type.

    Args:
        output_type: One of "llm_response", "system_added", or "all".

    Returns:
        A set of field names expected in the output.

    Raises:
        ValueError: If output_type is not recognized.

    Example:
        >>> llm_fields = get_expected_output_keys("llm_response")
        >>> "status" in llm_fields
        True
        >>> "schema_version" in llm_fields
        False
    """
    if output_type == "llm_response":
        return set(CODER_LLM_RESPONSE_FIELDS)
    elif output_type == "system_added":
        return set(CODER_SYSTEM_ADDED_FIELDS)
    elif output_type == "all":
        return set(CODER_LLM_RESPONSE_FIELDS | CODER_SYSTEM_ADDED_FIELDS)
    else:
        raise ValueError(
            f'Unknown output_type: "{output_type}". '
            'Expected one of: "llm_response", "system_added", "all"'
        )


def validate_schema_field(field: str, schema_section: str) -> bool:
    """Check if a field is mentioned in a schema section.

    This performs a case-sensitive search for the field name,
    looking for it as a quoted JSON key (JSON keys are case-sensitive).

    Args:
        field: The field name to search for.
        schema_section: The schema section string to search in.

    Returns:
        True if the field is found in the schema section, False otherwise.

    Example:
        >>> section = '{"status": "skipped", "reason": "..."}'
        >>> validate_schema_field("status", section)
        True
        >>> validate_schema_field("unknown", section)
        False
    """
    quoted_field = f'"{field}"'
    return quoted_field in schema_section


def validate_field_not_in_schema(field: str, schema_section: str) -> bool:
    """Check that a field is NOT mentioned as a JSON key in a schema section.

    This is the inverse of validate_schema_field, useful for verifying
    that system-added fields are not requested from the LLM. Checks for
    the quoted field name to avoid false positives from field names
    appearing in descriptions or values.

    Args:
        field: The field name that should NOT be present as a JSON key.
        schema_section: The schema section string to search in.

    Returns:
        True if the field is NOT found as a JSON key, False otherwise.

    Example:
        >>> section = '{"status": "skipped"}'
        >>> validate_field_not_in_schema("schema_version", section)
        True
    """
    return not validate_schema_field(field, schema_section)
