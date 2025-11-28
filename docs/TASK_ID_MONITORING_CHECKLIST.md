# Task ID Anomaly Monitoring Checklist

**Version**: 1.0.0  
**Date**: 2025-11-28  
**Purpose**: Quick reference for monitoring task_id related issues in production

---

## Daily Monitoring Checklist

### ✅ Morning Check (5 minutes)

**1. Check for Prefixed Task IDs** (Should be 0 after PR #1592)
```sql
SELECT COUNT(*) as prefixed_count
FROM tasks 
WHERE task_id LIKE 'task-%' 
  AND created_at > NOW() - INTERVAL '24 hours';
```
- ✅ Expected: 0
- ⚠️ Warning: > 0
- 🚨 Critical: > 10

**2. Check for Invalid UUID Formats**
```sql
SELECT COUNT(*) as invalid_count
FROM tasks 
WHERE task_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  AND created_at > NOW() - INTERVAL '24 hours';
```
- ✅ Expected: 0
- ⚠️ Warning: > 0
- 🚨 Critical: > 5

**3. Check for Hash Collisions**
```sql
SELECT hash(task_id::text) as task_hash, COUNT(*) as collision_count
FROM tasks
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY task_hash
HAVING COUNT(*) > 1;
```
- ✅ Expected: 0 rows
- ⚠️ Warning: Any collisions
- 🚨 Critical: > 1 collision/day

---

## Quick Monitoring Script

**Run this daily**:
```bash
cd ~/repos/morningai
source .venv/bin/activate

# Check for task ID anomalies
python tools/monitoring/check_task_id_anomalies.py

# Expected output:
# ✅ Prefixed IDs: 0
# ✅ Invalid UUIDs: 0
# ✅ Hash Collisions: 0
# ✅ Task ID validation complete
```

---

## Common Anomalies & Actions

### 1. Prefixed Task IDs (e.g., "task-550e8400-...")

**Cause**: External tools adding prefixes before passing to API

**Fixed in**: PR #1592 (UUID normalization in `get_task_by_id()`)

**If detected**:
- [ ] Check which external tool is sending prefixed IDs
- [ ] Verify PR #1592 is deployed
- [ ] Review API integration code
- [ ] Update external tool to send clean UUIDs

**Prevention**: API should strip prefixes automatically

---

### 2. Invalid UUID Formats

**Examples**:
- "task-123"
- "abc-def-ghi"
- "12345"
- Empty strings

**Cause**: Manual task creation, API validation bypass, or data corruption

**If detected**:
- [ ] Identify source of invalid IDs (check API logs)
- [ ] Review recent API changes
- [ ] Check if validation was bypassed
- [ ] Add stricter validation if needed
- [ ] Clean up invalid records

**Prevention**: Enforce UUID validation at API entry points

---

### 3. Hash Collisions

**Cause**: Using `hash(task_id)` to convert UUID to int

**Risk**: Task confusion in CodeGenerationWorkflow

**Current Usage**:
```python
# In ProjectEngineerAgent._execute_code_generation()
state = {
    "task_id": hash(task_id),  # Converts UUID to int
    ...
}
```

**If detected**:
- [ ] Review affected tasks
- [ ] Check if tasks were confused/mixed up
- [ ] Consider alternatives to hash():
  - Use UUID string directly
  - Use UUID.int (128-bit integer)
  - Use first 8 hex chars as int

**Long-term solution**: Refactor CodeGenerationWorkflow to accept UUID strings

---

## Weekly Review Checklist

### Monday Morning (10 minutes)

**1. Review Last Week's Anomalies**
```sql
-- Prefixed IDs (last 7 days)
SELECT DATE(created_at) as date, COUNT(*) as count
FROM tasks 
WHERE task_id LIKE 'task-%' 
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date;

-- Invalid UUIDs (last 7 days)
SELECT DATE(created_at) as date, COUNT(*) as count
FROM tasks 
WHERE task_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

**2. Analyze Trends**
- [ ] Are anomalies increasing or decreasing?
- [ ] Any new patterns or sources?
- [ ] Any correlation with deployments?

**3. Update Documentation**
- [ ] Document any new anomaly types discovered
- [ ] Update prevention strategies
- [ ] Share findings with team

---

## Incident Response

### If Anomalies Detected

**Severity P2 (Medium) - Response within 4 hours**:
- Prefixed IDs: 1-10 per day
- Invalid UUIDs: 1-5 per day
- Hash collisions: 1 per week

**Actions**:
1. [ ] Document the anomaly (task_id, timestamp, source)
2. [ ] Check if it caused any task failures
3. [ ] Identify root cause
4. [ ] Implement fix
5. [ ] Monitor for recurrence

**Severity P1 (High) - Response within 1 hour**:
- Prefixed IDs: > 10 per day
- Invalid UUIDs: > 5 per day
- Hash collisions: > 1 per day

**Actions**:
1. [ ] Immediately investigate source
2. [ ] Check for data corruption or API issues
3. [ ] Review recent deployments
4. [ ] Rollback if necessary
5. [ ] Implement emergency fix
6. [ ] Notify team

---

## Monitoring Tools

### Existing Tools

**Planner Statistics**:
```bash
python tools/monitoring/view_planner_stats.py --days 7
```

**Database Access**:
```bash
psql $DATABASE_URL
```

### Recommended New Tools

**Task ID Anomaly Checker** (to be created):
```bash
# tools/monitoring/check_task_id_anomalies.py
python tools/monitoring/check_task_id_anomalies.py

# Options:
--days N          # Check last N days (default: 1)
--format json     # Output in JSON format
--alert           # Send alerts if anomalies found
```

**Example Implementation**:
```python
#!/usr/bin/env python3
"""
Check for task ID anomalies in production database
"""
import sys
from common.database import get_db_session

def check_prefixed_ids(session, days=1):
    """Check for prefixed task IDs"""
    result = session.execute(f"""
        SELECT COUNT(*) FROM tasks 
        WHERE task_id LIKE 'task-%' 
        AND created_at > NOW() - INTERVAL '{days} days'
    """).scalar()
    
    if result > 0:
        print(f"⚠️ WARNING: {result} prefixed task IDs found!")
        return False
    else:
        print(f"✅ Prefixed IDs: 0")
        return True

def check_invalid_uuids(session, days=1):
    """Check for invalid UUID formats"""
    result = session.execute(f"""
        SELECT COUNT(*) FROM tasks 
        WHERE task_id !~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$'
        AND created_at > NOW() - INTERVAL '{days} days'
    """).scalar()
    
    if result > 0:
        print(f"🚨 CRITICAL: {result} invalid task IDs found!")
        return False
    else:
        print(f"✅ Invalid UUIDs: 0")
        return True

def check_hash_collisions(session, days=1):
    """Check for hash collisions"""
    result = session.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT hash(task_id::text) as task_hash
            FROM tasks
            WHERE created_at > NOW() - INTERVAL '{days} days'
            GROUP BY task_hash
            HAVING COUNT(*) > 1
        ) collisions
    """).scalar()
    
    if result > 0:
        print(f"⚠️ WARNING: {result} hash collisions found!")
        return False
    else:
        print(f"✅ Hash Collisions: 0")
        return True

def main():
    session = get_db_session()
    
    print("Checking task ID anomalies...")
    
    all_ok = True
    all_ok &= check_prefixed_ids(session)
    all_ok &= check_invalid_uuids(session)
    all_ok &= check_hash_collisions(session)
    
    if all_ok:
        print("\n✅ Task ID validation complete - No anomalies detected")
        sys.exit(0)
    else:
        print("\n⚠️ Task ID validation complete - Anomalies detected!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Key Takeaways

### ✅ What's Working

1. **UUID Normalization** (PR #1592)
   - Automatically strips prefixes like "task-"
   - Handles external tool integrations gracefully

2. **Path Traversal Prevention** (PR #1664, #1665)
   - Robust security validation
   - Comprehensive test coverage

3. **Granular Permissions** (PR #1665)
   - Separate allowed_files and allowed_directories
   - Clear security boundaries

### ⚠️ Known Issues

1. **Hash Collisions**
   - `hash(task_id)` can cause collisions
   - Consider using UUID string directly in CodeGenerationWorkflow

2. **External Tool Integration**
   - Some tools may add prefixes
   - Monitor for new integration issues

### 🎯 Monitoring Focus

1. **Daily**: Check for any task ID anomalies
2. **Weekly**: Review trends and patterns
3. **Monthly**: Analyze hash collision risk
4. **Quarterly**: Review and update monitoring procedures

---

## Quick Reference

### Expected Values (Normal Operation)

| Metric | Expected | Warning | Critical |
|--------|----------|---------|----------|
| Prefixed IDs | 0 | > 0 | > 10/day |
| Invalid UUIDs | 0 | > 0 | > 5/day |
| Hash Collisions | 0 | > 0 | > 1/week |

### Contact for Issues

- **P3 (Low)**: Create GitHub issue
- **P2 (Medium)**: Notify team lead via Slack
- **P1 (High)**: Page on-call engineer
- **P0 (Critical)**: Page on-call + notify CTO

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-28 | Devin AI | Initial task ID monitoring checklist |

---

**End of Document**
