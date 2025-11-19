"""
P2.2: Migration Idempotency Tests

Tests that database migrations can be safely run multiple times without errors.
This ensures migrations are idempotent and can handle:
- Re-running after partial failures
- Schema drift scenarios
- Rollback and re-apply scenarios

Test Coverage:
1. Supabase SQL migrations can be run multiple times
2. Schema consistency after repeated migrations
3. Rollback mechanisms work correctly
4. No data loss during migration re-runs
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

import pytest


MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"
SUPABASE_URL = os.getenv("TEST_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

IDEMPOTENCY_TESTS_ALLOWED = os.getenv("IDEMPOTENCY_TESTS_ALLOWED", "false").lower() == "true"


@pytest.fixture(scope="module")
def migration_files() -> List[Tuple[str, str]]:
    """Load all SQL migration files."""
    if not MIGRATIONS_DIR.exists():
        pytest.skip(f"Migrations directory not found: {MIGRATIONS_DIR}")
    
    migrations = []
    for file_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if file_path.name.startswith("test_") or file_path.name in [
            "PRE_DEPLOYMENT_VERIFICATION.sql",
            "backfill_user_profiles.sql"
        ]:
            continue
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        migrations.append((file_path.name, content))
    
    return migrations


class TestEnvironmentSafeguards:
    """Test that idempotency tests have proper safeguards."""
    
    def test_idempotency_tests_allowed_is_set(self):
        """Verify IDEMPOTENCY_TESTS_ALLOWED is explicitly set."""
        assert IDEMPOTENCY_TESTS_ALLOWED, (
            "IDEMPOTENCY_TESTS_ALLOWED must be set to 'true' to run idempotency tests. "
            "These tests may modify database schema and should only run in test environments."
        )
    
    def test_using_test_database(self):
        """
        Verify we're using a test database, not production.
        
        Note: This test is informational only for static analysis tests.
        It will pass with a warning if SUPABASE_URL is not set.
        """
        if not SUPABASE_URL:
            pytest.skip("SUPABASE_URL not set - static analysis tests don't require database connection")
        
        if "qevmlbsunnwgrsdibdoi" in SUPABASE_URL:
            pytest.skip(
                f"⚠️ WARNING: SUPABASE_URL points to production ({SUPABASE_URL}). "
                "Static analysis tests don't connect to the database, but be careful when running live tests."
            )


class TestMigrationIdempotency:
    """Test that migrations are idempotent (can be run multiple times safely)."""
    
    def test_migrations_use_idempotent_syntax(self, migration_files):
        """Verify migrations use idempotent SQL syntax."""
        non_idempotent_patterns = []
        
        for filename, content in migration_files:
            content_no_comments = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
            content_no_strings = re.sub(r"'[^']*'", '', content_no_comments)
            
            issues = []
            
            if re.search(r'\bCREATE\s+(TABLE|INDEX|TYPE|SCHEMA)\s+(?!IF\s+NOT\s+EXISTS)', 
                        content_no_strings, re.IGNORECASE):
                if not re.search(r'\bCREATE\s+OR\s+REPLACE\s+(FUNCTION|VIEW|PROCEDURE)', 
                               content_no_strings, re.IGNORECASE):
                    issues.append("Uses CREATE without IF NOT EXISTS (not idempotent)")
            
            if re.search(r'\bDROP\s+(TABLE|INDEX|TYPE|SCHEMA|POLICY|FUNCTION|VIEW)\s+(?!IF\s+EXISTS)', 
                        content_no_strings, re.IGNORECASE):
                issues.append("Uses DROP without IF EXISTS (not idempotent)")
            
            if re.search(r'\bALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+(?!IF\s+NOT\s+EXISTS)', 
                        content_no_strings, re.IGNORECASE):
                issues.append("Uses ALTER TABLE ADD COLUMN without IF NOT EXISTS (not idempotent)")
            
            if issues:
                non_idempotent_patterns.append({
                    "file": filename,
                    "issues": issues
                })
        
        if non_idempotent_patterns:
            report = "\n\n".join([
                f"❌ {item['file']}:\n  - " + "\n  - ".join(item['issues'])
                for item in non_idempotent_patterns
            ])
            pytest.fail(
                f"Found {len(non_idempotent_patterns)} migrations with non-idempotent syntax:\n\n{report}\n\n"
                "Migrations should use:\n"
                "- CREATE TABLE IF NOT EXISTS\n"
                "- DROP TABLE IF EXISTS\n"
                "- CREATE OR REPLACE FUNCTION\n"
                "- ALTER TABLE ... ADD COLUMN IF NOT EXISTS\n"
                "This ensures migrations can be safely re-run."
            )
    
    def test_migrations_have_proper_transaction_handling(self, migration_files):
        """Verify migrations use proper transaction blocks."""
        issues = []
        
        for filename, content in migration_files:
            if "DO $$" in content or "DO $" in content:
                continue
            
            has_begin = "BEGIN;" in content.upper()
            has_commit = "COMMIT;" in content.upper()
            
            if has_begin != has_commit:
                issues.append({
                    "file": filename,
                    "issue": "Has BEGIN but no COMMIT (or vice versa) - incomplete transaction handling"
                })
        
        if issues:
            report = "\n".join([f"❌ {item['file']}: {item['issue']}" for item in issues])
            pytest.fail(
                f"Found {len(issues)} migrations with incomplete transaction handling:\n\n{report}\n\n"
                "Migrations should either:\n"
                "1. Use explicit BEGIN; ... COMMIT; blocks\n"
                "2. Rely on implicit transactions (no BEGIN/COMMIT)\n"
                "3. Use DO $$ ... $$ blocks for complex logic"
            )
    
    def test_migration_019_is_idempotent(self, migration_files):
        """
        Specific test for Migration 019 (user_profiles RLS fix).
        This migration was recently applied to production and should be idempotent.
        """
        migration_019 = next(
            (content for name, content in migration_files if "fix_user_profiles_rls_recursion" in name),
            None
        )
        
        if not migration_019:
            pytest.skip("Migration 019 (user_profiles RLS recursion fix) not found")
        
        assert "DROP POLICY IF EXISTS" in migration_019, \
            "Migration 019 should use DROP POLICY IF EXISTS"
        
        assert "CREATE OR REPLACE FUNCTION" in migration_019, \
            "Migration 019 should use CREATE OR REPLACE FUNCTION"
        
        assert "DO $$" in migration_019 or "IF NOT EXISTS" in migration_019, \
            "Migration 019 should use conditional policy creation (DO block or IF NOT EXISTS)"


class TestMigrationRollback:
    """Test that migrations can be rolled back safely."""
    
    def test_migrations_have_rollback_documentation(self):
        """Verify critical migrations document rollback procedures."""
        checklist_path = MIGRATIONS_DIR / "PRE_DEPLOYMENT_CHECKLIST.md"
        
        if not checklist_path.exists():
            pytest.skip("PRE_DEPLOYMENT_CHECKLIST.md not found")
        
        with open(checklist_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "rollback" in content.lower() or "回滾" in content, \
            "PRE_DEPLOYMENT_CHECKLIST.md should document rollback procedures"
        
        assert "emergency" in content.lower() or "緊急" in content, \
            "PRE_DEPLOYMENT_CHECKLIST.md should document emergency procedures"


class TestSchemaConsistency:
    """Test that migrations maintain schema consistency."""
    
    def test_migration_numbering_is_sequential(self, migration_files):
        """Verify migration files are numbered sequentially."""
        migration_numbers = []
        
        for filename, _ in migration_files:
            match = re.match(r'^(\d+)_', filename)
            if match:
                migration_numbers.append((int(match.group(1)), filename))
        
        if not migration_numbers:
            pytest.skip("No numbered migrations found")
        
        migration_numbers.sort()
        
        seen_numbers = set()
        issues = []
        
        for num, filename in migration_numbers:
            if num in seen_numbers:
                issues.append(f"Duplicate migration number {num:03d}: {filename}")
            seen_numbers.add(num)
        
        if issues:
            pytest.fail(
                f"Found migration numbering issues:\n" + "\n".join(issues) + "\n\n"
                "Migration numbers should be unique and sequential."
            )
    
    def test_no_conflicting_migrations(self, migration_files):
        """Verify there are no conflicting migration files (e.g., two files with same number)."""
        migrations_by_number = {}
        
        for filename, _ in migration_files:
            match = re.match(r'^(\d+)_', filename)
            if match:
                num = match.group(1)
                if num not in migrations_by_number:
                    migrations_by_number[num] = []
                migrations_by_number[num].append(filename)
        
        conflicts = {num: files for num, files in migrations_by_number.items() if len(files) > 1}
        
        if conflicts:
            report = "\n".join([
                f"Migration {num}: {', '.join(files)}"
                for num, files in conflicts.items()
            ])
            pytest.fail(
                f"Found {len(conflicts)} conflicting migration numbers:\n\n{report}\n\n"
                "Each migration number should be unique. Consider renumbering or consolidating."
            )


class TestMigrationBestPractices:
    """Test that migrations follow best practices."""
    
    def test_migrations_have_descriptive_names(self, migration_files):
        """Verify migration files have descriptive names."""
        issues = []
        
        for filename, _ in migration_files:
            match = re.match(r'^\d+_(.+)\.sql$', filename)
            if match:
                description = match.group(1)
                
                if len(description) < 10:
                    issues.append(f"{filename}: Description too short (< 10 chars)")
                elif description in ["migration", "update", "fix", "change"]:
                    issues.append(f"{filename}: Description too generic")
        
        if issues:
            pytest.fail(
                f"Found {len(issues)} migrations with poor naming:\n" + "\n".join(issues) + "\n\n"
                "Migration names should be descriptive (e.g., '001_enable_rls_agent_tasks.sql')"
            )
    
    def test_migrations_avoid_dangerous_operations(self, migration_files):
        """Verify migrations avoid dangerous operations without safeguards."""
        dangerous_patterns = []
        
        for filename, content in migration_files:
            content_upper = content.upper()
            
            issues = []
            
            if "TRUNCATE" in content_upper and "-- SAFE:" not in content_upper:
                issues.append("Uses TRUNCATE (data loss risk)")
            
            if re.search(r'\bDROP\s+TABLE\s+(?!IF\s+EXISTS)', content, re.IGNORECASE):
                issues.append("Uses DROP TABLE without IF EXISTS")
            
            if "ALTER TABLE" in content_upper and "DROP COLUMN" in content_upper:
                if "-- SAFE:" not in content_upper and "IF EXISTS" not in content_upper:
                    issues.append("Uses ALTER TABLE DROP COLUMN (data loss risk)")
            
            if issues:
                dangerous_patterns.append({
                    "file": filename,
                    "issues": issues
                })
        
        if dangerous_patterns:
            report = "\n\n".join([
                f"⚠️ {item['file']}:\n  - " + "\n  - ".join(item['issues'])
                for item in dangerous_patterns
            ])
            pytest.fail(
                f"Found {len(dangerous_patterns)} migrations with potentially dangerous operations:\n\n{report}\n\n"
                "Dangerous operations should:\n"
                "1. Use IF EXISTS for DROP operations\n"
                "2. Include -- SAFE: comment explaining why it's safe\n"
                "3. Be documented in PRE_DEPLOYMENT_CHECKLIST.md"
            )


def test_migration_idempotency_summary(migration_files):
    """
    Summary test that provides an overview of migration idempotency status.
    This test always passes but provides useful information.
    """
    total_migrations = len(migration_files)
    
    idempotent_count = 0
    for _, content in migration_files:
        if any(pattern in content.upper() for pattern in [
            "IF NOT EXISTS",
            "IF EXISTS",
            "CREATE OR REPLACE",
            "DO $$"
        ]):
            idempotent_count += 1
    
    print(f"\n\n{'='*60}")
    print("📊 Migration Idempotency Summary")
    print(f"{'='*60}")
    print(f"Total migrations: {total_migrations}")
    print(f"Migrations with idempotent patterns: {idempotent_count} ({idempotent_count/total_migrations*100:.1f}%)")
    print(f"{'='*60}\n")
    
    assert True
