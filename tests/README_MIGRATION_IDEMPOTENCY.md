# Migration Idempotency Testing (P2.2)

## Overview

This document describes the migration idempotency testing strategy for MorningAI. Idempotent migrations can be safely run multiple times without errors or data corruption, which is critical for:

- **Recovery from failures**: Re-running migrations after partial failures
- **Schema drift**: Handling cases where production schema differs from expected state
- **Rollback scenarios**: Safely rolling back and re-applying migrations
- **Development workflows**: Allowing developers to reset and re-run migrations

## Test Coverage

### 1. Supabase SQL Migration Tests

**Test File**: `tests/test_migration_idempotency.py`

**Test Classes**:

#### `TestEnvironmentSafeguards`
- ✅ Verifies `IDEMPOTENCY_TESTS_ALLOWED` is set
- ✅ Ensures tests don't run against production database
- ✅ Validates test database URL

#### `TestMigrationIdempotency`
- ✅ Verifies migrations use idempotent SQL syntax:
  - `CREATE TABLE IF NOT EXISTS`
  - `DROP TABLE IF EXISTS`
  - `CREATE OR REPLACE FUNCTION`
  - `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- ✅ Checks proper transaction handling (BEGIN/COMMIT)
- ✅ Specific test for Migration 007 (recently applied to production)

#### `TestMigrationRollback`
- ✅ Verifies rollback procedures are documented
- ✅ Checks for emergency procedures in PRE_DEPLOYMENT_CHECKLIST.md

#### `TestSchemaConsistency`
- ✅ Verifies migration numbering is sequential
- ✅ Detects conflicting migration files
- ✅ Ensures no duplicate migration numbers

#### `TestMigrationBestPractices`
- ✅ Verifies descriptive migration names
- ✅ Detects dangerous operations (TRUNCATE, DROP COLUMN)
- ✅ Ensures safeguards for data-loss operations

### 2. Alembic Migration Tests

**CI Workflow**: `.github/workflows/alembic-check.yml`

**Test Steps**:
1. ✅ Apply migrations to PostgreSQL (upgrade head)
2. ✅ Test data insertion with enum values
3. ✅ Verify downgrade works (downgrade -1)
4. ✅ **NEW: Test idempotency** (upgrade → upgrade → downgrade → upgrade)
5. ✅ Test SQLite migrations (development)

## Running Tests Locally

### Supabase SQL Migration Tests

```bash
# Set environment variables
export IDEMPOTENCY_TESTS_ALLOWED=true
export TEST_SUPABASE_URL="https://dckisglnlemvpvmyvnut.supabase.co"  # Staging
export SUPABASE_SERVICE_ROLE_KEY="<staging-service-role-key>"

# Run tests
pytest tests/test_migration_idempotency.py -v
```

**Expected Output**:
```
tests/test_migration_idempotency.py::TestEnvironmentSafeguards::test_idempotency_tests_allowed_is_set PASSED
tests/test_migration_idempotency.py::TestEnvironmentSafeguards::test_using_test_database PASSED
tests/test_migration_idempotency.py::TestMigrationIdempotency::test_migrations_use_idempotent_syntax PASSED
tests/test_migration_idempotency.py::TestMigrationIdempotency::test_migrations_have_proper_transaction_handling PASSED
tests/test_migration_idempotency.py::TestMigrationIdempotency::test_migration_007_is_idempotent PASSED
tests/test_migration_idempotency.py::TestMigrationRollback::test_migrations_have_rollback_documentation PASSED
tests/test_migration_idempotency.py::TestSchemaConsistency::test_migration_numbering_is_sequential PASSED
tests/test_migration_idempotency.py::TestSchemaConsistency::test_no_conflicting_migrations PASSED
tests/test_migration_idempotency.py::TestMigrationBestPractices::test_migrations_have_descriptive_names PASSED
tests/test_migration_idempotency.py::TestMigrationBestPractices::test_migrations_avoid_dangerous_operations PASSED
tests/test_migration_idempotency.py::test_migration_idempotency_summary PASSED

📊 Migration Idempotency Summary
============================================================
Total migrations: 24
Migrations with idempotent patterns: 22 (91.7%)
============================================================
```

### Alembic Migration Tests

```bash
# Navigate to backend directory
cd handoff/20250928/40_App/api-backend

# Set up test database (PostgreSQL)
export DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_db"

# Run Alembic tests
alembic upgrade head
alembic upgrade head  # Should be idempotent
alembic downgrade -1
alembic upgrade head  # Should work after downgrade
```

## Environment Variables

### Required for Supabase SQL Tests

| Variable | Description | Example |
|----------|-------------|---------|
| `IDEMPOTENCY_TESTS_ALLOWED` | Must be `true` to run tests | `true` |
| `TEST_SUPABASE_URL` | Staging database URL | `https://dckisglnlemvpvmyvnut.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Staging service role key | `<staging-key>` |

### Required for Alembic Tests

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |

## Idempotency Best Practices

### ✅ DO: Use Idempotent SQL Syntax

