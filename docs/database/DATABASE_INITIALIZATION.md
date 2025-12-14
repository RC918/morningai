# Database Initialization Guide

This document describes the database initialization module extracted from `main.py` as part of Phase 1 refactoring (PR1e).

## Overview

The database initialization logic is located in `src/extensions/database.py` and provides:

1. **Database Configuration** - SQLAlchemy URI and engine options setup
2. **Environment-Aware Initialization** - Different paths for testing, production, and development
3. **Production Safety Guards** - Redis validation and retry logic with exponential backoff
4. **Test Mode Safety Net** - Ensures tables exist before each request in test mode

## Module Functions

### `configure_database(app, app_settings, db)`

Configures SQLAlchemy database settings for the Flask app.

**Parameters:**
- `app`: Flask application instance
- `app_settings`: Application settings object (from `common.config.settings`)
- `db`: SQLAlchemy database instance (from `src.models.user`)

**Behavior by Environment:**

| Environment | DATABASE_URL Set | Behavior |
|-------------|------------------|----------|
| Production | Yes (PostgreSQL) | Uses DATABASE_URL, validates not SQLite |
| Production | No | Raises `RuntimeError` (fail-fast) |
| Production | SQLite | Raises `RuntimeError` (ephemeral storage not allowed) |
| Development | Yes (PostgreSQL) | Uses DATABASE_URL |
| Development | No or SQLite | Uses local SQLite at `src/database/app.db` |
| Testing | Any | Uses SQLite in-memory with `StaticPool` |

**Test Mode Detection:**

Test mode is detected when either:
- `"pytest"` is in `sys.modules` (running under pytest)
- `app_settings.testing` is `True` (TESTING env var)

When test mode is detected:
- `app.config["TESTING"] = True`
- Uses `sqlite://` (in-memory)
- Uses `StaticPool` for connection pooling (thread-safe for tests)

### `initialize_database(app, db, app_settings)`

High-level entry point for conditional database initialization.

**Parameters:**
- `app`: Flask application instance
- `db`: SQLAlchemy database instance
- `app_settings`: Application settings object

**Initialization Flow:**

```
if app.config.get("TESTING"):
    init_test_database(app, db)
    _register_test_db_safety_net(app, db)
elif ENVIRONMENT == "production":
    validate_rate_limit_redis(app_settings)
    init_database_with_retry(app, db)
else:
    # Development: simple create_all()
    with app.app_context():
        db.create_all()
```

## Retry/Backoff Configuration

### `init_database_with_retry(app, db, max_retries=6, initial_delay=0.5)`

Handles transient connection issues during deployment with exponential backoff.

**Default Configuration:**
- `max_retries`: 6 attempts
- `initial_delay`: 0.5 seconds

**Retry Schedule:**

| Attempt | Delay Before Retry |
|---------|-------------------|
| 1 | 0.5s |
| 2 | 1.0s |
| 3 | 2.0s |
| 4 | 4.0s |
| 5 | 8.0s |
| 6 | 16.0s |
| **Total** | **~31.5s** |

**Why Retry Logic is Needed:**

This handles transient connection issues during deployment, especially with Supabase Session pooler which may briefly refuse connections during:
- Cold starts
- Network blips
- Connection pool exhaustion

**Customizing Retry Behavior:**

Currently, retry parameters are hardcoded. To customize:

```python
# In src/extensions/database.py
init_database_with_retry(app, db, max_retries=10, initial_delay=1.0)
```

