#!/usr/bin/env python3
"""
Semantic Rules v3 - Phase 1 Security Foundation

Enhanced semantic task rules for ProjectEngineerAgent:
- Directory restrictions with path normalization
- Task type restrictions
- Path traversal prevention (../ escape)
- Integration with existing safe_tasks.py
- NEW: Action restrictions (allowed_actions whitelist)
- NEW: Sensitive file/path blocking
- NEW: High-risk operation detection

Design Principles:
- Defense in depth: Multiple layers of validation
- Fail-safe defaults: Deny by default, allow explicitly
- Path normalization: Prevent directory traversal attacks
- Configurable: All rules configurable via environment variables
- Hard gate: Physical blocking at validation layer (not advisory)
"""
import logging
import os
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# High-risk actions that require Human-in-the-Loop approval
HIGH_RISK_ACTIONS: frozenset = frozenset({
    "DROP TABLE",
    "DROP DATABASE",
    "DELETE FROM",
    "TRUNCATE",
    "ALTER TABLE",
    "rm -rf",
    "rm -r",
    "sudo rm",
    "chmod 777",
    "chown",
})

# Sensitive file patterns that should never be modified by agents
# Phase 1 Security Foundation - Minimal Blocklist (PR #1943 revision)
#
# This blocklist only includes files that should NEVER be modified by agents:
# - Private keys and certificates (highest risk of credential exposure)
# - Explicit secrets files (secrets.yaml, secrets.yml)
# - Package manager auth tokens (.npmrc, .pypirc)
#
# Files NOT blocked (Agent can modify with caution):
# - .env files: May need modification for configuration
# - Deployment configs: render.yaml, vercel.json, fly.toml, docker-compose.*, etc.
# - Cloud credentials: Read-only in practice, but not blocked
#
# Operators can extend this list via PROJECT_ENGINEER_BLOCKED_FILE_PATTERNS if needed.
SENSITIVE_FILE_PATTERNS: frozenset = frozenset({
    # Private keys and certificates (NEVER modify)
    "private_key",
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    ".p12",  # PKCS#12 certificate files
    ".pfx",  # Windows certificate files
    # Explicit secrets files (NEVER modify)
    "secrets.yaml",
    "secrets.yml",
    # Package manager auth tokens (NEVER modify)
    ".npmrc",  # NPM auth tokens
    ".pypirc",  # PyPI auth tokens
})

# Comma-separated string version of SENSITIVE_FILE_PATTERNS for settings.py default value
# This ensures settings.py and semantic_rules.py stay in sync
SENSITIVE_FILE_PATTERNS_CSV: str = ",".join(sorted(SENSITIVE_FILE_PATTERNS))

# Default allowed actions for agents (conservative whitelist)
DEFAULT_ALLOWED_ACTIONS: frozenset = frozenset({
    "read_file",
    "write_file",
    "create_file",
    "list_directory",
    "search_code",
    "run_tests",
    "run_lint",
    "create_pr",
    "add_comment",
    "update_documentation",
})


@dataclass
class SemanticRuleViolation:
    """Represents a semantic rule violation"""
    rule_type: str  # "directory", "task_type", "path_traversal", "repo", "action", "sensitive_file", "high_risk"
    message: str
    severity: str  # "error", "warning", "critical"
    details: Optional[str] = None
    requires_approval: bool = False  # If True, requires Human-in-the-Loop approval


