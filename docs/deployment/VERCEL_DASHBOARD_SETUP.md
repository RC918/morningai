# Vercel Dashboard Setup Guide

## Overview

This guide provides step-by-step instructions for configuring the Vercel Dashboard to implement the recommended deployment strategy (Option A).

## Prerequisites

- Access to Vercel Dashboard with admin permissions
- GitHub repository: `RC918/morningai`
- Custom domains configured (optional but recommended)

## Team Information

- **Team Name**: Morning-Ai
- **Team Slug**: `morning-ai`
- **Team ID**: `team_Yf6MaEa5YoqhFpklL19AeZTD`

## Projects

### 1. morningai (frontend-dashboard)

- **Project ID**: `prj_2vBtvZikIy4hahhoauNC2AKQMtaM`
- **URL**: https://vercel.com/morning-ai/morningai

### 2. owner-console

- **Project ID**: `prj_KAkdZFlfq0x6xMLQ4OuXgxPrm1up`
- **URL**: https://vercel.com/morning-ai/owner-console

## Step-by-Step Configuration

### Step 1: Connect GitHub Repository

#### For morningai Project

1. Navigate to https://vercel.com/morning-ai/morningai/settings/git
2. Click **"Connect Git Repository"** button
3. Select **GitHub** as the provider
4. Choose repository: **RC918/morningai**
5. Click **"Connect"**
6. Set **Production Branch**: `main`
7. Click **"Save"**

#### For owner-console Project

1. Navigate to https://vercel.com/morning-ai/owner-console/settings/git
2. Follow the same steps as above
3. Set **Production Branch**: `main`

**Expected Result**: Both projects should now show "Connected to GitHub" with the RC918/morningai repository.

### Step 2: Configure Root Directory (Optional but Recommended)

This simplifies build paths and makes configuration more maintainable.

#### For morningai Project

1. Navigate to https://vercel.com/morning-ai/morningai/settings/general
2. Scroll to **"Root Directory"** section
3. Click **"Edit"**
4. Enter: `handoff/20250928/40_App/frontend-dashboard`
5. Click **"Save"**

**Note**: After setting Root Directory, you'll need to update `vercel.json` to use relative paths:
- `outputDirectory`: `dist` (instead of `handoff/20250928/40_App/frontend-dashboard/dist`)

#### For owner-console Project

1. Navigate to https://vercel.com/morning-ai/owner-console/settings/general
2. Set **Root Directory**: `handoff/20250928/40_App/owner-console`
3. Click **"Save"**

### Step 3: Configure Branch Aliases (Staging Environment)

Branch Aliases allow you to map a specific branch to a stable domain, creating a persistent staging environment.

#### For morningai Project

**Completed via API on 2025-11-04**:
- Domain: `staging.morningai.me`
- Git Branch: `develop`
- Verified: ✅ Yes

#### For owner-console Project

**Completed via API on 2025-11-04**:
- Domain: `staging-owner.morningai.me`
- Git Branch: `develop`
- Verified: ✅ Yes

**DNS Configuration** (Cloudflare - morningai.me zone):

Completed via Cloudflare API on 2025-11-04:
```
Type: CNAME
Name: staging
Value: cname.vercel-dns.com
TTL: 300 (Auto)
Proxy status: DNS only (gray cloud)

Type: CNAME
Name: staging-owner
Value: cname.vercel-dns.com
TTL: 300 (Auto)
Proxy status: DNS only (gray cloud)
```

**Note**: DNS records must be DNS-only (proxied=false) for Vercel domain verification to work correctly.

### Step 4: Configure Ignored Build Step (Optional)

This allows you to skip builds for documentation-only changes directly in the Dashboard.

#### For morningai Project

1. Navigate to https://vercel.com/morning-ai/morningai/settings/git
2. Scroll to **"Ignored Build Step"** section
3. Click **"Edit"**
4. Select **"Custom"**
5. Enter command:
   ```bash
   if git diff --name-only "$VERCEL_GIT_COMMIT_SHA^!" | grep -E -v '^(docs/|.*\.md$)' >/dev/null; then exit 1; else echo "Skipping docs-only change"; exit 0; fi
   ```
6. Click **"Save"**

