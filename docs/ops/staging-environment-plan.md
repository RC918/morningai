# Staging Environment Plan

**Document Date**: 2025-10-28  
**Status**: Proposed  
**Owner**: CTO  
**Related**: ADR-003 (Database-of-Record)

---

## Executive Summary

This document outlines the implementation plan for establishing a staging environment for the MorningAI platform. Currently, all updates deploy directly to production, creating significant risk. This plan provides a minimal viable staging setup that can be implemented in 2-3 hours while keeping costs low (~$7/month additional).

**Key Benefits**:
- 80%+ risk reduction for production deployments
- Safe testing environment for high-risk changes (DATABASE_URL, RLS, 2FA)
- Confidence in deployment process before production rollout
- Minimal cost increase (~15% of current infrastructure spend)

---

## Current State Analysis

### Deployment Configuration

**Production Services** (render.yaml):
1. `morningai-backend-v2` - Flask API (Python)
2. `morningai-agent-worker` - RQ Worker (Python)
3. `morningai-orchestrator-api` - FastAPI (Docker)
4. `morningai-worker-dashboard` - Ops Agent Dashboard (Python)
5. `morningai-ops-agent-worker` - Ops Agent Worker (Python)
6. `braintrust-processor` - Monitoring (Docker)

**Frontend** (vercel.json):
- `frontend-dashboard` - React PWA deployed to Vercel

**Current Risk**:
- ❌ No staging environment
- ❌ All changes deploy directly to production
- ❌ No pre-production validation
- ❌ Single branch deployment (`main` → production)

---

## Proposed Architecture

### Branch Strategy

```
main (production)
  ↑
  │ PR + Manual Approval
  │
develop (staging)
  ↑
  │ PR + Auto CI
  │
feature/* (development)
```

**Branch Policies**:
- `main`: Protected, requires PR approval, deploys to production
- `develop`: Protected, auto-deploys to staging, requires passing CI
- `feature/*`: Development branches, PR to `develop`

### Environment Separation

| Environment | Branch | Database | Redis | Sentry | Domain |
|-------------|--------|----------|-------|--------|--------|
| **Production** | `main` | Supabase Production | Upstash Production | `ENVIRONMENT=production` | `api.morningai.app` |
| **Staging** | `develop` | Supabase Staging | Upstash Staging | `ENVIRONMENT=staging` | `api-stg.morningai.app` |
| **Development** | `feature/*` | SQLite Local | Redis Local | `ENVIRONMENT=development` | `localhost:5000` |

---

## Implementation Plan

### Phase 1: Minimal Viable Staging (Today - 2-3 hours)

#### Step 1: Create `develop` Branch (10 minutes)

```bash
cd ~/repos/morningai
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop
```

**GitHub Branch Protection**:
1. Go to Settings → Branches → Add rule
2. Branch name pattern: `develop`
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging

#### Step 2: Create Staging Services on Render (30 minutes)

**Services to Create** (only 2 critical services):

**2.1 Backend API Staging**
- Service Name: `morningai-backend-v2-stg`
- Branch: `develop`
- Instance Type: Starter (smallest)
- Auto-suspend: Enabled (after 15 min inactivity)
- Environment Variables:
  ```yaml
  ENVIRONMENT: staging
  FLASK_ENV: staging
  DATABASE_URL: <STAGING_SUPABASE_URL>
  REDIS_URL: <STAGING_REDIS_URL>
  SENTRY_DSN: <SAME_AS_PROD>
  SENTRY_ENVIRONMENT: staging
  SECRET_KEY: <GENERATE_NEW>
  JWT_SECRET_KEY: <GENERATE_NEW>
  ADMIN_PASSWORD: <GENERATE_NEW>
  CORS_ORIGINS: http://localhost:5173,https://staging-frontend.morningai.app
  APP_VERSION: 8.0.0-staging
  ```

**2.2 Orchestrator API Staging**
- Service Name: `morningai-orchestrator-api-stg`
- Branch: `develop`
- Instance Type: Starter
- Auto-suspend: Enabled
- Environment Variables:
  ```yaml
  ENVIRONMENT: staging
  ORCHESTRATOR_JWT_SECRET: <GENERATE_NEW>
  REDIS_URL: <STAGING_REDIS_URL>
  LOG_LEVEL: DEBUG
  ```

