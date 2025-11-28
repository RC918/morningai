#!/usr/bin/env python3
"""
Safe Tasks Whitelist - Phase 2 Step A

Defines which task types are safe for automatic code generation.

Design Principles:
- Conservative by default: Only low-risk tasks are allowed
- Explicit whitelist: Tasks must be explicitly added to be considered safe
- Metadata-driven: Each safe task has associated risk and constraint metadata
- Gradual expansion: Whitelist will grow as we gain confidence

Phase 2 Step A Scope:
- Initial whitelist with 9 low-risk task types
- Metadata for risk assessment
- Integration with TaskClassifier

Phase 2 Step B Scope (future):
- Expand whitelist based on success metrics
- Add file path constraints
- Add complexity limits

Known Limitations:
- TaskClassifier Mismatch: Currently only 2 of 9 safe task types
  (documentation_update, test_generation) are produced by TaskClassifier.
  The other 7 types (update_readme, comment_enhancement, fix_lint, fix_typo,
  env_sync, config_update, i18n_update) are reserved for future classifier
  improvements in Phase 2 Step B. This conservative approach ensures we don't
  create unsafe automation while we gather real-world data to improve the
  classifier's task type granularity.
"""
import logging
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)


# Safe Task Types Whitelist
# These task types are considered safe for automatic code generation
# Using frozenset to ensure immutability
#
# NOTE: Currently only 2 of these 9 types (documentation_update, test_generation)
# are produced by TaskClassifier. The other 7 types are reserved for future
# classifier improvements in Phase 2 Step B. This is intentional and conservative.
SAFE_TASK_TYPES: frozenset = frozenset({
    # Documentation tasks (lowest risk)
    "documentation_update",     # Update README, docs, comments [CLASSIFIER PRODUCES]
    "update_readme",            # Specifically README updates [FUTURE]
    "comment_enhancement",      # Add/improve code comments [FUTURE]

    # Testing tasks (low risk, high value)
    "test_generation",          # Generate unit tests [CLASSIFIER PRODUCES]

    # Code quality tasks (low risk)
    "fix_lint",                 # Fix linting errors [FUTURE]
    "fix_typo",                 # Fix typos in code/comments [FUTURE]

    # Configuration tasks (low risk)
    "env_sync",                 # Sync environment variables [FUTURE]
    "config_update",            # Update configuration files [FUTURE]
    "i18n_update",              # Update internationalization files [FUTURE]
})


