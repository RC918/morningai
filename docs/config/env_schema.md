# Environment Variable Schema Documentation

## Overview

Morning AI uses a comprehensive environment configuration system with **53 variables** across 11 categories. This document provides the complete reference for all environment variables, their security levels, and usage guidelines.

**Schema Location**: `/config/env.schema.yaml`  
**Example File**: `/.env.example`  
**Validator**: `/env_schema_validator.py`

## Quick Start: Local Development

### Minimal Setup (5 Required Variables)

For local development, you need at minimum:

```bash
# 1. Copy example file
cp .env.example .env

# 2. Set these 5 critical variables:
JWT_SECRET_KEY=your-secret-key-minimum-32-characters-long
ADMIN_PASSWORD=your-admin-password
SECRET_KEY=your-flask-secret-key-minimum-32-characters
DATABASE_URL=postgresql://user:pass@localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0
```

### Full Development Setup (All Required Variables)

For full functionality including AI features:

```bash
# Authentication & Security (3 variables)
JWT_SECRET_KEY=your-jwt-secret-key
ADMIN_PASSWORD=your-admin-password
SECRET_KEY=your-flask-secret-key

# Database (1 variable)
DATABASE_URL=postgresql://localhost:5432/morningai

# Cloud Services - Supabase (3 variables)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Cloud Services - Cloudflare (2 variables)
CLOUDFLARE_API_TOKEN=your-cloudflare-token
CLOUDFLARE_ZONE_ID=your-zone-id

# Cloud Services - Vercel (3 variables)
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID=your-project-id

# Cloud Services - Render (1 variable)
RENDER_API_KEY=your-render-key

# Cloud Services - Upstash (2 variables)
UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token

# Monitoring - Sentry (1 variable)
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx

# Integration - GitHub (2 variables)
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=RC918/morningai

# Integration - OpenAI (1 variable)
OPENAI_API_KEY=sk-xxxxx
```

## Security Level Classification

### Critical (9 variables)
These must NEVER be committed to git or shared publicly:
- `JWT_SECRET_KEY` - Authentication compromise
- `ADMIN_PASSWORD` - Full system access
- `SECRET_KEY` - Session hijacking risk
- `MASTER_KEY` - Data encryption key
- `GITHUB_TOKEN` - Repository access
- `OPENAI_API_KEY` - API billing abuse
- `SUPABASE_SERVICE_ROLE_KEY` - Database admin access
- `STRIPE_SECRET_KEY` - Payment processing
- `STRIPE_WEBHOOK_SECRET` - Payment webhook validation

**Storage**: Use secure secrets management (GitHub Secrets, Render Environment, etc.)

### Secret (12 variables)
Sensitive but with limited scope:
- `SUPABASE_ANON_KEY` - Public key but still sensitive
- `CLOUDFLARE_API_TOKEN` - CDN/DNS management
- `VERCEL_TOKEN` - Deployment access
- `RENDER_API_KEY` - Deployment access
- `UPSTASH_REDIS_REST_TOKEN` - Redis access
- `SENTRY_AUTH_TOKEN` - Monitoring API
- `SLACK_WEBHOOK_URL` - Notification channel
- `TELEGRAM_BOT_TOKEN` - Bot access
- `FLY_API_TOKEN` - Fly.io deployment
- `TEST_ADMIN_JWT` - Test credentials
- `DATABASE_URL` - Database credentials
- `REDIS_URL` - Redis credentials

**Storage**: Secure storage recommended, rotate regularly

### Public (32 variables)
Configuration values safe to share:
- URLs (SUPABASE_URL, VITE_API_BASE_URL, etc.)
- IDs (CLOUDFLARE_ZONE_ID, VERCEL_ORG_ID, etc.)
- Feature flags (all *_ENABLED variables)
- Application settings (PORT, ENVIRONMENT, etc.)

**Storage**: Can be in `.env.example` or documentation

## Variables by Category

### Authentication (2 variables)
| Variable | Type | Required | Security | Description |
|----------|------|----------|----------|-------------|
| JWT_SECRET_KEY | secret | Yes | Critical | JWT signing key |
| ADMIN_PASSWORD | secret | Yes | Critical | Admin password |

### Cloud Services (13 variables)
**Supabase** (3):
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`

**Cloudflare** (2):
- `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`

**Vercel** (3):
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

**Render** (2):
- `RENDER_API_KEY`, `RENDER_INSTANCE_ID`

**Upstash** (2):
- `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

**Fly.io** (1):
- `FLY_API_TOKEN`

### Database (3 variables)
| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| DATABASE_URL | url | Yes | - | PostgreSQL URL |
| REDIS_URL | url | No | redis://localhost:6379/0 | Redis URL |
| MEMORY_TABLE | string | No | memory | Supabase table name |

