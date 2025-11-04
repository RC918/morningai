# ⚠️ CRITICAL: Supabase Migration Required Before Merge

## 🚨 Blocking Issue

This PR includes changes to the `user` routes that require database schema updates in production. **DO NOT MERGE** until the following migration has been executed in production Supabase.

## 📋 Migration SQL

Execute the following SQL in **Supabase production database** (or staging first for testing):

```sql
-- Add created_at column if not exists
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

-- Add preferences column if not exists
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS preferences TEXT DEFAULT '{}';

-- Backfill NULL values
UPDATE user_profiles 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

UPDATE user_profiles 
SET preferences = '{}' 
WHERE preferences IS NULL;
```

## ✅ Verification Steps

### 1. Verify Schema in Supabase Console

Navigate to: **Supabase Dashboard → Database → Tables → user_profiles**

Or run:

```bash
psql "$DATABASE_URL" -c "\d+ user_profiles"
```

Expected output should include:

```
Column      | Type      | Default
------------+-----------+-------------------------
id          | uuid      | ...
created_at  | timestamp | CURRENT_TIMESTAMP
preferences | text      | '{}'::text
...
```

### 2. Test in Staging First

```bash
# Set staging DATABASE_URL
export DATABASE_URL="postgresql://...staging.supabase.co..."

# Run migration
psql "$DATABASE_URL" -f migration.sql

# Verify
psql "$DATABASE_URL" -c "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='user_profiles' AND column_name IN ('created_at', 'preferences');"
```

### 3. Test Application

```bash
# Run integration tests against staging
export DATABASE_URL="postgresql://...staging.supabase.co..."
export TESTING=false
pytest tests/test_user_production.py -v
```

## 🔍 Why This Migration is Required

The PR adds two new endpoints:
- `GET /api/user/preferences` - Requires `preferences` column
- `POST /api/user/preferences` - Requires `preferences` column
- `GET /api/user/profile` - Uses `created_at` column

Without this migration, production will fail with:
- `column "preferences" does not exist`
- `column "created_at" does not exist`

## 📊 Impact Assessment

**Tables affected**: `user_profiles`  
**Downtime**: None (columns added with defaults)  
**Rollback**: Safe (columns can be dropped if needed)  
**Data loss risk**: None (only adding columns)

## 🚀 Deployment Checklist

- [ ] Execute migration in **staging** Supabase
- [ ] Verify schema in staging
- [ ] Run integration tests against staging
- [ ] Execute migration in **production** Supabase
- [ ] Verify schema in production
- [ ] Monitor Sentry for errors after deployment
- [ ] Merge PR
- [ ] Deploy application
- [ ] Verify `/api/user/preferences` endpoint works

## 🔗 Related

- **Sentry Issue**: #6971362853
- **PR**: #835
- **Migration file**: This document

## ⚠️ DO NOT MERGE UNTIL

✅ Migration executed in production  
✅ Schema verified  
✅ Integration tests pass against production DB

---

**Last updated**: 2025-10-27  
**Author**: Devin (automated)