**Note**: If using Dashboard Ignored Build Step, remove `ignoreCommand` from `vercel.json` to avoid conflicts.

#### For owner-console Project

Follow the same steps as above.

### Step 5: Configure Build & Development Settings

#### For morningai Project

1. Navigate to https://vercel.com/morning-ai/morningai/settings/general
2. Scroll to **"Build & Development Settings"**
3. Configure:
   - **Framework Preset**: Vite
   - **Build Command**: `pnpm --filter @morningai/shared-ui build && pnpm --filter frontend-dashboard build`
   - **Output Directory**: `handoff/20250928/40_App/frontend-dashboard/dist` (or `dist` if Root Directory is set)
   - **Install Command**: `pnpm install --prod=false`
4. Click **"Save"**

#### For owner-console Project

1. Navigate to https://vercel.com/morning-ai/owner-console/settings/general
2. Configure:
   - **Framework Preset**: Vite
   - **Build Command**: `cd ../../../ && pnpm --filter @morningai/shared-ui build && pnpm --filter owner-console build` (or simplified if Root Directory is set)
   - **Output Directory**: `dist`
   - **Install Command**: `cd ../../../ && pnpm install --prod=false` (or simplified if Root Directory is set)
3. Click **"Save"**

### Step 6: Configure Environment Variables

#### For morningai Project

1. Navigate to https://vercel.com/morning-ai/morningai/settings/environment-variables
2. Add the following variables:

**Production Environment**:
```
VITE_API_BASE_URL = https://api.morningai.app (Production)
VITE_SENTRY_DSN = https://...@sentry.io/... (Production, Preview, Development)
VITE_SENTRY_TRACES_SAMPLE_RATE = 0.1 (Production)
VITE_SENTRY_TRACES_SAMPLE_RATE = 1.0 (Preview, Development)
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE = 0.1 (Production)
VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE = 1.0 (Preview, Development)
VITE_SUPABASE_URL = https://xxx.supabase.co (Production, Preview, Development)
VITE_SUPABASE_ANON_KEY = eyJ... (Production, Preview, Development)
VITE_TOLGEE_API_KEY = tgpak_... (Production, Preview, Development)
VITE_TOLGEE_PROJECT_ID = ... (Production, Preview, Development)
VITE_TOLGEE_API_URL = https://app.tolgee.io (Production, Preview, Development)
NODE_ENV = production (Production)
NODE_ENV = development (Preview, Development)
```

**Preview/Staging Environment**:
```
VITE_API_BASE_URL = https://staging-api.morningai.app (Preview)
STAGING_TEST_EMAIL = test@example.com (Preview)
STAGING_TEST_PASSWORD = ... (Preview)
VITE_USE_MOCK = true (Preview, Development)
ENABLE_MOCK_USERS = true (Preview, Development)
```

3. For each variable:
   - Click **"Add New"**
   - Enter **Key** and **Value**
   - Select appropriate **Environments** (Production, Preview, Development)
   - Click **"Save"**

#### For owner-console Project

1. Navigate to https://vercel.com/morning-ai/owner-console/settings/environment-variables
2. Add:
```
VITE_API_BASE_URL = https://owner-api.morningai.app (Production)
VITE_API_BASE_URL = https://staging-owner-api.morningai.app (Preview)
VITE_SENTRY_DSN = https://...@sentry.io/... (Production, Preview, Development)
```

### Step 7: Configure Deployment Protection (Optional)

Enable deployment protection to require approval before deploying to production.

1. Navigate to https://vercel.com/morning-ai/morningai/settings/deployment-protection
2. Enable **"Deployment Protection"**
3. Select protection level:
   - **Standard Protection**: Requires Vercel authentication
   - **Password Protection**: Requires a password
   - **Trusted IPs**: Only allow specific IP addresses
4. Click **"Save"**

### Step 8: Enable Preview Deployment Comments

Automatically post preview deployment URLs as comments on GitHub PRs.

1. Navigate to https://vercel.com/morning-ai/morningai/settings/git
2. Scroll to **"Comments on Pull Requests"**
3. Enable **"Post deployment comments on pull requests"**
4. Click **"Save"**

**Expected Result**: Vercel will automatically comment on PRs with preview deployment URLs.

### Step 9: Configure Notifications (Optional)