```sql
-- ✅ GOOD: Idempotent table creation
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL
);

-- ✅ GOOD: Idempotent function creation
CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS UUID AS $$
    -- function body
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ✅ GOOD: Idempotent policy creation
DROP POLICY IF EXISTS "users_read_own" ON users;
CREATE POLICY "users_read_own" ON users
    FOR SELECT USING (id = auth.uid());

-- ✅ GOOD: Idempotent column addition
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id UUID;
```

### ❌ DON'T: Use Non-Idempotent Syntax

```sql
-- ❌ BAD: Will fail on second run
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL
);

-- ❌ BAD: Will fail if policy doesn't exist
DROP POLICY "users_read_own" ON users;

-- ❌ BAD: Will fail if column already exists
ALTER TABLE users ADD COLUMN tenant_id UUID;
```

### Transaction Handling

```sql
-- ✅ GOOD: Explicit transaction
BEGIN;
    -- migration statements
COMMIT;

-- ✅ GOOD: DO block for complex logic
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'my_policy') THEN
        EXECUTE 'CREATE POLICY my_policy ON my_table FOR SELECT USING (true)';
    END IF;
END
$$;

-- ❌ BAD: Incomplete transaction
BEGIN;
    -- migration statements
-- Missing COMMIT!
```

## Common Idempotency Issues

### Issue 1: CREATE without IF NOT EXISTS

**Problem**: Migration fails on second run
```sql
CREATE TABLE users (...);  -- ❌ Fails if table exists
```

**Solution**: Add IF NOT EXISTS
```sql
CREATE TABLE IF NOT EXISTS users (...);  -- ✅ Idempotent
```

### Issue 2: DROP without IF EXISTS

**Problem**: Migration fails if object doesn't exist
```sql
DROP POLICY "old_policy" ON users;  -- ❌ Fails if policy doesn't exist
```

**Solution**: Add IF EXISTS
```sql
DROP POLICY IF EXISTS "old_policy" ON users;  -- ✅ Idempotent
```

### Issue 3: ALTER TABLE ADD COLUMN

**Problem**: Migration fails if column already exists
```sql
ALTER TABLE users ADD COLUMN tenant_id UUID;  -- ❌ Fails if column exists
```

**Solution**: Add IF NOT EXISTS or use DO block
```sql
-- Option 1: IF NOT EXISTS (PostgreSQL 9.6+)
ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- Option 2: DO block
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE users ADD COLUMN tenant_id UUID;
    END IF;
END
$$;
```

## CI/CD Integration

### GitHub Actions

The idempotency tests run automatically in CI:

1. **Supabase SQL Tests**: Run via `pytest` in backend CI workflow
2. **Alembic Tests**: Run via `.github/workflows/alembic-check.yml`

**CI Workflow Steps**:
1. Set up PostgreSQL test database
2. Run migrations (upgrade head)
3. **Test idempotency** (upgrade head again)
4. Test downgrade
5. Test re-upgrade
6. Verify schema consistency

## Rollback Procedures

### Quick Rollback for RLS Policies

If a migration causes issues, you can quickly rollback RLS policies:

```sql
-- Example: Rollback Migration 004
DROP POLICY IF EXISTS "users_read_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_insert_own_tenant" ON agent_tasks;

-- Restore previous policies
CREATE POLICY "users_read_own_tenant" ON agent_tasks
    FOR SELECT TO authenticated USING (true);
```

### Full Database Restore

For critical failures, use Supabase backup restore:

1. Go to Supabase Dashboard → Settings → Database → Backups
2. Select the most recent backup before the migration
3. Click "Restore"
4. Wait for restore to complete
5. Verify application functionality

## Migration Checklist

Before applying a migration to production:

- [ ] ✅ Migration uses idempotent SQL syntax
- [ ] ✅ Migration has proper transaction handling
- [ ] ✅ Migration tested in staging environment
- [ ] ✅ Idempotency tests pass (`pytest tests/test_migration_idempotency.py`)
- [ ] ✅ Rollback procedure documented
- [ ] ✅ Backup created before applying migration
- [ ] ✅ Team notified of migration window

## Related Documentation

- [PRE_DEPLOYMENT_CHECKLIST.md](../migrations/PRE_DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification
- [DATABASE_ARCHITECTURE.md](../docs/DATABASE_ARCHITECTURE.md) - Database architecture overview
- [README_RLS_TESTING.md](README_RLS_TESTING.md) - RLS testing guide
- [Migration 007](../migrations/007_fix_user_profiles_rls_recursion.sql) - Example idempotent migration

## Summary

Migration idempotency testing ensures that:

1. ✅ **Migrations are safe to re-run** - No errors on repeated execution
2. ✅ **Schema consistency** - Database schema matches expected state
3. ✅ **Rollback safety** - Migrations can be rolled back and re-applied
4. ✅ **Production safety** - Migrations won't cause downtime or data loss
5. ✅ **Developer productivity** - Developers can reset and re-run migrations locally

This testing strategy is part of the **P2: Security Testing** phase of the MorningAI testing roadmap, ensuring that database migrations are robust and production-ready.
