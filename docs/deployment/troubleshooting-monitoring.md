# Monitoring Dashboard Troubleshooting Guide

**Last Updated**: 2025-11-04  
**Applies To**: Monitoring Dashboard v2 (`/api/phase7/monitoring/dashboard`)

---

## Overview

This guide provides troubleshooting steps for the MorningAI Monitoring Dashboard, focusing on 503 Service Unavailable errors and degradation scenarios.

---

## Quick Reference

### Endpoint Information

- **Primary Endpoint**: `/api/phase7/monitoring/dashboard`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Expected Responses**: 200 OK (normal/degraded) or 503 Service Unavailable (dual failure)

### Health Check Commands

```bash
# Production
curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard

# Staging
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard

# Local
curl http://localhost:8000/api/phase7/monitoring/dashboard
```

---

## Symptom: 503 Service Unavailable

### Response Payload

```json
{
  "error": "Core services unavailable",
  "message": "Both Redis and Database connections failed",
  "status": "service_unavailable",
  "request_id": "optional-trace-id"
}
```

### Root Cause

The monitoring dashboard returns 503 **only** when **both** Redis and Database are unavailable simultaneously. This is by design to indicate a critical infrastructure failure.

### Diagnostic Checklist

#### 1. Verify Redis Connectivity

```bash
# Check Redis connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"

# Expected: True

# Check Redis keys
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.keys('*'))"
```

**Common Issues**:
- ❌ `ConnectionError`: Redis server unreachable
- ❌ `AuthenticationError`: Invalid password in `REDIS_URL`
- ❌ `TimeoutError`: Network latency or firewall blocking

**Fixes**:
- Verify `REDIS_URL` format: `rediss://default:[PASSWORD]@[HOST]:6379` (note double `s` for TLS)
- Check Upstash dashboard for service status
- Verify firewall rules allow outbound connections to Upstash

#### 2. Verify Database Connectivity

```bash
# Check DB connection
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); conn = engine.connect(); print('Connected'); conn.close()"

# Expected: Connected

# Test query
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); conn = engine.connect(); result = conn.exec_driver_sql('SELECT 1'); print(result.fetchone()); conn.close()"
```

**Common Issues**:
- ❌ `OperationalError`: Database server unreachable
- ❌ `ProgrammingError`: Invalid credentials
- ❌ `TimeoutError`: Connection pool exhausted

**Fixes**:
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:6543/postgres`
- Check Supabase dashboard for project status (not paused)
- Verify connection pooler is enabled (port 6543)
- Check connection pool settings: `DB_POOL_SIZE`, `DB_POOL_MAX_OVERFLOW`

#### 3. Check Application Logs

```bash
# Render logs (production/staging)
# Go to: https://dashboard.render.com/ → Select service → Logs tab

# Look for:
# - "Both Redis and Database are unavailable" (ERROR level)
# - "Failed to get Redis queue stats" (WARNING level)
# - "Database connection failed" (ERROR level)

# Local logs
# Check terminal output where backend is running
```

#### 4. Verify Environment Variables

```bash
# Check required environment variables
echo $REDIS_URL
echo $DATABASE_URL
echo $BACKEND_SERVICES_AVAILABLE

