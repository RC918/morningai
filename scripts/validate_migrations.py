#!/usr/bin/env python3
"""
Migration Validation Script

Validates migration files to ensure:
1. No duplicate migration numbers
2. Contiguous numbering (no gaps)
3. No rogue migrations outside canonical directories
4. Consistent naming format

Usage:
    python scripts/validate_migrations.py
    python scripts/validate_migrations.py --strict  # Fail on warnings too

Exit codes:
    0 - All validations passed
    1 - Validation errors found
    2 - Validation warnings found (only with --strict)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


MIGRATIONS_DIR = Path("migrations")
CANONICAL_DIRS = [MIGRATIONS_DIR]
MIGRATION_PATTERN = re.compile(r"^(\d{3})_.*\.sql$")
EXCLUDED_DIRS = {"tests", "__pycache__", ".git", "node_modules", ".venv"}
EXCLUDED_FILES = {"backfill_user_profiles.sql"}

ALLOWED_MIGRATION_DIRS = {
    "migrations",
    "agents/dev_agent/migrations",
    "agents/faq_agent/migrations",
    "agents/ops_agent/migrations",
    "docs/database/migrations",
}

# Directories that get full validation (duplicates, gaps, naming)
# vs auxiliary directories that only get duplicates + naming (no gap checks)
MAIN_MIGRATION_DIR = "migrations"
AUXILIARY_MIGRATION_DIRS = {
    "agents/dev_agent/migrations",
    "agents/faq_agent/migrations",
    "agents/ops_agent/migrations",
    "docs/database/migrations",
}


def find_migration_files(base_dir: Path) -> List[Tuple[Path, int, str]]:
    """
    Find all migration files and extract their numbers.

    Returns:
        List of tuples: (file_path, migration_number, filename)
    """
    migrations = []

    if not base_dir.exists():
        return migrations

    for file_path in base_dir.iterdir():
        if file_path.is_file() and file_path.suffix == ".sql":
            if file_path.name in EXCLUDED_FILES:
                continue

            match = MIGRATION_PATTERN.match(file_path.name)
            if match:
                migration_num = int(match.group(1))
                migrations.append((file_path, migration_num, file_path.name))

    return sorted(migrations, key=lambda x: x[1])


def find_rogue_migrations(repo_root: Path) -> List[Path]:
    """
    Find SQL files that look like migrations but are outside allowed directories.

    Allowed directories are defined in ALLOWED_MIGRATION_DIRS.

    Returns:
        List of paths to rogue migration files
    """
    rogue_files = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        root_path = Path(root)

        for file in files:
            if not file.endswith(".sql"):
                continue

            match = MIGRATION_PATTERN.match(file)
            if not match:
                continue

            file_path = root_path / file
            relative_path = file_path.relative_to(repo_root)
            relative_dir = str(relative_path.parent)

            if "tests" in relative_dir:
                continue

            if relative_dir in ALLOWED_MIGRATION_DIRS:
                continue

            rogue_files.append(file_path)

    return rogue_files


def check_duplicate_numbers(migrations: List[Tuple[Path, int, str]]) -> List[str]:
    """
    Check for duplicate migration numbers.

    Returns:
        List of error messages
    """
    errors = []
    seen_numbers: dict = {}

    for file_path, num, filename in migrations:
        if num in seen_numbers:
            errors.append(
                f"Duplicate migration number {num:03d}: "
                f"'{seen_numbers[num]}' and '{filename}'"
            )
        else:
            seen_numbers[num] = filename

    return errors


def check_contiguous_numbering(migrations: List[Tuple[Path, int, str]]) -> List[str]:
    """
    Check for gaps in migration numbering.

    Returns:
        List of warning messages
    """
    warnings = []

    if not migrations:
        return warnings

    numbers = [m[1] for m in migrations]
    expected_start = 1

    if numbers[0] != expected_start:
        warnings.append(
            f"Migration numbering should start at {expected_start:03d}, "
            f"but starts at {numbers[0]:03d}"
        )

    for i in range(1, len(numbers)):
        expected = numbers[i - 1] + 1
        actual = numbers[i]
        if actual != expected:
            warnings.append(
                f"Gap in migration numbering: expected {expected:03d} after "
                f"{numbers[i - 1]:03d}, but found {actual:03d}"
            )

    return warnings


def check_naming_format(migrations: List[Tuple[Path, int, str]]) -> List[str]:
    """
    Check migration file naming format.

    Returns:
        List of warning messages
    """
    warnings = []
    name_pattern = re.compile(r"^\d{3}_[a-z][a-z0-9_]*\.sql$")

    for file_path, num, filename in migrations:
        if not name_pattern.match(filename):
            warnings.append(
                f"Migration '{filename}' does not follow naming convention: "
                "NNN_lowercase_with_underscores.sql"
            )

    return warnings


def validate_directory(
    repo_root: Path,
    dir_path: str,
    check_gaps: bool = True
) -> Tuple[List[str], List[str], int]:
    """
    Validate migrations in a single directory.

    Args:
        repo_root: Path to repository root
        dir_path: Relative path to migration directory
        check_gaps: Whether to check for contiguous numbering

    Returns:
        Tuple of (errors, warnings, migration_count)
    """
    errors: List[str] = []
    warnings: List[str] = []

    migrations_path = repo_root / dir_path
    migrations = find_migration_files(migrations_path)

    if not migrations:
        return errors, warnings, 0

    # Check duplicates (always)
    dup_errors = check_duplicate_numbers(migrations)
    for e in dup_errors:
        errors.append(f"[{dir_path}] {e}")

    # Check gaps (only for main directory)
    if check_gaps:
        gap_warnings = check_contiguous_numbering(migrations)
        for w in gap_warnings:
            warnings.append(f"[{dir_path}] {w}")

    # Check naming format (always)
    name_warnings = check_naming_format(migrations)
    for w in name_warnings:
        warnings.append(f"[{dir_path}] {w}")

    return errors, warnings, len(migrations)


def validate_migrations(repo_root: Path, strict: bool = False) -> int:
    """
    Run all migration validations.

    Args:
        repo_root: Path to repository root
        strict: If True, treat warnings as errors

    Returns:
        Exit code (0 = success, 1 = errors, 2 = warnings with strict mode)
    """
    print("=" * 60)
    print("Migration Validation Report")
    print("=" * 60)
    print()

    all_errors: List[str] = []
    all_warnings: List[str] = []
    total_migrations = 0

    # Validate main migrations directory (full validation with gap checks)
    print(f"Validating main directory: {MAIN_MIGRATION_DIR}/")
    print("-" * 40)
    migrations_path = repo_root / MIGRATIONS_DIR
    migrations = find_migration_files(migrations_path)
    print(f"  Found {len(migrations)} migration files")

    print("  Checking for duplicate migration numbers...")
    errors = check_duplicate_numbers(migrations)
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"    ERROR: {e}")
    else:
        print("    OK: No duplicate migration numbers")

    print("  Checking for contiguous numbering...")
    warnings = check_contiguous_numbering(migrations)
    all_warnings.extend(warnings)
    if warnings:
        for w in warnings:
            print(f"    WARNING: {w}")
    else:
        print("    OK: Migration numbers are contiguous")

    print("  Checking naming format...")
    warnings = check_naming_format(migrations)
    all_warnings.extend(warnings)
    if warnings:
        for w in warnings:
            print(f"    WARNING: {w}")
    else:
        print("    OK: All migrations follow naming convention")
    print()
    total_migrations += len(migrations)

    # Validate auxiliary directories (duplicates + naming only, no gap checks)
    for aux_dir in sorted(AUXILIARY_MIGRATION_DIRS):
        aux_path = repo_root / aux_dir
        if not aux_path.exists():
            continue

        print(f"Validating auxiliary directory: {aux_dir}/")
        print("-" * 40)
        errors, warnings, count = validate_directory(
            repo_root, aux_dir, check_gaps=False
        )
        print(f"  Found {count} migration files")

        if count == 0:
            print("  (no migrations to validate)")
            print()
            continue

        all_errors.extend(errors)
        all_warnings.extend(warnings)
        total_migrations += count

        if errors:
            for e in errors:
                print(f"    ERROR: {e}")
        if warnings:
            for w in warnings:
                print(f"    WARNING: {w}")
        if not errors and not warnings:
            print("    OK: All validations passed")
        print()

    # Check for rogue migrations
    print("Checking for rogue migrations outside allowed directories...")
    print("-" * 40)
    rogue_files = find_rogue_migrations(repo_root)
    if rogue_files:
        for f in rogue_files:
            all_errors.append(f"Rogue migration found: {f}")
            print(f"  ERROR: Rogue migration found: {f}")
    else:
        print("  OK: No rogue migrations found")
    print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total migrations checked: {total_migrations}")
    print(f"  Directories validated: {1 + len(AUXILIARY_MIGRATION_DIRS)}")
    print(f"  Errors: {len(all_errors)}")
    print(f"  Warnings: {len(all_warnings)}")
    print()

    if all_errors:
        print("FAILED: Validation errors found")
        return 1
    elif all_warnings and strict:
        print("FAILED: Validation warnings found (strict mode)")
        return 2
    else:
        print("PASSED: All validations successful")
        return 0


def main():
    strict = "--strict" in sys.argv

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    if not (repo_root / "migrations").exists():
        print(f"ERROR: migrations/ directory not found in {repo_root}")
        sys.exit(1)

    exit_code = validate_migrations(repo_root, strict=strict)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
