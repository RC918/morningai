# Canary Rollback Runbook

## Overview

This runbook provides step-by-step instructions for rolling back the LangGraph canary deployment in case of issues or SLO breaches.

**Target Time to Rollback:** < 5 minutes

**Related Documents**:
- [POST_DEPLOY_SMOKE_TEST_CHECKLIST.md](./POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) - Standardized post-rollback verification

## When to Rollback

Rollback should be initiated when:

1. **SLO Breaches**: Canary metrics exceed defined thresholds:
   - p95 latency > 2500ms (configurable via `CANARY_P95_MS_THRESHOLD`)
   - 5xx error rate > 1.0% (configurable via `CANARY_5XX_RATE_THRESHOLD`)
   - Planner failure rate > 5.0% (configurable via `CANARY_FAILURE_RATE_THRESHOLD`)

2. **Manual Decision**: Product/engineering decision to disable canary for any reason

3. **Incident Response**: Critical production issues traced to canary deployment

## Rollback Procedure

### Step 1: Set Canary Percentage to 0

**Render Dashboard:**
1. Navigate to https://dashboard.render.com
2. Select the `morningai-agent-worker` service
3. Go to **Environment** tab
4. Find `USE_LANGGRAPH_PERCENT` variable
5. Change value from current (e.g., `1` or `5`) to `0`
6. Click **Save Changes**

**Expected Time:** 1 minute

### Step 2: Redeploy Service

Render will automatically trigger a redeploy when environment variables change.

**Monitor deployment:**
1. Go to **Events** tab
2. Wait for "Deploy succeeded" message
3. Verify new deployment is live

**Expected Time:** 2-3 minutes

### Step 3: Verify Rollback

**Check Feature Flags:**
1. View worker logs in Render dashboard
2. Look for "Feature flags snapshot" log entry on startup
3. Verify `use_langgraph_percent: 0`

**Check Routing Decisions:**
1. Submit a test task via API or Owner Console
2. Check worker logs for "Using simple orchestrator" message
3. Verify no "Using LangGraph orchestrator" messages appear

**Check Monitoring Dashboard:**
1. Navigate to `/api/phase7/monitoring/dashboard`
2. Check `canary.flags.use_langgraph_percent` is `0`
3. Verify `canary.counts.decisions_langgraph` stops incrementing
4. Verify `canary.counts.decisions_simple` continues incrementing

**Expected Time:** 1 minute

### Step 4: Confirm System Stability

**Run Post-Rollback Verification:**
1. Follow [Post-Deploy Smoke Test Checklist](./POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) - "After LangGraph Canary Rollback" scenario
2. Verify all checks pass before proceeding

**Monitor for 15 minutes:**
1. Check error rates return to baseline
2. Verify p95 latency returns to normal
3. Confirm no new Sentry alerts

**Expected Time:** 15 minutes (monitoring period)

## Alternative Rollback Methods

### Method 2: Disable LangGraph Entirely

If `USE_LANGGRAPH_PERCENT=0` doesn't work, disable LangGraph completely:

1. Set `USE_LANGGRAPH=false` in Render environment
2. Set `USE_LANGGRAPH_PERCENT=0` (if not already)
3. Redeploy service
4. Verify rollback as in Step 3

### Method 3: Emergency Revert (Git)

If environment variable changes don't work:

1. Identify the commit before canary deployment was merged
2. Create emergency revert PR:
   ```bash
   git revert <canary-pr-merge-commit>
   git push origin main
   ```
3. Merge revert PR immediately
4. Render will auto-deploy from main branch

**Note:** This is a last resort and should only be used if environment variable rollback fails.

## Post-Rollback Actions

### Immediate (< 1 hour)

1. **Notify stakeholders**: Post in #engineering Slack channel
2. **Document incident**: Create incident report with:
   - Timestamp of rollback
   - Reason for rollback
   - SLO metrics at time of rollback
   - Any user-facing impact

3. **Preserve metrics**: Export canary metrics for analysis:
   ```bash
   curl https://api.morningai.app/api/phase7/monitoring/dashboard > canary_metrics_$(date +%s).json
   ```

### Follow-up (< 24 hours)

1. **Root cause analysis**: Investigate why rollback was needed
2. **Fix issues**: Address root cause before re-enabling canary
3. **Update thresholds**: Adjust SLO thresholds if they were too aggressive
4. **Test in staging**: Validate fixes in staging environment before production

### Re-enabling Canary

Before re-enabling canary:

1. ✅ Root cause identified and fixed
2. ✅ Changes tested in staging
3. ✅ Monitoring dashboard shows healthy metrics
4. ✅ Team consensus to proceed

