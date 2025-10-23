# Database Migrations

This directory contains SQL migration files for the MorningAI database schema.

## Week 1 Metrics Tables (001_week1_metrics_tables.sql)

### Purpose
Support UX baseline measurement as outlined in the Design System Enhancement Roadmap Week 1 tasks.

### Tables Created

#### 1. `ttv_metrics` (Time to Value Metrics)
Tracks the time from user first login to completion of first valuable operation.

**Columns:**
- `id` (UUID): Primary key
- `user_id` (TEXT): User identifier
- `tenant_id` (TEXT): Tenant identifier
- `ttv_ms` (INTEGER): Time to Value in milliseconds
- `operation` (TEXT): Type of first valuable operation
- `timestamp` (TIMESTAMPTZ): When the operation occurred
- `created_at` (TIMESTAMPTZ): Record creation time

**Indexes:**
- `idx_ttv_metrics_user_id`: Query by user
- `idx_ttv_metrics_tenant_id`: Query by tenant
- `idx_ttv_metrics_timestamp`: Time-based queries
- `idx_ttv_metrics_operation`: Query by operation type

**Baseline Target:** 50+ samples, TTV < 10 minutes

#### 2. `path_tracking` (Critical Path Tracking)
Tracks user completion of critical paths for success rate measurement.

**Columns:**
- `id` (UUID): Primary key
- `user_id` (TEXT): User identifier
- `tenant_id` (TEXT): Tenant identifier
- `path_name` (TEXT): Name of the critical path
- `status` (TEXT): Path status (in_progress, completed, failed)
- `duration_ms` (INTEGER): Path completion duration
- `error` (TEXT): Error message for failed paths
- `timestamp` (TIMESTAMPTZ): When the path event occurred
- `created_at` (TIMESTAMPTZ): Record creation time

**Indexes:**
- `idx_path_tracking_user_id`: Query by user
- `idx_path_tracking_tenant_id`: Query by tenant
- `idx_path_tracking_path_name`: Query by path name
- `idx_path_tracking_status`: Query by status
- `idx_path_tracking_timestamp`: Time-based queries

**Critical Paths Tracked:**
1. Login flow
2. Dashboard customization
3. Decision approval
4. Cost viewing
5. Strategy management

**Baseline Target:** 100+ samples, success rate > 95%

### Security

Both tables have Row Level Security (RLS) enabled with the following policies:

- **Users**: Can insert and view their own metrics
- **Service Role**: Full access for analytics and reporting

### How to Apply

Run the migration in your Supabase SQL Editor:

```sql
-- Copy and paste the contents of 001_week1_metrics_tables.sql
```

Or use the Supabase CLI:

```bash
supabase db push
```

### Verification

After applying the migration, verify the tables exist:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('ttv_metrics', 'path_tracking');
```

### Data Collection

Data is automatically collected via:

1. **TTV Tracking**: 
   - `App.jsx` tracks first login time in localStorage
   - CustomEvent `first-value-operation` triggers TTV calculation
   - Data sent to Sentry for collection

2. **Path Tracking**:
   - `appStore.js` provides `trackPathStart()`, `trackPathComplete()`, `trackPathFail()`
   - Components call these methods at path boundaries
   - Data sent to Sentry for collection

### Week 2 Baseline Collection

After deploying Week 1 code:
- Collect 50+ TTV samples over 1 week
- Collect 100+ path tracking samples
- Calculate mean, median, P90 for TTV
- Calculate success rate for each critical path
- Generate baseline report

### Related Files

- Frontend tracking: `frontend-dashboard-deploy/src/App.jsx`
- Path tracking store: `frontend-dashboard-deploy/src/stores/appStore.js`
- Roadmap: `docs/UX/DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md`