#### Step 3: Configure Vercel Staging (20 minutes)

**Vercel Project Settings**:
1. Go to Project Settings → Git
2. Configure Preview Deployments:
   - Production Branch: `main`
   - Preview Branch: `develop`
3. Add Preview Alias:
   - Alias: `staging-frontend.morningai.app`
   - Branch: `develop`

**Staging Environment Variables** (Vercel):
```yaml
VITE_API_BASE_URL: https://morningai-backend-v2-stg.onrender.com
VITE_SENTRY_DSN: <SAME_AS_PROD>
SENTRY_ENVIRONMENT: staging
```

#### Step 4: Create Staging Database (30 minutes)

**Option A: Separate Supabase Project (Recommended)**
1. Create new Supabase project: `morningai-staging`
2. Copy schema from production (without data)
3. Use Supabase CLI:
   ```bash
   supabase db dump --db-url <PROD_URL> --schema-only > schema.sql
   psql <STAGING_URL> < schema.sql
   ```
4. Configure RLS policies (same as production)

**Option B: Same Supabase, Different Schema**
1. Create schema: `CREATE SCHEMA staging;`
2. Copy tables to staging schema
3. Update DATABASE_URL: `postgresql://...?schema=staging`

**Seed Data** (staging only):
```sql
-- Create test users
INSERT INTO users (email, role) VALUES 
  ('test@morningai.app', 'owner'),
  ('dev@morningai.app', 'admin');

-- Create test tenants
INSERT INTO tenants (name, plan) VALUES 
  ('Test Tenant 1', 'free'),
  ('Test Tenant 2', 'pro');
```

#### Step 5: Create Staging Redis (15 minutes)

**Upstash Redis**:
1. Create new database: `morningai-staging`
2. Region: Same as production
3. Copy connection details to Render env vars

**Alternative**: Use same Redis with different key prefix
```python
REDIS_KEY_PREFIX = os.environ.get('ENVIRONMENT', 'production')
redis_key = f"{REDIS_KEY_PREFIX}:session:{session_id}"
```

#### Step 6: Add Staging CI Workflow (30 minutes)

Create `.github/workflows/deploy-staging.yml`:

```yaml
name: Deploy to Staging

on:
  push:
    branches: [develop]
  pull_request:
    branches: [develop]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd handoff/20250928/40_App/api-backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd handoff/20250928/40_App/api-backend
          pytest tests/ -v
      
      - name: Validate env schema
        run: python config/env_schema_validator.py

  smoke-test-staging:
    runs-on: ubuntu-latest
    needs: lint-and-test
    if: github.event_name == 'push'
    steps:
      - name: Wait for Render deployment
        run: sleep 60
      
      - name: Health check backend
        run: |
          response=$(curl -s -o /dev/null -w "%{http_code}" https://morningai-backend-v2-stg.onrender.com/healthz)
          if [ $response -ne 200 ]; then
            echo "Backend health check failed: $response"
            exit 1
          fi
          echo "✅ Backend health check passed"
      
      - name: Health check orchestrator
        run: |
          response=$(curl -s -o /dev/null -w "%{http_code}" https://morningai-orchestrator-api-stg.onrender.com/health)
          if [ $response -ne 200 ]; then
            echo "Orchestrator health check failed: $response"
            exit 1
          fi
          echo "✅ Orchestrator health check passed"
      
      - name: Verify staging environment
        run: |
          response=$(curl -s https://morningai-backend-v2-stg.onrender.com/healthz)
          echo "$response" | jq -e '.phase == "Phase 8"'
          echo "✅ Staging environment verified"
```

#### Step 7: Add Production Approval Gate (15 minutes)

Create `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  require-approval:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://morningai-backend-v2.onrender.com
    steps:
      - name: Deployment approved
        run: echo "✅ Production deployment approved"
      
      - name: Post-deploy health check
        run: |
          sleep 60
          curl -f https://morningai-backend-v2.onrender.com/healthz
```

**GitHub Environment Setup**:
1. Go to Settings → Environments → New environment
2. Name: `production`
3. Enable:
   - ✅ Required reviewers (add yourself)
   - ✅ Wait timer: 5 minutes

