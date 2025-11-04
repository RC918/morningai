# Orchestrator Rate Limiting and Test Mode

## Overview

This document describes the rate limiting and test mode features added to prevent orchestrator PR explosion incidents.

## Problem

On 2025-10-19, the orchestrator created 30 test PRs in 18 minutes (PR #390-#419) due to:
1. Default test mode being `true` instead of `false`
2. Auto-merge being attempted on draft PRs
3. No rate limiting to prevent runaway PR creation

## Solution

### 1. Fixed Default Test Mode

**Before:**
```python
is_test_mode = os.getenv("ORCHESTRATOR_TEST_MODE", "true").lower() == "true"
```

**After:**
```python
is_test_mode = os.getenv("ORCHESTRATOR_TEST_MODE", "false").lower() == "true"
```

**Impact:**
- Production environments no longer default to test mode
- Test mode must be explicitly enabled via `ORCHESTRATOR_TEST_MODE=true`
- Prevents accidental test PR creation in production

### 2. Conditional Auto-Merge

**Before:**
```python
# Always tried to enable auto-merge, even for draft PRs
subprocess.run(["gh", "pr", "merge", str(pr_num), "--auto", "--squash"])
```

**After:**
```python
if not is_test_mode:
    # Only enable auto-merge for production PRs
    subprocess.run(["gh", "pr", "merge", str(pr_num), "--auto", "--squash"])
else:
    print(f"[Test Mode] Skipping auto-merge for draft PR")
```

**Impact:**
- Draft PRs (test mode) skip auto-merge entirely
- Eliminates meaningless auto-merge attempts on draft PRs
- Clearer logging for test vs production behavior

### 3. Rate Limiting

**New Feature:** `utils/rate_limit.py`

```python
from utils.rate_limit import check_pr_rate_limit

allowed, count = check_pr_rate_limit(
    trace_id, 
    max_per_hour=10, 
    redis_url=os.getenv("REDIS_URL")
)

if not allowed:
    print(f"[Rate Limit] BLOCKED - Already created {count} PRs this hour")
    return None, "rate_limited", trace_id
```

**Features:**
- Limits PR creation to 10 per hour (configurable)
- Uses Redis for distributed rate limiting
- Falls back gracefully if Redis is unavailable
- Returns current count for monitoring

**Impact:**
- Prevents runaway PR creation
- Maximum 10 PRs per hour even if orchestrator malfunctions
- Protection against CI/webhook loops

## Configuration

### Production Environment (Render)

Added to `render.yaml`:
```yaml
- key: ORCHESTRATOR_TEST_MODE
  value: false  # Explicit production mode
```

### Test/CI Environments

Set in GitHub Actions or local `.env`:
```bash
ORCHESTRATOR_TEST_MODE=true  # Enable test mode
```

### Rate Limit Configuration

Default: 10 PRs per hour

To customize, modify the call in `graph.py`:
```python
check_pr_rate_limit(trace_id, max_per_hour=20)  # Increase to 20
```

## Usage

### Production Mode (Default)

```bash
# No environment variable needed
python graph.py --goal "Update FAQ"
```

Creates:
- ✅ Regular PR (not draft)
- ✅ Auto-merge enabled
- ✅ Label: `orchestrator`
- ✅ Rate limited to 10/hour

### Test Mode

```bash
export ORCHESTRATOR_TEST_MODE=true
python graph.py --goal "Test FAQ update"
```

Creates:
- ✅ Draft PR
- ✅ Auto-merge skipped
- ✅ Labels: `automated-test`, `orchestrator`
- ✅ Auto-cleanup after CI
- ✅ Rate limited to 10/hour

## Monitoring

### Check Current Rate Limit

```python
from utils.rate_limit import get_pr_count_last_hour

count = get_pr_count_last_hour(redis_url=os.getenv("REDIS_URL"))
print(f"PRs created this hour: {count}")
```

### Sentry Integration

Add to your Sentry configuration to monitor rate limiting:

```python
import sentry_sdk
from utils.rate_limit import get_pr_count_last_hour

count = get_pr_count_last_hour()
if count > 5:
    sentry_sdk.capture_message(
        f"Orchestrator created {count} PRs in the last hour",
        level="warning"
    )
```

## Testing

### Unit Tests

```bash
cd handoff/20250928/40_App/orchestrator
pytest tests/test_rate_limit.py -v
```

### Integration Test

```bash
# Set test mode
export ORCHESTRATOR_TEST_MODE=true
export REDIS_URL=redis://localhost:6379

# Create 11 PRs rapidly (11th should be blocked)
for i in {1..11}; do
    python graph.py --goal "Test $i"
done

# Expected: First 10 succeed, 11th blocked by rate limit
```

## Troubleshooting

### Problem: PRs still being created in test mode

**Check:**
```bash
echo $ORCHESTRATOR_TEST_MODE  # Should be "true"
```

**Fix:**
```bash
export ORCHESTRATOR_TEST_MODE=true
```

### Problem: Rate limit not working

**Check Redis connection:**
```bash
redis-cli ping  # Should return "PONG"
```

**Check environment variable:**
```bash
echo $REDIS_URL  # Should be set
```

**Check logs:**
```
[Rate Limit] PR count this hour: X/10  # Normal
[Rate Limit] Redis unavailable, allowing PR creation  # Redis down
```

### Problem: Rate limit too aggressive

**Temporary bypass** (emergency only):
```python
# In graph.py, comment out rate limit check
# allowed, count = check_pr_rate_limit(...)
# if not allowed:
#     return None, "rate_limited", trace_id
```

**Permanent fix:**
```python
# Increase limit
check_pr_rate_limit(trace_id, max_per_hour=20)
```

## Architecture

### Rate Limit Storage

```
Redis Key: orchestrator:pr_count:{hour_timestamp}
Value: integer (count of PRs created)
TTL: 3600 seconds (1 hour)
```

Example:
```
orchestrator:pr_count:489133  →  5  (expires in 45 minutes)
orchestrator:pr_count:489134  →  2  (expires in 1 hour 45 minutes)
```

### Flow Diagram

```
execute() called
    ↓
check_pr_rate_limit()
    ↓
Redis: INCR orchestrator:pr_count:{hour}
    ↓
    ├─ count <= 10 → ✅ Allow PR creation
    └─ count > 10  → ❌ Block PR creation
         ↓
    Return (allowed=False, count=11)
         ↓
    Log: "[Rate Limit] BLOCKED"
         ↓
    Return (None, "rate_limited", trace_id)
```

## Migration Guide

### From Old Orchestrator (No Rate Limiting)

1. **Update code:**
   ```bash
   git pull origin main
   ```

2. **Set environment variable:**
   ```bash
   # Production (Render)
   # Already set in render.yaml

   # Local development
   echo "ORCHESTRATOR_TEST_MODE=true" >> .env
   ```

3. **Deploy:**
   ```bash
   git push origin main
   ```

4. **Verify:**
   ```bash
   # Check logs for rate limit messages
   [Rate Limit] PR count this hour: 1/10
   ```

## Related Issues

- **PR #360**: Initial draft PR support and auto-cleanup
- **PR #387**: Comprehensive error handling improvements
- **Incident 2025-10-19**: 30 test PRs created in 18 minutes
- **This PR**: Complete fix with rate limiting

## References

- Analysis Report: `/home/ubuntu/ORCHESTRATOR_EXPLOSION_ANALYSIS_REPORT.md`
- Rate Limit Implementation: `handoff/20250928/40_App/orchestrator/utils/rate_limit.py`
- Graph Updates: `handoff/20250928/40_App/orchestrator/graph.py`
- Production Config: `render.yaml`
