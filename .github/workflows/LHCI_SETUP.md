# Lighthouse CI (LHCI) Setup Documentation

## Overview

This document describes the Lighthouse CI (LHCI) workflow configuration for the MorningAI project. LHCI runs automated performance, accessibility, and best practices audits on the frontend applications.

## Workflow Jobs

The LHCI workflow (`.github/workflows/lhci.yml`) contains two jobs:

### 1. `lhci-pr` - Pull Request Audits
- **Trigger**: Pull requests to `main` branch
- **Purpose**: Audit changes in PRs and provide feedback
- **Behavior**: Compares against baseline, posts comments on PR

### 2. `lhci-main` - Main Branch Audits  
- **Trigger**: Pushes to `main` branch, scheduled runs (nightly)
- **Purpose**: Collect performance signals and update baseline
- **Behavior**: Updates `.lhci-baseline.json` and `trend.csv`

## Trigger Conditions

### Path Filters

LHCI only runs when changes are made to:
```yaml
paths:
  - 'handoff/20250928/40_App/frontend-dashboard/**'
  - 'handoff/20250928/40_App/owner-console/**'
  - 'packages/shared-ui/**'
  - 'lighthouserc.json'
```

**Important**: Changes to `.github/workflows/lhci.yml` itself will NOT trigger LHCI. To test workflow changes:
1. Make a minimal change to a file in one of the trigger paths (e.g., add a comment)
2. Use `workflow_dispatch` trigger to manually run LHCI

### Manual Trigger

You can manually trigger LHCI from the GitHub Actions UI:
1. Go to Actions → Lighthouse CI
2. Click "Run workflow"
3. Select branch and run

This is useful for:
- Testing workflow configuration changes
- Running LHCI on demand without waiting for code changes
- Debugging LHCI issues

## Architecture

### Backend Bootstrap

LHCI requires a running backend API to handle authentication. The workflow includes:

#### 1. Python Setup
```yaml
- name: Setup Python for backend
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
```

#### 2. Install Dependencies
```bash
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt
```

#### 3. Environment Variables
```bash
export FLASK_APP=src.main:app
export ENABLE_MOCK_USERS=true          # Use mock users for testing
export ENABLE_ORCHESTRATOR=false       # Disable orchestrator (avoids Redis/TLS)
export JWT_SECRET_KEY=test-jwt-secret-for-lhci-ci
export FLASK_SECRET_KEY=test-flask-secret-for-lhci-ci
export ENVIRONMENT=development
export CORS_ORIGINS=http://localhost:4173,http://127.0.0.1:4173
export PYTHONPATH="${GITHUB_WORKSPACE}:${GITHUB_WORKSPACE}/handoff/20250928/40_App/api-backend/src:${PYTHONPATH}"
```

**Key Configuration**:
- `ENABLE_ORCHESTRATOR=false`: Disables orchestrator routes to avoid Redis TLS requirements in CI
- `ENABLE_MOCK_USERS=true`: Enables mock user authentication for testing
- `VITE_API_BASE_URL=http://localhost:5000`: Frontend points to local backend

#### 4. Start Backend
```bash
nohup gunicorn -b 0.0.0.0:5000 'src.main:app' \
  --workers=1 --threads=4 --timeout=120 \
  >> backend.log 2>&1 &
echo $! > backend.pid
```

#### 5. Health Check
```bash
for i in {1..30}; do
  if curl -sf http://localhost:5000/health > /dev/null; then
    echo "✅ Backend is ready"
    break
  fi
  echo "Waiting for backend... ($i/30)"
  sleep 2
done
```

**Timeout**: 60 seconds (30 attempts × 2 seconds)

### Frontend Build & Preview

#### 1. Build Application
```bash
echo "VITE_API_BASE_URL=http://localhost:5000" > .env.production
pnpm build
```

#### 2. Start Preview Server
```bash
pnpm preview --port 4173 &
echo $! > preview.pid
```

#### 3. Health Check
Waits up to 120 seconds for preview server to be ready.

### Authentication Setup

LHCI runs Playwright authentication setup before collecting Lighthouse data:

```bash
pnpm exec playwright test tests/auth.setup.spec.ts --trace on-first-retry
```

