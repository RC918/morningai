# Orchestrator API - Production Deployment Guide

## Overview

This guide covers deploying the Orchestrator API to production using Render.com with Docker.

## Prerequisites

- Render.com account
- Redis instance (Render Redis or external)
- GitHub repository access

## Architecture

```
┌─────────────────────────────────────────┐
│         Render.com Platform             │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  morningai-orchestrator-api      │  │
│  │  (Docker Container)              │  │
│  │                                  │  │
│  │  - FastAPI Application           │  │
│  │  - JWT Authentication            │  │
│  │  - Rate Limiting                 │  │
│  │  - HITL Gate                     │  │
│  │  - Task Router                   │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
└─────────────────┼───────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Redis Cloud   │
         │  (Task Queue)  │
         └────────────────┘
```

## Deployment Steps

### 1. Set Up Redis

**Option A: Render Redis (Recommended)**
1. Go to Render Dashboard
2. Create New → Redis
3. Choose plan (Starter or higher)
4. Copy the Redis URL

**Option B: External Redis**
- Use Redis Cloud, AWS ElastiCache, or any Redis provider
- Ensure it's accessible from Render

### 2. Configure Environment Variables

In Render Dashboard, set the following environment variables:

#### Required Variables

```bash
# Security (CRITICAL)
ORCHESTRATOR_JWT_SECRET=<generate-with-python-secrets>
ORCHESTRATOR_API_KEYS=<comma-separated-api-keys>

# Redis
REDIS_URL=redis://user:password@host:port/db
```

**Generate Secrets:**
```bash
# JWT Secret (min 32 chars)
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# API Keys (generate multiple)
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

#### Optional Variables

```bash
# CORS
ORCHESTRATOR_CORS_ORIGINS=https://morningai.vercel.app,https://*.vercel.app

# Rate Limiting
ORCHESTRATOR_RATE_LIMIT_TASKS=10
ORCHESTRATOR_RATE_LIMIT_EVENTS=20
ORCHESTRATOR_RATE_LIMIT_APPROVALS=5
ORCHESTRATOR_RATE_LIMIT_STATS=30

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# Task Queue
ORCHESTRATOR_QUEUE_PREFIX=orchestrator
ORCHESTRATOR_TASK_TTL=86400

# HITL Gate
ORCHESTRATOR_APPROVAL_TIMEOUT=86400
ORCHESTRATOR_APPROVAL_HISTORY_TTL=2592000
ORCHESTRATOR_MAX_APPROVAL_HISTORY=1000
```

### 3. Deploy via render.yaml

The `render.yaml` file in the repository root already includes the Orchestrator service configuration.

**Automatic Deployment:**
1. Push changes to `main` branch
2. Render automatically deploys the service
3. Monitor deployment in Render Dashboard

**Manual Deployment:**
1. Go to Render Dashboard
2. Create New → Web Service
3. Connect GitHub repository
4. Select `morningai-orchestrator-api` service
5. Deploy

### 4. Verify Deployment

**Health Check:**
```bash
curl https://morningai-orchestrator-api.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending": 0,
    "in_progress": 0,
    "completed": 0,
    "failed": 0
  }
}
```

**API Documentation:**
```bash
# OpenAPI docs
https://morningai-orchestrator-api.onrender.com/docs

# ReDoc
https://morningai-orchestrator-api.onrender.com/redoc
```

## Monitoring & Alerting

### Built-in Health Checks

Render automatically monitors the `/health` endpoint:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Action**: Restart container on failure

### Metrics to Monitor

1. **API Health**
   - Health check success rate
   - Response time
   - Error rate

2. **Redis Connection**
   - Connection status
   - Queue depth
   - Task processing rate

3. **Rate Limiting**
   - Rate limit hits
   - Blocked requests
   - Per-endpoint metrics

4. **Authentication**
   - Failed authentication attempts
   - Token expiration rate
   - API key usage

### Recommended Monitoring Tools

**Option 1: Render Metrics (Built-in)**
- CPU usage
- Memory usage
- Request count
- Response time

**Option 2: External APM**
- Sentry (error tracking)
- Datadog (full observability)
- New Relic (APM)

**Option 3: Custom Logging**
- CloudWatch Logs
- Papertrail
- Logtail

### Setting Up Alerts

**Render Alerts:**
1. Go to Service Settings
2. Configure Notifications
3. Set up Slack/Email alerts for:
   - Deployment failures
   - Health check failures
   - High CPU/Memory usage

**Custom Alerts (via Sentry):**
```python
# Add to orchestrator/api/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=0.1
)
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Health Check Failure | 2 consecutive | 3 consecutive |
| Response Time | > 1s | > 3s |
| Error Rate | > 1% | > 5% |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Queue Depth | > 100 | > 500 |

