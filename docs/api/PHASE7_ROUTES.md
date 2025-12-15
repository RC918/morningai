# Phase 7 API Routes Documentation

## Overview

Phase 7 routes provide APIs for Performance, Growth & Beta Introduction features. These routes were extracted from `main.py` to `src/routes/phase7.py` as part of Phase 1.6 route modularization (PR1.6b).

## Directory Structure

```
src/routes/
├── __init__.py           # Blueprint registration (includes phase7)
├── phase7.py             # Phase 7 API routes (11 endpoints)
├── phase456.py           # Phase 4-6 API routes (18 endpoints)
├── dashboard.py          # Dashboard routes (includes monitoring dashboard handler)
└── ...                   # Other route modules
```

## Route List

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/phase7/status` | GET | Phase 7 system status and configuration | No |
| `/api/phase7/approvals/pending` | GET | Get pending HITL approval requests | No |
| `/api/phase7/approvals/history` | GET | Get HITL approval history | No |
| `/api/phase7/beta/candidates` | GET | Get Beta program candidates | No |
| `/api/phase7/growth/metrics` | GET | Get growth strategy metrics | No |
| `/api/phase7/ops/metrics` | GET | Get operations performance metrics | No |
| `/api/phase7/monitoring/dashboard` | GET | Get monitoring dashboard data | No |
| `/api/phase7/monitoring/metrics` | GET | Get resilience pattern metrics | No |
| `/api/phase7/monitoring/alerts` | GET | Get current monitoring alerts | No |
| `/api/phase7/environment/validate` | GET, POST | Validate environment configuration | No |
| `/api/phase7/resilience/metrics` | GET | Get Phase 7 resilience metrics | No |

## Query Parameters

### `/api/phase7/approvals/history`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Maximum number of history records to return |

## Route Grouping Strategy

Phase 7 routes are grouped by functional area:

1. **System Status** (`/api/phase7/status`)
   - Overall Phase 7 system status and component configuration

2. **HITL Approvals** (`/api/phase7/approvals/*`)
   - Human-in-the-loop approval system
   - Pending requests and approval history

3. **Beta Program** (`/api/phase7/beta/*`)
   - Beta program candidate management

4. **Growth Metrics** (`/api/phase7/growth/*`)
   - Growth strategy metrics and reports

5. **Operations** (`/api/phase7/ops/*`)
   - Operations performance metrics

6. **Monitoring** (`/api/phase7/monitoring/*`)
   - Dashboard data, resilience metrics, and alerts

7. **Environment** (`/api/phase7/environment/*`)
   - Environment configuration validation

8. **Resilience** (`/api/phase7/resilience/*`)
   - Circuit breakers, retry patterns, bulkhead isolation

## Versioning Strategy

Currently, Phase 7 routes use the `/api/phase7/` prefix without explicit versioning. This follows the existing pattern in the codebase where phase-specific routes use phase numbers as implicit versions.

**Current Pattern:**
```
/api/phase7/monitoring/dashboard
/api/phase4/security/reviews
```

**Future Consideration:**
For API versioning, consider migrating to explicit version prefixes:
```
/api/v1/phase7/monitoring/dashboard
```

This would allow breaking changes to be introduced in `/api/v2/` while maintaining backward compatibility.

## `/api/phase7/monitoring/dashboard` Fallback Behavior

### Handler Delegation

The `/api/phase7/monitoring/dashboard` endpoint delegates to `src.routes.dashboard.get_dashboard_data()` to maintain the expected response schema and failure behavior. This is intentional to preserve backward compatibility with existing tests and consumers.

### Failure Matrix

| Redis Status | DB Status | HTTP Status | Response |
|--------------|-----------|-------------|----------|
| Available | Available | 200 | Full dashboard data with `metrics`, `system_health`, `agents`, `alerts` |
| Available | Failed | 200 | Degraded status with `db_error` alert |
| Failed | Available | 200 | Fallback `queue_depth` with `source: "fallback"` |
| Failed | Failed | 503 | `{"error": "Core services unavailable", "message": "Both Redis and Database connections failed", "status": "service_unavailable"}` |

### Response Schema (Success)

```json
{
  "system_health": {
    "overall_status": "healthy|degraded",
    "error_rate": 0.01,
    "avg_latency": 0.15,
    "open_circuit_breakers": 0
  },
  "metrics": {
    "api_request_rate": {"current": 0, "unit": "req/min", "trend": "stable"},
    "agent_task_success_rate": {"current": 0.95, "unit": "%", "trend": "stable"},
    "queue_depth": {"current": 0, "unit": "tasks", "trend": "stable"},
    "active_agents": {"current": 0, "unit": "agents", "trend": "stable"}
  },
  "agents": [...],
  "alerts": [...]
}
```

### Response Schema (Redis Fallback)

When Redis is unavailable, `queue_depth` includes fallback indicators:

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
  }
}
```

### Response Schema (503 Dual Failure)

```json
{
  "error": "Core services unavailable",
  "message": "Both Redis and Database connections failed",
  "status": "service_unavailable"
}
```

## Rate Limiting

Phase 7 routes do not have explicit rate limiting decorators. They inherit the global rate limiting behavior if configured:

- **Default**: 60 requests per 60 seconds per IP
- **Configuration**: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`
- **Behavior**: If Redis is unavailable, rate limiting is bypassed (graceful degradation)

To apply rate limiting to specific Phase 7 endpoints, add the `@rate_limit` decorator:

```python
from src.middleware.rate_limit import rate_limit

@bp.route("/api/phase7/status")
@rate_limit
def phase7_status():
    ...
```

## Error Handling

All Phase 7 routes follow a consistent error response pattern:

```json
{
  "error": "Error message describing what went wrong"
}
```

HTTP status codes:
- `200`: Success
- `500`: Internal server error (service unavailable, import error, etc.)
- `503`: Service unavailable (dual Redis + DB failure for `/monitoring/dashboard`)

## Runtime Import Pattern

Phase 7 routes use runtime imports via helper functions to support test patching:

```python
def _get_backend_services_available():
    """Check if backend services are available at runtime."""
    import src.main
    return src.main.BACKEND_SERVICES_AVAILABLE
```

This pattern allows tests to patch `src.main.BACKEND_SERVICES_AVAILABLE` without module-level import issues.

## Testing

### Contract Tests

```bash
# Import contract tests (19 tests)
pytest handoff/20250928/40_App/api-backend/tests/test_import_contract.py -v

# Route-map tests (9 tests, 184 routes)
pytest handoff/20250928/40_App/api-backend/tests/test_route_map.py -v
```

### Dashboard Degradation Tests

```bash
# Dashboard 503 integration tests
pytest handoff/20250928/40_App/api-backend/tests/test_dashboard_503_integration.py -v

# Dashboard degradation path tests
pytest handoff/20250928/40_App/api-backend/tests/test_dashboard_degradation.py -v
```

### Phase 7 Endpoint Tests

```bash
# Phase 7 endpoint tests
pytest handoff/20250928/40_App/api-backend/tests/test_phase7_endpoints.py -v
```

## Related Documentation

- [Phase 1 Implementation Plan](../phase-implementation/PHASE_1_IMPLEMENTATION_PLAN.md)
- [Rate Limiting Verification Guide](../RATE_LIMITING_VERIFICATION_GUIDE.md)
- [Database Initialization](../database/DATABASE_INITIALIZATION.md)