### Integration (8 variables)
- **GitHub**: `GITHUB_TOKEN`, `GITHUB_REPO`
- **OpenAI**: `OPENAI_API_KEY`
- **Notifications**: `SLACK_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`
- **MCP**: `MCP_SERVER_URL`, `AGENT_ID`

### Worker (2 variables)
| Variable | Default | Description |
|----------|---------|-------------|
| RQ_QUEUE_NAME | orchestrator | Redis Queue name |
| RQ_SERIALIZER | json | Serializer type |

### Application (7 variables)
- `FLASK_ENV`, `ENVIRONMENT`, `PORT`, `CORS_ORIGINS`
- `APP_VERSION`, `APP_PHASE`, `HOSTNAME`

### Feature Flags (7 variables)
All boolean, default `true` except DEMO_MODE and SANDBOX_ENABLED:
- `PHASE7_ENABLED`, `OPS_AGENT_ENABLED`, `GROWTH_STRATEGIST_ENABLED`
- `PM_AGENT_ENABLED`, `HITL_APPROVAL_ENABLED`
- `DEMO_MODE`, `SANDBOX_ENABLED`

### Frontend (4 variables)
All VITE_* prefixed for Vite build:
- `VITE_API_BASE_URL`, `VITE_FEATURES`, `VITE_SENTRY_DSN`, `VITE_USE_MOCK`

### Monitoring (2 variables)
- `SENTRY_DSN` (required), `SENTRY_AUTH_TOKEN` (optional)

### Payment (2 variables - Planned)
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

### Testing (1 variable)
- `TEST_ADMIN_JWT` - For E2E test authentication

## Adding a New Environment Variable

### 3-Step Process:

1. **Add to schema** (`config/env.schema.yaml`):
   ```yaml
   MY_NEW_VAR:
     type: string|secret|url|integer|boolean
     required: true|false
     default: optional-default-value
     description: Clear description of purpose
     category: Choose from existing categories
     security_level: critical|secret|public
     example: optional-example-value
   ```

2. **Regenerate .env.example**:
   ```bash
   python scripts/generate_env_example.py
   ```

3. **Update documentation** (this file) if it's a new category or has special usage

### Validation

All PRs automatically validate the schema:
- Schema structure check
- Required fields validation
- Type consistency check
- Description presence check

See workflow: `.github/workflows/backend.yml` (validate-env-schema job)

## CI/CD Usage

### GitHub Actions Secrets

All `security_level: critical` and `security_level: secret` variables should be configured as GitHub Secrets:

```yaml
env:
  JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
  ADMIN_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
  # ... etc
```

### Render Environment

Configured in `render.yaml`:
- Variables with `sync: false` pull from Render's secret store
- Variables with `generateValue: true` auto-generate on deploy
- Variables with `value:` are hardcoded (public values only)

### Vercel Environment

Frontend variables (VITE_*) configured in Vercel dashboard under project settings.

## Programmatic Validation

Use the built-in validator:

```python
from env_schema_validator import EnvSchemaValidator

validator = EnvSchemaValidator('config/env.schema.yaml')
result = validator.validate_environment()

if not result.valid:
    print(f"❌ Missing required: {result.missing_required}")
    print(f"❌ Invalid values: {result.invalid_values}")
    print(f"⚠️  Warnings: {result.warnings}")
else:
    print("✅ Environment validated successfully")
```

## Troubleshooting

### "Missing required environment variable X"
- Check `.env` file exists and variable is set
- For CI: verify GitHub Secret is configured
- For Render: check environment variable in dashboard

### "Invalid X value"
- Check type matches schema (e.g., URL must start with http://)
- For booleans, use: true/false, yes/no, 1/0
- For integers, ensure numeric value

### "Schema validation failed in CI"
- Run `python scripts/generate_env_example.py` after schema changes
- Ensure all fields have: type, description, category
- Check YAML syntax is valid

## Best Practices

1. **Never commit secrets** - Use `.gitignore` for `.env` files
2. **Use strong secrets** - Minimum 32 characters for JWT/SECRET keys
3. **Rotate regularly** - Change secrets every 90 days
4. **Separate environments** - Different secrets for dev/staging/prod
5. **Document changes** - Update this doc when adding variables
6. **Validate locally** - Run validator before committing
7. **Use examples** - Reference `.env.example` for structure

## References

- Schema: `/config/env.schema.yaml`
- Validator: `/env_schema_validator.py`
- Example: `/.env.example`
- Generator: `/scripts/generate_env_example.py`
- CI Validation: `/.github/workflows/backend.yml`

---

**Last Updated**: Phase 11 Task 4 (2025-10-13)  
**Total Variables**: 53 (19 required, 34 optional)  
**Maintainer**: Morning AI Engineering Team
