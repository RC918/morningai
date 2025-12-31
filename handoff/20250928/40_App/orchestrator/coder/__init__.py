"""
Coder Agent Module - EPIC D: Autonomous Coder Agent Family

This module provides the Coder agent family for autonomous code generation and fixing.

Components:
- SimpleCoder: Single-file coder agent with Three Don'ts safety guardrails (D-1a)
- GeneralCoder: Multi-file coder agent with atomic commits (D-1b)
- SeniorCoder: Reasoning-first architecture planner (D-2)
- CoderOutput: Structured output schema (status/reason/patch)
- autofix_gate: Gate logic for Router to check auto-fix eligibility

Issue #2761: D-2 Senior Coder Logic (Tier 1)
Issue #2760: D-1 General Coder Agent MVP
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
from .general_coder import (
    GeneralCoder,
    MultiFileCoderOutput,
    FilePatch,
    get_general_coder,
    MAX_FILES_PER_OPERATION,
)
from .senior_coder import (
    SeniorCoder,
    ArchitectureSpec,
    TaskAnalysis,
    TaskComplexity,
    ArchitecturePlan,
    ImplementationStep,
    FileAction,
    ReviewResult,
    get_senior_coder,
    ARCHITECTURE_SPEC_SCHEMA_VERSION,
)
from .autofix_gate import (
    is_autofix_allowed,
    is_path_excluded,
    EXCLUDED_PATHS,
)

__all__ = [
    # SimpleCoder (D-1a)
    "SimpleCoder",
    "CoderOutput",
    "CoderStatus",
    "CODER_OUTPUT_SCHEMA_VERSION",
    "get_simple_coder",
    "validate_python_syntax",
    "is_python_file",
    # GeneralCoder (D-1b)
    "GeneralCoder",
    "MultiFileCoderOutput",
    "FilePatch",
    "get_general_coder",
    "MAX_FILES_PER_OPERATION",
    # SeniorCoder (D-2)
    "SeniorCoder",
    "ArchitectureSpec",
    "TaskAnalysis",
    "TaskComplexity",
    "ArchitecturePlan",
    "ImplementationStep",
    "FileAction",
    "ReviewResult",
    "get_senior_coder",
    "ARCHITECTURE_SPEC_SCHEMA_VERSION",
    # Autofix gate
    "is_autofix_allowed",
    "is_path_excluded",
    "EXCLUDED_PATHS",
]
