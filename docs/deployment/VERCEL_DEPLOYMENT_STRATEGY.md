# Vercel Deployment Strategy

**Document Version**: 2.1  
**Last Updated**: 2025-11-26  
**Related Documents**:
- [ENVIRONMENTS.md](../ENVIRONMENTS.md) - 環境架構文件（單一真實來源）
- [PROJECT_STRUCTURE_REPORT.md](../PROJECT_STRUCTURE_REPORT.md) - 專案結構報告
- [ONBOARDING_GUIDE.md](../ONBOARDING_GUIDE.md) - 新人上手指南

## Overview

This document describes the deployment strategy for the MorningAI monorepo on Vercel, including branch policies, environment configuration, and best practices.

## Deployment Architecture

### Projects

We have **two Vercel projects** in the `morning-ai` team:

1. **morningai** (frontend-dashboard)
   - Project ID: `prj_2vBtvZikIy4hahhoauNC2AKQMtaM`
   - Root: `./` (monorepo root)
   - Output: `handoff/20250928/40_App/frontend-dashboard/dist`

2. **owner-console** (owner-console)
   - Project ID: `prj_KAkdZFlfq0x6xMLQ4OuXgxPrm1up`
   - Root: `handoff/20250928/40_App/owner-console/`
   - Output: `dist`

### Branch Strategy

| Environment | Branch | Deployment Type | URL Pattern |
|------------|--------|----------------|-------------|
| **Production** | `main` | Automatic | `morningai.vercel.app` / custom domain |
| **Preview** | `feature/*`, `fix/*`, `devin/*` | Automatic | `morningai-{hash}.vercel.app` |
| **Skip** | All other branches | None | N/A |

> **Note**: This is a trunk-based development model. There is no persistent `develop` branch. Staging backend services (on Render) deploy from `main`, while frontend staging uses Vercel preview deployments from feature branches.

### Deployment Rules

The deployment logic is controlled by `scripts/vercel-ignore.sh`:

1. **Docs-only changes**: Skip deployment if only `docs/` or `*.md` files changed (uses `VERCEL_GIT_COMMIT_SHA` for robustness)
2. **Preview deployments**: Only allow `feature/*`, `fix/*`, `devin/*` branches
3. **Production deployments**: Only allow `main` branch
4. **All other branches**: Skip deployment

## Configuration Files

