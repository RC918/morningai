# Staging Environment Setup Guide

## ✅ Phase 1 Complete (已完成)

### What's Been Done

1. **✅ `develop` Branch Created**
   - Branch: `develop` 
   - Remote: https://github.com/RC918/morningai/tree/develop
   - Status: Pushed and ready

2. **✅ Staging CI Workflow**
   - File: `.github/workflows/staging-deploy.yml`
   - Triggers: Push/PR to `develop` branch
   - Tests: Backend (pytest + coverage), Frontend (build), Smoke tests
   - Environment: `ENVIRONMENT=staging`

3. **✅ Staging Supabase Project**
   - Project Name: `morningai-staging`
   - Project ID: `dckisglnlemvpvmyvnut`
   - URL: https://dckisglnlemvpvmyvnut.supabase.co
   - Status: Provisioning complete

4. **✅ Credentials Secured**
   - STAGING_SUPABASE_URL: ✅
   - STAGING_SUPABASE_ANON_KEY: ✅ (stored securely)
   - STAGING_SUPABASE_SERVICE_ROLE_KEY: ✅ (stored securely)

---

## ✅ Phase 2 Complete (已完成)

### What's Been Done

1. **✅ Backend Staging Service**
   - Service Name: `morningai-backend-v2-stg`
   - URL: https://morningai-backend-v2-stg.onrender.com
   - Branch: `develop`
   - Runtime: Python 3
   - Status: ✅ Healthy
   - Database: ✅ Connected (Supabase PostgreSQL)
   - Redis: ✅ Connected (Upstash, TLS enabled)

2. **✅ Orchestrator Staging Service**
   - Service Name: `morningai-orchestrator-api-stg`
   - URL: https://morningai-orchestrator-api-stg.onrender.com
   - Branch: `develop`
   - Runtime: Docker
   - Status: ✅ Healthy
   - Redis: ✅ Connected (TLS)
   - Queue: ✅ Active (354 tasks)

