# Render Manual Deployment SOP

> **Version**: v0.2 (2025-12-24)
> **Status**: Active - All Render deployments are now manual
> **Owner**: @RC918 (Ryan Chen)
> **Related**: PR #2897, Issue #2901
> **Review Cadence**: Quarterly or after major infrastructure changes

## Overview

As of 2025-12-24, automatic deployments (autoDeploy) have been disabled for all Render services to address bandwidth/pipeline cost concerns. All production deployments must now be triggered manually.

## Services Requiring Manual Deploy

| Service | Render Dashboard Link | Purpose |
|---------|----------------------|---------|
| braintrust-processor | [Dashboard](https://dashboard.render.com/web/srv-xxx) | Braintrust integration |
| morningai-orchestrator-api | [Dashboard](https://dashboard.render.com/web/srv-xxx) | Main orchestrator API |
| morningai-worker-dashboard | [Dashboard](https://dashboard.render.com/web/srv-xxx) | Worker dashboard UI |
| morningai-ops-agent-worker | [Dashboard](https://dashboard.render.com/web/srv-xxx) | Ops agent worker |

> **IMPORTANT**: The `srv-xxx` values are placeholders. You MUST replace them with actual service IDs from Render Dashboard before using these links. Navigate via: Render Dashboard → Services → Select service name.

## Pre-Deployment Checklist

Before triggering a deployment:

- [ ] CI passes on `main` branch (check [GitHub Actions](https://github.com/RC918/morningai/actions))
- [ ] No blocking issues or incidents in progress
- [ ] Team notified in Slack/Discord (if applicable)
- [ ] Confirm which services need deployment (not all changes affect all services)
- [ ] Verify Render Dashboard links in this document are correct (or navigate manually)

## Deployment Steps

### 1. Access Render Dashboard

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Navigate to the MorningAI project
3. Select the service to deploy

### 2. Trigger Manual Deploy

1. Click on the service name
2. Click **"Manual Deploy"** button (top right)
3. Select **"Deploy latest commit"** or specific commit
4. Confirm deployment

### 3. Monitor Deployment

1. Watch the deployment logs in real-time
2. Wait for "Live" status (green indicator)
3. Check for any error messages in logs

## Post-Deployment Verification

After deployment completes:

### Health Check

```bash
# Quick liveness check (lightweight)
curl -s https://morningai-backend-v2.onrender.com/healthz | jq .

# Full diagnostic check (includes all service status)
curl -s https://morningai-backend-v2.onrender.com/health | jq .

# Expected response (both endpoints return same format):
# {"status": "healthy", "phase": "Phase 8", "database": "connected", "redis": {...}, ...}
```

> **Note**: Both `/health` and `/healthz` endpoints are available. Use `/healthz` for quick liveness checks, `/health` for detailed diagnostics.

### Smoke Test

1. Verify API responds correctly
2. Check recent logs for errors
3. Monitor error rates in Sentry (if configured)

### Verification Checklist

- [ ] Service shows "Live" status in Render
- [ ] Health endpoint returns 200
- [ ] No new errors in logs (first 5 minutes)
- [ ] Key functionality works (manual spot check)

## Rollback Procedure

If issues are detected after deployment:

### Quick Rollback

1. In Render Dashboard, go to the service
2. Click **"Deploys"** tab
3. Find the previous successful deployment
4. Click **"Redeploy"** on that version

### Emergency Contacts

- Primary: @RC918 (Ryan Chen)
- Render Status: https://status.render.com/

## Deployment Schedule Recommendations

- **Avoid**: Fridays, holidays, end of day
- **Prefer**: Tuesday-Thursday, morning hours
- **Batch**: Group related changes when possible to reduce deployment frequency

## Troubleshooting

### Deployment Stuck

1. Check Render status page for platform issues
2. Cancel and retry deployment
3. Check for resource limits (memory, CPU)

### Service Won't Start

1. Check environment variables are set correctly
2. Review startup logs for missing dependencies
3. Verify database connections

### Health Check Failing

1. Check if dependent services are running
2. Verify Redis/database connectivity
3. Review application logs for errors

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-24 | v0.2 | Added owner/review cadence, improved placeholder warnings, documented both health endpoints, added link verification checklist item |
| 2025-12-24 | v0.1 | Initial SOP created after disabling autoDeploy |

---

*This document should be updated as deployment procedures evolve. Report issues or suggest improvements to @RC918.*