# Task Metadata
# Provides additional constraints and information for each safe task type
SAFE_TASK_METADATA: Dict[str, Dict[str, Any]] = {
    "documentation_update": {
        "risk_level": "low",
        "max_files": 5,
        "allowed_extensions": [".md", ".rst", ".txt"],
        "allowed_files": ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE"],
        "allowed_directories": ["docs/"],
        "requires_review": False,
        "requires_tests": False,
        "description": "Update documentation files (README, guides, etc.)",
        "examples": [
            "Update README.md with installation instructions",
            "Add API documentation to docs/api.md",
            "Fix typos in CONTRIBUTING.md"
        ]
    },
    "update_readme": {
        "risk_level": "low",
        "max_files": 1,
        "allowed_extensions": [".md"],
        "allowed_files": ["README.md"],
        "allowed_directories": [],
        "requires_review": False,
        "requires_tests": False,
        "description": "Update README.md file",
        "examples": [
            "Add badges to README.md",
            "Update installation section in README",
            "Add usage examples to README"
        ]
    },
    "comment_enhancement": {
        "risk_level": "low",
        "max_files": 3,
        "allowed_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"],
        "allowed_files": [],
        "allowed_directories": ["src/", "lib/", "utils/", "components/", "services/"],
        "requires_review": True,
        "requires_tests": False,
        "description": "Add or improve code comments and docstrings",
        "examples": [
            "Add docstrings to functions in utils.py",
            "Improve inline comments in complex algorithm",
            "Add type hints and documentation"
        ]
    },
    "test_generation": {
        "risk_level": "low",
        "max_files": 5,
        "allowed_extensions": [".py", ".js", ".ts"],
        "allowed_files": [],
        "allowed_directories": ["tests/", "test/", "__tests__/", "spec/"],
        "requires_review": True,
        "requires_tests": True,  # Generated tests should be validated
        "description": "Generate unit tests for existing code",
        "examples": [
            "Generate tests for user_service.py",
            "Add missing test cases for edge conditions",
            "Create integration tests for API endpoints"
        ]
    },
    "fix_lint": {
        "risk_level": "low",
        "max_files": 10,
        "allowed_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"],
        "allowed_files": [],
        "allowed_directories": ["src/", "lib/", "tests/", "components/", "services/", "utils/"],
        "requires_review": False,
        "requires_tests": False,
        "description": "Fix linting errors (formatting, style)",
        "examples": [
            "Fix flake8 errors in backend/",
            "Fix eslint warnings in frontend/",
            "Apply black formatting to Python files"
        ]
    },
    "fix_typo": {
        "risk_level": "low",
        "max_files": 10,
        "allowed_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".txt"],
        "allowed_files": ["README.md"],
        "allowed_directories": ["src/", "lib/", "docs/", "tests/", "components/"],
        "requires_review": False,
        "requires_tests": False,
        "description": "Fix typos in code, comments, or documentation",
        "examples": [
            "Fix typo 'recieve' → 'receive' in comments",
            "Correct spelling errors in error messages",
            "Fix variable name typos"
        ]
    },
    "env_sync": {
        "risk_level": "low",
        "max_files": 3,
        "allowed_extensions": [".env.example", ".env.schema", ".yaml"],
        "allowed_files": [".env.example", "config/env.schema.yaml", "env.schema.yaml"],
        "allowed_directories": [],
        "requires_review": True,
        "requires_tests": False,
        "description": "Sync environment variable examples and schemas",
        "examples": [
            "Add new env var to .env.example",
            "Update env.schema.yaml with new variables",
            "Sync .env.example with .env.schema.yaml"
        ]
    },
    "config_update": {
        "risk_level": "low",
        "max_files": 5,
        "allowed_extensions": [".json", ".yaml", ".yml", ".toml", ".ini"],
        "allowed_files": ["package.json", "pyproject.toml", "tsconfig.json"],
        "allowed_directories": ["config/", ".github/"],
        "requires_review": True,
        "requires_tests": False,
        "description": "Update configuration files",
        "examples": [
            "Update package.json dependencies",
            "Add new config option to settings.yaml",
            "Update CI configuration"
        ]
    },
    "i18n_update": {
        "risk_level": "low",
        "max_files": 10,
        "allowed_extensions": [".json", ".yaml", ".yml", ".po", ".pot"],
        "allowed_files": [],
        "allowed_directories": ["locales/", "i18n/", "translations/", "lang/"],
        "requires_review": True,
        "requires_tests": False,
        "description": "Update internationalization files",
        "examples": [
            "Add Chinese translations to zh-CN.json",
            "Update English strings in en-US.json",
            "Add new translation keys"
        ]
    }
}


def is_safe_task(task_type: str) -> bool:
    """
    Check if a task type is safe for automatic code generation

    Args:
        task_type: Task type from TaskClassifier (e.g., "documentation_update")

    Returns:
        True if task is in safe whitelist, False otherwise

    Example:
        >>> is_safe_task("documentation_update")
        True
        >>> is_safe_task("refactor")
        False
    """
    is_safe = task_type in SAFE_TASK_TYPES

    if is_safe:
        logger.debug(f"[SafeTasks] Task type '{task_type}' is SAFE for code generation")
    else:
        logger.debug(f"[SafeTasks] Task type '{task_type}' is NOT SAFE for code generation")

    return is_safe


