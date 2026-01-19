#!/usr/bin/env python3
"""
Deprecation Deadline Enforcement Script

Issue #4223: Implement deprecation milestone tracking system
Issue #4238: DRY refactoring using shared deprecation_utils

This script checks the DEPRECATION_REGISTRY in settings.py and:
1. FAILS if any deprecation deadline has passed (enforcement)
2. WARNS if any deprecation deadline is within 30 days (pre-deadline alert)

Blueprint Alignment:
- Section 4.3: Model Governance Framework v2 - Clean tech debt management
- Section 4.6: Evidence Ledger - Track deprecation decisions and enforcement

Usage:
    python scripts/check_deprecations.py

Exit codes:
    0 - All deprecations are within their deadlines
    1 - One or more deprecation deadlines have passed (FAIL)
    2 - Script error (e.g., import failure)

CI Integration:
    Add to GitHub Actions workflow:
    ```yaml
    - name: Check Deprecation Deadlines
      run: python scripts/check_deprecations.py
    ```
"""

import sys
from pathlib import Path

# Add the repo root to the path so we can import from common.config
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

try:
    from common.config.settings import DEPRECATION_REGISTRY
    from common.config.deprecation_utils import iter_deprecations_safe
except ImportError as e:
    print(f"ERROR: Failed to import deprecation utilities: {e}")
    print("Make sure you're running this script from the repository root.")
    sys.exit(2)


def check_deprecations() -> tuple[list, list, list]:
    """
    Check all deprecations in the registry.

    Uses shared iter_deprecations_safe() for DRY code.

    Returns:
        tuple: (expired_list, warning_list, errors_list)
            - expired_list: List of deprecations that have passed their deadline
            - warning_list: List of deprecations within WARNING_DAYS of deadline
            - errors_list: List of deprecations with configuration errors
    """
    expired = []
    warnings = []
    errors = []

    for dep, error in iter_deprecations_safe():
        if error:
            # Extract old_env from error message for reporting
            # Error format: "Invalid date for {old_env}: {error}"
            errors.append({
                "error": error,
            })
            continue

        if dep.is_expired:
            expired.append({
                "old_env": dep.old_env,
                "new_env": dep.new_env,
                "removal_date": dep.removal_date_str,
                "issue_ref": dep.issue_ref,
                "days_overdue": abs(dep.days_until_removal),
            })
        elif dep.is_warning:
            warnings.append({
                "old_env": dep.old_env,
                "new_env": dep.new_env,
                "removal_date": dep.removal_date_str,
                "issue_ref": dep.issue_ref,
                "days_remaining": dep.days_until_removal,
            })


def print_report(expired: list, warnings: list, errors: list) -> None:
    """Print a formatted report of deprecation status."""
    print("=" * 60)
    print("DEPRECATION DEADLINE CHECK")
    print("=" * 60)
    print()

    if errors:
        print("CONFIGURATION ERRORS:")
        print("-" * 40)
        for item in errors:
            print(f"  {item['error']}")
            print("    Expected format: YYYY-MM-DD")
            print()

    if expired:
        print("EXPIRED DEPRECATIONS (ACTION REQUIRED):")
        print("-" * 40)
        for item in expired:
            print(f"  {item['old_env']} -> {item['new_env']}")
            print(f"    Deadline: {item['removal_date']}")
            print(f"    Status: {item['days_overdue']} days OVERDUE")
            if item["issue_ref"]:
                print(f"    Issue: {item['issue_ref']}")
            print()
    else:
        print("No expired deprecations.")
        print()

    if warnings:
        print("UPCOMING DEPRECATIONS (WARNING):")
        print("-" * 40)
        for item in warnings:
            print(f"  {item['old_env']} -> {item['new_env']}")
            print(f"    Deadline: {item['removal_date']}")
            print(f"    Status: {item['days_remaining']} days remaining")
            if item["issue_ref"]:
                print(f"    Issue: {item['issue_ref']}")
            print()
    else:
        print("No upcoming deprecations within the next 30 days.")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total deprecations tracked: {len(DEPRECATION_REGISTRY)}")
    print(f"  Configuration errors: {len(errors)}")
    print(f"  Expired (FAIL): {len(expired)}")
    print(f"  Upcoming warnings: {len(warnings)}")
    print()


def main() -> int:
    """
    Main entry point.

    Returns:
        int: Exit code (0 = success, 1 = expired deprecations, 2 = config errors)
    """
    expired, warnings, errors = check_deprecations()
    print_report(expired, warnings, errors)

    if errors:
        print("RESULT: FAIL - Configuration errors in DEPRECATION_REGISTRY")
        print()
        print("To fix this:")
        print("  1. Check the date format for each entry (must be YYYY-MM-DD)")
        print("  2. Ensure all required fields are present")
        return 2

    if expired:
        print("RESULT: FAIL - Expired deprecations must be removed from codebase")
        print()
        print("To fix this:")
        print("  1. Remove support for the deprecated environment variable")
        print("  2. Remove the entry from DEPRECATION_REGISTRY in settings.py")
        print("  3. Update any documentation referencing the old variable")
        return 1

    if warnings:
        print("RESULT: PASS (with warnings)")
        print()
        print("Upcoming deprecations should be addressed before their deadlines.")
    else:
        print("RESULT: PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
