"""
Deprecation Utilities - Shared logic for deprecation handling.

Issue #4238: DRY refactoring for deprecation warning logic.

This module provides shared utilities for working with DEPRECATION_REGISTRY,
reducing code duplication between:
- settings.py: Runtime warnings for deprecated usage
- scripts/check_deprecations.py: CI enforcement and pre-deadline alerts

Blueprint Alignment:
- Section 4.3: Model Governance Framework v2 - Clean tech debt management
- Section 4.3: Single Source of Truth - Centralized deprecation utilities
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Iterator, Literal

from common.config.settings import DEPRECATION_REGISTRY


# Configuration constants
WARNING_DAYS = 30  # Warn if deadline is within this many days


@dataclass
class DeprecationInfo:
    """Parsed deprecation entry with computed fields.

    This dataclass provides a convenient interface for working with
    deprecation entries, including parsed dates and computed status.

    Attributes:
        old_env: The deprecated environment variable name
        new_env: The replacement environment variable name
        old_field: The deprecated field name in Settings (None for env-only checks)
        new_field: The replacement field name in Settings (None for env-only checks)
        removal_date: Parsed date object for the removal deadline
        removal_date_str: Original date string (YYYY-MM-DD format)
        issue_ref: Reference to the GitHub issue tracking this deprecation
        check_type: "field" for field-based checks, "env" for env-var-only checks
    """
    old_env: str
    new_env: str
    old_field: Optional[str]
    new_field: Optional[str]
    removal_date: date
    removal_date_str: str
    issue_ref: Optional[str]
    check_type: Literal["field", "env"]

    @property
    def days_until_removal(self) -> int:
        """Calculate days until removal deadline (negative if overdue)."""
        return (self.removal_date - date.today()).days

    @property
    def is_expired(self) -> bool:
        """Check if the deprecation deadline has passed."""
        return self.days_until_removal < 0

    @property
    def is_warning(self) -> bool:
        """Check if the deprecation is within the warning period."""
        days = self.days_until_removal
        return 0 <= days <= WARNING_DAYS

    def format_warning_message(self) -> str:
        """Format a deprecation warning message.

        Returns:
            Formatted warning message string with optional issue reference.
        """
        msg = (
            f"{self.old_env} is deprecated. Please use {self.new_env} instead. "
            f"Support for {self.old_env} will be removed after {self.removal_date_str}."
        )
        if self.issue_ref:
            msg += f" See {self.issue_ref} for details."
        return msg


def parse_removal_date(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format.

    Args:
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        Parsed date object.

    Raises:
        ValueError: If the date string is not in the expected format.
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def iter_deprecations() -> Iterator[DeprecationInfo]:
    """Iterate over deprecation entries with parsed dates.

    This generator yields DeprecationInfo objects for each entry in
    DEPRECATION_REGISTRY, with dates parsed and ready for use.

    Yields:
        DeprecationInfo objects for each valid registry entry.

    Raises:
        ValueError: If a date string cannot be parsed (propagated from parse_removal_date).

    Example:
        for dep in iter_deprecations():
            if dep.is_expired:
                print(f"{dep.old_env} is overdue by {abs(dep.days_until_removal)} days")
    """
    for entry in DEPRECATION_REGISTRY:
        removal_date = parse_removal_date(entry["removal_date"])
        yield DeprecationInfo(
            old_env=entry["old_env"],
            new_env=entry["new_env"],
            old_field=entry["old_field"],
            new_field=entry["new_field"],
            removal_date=removal_date,
            removal_date_str=entry["removal_date"],
            issue_ref=entry["issue_ref"],
            check_type=entry["check_type"],
        )


def iter_deprecations_safe() -> Iterator[tuple[Optional[DeprecationInfo], Optional[str]]]:
    """Iterate over deprecation entries, catching parse errors.

    This generator yields tuples of (DeprecationInfo, error_message) for each
    entry in DEPRECATION_REGISTRY. If parsing succeeds, error_message is None.
    If parsing fails, DeprecationInfo is None and error_message contains the error.

    Yields:
        Tuples of (DeprecationInfo or None, error_message or None).

    Example:
        for dep, error in iter_deprecations_safe():
            if error:
                print(f"Config error: {error}")
            elif dep.is_expired:
                print(f"{dep.old_env} is overdue")
    """
    for entry in DEPRECATION_REGISTRY:
        try:
            removal_date = parse_removal_date(entry["removal_date"])
            yield DeprecationInfo(
                old_env=entry["old_env"],
                new_env=entry["new_env"],
                old_field=entry["old_field"],
                new_field=entry["new_field"],
                removal_date=removal_date,
                removal_date_str=entry["removal_date"],
                issue_ref=entry["issue_ref"],
                check_type=entry["check_type"],
            ), None
        except ValueError as e:
            yield None, f"Invalid date for {entry['old_env']}: {e}"
