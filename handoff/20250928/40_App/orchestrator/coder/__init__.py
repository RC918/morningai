"""
Coder Agent Module - EPIC D: Autonomous Coder Agent Family

This module provides the SimpleCoder agent for D-1 Phase 0 (proof-of-life).

Components:
- SimpleCoder: Minimal coder agent with Three Don'ts safety guardrails
- CoderOutput: Structured output schema (status/reason/patch)
- autofix_gate: Gate logic for Router to check auto-fix eligibility

Issue #3211: D-1.1 Coder Three Don'ts Safety Guardrails
Parent Issue #2760: D-1 General Coder Agent MVP
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
"""

from .simple_coder import (
    SimpleCoder,
    CoderOutput,
    CoderStatus,
    CODER_OUTPUT_SCHEMA_VERSION,
    get_simple_coder,
    validate_python_syntax,
    is_python_file,
)
from .autofix_gate import (
    is_autofix_allowed,
    is_path_excluded,
    EXCLUDED_PATHS,
)

__all__ = [
    "SimpleCoder",
    "CoderOutput",
    "CoderStatus",
    "CODER_OUTPUT_SCHEMA_VERSION",
    "get_simple_coder",
    "validate_python_syntax",
    "is_python_file",
    "is_autofix_allowed",
    "is_path_excluded",
    "EXCLUDED_PATHS",
]