### Root vercel.json (morningai project)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "pnpm --filter @morningai/shared-ui build && pnpm --filter frontend-dashboard build",
  "installCommand": "pnpm install --prod=false",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist",
  "ignoreCommand": "bash ./scripts/vercel-ignore.sh",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### owner-console/vercel.json

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "cd ../../../ && pnpm --filter @morningai/shared-ui build && pnpm --filter owner-console build",
  "installCommand": "cd ../../../ && pnpm install --prod=false",
  "outputDirectory": "dist",
  "ignoreCommand": "bash ../../../../scripts/vercel-ignore.sh",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "git": {
    "deploymentEnabled": {
      "gh-pages-storybook": false
    }
  }
}
```

> **Note**: The `git.deploymentEnabled` configuration disables deployments for the `gh-pages-storybook` branch. See [Artifact Branch Deployment Errors](#artifact-branch-deployment-errors) for details.

## Vercel Dashboard Configuration (Option A - Recommended)

### Step 1: Connect GitHub Repository

1. Go to Vercel Dashboard → Projects → morningai → Settings → Git
2. Click "Connect Git Repository"
3. Select `RC918/morningai`
4. Set **Production Branch**: `main`

Repeat for the `owner-console` project.

### Step 2: Staging Environment (Trunk-Based Model)

> **Note**: The project uses a trunk-based development model. There is no persistent `develop` branch.

**Frontend Staging**: Use Vercel preview deployments from feature branches (`feature/*`, `fix/*`, `devin/*`).

**Backend Staging**: Render services (`morningai-backend-v2-stg`, `morningai-orchestrator-api-stg`) deploy from `main` branch with staging environment variables.

**DNS Configuration** (Cloudflare - morningai.me zone):
- CNAME: `staging.morningai.me` → `cname.vercel-dns.com` (DNS-only, proxied=false)
- CNAME: `staging-owner.morningai.me` → `cname.vercel-dns.com` (DNS-only, proxied=false)

> **Historical Note**: Branch aliases for `develop` were configured on 2025-11-04 but the `develop` branch was later removed in favor of trunk-based development.

### Step 3: Configure Ignored Build Step (Optional)

If you prefer to manage deployment rules in the Dashboard instead of `vercel-ignore.sh`:

1. Go to Vercel Dashboard → Projects → morningai → Settings → Git
2. Under "Ignored Build Step", add:
   ```bash
   if git diff --name-only "$VERCEL_GIT_COMMIT_SHA^!" | grep -E -v '^(docs/|.*\.md$)' >/dev/null; then exit 1; else echo "Skipping docs-only change"; exit 0; fi
   ```

**Note**: If using Dashboard Ignored Build Step, remove `ignoreCommand` from `vercel.json` to avoid conflicts.

### Step 4: Configure Environment Variables

#### Production Environment

| Variable | Value | Target |
|----------|-------|--------|
| `VITE_API_BASE_URL` | `https://api.morningai.app` | Production |
| `VITE_SENTRY_DSN` | `https://...@sentry.io/...` | Production |
| `VITE_SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Production |
| `VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE` | `0.1` | Production |
| `VITE_SUPABASE_URL` | `https://...supabase.co` | Production |
| `VITE_SUPABASE_ANON_KEY` | `eyJ...` | Production |
| `VITE_TOLGEE_API_KEY` | `tgpak_...` | Production |
| `VITE_TOLGEE_PROJECT_ID` | `...` | Production |
| `VITE_TOLGEE_API_URL` | `https://app.tolgee.io` | Production |

#### Staging Environment

| Variable | Value | Target |
|----------|-------|--------|
| `VITE_API_BASE_URL` | `https://staging-api.morningai.app` | Preview |
| `VITE_SENTRY_DSN` | `https://...@sentry.io/...` | Preview |
| `VITE_SENTRY_TRACES_SAMPLE_RATE` | `1.0` | Preview |
| `VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE` | `1.0` | Preview |
| `STAGING_TEST_EMAIL` | `test@example.com` | Preview |
| `STAGING_TEST_PASSWORD` | `...` | Preview |

#### Preview Environment

Same as Staging, but with lighter Sentry sampling and test credentials.

### Step 5: Set Root Directory (Recommended)

To simplify build paths:

1. Go to Vercel Dashboard → Projects → morningai → Settings → General
2. Set **Root Directory**: `handoff/20250928/40_App/frontend-dashboard`
3. Update `vercel.json`:
   ```json
   {
     "buildCommand": "pnpm --filter @morningai/shared-ui build && pnpm --filter frontend-dashboard build",
     "installCommand": "pnpm install --prod=false",
     "outputDirectory": "dist"
   }
   ```

Repeat for `owner-console` with Root Directory: `handoff/20250928/40_App/owner-console`.

## Environment Variables Audit

### Current State (API Query Results)

**morningai project** (6 variables):
- `NODE_ENV`
- `OPENAI_MAX_DAILY_COST`
- `VITE_API_BASE_URL`
- `VITE_SENTRY_DSN`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_SUPABASE_URL`

**owner-console project** (1 variable):
- `VITE_API_BASE_URL`

### Frontend Code Usage (Verified)

The frontend code only uses the following environment variables:
- `import.meta.env.DEV`
- `import.meta.env.MODE`
- `import.meta.env.PROD`
- `import.meta.env.VITE_API_BASE_URL`
- `import.meta.env.VITE_FEATURES`
- `import.meta.env.VITE_PHASE`
- `import.meta.env.VITE_SENTRY_DSN`
- `import.meta.env.VITE_SUPABASE_ANON_KEY`
- `import.meta.env.VITE_SUPABASE_URL`
- `import.meta.env.VITE_USE_MOCK`

### Backend-Style Variables (Not Used in Frontend)

The following variables appear in the Vercel Dashboard screenshots but are **not used** in the frontend code:
- `JWT_SECRET_KEY`
- `COOKIE_SECURE`
- `COOKIE_DOMAIN`
- `COOKIE_SAMESITE`
- `SENTRY_AUTH_TOKEN`
- `SENTRY_ORG`
- `SENTRY_PROJECT`
- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`

**Recommendation**: These backend-style variables should be:
1. **Removed from Vercel frontend projects** (security risk - exposed to client)
2. **Moved to backend infrastructure** (Render, Supabase, or backend environment)
3. **Kept only if used by Vercel serverless functions** (if any exist)

### Missing Variables (Recommended to Add)

Based on the codebase analysis, consider adding:
- `VITE_FEATURES` - Feature flags
- `VITE_PHASE` - Current phase (for phase-based UI)
- `VITE_USE_MOCK` - Enable mock data for development
- `VITE_OWNER_CONSOLE_API` - Owner console API endpoint
- `VITE_TOLGEE_API_KEY` - Tolgee i18n API key
- `VITE_TOLGEE_PROJECT_ID` - Tolgee project ID
- `VITE_TOLGEE_API_URL` - Tolgee API URL
- `ENABLE_MOCK_USERS` - Enable mock users for testing

## Deployment Workflow

### For Developers

1. **Feature Development**:
   ```bash
   git checkout -b feature/my-feature
   # Make changes
   git push origin feature/my-feature
   # Create PR → Vercel automatically creates preview deployment
   ```

2. **Production Deployment** (Trunk-Based):
   ```bash
   # Merge feature branch directly to main via PR
   git checkout main
   git pull origin main
   # Create PR from feature branch → main
   # After PR approval and merge, Vercel automatically deploys to production
   ```

> **Note**: This is a trunk-based development model. Features are merged directly to `main` after review. Backend staging services on Render use `main` branch with staging environment variables.

### For CI/CD

The deployment is fully automated:
- **Preview**: Automatic on PR creation for `feature/*`, `fix/*`, `devin/*` branches
- **Production**: Automatic on push to `main` branch

## Post-Deployment Smoke Tests

After each deployment, run these smoke tests to verify functionality:

### Backend API Health Check
```bash
# Production
curl https://morningai-backend-v2.onrender.com/healthz

# Staging
curl https://morningai-backend-v2-stg.onrender.com/healthz

# Expected: {"status": "healthy", "phase": "Phase 8", ...}
```

### Monitoring Dashboard Endpoint
```bash
# Production
curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard

# Staging
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard

# Expected: 200 OK with metrics or 503 if both Redis+DB down
```

### Frontend Accessibility
- **Production**: Visit https://morningai.vercel.app
- **Staging**: Visit https://staging.morningai.me
- **Owner Console Staging**: Visit https://staging-owner.morningai.me

### Degradation Testing (Staging Only)

**Note**: These tests require backend access and should only be run in staging/test environments.

1. **Simulate Redis Failure** (see [Monitoring Troubleshooting Guide](./troubleshooting-monitoring.md)):
   - Expected: 200 OK with fallback metrics (`available: false`, `source: 'fallback'`)

2. **Simulate DB Failure** (see integration tests):
   - Expected: 200 OK with degraded status + critical alert

3. **Simulate Dual Failure** (see integration tests):
   - Expected: 503 Service Unavailable with `ServiceUnavailableError`

**Reference**: See `api-backend/tests/test_dashboard_503_integration.py` for test patterns.

## Monitoring and Observability

### Vercel Dashboard

- **Deployments**: View all deployments at `vercel.com/morning-ai/morningai/deployments`
- **Analytics**: View performance metrics at `vercel.com/morning-ai/morningai/analytics`
- **Logs**: View build and runtime logs at `vercel.com/morning-ai/morningai/logs`

### Sentry Integration

All deployments send errors and performance data to Sentry:
- **Production**: Lower sampling rate (10%)
- **Staging/Preview**: Higher sampling rate (100%)

## Troubleshooting

### Deployment Not Triggering

1. Check if branch matches the deployment rules in `vercel-ignore.sh`
2. Verify GitHub is connected in Vercel Dashboard
3. Check if only docs were changed (will skip deployment)

### Staging Domain Shows "404: DEPLOYMENT_NOT_FOUND"

**Symptom**: Accessing `staging.morningai.me` or `staging-owner.morningai.me` shows a 404 error with code `DEPLOYMENT_NOT_FOUND`.

**Root Cause**: The staging domain aliases were configured for a `develop` branch that no longer exists (trunk-based model).

**Solution**:
1. Use Vercel preview deployments from feature branches for frontend staging
2. Backend staging is available at Render services (`morningai-backend-v2-stg.onrender.com`)
3. For a stable frontend staging URL, configure a branch alias to point to `main` or use preview deployment URLs directly

### Build Failures

1. Check build logs in Vercel Dashboard
2. Verify `pnpm` version matches `packageManager` in `package.json`
3. Ensure `@morningai/shared-ui` builds before the app

### Environment Variables Not Working

1. Verify variable names start with `VITE_` prefix
2. Check variable is set for the correct environment (Production/Preview/Development)
3. Rebuild the deployment after adding new variables

### Artifact Branch Deployment Errors

**Symptom**: Deployment fails with error `The specified Root Directory "handoff/20250928/40_App/owner-console" does not exist` on branches like `gh-pages-storybook`.

**Root Cause**: Artifact branches (like `gh-pages-storybook` for GitHub Pages) contain only static build files, not the source code directory structure. Vercel validates the `rootDirectory` exists **before** running the `ignoreCommand`, so the ignore logic never gets a chance to skip the build.

**Solution**: Use `git.deploymentEnabled` in `vercel.json` to disable deployments for artifact branches at an earlier stage:

```json
{
  "git": {
    "deploymentEnabled": {
      "gh-pages-storybook": false
    }
  }
}
```

This configuration prevents Vercel from attempting to deploy the specified branch entirely, avoiding the `rootDirectory` validation error.

**When to use this pattern**:
- GitHub Pages artifact branches (e.g., `gh-pages`, `gh-pages-storybook`)
- Any branch that contains only build artifacts without source code structure
- Branches that should never trigger Vercel deployments

**Reference**: [Vercel Git Configuration Documentation](https://vercel.com/docs/project-configuration/git-configuration#git.deploymentenabled)

## Security Considerations

1. **Never expose backend secrets** in Vercel frontend projects
2. **Use `VITE_` prefix** for all client-side environment variables
3. **Rotate secrets regularly** using the Secret Rotation Policy
4. **Audit environment variables** quarterly to remove unused variables

## Future Improvements

1. **Turborepo Remote Caching**: Enable on Vercel to speed up builds
2. **Custom Domains**: Configure production domains (e.g., `app.morningai.com`)
3. **Preview Deployment Comments**: Enable automatic PR comments with preview URLs
4. **Deployment Protection**: Require approval for production deployments
5. **Environment Variable Groups**: Use groups for shared variables across projects

## References

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel CLI](https://vercel.com/docs/cli)
- [Vercel API](https://vercel.com/docs/rest-api)
- [Project Roadmap](/.github/projects/cto-strategic-roadmap-q4-2025-q2-2026.yml)
- [Environment Variables Schema](/config/env.schema.yaml)

---

**Last Updated**: 2025-12-16
**Owner**: CTO + DevOps Team
**Status**: Active

**近期重要更新** (2025-12-16):

*Vercel 配置更新：*
- **PR #2562**: 新增 `git.deploymentEnabled` 配置禁用 `gh-pages-storybook` 分支部署
  - 解決 artifact branch 導致的 rootDirectory 驗證錯誤
  - 新增 Troubleshooting 文檔：[Artifact Branch Deployment Errors](#artifact-branch-deployment-errors)

**近期重要更新** (2025-12-02 至 2025-12-03):

*注意：以下環境變數為後端/Worker 專用，不應加入 Vercel 前端專案：*
- `DISABLE_GEMINI3` (boolean) - Gemini 3 實驗緊急開關 (PR #1804)
- `REASONING_MODE_ENABLED` (boolean) - Gemini 3 推理模式 (PR #1794)
- `RQ_MAX_JOBS` (integer) - Worker 記憶體管理 (PR #1790, #1797)
- `WORKER_HEARTBEAT_INTERVAL` (integer) - Worker 心跳間隔 (PR #1798)
- `WORKER_HEARTBEAT_TTL` (integer) - 心跳 key 過期時間 (PR #1798)

*前端相關更新：*
- **PR #1802**: DashboardHeader 和 Sidebar Storybook stories
- **PR #1801**: iotask 元件樣式更新 (Button, Badge, Card, Input, Progress)
- **PR #1796**: iotask 設計系統升級 - 設計令牌更新

*CI/CD 更新：*
- **PR #1803**: 新增 `.github/workflows/gemini3-reviewer-gate.yml` CI 工作流程

**近兩日重要更新** (2025-11-25 至 2025-11-26):
- **PR #1548**: Frontend Dashboard 代碼分割優化 - 20% bundle 減少 + Lighthouse CI color-contrast 修復
  - Path: `handoff/20250928/40_App/frontend-dashboard/`
- **PR #1562**: RQ Job Timeout 配置 - 新增 `RQ_JOB_TIMEOUT` 環境變數
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
- **PR #1547**: AppleButton 遷移到 shared-ui - Adapter pattern 實作
  - Path: `packages/shared-ui/`
- **PR #1546**: Phase 2 UI 完成 - 情感顏色、AppleButton 對齊、Spring 動畫
- **PR #1545**: P1 情感顏色 + AgentExecutionLogs Apple 設計
- **PR #1544**: Apple 設計系統全局應用
- **PR #1543**: Dark Mode 禁用 + PlatformSettings 卡片樣式修復
- **LoginPage UX 改進**: 使用 Apple 設計系統全面重構

**先前重要更新** (2025-11-12 至 2025-11-19):
- Phase 1 (B): LLM Planner 整合與 ContextManager 實作 (#1353)
- Phase 2: Code Generation Workflow with Security Validation (#1347)
- Phase 1.5: Agent Evaluation Monitoring Dashboard (#1337)
- Design Token Migration 完成 - Tailwind config + semantic tokens (#1323, #1331, #1332)
- Owner Console E2E 測試完成 (#1345, #1348)
- Lighthouse CI 設置文檔與 workflow_dispatch 觸發器 (#1346)
