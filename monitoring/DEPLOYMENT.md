# Braintrust Trace Processor Deployment Guide

## Overview

The Braintrust Trace Processor is a FastAPI service that receives trace data from Vercel and processes it for monitoring, cost analysis, and alerting.

## Prerequisites

- Docker installed
- PostgreSQL database with migrations 010-013 applied
- Environment variables configured

## Environment Variables

Create a `.env` file or configure the following environment variables:

```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/database

# Optional (with defaults)
COST_ALERT_THRESHOLD=10.0          # Alert when LLM cost exceeds this amount
LATENCY_ALERT_THRESHOLD=500.0      # Alert when latency exceeds this (ms)
```

## Deployment Options

### Option 1: Docker (Recommended)

#### Build the Docker image

```bash
cd monitoring
docker build -t braintrust-processor:latest .
```

#### Run the container

```bash
docker run -d \
  --name braintrust-processor \
  -p 8001:8001 \
  -e DATABASE_URL="postgresql://user:password@host:port/database" \
  -e COST_ALERT_THRESHOLD=10.0 \
  -e LATENCY_ALERT_THRESHOLD=500.0 \
  --restart unless-stopped \
  braintrust-processor:latest
```

#### Check health

```bash
curl http://localhost:8001/health
```

### Option 2: Render.com

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `cd monitoring && pip install -r requirements.txt`
   - **Start Command**: `cd monitoring && uvicorn braintrust_processor:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `DATABASE_URL`, `COST_ALERT_THRESHOLD`, `LATENCY_ALERT_THRESHOLD`
4. Deploy

### Option 3: Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Create `fly.toml`:

```toml
app = "braintrust-processor"
primary_region = "sjc"

[build]
  dockerfile = "monitoring/Dockerfile"

[env]
  PORT = "8001"

[[services]]
  internal_port = 8001
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = "30s"
    timeout = "10s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
```

4. Set secrets:
```bash
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set COST_ALERT_THRESHOLD=10.0
fly secrets set LATENCY_ALERT_THRESHOLD=500.0
```

5. Deploy:
```bash
fly deploy
```

### Option 4: AWS Lambda (Serverless)

Use Mangum adapter:

```bash
pip install mangum
```

Update `braintrust_processor.py`:

```python
from mangum import Mangum

# ... existing code ...

handler = Mangum(app)
```

Deploy using AWS SAM or Serverless Framework.

## Vercel Integration

### Configure Vercel Trace Drains

1. Go to Vercel Dashboard → Project Settings → Integrations
2. Add Trace Drain:
   - **URL**: `https://your-braintrust-service.com/webhook/vercel-trace`
   - **Sampling Rate**: 10% (0.1)
   - **Headers**: Add authentication if needed

### Test Webhook

```bash
curl -X POST https://your-braintrust-service.com/webhook/vercel-trace \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-trace-123",
    "timestamp": "2025-10-21T00:00:00Z",
    "duration": 250,
    "status": "success",
    "url": "/api/test",
    "method": "GET",
    "metadata": {
      "model": "gpt-4",
      "tokens": 1000
    }
  }'
```

## API Endpoints

### POST /webhook/vercel-trace
Receive trace data from Vercel

### GET /health
Health check endpoint

### GET /metrics/summary?hours=24
Get metrics summary for the last N hours

### GET /alerts/recent?limit=100
Get recent alerts

## Monitoring

### Check Service Status

```bash
curl https://your-braintrust-service.com/health
```

### View Recent Metrics

```bash
curl https://your-braintrust-service.com/metrics/summary?hours=24
```

### View Recent Alerts

```bash
curl https://your-braintrust-service.com/alerts/recent?limit=10
```

## Troubleshooting

### Service won't start

1. Check DATABASE_URL is correct
2. Verify database has migrations 010-013 applied
3. Check logs: `docker logs braintrust-processor`

### Traces not being received

1. Verify Vercel webhook URL is correct
2. Check Vercel webhook logs in dashboard
3. Test webhook manually with curl
4. Check service logs for errors

### High memory usage

1. Reduce sampling rate in Vercel (e.g., 5% instead of 10%)
2. Add database connection pooling
3. Increase container memory limits

## Maintenance

### Update Service

```bash
# Pull latest code
git pull

# Rebuild and restart
cd monitoring
docker build -t braintrust-processor:latest .
docker stop braintrust-processor
docker rm braintrust-processor
docker run -d --name braintrust-processor ... (same command as above)
```

### Backup Database

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Refresh Materialized Views

```bash
psql $DATABASE_URL -c "SELECT refresh_daily_cost_summary();"
```

## Security

1. **Use HTTPS**: Always use HTTPS for webhook endpoints
2. **Authentication**: Add webhook authentication headers
3. **Rate Limiting**: Configure rate limiting on webhook endpoint
4. **Database Access**: Use read-only credentials if possible
5. **Secrets Management**: Use environment variables, never commit secrets

## Cost Optimization

1. **Sampling Rate**: Start with 10%, reduce if costs are high
2. **Data Retention**: Set up automatic cleanup of old traces (>90 days)
3. **Materialized Views**: Refresh only during off-peak hours
4. **Alerting**: Set appropriate thresholds to avoid alert fatigue

## Support

For issues or questions:
- Check logs: `docker logs braintrust-processor`
- Review database migrations: `migrations/011_*.sql`, `migrations/012_*.sql`, `migrations/013_*.sql`
- Contact: Ryan Chen (@RC918)
