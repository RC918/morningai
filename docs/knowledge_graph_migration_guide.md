# Knowledge Graph Database Migration Guide

This guide covers database setup, migration execution, and rollback procedures for the Knowledge Graph system.

---

## Prerequisites

### 1. Database Requirements

- **PostgreSQL**: Version 12 or higher
- **pgvector Extension**: Required for vector operations
- **Connection**: Admin access to PostgreSQL instance

### 2. Environment Variables

```bash
# Required
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export SUPABASE_DB_PASSWORD="your-database-password"

# Optional but recommended
export OPENAI_API_KEY="sk-..."
export REDIS_URL="redis://..."
export OPENAI_MAX_DAILY_COST="5.0"
```

---

## Migration Workflow

### Development Environment

#### Step 1: Verify pgvector Availability

```bash
# Connect to PostgreSQL
psql $SUPABASE_URL

# Check if pgvector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

**Expected Output**:
```
   name   | default_version | installed_version |      comment
----------+-----------------+-------------------+-------------------
 vector   | 0.5.0          |                   | vector data type
```

If not available, install pgvector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Step 2: Run Migration Script (Interactive)

```bash
cd /path/to/morningai
python agents/dev_agent/migrations/run_migration.py
```

The script will:
1. ✅ Check pgvector extension availability
2. ✅ Check for existing tables
3. ✅ Show migration SQL preview
4. ❓ Ask for confirmation
5. ✅ Execute migration in transaction
6. ✅ Verify tables and indexes created

**Sample Output**:
```
=== Knowledge Graph Database Migration ===

[1/5] Checking pgvector extension...
✓ pgvector extension is available (version 0.5.0)

[2/5] Checking existing tables...
ℹ Tables not found (first-time setup)

[3/5] Loading migration SQL...
✓ Migration SQL loaded (125 lines)

Migration Preview:
------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS code_embeddings (
    id SERIAL PRIMARY KEY,
    ...
);
------------------------------------------------------------

[4/5] Ready to execute migration
⚠️  This will create 4 tables and indexes in your database.

Continue? (yes/no): yes

[5/5] Executing migration...
✓ Migration executed successfully!

Created tables:
  - code_embeddings
  - code_patterns
  - code_relationships
  - embedding_cache_stats

Created indexes:
  - code_embeddings_embedding_idx (HNSW)
  - code_embeddings_file_path_idx
  - ...

Migration completed successfully! ✓
```

### Staging Environment

#### Step 1: Create Test Database Backup

```bash
# Before migration, create backup
pg_dump $STAGING_DB_URL > staging_backup_$(date +%Y%m%d).sql
```

#### Step 2: Execute Migration (Same as Dev)

```bash
export SUPABASE_URL=$STAGING_DB_URL
export SUPABASE_DB_PASSWORD=$STAGING_DB_PASSWORD

python agents/dev_agent/migrations/run_migration.py
```

#### Step 3: Verification Checklist

- [ ] All 4 tables created (`code_embeddings`, `code_patterns`, `code_relationships`, `embedding_cache_stats`)
- [ ] HNSW index on `code_embeddings.embedding` created
- [ ] Unique constraints working (test duplicate insert)
- [ ] pgvector operations work (test similarity search)
- [ ] Application can connect and query

**Verification Script**:
```bash
pytest agents/dev_agent/tests/kg_e2e/test_migration_creates_tables.py -v
```

#### Step 4: Test Application Integration

```bash
# Run E2E tests
pytest agents/dev_agent/tests/kg_e2e/ -v

# Test indexing small codebase
python agents/dev_agent/examples/knowledge_graph_example.py
```

### Production Environment

**⚠️ CRITICAL: Follow this checklist exactly**

#### Pre-Migration Checklist

- [ ] Migration tested successfully in staging
- [ ] Database backup created and verified
- [ ] Downtime window scheduled (if required)
- [ ] Rollback plan prepared
- [ ] Team notified

#### Step 1: Create Production Backup

```bash
# Full database backup
pg_dump $PRODUCTION_DB_URL -Fc > prod_backup_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
pg_restore --list prod_backup_*.dump | head -20
```

#### Step 2: Test Backup Restore (Optional but Recommended)

```bash
# Create test database
createdb test_restore

# Restore backup
pg_restore -d test_restore prod_backup_*.dump

# Verify
psql test_restore -c "SELECT count(*) FROM information_schema.tables;"
```

#### Step 3: Execute Migration

```bash
export SUPABASE_URL=$PRODUCTION_DB_URL
export SUPABASE_DB_PASSWORD=$PRODUCTION_DB_PASSWORD

python agents/dev_agent/migrations/run_migration.py
```

**Review migration output carefully. If any errors occur, proceed to rollback.**

#### Step 4: Post-Migration Verification

```bash
# Connect to production database
psql $PRODUCTION_DB_URL

# Verify tables
\dt

# Verify indexes
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename LIKE 'code_%';

# Test vector operations
SELECT version FROM pg_extension WHERE extname = 'vector';

# Test similarity search
SELECT file_path, embedding <=> '[0.1, 0.1, ...]'::vector AS distance
FROM code_embeddings
LIMIT 1;
```

#### Step 5: Monitor Application

- [ ] Application starts without errors
- [ ] Health check endpoint returns 200
- [ ] API can generate embeddings
- [ ] Searches return results (if data present)
- [ ] Error logs show no database issues

---

## Rollback Procedures

### Scenario 1: Migration Failed During Execution

**The migration script uses transactions, so failure = automatic rollback.**

```sql
-- Verify rollback happened
psql $DB_URL -c "\dt"

