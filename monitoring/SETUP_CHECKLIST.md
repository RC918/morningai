# ✅ Monitoring Setup Checklist

**Engineering Team**: Use this checklist to set up RLS Phase 2 monitoring

---

## 📋 Pre-requisites

- [ ] Access to Supabase Dashboard
- [ ] Access to Sentry project (optional but recommended)
- [ ] Service role key for Supabase
- [ ] Python 3.8+ installed
- [ ] Email access (for sending reports)

---

## 🔧 Setup Tasks

### 1. Environment Setup (15 minutes)

- [ ] Clone/pull latest code from main branch
- [ ] Navigate to `monitoring/` directory
- [ ] Install Python dependencies:
  ```bash
  pip install -r requirements.txt
  # Or manually: pip install psycopg2-binary sentry-sdk
  ```
- [ ] Set environment variables:
  ```bash
  export DATABASE_URL="postgresql://user:password@host:5432/database"
  export SENTRY_DSN="[your-dsn]"  # Optional
  ```
- [ ] Test connection:
  ```bash
  python -c "import psycopg2; print('✅ psycopg2 OK')"
  ```

---

### 2. SQL Queries Setup (30 minutes)

**Option A: Supabase Dashboard (Recommended)**

- [ ] Open Supabase Dashboard → SQL Editor
- [ ] Create new query folder "RLS Phase 2 Monitoring"
- [ ] For each query file in `sql_queries/`:
  - [ ] `01_rls_health_check.sql` - Copy and save
  - [ ] `02_tenant_isolation_verification.sql` - Copy and save
  - [ ] `03_rls_policy_effectiveness.sql` - Copy and save
  - [ ] `04_user_tenant_coverage.sql` - Copy and save
  - [ ] `05_rls_performance_metrics.sql` - Copy and save
- [ ] Run each query once to verify it works
- [ ] Bookmark the query folder for quick access

**Option B: Command Line (Advanced)**

- [ ] Get database connection string from Supabase
- [ ] Run: `psql $DATABASE_URL -f sql_queries/01_rls_health_check.sql`
- [ ] Repeat for all 5 queries

---

### 3. Sentry Configuration (2 hours)

**Skip this section if Sentry is not available**

- [ ] Log in to Sentry dashboard
- [ ] Navigate to MorningAI backend project
- [ ] Create alert rule #1: tenant_id Errors
  - [ ] Name: "RLS Phase 2 - tenant_id Errors"
  - [ ] Filter: Error message contains "tenant_id"
  - [ ] Condition: Issue is first seen OR > 5 times in 1 hour
  - [ ] Action: Email ryan2939z@gmail.com
- [ ] Create alert rule #2: RLS Policy Violations
  - [ ] Name: "RLS Phase 2 - Policy Violations"
  - [ ] Filter: Error message contains "permission denied for table"
  - [ ] Condition: Issue is first seen
  - [ ] Action: Email + Slack (if configured)
- [ ] Create alert rule #3: Slow Queries
  - [ ] Name: "RLS Phase 2 - Performance"
  - [ ] Filter: Transaction contains "agent_tasks" AND duration > 1000ms
  - [ ] Condition: > 10 times in 1 hour
  - [ ] Action: Daily digest email
- [ ] Test alerts by triggering a test error
- [ ] Verify email is received

---

### 4. Backend Logging Enhancement (1 hour)

**Note**: This is optional if Sentry is not configured

- [ ] Open `handoff/20250928/40_App/orchestrator/persistence/db_writer.py`
- [ ] Add Sentry import at top:
  ```python
  try:
      import sentry_sdk
  except ImportError:
      sentry_sdk = None
  ```
- [ ] In `upsert_task_queued()` function, add tenant context logging:
  ```python
  if sentry_sdk and tenant_id:
      sentry_sdk.set_context("tenant", {"tenant_id": tenant_id, "task_id": task_id})
  ```
- [ ] In exception handling, add tenant context:
  ```python
  if sentry_sdk:
      sentry_sdk.capture_exception(e, extra={"tenant_id": tenant_id or "default"})
  ```
- [ ] Test locally to ensure no import errors
- [ ] Commit changes (will be included in monitoring PR)

---

### 5. Test Monitoring Script (30 minutes)

