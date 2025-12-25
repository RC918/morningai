# PostgreSQL Connection Fix - Production Verification

## Date: December 26, 2025

## Context

This PR verifies that PR #2972 (PostgreSQL connection lifecycle fix) is properly deployed to production.

## Deployment Timeline

| Time (UTC+8) | Event |
|--------------|-------|
| Dec 25, 10:17 PM | Production worker at `f81e4a5` (without fix) |
| Dec 26, 2:52 AM | Manual deploy triggered for `d62ec24` |
| Dec 26, 2:54 AM | Production worker live with `d62ec24` (with fix) |

## Expected Behavior

After this PR triggers the webhook, the production worker logs should show:
- `"PostgreSQL checkpointer initialized with per-operation connection borrowing"`

## Verification Checklist

- [ ] Worker logs show per-operation connection borrowing initialization
- [ ] No new `Pipeline [BAD]` errors in Sentry
- [ ] No new `SSL connection has been closed unexpectedly` errors
- [ ] Workflow completes successfully (Job OK with success=True)

## Fix Details

PR #2972 changed the PostgreSQL checkpointer from holding a single connection for the entire workflow (~2 minutes) to per-operation connection borrowing, where each checkpoint operation briefly borrows a connection from the pool.

This prevents connection timeout issues during long-running workflows.
