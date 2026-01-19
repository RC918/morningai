#!/usr/bin/env python3
"""
Deprecation Deadline Enforcement Script

Issue #4223: Implement deprecation milestone tracking system

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
from datetime import datetime
from pathlib import Path

# Add the repo root to the path so we can import from common.config
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

try:
    from common.config.settings import DEPRECATION_REGISTRY
except ImportError as e:
    print(f"ERROR: Failed to import DEPRECATION_REGISTRY: {e}")
    print("Make sure you're running this script from the repository root.")
    sys.exit(2)


# Configuration
WARNING_DAYS = 30  # Warn if deadline is within this many days


def parse_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def check_deprecations() -> tuple[list, list]:
    """
    Check all deprecations in the registry.

    Returns:
        tuple: (expired_list, warning_list)
            - expired_list: List of deprecations that have passed their deadline
            - warning_list: List of deprecations within WARNING_DAYS of deadline
    """
    today = datetime.now()

    expired = []
    warnings = []

    for entry in DEPRECATION_REGISTRY:
        old_env = entry["old_env"]
        new_env = entry["new_env"]
        removal_date_str = entry["removal_date"]
        issue_ref = entry.get("issue_ref", "N/A")

        try:
            removal_date = parse_date(removal_date_str)
        except ValueError as e:
            print(f"ERROR: Invalid date format for {old_env}: {removal_date_str}")
            print("  Expected format: YYYY-MM-DD")
            expired.append({
                "old_env": old_env,
                "new_env": new_env,
                "removal_date": removal_date_str,
                "issue_ref": issue_ref,
                "error": str(e),
            })
            continue

        days_until = (removal_date - today).days

        if days_until < 0:
            # Deadline has passed
            expired.append({
                "old_env": old_env,
                "new_env": new_env,
                "removal_date": removal_date_str,
                "issue_ref": issue_ref,
                "days_overdue": abs(days_until),
            })
        elif days_until <= WARNING_DAYS:
            # Deadline is approaching
            warnings.append({
                "old_env": old_env,
                "new_env": new_env,
                "removal_date": removal_date_str,
                "issue_ref": issue_ref,
                "days_remaining": days_until,
            })

    return expired, warnings


def print_report(expired: list, warnings: list) -> None:
    """Print a formatted report of deprecation status."""
    print("=" * 60)
    print("DEPRECATION DEADLINE CHECK")
    print("=" * 60)
    print()

    if expired:
        print("EXPIRED DEPRECATIONS (ACTION REQUIRED):")
        print("-" * 40)
        for item in expired:
            print(f"  {item['old_env']} -> {item['new_env']}")
            print(f"    Deadline: {item['removal_date']}")
            if "days_overdue" in item:
                print(f"    Status: {item['days_overdue']} days OVERDUE")
            if "error" in item:
                print(f"    Error: {item['error']}")
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
    print(f"  Expired (FAIL): {len(expired)}")
    print(f"  Upcoming warnings: {len(warnings)}")
    print()


def main() -> int:
    """
    Main entry point.

    Returns:
        int: Exit code (0 = success, 1 = expired deprecations found)
    """
    expired, warnings = check_deprecations()
    print_report(expired, warnings)

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