## Scaling

### Horizontal Scaling

**Render Auto-Scaling:**
1. Go to Service Settings
2. Enable Auto-Scaling
3. Configure:
   - Min instances: 1
   - Max instances: 3
   - CPU threshold: 70%

**Manual Scaling:**
```bash
# Via Render Dashboard
Settings → Scaling → Number of Instances
```

### Vertical Scaling

**Render Plans:**
- Starter: 512 MB RAM, 0.5 CPU
- Standard: 2 GB RAM, 1 CPU
- Pro: 4 GB RAM, 2 CPU

## Security Checklist

- [ ] `ORCHESTRATOR_JWT_SECRET` is set and unique (min 32 chars)
- [ ] `ORCHESTRATOR_API_KEYS` are generated and secure
- [ ] `REDIS_URL` uses TLS (rediss://)
- [ ] CORS origins are restricted (no `*`)
- [ ] Rate limiting is enabled
- [ ] Health checks are configured
- [ ] Logs are being collected
- [ ] Alerts are configured
- [ ] SSL/TLS is enabled (automatic on Render)

## Troubleshooting

### Service Won't Start

**Check Logs:**
```bash
# Via Render Dashboard
Logs → View Logs

# Common issues:
# 1. Missing ORCHESTRATOR_JWT_SECRET
# 2. Invalid REDIS_URL
# 3. Port binding issues
```

**Fix:**
1. Verify all required environment variables are set
2. Check Redis connection
3. Review startup logs

### Health Check Failing

**Possible Causes:**
1. Redis connection lost
2. Application crash
3. Timeout issues

**Fix:**
```bash
# Check Redis status
redis-cli -u $REDIS_URL ping

# Check application logs
# Look for errors in /health endpoint
```

### High Memory Usage

**Causes:**
1. Memory leaks
2. Large task payloads
3. Too many concurrent requests

**Fix:**
1. Restart service
2. Increase instance size
3. Review task payload sizes
4. Enable rate limiting

### Rate Limiting Issues

**Symptoms:**
- 429 Too Many Requests errors
- Legitimate requests blocked

**Fix:**
1. Adjust rate limits in environment variables
2. Review rate limit logs
3. Consider IP whitelisting for trusted agents

## Rollback Procedure

**Via Render Dashboard:**
1. Go to Service → Deploys
2. Find previous successful deployment
3. Click "Rollback to this deploy"

**Via Git:**
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Render auto-deploys the revert
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error rates
- Check health check status
- Review rate limiting metrics

**Weekly:**
- Review logs for anomalies
- Check Redis memory usage
- Update dependencies (if needed)

**Monthly:**
- Rotate API keys
- Review and update rate limits
- Performance optimization
- Security audit

### Backup & Recovery

**Redis Backup:**
- Render Redis: Automatic daily backups
- External Redis: Configure backup schedule

**Configuration Backup:**
- Environment variables documented in `.env.example`
- Infrastructure as code in `render.yaml`

## Support

**Render Support:**
- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Status: https://status.render.com

**Orchestrator Issues:**
- GitHub: https://github.com/RC918/morningai/issues
- Label: `orchestrator`

## Additional Resources

- [Orchestrator README](./README.md)
- [API Documentation](./docs/API.md)
- [Architecture Overview](./docs/ARCHITECTURE.md)
- [Environment Variables](./.env.example)
