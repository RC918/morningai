# Phase 2 Production Monitoring Guide

**Version**: 1.0.0  
**Date**: 2025-11-28  
**Status**: Active  

---

## Overview

This guide provides monitoring procedures for Phase 2 ProjectEngineerAgent deployment in production. It covers key metrics, anomaly detection, and incident response procedures.

**Phase 2 Components**:
- ProjectEngineerAgent (Devin-like meta-agent)
- CodeGenerationWorkflow (LangGraph-based code generation)
- Safe Tasks whitelist (9 task types)
- Per-task directory whitelist (security sandbox)

---

## Table of Contents

1. [Critical Metrics](#1-critical-metrics)
2. [Task ID Anomaly Detection](#2-task-id-anomaly-detection)
3. [Security Monitoring](#3-security-monitoring)
4. [Performance Monitoring](#4-performance-monitoring)
5. [Error Monitoring](#5-error-monitoring)
6. [Incident Response](#6-incident-response)
7. [Daily Checklist](#7-daily-checklist)
8. [Weekly Review](#8-weekly-review)

---

## 1. Critical Metrics

### 1.1 Task Execution Metrics

**Key Performance Indicators (KPIs)**:

| Metric | Target | Warning | Critical | Description |
|--------|--------|---------|----------|-------------|
| Task Success Rate | > 95% | < 90% | < 80% | Percentage of tasks completed successfully |
| Average Task Duration | < 5 min | > 10 min | > 15 min | Time from task start to completion |
| Task Classification Accuracy | > 90% | < 85% | < 75% | Correct task type classification rate |
| Safe Task Execution Rate | 100% | < 100% | < 100% | Only safe tasks should execute |
| Path Traversal Blocks | 0 expected | > 0 | > 5/day | Security violations blocked |

**Monitoring Commands**:
```bash
# View recent task execution stats
python tools/monitoring/view_planner_stats.py --days 1

# Check task success rate
python tools/monitoring/view_planner_stats.py --metric success_rate

# View task duration distribution
python tools/monitoring/view_planner_stats.py --metric duration
```

### 1.2 Code Generation Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| PR Creation Success Rate | > 90% | < 80% | < 70% |
| Code Generation Failures | < 5% | > 10% | > 20% |
| Security Validation Failures | 0 | > 0 | > 3/day |
| Rollback Events | < 1% | > 5% | > 10% |

---

## 2. Task ID Anomaly Detection

### 2.1 Task ID Format Validation

**Expected Format**: UUID v4 (36 characters with hyphens)
```
Example: 550e8400-e29b-41d4-a716-446655440000
```

**Common Anomalies**:

1. **Prefixed Task IDs** (Fixed in PR #1592)
   - Pattern: `task-550e8400-e29b-41d4-a716-446655440000`
   - Cause: External tools adding prefixes
   - Fix: UUID normalization in `get_task_by_id()`

2. **Hash Collisions**
   - Pattern: Multiple tasks with same `hash(task_id)`
   - Cause: `hash()` converting UUID to int
   - Risk: Task confusion in CodeGenerationWorkflow

3. **Invalid UUIDs**
   - Pattern: Non-UUID strings (e.g., "task-123", "abc")
   - Cause: Manual task creation or API misuse
   - Action: Reject with clear error message

### 2.2 Monitoring Queries

**Check for Task ID Anomalies**:
```sql
-- Find prefixed task IDs (should be 0 after PR #1592)
SELECT task_id, created_at 
FROM tasks 
WHERE task_id LIKE 'task-%' 
  AND created_at > NOW() - INTERVAL '24 hours';

-- Find invalid UUID formats
SELECT task_id, created_at 
FROM tasks 
WHERE task_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  AND created_at > NOW() - INTERVAL '24 hours';

-- Check for hash collisions (multiple tasks with same hash)
SELECT hash(task_id::text) as task_hash, COUNT(*) as count
FROM tasks
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY task_hash
HAVING COUNT(*) > 1;
```

**Python Monitoring Script**:
```python
# tools/monitoring/check_task_id_anomalies.py
import re
from common.database import get_db_session

def check_task_id_anomalies():
    """Check for task ID format anomalies"""
    session = get_db_session()
    
    # Check for prefixed IDs
    prefixed = session.execute("""
        SELECT COUNT(*) FROM tasks 
        WHERE task_id LIKE 'task-%' 
        AND created_at > NOW() - INTERVAL '24 hours'
    """).scalar()
    
    if prefixed > 0:
        print(f"⚠️ WARNING: {prefixed} prefixed task IDs found!")
    
    # Check for invalid UUIDs
    invalid = session.execute("""
        SELECT COUNT(*) FROM tasks 
        WHERE task_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        AND created_at > NOW() - INTERVAL '24 hours'
    """).scalar()
    
    if invalid > 0:
        print(f"🚨 CRITICAL: {invalid} invalid task IDs found!")
    
    print("✅ Task ID validation complete")

if __name__ == "__main__":
    check_task_id_anomalies()
```

### 2.3 Alert Thresholds

| Anomaly Type | Warning | Critical | Action |
|--------------|---------|----------|--------|
| Prefixed IDs | > 0 | > 10/day | Investigate external tool integration |
| Invalid UUIDs | > 0 | > 5/day | Check API validation, review logs |
| Hash Collisions | > 0 | > 1/week | Review hash usage, consider alternatives |

---

## 3. Security Monitoring

### 3.1 Path Traversal Attack Detection

**Monitoring Points**:
1. `_is_safe_file_path()` rejections
2. Global deny list violations
3. Whitelist bypass attempts

**Log Patterns to Monitor**:
```python
# Warning logs from code_generation_workflow.py
"Blocked path outside allowed constraints"
"Path contains dangerous pattern"
"Cannot compute relative path"
```

**Query for Security Violations**:
```bash
# Check logs for path traversal attempts (last 24 hours)
grep "Blocked path outside allowed constraints" /var/log/morningai/orchestrator.log | tail -100

# Check for deny list violations
grep "Path contains dangerous pattern" /var/log/morningai/orchestrator.log | tail -50

# Count violations by hour
grep "Blocked path" /var/log/morningai/orchestrator.log | \
  awk '{print $1, $2}' | cut -d: -f1 | uniq -c
```

### 3.2 Safe Task Whitelist Violations

**Expected Behavior**: Only tasks in `SAFE_TASKS` should execute

**Monitoring**:
```python
# Check for unsafe task execution attempts
SELECT task_type, COUNT(*) as attempts
FROM task_execution_logs
WHERE status = 'rejected_unsafe'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY task_type
ORDER BY attempts DESC;
```

**Alert if**:
- Any task type not in `SAFE_TASKS` executes code generation
- Safe task whitelist is modified without approval
- Task classification produces unexpected types

### 3.3 Security Incident Response

**If path traversal detected**:
1. ✅ Verify block was successful (file not accessed)
2. ✅ Review task metadata and whitelist configuration
3. ✅ Check if legitimate use case or attack attempt
4. ✅ Update whitelist if needed, or escalate if attack

**If unsafe task executes**:
1. 🚨 IMMEDIATE: Stop task execution
2. 🚨 Review task classification logic
3. 🚨 Check if `SAFE_TASKS` was modified
4. 🚨 Audit recent code changes
5. 🚨 Rollback if necessary

---

## 4. Performance Monitoring

### 4.1 Task Duration Tracking

**Baseline Performance** (from testing):
- Documentation update: 2-4 minutes
- Test generation: 3-5 minutes
- Simple refactoring: 4-6 minutes

**Performance Degradation Indicators**:
```sql
-- Tasks taking longer than expected
SELECT task_id, task_type, duration_seconds
FROM task_execution_logs
WHERE duration_seconds > 600  -- 10 minutes
  AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY duration_seconds DESC;

-- Average duration by task type (last 7 days)
SELECT task_type, 
       AVG(duration_seconds) as avg_duration,
       MAX(duration_seconds) as max_duration,
       COUNT(*) as count
FROM task_execution_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY task_type;
```

### 4.2 Resource Utilization

**Monitor**:
- CPU usage during code generation
- Memory usage (LangGraph state size)
- Disk I/O (file operations)
- Network I/O (LLM API calls)

**Alert Thresholds**:
- CPU > 80% sustained for > 5 minutes
- Memory > 4GB per task
- Disk I/O > 100 MB/s sustained
- LLM API latency > 10 seconds

---

## 5. Error Monitoring

### 5.1 Common Error Patterns

**1. Task Classification Errors**
```python
# Log pattern
"[TaskClassifier] Classification failed"

# Monitoring query
SELECT error_message, COUNT(*) as occurrences
FROM error_logs
WHERE component = 'TaskClassifier'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY error_message;
```

**2. Code Generation Failures**
```python
# Log pattern
"[CodeGenerationWorkflow] Workflow execution failed"

# Common causes
- LLM API timeout
- Security validation failure
- File write permission denied
- Git operation failure
```

**3. PR Creation Failures**
```python
# Log pattern
"[CodeGenerationWorkflow] Failed to create PR"

# Common causes
- GitHub API rate limit
- Invalid branch name
- Merge conflict
- CI check failure
```

### 5.2 Error Rate Thresholds

| Error Type | Normal | Warning | Critical |
|------------|--------|---------|----------|
| Classification Errors | < 1% | > 5% | > 10% |
| Code Generation Failures | < 5% | > 15% | > 25% |
| PR Creation Failures | < 2% | > 10% | > 20% |
| Security Validation Failures | 0% | > 0% | > 1% |

---

## 6. Incident Response

### 6.1 Severity Levels

**P0 - Critical** (Immediate response required)
- Security breach or vulnerability exploited
- Data loss or corruption
- Complete service outage
- Unsafe task executed

**P1 - High** (Response within 1 hour)
- High error rate (> 25%)
- Performance degradation (> 2x baseline)
- Multiple security violations
- PR creation failures > 50%

**P2 - Medium** (Response within 4 hours)
- Moderate error rate (10-25%)
- Task duration increase (1.5-2x baseline)
- Occasional security violations
- Classification accuracy drop

**P3 - Low** (Response within 24 hours)
- Minor performance issues
- Low error rate (< 10%)
- Documentation needed
- Feature requests

### 6.2 Incident Response Procedures

**For Security Incidents (P0)**:
1. ✅ Immediately disable code generation (`enable_code_generation=False`)
2. ✅ Review recent task executions and file changes
3. ✅ Check for unauthorized access or data exfiltration
4. ✅ Notify security team and stakeholders
5. ✅ Preserve logs and evidence
6. ✅ Conduct root cause analysis
7. ✅ Implement fix and additional safeguards
8. ✅ Re-enable with enhanced monitoring

**For Performance Issues (P1-P2)**:
1. ✅ Check resource utilization (CPU, memory, disk)
2. ✅ Review recent code changes
3. ✅ Check LLM API latency and rate limits
4. ✅ Analyze slow queries and bottlenecks
5. ✅ Scale resources if needed
6. ✅ Optimize code if bottleneck identified

**For Error Rate Spikes (P1-P2)**:
1. ✅ Check error logs for patterns
2. ✅ Identify affected task types
3. ✅ Review recent deployments
4. ✅ Check external dependencies (GitHub API, LLM API)
5. ✅ Rollback if recent deployment caused issue
6. ✅ Fix root cause and redeploy

---

## 7. Daily Checklist

**Morning Check** (10 minutes):
- [ ] Review overnight task execution stats
- [ ] Check error rate (should be < 5%)
- [ ] Verify no security violations
- [ ] Check task ID anomalies (should be 0)
- [ ] Review performance metrics (duration, success rate)

**Commands**:
```bash
# Daily monitoring script
cd ~/repos/morningai
source .venv/bin/activate

# 1. Task execution stats
python tools/monitoring/view_planner_stats.py --days 1

# 2. Check for task ID anomalies
python tools/monitoring/check_task_id_anomalies.py

# 3. Review error logs
tail -100 /var/log/morningai/orchestrator.log | grep ERROR

# 4. Check security violations
grep "Blocked path" /var/log/morningai/orchestrator.log | tail -50

# 5. Performance check
python tools/monitoring/view_planner_stats.py --metric duration
```

**Evening Check** (5 minutes):
- [ ] Review day's task execution summary
- [ ] Check for any new error patterns
- [ ] Verify all PRs created successfully
- [ ] Review any alerts or warnings

---

## 8. Weekly Review

**Weekly Analysis** (30 minutes):
- [ ] Analyze task success rate trends
- [ ] Review task classification accuracy
- [ ] Check for performance degradation over time
- [ ] Review security violation patterns
- [ ] Analyze task type distribution
- [ ] Review error logs for recurring issues
- [ ] Update monitoring thresholds if needed

**Weekly Report Template**:
```markdown
# Phase 2 Weekly Monitoring Report

**Week of**: [Date Range]

## Summary
- Total tasks executed: [count]
- Success rate: [percentage]
- Average task duration: [minutes]
- Security violations: [count]
- Task ID anomalies: [count]

## Key Metrics
- Task classification accuracy: [percentage]
- PR creation success rate: [percentage]
- Error rate: [percentage]
- Performance vs baseline: [comparison]

## Issues Identified
1. [Issue description]
   - Severity: [P0/P1/P2/P3]
   - Status: [Open/In Progress/Resolved]
   - Action: [Description]

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Next Week Focus
- [Focus area 1]
- [Focus area 2]
```

---

## 9. Monitoring Tools

### 9.1 Existing Tools

**Planner Statistics CLI**:
```bash
# View planner statistics
python tools/monitoring/view_planner_stats.py

# Options:
--days N          # Show stats for last N days
--metric NAME     # Show specific metric (success_rate, duration, etc.)
--format json     # Output in JSON format
```

**Database Queries**:
```bash
# Connect to database
psql $DATABASE_URL

# Useful queries in tools/monitoring/queries.sql
```

### 9.2 Recommended New Tools

**Task ID Anomaly Checker** (to be created):
```bash
python tools/monitoring/check_task_id_anomalies.py
```

**Security Violation Monitor** (to be created):
```bash
python tools/monitoring/check_security_violations.py --days 1
```

**Performance Analyzer** (to be created):
```bash
python tools/monitoring/analyze_performance.py --baseline
```

---

## 10. Contact Information

**Escalation Path**:
1. **P3 (Low)**: Create GitHub issue, assign to team
2. **P2 (Medium)**: Notify team lead via Slack
3. **P1 (High)**: Page on-call engineer
4. **P0 (Critical)**: Page on-call + notify security team + notify CTO

**Key Contacts**:
- Engineering Team Lead: [Contact]
- Security Team: [Contact]
- DevOps/SRE: [Contact]
- CTO: Ryan Chen (@RC918)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-28 | Devin AI | Initial production monitoring guide |

---

**End of Document**
