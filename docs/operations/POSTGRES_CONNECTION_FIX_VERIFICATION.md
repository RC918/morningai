# PostgreSQL Connection Lifecycle Fix Verification

## Date: December 26, 2025

## PR Reference
- PR #2972: fix(orchestrator): decouple rate limiter + fix PostgreSQL connection lifecycle (#2969)

## Problem Statement

Production Sentry errors showed PostgreSQL connection failures during long workflows (~2 minutes):
- "the connection is closed" (12 events, Escalating)
- "SSL connection has been closed unexpectedly" (5 events)
- "psycopg.Pipeline [BAD]" state
- "prepared statement _pg3_1 does not exist" (4 events)

## Root Cause

The previous implementation held a single pooled connection for the entire `app.invoke()` duration (~2 minutes). Any network hiccup or Supabase reset killed the connection with no recovery.

```python
# OLD (Vulnerable)
with pool.connection() as conn:
    checkpointer = PostgresSaver(conn)
    app.invoke(...)  # Holds connection for ~2 minutes
```

## Fix Applied

Changed to per-operation connection borrowing:

```python
# NEW (Resilient)
checkpointer = PostgresSaver(pool)  # Pass pool, not connection
app.invoke(...)
# Each checkpoint operation borrows connection briefly from pool
```

Key changes:
1. `prepare_threshold=0` - Disables prepared statements to avoid "prepared statement does not exist" errors
2. `PostgresSaver(pool)` - Each checkpoint operation borrows connection briefly
3. New `get_postgres_checkpointer()` function replaces context manager approach

## Verification Checklist

- [ ] Staging deployment successful
- [ ] Worker logs show "PostgreSQL checkpointer initialized with per-operation connection borrowing"
- [ ] No "Pipeline [BAD]" errors in logs
- [ ] No "SSL connection closed" errors in logs
- [ ] Workflow completes successfully
- [ ] Sentry error count decreases over 24 hours

## Blueprint Alignment

- **Design for Failure**: Connection can die without killing entire workflow
- **Safety Governor v2**: Graceful degradation under network instability

## Related Issues

- Issue #2968: ResilientPostgresSaver (long-term retry/reconnect logic)
- Issue #2969: Rate Limiter decoupling
- Issue #2973: Concurrent webhook tests
- Issue #2974: Fault injection tests
