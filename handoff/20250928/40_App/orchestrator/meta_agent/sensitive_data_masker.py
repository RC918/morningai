"""
Sensitive Data Masker - Utility for masking sensitive information

This module provides utilities for masking sensitive data such as tokens,
passwords, API keys, and other secrets in logs, state files, and audit events.

Issue: #1960 - 狀態目錄權限與敏感資料遮罩
Milestone: M5 - Meta Agent 優化
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set, Union


class SensitiveDataMasker:
    """
    Utility class for masking sensitive data in strings and dictionaries.

    Supports masking of common sensitive patterns (tokens, passwords, keys)
    and custom regex patterns. Masked values show first 4 and last 4 characters
    with **** in between.

    Example:
        masker = SensitiveDataMasker()
        masked = masker.mask_value("sk-1234567890abcdef")
        # Returns: "sk-1****cdef"
    """

    # Default sensitive key patterns (case-insensitive)
    DEFAULT_SENSITIVE_KEYS: Set[str] = {
        "token",
        "key",
        "password",
        "secret",
        "api_key",
        "apikey",
        "auth",
        "credential",
        "credentials",
        "access_token",
        "refresh_token",
        "bearer",
        "authorization",
        "private_key",
        "private",
        "cert",
        "certificate",
    }

    # Default regex patterns for sensitive values
    DEFAULT_VALUE_PATTERNS: List[str] = [
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI API keys
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub personal access tokens
        r"gho_[a-zA-Z0-9]{36}",  # GitHub OAuth tokens
        r"github_pat_[a-zA-Z0-9_]{22,}",  # GitHub fine-grained PATs
        r"xoxb-[a-zA-Z0-9-]+",  # Slack bot tokens
        r"xoxp-[a-zA-Z0-9-]+",  # Slack user tokens
        r"Bearer\s+[a-zA-Z0-9._-]+",  # Bearer tokens
        r"Basic\s+[a-zA-Z0-9+/=]+",  # Basic auth
        # PostgreSQL DSN patterns (Issue #3107)
        # Format: postgres://user:password@host:port/database
        # Format: postgresql://user:password@host:port/database
        r"postgres(?:ql)?://[^:]+:[^@]+@[^\s]+",
        # Password in query params or config: password=secret, pwd=secret
        r"(?:password|passwd|pwd)\s*[=:]\s*[^\s,;\"']+",
        # DSN-style connection strings with password
        r"host=[^\s]+\s+.*password=[^\s]+",
    ]

    # Minimum length for masking (shorter values are fully masked)
    MIN_MASK_LENGTH = 8

    def __init__(
        self,
        sensitive_keys: Optional[Set[str]] = None,
        value_patterns: Optional[List[str]] = None,
        mask_char: str = "*",
        mask_length: int = 4,
    ):
        """
        Initialize the SensitiveDataMasker.

        Args:
            sensitive_keys: Set of key names to treat as sensitive.
                           Merged with defaults if provided.
            value_patterns: List of regex patterns for sensitive values.
                           Merged with defaults if provided.
            mask_char: Character to use for masking (default: *)
            mask_length: Number of mask characters (default: 4)
        """
        self.sensitive_keys = self.DEFAULT_SENSITIVE_KEYS.copy()
        if sensitive_keys:
            self.sensitive_keys.update(sensitive_keys)

        patterns = self.DEFAULT_VALUE_PATTERNS.copy()
        if value_patterns:
            patterns.extend(value_patterns)

        self.value_patterns: List[Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in patterns
        ]

        self.mask_char = mask_char
        self.mask_length = mask_length

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data."""
        key_lower = key.lower()
        for sensitive in self.sensitive_keys:
            if sensitive in key_lower:
                return True
        return False

    def mask_value(self, value: str) -> str:
        """
        Mask a sensitive value.

        Format: first 4 chars + "****" + last 4 chars
        For short values (< 8 chars): fully masked

        Args:
            value: The value to mask

        Returns:
            Masked value string
        """
        if not value or not isinstance(value, str):
            return value

        value_len = len(value)

        if value_len < self.MIN_MASK_LENGTH:
            return self.mask_char * value_len

        # Show first 4 and last 4 characters
        prefix = value[:4]
        suffix = value[-4:]
        mask = self.mask_char * self.mask_length

        return f"{prefix}{mask}{suffix}"

    def mask_string(self, text: str) -> str:
        """
        Mask sensitive patterns within a string.

        Scans the text for known sensitive patterns and masks them.

        Args:
            text: The text to scan and mask

        Returns:
            Text with sensitive patterns masked
        """
        if not text or not isinstance(text, str):
            return text

        result = text
        for pattern in self.value_patterns:
            result = pattern.sub(
                lambda m: self.mask_value(m.group(0)),
                result
            )

        return result

    def mask_dict(
        self,
        data: Dict[str, Any],
        deep: bool = True,
    ) -> Dict[str, Any]:
        """
        Recursively mask sensitive values in a dictionary.

        Args:
            data: Dictionary to mask
            deep: Whether to recursively mask nested dicts/lists

        Returns:
            New dictionary with sensitive values masked
        """
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            result[key] = self._mask_value_by_key(key, value, deep)

        return result

    def _mask_value_by_key(
        self,
        key: str,
        value: Any,
        deep: bool = True,
    ) -> Any:
        """Mask a value based on its key and type."""
        if value is None:
            return None

        # Check if key indicates sensitive data
        is_sensitive = self._is_sensitive_key(key)

        if isinstance(value, str):
            if is_sensitive:
                return self.mask_value(value)
            return self.mask_string(value)

        if isinstance(value, dict) and deep:
            return self.mask_dict(value, deep)

        if isinstance(value, list) and deep:
            return [
                self._mask_list_item(item, deep)
                for item in value
            ]

        return value

    def _mask_list_item(self, item: Any, deep: bool = True) -> Any:
        """Mask an item in a list."""
        if isinstance(item, dict):
            return self.mask_dict(item, deep)
        if isinstance(item, str):
            return self.mask_string(item)
        if isinstance(item, list) and deep:
            return [self._mask_list_item(i, deep) for i in item]
        return item

    def mask_any(self, data: Union[str, Dict, List, Any]) -> Any:
        """
        Mask sensitive data in any supported type.

        Args:
            data: Data to mask (string, dict, list, or other)

        Returns:
            Masked data
        """
        if isinstance(data, str):
            return self.mask_string(data)
        if isinstance(data, dict):
            return self.mask_dict(data)
        if isinstance(data, list):
            return [self._mask_list_item(item) for item in data]
        return data


# Global instance for convenience
_default_masker: Optional[SensitiveDataMasker] = None


def get_masker() -> SensitiveDataMasker:
    """Get the default SensitiveDataMasker instance."""
    global _default_masker
    if _default_masker is None:
        _default_masker = SensitiveDataMasker()
    return _default_masker


def mask_sensitive_data(data: Union[str, Dict, List, Any]) -> Any:
    """
    Convenience function to mask sensitive data using the default masker.

    Args:
        data: Data to mask

    Returns:
        Masked data
    """
    return get_masker().mask_any(data)
