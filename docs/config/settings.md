# Settings Module Documentation

## Overview

The `common.config.settings` module provides centralized, type-safe configuration management for the MorningAI platform using Pydantic BaseSettings. This replaces scattered `os.getenv()` calls throughout the codebase with a single source of truth for environment variables.

**Location**: `common/config/settings.py`  
**Schema**: `config/env.schema.yaml` (114 variables: 20 required, 94 optional)

## Key Features

1. **Type Safety**: All environment variables are validated and converted to the correct Python types
2. **Centralized Management**: Single source of truth for all configuration
3. **Test-Aware Caching**: Automatically detects test mode and reloads settings for each test
4. **Production Guards**: Built-in validators prevent insecure configurations in production
5. **Backward Compatibility**: Lazy-loaded singleton pattern maintains compatibility with existing code
6. **Environment Variable Aliases**: Maps UPPERCASE env vars to snake_case Python attributes

## Quick Start

### Basic Usage

```python
from common.config.settings import get_settings

# Get settings instance
settings = get_settings()

# Access configuration values
jwt_secret = settings.jwt_secret_key
redis_url = settings.redis_url
is_prod = settings.is_production
```

### Using the Settings Proxy (Lazy Loading)

```python
from common.config.settings import settings

# Proxy automatically initializes on first access
jwt_secret = settings.jwt_secret_key
redis_url = settings.redis_url
```

### In Tests

```python
import os
from common.config.settings import reload_settings

def test_with_custom_config():
    # Set test environment variables
    os.environ['JWT_SECRET_KEY'] = 'test-key-123'
    os.environ['REDIS_URL'] = 'redis://test:6379'
    
    # Reload settings to pick up new values
    settings = reload_settings()
    
    assert settings.jwt_secret_key == 'test-key-123'
    assert settings.redis_url == 'redis://test:6379'
```

## Architecture

### Settings Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                     get_settings()                          │
│                                                             │
│  1. Check if pytest in sys.modules OR TESTING=true         │
│     ├─ YES: Create new Settings instance (test mode)       │
│     └─ NO:  Return cached singleton (production mode)      │
│                                                             │
│  2. Settings.__init__()                                     │
│     ├─ Load environment variables via Pydantic             │
│     ├─ Apply Field aliases (UPPERCASE → snake_case)        │
│     ├─ Validate types and constraints                      │
│     └─ Run field validators                                │
│                                                             │
│  3. Return Settings instance                                │
└─────────────────────────────────────────────────────────────┘
```

### Test-Aware Caching

The settings module automatically detects test mode and adjusts its caching behavior:

**Production Mode** (singleton):
- First call to `get_settings()` creates instance
- Subsequent calls return cached instance
- Efficient for production use

**Test Mode** (fresh instances):
- Detected via `'pytest' in sys.modules` or `TESTING=true`
- Each call to `get_settings()` creates new instance
- Allows tests to modify environment variables at runtime

### Environment Variable Mapping

Environment variables are mapped to Python attributes using Field aliases:

```python
# Environment Variable → Python Attribute
REDIS_URL           → settings.redis_url
OPENAI_API_KEY      → settings.openai_api_key
JWT_SECRET_KEY      → settings.jwt_secret_key
ENABLE_MOCK_USERS   → settings.enable_mock_users
```

## Production Guards

### Mock Users Validator

Prevents mock users from being enabled in production or staging:

```python
@field_validator("enable_mock_users")
def validate_mock_users_production(cls, v: bool, info) -> bool:
    environment = info.data.get("environment", "development")
    if v and environment in ["production", "staging"]:
        raise ValueError(
            f"ENABLE_MOCK_USERS must be false in {environment} environment. "
            "Mock users are only allowed in development."
        )
    return v
```

**Example Error**:
```
ValueError: ENABLE_MOCK_USERS must be false in production environment. Mock users are only allowed in development.
```

### TOTP Encryption Key Warning

Warns if TOTP encryption key is too short:

```python
@field_validator("totp_encryption_key")
def validate_totp_key(cls, v: Optional[str]) -> Optional[str]:
    if v and len(v) < 32:
        warnings.warn(
            "TOTP_ENCRYPTION_KEY should be at least 32 characters. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'",
            UserWarning
        )
    return v