**Required Secrets**:
- `VITE_SUPABASE_URL`: Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Supabase anonymous key
- `TEST_EMAIL`: Test user email
- `TEST_PASSWORD`: Test user password

**Output**: `playwright/.auth/storageState.json` (authentication state)

### Lighthouse Collection

#### Configuration Files
- **PR audits**: Uses default `lighthouserc.json`
- **Main audits**: Uses `lighthouserc.main.json`

#### Collection Command
```bash
pnpm dlx @lhci/cli collect \
  --config=../../../../lighthouserc.main.json \
  --url=http://localhost:4173/ \
  --url=http://localhost:4173/login \
  --url=http://localhost:4173/pricing \
  --url=http://localhost:4173/dashboard \
  --url=http://localhost:4173/settings \
  --numberOfRuns=1 \
  --settings.chromeFlags="--no-sandbox --disable-dev-shm-usage"
```

**Chrome Flags**:
- `--no-sandbox`: Required for CI environment
- `--disable-dev-shm-usage`: Prevents shared memory issues

#### Artifacts
- `.lighthouseci/`: Lighthouse reports and data
- `backend.log`: Backend startup and runtime logs
- `test-results/`: Playwright test results
- `playwright-report/`: Playwright HTML report

### Cleanup

Both jobs properly clean up resources:

```yaml
- name: Upload backend logs
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: backend-logs-lhci-pr  # or backend-logs-lhci-main
    path: handoff/20250928/40_App/api-backend/backend.log
    retention-days: 14

- name: Stop backend
  if: always()
  run: |
    if [ -f handoff/20250928/40_App/api-backend/backend.pid ]; then
      kill $(cat handoff/20250928/40_App/api-backend/backend.pid) || true
    fi

- name: Stop preview server
  if: always()
  run: |
    if [ -f preview.pid ]; then
      kill $(cat preview.pid) || true
    fi
```

## Troubleshooting

### Backend Failed to Start

**Symptoms**: "❌ Backend failed to start" in logs

**Diagnosis**:
1. Check `backend-logs-lhci-pr` or `backend-logs-lhci-main` artifact
2. Look for Python import errors or missing dependencies

**Common Causes**:
- Missing dependencies in `requirements.txt`
- PYTHONPATH misconfiguration
- Port 5000 already in use
- Import errors from orchestrator (should be disabled with `ENABLE_ORCHESTRATOR=false`)

**Solutions**:
- Verify `requirements.txt` includes all necessary packages
- Check PYTHONPATH includes both orchestrator and api-backend/src
- Ensure `ENABLE_ORCHESTRATOR=false` is set

### 500 Error on /api/auth/v2/csrf

**Symptoms**: Authentication setup fails with 500 errors

**Diagnosis**:
1. Check if backend is running: `curl http://localhost:5000/health`
2. Check backend logs for errors

**Common Causes**:
- Backend not started before authentication setup
- Missing environment variables (JWT_SECRET_KEY, FLASK_SECRET_KEY)
- CORS configuration doesn't include preview server origin

**Solutions**:
- Ensure backend health check passes before auth setup
- Verify all required environment variables are set
- Check CORS_ORIGINS includes `http://localhost:4173`

### Authentication Setup Fails

**Symptoms**: `auth.setup.spec.ts` fails, no `storageState.json` created

**Diagnosis**:
1. Check Playwright test results artifact
2. Review `playwright-report/` for detailed error messages

**Common Causes**:
- Missing or incorrect test credentials
- Backend not responding to auth endpoints
- Supabase configuration issues
- Cookie security issues (Secure; SameSite=None)