# All should be set and non-empty
```

### Recovery Steps

#### Immediate Recovery (Production)

1. **Check Service Status**:
   - Upstash Redis: https://console.upstash.com/
   - Supabase DB: https://supabase.com/dashboard/

2. **Restart Backend Service** (if needed):
   - Render Dashboard → Select service → Manual Deploy → Deploy latest commit

3. **Monitor Recovery**:
   ```bash
   # Watch for 200 OK response
   watch -n 5 'curl -s https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq .system_health.overall_status'
   ```

#### Long-term Prevention

1. **Set up monitoring alerts** for Redis and DB connectivity
2. **Configure connection retries** with exponential backoff
3. **Implement circuit breakers** for external dependencies
4. **Add health check probes** to detect issues early

---

## Symptom: 200 OK with Degraded Status

### Response Payload

```json
{
  "system_health": {
    "overall_status": "degraded",
    ...
  },
  "alerts": [
    {
      "id": "db_error",
      "severity": "critical",
      "message": "Database connection failed",
      "timestamp": "2025-11-04T16:45:58.648953"
    }
  ]
}
```

### Root Cause

Database is unavailable, but Redis is still functioning. The dashboard returns degraded status with an alert.

### Diagnostic Steps

1. **Check Database Connectivity** (see section above)
2. **Verify Redis is Working**:
   ```bash
   curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq '.metrics.queue_depth'
   
   # Should show real queue depth, not fallback
   ```

3. **Check Alert Details**:
   ```bash
   curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq '.alerts'
   ```

### Recovery Steps

1. **Restore Database Connection** (see Database Connectivity section)
2. **Verify Recovery**:
   ```bash
   curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq '.system_health.overall_status'
   
   # Expected: "healthy"
   ```

---

## Symptom: 200 OK with Fallback Metrics

### Response Payload

```json
{
  "metrics": {
    "queue_depth": {
      "current": 0,
      "unit": "tasks",
      "trend": "unknown",
      "available": false,
      "source": "fallback",
      "error": "Redis unavailable"
    }
  },
  "alerts": [
    {
      "id": "redis_error",
      "severity": "warning",
      "message": "Redis connection unavailable",
      "timestamp": "2025-11-04T16:45:58.648953"
    }
  ]
}
```

### Root Cause

Redis is unavailable, but Database is still functioning. The dashboard returns fallback metrics with explicit markers.

### Diagnostic Steps

1. **Check Redis Connectivity** (see section above)
2. **Verify Database is Working**:
   ```bash
   curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq '.system_health.overall_status'
   
   # Should show "healthy" (not "degraded")
   ```

3. **Check Fallback Markers**:
   ```bash
   curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq '.metrics.queue_depth'
   
   # Should show: available=false, source="fallback", error="Redis unavailable"
   ```

### Recovery Steps

1. **Restore Redis Connection** (see Redis Connectivity section)
2. **Verify Recovery**:
   ```bash
   curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard | jq '.metrics.queue_depth.available'
   
   # Expected: true (or field not present)
   ```

---

## Testing & Reproduction

### Local Testing (Development Only)

**Simulate Redis Failure**:
```python
# In test environment only
from unittest.mock import patch

with patch('src.utils.redis_client.get_redis_client') as mock_redis:
    mock_redis.side_effect = Exception("Redis connection failed")
    # Make request to /api/phase7/monitoring/dashboard
    # Expected: 200 OK with fallback metrics
```

**Simulate DB Failure**:
```python
# In test environment only
from unittest.mock import patch

with patch('src.routes.dashboard.check_db_health') as mock_db:
    mock_db.return_value = (False, "Database connection failed")
    # Make request to /api/phase7/monitoring/dashboard
    # Expected: 200 OK with degraded status
```

**Simulate Dual Failure**:
```python
# In test environment only
from unittest.mock import patch

with patch('src.utils.redis_client.get_redis_client') as mock_redis, \
     patch('src.routes.dashboard.check_db_health') as mock_db:
    mock_redis.side_effect = Exception("Redis connection failed")
    mock_db.return_value = (False, "Database connection failed")
    # Make request to /api/phase7/monitoring/dashboard
    # Expected: 503 Service Unavailable
```

### Integration Tests

Run the integration test suite:
```bash
cd handoff/20250928/40_App/api-backend
pytest tests/test_dashboard_503_integration.py -v

# Expected: 2 passed
# - test_dual_failure_returns_503_with_health_seam
# - test_db_failure_only_returns_200_degraded
```

---

## Code References

### Backend Implementation

- **Main Route**: `handoff/20250928/40_App/api-backend/src/main.py:574`
  - Function: `get_monitoring_dashboard()`
  - Registers public endpoint

- **Core Logic**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:35`
  - Function: `get_dashboard_data()`
  - Implements degradation semantics

