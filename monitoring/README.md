# 📊 RLS Phase 2 Production Monitoring System

**Created**: October 18, 2025  
**Purpose**: Monitor tenant isolation and RLS policy effectiveness post-Phase 2 deployment  
**Critical Period**: First 48 hours after deployment

---

## 🎯 Quick Start

### For Daily Monitoring (First 48 Hours)

**Morning Check (9 AM)**:
```bash
# Run critical checks
cd /home/ubuntu/repos/morningai/monitoring
python scripts/daily_monitoring_report.py --time morning
```

**Evening Check (6 PM)**:
```bash
# Run full report
python scripts/daily_monitoring_report.py --time evening
```

---

## 📁 Directory Structure

```
monitoring/
├── README.md                          # This file
├── sql_queries/                       # Supabase SQL monitoring queries
│   ├── 01_rls_health_check.sql       # RLS enabled + policy count
│   ├── 02_tenant_isolation_verification.sql  # NULL tenant_id check
│   ├── 03_rls_policy_effectiveness.sql       # Policy logic validation
│   ├── 04_user_tenant_coverage.sql           # User lockout prevention
│   └── 05_rls_performance_metrics.sql        # Performance monitoring
├── scripts/
│   └── daily_monitoring_report.py    # Automated monitoring script
└── reports/                           # Generated daily reports (auto-created)
```

---

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r monitoring/requirements.txt
# Or manually:
pip install psycopg2-binary sentry-sdk
```

### 2. Set Environment Variables

```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
export SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"  # Optional
```

**Important**: The script now uses direct PostgreSQL connection via `psycopg2` instead of the Supabase client. You need to provide a valid `DATABASE_URL` connection string.

### 3. Configure Supabase SQL Queries

**Option A: Manual Setup**
1. Open Supabase Dashboard → SQL Editor
2. Create new query tab named "RLS Monitoring"
3. Copy each query from `sql_queries/` folder
4. Save and run to verify

**Option B: Direct Database Access** (if psql available)
```bash
psql $DATABASE_URL -f sql_queries/01_rls_health_check.sql
psql $DATABASE_URL -f sql_queries/02_tenant_isolation_verification.sql
# ... repeat for all queries
```

### 4. Test the Monitoring Script

```bash
cd monitoring
python scripts/daily_monitoring_report.py --time morning
```

Expected output:
```
=== RLS Monitoring Report (Morning Check) ===
Timestamp: 2025-10-18T09:00:00Z

Summary:
- Checks Passed: 5/5
- Critical Alerts: 0
- Warning Alerts: 0

