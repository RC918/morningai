# Orchestrator API - Monitoring & Alerting Guide

## Overview

This guide covers monitoring, alerting, and observability for the Orchestrator API in production.

**Production URL**: `https://morningai-orchestrator-api.onrender.com`

## Quick Health Check

```bash
curl https://morningai-orchestrator-api.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 0,
    "processing_tasks": 0,
    "total_tasks": 0
  }
}
```

## Monitoring Setup

### 1. Render Built-in Monitoring

Render provides automatic monitoring for all services.

**Access Metrics**:
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select `morningai-orchestrator-api` service
3. Click "Metrics" tab

**Available Metrics**:
- CPU Usage (%)
- Memory Usage (MB)
- Request Count
- Response Time (ms)
- HTTP Status Codes

**Automatic Health Checks**:
- Endpoint: `/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Action: Restart container on failure

### 2. Application Logs

**View Logs**:
```bash
# Via Render Dashboard
Dashboard → morningai-orchestrator-api → Logs

# Via Render CLI (if installed)
render logs morningai-orchestrator-api
```

**Log Levels**:
- `INFO`: Normal operations
- `WARNING`: Potential issues
- `ERROR`: Errors that need attention
- `CRITICAL`: Critical failures

**Important Log Patterns**:
```
# Health check
INFO: 10.222.23.129:56340 - "GET /health HTTP/1.1" 200 OK

# Task creation
INFO: Created task task_abc123 assigned to dev_agent

# Authentication failure
WARNING: Invalid JWT token: Signature has expired

# Rate limit hit
WARNING: Rate limit exceeded for IP 1.2.3.4

# Redis connection issue
ERROR: Failed to connect to Redis: Connection refused
```

### 3. Queue Monitoring

Monitor queue depth to prevent backlog:

```bash
# Get current queue stats
curl https://morningai-orchestrator-api.onrender.com/stats
```

**Response**:
```json
{
  "queue": {
    "pending_tasks": 5,
    "processing_tasks": 2,
    "total_tasks": 150
  },
  "timestamp": "2025-10-22T06:00:00Z"
}
```

**Monitoring Script** (Python):
```python
import requests
import time

def monitor_queue(threshold=100):
    while True:
        try:
            response = requests.get(
                "https://morningai-orchestrator-api.onrender.com/stats",
                timeout=10
            )
            stats = response.json()
            
            pending = stats["queue"]["pending_tasks"]
            processing = stats["queue"]["processing_tasks"]
            
            print(f"Queue: {pending} pending, {processing} processing")
            
            if pending > threshold:
                print(f"⚠️  WARNING: High queue depth: {pending} tasks")
                # Send alert (email, Slack, etc.)
            
            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"❌ Error monitoring queue: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_queue(threshold=100)
```

### 4. Uptime Monitoring

Use external uptime monitoring services:

**Recommended Services**:
- [UptimeRobot](https://uptimerobot.com) (Free)
- [Pingdom](https://www.pingdom.com)
- [StatusCake](https://www.statuscake.com)

**Configuration**:
- URL: `https://morningai-orchestrator-api.onrender.com/health`
- Method: GET
- Expected Status: 200
- Expected Content: `"status": "healthy"`
- Check Interval: 5 minutes
- Alert After: 2 consecutive failures

### 5. Custom Monitoring Dashboard

Create a simple monitoring dashboard using Python:

```python
import requests
import time
from datetime import datetime

def get_health():
    try:
        response = requests.get(
            "https://morningai-orchestrator-api.onrender.com/health",
            timeout=10
        )
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def get_stats():
    try:
        response = requests.get(
            "https://morningai-orchestrator-api.onrender.com/stats",
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def print_dashboard():
    print("\n" + "="*60)
    print(f"Orchestrator API Dashboard - {datetime.now()}")
    print("="*60)
    
    # Health check
    healthy, health_data = get_health()
    status_icon = "✅" if healthy else "❌"
    print(f"\n{status_icon} Health: {'Healthy' if healthy else 'Unhealthy'}")
    
    if healthy:
        print(f"   Redis: {health_data.get('redis', 'unknown')}")
    
    # Queue stats
    stats = get_stats()
    if "error" not in stats:
        queue = stats.get("queue", {})
        print(f"\n📊 Queue Statistics:")
        print(f"   Pending: {queue.get('pending_tasks', 0)}")
        print(f"   Processing: {queue.get('processing_tasks', 0)}")
        print(f"   Total: {queue.get('total_tasks', 0)}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    while True:
        print_dashboard()
        time.sleep(300)  # Update every 5 minutes
```

