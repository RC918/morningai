# MorningAI Environment Architecture

## Overview

MorningAI uses a multi-environment deployment architecture to ensure safe development, testing, and production workflows. This document provides a comprehensive overview of all environments, their configurations, and deployment processes.

---

## Environment Summary

| Environment | Status | Purpose | Branch | Auto-Deploy |
|-------------|--------|---------|--------|-------------|
| **Production** | ✅ Active | Live user-facing services | `main` | Yes |
| **Staging** | ✅ Active | Pre-production testing | `develop` | Yes |
| **Local Development** | ✅ Active | Developer workstations | Any | No |

---

## 🚀 Production Environment

### Services

#### Backend API
- **URL**: https://morningai-backend-v2.onrender.com
- **Service Name**: `morningai-backend-v2`
- **Platform**: Render
- **Runtime**: Python 3
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /healthz`

#### Orchestrator API
- **URL**: https://morningai-orchestrator-api.onrender.com
- **Service Name**: `morningai-orchestrator-api`
- **Platform**: Render
- **Runtime**: Docker
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /health`

⚠️ **Orchestrator Architecture (Dual System)**

MorningAI uses a producer-consumer architecture with two orchestrator implementations:

| Component | Role | Maturity | Service | Path |
|-----------|------|----------|---------|------|
| **API Orchestrator** | API Layer (FastAPI) | Beta | `morningai-orchestrator-api` | `orchestrator/` |
| **Worker Orchestrator** | Task Execution (RQ + LangGraph) | Production | `morningai-agent-worker` | `handoff/20250928/40_App/orchestrator/` |

**Architecture**: Producer (API) receives HTTP requests and enqueues tasks to Redis. Consumer (Worker) polls Redis and executes tasks using LangGraph workflows.

**Documentation**: [ADR-001: Dual Orchestrator Architecture](adr/001-dual-orchestrator-architecture.md), [ADR-002: Producer-Consumer Architecture](adr/002-producer-consumer-architecture.md)