```

### Redis TLS Warning

Warns about non-TLS Redis connections:

```python
@field_validator("redis_url")
def warn_non_tls_redis(cls, v: str) -> str:
    if v and not v.startswith("rediss://"):
        warnings.warn(
            f"Redis URL does not use TLS (rediss://): {v}. "
            "For production, consider using UPSTASH_REDIS_REST_URL which has HTTPS/TLS by default.",
            UserWarning
        )
    return v
```

### JWT Validation (in auth_service.py)

JWT secret validation is performed in `auth_service.py:validate_security_config()`:

- **Production Requirements**:
  - JWT_SECRET_KEY must be set
  - Must be at least 32 characters
  - Cannot use known weak values: `'your-secret-key'`, `'secret'`, `'changeme'`, `'test'`, `'test-secret-key-for-testing'`

- **Non-Production Behavior**:
  - Logs warning if JWT_SECRET_KEY not set
  - Uses fallback: `'test-secret-key-for-testing'`

## Secret Handling

### Overview

The Settings module uses **Pydantic SecretStr** to protect sensitive configuration values from accidental exposure in logs, exception tracebacks, repr() output, and developer terminals. All 31 secret fields are automatically masked when the Settings object is printed or logged.

### Secret Fields

The following fields are protected using SecretStr:

**Authentication & Encryption** (7 fields):
- `jwt_secret_key` - JWT token signing key
- `admin_password` - Admin user password
- `flask_secret_key` - Flask session secret
- `secret_key` - Deprecated Flask secret
- `encryption_master_key` - Master encryption key
- `master_key` - Deprecated master key
- `totp_encryption_key` - TOTP secret encryption key

**Database** (3 fields):
- `supabase_db_password` - Supabase database password
- `supabase_anon_key` - Supabase anonymous key
- `supabase_service_role_key` - Supabase service role key

**Cloud Providers** (7 fields):
- `cloudflare_api_token` - Cloudflare API token
- `vercel_token` - Vercel deployment token
- `vercel_token_new` - New Vercel token
- `vercel_token_2` - Secondary Vercel token
- `render_api_key` - Render API key
- `upstash_redis_rest_token` - Upstash Redis token
- `fly_api_token` - Fly.io API token

**Monitoring & Auth** (2 fields):
- `sentry_auth_token` - Sentry authentication token
- `monitor_auth_token` - Monitoring system token

**API Keys** (6 fields):
- `github_token` - GitHub API token
- `agent_github_token` - Agent GitHub token
- `openai_api_key` - OpenAI API key
- `telegram_bot_token` - Telegram bot token
- `mailtrap_api_token` - Mailtrap API token
- `dashboard_api_key` - Dashboard API key

**Orchestrator & Payments** (4 fields):
- `orchestrator_jwt_secret` - Orchestrator JWT secret
- `stripe_secret_key` - Stripe secret key
- `stripe_webhook_secret_key` - Stripe webhook secret
- `stripe_webhook_secret` - Deprecated Stripe webhook secret

**Testing** (2 fields):
- `test_admin_jwt` - Test admin JWT token
- `staging_test_password` - Staging test password

### How SecretStr Works

#### Dual-Field + Property Pattern

Each secret field uses a dual-field pattern:
1. **Internal SecretStr field**: `{name}_secret` (e.g., `jwt_secret_key_secret`)
2. **Public property**: `{name}` (e.g., `jwt_secret_key`)

```python
# Internal field (masked in repr/logs)
jwt_secret_key_secret: Optional[SecretStr] = Field(
    None,
    alias="JWT_SECRET_KEY",
    repr=False  # Prevents display in repr()
)

# Public property (returns unwrapped string)
@property
def jwt_secret_key(self) -> Optional[str]:
    """JWT secret key (unwrapped from SecretStr)"""
    return self.jwt_secret_key_secret.get_secret_value() if self.jwt_secret_key_secret else None
```

#### Masking Behavior

**Masked in repr/str/logs**:
```python
settings = get_settings()
print(settings)  # Secrets show as '**********' or SecretStr('**********')
repr(settings)   # Secrets are masked
str(settings)    # Secrets are masked
```

**Accessible via properties**:
```python
settings = get_settings()
api_key = settings.openai_api_key  # Returns actual string value
jwt_secret = settings.jwt_secret_key  # Returns actual string value
```

### Security Best Practices

#### ✅ DO

**Access secrets via properties**:
```python
from common.config.settings import get_settings

settings = get_settings()
api_key = settings.openai_api_key  # Safe: returns string
```

**Use secrets in API calls**:
```python
import openai
from common.config.settings import get_settings

