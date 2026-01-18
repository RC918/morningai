#!/usr/bin/env python3
"""
H-4 CI Enforcement: Check Protected Test Modifications

Blueprint Section 5.4: Regression Pipeline CI Enforcement
- Detects modifications to protected regression tests
- Blocks deletion of protected tests (Safety Governor)
- Requires reviewer approval for modifications

Usage:
    python check_protected_tests.py --base <base_sha> --head <head_sha>
"""

import argparse
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

# Protection marker that identifies protected regression tests
PROTECTION_MARKER = "REGRESSION_METADATA"

# Default regression test directory
REGRESSION_TEST_DIR = "tests/regression"


def get_changed_files(base_sha: str, head_sha: str) -> List[Tuple[str, str]]:
    """
    Get list of changed files between two commits.

    Returns:
        List of (status, file_path) tuples where status is:
        - 'A' for added
        - 'M' for modified
        - 'D' for deleted
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", f"{base_sha}...{head_sha}"],
            capture_output=True,
            text=True,
            check=True,
        )
        changes = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                status, file_path = parts
                changes.append((status[0], file_path))
        return changes
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        return []


def get_file_content_at_commit(file_path: str, commit_sha: str) -> Optional[str]:
    """Get file content at a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit_sha}:{file_path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def is_regression_test_file(file_path: str, regression_dir: str = REGRESSION_TEST_DIR) -> bool:
    """Check if a file is in the regression test directory."""
    normalized_path = os.path.normpath(file_path).replace("\\", "/")
    normalized_dir = os.path.normpath(regression_dir).replace("\\", "/")
    return normalized_path == normalized_dir or normalized_path.startswith(normalized_dir + "/")


def is_protected_test(file_content: str) -> bool:
    """Check if file content contains protection marker.
    
    Uses word boundary matching to avoid false positives with similar markers
    like REGRESSION_METADATA_EXTRA.
    """
    # Use word boundary regex to match exact marker name
    pattern = r'\b' + re.escape(PROTECTION_MARKER) + r'\b'
    return bool(re.search(pattern, file_content))


def check_protected_test_modifications(
    base_sha: str,
    head_sha: str,
    regression_dir: str = REGRESSION_TEST_DIR,
) -> Dict[str, List[str]]:
    """
    Check for modifications to protected regression tests.

    Returns:
        Dict with:
        - 'deleted': List of deleted protected test files
        - 'modified': List of modified protected test files
        - 'errors': List of error messages
    """
    result = {
        "deleted": [],
        "modified": [],
        "errors": [],
    }

    changes = get_changed_files(base_sha, head_sha)

    for status, file_path in changes:
        # Only check files in regression test directory
        if not is_regression_test_file(file_path, regression_dir):
            continue

        # Only check Python test files
        if not file_path.endswith(".py"):
            continue

        # Get old content to check if it was protected
        old_content = get_file_content_at_commit(file_path, base_sha)

        if old_content is None:
            # New file - always allowed
            continue

        if not is_protected_test(old_content):
            # Not a protected test - allowed
            continue

        # Protected test was modified or deleted
        if status == "D":
            result["deleted"].append(file_path)
            print(f"::error::Protected regression test DELETED: {file_path}")
            print(
                "::error::Deletion of protected tests is blocked by Safety Governor "
                "(Blueprint Section 5.4)"
            )
        elif status == "M":
            result["modified"].append(file_path)
            print(f"::warning::Protected regression test MODIFIED: {file_path}")
            print(
                "::warning::Modification requires explicit reviewer approval "
                "(Blueprint Section 5.4)"
            )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Check for protected regression test modifications"
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base commit SHA (PR base)",
    )
    parser.add_argument(
        "--head",
        required=True,
        help="Head commit SHA (PR head)",
    )
    parser.add_argument(
        "--regression-dir",
        default=REGRESSION_TEST_DIR,
        help=f"Regression test directory (default: {REGRESSION_TEST_DIR})",
    )
    parser.add_argument(
        "--allow-modifications",
        action="store_true",
        help="Allow modifications (only warn, don't fail)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("H-4 CI Enforcement: Checking Protected Test Modifications")
    print("Blueprint Section 5.4: Regression Pipeline")
    print("=" * 60)
    print()
    print(f"Base SHA: {args.base}")
    print(f"Head SHA: {args.head}")
    print(f"Regression dir: {args.regression_dir}")
    print()

    result = check_protected_test_modifications(
        args.base,
        args.head,
        args.regression_dir,
    )

    # Report results
    if result["deleted"]:
        print()
        print("=" * 60)
        print("BLOCKED: Protected tests cannot be deleted")
        print("=" * 60)
        for file_path in result["deleted"]:
            print(f"  - {file_path}")
        print()
        print("To proceed:")
        print("  1. Restore the deleted test file")
        print("  2. If the test is no longer needed, request Safety Governor override")
        print("  3. Document the reason in the PR description")
        sys.exit(1)

    if result["modified"] and not args.allow_modifications:
        print()
        print("=" * 60)
        print("REQUIRES APPROVAL: Protected tests were modified")
        print("=" * 60)
        for file_path in result["modified"]:
            print(f"  - {file_path}")
        print()
        print("To proceed:")
        print("  1. Ensure a reviewer explicitly approves the modification")
        print("  2. Document why the change is necessary")
        print("  3. Reference the original issue that created the test")
        # Don't fail for modifications - just warn and require approval
        # The PR review process will handle approval
        print()
        print("This PR requires explicit reviewer approval for test modifications.")

    if not result["deleted"] and not result["modified"]:
        print("No protected regression tests were modified or deleted.")
        print("Check passed!")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