## Alerting Configuration

### 1. Render Notifications

**Setup Alerts**:
1. Go to Render Dashboard
2. Select `morningai-orchestrator-api` service
3. Click "Settings" → "Notifications"
4. Add notification channels:
   - Email
   - Slack
   - Webhook

**Alert Types**:
- Deployment failures
- Health check failures
- Service restarts
- High CPU/Memory usage

### 2. Slack Alerts

Create a Slack webhook for alerts:

```python
import requests

def send_slack_alert(webhook_url, message, severity="warning"):
    emoji = {
        "info": ":information_source:",
        "warning": ":warning:",
        "error": ":x:",
        "critical": ":rotating_light:"
    }
    
    payload = {
        "text": f"{emoji.get(severity, ':bell:')} *Orchestrator Alert*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
    }
    
    requests.post(webhook_url, json=payload)

# Usage
webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# High queue depth alert
send_slack_alert(
    webhook_url,
    "*High Queue Depth*\n"
    "Pending tasks: 150\n"
    "Processing tasks: 5\n"
    "Action: Check agent health",
    severity="warning"
)

# Service down alert
send_slack_alert(
    webhook_url,
    "*Service Health Check Failed*\n"
    "Status: Unhealthy\n"
    "Redis: Disconnected\n"
    "Action: Check Redis connection",
    severity="critical"
)
```

### 3. Email Alerts

