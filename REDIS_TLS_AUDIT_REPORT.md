# Redis TLS Security Audit Report

**Date**: 2025-10-23  
**Priority**: P1 (Critical Security Issue)  
**Status**: In Progress

## Executive Summary

Current Redis configuration has **insecure fallbacks** to `redis://localhost:6379` in multiple locations. While the main `redis_client.py` supports TLS, many other components still use non-TLS connections.

## Audit Findings

### ✅ Secure Components

1. **`handoff/20250928/40_App/api-backend/src/utils/redis_client.py`**
   - ✅ Supports Upstash Redis (HTTPS)
   - ✅ Supports `rediss://` (TLS)
   - ✅ Logs warning for non-TLS connections
   - ⚠️ Still allows non-TLS fallback

### ❌ Insecure Components (Require Fixes)

#### Production Code

1. **`handoff/20250928/40_App/orchestrator/redis_queue/worker.py:83`**
   ```python
   redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
   ```
   - **Risk**: High - Production worker uses insecure fallback
   - **Fix**: Remove fallback, require TLS configuration

2. **`handoff/20250928/40_App/orchestrator/governance/cost_tracker.py:27`**
   ```python
   self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
   ```
   - **Risk**: High - Cost tracking uses insecure fallback
   - **Fix**: Remove fallback, require TLS configuration

3. **`handoff/20250928/40_App/orchestrator/api/main.py:46`**
   ```python
   redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
   ```
   - **Risk**: High - API server uses insecure fallback
   - **Fix**: Remove fallback, require TLS configuration

4. **`agents/ops_agent/worker.py:70`**
   ```python
   self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
   ```
   - **Risk**: High - Ops agent uses insecure fallback
   - **Fix**: Remove fallback, require TLS configuration

5. **`orchestrator/integrations/ops_agent_client.py:257`**
   ```python
   async def start_ops_agent_client(redis_url: str = "redis://localhost:6379"):
   ```
   - **Risk**: Medium - Default parameter uses insecure connection
   - **Fix**: Remove default, require explicit configuration

6. **`meta_agent_decision_hub.py:432`**
   ```python
   def __init__(self, redis_url: str = "redis://localhost:6379", db_url: str = None):
   ```
   - **Risk**: Medium - Default parameter uses insecure connection
   - **Fix**: Remove default, require explicit configuration

#### CI/CD Configuration

7. **`.github/workflows/test-agents.yml`** (3 occurrences)
   ```yaml
   REDIS_URL: redis://localhost:6379/0
   ```
   - **Risk**: Low - Test environment only
   - **Fix**: Keep for local testing, but document as test-only

8. **`.github/workflows/test-apps.yml`** (2 occurrences)
   ```yaml
   REDIS_URL: redis://localhost:6379/0
   ```
   - **Risk**: Low - Test environment only
   - **Fix**: Keep for local testing, but document as test-only

9. **`.github/workflows/backend.yml:80`**
   ```yaml
   REDIS_URL: redis://localhost:6379/0
   ```
   - **Risk**: Low - Test environment only
   - **Fix**: Keep for local testing, but document as test-only

#### Configuration Files

10. **`config/env.schema.yaml:53`**
    ```yaml
    default: redis://localhost:6379/0
    ```
    - **Risk**: High - Schema default is insecure
    - **Fix**: Remove default or change to `rediss://` example

11. **`.env.example:128`**
    ```yaml
    REDIS_URL=redis://localhost:6379/0
    ```
    - **Risk**: Medium - Example file shows insecure configuration
    - **Fix**: Change to `rediss://` example with comment

12. **`orchestrator/.env.example:20`**
    ```yaml
    REDIS_URL=redis://localhost:6379/0
    ```
    - **Risk**: Medium - Example file shows insecure configuration
    - **Fix**: Change to `rediss://` example with comment

#### Test Files (Lower Priority)

13. **Test files** (12+ occurrences)
    - `test_redis_performance.py`
    - `test_env_schema_validator.py`
    - `test_rq_worker.py`
    - `test_worker_heartbeat.py`
    - etc.
    - **Risk**: Low - Test environment only
    - **Fix**: Keep for local testing, add comments

## Recommended Actions

### Phase 1: Production Code (Immediate - Day 1)

1. **Remove insecure fallbacks in production code**:
   - `orchestrator/redis_queue/worker.py`
   - `orchestrator/governance/cost_tracker.py`
   - `orchestrator/api/main.py`
   - `agents/ops_agent/worker.py`
   - `orchestrator/integrations/ops_agent_client.py`
   - `meta_agent_decision_hub.py`

2. **Update configuration schemas**:
   - `config/env.schema.yaml`
   - `.env.example`
   - `orchestrator/.env.example`

### Phase 2: Documentation (Day 1-2)

1. **Update documentation**:
   - Add Redis TLS setup guide
   - Update deployment documentation
   - Add security best practices

2. **Update CI/CD documentation**:
   - Document that CI uses local Redis for testing
   - Add production Redis setup instructions

### Phase 3: Validation (Day 2)

1. **Add validation**:
   - Create script to verify all Redis connections use TLS
   - Add pre-commit hook to prevent insecure Redis URLs
   - Update CI to check for insecure Redis configurations

## Implementation Plan

### Step 1: Create Helper Function

```python
# utils/redis_config.py
def get_secure_redis_url() -> str:
    """
    Get Redis URL with TLS enforcement.
    Raises ValueError if no secure Redis configuration found.
    """
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    if upstash_url:
        return upstash_url
    
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        if not redis_url.startswith("rediss://") and not redis_url.startswith("redis://localhost"):
            raise ValueError(
                "❌ REDIS_URL must use TLS (rediss://) for production. "
                "Use redis://localhost only for local development."
            )
        return redis_url
    
    raise ValueError(
        "❌ No Redis configuration found. "
        "Set UPSTASH_REDIS_REST_URL or REDIS_URL environment variable."
    )
```

### Step 2: Replace All Insecure Fallbacks

Replace:
```python
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

With:
```python
from utils.redis_config import get_secure_redis_url
redis_url = get_secure_redis_url()
```

### Step 3: Update Configuration Files

`.env.example`:
```bash
# Redis Configuration (Production - REQUIRED)
# Use Upstash Redis (recommended) or Redis Cloud with TLS
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token

# OR use Redis with TLS
REDIS_URL=rediss://your-redis-host:6380/0

# Local development only (NOT for production)
# REDIS_URL=redis://localhost:6379/0
```

## Success Criteria

- [ ] All production code uses TLS or Upstash Redis
- [ ] No insecure fallbacks in production code
- [ ] Configuration examples show secure setup
- [ ] Documentation updated
- [ ] Validation script created
- [ ] CI checks for insecure Redis URLs
- [ ] PR created and reviewed
- [ ] All tests pass

## Timeline

- **Day 1 Morning**: Phase 1 (Production code fixes)
- **Day 1 Afternoon**: Phase 2 (Documentation)
- **Day 2 Morning**: Phase 3 (Validation)
- **Day 2 Afternoon**: PR review and merge

## Related PRs

- PR #695: Enable Redis TLS with Upstash (HTTPS) - Security Enhancement
- PR #720: P5: Add Independent CI Jobs for Agent and App Tests (merged)

---

**Next Steps**: Begin Phase 1 implementation