settings = get_settings()
openai.api_key = settings.openai_api_key  # Safe: string value
```

**Log non-secret fields**:
```python
logger.info(f"Environment: {settings.environment}")
logger.info(f"Redis URL: {settings.redis_url}")  # OK if not sensitive
```

#### ❌ DON'T

**Never log the entire Settings object**:
```python
# BAD: May expose secrets in some contexts
logger.info(f"Settings: {settings}")
logger.debug(f"Config: {repr(settings)}")
```

**Never log secret properties directly**:
```python
# BAD: Exposes secret in logs
logger.info(f"API Key: {settings.openai_api_key}")
logger.debug(f"JWT Secret: {settings.jwt_secret_key}")
```

**Never use model_dump() on Settings**:
```python
# BAD: May expose secrets
config_dict = settings.model_dump()
logger.info(config_dict)
```

**Never print secrets for debugging**:
```python
# BAD: Exposes secret in terminal/logs
print(f"Debug API Key: {settings.openai_api_key}")
```

### Advanced Usage

#### Accessing SecretStr Directly

For advanced use cases, you can access the SecretStr object directly:

```python
settings = get_settings()

# Access SecretStr object (rarely needed)
secret_str_obj = settings.jwt_secret_key_secret

# Check if secret is set
if secret_str_obj:
    # Get unwrapped value
    raw_value = secret_str_obj.get_secret_value()
```

#### Testing with Secrets

```python
import os
from common.config.settings import reload_settings

def test_with_secret():
    # Set secret via environment variable
    os.environ['OPENAI_API_KEY'] = 'sk-test-key-123'
    
    # Reload settings
    settings = reload_settings()
    
    # Access secret (returns string)
    assert settings.openai_api_key == 'sk-test-key-123'
    
    # Verify masking in repr
    assert 'sk-test-key-123' not in repr(settings)
```

### Validator Updates

Validators that target secret fields must use the `*_secret` field name and unwrap SecretStr values:

```python
@field_validator("totp_encryption_key_secret", mode="after")
@classmethod
def validate_totp_key(cls, v: Optional[SecretStr]) -> Optional[SecretStr]:
    """Validate TOTP encryption key format"""
    if v:
        raw = v.get_secret_value()  # Unwrap to validate
        if raw and len(raw) < 32:
            warnings.warn("TOTP_ENCRYPTION_KEY should be at least 32 characters")
    return v
```

### Migration Notes

**No code changes required** for existing code that accesses secret fields via properties:

```python
# Before SecretStr (still works)
settings = get_settings()
api_key = settings.openai_api_key  # Returns str

# After SecretStr (same behavior)
settings = get_settings()
api_key = settings.openai_api_key  # Still returns str
```

The dual-field + property pattern ensures backward compatibility while adding security.

## Migration Guide

### Step 1: Import the Settings Module

**Before**:
```python
import os

jwt_secret = os.getenv('JWT_SECRET_KEY', 'default-secret')
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
enable_mock = os.getenv('ENABLE_MOCK_USERS', 'false').lower() == 'true'
```

**After**:
```python
from common.config.settings import get_settings

settings = get_settings()
jwt_secret = settings.jwt_secret_key
redis_url = settings.redis_url
enable_mock = settings.enable_mock_users
```

### Step 2: Handle Optional Values

**Before**:
```python
redis_url = os.getenv('REDIS_URL')
if redis_url:
    connect_to_redis(redis_url)
```

**After**:
```python
from common.config.settings import get_settings

settings = get_settings()
if settings.redis_url:
    connect_to_redis(settings.redis_url)
```

### Step 3: Use Runtime Initialization

**⚠️ IMPORTANT**: Never call `get_settings()` at module level (during import). Always call it inside functions or methods.

**❌ BAD** (module-level):
```python
from common.config.settings import get_settings

# This runs at import time, before tests can set environment variables
settings = get_settings()
JWT_SECRET = settings.jwt_secret_key

def authenticate(token):
    # Uses JWT_SECRET from import time
    return verify_token(token, JWT_SECRET)
```

**✅ GOOD** (runtime):
```python
from common.config.settings import get_settings

def authenticate(token):
    # Reads settings at runtime, after tests have set environment variables
    jwt_secret = get_settings().jwt_secret_key
    return verify_token(token, jwt_secret)
```

### Step 4: Update Tests

**Before**:
```python
import os
from unittest.mock import patch