class SemanticRulesValidator:
    """
    Validates semantic rules for ProjectEngineerAgent tasks.

    Phase 4 PR-1 Features:
    - Directory prefix validation (PROJECT_ENGINEER_ALLOWED_DIRECTORIES)
    - Task type validation (PROJECT_ENGINEER_ALLOWED_TASK_TYPES)
    - Path normalization and traversal prevention
    - Repository validation (existing from Phase 3 PR-4)
    """

    def __init__(self):
        """Initialize validator with settings from environment"""
        self._load_settings()

    def _load_settings(self):
        """Load settings from environment or use defaults"""
        try:
            from common.config.settings import settings
            self.allowed_directories = self._parse_list(
                settings.project_engineer_allowed_directories
            )
            self.allowed_repos = self._parse_list(
                settings.project_engineer_allowed_repos
            )
            # Phase 4 PR-1
            self.allowed_task_types = self._parse_list(
                getattr(settings, 'project_engineer_allowed_task_types', '')
            )
            # Phase 1 Security Foundation - NEW
            self.allowed_actions = self._parse_list(
                getattr(settings, 'project_engineer_allowed_actions', '')
            )
            self.blocked_file_patterns = self._parse_list(
                getattr(settings, 'project_engineer_blocked_files', '')
            )
            self.require_hitl_for_high_risk = getattr(
                settings, 'project_engineer_require_hitl_high_risk', True
            )
            logger.info(
                "[SemanticRules] Loaded settings: "
                f"allowed_directories={self.allowed_directories}, "
                f"allowed_repos={self.allowed_repos}, "
                f"allowed_task_types={self.allowed_task_types}, "
                f"allowed_actions={self.allowed_actions}, "
                f"blocked_file_patterns={self.blocked_file_patterns}, "
                f"require_hitl_for_high_risk={self.require_hitl_for_high_risk}"
            )
        except (ImportError, AttributeError) as e:
            logger.warning(f"[SemanticRules] Failed to load settings: {e}, using defaults")
            self.allowed_directories = ["docs/", "tests/", "handoff/"]
            self.allowed_repos = ["RC918/morningai"]
            self.allowed_task_types = []  # Empty means all safe task types allowed
            self.allowed_actions = list(DEFAULT_ALLOWED_ACTIONS)  # Use default whitelist
            self.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)  # Block sensitive files
            self.require_hitl_for_high_risk = True  # Require approval for high-risk actions

    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list, filtering empty values"""
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    def normalize_path(self, path: str) -> Tuple[str, bool]:
        """
        Normalize a file path and detect traversal attempts.

        Args:
            path: File path to normalize

        Returns:
            Tuple of (normalized_path, is_safe)
            - normalized_path: The normalized path (or original if unsafe)
            - is_safe: True if path is safe, False if traversal detected
        """
        if not path:
            return "", True

        # Remove leading/trailing whitespace
        path = path.strip()

        # Detect obvious traversal patterns before normalization
        traversal_patterns = [
            r'\.\.',           # .. anywhere
            r'^\./',           # ./ at start only
            r'/\./',           # /./ anywhere
            r'//+',            # multiple slashes
            r'%2e%2e',         # URL-encoded ..
            r'%2f',            # URL-encoded /
            r'\\',             # backslash (Windows path)
        ]

        for pattern in traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"[SemanticRules] Path traversal pattern detected: {pattern} in {path}")
                return path, False

        # Normalize the path
        # 1. Convert to forward slashes
        normalized = path.replace('\\', '/')

        # 2. Remove leading slash for relative path comparison
        if normalized.startswith('/'):
            normalized = normalized[1:]

        # 3. Use os.path.normpath to resolve . and .. (but we already rejected ..)
        # We use a custom normalization to avoid os.path.normpath resolving ..
        parts = []
        for part in normalized.split('/'):
            if part == '.' or part == '':
                continue
            if part == '..':
                # This should have been caught above, but double-check
                logger.warning(f"[SemanticRules] Path traversal detected in normalization: {path}")
                return path, False
            parts.append(part)

        normalized = '/'.join(parts)

        # 4. Ensure no absolute path escapes
        if os.path.isabs(normalized):
            logger.warning(f"[SemanticRules] Absolute path detected: {path}")
            return path, False

        return normalized, True

    def validate_directory(self, file_path: str) -> Tuple[bool, Optional[SemanticRuleViolation]]:
        """
        Validate that a file path is within allowed directories.

        Args:
            file_path: File path to validate

        Returns:
            Tuple of (is_valid, violation)
        """
        if not self.allowed_directories:
            # Empty list means all directories allowed
            return True, None

        # Normalize the path
        normalized_path, is_safe = self.normalize_path(file_path)

        if not is_safe:
            return False, SemanticRuleViolation(
                rule_type="path_traversal",
                message=f"Path traversal detected in '{file_path}'",
                severity="error",
                details="Path contains traversal patterns (../, ./, etc.) which are not allowed"
            )

        # Check if path starts with any allowed directory prefix
        for allowed_dir in self.allowed_directories:
            # Normalize the allowed directory. An empty or root-only entry allows all paths.
            allowed_normalized = allowed_dir.strip().strip('/')
            if not allowed_normalized:
                logger.debug(f"[SemanticRules] Path '{file_path}' allowed by root-level rule ('{allowed_dir}')")
                return True, None

            # Check if the file path starts with the allowed directory
            if normalized_path.startswith(allowed_normalized + '/') or normalized_path == allowed_normalized:
                logger.debug(f"[SemanticRules] Path '{file_path}' allowed (matches '{allowed_dir}')")
                return True, None

        # Path not in any allowed directory
        return False, SemanticRuleViolation(
            rule_type="directory",
            message=f"File '{file_path}' is not in allowed directories",
            severity="error",
            details=f"Allowed directories: {', '.join(self.allowed_directories)}"
        )

    def validate_task_type(self, task_type: str) -> Tuple[bool, Optional[SemanticRuleViolation]]:
        """
        Validate that a task type is allowed.

        Args:
            task_type: Task type to validate

        Returns:
            Tuple of (is_valid, violation)
        """
        if not self.allowed_task_types:
            # Empty list means all safe task types allowed
            # Delegate to safe_tasks.py for the actual check
            if self._is_safe_task(task_type):
                return True, None
            return False, SemanticRuleViolation(
                rule_type="task_type",
                message=f"Task type '{task_type}' is not in safe whitelist",
                severity="error",
                details="Task must be in SAFE_TASK_TYPES to be automated"
            )

        # Check against explicit allowed list
        if task_type in self.allowed_task_types:
            return True, None

        return False, SemanticRuleViolation(
            rule_type="task_type",
            message=f"Task type '{task_type}' is not in allowed task types",
            severity="error",
            details=f"Allowed task types: {', '.join(self.allowed_task_types)}"
        )

    def _is_safe_task(self, task_type: str) -> bool:
        """
        Check if task type is in safe whitelist.
        Wrapper to handle import issues in different contexts.
        Uses importlib for cleaner import path iteration.
        """
        from importlib import import_module

        import_paths = [
            ('.safe_tasks', __package__),  # Relative import
            ('safe_tasks', None),          # Absolute import
            ('project_engineer.safe_tasks', None)  # Full path import
        ]

        for module_name, package in import_paths:
            try:
                module = import_module(module_name, package=package)
                if hasattr(module, 'is_safe_task'):
                    return module.is_safe_task(task_type)
            except (ImportError, ModuleNotFoundError, ValueError, TypeError):
                # ValueError/TypeError can occur if __package__ is None for relative imports
                continue

        logger.warning("[SemanticRules] Could not import is_safe_task, defaulting to False")
        return False

    def validate_repo(self, repo: str) -> Tuple[bool, Optional[SemanticRuleViolation]]:
        """
        Validate that a repository is allowed.

        Args:
            repo: Repository name (owner/repo format)

        Returns:
            Tuple of (is_valid, violation)
        """
        if not self.allowed_repos:
            # Empty list means all repos allowed
            return True, None

        if repo in self.allowed_repos:
            return True, None

        return False, SemanticRuleViolation(
            rule_type="repo",
            message=f"Repository '{repo}' is not in allowed repositories",
            severity="error",
            details=f"Allowed repositories: {', '.join(self.allowed_repos)}"
        )

    def validate_action(self, action: str) -> Tuple[bool, Optional[SemanticRuleViolation]]:
        """
        Validate that an action is allowed (Phase 1 Security Foundation).

        Args:
            action: Action name to validate (e.g., "read_file", "write_file")

        Returns:
            Tuple of (is_valid, violation)
        """
        # First check if it's a high-risk action
        for high_risk in HIGH_RISK_ACTIONS:
            if high_risk.lower() in action.lower():
                if self.require_hitl_for_high_risk:
                    return False, SemanticRuleViolation(
                        rule_type="high_risk",
                        message=f"Action '{action}' is high-risk and requires Human-in-the-Loop approval",
                        severity="critical",
                        details=f"High-risk pattern detected: '{high_risk}'. This action requires manual approval.",
                        requires_approval=True
                    )
                else:
                    logger.warning(f"[SemanticRules] High-risk action '{action}' allowed (HITL disabled)")

        # Check against allowed actions whitelist
        if not self.allowed_actions:
            # Empty list means use default allowed actions
            if action in DEFAULT_ALLOWED_ACTIONS:
                return True, None
        else:
            if action in self.allowed_actions:
                return True, None

        return False, SemanticRuleViolation(
            rule_type="action",
            message=f"Action '{action}' is not in allowed actions whitelist",
            severity="error",
            details=f"Allowed actions: {', '.join(self.allowed_actions or DEFAULT_ALLOWED_ACTIONS)}"
        )

    def validate_sensitive_file(self, file_path: str) -> Tuple[bool, Optional[SemanticRuleViolation]]:
        """
        Validate that a file is not a sensitive file (Phase 1 Security Foundation).

        Args:
            file_path: File path to validate

        Returns:
            Tuple of (is_valid, violation)
        """
        if not file_path:
            return True, None

        # Normalize the path
        normalized_path, is_safe = self.normalize_path(file_path)
        if not is_safe:
            return False, SemanticRuleViolation(
                rule_type="path_traversal",
                message=f"Path traversal detected in '{file_path}'",
                severity="error",
                details="Path contains traversal patterns which are not allowed"
            )

        # Get the filename from the path
        filename = os.path.basename(normalized_path)

        # Check against blocked file patterns
        blocked_patterns = self.blocked_file_patterns or SENSITIVE_FILE_PATTERNS
        for pattern in blocked_patterns:
            # Handle wildcard patterns
            if pattern.startswith("*."):
                if filename.endswith(pattern[1:]):
                    return False, SemanticRuleViolation(
                        rule_type="sensitive_file",
                        message=f"File '{file_path}' matches sensitive file pattern '{pattern}'",
                        severity="critical",
                        details="Modifying sensitive files is not allowed. This includes credentials, secrets, and deployment configs.",
                        requires_approval=True
                    )
            else:
                # Exact match or contains pattern
                if pattern in filename or pattern in normalized_path:
                    return False, SemanticRuleViolation(
                        rule_type="sensitive_file",
                        message=f"File '{file_path}' matches sensitive file pattern '{pattern}'",
                        severity="critical",
                        details="Modifying sensitive files is not allowed. This includes credentials, secrets, and deployment configs.",
                        requires_approval=True
                    )

        return True, None

    def validate_command(self, command: str) -> Tuple[bool, Optional[SemanticRuleViolation]]:
        """
        Validate that a shell command doesn't contain high-risk operations (Phase 1 Security Foundation).

        Args:
            command: Shell command to validate

        Returns:
            Tuple of (is_valid, violation)
        """
        if not command:
            return True, None

        # Check for high-risk patterns in the command
        for high_risk in HIGH_RISK_ACTIONS:
            if high_risk.lower() in command.lower():
                if self.require_hitl_for_high_risk:
                    return False, SemanticRuleViolation(
                        rule_type="high_risk",
                        message=f"Command contains high-risk operation: '{high_risk}'",
                        severity="critical",
                        details=f"Command: '{command[:100]}...' requires Human-in-the-Loop approval.",
                        requires_approval=True
                    )
                else:
                    logger.warning(f"[SemanticRules] High-risk command allowed (HITL disabled): {command[:50]}...")

        return True, None

    def validate_file_paths(self, file_paths: List[str]) -> Tuple[bool, List[SemanticRuleViolation]]:
        """
        Validate multiple file paths.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Tuple of (all_valid, violations)
        """
        violations = []

        for path in file_paths:
            is_valid, violation = self.validate_directory(path)
            if not is_valid and violation:
                violations.append(violation)

        return len(violations) == 0, violations

    def validate_task(
        self,
        repo: str,
        task_type: str,
        file_paths: Optional[List[str]] = None,
        action: Optional[str] = None,
        command: Optional[str] = None
    ) -> Tuple[bool, List[SemanticRuleViolation]]:
        """
        Validate all semantic rules for a task (Phase 1 Security Foundation).

        Args:
            repo: Repository name
            task_type: Task type
            file_paths: Optional list of file paths
            action: Optional action name to validate
            command: Optional shell command to validate

        Returns:
            Tuple of (is_valid, violations)
        """
        violations = []

        # Validate repository
        is_valid, violation = self.validate_repo(repo)
        if not is_valid and violation:
            violations.append(violation)

        # Validate task type
        is_valid, violation = self.validate_task_type(task_type)
        if not is_valid and violation:
            violations.append(violation)

        # Validate file paths if provided
        if file_paths:
            _, path_violations = self.validate_file_paths(file_paths)
            violations.extend(path_violations)

            # Also check for sensitive files (Phase 1 Security Foundation)
            for file_path in file_paths:
                is_valid, violation = self.validate_sensitive_file(file_path)
                if not is_valid and violation:
                    violations.append(violation)

        # Validate action if provided (Phase 1 Security Foundation)
        if action:
            is_valid, violation = self.validate_action(action)
            if not is_valid and violation:
                violations.append(violation)

        # Validate command if provided (Phase 1 Security Foundation)
        if command:
            is_valid, violation = self.validate_command(command)
            if not is_valid and violation:
                violations.append(violation)

        return len(violations) == 0, violations


# Module-level validator instance (lazy initialization)
_validator: Optional[SemanticRulesValidator] = None


def get_validator() -> SemanticRulesValidator:
    """Get or create the semantic rules validator instance"""
    global _validator
    if _validator is None:
        _validator = SemanticRulesValidator()
    return _validator


def validate_directory(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a single file path.

    Args:
        file_path: File path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    is_valid, violation = validator.validate_directory(file_path)
    if violation:
        return False, violation.message
    return True, None


def validate_task_type(task_type: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a task type.

    Args:
        task_type: Task type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    is_valid, violation = validator.validate_task_type(task_type)
    if violation:
        return False, violation.message
    return True, None


def validate_repo(repo: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a repository.

    Args:
        repo: Repository name (owner/repo format)

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    is_valid, violation = validator.validate_repo(repo)
    if violation:
        return False, violation.message
    return True, None


def normalize_path(path: str) -> Tuple[str, bool]:
    """
    Convenience function to normalize a path.

    Args:
        path: File path to normalize

    Returns:
        Tuple of (normalized_path, is_safe)
    """
    validator = get_validator()
    return validator.normalize_path(path)


def validate_task(
    repo: str,
    task_type: str,
    file_paths: Optional[List[str]] = None,
    action: Optional[str] = None,
    command: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate all semantic rules for a task.

    Args:
        repo: Repository name
        task_type: Task type
        file_paths: Optional list of file paths
        action: Optional action name to validate
        command: Optional shell command to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = get_validator()
    is_valid, violations = validator.validate_task(repo, task_type, file_paths, action, command)
    error_messages = [v.message for v in violations]
    return is_valid, error_messages


def validate_action(action: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate an action (Phase 1 Security Foundation).

    Args:
        action: Action name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    is_valid, violation = validator.validate_action(action)
    if violation:
        return False, violation.message
    return True, None


def validate_sensitive_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a file is not sensitive (Phase 1 Security Foundation).

    Args:
        file_path: File path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    is_valid, violation = validator.validate_sensitive_file(file_path)
    if violation:
        return False, violation.message
    return True, None


def validate_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a shell command (Phase 1 Security Foundation).

    Args:
        command: Shell command to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = get_validator()
    is_valid, violation = validator.validate_command(command)
    if violation:
        return False, violation.message
    return True, None


def get_security_summary() -> dict:
    """
    Get summary of security configuration (Phase 1 Security Foundation).

    Returns:
        Dict with security configuration summary
    """
    validator = get_validator()
    return {
        "allowed_directories": validator.allowed_directories,
        "allowed_repos": validator.allowed_repos,
        "allowed_task_types": validator.allowed_task_types,
        "allowed_actions": validator.allowed_actions or list(DEFAULT_ALLOWED_ACTIONS),
        "blocked_file_patterns": validator.blocked_file_patterns or list(SENSITIVE_FILE_PATTERNS),
        "high_risk_actions": list(HIGH_RISK_ACTIONS),
        "require_hitl_for_high_risk": validator.require_hitl_for_high_risk,
        "version": "3.0.0-phase1-security-foundation"
    }


# Logging on module import
logger.info("[SemanticRules] Module loaded - Phase 1 Security Foundation (Semantic Rules v3)")