**Solutions**:
- Verify `TEST_EMAIL` and `TEST_PASSWORD` secrets are set
- Check backend `/api/auth/v2/csrf` endpoint is accessible
- Verify Supabase secrets (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`)
- If using HTTPS-only cookies, may need to serve preview over HTTPS

### HTTPS / Cookie Security Issues

**Symptoms**: Cookies not being set, authentication fails despite 200 responses

**Background**: If backend sets cookies with `Secure; SameSite=None`, they require HTTPS.

**Current Setup**: Uses HTTP (`http://localhost:4173`)

**Potential Solutions** (if needed):
1. Use self-signed certificate for preview server
2. Add Chrome flags: `--ignore-certificate-errors`, `--unsafely-treat-insecure-origin-as-secure=http://localhost:4173`
3. Configure backend to not require Secure cookies in test environment

### PYTHONPATH Issues

**Symptoms**: Import errors for `common` or `src.services.auth_service`

**Diagnosis**: Check import preflight output in backend logs

**Solution**: Verify PYTHONPATH includes:
```bash
${GITHUB_WORKSPACE}:${GITHUB_WORKSPACE}/handoff/20250928/40_App/api-backend/src
```

### Port Conflicts

**Symptoms**: Backend or preview server fails to start

**Diagnosis**: Check for "Address already in use" errors

**Solution**: Ports 5000 (backend) and 4173 (preview) should be available in CI. If conflicts occur, may need to use different ports or ensure proper cleanup from previous runs.

### Timeout Issues

**Symptoms**: Health checks timeout, workflow takes too long

**Current Timeouts**:
- Backend health check: 60 seconds (30 × 2s)
- Preview server health check: 120 seconds (60 × 2s)
- Overall job timeout: 15 minutes

**Solutions**:
- Increase retry count or interval if backend startup is slow
- Check for blocking operations in backend startup
- Optimize frontend build if preview server is slow to start

## Verification

### Success Indicators

1. **Backend Started**:
   ```
   ✅ Backend is ready
   ```

2. **Authentication Setup**:
   ```
   ✅ Storage state file exists
   Origins: 1
   localStorage keys: supabase.auth.token
   ```

3. **LHCI Collection**:
   ```
   Lighthouse CI collected 5 reports
   ```

4. **Artifacts Uploaded**:
   - `lhci-artifacts-pr` or `lhci-artifacts-main`
   - `backend-logs-lhci-pr` or `backend-logs-lhci-main`
   - `playwright-test-results`

### Manual Verification

After LHCI runs successfully:

1. **Check Artifacts**:
   - Download `lhci-artifacts-*` and verify `.lighthouseci/` directory exists
   - Review Lighthouse HTML reports

2. **Check Backend Logs**:
   - Download `backend-logs-*` artifact
   - Verify no errors during startup or runtime

3. **Check PR Comments** (for `lhci-pr`):
   - LHCI should post a comment with audit results
   - Compare against baseline

4. **Check Baseline Updates** (for `lhci-main`):
   - Verify `.lhci-baseline.json` is updated
   - Check `trend.csv` for new data points

## Maintenance

### Updating Backend Configuration

When modifying backend setup:
1. Test changes in E2E workflow first (`.github/workflows/frontend.yml`)
2. Apply same changes to both `lhci-pr` and `lhci-main` jobs
3. Ensure symmetry between the two jobs

### Updating Lighthouse Configuration

When modifying Lighthouse audits:
1. Update `lighthouserc.json` (for PR audits)
2. Update `lighthouserc.main.json` (for main audits)
3. Consider impact on baseline and thresholds

### Adding New Routes

To audit new routes:
1. Add `--url=http://localhost:4173/new-route` to LHCI collect command
2. Update both `lhci-pr` and `lhci-main` jobs
3. Ensure route is accessible without authentication or update auth setup

## Related Documentation

- [Playwright E2E Tests](../../handoff/20250928/40_App/frontend-dashboard/e2e/README.md)
- [Backend API Documentation](../../handoff/20250928/40_App/api-backend/README.md)
- [Environment Variables Schema](../../config/env.schema.yaml)

## References

- [Lighthouse CI Documentation](https://github.com/GoogleChrome/lighthouse-ci)
- [Playwright Authentication](https://playwright.dev/docs/auth)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

## Changelog

### 2025-11-18
- **Added**: Backend startup logic to fix authentication failures (PR #1344)
- **Added**: Backend health check with 30-attempt retry
- **Added**: Backend log upload for debugging
- **Added**: Proper backend cleanup steps
- **Added**: `workflow_dispatch` trigger for manual runs
- **Added**: Complete LHCI setup documentation
- **Fixed**: 500 errors on `/api/auth/v2/csrf` endpoint
- **Fixed**: LHCI unable to run due to authentication failures

### Previous
- Initial LHCI workflow setup
- PR and main branch audit jobs
- Baseline and trend tracking
