# Infrastructure Secrets & Configuration

## Overview
This document describes the secret management and configuration for the morningai infrastructure, including Sentry DSN, Redis URLs, and environment variable handling.

## Secret Sources

### SENTRY_DSN
- **Purpose**: Sentry error tracking and monitoring
- **Source**: Sentry.io project settings
- **Format**: `https://<public_key>@<org>.ingest.sentry.io/<project_id>`
- **Services using it**: 
  - `morningai-backend-v2` (Flask API)
  - `morningai-agent-worker` (RQ Worker)

**How to obtain:**
1. Log into Sentry.io
2. Navigate to project settings
3. Go to "Client Keys (DSN)" section
4. Copy the DSN URL

**Common issues:**
- **Missing public key error**: Ensure the DSN format includes the public key portion (before the `@`)
  - ❌ Wrong: `https://sentry.io/12345`
  - ✅ Correct: `https://abc123def456@o123456.ingest.sentry.io/789012`

### REDIS_URL
- **Purpose**: Redis connection for RQ task queue
- **Source**: Upstash Redis or other Redis provider
- **Format**: `rediss://:<password>@<host>:<port>` (use `rediss://` for TLS)
- **Services using it**:
  - `morningai-backend-v2` (enqueues tasks)
  - `morningai-agent-worker` (processes tasks)

**How to obtain:**
1. Log into Upstash or your Redis provider
2. Copy the connection string
3. Ensure it starts with `redis://` or `rediss://` (TLS recommended)

**Common issues:**
- **ValueError: Redis URL must specify scheme**: Ensure URL starts with `redis://` or `rediss://`
  - ❌ Wrong: `<password>@<host>:<port>`
  - ✅ Correct: `rediss://:<password>@<host>:<port>`

## Render Environment Variables

### Configuration Priority
Environment variables in Render follow this priority order (highest to lowest):
1. **Service-specific environment variables** (set in Render dashboard)
2. **Environment groups** (shared across services)
3. **render.yaml** (default values)

### Setting Environment Variables

**Via Render Dashboard:**
1. Go to your service (e.g., `morningai-backend-v2`)
2. Click "Environment" tab
3. Click "Add Environment Variable"
4. Enter key and value
5. Click "Save Changes"
6. Service will automatically redeploy

**Via render.yaml:**
```yaml
services:
  - type: web
    name: morningai-backend-v2
    env:
      - key: SENTRY_DSN
        sync: false  # Must be set manually in dashboard
      - key: APP_VERSION
        value: "8.0.0"  # Default value
```

**Note**: Sensitive values like `SENTRY_DSN` and `REDIS_URL` should be set via the dashboard, not in render.yaml.

## Sentry Alert Rules

Alert rules are configured in the Sentry dashboard, not in code. Recommended configuration:

### Web Service Alerts (morningai-backend-v2)
1. **High Error Rate**
   - Condition: Same error occurs >10 times in 5 minutes
   - Action: Email/Slack notification
   - Severity: Warning

2. **Critical Errors**
   - Condition: 5xx errors
   - Action: Immediate notification
   - Severity: Critical

### Worker Service Alerts (morningai-agent-worker)
1. **Job Failures**
   - Condition: 3 consecutive job failures
   - Action: Email/Slack notification
   - Severity: Critical

2. **Worker Crash**
   - Condition: Worker process exits unexpectedly
   - Action: Immediate notification
   - Severity: Critical

### Noise Reduction
- **400 Bad Request**: Filtered via `before_send` hook (client errors)
- **404 Not Found**: Filtered via `before_send` hook (expected behavior)

**How to configure alerts:**
1. Log into Sentry.io
2. Go to "Alerts" → "Create Alert"
3. Select "Issues" alert type
4. Configure conditions as described above
5. Set notification channels (Email, Slack, etc.)

## Checking Logs

### Render Service Logs
1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab
4. Filter by:
   - **Error logs**: Search for `"level":"ERROR"`
   - **Sentry init**: Search for `"Sentry initialized"`
   - **Worker tasks**: Search for `"task_id"`

### Sentry Error Logs
1. Log into Sentry.io
2. Go to "Issues" page
3. Filter by:
   - **Environment**: production/staging
   - **Service**: morningai-backend-v2 or morningai-agent-worker
   - **Time range**: Last 24h/7d/30d

### Common Log Messages

**Successful Sentry initialization:**
```json
{"timestamp":"...","level":"INFO","message":"Sentry initialized successfully with release 8.0.0","operation":"__main__"}
```

**Failed Sentry initialization:**
```json
{"timestamp":"...","level":"WARNING","message":"Failed to initialize Sentry: Invalid DSN. Continuing without Sentry integration.","operation":"__main__"}
```

**Worker task execution:**
```json
{"timestamp":"...","level":"INFO","message":"Starting orchestrator task","operation":"orchestrator.redis_queue.worker","task_id":"..."}
```

## Troubleshooting

### Sentry not receiving events
1. Check logs for "Sentry initialized" message
2. Verify SENTRY_DSN is set correctly in Render
3. Test with `sentry_sdk.capture_message("test")` in code
4. Check Sentry project settings for correct DSN

### Worker not processing tasks
1. Check worker logs for startup messages
2. Verify REDIS_URL is correct
3. Check Redis connectivity: `redis-cli -u $REDIS_URL ping`
4. Verify worker is running: Check Render service status

### Too many 400/404 alerts
1. Verify `before_send` hook is configured in main.py
2. Check Sentry alert rules exclude 400/404
3. Review filtered events in Sentry → "Inbound Filters"

## Security Best Practices

1. **Never commit secrets to git**
   - Use Render dashboard for sensitive values
   - Add `.env` files to `.gitignore`

2. **Rotate secrets periodically**
   - SENTRY_DSN: Regenerate in Sentry dashboard
   - REDIS_URL: Rotate password in provider

3. **Use TLS for Redis**
   - Always use `rediss://` (not `redis://`) for production

4. **Limit secret access**
   - Only grant Render access to team members who need it
   - Use Sentry organizations to control access

## Additional Resources

- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Redis Connection Strings](https://redis.io/docs/reference/clients/#connection-strings)
- [RQ Worker Documentation](https://python-rq.org/docs/workers/)
