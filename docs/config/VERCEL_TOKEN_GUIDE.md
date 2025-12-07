# VERCEL_TOKEN Usage Guide

## Overview

This guide explains the Vercel token configuration for the MorningAI platform. The platform uses Vercel for frontend deployments and provides programmatic access through the Ops Agent.

## Token Semantics

| Token | Purpose | Required | Usage |
|-------|---------|----------|-------|
| `VERCEL_TOKEN` | Primary Vercel API token | Recommended | All Vercel operations (Ops Agent, CI diagnostics) |
| `VERCEL_TOKEN_NEW` | Temporary rotation token | Optional | Only during token rotation |
| `VERCEL_TOKEN_2` | Testing/sandbox token | Optional | Integration tests, sandbox environments |

## Deployment Mechanism

**Important**: Vercel deployments are handled by Vercel's native GitHub integration, NOT GitHub Actions.

- **Production**: Automatic on push to `main` branch
- **Preview**: Automatic on PR creation for `feature/*`, `fix/*`, `devin/*` branches

> **Note**: This project uses a trunk-based development model. There is no persistent `develop` branch. Staging is handled via Render backend services (deploying from `main` with staging env vars) and Vercel preview deployments.

The `VERCEL_TOKEN` is NOT required for deployments. It is only needed for:
1. Ops Agent Vercel operations (deployment monitoring, rollback, status checks)
2. CI diagnostic workflows (`env-diagnose.yml`)

## Token Consumers

### 1. Ops Agent Worker (`agents/ops_agent/worker.py`)

```python
# Uses VERCEL_TOKEN as primary, falls back to VERCEL_TOKEN_NEW
self.vercel_token = vercel_token or os.getenv("VERCEL_TOKEN") or os.getenv("VERCEL_TOKEN_NEW")
```

**Capabilities**:
- List deployments
- Monitor deployment status
- Trigger rollbacks
- Promote deployments to production

### 2. Ops Agent Dashboard (`agents/ops_agent/dashboard/app.py`)

```python
vercel_token = os.getenv("VERCEL_TOKEN")
```

**Capabilities**:
- Display deployment status in dashboard
- Provide deployment history

### 3. CI Diagnostic Workflow (`.github/workflows/env-diagnose.yml`)

```yaml
env:
  VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
run: |
  npx vercel projects ls --token "$VERCEL_TOKEN"
```

**Capabilities**:
- Verify Vercel credentials are valid
- List Vercel projects for diagnostics

## Configuration

### For Ops Agent (Render)

Set in `morningai-ops-agent-worker` service environment:

```bash
VERCEL_TOKEN=your-vercel-api-token
VERCEL_TEAM_ID=your-team-id  # Optional
```

### For CI Diagnostics (GitHub Secrets)

Set in repository secrets:

```
VERCEL_TOKEN=your-vercel-api-token
VERCEL_ORG_ID=your-org-id
```

## Token Rotation Procedure

1. **Generate new token** in Vercel Dashboard (Settings > Tokens)
2. **Set as `VERCEL_TOKEN_NEW`** in all environments
3. **Verify operations** work with new token
4. **Move value to `VERCEL_TOKEN`** (replace old token)
5. **Delete `VERCEL_TOKEN_NEW`** from all environments
6. **Revoke old token** in Vercel Dashboard

### Rotation Frequency

Per `SECRET_ROTATION_POLICY.md`, `VERCEL_TOKEN` is Tier 2 (quarterly rotation).

## Troubleshooting

### Ops Agent Vercel Operations Failing

1. Check if `VERCEL_TOKEN` is set:
   ```bash
   echo $VERCEL_TOKEN
   ```

2. Verify token is valid:
   ```bash
   curl -H "Authorization: Bearer $VERCEL_TOKEN" \
        https://api.vercel.com/v9/projects
   ```

3. Check token has correct scopes (needs project read/write access)

### CI Diagnostic Workflow Skipped

If `env-diagnose.yml` shows "Vercel credentials not configured":
- Verify `VERCEL_TOKEN` is set in GitHub Secrets
- Verify `VERCEL_ORG_ID` is set in GitHub Secrets

## Related Documentation

- [Vercel Deployment Strategy](../deployment/VERCEL_DEPLOYMENT_STRATEGY.md)
- [Vercel Environment Variables](../deployment/VERCEL_ENVIRONMENT_VARIABLES.md)
- [Secret Rotation Policy](../SECRET_ROTATION_POLICY.md)
- [Ops Agent README](../../agents/ops_agent/README.md)
- [Operations Runbook](../../agents/ops_agent/OPERATIONS_RUNBOOK.md)

---

**Last Updated**: November 2025
**Maintained By**: Platform Team
