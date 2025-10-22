# Orchestrator API Monitoring Setup

This document describes the automated monitoring system for the MorningAI Orchestrator API.

## Overview

The monitoring system uses a Python script that runs every 5 minutes via GitHub Actions to check the health and performance of the Orchestrator API. When issues are detected, alerts are automatically sent to Slack.

## Components

### 1. Monitoring Script

**Location**: `scripts/monitor_orchestrator.py`

**Features**:
- Health check monitoring (endpoint: `/health`)
- Queue depth monitoring (endpoint: `/stats`)
- Response time tracking
- Redis connection status verification
- Automatic Slack notifications

**Thresholds**:
- Maximum response time: 5 seconds
- Warning queue depth: 100 pending tasks
- Critical queue depth: 500 pending tasks

### 2. GitHub Actions Workflow

**Location**: `.github/workflows/monitor-orchestrator.yml`

**Schedule**: Runs every 5 minutes (`*/5 * * * *`)

**Triggers**:
- Scheduled (cron)
- Manual dispatch (via GitHub Actions UI)

### 3. Slack Integration

**Channel**: `#alerts` in the `morningai` workspace

**Alert Types**:
- 🔴 **Critical**: Service down, connection errors, timeouts, critical queue depth
- ⚠️ **Warning**: Slow response times, elevated queue depth
- ❌ **Error**: Redis connection issues, health check failures
- ✅ **Success**: Monitoring system status updates

## Setup Instructions

### Prerequisites

1. Slack workspace with `#alerts` channel
2. Slack Incoming Webhook URL
3. GitHub repository with Actions enabled

### Step 1: Configure Slack Webhook

1. Go to https://api.slack.com/apps
2. Create a new app or select existing app
3. Enable "Incoming Webhooks"
4. Add webhook to `#alerts` channel
5. Copy the webhook URL (format: `https://hooks.slack.com/services/...`)

### Step 2: Add GitHub Secret

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add secret:
   - **Name**: `SLACK_WEBHOOK_URL`
   - **Value**: Your Slack webhook URL from Step 1
5. Click **Add secret**

### Step 3: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If prompted, enable GitHub Actions
3. The workflow will automatically run every 5 minutes

### Step 4: Manual Test (Optional)

1. Go to **Actions** tab
2. Select **Monitor Orchestrator API** workflow
3. Click **Run workflow** → **Run workflow**
4. Check the `#alerts` channel for test results

## Monitoring Checks

### Health Check

**Endpoint**: `GET /health`

**Success Criteria**:
- HTTP 200 status code
- Response time < 5 seconds
- Redis status: "connected"

**Failure Actions**:
- **Timeout (>10s)**: Send critical alert
- **Connection error**: Send critical alert
- **Redis disconnected**: Send error alert
- **Slow response (>5s)**: Send warning alert

### Queue Check

**Endpoint**: `GET /stats`

**Monitored Metrics**:
- `pending_tasks`: Number of tasks waiting to be processed
- `processing_tasks`: Number of tasks currently being processed
- `total_tasks`: Total number of tasks in the system

**Alert Thresholds**:
- **Critical** (≥500 pending): Immediate action required
- **Warning** (≥100 pending): Monitor agent capacity

## Alert Examples

### Critical Alert: Service Down

```
🚨 Orchestrator Alert

Health Check Failed - Connection Error
Unable to connect to the API.
URL: https://morningai-orchestrator-api.onrender.com/health
Possible causes: Service is down, network issue, or DNS problem

Time: 2025-10-22 09:30:00 UTC | Severity: CRITICAL
```

### Warning Alert: High Queue Depth

```
⚠️ Orchestrator Alert

WARNING: Elevated Queue Depth
Pending tasks: 150 (threshold: 100)
Processing tasks: 5
Total tasks: 155

Recommendation: Monitor agent capacity.

Time: 2025-10-22 09:30:00 UTC | Severity: WARNING
```

### Success: All Checks Passed

When all checks pass, no alert is sent (to avoid noise). You can check the GitHub Actions logs to see successful runs.

## Troubleshooting

### No Alerts Received

1. **Check GitHub Actions**:
   - Go to **Actions** tab
   - Verify workflow is running successfully
   - Check for error messages in logs

2. **Verify Slack Webhook**:
   - Ensure `SLACK_WEBHOOK_URL` secret is set correctly
   - Test webhook manually:
     ```bash
     curl -X POST -H 'Content-type: application/json' \
       --data '{"text":"Test message"}' \
       YOUR_WEBHOOK_URL
     ```

3. **Check Workflow Permissions**:
   - Go to **Settings** → **Actions** → **General**
   - Ensure "Read and write permissions" is enabled

### False Positives

If you receive alerts when the service is actually healthy:

1. **Adjust thresholds** in `scripts/monitor_orchestrator.py`:
   ```python
   self.max_response_time = 10.0  # Increase from 5.0
   self.max_queue_depth = 200     # Increase from 100
   ```

2. **Commit and push changes**:
   ```bash
   git add scripts/monitor_orchestrator.py
   git commit -m "Adjust monitoring thresholds"
   git push
   ```

### Workflow Not Running

1. **Check cron schedule**:
   - GitHub Actions may have up to 10-minute delay for scheduled workflows
   - Use manual dispatch to test immediately

2. **Verify workflow file**:
   - Ensure `.github/workflows/monitor-orchestrator.yml` exists
   - Check for YAML syntax errors

## Customization

### Change Monitoring Frequency

Edit `.github/workflows/monitor-orchestrator.yml`:

```yaml
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
    # - cron: '0 * * * *'   # Every hour
    # - cron: '0 */6 * * *' # Every 6 hours
```

### Add Custom Checks

Edit `scripts/monitor_orchestrator.py` and add new methods:

```python
def check_custom_metric(self) -> bool:
    """Check custom metric"""
    # Your custom logic here
    pass

def run(self) -> int:
    """Run all monitoring checks"""
    health_ok = self.run_health_check()
    queue_ok = self.run_queue_check()
    custom_ok = self.check_custom_metric()  # Add your check
    
    if health_ok and queue_ok and custom_ok:
        return 0
    else:
        return 1
```

### Change Alert Format

Edit the `send_slack_alert()` method in `scripts/monitor_orchestrator.py` to customize the message format.

## Monitoring Dashboard

To view monitoring history:

1. Go to **Actions** tab in GitHub
2. Select **Monitor Orchestrator API** workflow
3. View run history and logs

## Cost

**GitHub Actions**: Free for public repositories, 2,000 minutes/month for private repositories

**Slack**: Free tier includes unlimited messages

**Estimated Usage**: ~8,640 workflow runs per month (every 5 minutes) = ~43 minutes of GitHub Actions time

## Related Documentation

- [API Usage Guide](../orchestrator/API_USAGE.md)
- [Deployment Guide](../RENDER_DEPLOYMENT_GUIDE.md)
- [Monitoring Guide](../orchestrator/MONITORING.md)

## Support

For issues or questions:
1. Check GitHub Actions logs for error details
2. Review this documentation
3. Contact the development team