def test_authentication():
    with patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-key'}):
        # Code that uses os.getenv('JWT_SECRET_KEY')
        result = authenticate(token)
        assert result is True
```

**After**:
```python
import os
from common.config.settings import reload_settings

def test_authentication():
    os.environ['JWT_SECRET_KEY'] = 'test-key'
    reload_settings()  # Force reload to pick up new value
    
    result = authenticate(token)
    assert result is True
```

Or use `patch.dict` without `clear=True`:
```python
from unittest.mock import patch

def test_authentication():
    with patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-key'}):
        # Settings will automatically reload in test mode
        result = authenticate(token)
        assert result is True
```

### Step 5: Handle Type Conversions

The settings module automatically handles type conversions:

**Before**:
```python
# Manual type conversion
port = int(os.getenv('PORT', '5000'))
debug = os.getenv('DEBUG', 'false').lower() == 'true'
cost_threshold = float(os.getenv('COST_ALERT_THRESHOLD', '50.0'))
```

**After**:
```python
from common.config.settings import get_settings

settings = get_settings()
port = settings.port  # Already an int
debug = settings.debug  # Already a bool
cost_threshold = settings.cost_alert_threshold  # Already a float
```

## Common Patterns

### Pattern 1: Database Connection

**Before**:
```python
import os
import psycopg2

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(db_url)
```

**After**:
```python
import psycopg2
from common.config.settings import get_settings

def get_db_connection():
    settings = get_settings()
    if not settings.database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(settings.database_url)
```

### Pattern 2: Redis Client

**Before**:
```python
import os
import redis

def get_redis_client():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    return redis.from_url(redis_url)
```

**After**:
```python
import redis
from common.config.settings import get_settings

def get_redis_client():
    settings = get_settings()
    redis_url = settings.redis_url or 'redis://localhost:6379'
    return redis.from_url(redis_url)
```

### Pattern 3: API Keys

**Before**:
```python
import os
from openai import OpenAI

def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)
```

**After**:
```python
from openai import OpenAI
from common.config.settings import get_settings

def get_openai_client():
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=settings.openai_api_key)
```

### Pattern 4: Feature Flags

**Before**:
```python
import os

def should_use_langgraph():
    use_langgraph = os.getenv('USE_LANGGRAPH', 'false').lower() == 'true'
    percent = int(os.getenv('USE_LANGGRAPH_PERCENT', '0'))
    
    if not use_langgraph:
        return False
    
    import random
    return random.randint(0, 100) < percent
```

**After**:
```python
from common.config.settings import get_settings

def should_use_langgraph():
    settings = get_settings()
    
    if not settings.use_langgraph:
        return False
    
    import random
    return random.randint(0, 100) < settings.use_langgraph_percent
```

## Troubleshooting

### Issue: Settings not picking up environment variables in tests

**Symptom**: Tests set environment variables but settings still uses old values.

**Solution**: Call `reload_settings()` after setting environment variables:

```python
import os
from common.config.settings import reload_settings

def test_with_custom_config():
    os.environ['JWT_SECRET_KEY'] = 'test-key'
    reload_settings()  # Force reload
    
    settings = get_settings()
    assert settings.jwt_secret_key == 'test-key'
```

### Issue: Import-time errors in tests

**Symptom**: Tests fail with validation errors before test fixtures are set up.

**Solution**: Move `get_settings()` calls from module level to function level:

```python
# ❌ BAD: Module-level call
from common.config.settings import get_settings
settings = get_settings()  # Runs at import time

# ✅ GOOD: Function-level call
from common.config.settings import get_settings

def my_function():
    settings = get_settings()  # Runs at call time
```

### Issue: ValidationError for environment variable

**Symptom**: `pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings`

**Solution**: Check that the environment variable value matches the expected type and constraints:

```python
# For Literal types, value must match exactly
ENVIRONMENT=production  # ✅ Valid: 'development', 'staging', or 'production'
ENVIRONMENT=prod        # ❌ Invalid: not in allowed values