def get_safe_task_metadata(task_type: str) -> Dict[str, Any]:
    """
    Get metadata for a safe task type

    Args:
        task_type: Task type from TaskClassifier

    Returns:
        Dict with risk_level, max_files, requires_review, etc.
        Returns empty dict if task type is not in safe whitelist

    Example:
        >>> metadata = get_safe_task_metadata("documentation_update")
        >>> print(metadata["risk_level"])
        'low'
        >>> print(metadata["max_files"])
        5
    """
    if task_type not in SAFE_TASK_TYPES:
        logger.warning(f"[SafeTasks] Task type '{task_type}' not in safe whitelist")
        return {}

    metadata = SAFE_TASK_METADATA.get(task_type, {})

    if not metadata:
        logger.warning(f"[SafeTasks] No metadata found for safe task '{task_type}'")
        # Return default metadata
        return {
            "risk_level": "unknown",
            "max_files": 1,
            "allowed_extensions": [],
            "requires_review": True,
            "requires_tests": False,
            "description": f"Safe task: {task_type}",
            "examples": []
        }

    return metadata


def validate_task_constraints(
    task_type: str,
    file_paths: list,
    file_count: int = None
) -> tuple[bool, str]:
    """
    Validate that a task meets the constraints for its type

    Args:
        task_type: Task type from TaskClassifier
        file_paths: List of file paths to be modified
        file_count: Optional file count (if file_paths not available)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_task_constraints(
        ...     "documentation_update",
        ...     ["README.md", "docs/api.md"]
        ... )
        >>> print(is_valid)
        True
    """
    if not is_safe_task(task_type):
        return False, f"Task type '{task_type}' is not in safe whitelist"

    metadata = get_safe_task_metadata(task_type)

    # Check file count
    actual_file_count = file_count if file_count is not None else len(file_paths)
    max_files = metadata.get("max_files", 1)

    if actual_file_count > max_files:
        return False, (
            f"Task modifies {actual_file_count} files, "
            f"but max allowed for '{task_type}' is {max_files}"
        )

    # Check file extensions
    allowed_extensions = metadata.get("allowed_extensions", [])
    if allowed_extensions and file_paths:
        for file_path in file_paths:
            # Check if file extension matches any allowed extension
            matches = any(file_path.endswith(ext) for ext in allowed_extensions)
            if not matches:
                return False, (
                    f"File '{file_path}' has disallowed extension for '{task_type}'. "
                    f"Allowed: {allowed_extensions}"
                )

    return True, ""


def get_all_safe_tasks() -> Set[str]:
    """
    Get all safe task types

    Returns:
        Set of safe task type strings (mutable copy for external use)

    Example:
        >>> safe_tasks = get_all_safe_tasks()
        >>> print(len(safe_tasks))
        9
        >>> print("documentation_update" in safe_tasks)
        True
    """
    return set(SAFE_TASK_TYPES)


def get_safe_tasks_summary() -> Dict[str, Any]:
    """
    Get summary of safe tasks configuration

    Returns:
        Dict with summary information

    Example:
        >>> summary = get_safe_tasks_summary()
        >>> print(summary["total_safe_tasks"])
        9
        >>> print(summary["risk_levels"])
        {'low': 9}
    """
    risk_levels = {}
    for task_type in SAFE_TASK_TYPES:
        metadata = get_safe_task_metadata(task_type)
        risk_level = metadata.get("risk_level", "unknown")
        risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1

    return {
        "total_safe_tasks": len(SAFE_TASK_TYPES),
        "safe_task_types": list(SAFE_TASK_TYPES),
        "risk_levels": risk_levels,
        "version": "1.0.0-phase2-step-a"
    }


# Logging on module import
logger.info(
    f"[SafeTasks] Loaded {len(SAFE_TASK_TYPES)} safe task types: "
    f"{', '.join(sorted(SAFE_TASK_TYPES))}"
)