---

### Phase 2: Extended Staging (Next Week - Optional)

#### Additional Services
- `morningai-agent-worker-stg`
- `morningai-worker-dashboard-stg`
- `morningai-ops-agent-worker-stg`
- `braintrust-processor-stg`

#### Enhanced Testing
- Integration tests against staging
- Load testing with k6
- Security scanning with OWASP ZAP

---

## Deployment Workflow

### Development → Staging → Production

```
1. Developer creates feature branch
   └─> git checkout -b feature/new-feature

2. Developer opens PR to develop
   └─> CI runs: lint, tests, env validation
   └─> Auto-deploy to staging on merge

3. Staging validation
   └─> Smoke tests run automatically
   └─> Manual QA testing
   └─> Verify logs in Sentry (staging environment)

4. Promote to production
   └─> Create PR: develop → main
   └─> CI runs: full test suite
   └─> Manual approval required
   └─> Deploy to production
   └─> Post-deploy health checks
```

### Rollback Procedure

**Staging Rollback**:
```bash
# Revert commit on develop
git revert <commit-hash>
git push origin develop

# Or force rollback to previous commit
git reset --hard <previous-commit>
git push origin develop --force
```

**Production Rollback**:
```bash
# Never force push to main!
# Instead, revert the problematic commit
git checkout main
git revert <commit-hash>
git push origin main

# Or create hotfix branch
git checkout -b hotfix/rollback-issue
git revert <commit-hash>
# Create PR to main
```

---

## Cost Analysis

### Current Costs (Production Only)

| Service | Type | Cost/Month |
|---------|------|------------|
| Backend API | Starter | $7 |
| Agent Worker | Starter | $7 |
| Orchestrator API | Starter | $7 |
| Worker Dashboard | Starter | $7 |
| Ops Agent Worker | Starter | $7 |
| Braintrust Processor | Starter | $7 |
| **Subtotal** | | **$42** |
| Vercel | Hobby | $0 |
| Supabase | Free | $0 |
| Upstash Redis | Free | $0 |
| **Total** | | **$42/month** |

### New Costs (With Minimal Staging)

| Service | Type | Cost/Month | Notes |
|---------|------|------------|-------|
| Backend API Staging | Starter | $7 | Auto-suspend enabled |
| Orchestrator API Staging | Starter | $7 | Auto-suspend enabled |
| **Staging Subtotal** | | **$14** | |
| **With Auto-suspend** | | **~$7** | 50% savings |
| Supabase Staging | Free/Paid | $0-25 | Free tier sufficient for staging |
| Upstash Redis Staging | Free | $0 | Free tier sufficient |
| **Total New Cost** | | **~$7-32/month** | |
| **Total Infrastructure** | | **~$49-74/month** | |

**ROI**:
- Investment: $7-32/month (~15-75% increase)
- Risk Reduction: 80%+ (prevents production incidents)
- Confidence: High (safe testing before production)
- Incident Cost Avoidance: $500-5000/incident (downtime, reputation, debugging)

---

## Security Considerations

### Secrets Separation

**Production Secrets** (never use in staging):
- `GITHUB_TOKEN` (with write access)
- `STRIPE_SECRET_KEY` (when implemented)
- `OPENAI_API_KEY` (use separate key with lower rate limits)
- Production database credentials

**Staging Secrets** (separate from production):
- Generate new `SECRET_KEY`, `JWT_SECRET_KEY`, `ADMIN_PASSWORD`
- Use staging-specific API keys where possible
- Use test mode for payment providers

### Data Protection

**Staging Data Policy**:
- ❌ Never copy production PII to staging
- ✅ Use synthetic/anonymized data only
- ✅ Seed with test data
- ✅ Implement data retention policy (auto-delete after 30 days)

### Access Control

**Staging Access**:
- Development team: Full access
- QA team: Read access
- Stakeholders: Demo access only
- Public: No access (IP whitelist or VPN)

---

## Monitoring and Observability

### Sentry Configuration

**Separate Environments**:
```python
sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'],
    environment=os.environ.get('ENVIRONMENT', 'production'),
    traces_sample_rate=1.0 if os.environ.get('ENVIRONMENT') == 'staging' else 0.1
)
```

