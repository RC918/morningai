# Secret Key Naming Standard

## Purpose
This document establishes a consistent naming convention for all secret keys in the MorningAI project to improve clarity, security, and maintainability.

## Naming Convention

All secret keys should follow this pattern:
```
{PURPOSE}_{TYPE}_KEY
```

Where:
- `PURPOSE`: What the key is used for (JWT, FLASK, ENCRYPTION, STRIPE, etc.)
- `TYPE`: The type of key (SECRET, API, WEBHOOK, etc.)
- `KEY`: Always ends with "KEY" for clarity

## Standardized Secret Keys

### Current Keys and Their Standardized Names

| Current Name | Standardized Name | Purpose | Security Level |
|--------------|-------------------|---------|----------------|
| `JWT_SECRET_KEY` | `JWT_SECRET_KEY` | JWT token signing | Critical ✅ |
| `SECRET_KEY` | `FLASK_SECRET_KEY` | Flask session signing | Critical |
| `MASTER_KEY` | `ENCRYPTION_MASTER_KEY` | Data encryption master key | Critical |
| `STRIPE_SECRET_KEY` | `STRIPE_SECRET_KEY` | Stripe API authentication | Critical ✅ |
| `STRIPE_WEBHOOK_SECRET` | `STRIPE_WEBHOOK_SECRET_KEY` | Stripe webhook validation | Critical |

### Usage Guidelines

#### JWT_SECRET_KEY
- **Purpose**: Signs and verifies JWT authentication tokens
- **Used in**: `auth_middleware.py`, `routes/auth.py`
- **Security**: CRITICAL - Must be kept secret, rotated regularly
- **Length**: Minimum 32 characters
- **Example**: `openssl rand -hex 32`

#### FLASK_SECRET_KEY
- **Purpose**: Signs Flask session cookies
- **Used in**: `main.py` (`app.config['SECRET_KEY']`)
- **Security**: CRITICAL - Must be kept secret
- **Length**: Minimum 32 characters
- **Example**: `openssl rand -hex 32`

#### ENCRYPTION_MASTER_KEY
- **Purpose**: Master key for encrypting sensitive data at rest
- **Used in**: `main.py` (health check endpoint)
- **Security**: CRITICAL - Must be kept secret, never rotated without data migration
- **Length**: 32 bytes (256-bit)
- **Example**: `openssl rand -base64 32`

#### STRIPE_SECRET_KEY
- **Purpose**: Authenticates with Stripe API
- **Used in**: Payment processing (Phase 10)
- **Security**: CRITICAL - Provided by Stripe
- **Format**: `sk_live_...` (production) or `sk_test_...` (testing)

#### STRIPE_WEBHOOK_SECRET_KEY
- **Purpose**: Validates Stripe webhook signatures
- **Used in**: Webhook handlers (Phase 10)
- **Security**: CRITICAL - Provided by Stripe
- **Format**: `whsec_...`

## Migration Plan

### Phase 1: Update .env.example (Immediate)
1. Rename `SECRET_KEY` → `FLASK_SECRET_KEY` in .env.example
2. Rename `MASTER_KEY` → `ENCRYPTION_MASTER_KEY` in .env.example
3. Rename `STRIPE_WEBHOOK_SECRET` → `STRIPE_WEBHOOK_SECRET_KEY` in .env.example
4. Add comments explaining each key's purpose

### Phase 2: Update Code References (30 days)
1. Update `main.py` to use `FLASK_SECRET_KEY`
2. Update `main.py` to use `ENCRYPTION_MASTER_KEY`
3. Add backward compatibility for 30 days:
   ```python
   flask_secret = os.environ.get('FLASK_SECRET_KEY') or os.environ.get('SECRET_KEY', 'default')
   master_key = os.environ.get('ENCRYPTION_MASTER_KEY') or os.environ.get('MASTER_KEY', 'default')
   ```

### Phase 3: Update Documentation (30 days)
1. Update all documentation references
2. Update deployment guides
3. Update CI/CD environment variable configurations

### Phase 4: Remove Backward Compatibility (60 days)
1. Remove fallback to old key names
2. Enforce new naming convention in CI

## Security Best Practices

### Key Generation
```bash
# JWT and Flask secret keys (hex format)
openssl rand -hex 32

# Encryption master key (base64 format)
openssl rand -base64 32
```

### Key Rotation Schedule
- **JWT_SECRET_KEY**: Every 90 days
- **FLASK_SECRET_KEY**: Every 90 days
- **ENCRYPTION_MASTER_KEY**: Never (requires data migration)
- **STRIPE_SECRET_KEY**: Only when compromised
- **STRIPE_WEBHOOK_SECRET_KEY**: Only when compromised

### Key Storage
- **Development**: `.env` file (gitignored)
- **Staging/Production**: Platform secrets (Render, Vercel)
- **Future (Phase 10)**: HashiCorp Vault or AWS KMS

## Validation

### Environment Variable Schema
Update `config/env.schema.yaml` to enforce naming convention:
```yaml
FLASK_SECRET_KEY:
  type: string
  required: true
  security: critical
  min_length: 32

ENCRYPTION_MASTER_KEY:
  type: string
  required: false
  security: critical
  min_length: 32
```

### CI Validation
Add CI check to ensure:
1. All secret keys follow naming convention
2. No deprecated key names in code
3. All keys meet minimum length requirements

## References
- OWASP Key Management Cheat Sheet
- NIST SP 800-57: Key Management Guidelines
- Flask Security Best Practices
- JWT Best Current Practices (RFC 8725)
