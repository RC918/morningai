"""
Memory v2 Sanitizer - PII Sanitization and Input Validation

EPIC G: Memory v2 (Blueprint Section 5.1)
Issue: #3968 (PII sanitization), #3966 (Input validation)

This module provides sanitization and validation for Memory v2 entries:
1. PII detection and redaction using PIIScanner (EPIC E Phase E-4)
2. Input validation for MemoryEntry fields
3. Content sanitization before storage

Blueprint Alignment:
- Section 4.2: Compliance Radar v2 - PII protection
- Section 4.7: Capability-Based Security - input validation
- Section 5.1: Memory v2 - safe storage
- Section 9.2: Safe by Design - redaction protects PII/secrets
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SanitizationAction(str, Enum):
    """Actions for sanitization results"""
    ALLOW = "allow"           # Content is clean, allow storage
    REDACT = "redact"         # PII found and redacted
    BLOCK = "block"           # Critical PII found, block storage
    INVALID = "invalid"       # Input validation failed


class ValidationErrorType(str, Enum):
    """Types of validation errors"""
    EMPTY_KEY = "empty_key"
    EMPTY_CONTENT = "empty_content"
    KEY_TOO_LONG = "key_too_long"
    CONTENT_TOO_LONG = "content_too_long"
    INVALID_CHARACTERS = "invalid_characters"
    INVALID_METADATA = "invalid_metadata"
    INVALID_LAYER = "invalid_layer"
    INVALID_SCOPE = "invalid_scope"


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    errors: List[Tuple[ValidationErrorType, str]]
    sanitized_key: Optional[str] = None
    sanitized_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "is_valid": self.is_valid,
            "errors": [(e[0].value, e[1]) for e in self.errors],
            "has_sanitized_key": self.sanitized_key is not None,
            "has_sanitized_content": self.sanitized_content is not None,
        }


@dataclass
class SanitizationResult:
    """Result of sanitization operation"""
    action: SanitizationAction
    original_content: str
    sanitized_content: str
    pii_found: bool
    pii_categories: List[str]
    validation_result: Optional[ValidationResult] = None
    blocked_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "action": self.action.value,
            "pii_found": self.pii_found,
            "pii_categories": self.pii_categories,
            "content_modified": self.original_content != self.sanitized_content,
            "blocked_reason": self.blocked_reason,
        }


class MemorySanitizer:
    """
    Memory v2 Sanitizer for PII protection and input validation.

    EPIC G: Memory v2 (Blueprint Section 5.1)
    Issues: #3968 (PII sanitization), #3966 (Input validation)

    Integrates with PIIScanner (EPIC E Phase E-4) to detect and redact
    PII before storing in Memory v2 layers.

    Usage:
        sanitizer = get_memory_sanitizer()

        # Validate and sanitize entry
        result = sanitizer.sanitize_entry(entry)
        if result.action == SanitizationAction.ALLOW:
            memory.save(entry)
        elif result.action == SanitizationAction.REDACT:
            entry.content = result.sanitized_content
            memory.save(entry)
        elif result.action == SanitizationAction.BLOCK:
            logger.warning("Blocked due to critical PII")
    """

    # Validation limits
    MAX_KEY_LENGTH = 512
    MAX_CONTENT_LENGTH = 1_000_000  # 1MB
    MAX_METADATA_SIZE = 65536  # 64KB

    # Characters allowed in keys (alphanumeric, dash, underscore, colon, dot)
    KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_\-:.]+$')

    # PII categories that should block storage (critical PII)
    BLOCKING_PII_CATEGORIES = frozenset([
        "ssn",
        "credit_card",
        "passport",
        "driver_license",
    ])

    def __init__(
        self,
        enabled: bool = True,
        block_on_critical_pii: bool = True,
        redact_pii: bool = True,
        validate_input: bool = True,
    ):
        """
        Initialize MemorySanitizer.

        Args:
            enabled: Whether sanitization is enabled
            block_on_critical_pii: Block storage if critical PII found
            redact_pii: Redact non-critical PII before storage
            validate_input: Validate input fields
        """
        self.enabled = enabled
        self.block_on_critical_pii = block_on_critical_pii
        self.redact_pii = redact_pii
        self.validate_input = validate_input
        self._pii_scanner = None
        self._load_settings()

        logger.info(
            "[MemorySanitizer] Initialized - EPIC G #3968/#3966: "
            "enabled=%s, block_critical=%s, redact=%s, validate=%s",
            self.enabled,
            self.block_on_critical_pii,
            self.redact_pii,
            self.validate_input,
        )

    def _load_settings(self) -> None:
        """Load settings from configuration if available."""
        try:
            import os
            self.enabled = os.getenv(
                "MEMORY_V2_SANITIZATION_ENABLED", "true"
            ).lower() == "true"
            self.block_on_critical_pii = os.getenv(
                "MEMORY_V2_BLOCK_CRITICAL_PII", "true"
            ).lower() == "true"
            self.redact_pii = os.getenv(
                "MEMORY_V2_REDACT_PII", "true"
            ).lower() == "true"
            self.validate_input = os.getenv(
                "MEMORY_V2_VALIDATE_INPUT", "true"
            ).lower() == "true"
        except Exception as e:
            logger.debug("[MemorySanitizer] Using default settings: %s", e)

    def _get_pii_scanner(self):
        """Get PIIScanner instance lazily."""
        if self._pii_scanner is not None:
            return self._pii_scanner

        try:
            from governance.pii_scanner import get_pii_scanner
            self._pii_scanner = get_pii_scanner()
            return self._pii_scanner
        except ImportError:
            logger.debug("[MemorySanitizer] PIIScanner not available")
            return None

    def validate_key(self, key: str) -> ValidationResult:
        """
        Validate memory entry key.

        Args:
            key: The key to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors: List[Tuple[ValidationErrorType, str]] = []

        if not key:
            errors.append((
                ValidationErrorType.EMPTY_KEY,
                "Key cannot be empty"
            ))
            return ValidationResult(is_valid=False, errors=errors)

        if len(key) > self.MAX_KEY_LENGTH:
            errors.append((
                ValidationErrorType.KEY_TOO_LONG,
                f"Key exceeds maximum length of {self.MAX_KEY_LENGTH}"
            ))

        if not self.KEY_PATTERN.match(key):
            errors.append((
                ValidationErrorType.INVALID_CHARACTERS,
                "Key contains invalid characters. "
                "Only alphanumeric, dash, underscore, colon, and dot allowed."
            ))

        # Sanitize key by removing invalid characters
        sanitized_key = re.sub(r'[^a-zA-Z0-9_\-:.]', '_', key)
        if len(sanitized_key) > self.MAX_KEY_LENGTH:
            sanitized_key = sanitized_key[:self.MAX_KEY_LENGTH]

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_key=sanitized_key if sanitized_key != key else None,
        )

    def validate_content(self, content: str) -> ValidationResult:
        """
        Validate memory entry content.

        Args:
            content: The content to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors: List[Tuple[ValidationErrorType, str]] = []

        if not content:
            errors.append((
                ValidationErrorType.EMPTY_CONTENT,
                "Content cannot be empty"
            ))
            return ValidationResult(is_valid=False, errors=errors)

        if len(content) > self.MAX_CONTENT_LENGTH:
            errors.append((
                ValidationErrorType.CONTENT_TOO_LONG,
                f"Content exceeds maximum length of {self.MAX_CONTENT_LENGTH}"
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )

    def validate_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Validate memory entry metadata.

        Args:
            metadata: The metadata dictionary to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors: List[Tuple[ValidationErrorType, str]] = []

        if metadata is None:
            return ValidationResult(is_valid=True, errors=[])

        try:
            import json
            serialized = json.dumps(metadata)
            if len(serialized) > self.MAX_METADATA_SIZE:
                errors.append((
                    ValidationErrorType.INVALID_METADATA,
                    f"Metadata exceeds maximum size of {self.MAX_METADATA_SIZE}"
                ))
        except (TypeError, ValueError) as e:
            errors.append((
                ValidationErrorType.INVALID_METADATA,
                f"Metadata is not JSON serializable: {e}"
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )

    def scan_for_pii(self, content: str) -> Tuple[bool, List[str], str]:
        """
        Scan content for PII and optionally redact.

        Args:
            content: Content to scan

        Returns:
            Tuple of (has_critical_pii, pii_categories, redacted_content)
        """
        scanner = self._get_pii_scanner()
        if scanner is None:
            return False, [], content

        try:
            result = scanner.scan(content)

            if not result.has_pii:
                return False, [], content

            # Extract categories found
            categories = list(set(
                f.category.value for f in result.findings
            ))

            # Check for critical PII
            has_critical = any(
                cat in self.BLOCKING_PII_CATEGORIES
                for cat in categories
            )

            # Redact PII if enabled
            redacted_content = content
            if self.redact_pii and result.findings:
                redacted_content = self._redact_content(content, result.findings)

            return has_critical, categories, redacted_content

        except Exception as e:
            logger.warning("[MemorySanitizer] PII scan failed: %s", e)
            return False, [], content

    def _redact_content(self, content: str, findings) -> str:
        """
        Redact PII from content based on findings.

        Args:
            content: Original content
            findings: List of PIIFinding objects

        Returns:
            Content with PII redacted
        """
        if not findings:
            return content

        # Sort findings by position (descending) to redact from end to start
        # This preserves positions during replacement
        sorted_findings = sorted(
            findings,
            key=lambda f: f.position,
            reverse=True,
        )

        redacted = content
        for finding in sorted_findings:
            if finding.redacted_text:
                # Use the pre-computed redacted text from PIIScanner
                # Find the original text at the position and replace
                start = finding.position
                # Estimate end position based on matched text length
                # (matched_text is sanitized, so we need to search)
                original_text = self._find_original_text(
                    redacted, start, finding.category.value
                )
                if original_text:
                    redacted = (
                        redacted[:start] +
                        finding.redacted_text +
                        redacted[start + len(original_text):]
                    )

        return redacted

    def _find_original_text(
        self,
        content: str,
        start: int,
        category: str,
    ) -> Optional[str]:
        """Find original PII text at position for redaction."""
        # Use category-specific patterns to find the text
        patterns = {
            "email": r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
            "phone": r'(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            "ssn": r'(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}',
            "credit_card": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}',
            "ip_address": r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)',
        }

        pattern = patterns.get(category)
        if not pattern:
            return None

        # Search from the start position
        match = re.search(pattern, content[start:], re.IGNORECASE)
        if match and match.start() == 0:
            return match.group(0)

        return None

    def sanitize_content(self, content: str) -> SanitizationResult:
        """
        Sanitize content for storage.

        Args:
            content: Content to sanitize

        Returns:
            SanitizationResult with action and sanitized content
        """
        if not self.enabled:
            return SanitizationResult(
                action=SanitizationAction.ALLOW,
                original_content=content,
                sanitized_content=content,
                pii_found=False,
                pii_categories=[],
            )

        # Validate content
        if self.validate_input:
            validation = self.validate_content(content)
            if not validation.is_valid:
                return SanitizationResult(
                    action=SanitizationAction.INVALID,
                    original_content=content,
                    sanitized_content=content,
                    pii_found=False,
                    pii_categories=[],
                    validation_result=validation,
                    blocked_reason="Content validation failed",
                )

        # Scan for PII
        has_critical, categories, redacted = self.scan_for_pii(content)

        if has_critical and self.block_on_critical_pii:
            return SanitizationResult(
                action=SanitizationAction.BLOCK,
                original_content=content,
                sanitized_content=redacted,
                pii_found=True,
                pii_categories=categories,
                blocked_reason=f"Critical PII detected: {', '.join(categories)}",
            )

        if categories and self.redact_pii:
            return SanitizationResult(
                action=SanitizationAction.REDACT,
                original_content=content,
                sanitized_content=redacted,
                pii_found=True,
                pii_categories=categories,
            )

        return SanitizationResult(
            action=SanitizationAction.ALLOW,
            original_content=content,
            sanitized_content=content,
            pii_found=len(categories) > 0,
            pii_categories=categories,
        )

    def sanitize_entry(self, entry) -> SanitizationResult:
        """
        Sanitize a MemoryEntry for storage.

        Args:
            entry: MemoryEntry to sanitize

        Returns:
            SanitizationResult with action and sanitized content
        """
        if not self.enabled:
            return SanitizationResult(
                action=SanitizationAction.ALLOW,
                original_content=entry.content,
                sanitized_content=entry.content,
                pii_found=False,
                pii_categories=[],
            )

        errors: List[Tuple[ValidationErrorType, str]] = []

        # Validate key
        if self.validate_input:
            key_result = self.validate_key(entry.key)
            if not key_result.is_valid:
                errors.extend(key_result.errors)

            # Validate metadata
            metadata_result = self.validate_metadata(entry.metadata)
            if not metadata_result.is_valid:
                errors.extend(metadata_result.errors)

        if errors:
            return SanitizationResult(
                action=SanitizationAction.INVALID,
                original_content=entry.content,
                sanitized_content=entry.content,
                pii_found=False,
                pii_categories=[],
                validation_result=ValidationResult(
                    is_valid=False,
                    errors=errors,
                ),
                blocked_reason="Entry validation failed",
            )

        # Sanitize content
        return self.sanitize_content(entry.content)


# Global singleton instance
_memory_sanitizer: Optional[MemorySanitizer] = None


def get_memory_sanitizer() -> MemorySanitizer:
    """
    Get or create global MemorySanitizer instance.

    EPIC G: Memory v2 (Blueprint Section 5.1)
    Issues: #3968 (PII sanitization), #3966 (Input validation)

    Returns:
        MemorySanitizer instance
    """
    global _memory_sanitizer
    if _memory_sanitizer is None:
        _memory_sanitizer = MemorySanitizer()
    return _memory_sanitizer


def reset_memory_sanitizer() -> None:
    """Reset global MemorySanitizer instance (for testing)."""
    global _memory_sanitizer
    _memory_sanitizer = None


def sanitize_for_memory(content: str) -> SanitizationResult:
    """
    Convenience function to sanitize content for memory storage.

    Args:
        content: Content to sanitize

    Returns:
        SanitizationResult with action and sanitized content
    """
    return get_memory_sanitizer().sanitize_content(content)