# For boolean types, use standard boolean strings
ENABLE_MOCK_USERS=true   # ✅ Valid
ENABLE_MOCK_USERS=True   # ✅ Valid
ENABLE_MOCK_USERS=1      # ✅ Valid
ENABLE_MOCK_USERS=yes    # ✅ Valid
```

### Issue: UPPERCASE environment variable not found

**Symptom**: Environment variable is set but settings attribute is None.

**Solution**: Check that the Field alias is defined in settings.py:

```python
# In settings.py
redis_url: Optional[str] = Field(None, alias="REDIS_URL")
```

If the alias is missing, add it following the existing pattern.

## Best Practices

1. **Always use runtime initialization**: Never call `get_settings()` at module level
2. **Use type hints**: Leverage the type safety provided by Pydantic
3. **Handle None values**: Check for None before using optional settings
4. **Use reload_settings() in tests**: Ensure tests pick up environment variable changes
5. **Follow naming conventions**: Use snake_case for Python attributes, UPPERCASE for env vars
6. **Document new settings**: Add new environment variables to `config/env.schema.yaml`
7. **Test production guards**: Verify that validators prevent insecure configurations

## Related Documentation

- **Environment Schema**: `config/env.schema.yaml` - Complete list of all environment variables
- **Environment Setup**: `docs/ENVIRONMENTS.md` - Environment-specific configuration
- **Security Configuration**: `handoff/20250928/40_App/api-backend/src/services/auth_service.py:validate_security_config()` - JWT and security validation
- **Testing Guide**: `docs/TESTING.md` - Testing best practices

## Support

For questions or issues with the settings module:

1. Check this documentation first
2. Review `config/env.schema.yaml` for available variables
3. Check existing usage in migrated files (see PR #1204)
4. Ask in the engineering team channel

## Changelog

### 2025-11-08 - Initial Release (PR #1199, #1204)

- Added Pydantic BaseSettings for centralized configuration
- Migrated 21 critical path files (64 environment variable calls)
- Added test-aware caching for pytest compatibility
- Added production guards for mock users, TOTP keys, and Redis TLS
- Created comprehensive unit tests (10 passing tests)
- Added this documentation

### Future Enhancements

- Migrate remaining ~500 os.getenv() calls (PR #1c)
- Add AST-based CI gate to prevent new os.getenv() calls (PR #1d)
- Add more comprehensive unit tests (PR #1e)
- Consider adding runtime configuration reloading for production

## CORS Configuration

### Overview

The `CORS_ORIGINS` environment variable controls which origins are allowed to make cross-origin requests to the API backend. This is critical for security and for enabling frontend applications (including Vercel preview deployments) to communicate with the backend.

### Environment Variable

**Name**: `CORS_ORIGINS` (uppercase)  
**Field**: `cors_origins` (lowercase with underscore)  
**Type**: `str` (comma-separated list)  
**Default**: `"http://localhost:5173,http://localhost:5174"`  
**Alias**: `alias="CORS_ORIGINS"` (required for Pydantic to load the environment variable)

### Configuration Format

CORS origins must be specified as a comma-separated list of full URLs (including protocol):

```bash
# ✅ Correct format
CORS_ORIGINS="http://localhost:5173,http://localhost:5174,https://app.example.com,https://preview.vercel.app"

# ❌ Incorrect formats
CORS_ORIGINS="localhost:5173"  # Missing protocol
CORS_ORIGINS="https://app.example.com/"  # Trailing slash (will cause mismatch)
CORS_ORIGINS="https://app.example.com https://preview.vercel.app"  # Space-separated (must be comma-separated)
```

### Environment-Specific Configuration

#### Development

```bash
CORS_ORIGINS="http://localhost:5173,http://localhost:5174"
```

Development typically only needs localhost origins for local frontend development.

#### Staging

```bash
CORS_ORIGINS="http://localhost:5173,http://localhost:5174,https://morningai-staging.vercel.app,https://owner-console-staging.vercel.app,https://morningai-git-feature-branch-abc123.vercel.app,https://owner-console-git-feature-branch-abc123.vercel.app"
```

Staging should include:
- Localhost origins (for local testing against staging backend)
- Staging deployment URLs
- Vercel preview URLs for active feature branches

**Note**: Vercel preview URLs follow the pattern `https://{app}-git-{branch}-{hash}.vercel.app`. You need to add each preview URL explicitly to `CORS_ORIGINS` in Render.com when testing feature branches.

#### Production

```bash
CORS_ORIGINS="https://morningai.com,https://app.morningai.com,https://owner-console.morningai.com"
```

Production should ONLY include production domains. Never include:
- Localhost origins
- Staging domains
- Vercel preview URLs (blocked by `is_vercel_preview()` for security)

### Vercel Preview URL Handling

The backend includes special logic to automatically allow Vercel preview URLs in non-production environments:

```python
def is_vercel_preview(origin):
    """
    Check if origin is a Vercel preview URL.
    Allows Vercel preview origins in staging and development environments.
    Blocks them in production for security.
    """
    if not origin:
        return False
    
    env = (app_settings.environment or "").lower()
    
    if env == "production":
        return False  # Block Vercel previews in production
    
    # Allow Vercel preview URLs in staging/development
    return bool(re.match(r"^https://.*\.vercel\.app$", origin))
```

**Behavior**:
- **Staging/Development**: Vercel preview URLs (`*.vercel.app`) are automatically allowed even if not in `CORS_ORIGINS`
- **Production**: Vercel preview URLs are blocked for security, regardless of `CORS_ORIGINS` setting

### Render.com Configuration

To set `CORS_ORIGINS` in Render.com:

1. Go to your service (e.g., `morningai-backend-v2-stg`)
2. Navigate to **Environment** tab
3. Add environment variable:
   - **Key**: `CORS_ORIGINS`
   - **Value**: Comma-separated list of origins (no spaces around commas)
4. Click **Save Changes**
5. Render.com will automatically redeploy (2-3 minutes)

### CORS_DEBUG Environment Variable

The `CORS_DEBUG` environment variable controls whether CORS debug logging is enabled. This is useful for troubleshooting CORS issues in development and staging environments.

**Name**: `CORS_DEBUG`  
**Type**: `boolean`  
**Default**: `false`  
**Security Level**: Public

#### Gate Behavior

`CORS_DEBUG` is force-disabled in production environments for security reasons:

```python
cors_debug_enabled = _as_bool(os.getenv("CORS_DEBUG")) and not app_settings.is_production
```

To see CORS debug logs, you must satisfy **both** conditions:
1. `CORS_DEBUG=true` (explicitly enabled)
2. `LOG_LEVEL=DEBUG` (logging level set to DEBUG)

**Environment Behavior**:
- **Production**: CORS debug logs are **never** emitted, regardless of `CORS_DEBUG` setting
- **Staging/Development**: CORS debug logs are emitted only when `CORS_DEBUG=true` AND `LOG_LEVEL=DEBUG`

#### Sanitized Output

CORS debug logs are sanitized to prevent information leakage. They only output:
- Boolean status flags (`origin_present`, `in_allowlist`, `is_preview`)
- Counts (`allowlist_count`)
- Environment name

They **never** output:
- Raw origin URLs
- Complete allowlist contents
- Environment variable values

### Verification

After deploying with `CORS_ORIGINS` configured and `CORS_DEBUG=true` + `LOG_LEVEL=DEBUG`, check the startup logs:

```
[CORS DEBUG] Startup: env=staging, allowlist_count=3
```

When a request is made, you should see sanitized logs:

```
[CORS DEBUG] add_cors_headers: origin_present=True, in_allowlist=True, is_preview=False, allowlist_count=3
[CORS DEBUG] add_cors_headers: headers_added=True
```

### Troubleshooting

#### Issue: CORS_ORIGINS environment variable not loaded

**Symptom**: Backend logs show default localhost values even though `CORS_ORIGINS` is set in Render.com.

**Root Cause**: The `cors_origins` field in `settings.py` was missing the `alias="CORS_ORIGINS"` configuration, causing Pydantic to look for lowercase `cors_origins` instead of uppercase `CORS_ORIGINS`.