**Consolidation Plan**: 2026 Q1 (tracked in [Issue #1105](https://github.com/RC918/morningai/issues/1105))

#### Frontend Dashboard
- **URL**: https://morningai.vercel.app
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)

### Infrastructure

#### Database
- **Provider**: Supabase PostgreSQL
- **Type**: Production instance
- **Connection**: Pooler (port 6543)
- **Backups**: Automatic daily backups

#### Redis
- **Provider**: Upstash
- **Type**: Production instance
- **Protocol**: `rediss://` (TLS enabled)
- **Key Prefix**: None (production)

#### Monitoring
- **Error Tracking**: Sentry
- **Environment Tag**: `production`
- **Uptime Target**: 99.9%

### Environment Variables

**Critical Variables**:
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
JWT_SECRET_KEY=<production-secret>
SECRET_KEY=<production-secret>
MASTER_ENCRYPTION_KEY=<production-secret>
ORCHESTRATOR_JWT_SECRET=<production-secret>
```

**Monitoring**:
```bash
SENTRY_DSN=<production-dsn>
SENTRY_ENVIRONMENT=production
```

**Rate Limiting**:
```bash
# Rate limiting configuration (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=true               # Fail on startup if Redis unavailable (production only)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

---

## 🧪 Staging Environment

### Services

#### Backend API Staging
- **URL**: https://morningai-backend-v2-stg.onrender.com
- **Service Name**: `morningai-backend-v2-stg`
- **Platform**: Render
- **Runtime**: Python 3
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Health Check**: `GET /healthz`
- **Status**: ✅ Healthy

**Health Check Response**:
```json
{
  "database": "connected",
  "phase": "Phase 8: Self-service Dashboard & Reporting Center",
  "redis": {
    "protocol": "rediss",
    "status": "connected",
    "tls_enabled": true,
    "type": "redis",
    "url": "main-gull-14059.upstash.io:6379"
  },
  "services": {
    "backend_services": "available",
    "phase4_apis": "available",
    "phase5_apis": "available",
    "phase6_apis": "available",
    "security_manager": "available"
  },
  "status": "healthy",
  "timestamp": "2025-10-28T08:18:16.548126",
  "version": "8.0.0"
}
```

#### Orchestrator API Staging
- **URL**: https://morningai-orchestrator-api-stg.onrender.com
- **Service Name**: `morningai-orchestrator-api-stg`
- **Platform**: Render
- **Runtime**: Docker
- **Dockerfile**: `orchestrator/Dockerfile`
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Health Check**: `GET /health`
- **Status**: ✅ Healthy

**Health Check Response**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 292,
    "processing_tasks": 62,
    "total_tasks": 354
  }
}
```

#### Frontend Dashboard Staging
- **URL**: https://staging.morningai.me
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Status**: ✅ Healthy

#### Owner Console Staging
- **URL**: https://staging-owner.morningai.me
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Status**: ✅ Healthy

**Deployment Strategy**:
- **Branch Policy**: `develop` → staging, `main` → production, `feature/*|fix/*|devin/*` → preview
- **Ignore Script**: `scripts/vercel-ignore.sh` (skips docs-only changes)
- **Documentation**: See [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](deployment/VERCEL_DEPLOYMENT_STRATEGY.md) for complete setup and troubleshooting

### Infrastructure

#### Database
- **Provider**: Supabase PostgreSQL
- **Project Name**: `morningai-staging`
- **Project ID**: `dckisglnlemvpvmyvnut`
- **URL**: https://dckisglnlemvpvmyvnut.supabase.co
- **Connection**: Pooler (port 6543)
- **Data**: Separate from production

#### Redis
- **Provider**: Upstash (shared with production)
- **Protocol**: `rediss://` (TLS enabled)
- **Key Prefix**: `stg:` (isolates staging data)
- **Queue Name**: `orchestrator-staging`

#### Monitoring
- **Error Tracking**: Sentry
- **Environment Tag**: `staging`
- **Cost**: ~$14/month (Render Starter plans)

### Environment Variables

**Backend Staging**:
```bash
# Environment
ENVIRONMENT=staging

# Database (Staging Supabase)
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>

# Redis (Shared with production, isolated by prefix)
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging

# Database Connection Pool
DB_POOL_SIZE=5
DB_POOL_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Security (Different from production)
JWT_SECRET_KEY=<staging-secret>
SECRET_KEY=<staging-secret>
MASTER_ENCRYPTION_KEY=<staging-secret>

# Monitoring
SENTRY_DSN=<same-as-production>
SENTRY_ENVIRONMENT=staging

# Rate Limiting (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=false              # Allow startup without Redis (staging)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Orchestrator Staging**:
```bash
# Environment
ENVIRONMENT=staging
PORT=8000

# Security (REQUIRED)
ORCHESTRATOR_JWT_SECRET=<staging-orchestrator-secret-48-chars>

# Redis (REQUIRED)
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging

# Optional
ORCHESTRATOR_CORS_ORIGINS=https://morningai-staging.vercel.app,http://localhost:5173
SENTRY_ENVIRONMENT=staging
LOG_LEVEL=INFO
```

### Setup Documentation

For complete staging environment setup instructions, see:
- **[Staging Setup Guide](ops/STAGING_SETUP_GUIDE.md)** - Comprehensive setup guide with step-by-step instructions

---

## 💻 Local Development Environment

### Services

#### Backend API
- **URL**: http://localhost:8000
- **Runtime**: Python 3.12+
- **Framework**: Flask
- **Start Command**: 
  ```bash
  # Option 1: Flask CLI (recommended for development)
  export FLASK_APP=src.main
  flask run --port 8000
  
  # Option 2: Gunicorn (production-like)
  gunicorn "src.main:app" --bind 0.0.0.0:8000 --reload
  
  # Quick one-liner (equivalent to Option 1)
  export FLASK_APP=src.main && flask run --port 8000
  ```
- **Working Directory**: `handoff/20250928/40_App/api-backend`

#### Orchestrator API
- **URL**: http://localhost:8001
- **Runtime**: Python 3.12+
- **Framework**: FastAPI
- **Start Command**: `uvicorn orchestrator.api.main:app --port 8001 --reload`
- **Working Directory**: Repository root

#### Frontend Dashboard
- **URL**: http://localhost:5173
- **Runtime**: Node.js 20+
- **Start Command**: `npm run dev`
- **Working Directory**: `handoff/20250928/40_App/frontend-dashboard`

### Infrastructure

#### Database
- **Option 1**: Local PostgreSQL
- **Option 2**: Staging Supabase (recommended for testing)
- **Option 3**: Production Supabase (read-only, for debugging)

#### Redis
- **Option 1**: Local Redis (`redis://localhost:6379/0`)
- **Option 2**: Staging Redis (recommended for testing)

### Environment Variables

Create `.env` file in each service directory:

**Backend `.env`**:
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0
TESTING=false

# Or use staging infrastructure
DATABASE_URL=<staging-database-url>
REDIS_URL=<staging-redis-url>
REDIS_KEY_PREFIX=dev:

# Rate Limiting (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=false              # Allow startup without Redis (development)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Frontend `.env.local`**:
```bash
VITE_API_URL=http://localhost:8000
VITE_ORCHESTRATOR_URL=http://localhost:8001
VITE_ENVIRONMENT=development

# Or point to staging backend
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
VITE_ORCHESTRATOR_URL=https://morningai-orchestrator-api-stg.onrender.com
```

### Setup Documentation

For complete local development setup instructions, see:
- **[Local Development Setup](setup_local.md)** - Quick start guide and troubleshooting

---

## 🔄 Deployment Workflow

### Development Flow

```mermaid
graph LR
    A[Feature Branch] -->|PR| B[develop]
    B -->|Auto-deploy| C[Staging Environment]
    C -->|Manual Test| D{Tests Pass?}
    D -->|Yes| E[PR to main]
    E -->|Manual Approval| F[Production]
    D -->|No| A
```

### Step-by-Step Process

#### 1. Feature Development
```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Develop and commit
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

#### 2. Staging Deployment
```bash
# Create PR to develop
# GitHub Actions will:
# - Run staging CI checks
# - Auto-deploy to Render staging services

# Test on staging
curl https://morningai-backend-v2-stg.onrender.com/healthz
```

#### 3. Production Deployment
```bash
# After staging tests pass, create PR to main
# Requires manual approval
# Auto-deploys to production services
```

### CI/CD Workflows

#### Staging CI (`.github/workflows/staging-deploy.yml`)
- **Trigger**: Push/PR to `develop` branch
- **Tests**: Backend (pytest + coverage), Frontend (build), Smoke tests
- **Deploy**: Auto-deploy to Render staging services
- **Environment**: `ENVIRONMENT=staging`

#### Production CI (`.github/workflows/backend.yml`, etc.)
- **Trigger**: Push to `main` branch
- **Tests**: Full test suite, E2E tests
- **Deploy**: Auto-deploy to production services
- **Validation**: Post-deploy health checks (90% SLA)

---

## 🧪 Testing Environments

### Health Check Commands

**Production**:
```bash
# Backend
curl https://morningai-backend-v2.onrender.com/healthz

# Orchestrator
curl https://morningai-orchestrator-api.onrender.com/health

# Monitoring Dashboard
curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard
```

**Staging**:
```bash
# Backend
curl https://morningai-backend-v2-stg.onrender.com/healthz

# Orchestrator
curl https://morningai-orchestrator-api-stg.onrender.com/health

# Monitoring Dashboard
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard
```

**Local**:
```bash
# Backend
curl http://localhost:8000/healthz

# Orchestrator
curl http://localhost:8001/health

# Monitoring Dashboard
curl http://localhost:8000/api/phase7/monitoring/dashboard
```

### Monitoring Dashboard Endpoints

**Primary Endpoint** (Recommended):
- **Path**: `/api/phase7/monitoring/dashboard`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ✅ Production Ready

**Legacy Endpoint** (Deprecated):
- **Path**: `/api/dashboard/data`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ⚠️ **DEPRECATED** - Use `/api/phase7/monitoring/dashboard` instead
- **Deprecation Timeline**: TBD (tracked in future release notes)

**Degradation Behavior**:

| Scenario | HTTP Status | Response Behavior |
|----------|-------------|-------------------|
| All services healthy | 200 OK | Full metrics with real data |
| Redis unavailable | 200 OK | Fallback metrics with `available: false`, `source: 'fallback'`, `error: 'Redis unavailable'` |
| Database unavailable | 200 OK | `overall_status: 'degraded'` with critical alert |
| Both Redis + DB unavailable | 503 Service Unavailable | `ServiceUnavailableError` response |

**Environment Variables**:
- `REDIS_URL`: Required for queue metrics
- `DATABASE_URL`: Required for health checks
- `BACKEND_SERVICES_AVAILABLE`: Gate flag (auto-set by backend)

**Documentation**: See [Monitoring Troubleshooting Guide](deployment/troubleshooting-monitoring.md) for 503 error diagnosis

### Expected Responses

**Backend `/healthz`**:
```json
{
  "status": "healthy",
  "phase": "Phase 8",
  "version": "8.0.0",
  "database": "connected",
  "redis": {
    "status": "connected",
    "protocol": "rediss",
    "tls_enabled": true
  },
  "services": {
    "backend_services": "available",
    "phase4_apis": "available",
    "phase5_apis": "available",
    "phase6_apis": "available",
    "security_manager": "available"
  }
}
```

**Orchestrator `/health`**:
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

---

## 🔐 Security & Secrets

### Secret Management

**Production Secrets**:
- Stored in Render dashboard (encrypted)
- Different from staging secrets
- Minimum 32 characters for JWT/encryption keys
- Rotated quarterly

**Staging Secrets**:
- Stored in Render dashboard (encrypted)
- Different from production secrets
- Can use weaker secrets (but still 32+ chars)
- Rotated as needed

**Local Secrets**:
- Stored in `.env` files (gitignored)
- Can use test/dummy values
- Never commit to repository

### Secret Generation

```bash
# Generate JWT secret (48 characters recommended)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Generate encryption key (32 characters minimum)
openssl rand -hex 32

# Generate API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 Monitoring & Observability

### Sentry Error Tracking

**Production**:
- Environment: `production`
- Dashboard: https://sentry.io/organizations/morningai/issues/?environment=production
- Alerts: Enabled for critical errors

**Staging**:
- Environment: `staging`
- Dashboard: https://sentry.io/organizations/morningai/issues/?environment=staging
- Alerts: Disabled (testing environment)

### Render Monitoring

**Production Services**:
- Dashboard: https://dashboard.render.com/
- Metrics: CPU, Memory, Request count
- Logs: Real-time log streaming
- Alerts: Enabled for downtime

**Staging Services**:
- Dashboard: https://dashboard.render.com/
- Auto-suspend: Enabled (15 minutes inactivity)
- Cost optimization: ~50% savings

### Supabase Monitoring

**Production Database**:
- Dashboard: https://supabase.com/dashboard/project/[production-id]
- Metrics: Connection pool, Query performance
- Backups: Daily automatic backups

**Staging Database**:
- Dashboard: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- Metrics: Connection pool, Query performance
- Data cleanup: Monthly manual cleanup

---

## 💰 Cost Breakdown

### Production
- **Render Backend**: $7/month (Starter)
- **Render Orchestrator**: $7/month (Starter)
- **Vercel Frontend**: $0/month (Free tier)
- **Supabase Database**: $0/month (Free tier) or $25/month (Pro)
- **Upstash Redis**: $0/month (Free tier) or $10/month (Pay-as-you-go)
- **Total**: ~$14-49/month

### Staging
- **Render Backend**: $7/month (Starter, auto-suspend enabled)
- **Render Orchestrator**: $7/month (Starter, auto-suspend enabled)
- **Supabase Database**: $0/month (Free tier)
- **Upstash Redis**: $0/month (Shared with production)
- **Total**: ~$14/month (effective ~$7/month with auto-suspend)

### Local Development
- **Cost**: $0/month
- **Infrastructure**: Developer workstation only

---

## 🚨 Troubleshooting

### Common Issues

#### Issue: Service won't start
**Check**:
1. Build logs in Render dashboard
2. All required environment variables are set
3. `DATABASE_URL` format is correct
4. `REDIS_URL` is accessible

**Fix**:
```bash
# Test DATABASE_URL locally
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Test REDIS_URL locally
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

#### Issue: Database connection fails
**Check**:
1. Supabase project is running (not paused)
2. `DATABASE_URL` includes correct password
3. Connection pooler is enabled (port 6543)
4. IP allowlist includes Render IPs (if configured)

**Fix**:
- Get fresh `DATABASE_URL` from Supabase dashboard → Settings → Database → Connection string (Pooler)

#### Issue: Redis connection fails
**Check**:
1. `REDIS_URL` uses `rediss://` (double s) for TLS
2. Upstash Redis is accessible
3. Password is correct

**Fix**:
- Get fresh `REDIS_URL` from Upstash dashboard
- Ensure `rediss://` scheme (not `redis://`)

#### Issue: ORCHESTRATOR_JWT_SECRET error
**Error**: `CRITICAL SECURITY ERROR: ORCHESTRATOR_JWT_SECRET environment variable is not set`

**Fix**:
```bash
# Generate new secret (48 characters)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Add to Render environment variables
# Key: ORCHESTRATOR_JWT_SECRET
# Value: <generated-secret>
```

#### Issue: Staging auto-suspend too aggressive
**Fix**:
- Disable auto-suspend in Render dashboard
- Or: Set up cron job to ping `/healthz` every 10 minutes

---

## 📝 Best Practices

### Development
1. **Always test on staging first** before merging to `main`
2. **Use feature branches** for all development
3. **Run tests locally** before pushing
4. **Keep staging data separate** from production

### Deployment
1. **Review staging deployment** before production
2. **Monitor health checks** after deployment
3. **Check Sentry** for errors after deployment
4. **Have rollback plan** ready

### Security
1. **Never commit secrets** to repository
2. **Use different secrets** for each environment
3. **Rotate secrets** quarterly (production) or as needed (staging)
4. **Use TLS** for all external connections (`rediss://`, `https://`)

### Cost Optimization
1. **Enable auto-suspend** for staging services
2. **Clean up staging data** monthly
3. **Monitor usage** in Render/Supabase dashboards
4. **Use free tiers** where possible

---

## 🔗 Quick Links

### Production
- **Backend**: https://morningai-backend-v2.onrender.com
- **Orchestrator**: https://morningai-orchestrator-api.onrender.com
- **Tenant Dashboard**: https://app.gm365.me
- **Owner Console**: https://admin.gm365.me
- **Render Dashboard**: https://dashboard.render.com/

### Staging
- **Backend**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator**: https://morningai-orchestrator-api-stg.onrender.com
- **Supabase**: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- **Setup Guide**: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)

### Documentation
- **Local Setup**: [docs/setup_local.md](setup_local.md)
- **Contributing**: [docs/CONTRIBUTING.md](CONTRIBUTING.md)
- **CI/CD**: [docs/ci_matrix.md](ci_matrix.md)
- **Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)

---

**Last Updated**: 2025-10-28  
**Maintained By**: CTO / DevOps Team  
**Status**: ✅ All environments operational