-- Should NOT see code_embeddings, code_patterns, etc.
```

No action needed - just fix the issue and retry.

### Scenario 2: Migration Succeeded but Application Issues

#### Option A: Drop New Tables (Clean Rollback)

```bash
# Connect to database
psql $DB_URL

# Execute rollback
\i agents/dev_agent/migrations/002_drop_knowledge_graph_tables.sql
```

**Rollback SQL** (`002_drop_knowledge_graph_tables.sql`):
```sql
-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS code_relationships CASCADE;
DROP TABLE IF EXISTS code_patterns CASCADE;
DROP TABLE IF EXISTS embedding_cache_stats CASCADE;
DROP TABLE IF EXISTS code_embeddings CASCADE;

-- Optionally drop extension (only if not used elsewhere)
-- DROP EXTENSION IF EXISTS vector;

-- Verify
SELECT tablename FROM pg_tables WHERE tablename LIKE 'code_%';
```

#### Option B: Restore from Backup (Full Restore)

```bash
# Drop current database (⚠️ DANGER)
dropdb $DB_NAME

# Recreate database
createdb $DB_NAME

# Restore from backup
pg_restore -d $DB_NAME prod_backup_*.dump

# Verify
psql $DB_NAME -c "SELECT count(*) FROM information_schema.tables;"
```

### Scenario 3: Partial Data Issues

If migration succeeded but data is corrupted:

```sql
-- Truncate tables (keep schema)
TRUNCATE TABLE code_embeddings CASCADE;
TRUNCATE TABLE code_patterns CASCADE;
TRUNCATE TABLE code_relationships CASCADE;
TRUNCATE TABLE embedding_cache_stats CASCADE;

-- Re-index from scratch
-- Use application indexing command
```

---

## Troubleshooting

### Issue: pgvector Extension Not Available

**Symptoms**:
```
ERROR: extension "vector" is not available
```

**Solution**:
1. **Supabase**: Enable pgvector in Dashboard → Extensions
2. **Self-hosted**: Install pgvector:
   ```bash
   git clone https://github.com/pgvector/pgvector.git
   cd pgvector
   make
   sudo make install
   ```

### Issue: Permission Denied

**Symptoms**:
```
ERROR: permission denied to create extension "vector"
```

**Solution**:
```sql
-- Grant superuser temporarily
ALTER USER postgres SUPERUSER;

-- Create extension
CREATE EXTENSION vector;

-- Revoke superuser
ALTER USER postgres NOSUPERUSER;
```

### Issue: Index Creation Slow

**Symptoms**:
```
Creating index... (taking >5 minutes)
```

**Solution**:
HNSW index creation is slow for large datasets. This is normal.

- **Small (<10K vectors)**: ~30 seconds
- **Medium (10K-100K)**: ~2-5 minutes
- **Large (>100K)**: ~10-30 minutes

To monitor progress:
```sql
SELECT now(), * FROM pg_stat_progress_create_index;
```

### Issue: Migration Hangs

**Symptoms**:
Script hangs at "Executing migration..."

**Solution**:
1. Check for locks:
   ```sql
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

2. Check for blocking queries:
   ```sql
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

3. Cancel and retry:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE datname = 'your_db' AND state = 'idle in transaction';
   ```

---

## HNSW Index Optimization

### When to Re-index

Re-create HNSW index if:
- Database has grown significantly (>10x vectors)
- Query performance degraded (P95 > 100ms)
- You need to change index parameters

### Re-indexing Procedure

```sql
-- Drop existing index
DROP INDEX IF EXISTS code_embeddings_embedding_idx;

-- Recreate with new parameters (adjust m and ef_construction)
CREATE INDEX code_embeddings_embedding_idx 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 32, ef_construction = 128);  -- Increased for better accuracy
```

**Parameter Guidelines**:
| Dataset Size | m | ef_construction | Build Time | Query Speed |
|--------------|---|----------------|------------|-------------|
| <10K         | 16 | 64             | ~30s       | ~5ms        |
| 10K-100K     | 16-32 | 64-128     | ~2-5min    | ~10-20ms    |
| >100K        | 32-64 | 128-256    | ~10-30min  | ~20-40ms    |

---

## Best Practices

### 1. Always Use Staging First

Never run migrations directly in production without testing in staging.

### 2. Create Backups

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kg_backup_$TIMESTAMP.dump"

pg_dump $DB_URL -Fc > $BACKUP_FILE

# Keep last 7 days
find $BACKUP_DIR -name "kg_backup_*.dump" -mtime +7 -delete
```

### 3. Monitor After Migration

```bash
# Watch PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log | grep "code_"

# Watch application logs
tail -f /var/log/app/knowledge_graph.log
```

### 4. Schedule Maintenance Window

For large production databases:
- Schedule during low-traffic hours
- Notify users of potential brief disruption
- Have rollback plan ready

---

## Appendix: Manual Migration Steps

If the migration script doesn't work, you can execute manually:

```bash
# 1. Connect to database
psql $SUPABASE_URL

# 2. Create extension
CREATE EXTENSION IF NOT EXISTS vector;

# 3. Execute migration SQL
\i agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql

# 4. Verify
\dt
\di

# 5. Test vector operations
SELECT '[0.1]'::vector <=> '[0.2]'::vector;
```

---

## Support

If you encounter issues not covered in this guide:

1. Check application logs: `logs/knowledge_graph.log`
2. Check database logs: `pg_log` or Supabase Dashboard
3. Run diagnostic: `python agents/dev_agent/migrations/run_migration.py --check-only`
4. Create issue with error details

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-17  
**Compatibility**: PostgreSQL 12+, pgvector 0.5.0+