**Benefits**:
- Separate error tracking for staging vs production
- Higher trace sampling in staging (100% vs 10%)
- Clear environment labels in Sentry dashboard

### Logging

**Log Levels by Environment**:
- Production: `INFO`
- Staging: `DEBUG`
- Development: `DEBUG`

**Log Aggregation**:
- Use Render's built-in logs for staging
- Consider Datadog/Logtail for production (future)

---

## Testing Strategy

### Smoke Tests (Automated)

Run after every staging deployment:
```bash
# Health checks
curl -f https://morningai-backend-v2-stg.onrender.com/healthz
curl -f https://morningai-orchestrator-api-stg.onrender.com/health

# Critical endpoints
curl -f https://morningai-backend-v2-stg.onrender.com/api/phase7/status
curl -f https://morningai-backend-v2-stg.onrender.com/api/dashboard/layouts

# Database connectivity
curl -f https://morningai-backend-v2-stg.onrender.com/api/health
```

### Integration Tests (Manual)

Before promoting to production:
1. ✅ User authentication flow (login, logout, 2FA)
2. ✅ Agent task creation and execution
3. ✅ Dashboard data loading
4. ✅ API rate limiting
5. ✅ Error handling and logging

### Load Tests (Optional)

Use k6 for load testing staging:
```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '3m', target: 50 },
    { duration: '1m', target: 0 },
  ],
};

export default function () {
  let res = http.get('https://morningai-backend-v2-stg.onrender.com/healthz');
  check(res, { 'status is 200': (r) => r.status === 200 });
}
```

---

## Success Criteria

### Week 1 (Minimal Staging)
- ✅ `develop` branch created and protected
- ✅ 2 staging services deployed (backend + orchestrator)
- ✅ Staging database configured
- ✅ Staging CI workflow passing
- ✅ Production approval gate configured
- ✅ Smoke tests passing

### Week 2 (Validation)
- ✅ 3+ deployments to staging without issues
- ✅ 1+ production deployment via staging → main flow
- ✅ Team comfortable with new workflow
- ✅ Documentation updated

### Month 1 (Maturity)
- ✅ All 6 services have staging equivalents
- ✅ Integration tests running against staging
- ✅ Zero production incidents from untested changes
- ✅ Staging environment used for demos

---

## Troubleshooting

### Common Issues

**Issue**: Staging service won't start
- Check Render logs for errors
- Verify all environment variables are set
- Confirm DATABASE_URL is valid
- Check if auto-suspend is causing delays

**Issue**: Staging database connection fails
- Verify Supabase project is active
- Check IP whitelist (Render IPs)
- Confirm DATABASE_URL format
- Test connection with `psql`

**Issue**: CI smoke tests fail
- Wait longer for Render deployment (increase sleep time)
- Check if service is auto-suspended (first request wakes it)
- Verify health check endpoints return 200
- Check Sentry for errors

**Issue**: Secrets not syncing
- Render's `sync: false` means manual management
- Update secrets in Render dashboard manually
- Consider using secret management tool (Vault)

---

## Future Enhancements

### Short-term (Month 2-3)
- [ ] Add remaining 4 services to staging
- [ ] Implement blue-green deployment for production
- [ ] Add automated integration tests
- [ ] Set up staging data seeding scripts

### Medium-term (Month 4-6)
- [ ] Implement canary deployments
- [ ] Add performance monitoring (Datadog)
- [ ] Create disaster recovery runbook
- [ ] Implement infrastructure-as-code (Terraform)

### Long-term (Month 7-12)
- [ ] Multi-region staging environments
- [ ] Automated rollback on failed health checks
- [ ] Chaos engineering tests
- [ ] Preview environments per PR (Render Preview)

---

## References

- ADR-003: Database-of-Record Decision
- render.yaml: Production service configuration
- vercel.json: Frontend deployment configuration
- CTO Technical Assessment Report (2025-10-28)

---

**Document Status**: Ready for Implementation  
**Next Steps**: Create `develop` branch and begin Phase 1 implementation  
**Estimated Time**: 2-3 hours for minimal viable staging  
**Estimated Cost**: ~$7/month additional