**Future Enhancement:** Consider making these configurable via environment variables (see Epic #2374 follow-up).

## Redis Validation Guide

### `validate_rate_limit_redis(app_settings)`

Validates Redis connection for rate limiting in production.

**Purpose:**

Provides fail-fast behavior: if Redis is unavailable in production, the application will refuse to start rather than running without rate limiting protection.

**Why This Matters:**

- Rate limiting prevents DoS attacks
- Running production without rate limiting is a security risk
- Better to fail at startup than silently run unprotected

**Configuration:**

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `RATE_LIMIT_FAIL_FAST` | `true` | Enable/disable fail-fast behavior |
| `REDIS_URL` | - | Primary Redis connection URL |
| `UPSTASH_REDIS_REST_URL` | - | Alternative Redis URL (Upstash) |

**Disabling Fail-Fast (Not Recommended):**

```bash
# Emergency override - NOT RECOMMENDED for production
export RATE_LIMIT_FAIL_FAST=false
```

**Troubleshooting Redis Connection:**

1. **Check Redis URL is set:**
   ```bash
   echo $REDIS_URL
   echo $UPSTASH_REDIS_REST_URL
   ```

2. **Test Redis connection manually:**
   ```python
   import redis
   r = redis.from_url(os.environ['REDIS_URL'])
   r.ping()  # Should return True
   ```

3. **Common Issues:**
   - Missing `REDIS_URL` environment variable
   - Firewall blocking Redis port (usually 6379)
   - Redis server not running
   - Invalid credentials in URL

## Test Mode Safety Net

### `_register_test_db_safety_net(app, db)`

Registers a `before_request` handler that ensures tables exist before each request in test mode.

**Why This is Needed:**

In test mode, the SQLite in-memory database may lose tables between requests if:
- The connection is closed and reopened
- A new thread handles the request
- The test framework resets state

**How It Works:**

```python
@app.before_request
def ensure_tables():
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    if "agents" not in existing_tables or "tasks" not in existing_tables:
        db.create_all()
```

**Performance Note:**

This check runs before every request in test mode. The overhead is minimal because:
- `inspect()` is a lightweight operation
- `create_all()` is only called if tables are missing
- This only runs in test mode, not production

## Usage Examples

### Basic Usage (Already Configured in main.py)

```python
from src.extensions.database import configure_database, initialize_database
from src.models.user import db
from common.config.settings import get_settings

app = Flask(__name__)
app_settings = get_settings()

# Configure database (sets up URI, engine options)
configure_database(app, app_settings, db)

# Initialize database (creates tables, validates Redis in production)
initialize_database(app, db, app_settings)
```

### Testing with Custom Configuration

```python
import pytest
from flask import Flask
from src.models.user import db
from src.extensions.database import configure_database, initialize_database

@pytest.fixture
def test_app():
    """Create a test Flask app with database configured."""
    app = Flask(__name__)
    
    # Mock settings for testing
    class MockSettings:
        testing = True
        environment = "development"
        database_url = None
        rate_limit_fail_fast = False
    
    configure_database(app, MockSettings(), db)
    initialize_database(app, db, MockSettings())
    
    yield app
```

## Logging Messages

All logging messages are preserved verbatim from the original `main.py` implementation:

| Level | Message | When |
|-------|---------|------|
| CRITICAL | `"FATAL: Production environment requires DATABASE_URL to be set"` | Production without DATABASE_URL |
| CRITICAL | `"FATAL: Production environment cannot use SQLite (ephemeral storage)"` | Production with SQLite |
| INFO | `"Database configured: {driver} (host: {host})"` | Successful configuration |
| INFO | `"Test mode detected: Using SQLite in-memory with StaticPool"` | Test mode |
| INFO | `"Rate limit fail-fast disabled via RATE_LIMIT_FAIL_FAST=false"` | Fail-fast disabled |
| INFO | `"Rate limiting Redis connection validated at startup"` | Redis validation success |
| CRITICAL | `"FATAL: Rate limiting Redis unavailable in production: {error}"` | Redis validation failure |
| INFO | `"Database tables initialized successfully"` | Successful initialization |
| WARNING | `"Database initialization attempt {n}/{max} failed: {error}"` | Retry attempt |
| INFO | `"Retrying in {delay}s..."` | Before retry |
| CRITICAL | `"FATAL: Failed to initialize database after {max} attempts: {error}"` | All retries exhausted |
| INFO | `"Test database tables initialized (SQLite in-memory)"` | Test DB initialized |

## Related Documentation

- [Phase 1 Refactoring Plan](../PHASE1_MAIN_PY_REFACTORING_PLAN.md) - Overall refactoring strategy
- [Environment Schema](../../config/env.schema.yaml) - Environment variable definitions
- [Settings Documentation](../config/settings.md) - Application settings reference
- [Migrations Guide](./MIGRATIONS.md) - Database migration procedures

## Troubleshooting

### "Production must have DATABASE_URL configured"

**Cause:** Running in production environment without `DATABASE_URL` set.

**Solution:**
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### "Production must use PostgreSQL, not SQLite"

**Cause:** `DATABASE_URL` starts with `sqlite://` in production.

**Solution:** Use PostgreSQL for production deployments.

### "Production environment requires Redis for rate limiting"

**Cause:** Redis is unavailable and `RATE_LIMIT_FAIL_FAST` is not disabled.

**Solution:**
1. Ensure Redis is running and accessible
2. Set `REDIS_URL` or `UPSTASH_REDIS_REST_URL`
3. (Emergency only) Set `RATE_LIMIT_FAIL_FAST=false`

### Database initialization fails after multiple retries

**Cause:** Persistent database connection issues.

**Solution:**
1. Check database server is running
2. Verify connection string is correct
3. Check network connectivity
4. Review database server logs