**Re-enable gradually (see ADR-005 for full rollout plan):**
1. Start with `USE_LANGGRAPH_PERCENT=5` (5%) - baseline metrics
2. Monitor for 1 week, verify success rate > 95%, p95 < 30s
3. Increase to `USE_LANGGRAPH_PERCENT=15` (15%) - staging validation
4. Monitor for 1 week, verify no SLO breaches
5. Increase to `USE_LANGGRAPH_PERCENT=25` (25%) - expanded canary
6. Monitor for 1 week, verify stable performance
7. Increase to `USE_LANGGRAPH_PERCENT=50` (50%) - majority traffic
8. Monitor for 1 week, verify stable performance
9. Full rollout: `USE_LANGGRAPH_PERCENT=100` (100%)

**Note:** FAQ tasks bypass LangGraph by default (USE_LANGGRAPH_FOR_FAQ=false) to preserve low latency.

## Monitoring and Alerts

### Canary Metrics Dashboard

**URL:** `https://api.morningai.app/api/phase7/monitoring/dashboard`

**Key Metrics:**
- `canary.counts.decisions_langgraph`: Number of tasks routed to LangGraph
- `canary.counts.decisions_simple`: Number of tasks routed to simple orchestrator
- `canary.latency.p95_ms`: p95 latency for LangGraph tasks
- `canary.rates.error_5xx_rate`: 5xx error rate percentage
- `canary.rates.failure_rate`: Planner failure rate percentage
- `canary.slo_compliance.all_ok`: Boolean indicating all SLOs are met

### Sentry Alerts

Canary SLO breaches automatically trigger Sentry alerts with tags:
- `alert_type`: `p95_latency_breach`, `error_5xx_rate_breach`, or `failure_rate_breach`
- `component`: `canary_deployment`

**Alert Cooldown:** 5 minutes (configurable via `CANARY_ALERTING_COOLDOWN_SECONDS`)

### Webhook Alerts (Optional)

If `OPS_ALERT_WEBHOOK_URL` is configured, alerts are also sent to the webhook endpoint.

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LANGGRAPH_PERCENT` | `0` | Percentage of tasks routed to LangGraph (0-100) |
| `USE_LANGGRAPH` | `false` | Enable LangGraph for all tasks (overridden by percent) |
| `USE_LLM_PLANNER` | `false` | Enable LLM-powered planner in LangGraph |
| `CANARY_METRICS_ENABLED` | `true` | Enable canary metrics collection |
| `CANARY_ALERTING_ENABLED` | `true` | Enable canary SLO alerting |
| `CANARY_WINDOW_MINUTES` | `15` | Time window for SLO evaluation (minutes) |
| `CANARY_P95_MS_THRESHOLD` | `2500` | p95 latency threshold (milliseconds) |
| `CANARY_5XX_RATE_THRESHOLD` | `1.0` | 5xx error rate threshold (percentage) |
| `CANARY_FAILURE_RATE_THRESHOLD` | `5.0` | Planner failure rate threshold (percentage) |
| `OPS_ALERT_WEBHOOK_URL` | (unset) | Optional webhook URL for alerts |

### Render Service

- **Service Name:** `morningai-agent-worker`
- **Dashboard:** https://dashboard.render.com
- **Logs:** Available in Render dashboard under "Logs" tab

## Troubleshooting

### Issue: Rollback doesn't take effect

**Symptoms:** After setting `USE_LANGGRAPH_PERCENT=0`, tasks still route to LangGraph

**Resolution:**
1. Verify environment variable was saved in Render
2. Check deployment completed successfully
3. Verify worker restarted (check startup logs)
4. If issue persists, try Method 2 (disable LangGraph entirely)

### Issue: Can't access Render dashboard

**Symptoms:** Unable to log in to Render dashboard

**Resolution:**
1. Contact Render account owner for access
2. Use alternative Method 3 (Git revert) if urgent
3. Update access documentation for future incidents

### Issue: Metrics not updating

**Symptoms:** Canary metrics dashboard shows stale data

**Resolution:**
1. Check Redis connectivity: `redis-cli -u $REDIS_URL ping`
2. Verify `CANARY_METRICS_ENABLED=true`
3. Check worker logs for metric collection errors
4. Restart worker if necessary

## Contact Information

**On-Call Engineer:** Check PagerDuty rotation

**Escalation:**
- Engineering Lead: [Contact Info]
- CTO: [Contact Info]

**Slack Channels:**
- `#engineering` - General engineering discussion
- `#incidents` - Active incident response
- `#monitoring` - Monitoring and alerting

## Testing This Runbook

**Staging Environment:**

Test rollback procedure in staging before production:

1. Enable canary in staging: `USE_LANGGRAPH_PERCENT=10`
2. Submit test tasks and verify routing
3. Follow rollback procedure
4. Verify rollback successful
5. Document time taken for each step

**Expected Total Time:** < 5 minutes (excluding monitoring period)

## Version History

- **v1.1** (2025-12-10): Add reference to Post-Deploy Smoke Test Checklist for standardized verification
- **v1.0** (2025-11-21): Initial runbook created as part of canary hardening sprint