Send email alerts using SMTP:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(smtp_host, smtp_port, username, password, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        print("Alert email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Usage
send_email_alert(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password",
    to_email="admin@morningai.com",
    subject="[ALERT] Orchestrator API - High Queue Depth",
    body="Pending tasks: 150\nProcessing tasks: 5\n\nPlease check agent health."
)
```

### 4. PagerDuty Integration

For critical production alerts:

```python
import requests

def trigger_pagerduty_alert(routing_key, summary, severity="error", source="orchestrator-api"):
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "severity": severity,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    response = requests.post(
        "https://events.pagerduty.com/v2/enqueue",
        json=payload
    )
    
    return response.status_code == 202

# Usage
trigger_pagerduty_alert(
    routing_key="YOUR_ROUTING_KEY",
    summary="Orchestrator API health check failed - Redis disconnected",
    severity="critical"
)
```

## Alert Thresholds

### Recommended Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Health Check Failure | 2 consecutive | 3 consecutive | Restart service, check Redis |
| Response Time | > 1s | > 3s | Check Redis latency, scale up |
| Error Rate | > 1% | > 5% | Check logs, investigate errors |
| CPU Usage | > 70% | > 90% | Scale up instance |
| Memory Usage | > 80% | > 95% | Scale up instance, check leaks |
| Queue Depth (Pending) | > 50 | > 100 | Check agent health, scale agents |
| Queue Depth (Processing) | > 20 | > 50 | Check agent processing time |
| Rate Limit Hits | > 100/hour | > 500/hour | Investigate abuse, adjust limits |
| Failed Auth Attempts | > 50/hour | > 200/hour | Possible attack, review logs |

### Alert Escalation

**Level 1 - Info** (No action required):
- Normal operations
- Successful deployments
- Low queue depth

**Level 2 - Warning** (Monitor):
- High queue depth (50-100 tasks)
- Elevated response time (1-3s)
- Moderate CPU/Memory usage (70-90%)
- Rate limit hits (100-500/hour)

**Level 3 - Error** (Action required):
- Very high queue depth (>100 tasks)
- High response time (>3s)
- High CPU/Memory usage (>90%)
- Multiple rate limit hits (>500/hour)
- Authentication failures (>200/hour)

**Level 4 - Critical** (Immediate action):
- Health check failures
- Redis disconnection
- Service crashes
- Zero available capacity
- Security incidents

## Monitoring Checklist

### Daily Checks
- [ ] Review error logs
- [ ] Check queue depth
- [ ] Verify health check status
- [ ] Monitor response times
- [ ] Review rate limit hits

### Weekly Checks
- [ ] Analyze error trends
- [ ] Review authentication failures
- [ ] Check resource usage trends
- [ ] Verify backup status
- [ ] Update alert thresholds if needed

### Monthly Checks
- [ ] Performance optimization review
- [ ] Security audit
- [ ] Capacity planning
- [ ] Update monitoring scripts
- [ ] Review and update documentation

## Troubleshooting

### High Queue Depth

**Symptoms**:
- Pending tasks > 100
- Tasks not being processed

**Diagnosis**:
```bash
# Check queue stats
curl https://morningai-orchestrator-api.onrender.com/stats

# Check agent health
# (Check individual agent endpoints)
```

**Solutions**:
1. Check if agents are running
2. Verify Redis connection
3. Scale up agent instances
4. Increase agent processing capacity

### High Response Time

**Symptoms**:
- Response time > 3s
- Slow API responses

**Diagnosis**:
```bash
# Test response time
time curl https://morningai-orchestrator-api.onrender.com/health

# Check Redis latency
redis-cli -u $REDIS_URL --latency
```

**Solutions**:
1. Check Redis latency
2. Scale up Orchestrator instance
3. Optimize Redis queries
4. Add caching layer

### Health Check Failures

**Symptoms**:
- Health endpoint returns 503
- Redis connection errors

**Diagnosis**:
```bash
# Check health endpoint
curl -v https://morningai-orchestrator-api.onrender.com/health

# Check Redis connection
redis-cli -u $REDIS_URL ping
```

**Solutions**:
1. Verify Redis is running
2. Check Redis URL configuration
3. Restart Orchestrator service
4. Check network connectivity

### High Error Rate

**Symptoms**:
- Many 500 errors in logs
- Failed task creations

**Diagnosis**:
```bash
# Check recent logs
# Look for ERROR and CRITICAL level logs

# Test endpoints
curl -X POST https://morningai-orchestrator-api.onrender.com/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "bugfix", "payload": {}, "priority": "P2"}'
```

**Solutions**:
1. Review error logs for patterns
2. Check Redis connection
3. Verify authentication configuration
4. Check for code bugs

## Monitoring Tools

### Recommended Tools

**Application Performance Monitoring (APM)**:
- [Sentry](https://sentry.io) - Error tracking
- [Datadog](https://www.datadoghq.com) - Full observability
- [New Relic](https://newrelic.com) - APM
- [Prometheus](https://prometheus.io) - Metrics collection

**Log Management**:
- [Papertrail](https://www.papertrail.com) - Log aggregation
- [Logtail](https://logtail.com) - Log management
- [CloudWatch Logs](https://aws.amazon.com/cloudwatch/) - AWS logs

**Uptime Monitoring**:
- [UptimeRobot](https://uptimerobot.com) - Free uptime monitoring
- [Pingdom](https://www.pingdom.com) - Uptime and performance
- [StatusCake](https://www.statuscake.com) - Website monitoring

**Dashboards**:
- [Grafana](https://grafana.com) - Visualization
- [Kibana](https://www.elastic.co/kibana) - Log visualization
- Custom dashboards (Python/Node.js)

### Setting Up Sentry

Add Sentry for error tracking:

```python
# Add to orchestrator/api/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration()]
)
```

**Environment Variables**:
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
```

## Metrics to Track

### Business Metrics
- Tasks created per hour
- Task completion rate
- Average task processing time
- HITL approval rate
- Agent utilization

### Technical Metrics
- API response time (p50, p95, p99)
- Error rate (%)
- Request rate (req/s)
- Queue depth (pending, processing)
- Redis latency (ms)
- CPU usage (%)
- Memory usage (MB)
- Network I/O (MB/s)

### Security Metrics
- Failed authentication attempts
- Rate limit hits
- Invalid token attempts
- API key usage
- CORS violations

## Support

- **Render Status**: https://status.render.com
- **GitHub Issues**: https://github.com/RC918/morningai/issues
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **API Documentation**: [API_USAGE.md](./API_USAGE.md)