- [ ] Run morning check test:
  ```bash
  cd monitoring
  python scripts/daily_monitoring_report.py --time morning
  ```
- [ ] Verify output shows all 5 checks passing
- [ ] Run evening check test:
  ```bash
  python scripts/daily_monitoring_report.py --time evening
  ```
- [ ] Verify full report is generated
- [ ] Check that report file is created in `reports/` directory
- [ ] Review report for any unexpected issues

---

### 6. Schedule Daily Monitoring (15 minutes)

**Option A: Cron (Linux/Mac)**

- [ ] Edit crontab: `crontab -e`
- [ ] Add morning check (9 AM):
  ```bash
  0 9 * * * cd /path/to/morningai/monitoring && python scripts/daily_monitoring_report.py --time morning >> logs/morning.log 2>&1
  ```
- [ ] Add evening check (6 PM):
  ```bash
  0 18 * * * cd /path/to/morningai/monitoring && python scripts/daily_monitoring_report.py --time evening | mail -s "RLS Monitoring Report" ryan2939z@gmail.com
  ```
- [ ] Save and verify: `crontab -l`

**Option B: GitHub Actions (Recommended for team)**

- [ ] Create `.github/workflows/monitoring.yml`:
  ```yaml
  name: RLS Monitoring
  on:
    schedule:
      - cron: '0 9 * * *'  # 9 AM UTC
      - cron: '0 18 * * *' # 6 PM UTC
  jobs:
    monitor:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Run monitoring
          env:
            DATABASE_URL: ${{ secrets.DATABASE_URL }}
            SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
          run: |
            pip install -r monitoring/requirements.txt
            python monitoring/scripts/daily_monitoring_report.py --time evening
  ```
- [ ] Add secrets to GitHub repository settings

**Option C: Manual (Temporary)**

- [ ] Set calendar reminders for 9 AM and 6 PM
- [ ] Run manually until automated solution is ready

---

### 7. First Monitoring Report (15 minutes)

- [ ] Run the first official monitoring check:
  ```bash
  python scripts/daily_monitoring_report.py --time evening > reports/first_report.txt
  ```
- [ ] Review the report for any issues
- [ ] Send report to Ryan:
  ```bash
  mail -s "RLS Phase 2 - First Monitoring Report" ryan2939z@gmail.com < reports/first_report.txt
  ```
  Or manually copy report and send via email
- [ ] Post summary in #engineering Slack:
  ```
  ✅ RLS Phase 2 monitoring is now active!
  - All 5 SQL queries configured
  - Sentry alerts set up
  - First report sent to Ryan
  - Daily monitoring starting tomorrow 9 AM
  ```

---

## 🎯 Validation

After completing all setup tasks, verify:

- [ ] All 5 SQL queries run successfully in Supabase
- [ ] Monitoring script runs without errors
- [ ] Report file is generated in `monitoring/reports/`
- [ ] Sentry alerts are configured (or noted as skipped)
- [ ] Daily schedule is set (cron, GitHub Actions, or manual)
- [ ] First report sent to Ryan
- [ ] Team notified in Slack

---

## 📅 Next Steps

### For Next 48 Hours (Critical Period)

**Daily at 9 AM**:
1. Run monitoring script (manual or automated)
2. Check for CRITICAL alerts
3. Review Sentry for new errors
4. Log results

**Daily at 6 PM**:
1. Run full monitoring report
2. Review all 5 queries
3. Send report to Ryan
4. Update team in Slack

### After 48 Hours

- [ ] Review monitoring results with team
- [ ] Decide if any alerts need threshold adjustments
- [ ] Reduce monitoring frequency to daily (9 AM only)
- [ ] Schedule weekly full audit (Fridays)

---

## 🚨 Escalation

If you encounter issues during setup:

1. **Can't access Supabase**: Contact DevOps/Infra team
2. **SQL queries fail**: Check service role key permissions
3. **Sentry not working**: Skip for now, use SQL queries only
4. **Script errors**: Check Python version (3.8+ required)
5. **Other blockers**: Post in #engineering Slack

---

## ✅ Sign-off

**Completed by**: _________________  
**Date**: _________________  
**Time**: _________________  
**Issues encountered**: _________________  
**Notes**: _________________

---

**Estimated Total Time**: 4-5 hours  
**Priority**: P0 (must complete today)  
**Support**: Available via Slack #engineering