- **DB Health Check**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:17`
  - Function: `check_db_health()`
  - Test seam for mocking DB failures

### Tests

- **Integration Tests**: `handoff/20250928/40_App/api-backend/tests/test_dashboard_503_integration.py`
  - `test_dual_failure_returns_503_with_health_seam`: Verifies 503 response
  - `test_db_failure_only_returns_200_degraded`: Verifies degraded status

### API Contract

- **OpenAPI Schema**: `handoff/20250928/40_App/owner-console/src/lib/openapi.yaml`
  - ServiceUnavailableError schema (lines 506-525)
  - Monitoring endpoint definition (lines 168-254)

---

## Environment Variables

### Required Variables

- `REDIS_URL`: Redis connection string
  - Format: `rediss://default:[PASSWORD]@[HOST]:6379`
  - Used for: Queue metrics

- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://user:pass@host:6543/postgres`
  - Used for: Health checks

- `BACKEND_SERVICES_AVAILABLE`: Gate flag
  - Set by: `src/main.py` during startup
  - Used for: Service availability checks

- `MORNINGAI_REPO_PATH`: Repository root path (Added PR #1398)
  - Format: `/opt/render/project/src` (Render.com production)
  - Used for: Context manager file discovery
  - Fallback: Git detection → marker-based discovery
  - Path: `handoff/20250928/40_App/orchestrator/context_manager.py`

### Optional Variables

- `DB_POOL_SIZE`: Connection pool size (default: 5)
- `DB_POOL_MAX_OVERFLOW`: Max overflow connections (default: 10)
- `DB_POOL_RECYCLE`: Connection recycle time in seconds (default: 3600)
- `DB_POOL_PRE_PING`: Enable connection health checks (default: true)

See [Environment Variables Schema](../../config/env.schema.yaml) for complete list.

### CI/CD Environment Variables (PR #1399)

Backend test workflows now require:
- **Python Version**: 3.12 (unified across backend.yml and test-apps.yml)
- **Redis Service**: Required for backend tests
  - Image: `redis:7-alpine`
  - Port: 6379
  - Health check: `redis-cli ping`
- **PyJWT Conflict Resolution**: `pip uninstall -y jwt` before installing dependencies

---

## Related Documentation

- **[ONBOARDING_GUIDE.md](../ONBOARDING_GUIDE.md)** - Observability & Monitoring section
- **[ENVIRONMENTS.md](../ENVIRONMENTS.md)** - Monitoring Dashboard Endpoints section
- **[PROJECT_STRUCTURE_REPORT.md](../PROJECT_STRUCTURE_REPORT.md)** - Monitoring API Surface section
- **[VERCEL_DEPLOYMENT_STRATEGY.md](./VERCEL_DEPLOYMENT_STRATEGY.md)** - Smoke test checklist

---

## Support

For additional support:
- **GitHub Issues**: https://github.com/RC918/morningai/issues
- **Team Lead**: Ryan Chen (@RC918)
- **Email**: ryan2939z@gmail.com

---

## Recent Updates (Nov 18-21, 2025)

### PR #1350: E2E Testing Infrastructure
- **Path**: `handoff/20250928/40_App/owner-console/e2e/`
- **Tests**: 32 Playwright tests passing (11→32)
- **Key Fixes**: Route handler isolation, API mocking, VITE_E2E security gate
- **CI**: 55/55 checks passing

### PR #1398: Production Path Discovery
- **Path**: `handoff/20250928/40_App/orchestrator/context_manager.py`
- **Change**: Replaced hardcoded `~/repos/morningai` with `MORNINGAI_REPO_PATH` env var
- **Fallback**: 4-layer mechanism (env var → git → marker-based → error)
- **CI**: 40/40 checks passing

### PR #1399: Backend Test Environment Alignment
- **Path**: `.github/workflows/test-apps.yml`
- **Changes**: Python 3.12, Redis service, PyJWT conflict resolution
- **Result**: Unified backend.yml and test-apps.yml configurations
- **CI**: 33/33 checks passing

---

**Maintained By**: CTO / DevOps Team  
**Version**: 1.1.0  
**Last Updated**: 2025-11-21
