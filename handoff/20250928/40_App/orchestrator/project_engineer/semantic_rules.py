#!/usr/bin/env python3
"""
Semantic Rules v2 - Phase 4 PR-1

Enhanced semantic task rules for ProjectEngineerAgent:
- Directory restrictions with path normalization
- Task type restrictions
- Path traversal prevention (../ escape)
- Integration with existing safe_tasks.py

Design Principles:
- Defense in depth: Multiple layers of validation
- Fail-safe defaults: Deny by default, allow explicitly
- Path normalization: Prevent directory traversal attacks
- Configurable: All rules configurable via environment variables
"""
import logging
import os
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SemanticRuleViolation:
    """Represents a semantic rule violation"""
    rule_type: str  # "directory", "task_type", "path_traversal", "repo"
    message: str
    severity: str  # "error", "warning"
    details: Optional[str] = None


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
            # New in Phase 4 PR-1
            self.allowed_task_types = self._parse_list(
                getattr(settings, 'project_engineer_allowed_task_types', '')
            )
            logger.info(
                "[SemanticRules] Loaded settings: "
                f"allowed_directories={self.allowed_directories}, "
                f"allowed_repos={self.allowed_repos}, "
                f"allowed_task_types={self.allowed_task_types}"
            )
        except (ImportError, AttributeError) as e:
            logger.warning(f"[SemanticRules] Failed to load settings: {e}, using defaults")
            self.allowed_directories = ["docs/", "tests/", "handoff/"]
            self.allowed_repos = ["RC918/morningai"]
            self.allowed_task_types = []  # Empty means all safe task types allowed
    
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
            r'\./',            # ./ at start or after /
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
            # Normalize the allowed directory too
            allowed_normalized = allowed_dir.strip('/')
            if not allowed_normalized:
                continue
            
            # Check if the file path starts with the allowed directory
            if normalized_path.startswith(allowed_normalized + '/') or normalized_path == allowed_normalized:
                logger.debug(f"[SemanticRules] Path '{file_path}' allowed (matches '{allowed_dir}')")
                return True, None
            
            # Also check if the file is directly in the allowed directory
            if '/' not in normalized_path and allowed_normalized == '':
                # Root-level file, check if root is allowed
                continue
        
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
        """
        try:
            from .safe_tasks import is_safe_task
            return is_safe_task(task_type)
        except ImportError:
            try:
                from safe_tasks import is_safe_task
                return is_safe_task(task_type)
            except ImportError:
                try:
                    from project_engineer.safe_tasks import is_safe_task
                    return is_safe_task(task_type)
                except ImportError:
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
        file_paths: Optional[List[str]] = None
    ) -> Tuple[bool, List[SemanticRuleViolation]]:
        """
        Validate all semantic rules for a task.
        
        Args:
            repo: Repository name
            task_type: Task type
            file_paths: Optional list of file paths
            
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
    file_paths: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate all semantic rules for a task.
    
    Args:
        repo: Repository name
        task_type: Task type
        file_paths: Optional list of file paths
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = get_validator()
    is_valid, violations = validator.validate_task(repo, task_type, file_paths)
    error_messages = [v.message for v in violations]
    return is_valid, error_messages


# Logging on module import
logger.info("[SemanticRules] Module loaded - Phase 4 PR-1 Semantic Rules v2")