✅ No alerts - All systems operational
```

---

## 🚨 Alert Levels

| Level | Symbol | Meaning | Action Required |
|-------|--------|---------|-----------------|
| **OK** | ✅ | All checks passed | Continue monitoring |
| **WARNING** | 🟡 | Anomaly detected, non-critical | Investigate within 24h |
| **CRITICAL** | 🔴 | Security/data integrity issue | **Immediate action required** |

### Critical Alert Triggers

1. **NULL tenant_id detected** → Users can see all data (RLS bypass)
2. **RLS policy disabled** → No tenant isolation
3. **Users without tenant_id** → Locked out by RLS
4. **Orphaned tasks** → Data integrity violation

---

## 📋 SQL Queries Explained

### Query 1: RLS Health Check
**Purpose**: Verify RLS is enabled on critical tables  
**Frequency**: Daily (9 AM)  
**Alert if**: RLS disabled OR no policies found  

**What it checks**:
- `agent_tasks` table has RLS enabled
- At least 5 policies exist (service_role + 4 user policies)
- Policies are active and correctly configured

---

### Query 2: Tenant Isolation Verification
**Purpose**: Ensure all tasks have valid tenant_id  
**Frequency**: Every 4 hours (first 48h), then daily  
**Alert if**: NULL tenant_id found  

**What it checks**:
- Count of tasks with NULL tenant_id (should be 0)
- Tenant coverage percentage (should be 100%)
- Distribution across tenants

---

### Query 3: RLS Policy Effectiveness
**Purpose**: Verify policies enforce tenant isolation  
**Frequency**: Daily (9 AM)  
**Alert if**: Policies using `USING(true)` instead of tenant checks  

**What it checks**:
- Phase 1 policies (insecure) vs Phase 2 policies (secure)
- Policy logic includes `tenant_id` comparison
- No overly permissive policies for regular users

---

### Query 4: User Tenant Coverage
**Purpose**: Prevent user lockouts  
**Frequency**: Daily (6 PM)  
**Alert if**: Users with NULL tenant_id found  

**What it checks**:
- All users have tenant_id assigned
- No orphaned users (tenant_id references deleted tenant)
- Tenant membership distribution

---

### Query 5: Performance Metrics
**Purpose**: Detect RLS-related performance issues  
**Frequency**: Weekly  
**Alert if**: Query time > 1 second OR index not used  

**What it checks**:
- `idx_agent_tasks_tenant_id` index is being used
- Query execution time is acceptable
- No performance regression from Phase 2 changes

---

## 🔄 Monitoring Schedule

### First 48 Hours (Critical Period)

| Time | Action | Queries | Report To |
|------|--------|---------|-----------|
| 9:00 AM | Morning check | 1, 2, 3 | Log only |
| 1:00 PM | Quick check | 2 only | Log only |
| 6:00 PM | Evening report | 1, 2, 3, 4, 5 | Ryan (email) |

### After 48 Hours (Steady State)

| Frequency | Action | Queries |
|-----------|--------|---------|
| Daily 9 AM | Health check | 1, 2 |
| Weekly (Friday) | Full audit | 1, 2, 3, 4, 5 |
| Monthly | Performance review | 5 only |

---

## 📧 Reporting

### Morning Report (9 AM)
- **Audience**: Engineering team (internal)
- **Format**: Summary only
- **Alerts only**: Only send if issues detected

### Evening Report (6 PM)
- **Audience**: Ryan (CEO/CTO)
- **Format**: Full report with all metrics
- **Always send**: Yes (even if no issues)

### Report Delivery Methods

**Email** (Primary):
```bash
python scripts/daily_monitoring_report.py --time evening | mail -s "RLS Monitoring Report" ryan2939z@gmail.com
```

**Slack** (Optional):
```bash
# Configure Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python scripts/daily_monitoring_report.py --time evening | slack-cli send --channel #morningai-alerts
```

**File** (Auto-saved):
```
monitoring/reports/rls_report_20251018.txt
```

---

## 🚨 Incident Response

### If CRITICAL Alert Detected

1. **Stop and Assess**
   - What query failed?
   - How many rows affected?
   - Is it actively worsening?

2. **Immediate Mitigation**
   - If NULL tenant_id: Stop creating new tasks
   - If RLS disabled: Enable immediately
   - If users locked out: Assign tenant_id

3. **Notify**
   - Engineering Team Lead
   - Ryan (CEO)
   - Post in #engineering Slack

4. **Fix**
   - Follow incident playbook in `MONITORING_SETUP_GUIDE.md`
   - Deploy hotfix if needed
   - Verify fix with monitoring queries

5. **Document**
   - Create postmortem issue
   - Update monitoring thresholds if needed

---

## 🎯 Success Criteria

After 48 hours, monitoring is successful if:

- ✅ Zero NULL tenant_id detected
- ✅ Zero RLS policy errors
- ✅ Zero user lockouts
- ✅ Zero orphaned tasks
- ✅ Performance stable (no regression)

If all criteria met → Reduce monitoring frequency to weekly

---

## 🔧 Troubleshooting

### Script Fails: "DATABASE_URL not set"
**Solution**:
```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### Script Fails: "psycopg2 module not found"
**Solution**:
```bash
pip install psycopg2-binary sentry-sdk
```

### SQL Query Returns Error: "permission denied"
**Solution**: Use service role key, not anon key

### Sentry Not Receiving Events
**Solution**:
1. Verify `SENTRY_DSN` is set correctly
2. Check Sentry project exists
3. Test with: `sentry_sdk.capture_message("Test")`

---

## 📚 Additional Resources

- **Full Monitoring Guide**: See `MONITORING_SETUP_GUIDE.md` attachment
- **Engineering Instructions**: See `ENGINEERING_TEAM_INSTRUCTIONS.md` attachment
- **RLS Phase 2 Details**: See `docs/RLS_IMPLEMENTATION_GUIDE.md`
- **Migration Scripts**: See `migrations/003_*.sql` and `migrations/004_*.sql`

---

## 🙋 Support

**Technical Questions**: 
- Devin (Acting CTO) via GitHub issues
- Engineering Team Lead

**Urgent Issues**:
- Slack: #engineering
- Email: ryan2939z@gmail.com

---

## 📝 Changelog

### v1.0 - October 18, 2025
- Initial monitoring system setup
- 5 SQL queries created
- Python automation script
- Sentry integration
- Daily reporting workflow

---

**Next Review**: After 48-hour monitoring period completes