Set up Slack or email notifications for deployment events.

1. Navigate to https://vercel.com/morning-ai/morningai/settings/notifications
2. Click **"Add Integration"**
3. Select **Slack** or **Email**
4. Configure notification triggers:
   - Deployment Started
   - Deployment Ready
   - Deployment Failed
   - Deployment Canceled
5. Click **"Save"**

### Step 10: Enable Turborepo Remote Caching (Optional)

Speed up builds by caching Turborepo outputs.

1. Navigate to https://vercel.com/morning-ai/morningai/settings/general
2. Scroll to **"Turborepo Remote Caching"**
3. Click **"Enable"**
4. Click **"Save"**

**Expected Result**: Subsequent builds will be faster due to cached outputs.

## Verification

### Test Production Deployment

1. Push a commit to `main` branch:
   ```bash
   git checkout main
   git commit --allow-empty -m "test: trigger production deployment"
   git push origin main
   ```
2. Check https://vercel.com/morning-ai/morningai/deployments
3. Verify deployment succeeds and is marked as "Production"

### Test Staging Deployment

1. Push a commit to `develop` branch:
   ```bash
   git checkout develop
   git commit --allow-empty -m "test: trigger staging deployment"
   git push origin develop
   ```
2. Check https://vercel.com/morning-ai/morningai/deployments
3. Verify deployment succeeds and is accessible at `staging-dashboard.morningai.app`

### Test Preview Deployment

1. Create a feature branch and push:
   ```bash
   git checkout -b feature/test-preview
   git commit --allow-empty -m "test: trigger preview deployment"
   git push origin feature/test-preview
   ```
2. Create a PR on GitHub
3. Check that Vercel comments on the PR with a preview URL
4. Verify deployment succeeds and is accessible at the preview URL

### Test Docs-Only Skip

1. Create a branch with only docs changes:
   ```bash
   git checkout -b docs/test-skip
   echo "test" >> docs/README.md
   git add docs/README.md
   git commit -m "docs: test skip deployment"
   git push origin docs/test-skip
   ```
2. Check https://vercel.com/morning-ai/morningai/deployments
3. Verify deployment is skipped (should see "Ignored Build Step" message)

## Troubleshooting

### GitHub Not Connected

**Symptom**: "Connect Git Repository" button still visible after connecting.

**Solution**:
1. Disconnect and reconnect GitHub integration
2. Ensure you have admin permissions on the GitHub repository
3. Check Vercel GitHub App permissions at https://github.com/settings/installations

### Branch Alias Not Working

**Symptom**: `develop` branch deploys but not to the staging domain.

**Solution**:
1. Verify DNS records are correctly configured
2. Check domain is assigned to the correct branch in Vercel Dashboard
3. Wait up to 24 hours for DNS propagation

### Build Fails After Configuration

**Symptom**: Builds fail with "command not found" or similar errors.

**Solution**:
1. Verify Build Command is correct
2. Check Install Command includes `--prod=false` to install devDependencies
3. Ensure Root Directory (if set) is correct
4. Check build logs for specific error messages

### Environment Variables Not Available

**Symptom**: `import.meta.env.VITE_*` returns undefined.

**Solution**:
1. Verify variable is prefixed with `VITE_`
2. Check variable is set for the correct environment (Production/Preview/Development)
3. Trigger a new deployment after adding variables
4. Check deployment logs to verify variable is set

## Maintenance

### Regular Tasks

- **Weekly**: Review deployment logs for errors
- **Monthly**: Audit environment variables for unused variables
- **Quarterly**: Review and update deployment strategy
- **Annually**: Rotate secrets and update environment variables

### Monitoring

- **Deployment Success Rate**: Monitor at https://vercel.com/morning-ai/morningai/analytics
- **Build Times**: Check for increasing build times (may indicate need for optimization)
- **Error Rates**: Monitor Sentry for deployment-related errors

## References

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Git Integration](https://vercel.com/docs/concepts/git)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Deployment Strategy](./VERCEL_DEPLOYMENT_STRATEGY.md)
- [Environment Variables Guide](./VERCEL_ENVIRONMENT_VARIABLES.md)

---

**Last Updated**: 2025-11-04
**Owner**: CTO + DevOps Team
**Status**: Active