3. **✅ Environment Variables Configured**
   - ORCHESTRATOR_JWT_SECRET: ✅ (48 characters)
   - REDIS_URL: ✅ (rediss:// with TLS)
   - DATABASE_URL: ✅ (Staging Supabase)
   - All required variables: ✅ Set

4. **✅ Health Checks Verified**
   - Backend `/healthz`: ✅ Passing
   - Orchestrator `/health`: ✅ Passing
   - All services operational: ✅

---

## 📋 Phase 2: Render Staging Services Setup (完整記錄)

### Overview

Create 2 staging services on Render to mirror critical production services:
- `morningai-backend-v2-stg` (Flask API)
- `morningai-orchestrator-api-stg` (FastAPI)

**Cost**: ~$7/month (with auto-suspend enabled)

---

### Service 1: Backend API Staging

#### Basic Configuration

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Click "New +" → "Web Service"**
3. **Connect Repository**: `RC918/morningai`

#### Service Settings

| Setting | Value |
|---------|-------|
| **Name** | `morningai-backend-v2-stg` |
| **Region** | Oregon (US West) or Tokyo (Asia) |
| **Branch** | `develop` |
| **Root Directory** | `handoff/20250928/40_App/api-backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 src.main:app` |
| **Instance Type** | Starter ($7/month) |
| **Auto-Deploy** | Yes (on push to `develop`) |

#### Environment Variables

**Critical Variables** (必須設定):

```bash
# Environment
ENVIRONMENT=staging

# Database (Staging Supabase)
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_ANON_KEY=[從 Devin 取得]
SUPABASE_SERVICE_ROLE_KEY=[從 Devin 取得]

# Redis (使用現有 Upstash Redis)
REDIS_URL=[從生產環境複製]

# Database Connection Pool
DB_POOL_SIZE=5
DB_POOL_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Security
JWT_SECRET_KEY=[生成新的 32+ 字元密鑰]
SECRET_KEY=[生成新的 32+ 字元密鑰]
MASTER_ENCRYPTION_KEY=[生成新的 32+ 字元密鑰]

# Monitoring
SENTRY_DSN=[從生產環境複製]
SENTRY_ENVIRONMENT=staging

# Testing
TESTING=false
```

**Optional Variables** (可選):

```bash
# LLM (可使用較便宜的模型)
OPENAI_API_KEY=[從生產環境複製]
ANTHROPIC_API_KEY=[從生產環境複製]

# External Services (可選)
TELEGRAM_BOT_TOKEN=[從生產環境複製或留空]
SLACK_WEBHOOK_URL=[留空或使用測試 webhook]

# Feature Flags
HITL_APPROVAL_ENABLED=false
```

#### Advanced Settings

1. **Auto-Suspend**: 
   - Enable "Suspend after 15 minutes of inactivity"
   - Saves ~50% cost ($7 → $3.50/month)

2. **Health Check Path**: `/healthz`

3. **Disk**: 
   - Not needed (using Supabase for persistence)

---

### Service 2: Orchestrator API Staging

#### Basic Configuration

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Click "New +" → "Web Service"**
3. **Connect Repository**: `RC918/morningai`

#### Service Settings

| Setting | Value |
|---------|-------|
| **Name** | `morningai-orchestrator-api-stg` |
| **Region** | Oregon (US West) or Tokyo (Asia) |
| **Branch** | `develop` |
| **Root Directory** | `.` (repository root) |
| **Runtime** | Docker |
| **Docker Build Context** | `.` |
| **Dockerfile Path** | `orchestrator/Dockerfile` |
| **Instance Type** | Starter ($7/month) |
| **Auto-Deploy** | Yes (on push to `develop`) |

#### Environment Variables

**Critical Variables** (必須設定):

```bash
# Environment
ENVIRONMENT=staging
PORT=8000

# Security (REQUIRED)
ORCHESTRATOR_JWT_SECRET=[生成 48+ 字元密鑰]

# Redis (REQUIRED)
REDIS_URL=[從生產環境複製，必須是 rediss:// 開頭]

# Optional but Recommended
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
ORCHESTRATOR_CORS_ORIGINS=https://morningai-staging.vercel.app,http://localhost:5173
SENTRY_ENVIRONMENT=staging
LOG_LEVEL=INFO
```

**重要提醒**:
- `ORCHESTRATOR_JWT_SECRET`: 必須至少 32 字元，建議 48 字元
- `REDIS_URL`: 必須使用 `rediss://` (雙 s) 表示 TLS 加密
- 每個 Render 服務都有獨立的環境變數，需要單獨設定

---

### Service URLs (部署後)

After deployment, you'll get:

- **Backend Staging**: `https://morningai-backend-v2-stg.onrender.com`
- **Orchestrator Staging**: `https://morningai-orchestrator-api-stg.onrender.com`

---

## 🔐 Generating Secret Keys

Use these commands to generate secure keys:

```bash
# JWT_SECRET_KEY (32+ characters)
openssl rand -hex 32

# SECRET_KEY (32+ characters)
openssl rand -hex 32

# MASTER_ENCRYPTION_KEY (32+ characters)
openssl rand -hex 32
```

---

## 🌐 Phase 3: Vercel Frontend Staging (可選)

### Option A: Automatic Preview Deployments (推薦)

Vercel automatically creates preview deployments for all branches:

1. **Push to `develop` branch** → Vercel auto-deploys
2. **Preview URL**: `https://morningai-git-develop-rc918.vercel.app`
3. **No configuration needed** ✅

### Option B: Custom Staging Domain (進階)

If you want a fixed staging URL:

1. **Go to Vercel Dashboard** → Project Settings
2. **Git** → Add `develop` as Production Branch
3. **Domains** → Add custom domain: `staging.morningai.app`
4. **Environment Variables** (for `develop` branch):

```bash
VITE_API_BASE_URL=https://morningai-backend-v2-stg.onrender.com
VITE_ORCHESTRATOR_URL=https://morningai-orchestrator-api-stg.onrender.com
VITE_ENVIRONMENT=staging
SENTRY_ENVIRONMENT=staging
```

---

## 🧪 Testing Staging Environment

### 1. Health Checks

```bash
# Backend
curl https://morningai-backend-v2-stg.onrender.com/healthz

# Expected response:
{
  "phase": "Phase 8",
  "version": "8.0.0",
  "status": "healthy",
  "database": "connected"
}

# Orchestrator
curl https://morningai-orchestrator-api-stg.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "environment": "staging"
}
```

### 2. Database Connection Test

```bash
# Test Supabase connection
curl -X POST https://morningai-backend-v2-stg.onrender.com/api/test/db \
  -H "Content-Type: application/json"

# Should return: {"status": "connected", "database": "staging"}
```

### 3. End-to-End Test

```bash
# Trigger FAQ generation (async task)
curl -X POST https://morningai-backend-v2-stg.onrender.com/api/agent/faq \
  -H "Content-Type: application/json" \
  -d '{"question": "What is MorningAI?"}'

# Response (202 Accepted):
{
  "task_id": "abc123",
  "status": "queued",
  "trace_id": "trace-xyz"
}

# Poll task status
curl https://morningai-backend-v2-stg.onrender.com/api/agent/tasks/abc123

# Response (when complete):
{
  "task_id": "abc123",
  "status": "completed",
  "result": "..."
}
```

---

## 🔄 Deployment Workflow

### Development → Staging → Production

```mermaid
graph LR
    A[Feature Branch] -->|PR| B[develop]
    B -->|Auto-deploy| C[Staging Environment]
    C -->|Manual Test| D{Tests Pass?}
    D -->|Yes| E[PR to main]
    E -->|Manual Approval| F[Production]
    D -->|No| A
```

### Step-by-Step

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. **Develop & Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/my-feature
   ```

3. **Create PR to `develop`**
   - GitHub will run staging CI checks
   - Auto-deploys to Render staging services

4. **Test on Staging**
   - Verify at `https://morningai-backend-v2-stg.onrender.com`
   - Run manual tests
   - Check logs in Render dashboard

5. **Merge to `develop`**
   - Staging environment updated

6. **Create PR to `main`** (when ready for production)
   - Requires manual approval
   - Deploys to production services

---

## 📊 Monitoring Staging

### Render Dashboard

- **Logs**: https://dashboard.render.com/web/[service-id]/logs
- **Metrics**: CPU, Memory, Request count
- **Events**: Deploys, Suspends, Resumes

### Sentry (Error Tracking)

- **Environment Filter**: `staging`
- **Dashboard**: https://sentry.io/organizations/morningai/issues/?environment=staging

### Database (Supabase)

- **Dashboard**: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- **Table Editor**: View/edit staging data
- **SQL Editor**: Run queries
- **Logs**: API logs, Postgres logs

---

## 🚨 Troubleshooting

### Issue: Service won't start

**Check**:
1. Build logs in Render dashboard
2. Verify all required environment variables are set
3. Check `DATABASE_URL` format: `postgresql://...`
4. Verify `REDIS_URL` is accessible

**Fix**:
```bash
# Test DATABASE_URL locally
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"
```

### Issue: Database connection fails

**Check**:
1. Supabase project is running (not paused)
2. `DATABASE_URL` includes correct password
3. Connection pooler is enabled (port 6543)

**Fix**:
- Get fresh `DATABASE_URL` from Supabase dashboard → Settings → Database → Connection string (Pooler)

### Issue: Auto-suspend too aggressive

**Fix**:
- Disable auto-suspend in Render dashboard
- Or: Set up cron job to ping `/healthz` every 10 minutes

### Issue: CI checks fail on `develop`

**Check**:
1. `.github/workflows/staging-deploy.yml` syntax
2. Test coverage threshold (74%+)
3. Environment variables in CI (REDIS_URL, TESTING=true)

**Fix**:
```bash
# Run tests locally
cd handoff/20250928/40_App/api-backend
export REDIS_URL=redis://localhost:6379/0
export TESTING=true
export ENVIRONMENT=staging
pytest --cov=src --cov-fail-under=74 -v
```

---

## 📝 Checklist

### Phase 1 (完成 ✅)
- [x] Create `develop` branch
- [x] Push `develop` to remote
- [x] Create staging CI workflow
- [x] Create Supabase staging project
- [x] Receive staging credentials

### Phase 2 (完成 ✅)
- [x] Create `morningai-backend-v2-stg` on Render
- [x] Configure backend environment variables
- [x] Test backend health check
- [x] Create `morningai-orchestrator-api-stg` on Render
- [x] Configure orchestrator environment variables (ORCHESTRATOR_JWT_SECRET, REDIS_URL)
- [x] Fix Docker configuration for orchestrator
- [x] Test orchestrator health check
- [x] Verify database connections
- [x] Verify Redis connections (TLS)
- [x] Verify all services operational

### Phase 3 (可選 - 建議暫不執行)
- [ ] Configure Vercel staging domain
- [ ] Add staging environment variables to Vercel
- [ ] Test end-to-end flow

**決策**: 目前不建立前端 staging，使用本地前端 + staging backend 測試即可

### Phase 4 (未來)
- [ ] Add remaining 4 services (workers) to staging
- [ ] Set up staging monitoring dashboard
- [ ] Document staging runbooks
- [ ] Create staging data seed scripts
- [ ] Set up automated staging data cleanup (monthly)

---

## 🔗 Quick Links

- **Staging Branch**: https://github.com/RC918/morningai/tree/develop
- **Staging CI**: https://github.com/RC918/morningai/actions/workflows/staging-deploy.yml
- **Supabase Dashboard**: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- **Render Dashboard**: https://dashboard.render.com/
- **Staging Environment Plan**: `docs/ops/staging-environment-plan.md` (500+ lines)

---

## 💡 Best Practices

1. **Always test on staging first** before merging to `main`
2. **Use staging for risky changes** (DATABASE_URL, RLS, 2FA)
3. **Keep staging data separate** from production
4. **Monitor staging costs** (should be <$10/month)
5. **Clean up old staging data** monthly
6. **Document staging-specific issues** in this guide

---

## 📞 Support

If you encounter issues:

1. **Check Render logs** first
2. **Check Supabase logs** for database issues
3. **Check GitHub Actions logs** for CI issues
4. **Ask Devin** for assistance with configuration

---

## 🎉 Staging Environment Complete!

**Status**: ✅ **Fully Operational**

**Services**:
- ✅ Backend Staging: https://morningai-backend-v2-stg.onrender.com
- ✅ Orchestrator Staging: https://morningai-orchestrator-api-stg.onrender.com
- ✅ Staging Database: Supabase PostgreSQL (dckisglnlemvpvmyvnut)
- ✅ Staging Redis: Upstash (shared with production, key prefix: `stg:`)

**Last Updated**: 2025-10-28
**Status**: Phase 1 & 2 Complete ✅, Ready for Development Use
