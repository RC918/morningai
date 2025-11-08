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