**Solution**: Ensure the field definition includes the alias (fixed in PR #1247):

```python
cors_origins: str = Field(
    default="http://localhost:5173,http://localhost:5174",
    alias="CORS_ORIGINS",  # ← Required for Pydantic to load CORS_ORIGINS env var
    description="CORS allowed origins (comma-separated)"
)
```

#### Issue: ENVIRONMENT variable not loaded (staging reads as production)

**Symptom**: Backend logs show `env='production'` even though `ENVIRONMENT=staging` is set in Render.com. This causes `is_vercel_preview()` to block all Vercel preview URLs, resulting in CORS errors.

**Root Cause**: The `environment` field in `settings.py` was missing the `alias="ENVIRONMENT"` configuration. Pydantic's `model_config` has `case_sensitive=True`, so it only reads the exact field name `environment` (lowercase) and ignores `ENVIRONMENT` (uppercase).

**Diagnosis**: Check backend startup logs for:
```
[CORS DEBUG] Startup: env=staging, allowlist_count=3
[CORS DEBUG] is_vercel_preview: blocked_by_production=True  # ← Should not appear in staging!
```

If `env='production'` when `ENVIRONMENT=staging` is set, the alias is missing.

**Solution**: Ensure the field definition includes the alias (fixed in this PR):

```python
environment: Literal["development", "staging", "production"] = Field(
    default="production",
    alias="ENVIRONMENT",  # ← Required for Pydantic to load ENVIRONMENT env var
    description="Deployment environment"
)

flask_env: Literal["development", "staging", "production"] = Field(
    default="development",
    alias="FLASK_ENV",  # ← Required for Pydantic to load FLASK_ENV env var
    description="Flask environment mode"
)
```

**Impact**: Without this alias, staging backends default to `environment='production'`, which:
- Blocks all Vercel preview URLs (security feature)
- Causes CORS errors for preview deployments
- Prevents 2FA testing on preview environments

#### Issue: CORS errors in browser console

**Symptom**: Browser shows "Access to fetch at '...' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present"

**Diagnosis**:
1. Check backend logs for `[CORS DEBUG]` lines (requires `CORS_DEBUG=true` and `LOG_LEVEL=DEBUG`)
2. Verify `in_allowlist=True` or `is_preview=True` in the logs
3. Verify `headers_added=True` log appears

**Common Causes**:
- Origin URL has trailing slash (e.g., `https://app.example.com/` vs `https://app.example.com`)
- Protocol mismatch (e.g., `http://` vs `https://`)
- Origin not in `CORS_ORIGINS` environment variable
- Typo in origin URL

#### Issue: Vercel preview URLs not working in staging

**Symptom**: Vercel preview URLs show CORS errors even though `ENVIRONMENT=staging`.

**Diagnosis**:
1. Check backend logs for `[CORS DEBUG] is_vercel_preview:` lines (requires `CORS_DEBUG=true` and `LOG_LEVEL=DEBUG`)
2. Verify `blocked_by_production=True` does NOT appear (indicates production environment)
3. Check `is_vercel_pattern=True` appears for Vercel preview URLs

**Solution**: Ensure `ENVIRONMENT=staging` is set in Render.com and backend has redeployed with the latest code.

### Security Considerations

1. **Never use `*` (wildcard) for CORS origins** when credentials are involved - browsers will reject it
2. **Always include protocol** (`https://`) in origin URLs
3. **No trailing slashes** in origin URLs - they must match exactly
4. **Production should only include production domains** - never include staging or preview URLs
5. **Vercel preview URLs are automatically blocked in production** for security

### Testing

Unit tests for CORS configuration are located in `handoff/20250928/40_App/api-backend/tests/test_cors_config.py`:

- `test_cors_origins_env_var_loaded_via_alias`: Verifies `CORS_ORIGINS` environment variable is loaded
- `test_cors_headers_added_for_allowed_origin`: Verifies CORS headers are added for allowed origins
- `test_cors_headers_not_added_for_disallowed_origin`: Verifies CORS headers are not added for disallowed origins
- `test_vercel_preview_allowed_in_staging`: Verifies Vercel preview URLs are allowed in staging
- `test_vercel_preview_blocked_in_production`: Verifies Vercel preview URLs are blocked in production

Run tests with:

```bash
pytest handoff/20250928/40_App/api-backend/tests/test_cors_config.py -v
```

### Related Documentation

- [Environment Variables Schema](./env_schema.md)
- [Vercel Deployment Strategy](../deployment/VERCEL_DEPLOYMENT_STRATEGY.md)
- [Vercel Environment Variables](../deployment/VERCEL_ENVIRONMENT_VARIABLES.md)

## Owner Console Feature Flags

### VITE_FEATURE_OWNER_CONSOLE_API

Controls whether the Owner Console uses real backend authentication or mock data.

**Type**: `boolean`  
**Default**: `true` (in production builds), `false` (in development)  
**Category**: Frontend  
**Security Level**: Public

#### Behavior

**Production Builds** (`import.meta.env.PROD = true`):
- **Default**: `true` - Uses real backend API
- **Priority**: Environment variable → Default (true)
- **Security**: URL parameters and localStorage are **ignored** in production to prevent accidental mock auth in production/staging

**Development Builds** (`import.meta.env.DEV = true`):
- **Default**: `false` - Uses mock authentication for local development
- **Priority**: URL params → localStorage → Environment variable → Default (false)
- **Flexibility**: Developers can override via URL or localStorage for testing

#### Priority Order

**Development**:
```
URL Parameter > localStorage > Environment Variable > Default (false)
```

**Production**:
```
Environment Variable > Default (true)
```
*Note: URL parameters and localStorage are ignored in production for security*

#### Usage Examples

**Set via Environment Variable** (recommended for production/staging):
```bash
# Enable real backend (production default)
VITE_FEATURE_OWNER_CONSOLE_API=true

# Disable (use mock auth - development only)
VITE_FEATURE_OWNER_CONSOLE_API=false
```

**Override via URL Parameter** (development only):
```
# Enable real backend
http://localhost:5173/?feature_OWNER_CONSOLE_API=true

# Disable (use mock auth)
http://localhost:5173/?feature_OWNER_CONSOLE_API=false
```

**Override via localStorage** (development only):
```javascript
// Enable real backend
localStorage.setItem('feature_flag_OWNER_CONSOLE_API', 'true');

// Disable (use mock auth)
localStorage.setItem('feature_flag_OWNER_CONSOLE_API', 'false');

// Clear override
localStorage.removeItem('feature_flag_OWNER_CONSOLE_API');
```

**Programmatic Access**:
```javascript
import { isFeatureEnabled, setFeatureFlag, clearFeatureFlag } from '@/lib/feature-flags';

// Check if feature is enabled
const useRealBackend = isFeatureEnabled('OWNER_CONSOLE_API');

// Set flag (development only - localStorage)
setFeatureFlag('OWNER_CONSOLE_API', true);

// Clear flag
clearFeatureFlag('OWNER_CONSOLE_API');
```

#### Security Considerations

1. **Production Lock**: In production builds, URL parameters and localStorage overrides are **disabled** for `OWNER_CONSOLE_API` to prevent users from accidentally enabling mock authentication in production/staging environments.

2. **Mock Auth Warning**: When `OWNER_CONSOLE_API` is disabled in production, the application throws an error instead of falling back to mock authentication:
   ```
   Backend API is not configured. Please contact your system administrator.
   (OWNER_CONSOLE_API feature flag is disabled in production)
   ```

3. **CORS Requirements**: When using real backend authentication, ensure:
   - Backend CORS is configured to allow the Owner Console origin
   - `CORS_ORIGINS` environment variable includes the Owner Console URL
   - Example: `CORS_ORIGINS=https://owner-console.vercel.app,https://owner-console-preview.vercel.app`

#### Debugging

Enable debug logging to see feature flag resolution:

**Development** (automatic):
```javascript
// Debug logs are automatically enabled in development
// Console output: [Feature Flags] OWNER_CONSOLE_API resolved from url: true
```

**Production** (manual):
```javascript
// Enable debug logging
localStorage.setItem('debug_feature_flags', 'true');

// Disable debug logging
localStorage.removeItem('debug_feature_flags');
```

#### Related Configuration

- **Backend API URL**: `VITE_API_BASE_URL` (default: `http://localhost:5001`)
- **CORS Origins**: `CORS_ORIGINS` (backend setting)
- **2FA Settings**: `FEATURE_2FA_ENABLED`, `FEATURE_2FA_PREAUTH`

#### Migration Notes

**Before** (hardcoded mock check):
```javascript
const useMockAuth = import.meta.env.VITE_USE_MOCK === 'true';
```

**After** (feature flag):
```javascript
import { isFeatureEnabled } from '@/lib/feature-flags';

const useRealBackend = isFeatureEnabled('OWNER_CONSOLE_API');
```

#### Troubleshooting

**Problem**: Owner Console shows "Mock User" in production

**Solution**: Verify environment variables are set correctly:
```bash
# Check Vercel environment variables
vercel env ls

# Should show:
# VITE_FEATURE_OWNER_CONSOLE_API = true (Production, Preview)
# VITE_API_BASE_URL = https://api.morningai.com (Production)
```

**Problem**: CORS errors when using real backend

**Solution**: Add Owner Console origin to backend CORS configuration:
```bash
# Backend environment variable
CORS_ORIGINS=https://owner-console.vercel.app,https://owner-console-git-*.vercel.app
```

**Problem**: Feature flag not updating after environment variable change

**Solution**: Vite injects environment variables at build time. Redeploy to pick up new values:
```bash
# Trigger new deployment
git commit --allow-empty -m "Redeploy to update env vars"
git push
```
