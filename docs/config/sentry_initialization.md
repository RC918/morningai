# Sentry Initialization Documentation

## Overview

The `src/extensions/sentry.py` module provides centralized Sentry error tracking initialization for the MorningAI Flask application. This module was extracted from `main.py` as part of Phase 1 refactoring (PR1f) to improve code organization and testability.

**Location**: `handoff/20250928/40_App/api-backend/src/extensions/sentry.py`
**Related**: `docs/sentry-alerts.md` (Alert rules configuration)

## Key Functions

The module exports two main functions:

1. **`init_sentry(app_settings, _as_bool_func)`** - Initialize Sentry SDK with proper configuration
2. **`before_send(event, hint)`** - Filter callback to reduce noise from 400/404 errors

## Quick Start

### Basic Usage with Settings

```python
from common.config.settings import settings as app_settings
from src.utils.helpers import _as_bool
from src.extensions.sentry import init_sentry

sentry_dsn = init_sentry(app_settings, _as_bool)

if sentry_dsn:
    print(f"Sentry initialized with DSN: {sentry_dsn[:20]}...")
else:
    print("Sentry not initialized (disabled or no DSN)")
```

### Usage in main.py

```python
from common.config.settings import settings as app_settings
from src.utils.helpers import _as_bool
from src.extensions.sentry import init_sentry

SENTRY_DSN = init_sentry(app_settings, _as_bool)
```

## Configuration

### Required Settings

The `init_sentry()` function requires an `app_settings` object with the following attributes:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `sentry_dsn` | `str` or `None` | Sentry DSN URL | `https://xxx@o0.ingest.sentry.io/0` |
| `environment` | `str` or `None` | Current environment | `production`, `staging`, `development` |
| `app_version` | `str` or `None` | Application version | `8.0.0` |

### Environment Variables

The following environment variables control Sentry behavior:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SENTRY_DSN` | `str` | `None` | Sentry DSN URL (required for Sentry to initialize) |
| `ENVIRONMENT` | `str` | `development` | Current environment |
| `TESTING` | `bool` | `false` | Disables Sentry in non-production environments |
| `DISABLE_SENTRY_FOR_TESTS` | `bool` | `false` | Explicitly disables Sentry for tests |

### Environment-Specific Behavior

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     init_sentry() Decision Flow                          │
│                                                                          │
│  1. Check SENTRY_DSN                                                     │
│     └─ Empty/None: Return None (Sentry not initialized)                 │
│                                                                          │
│  2. Check disable flags (TESTING or DISABLE_SENTRY_FOR_TESTS)           │
│     ├─ Both False: Continue to initialization                           │
│     └─ Either True:                                                     │
│         ├─ Production: Log warning, IGNORE flags, initialize Sentry    │
│         └─ Non-production: Return None (Sentry disabled)               │
│                                                                          │
│  3. Initialize Sentry SDK                                                │
│     ├─ Success: Return SENTRY_DSN                                       │
│     └─ Failure: Log warning, return None                                │
└─────────────────────────────────────────────────────────────────────────┘
```

## before_send Callback Design

### Purpose

The `before_send` callback filters out common client errors (400 Bad Request, 404 Not Found) to reduce noise in Sentry and focus on actual server errors that require attention.

### How It Works

```python
def before_send(event, hint):
    """Filter out 400/404 errors to reduce noise in Sentry."""
    
    # Check exception info for HTTP errors with code attribute
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if hasattr(exc_value, "code") and exc_value.code in [400, 404]:
            return None  # Drop the event
    
    # Check event request status code
    if event.get("request", {}).get("status_code") in [400, 404]:
        return None  # Drop the event
    
    return event  # Send the event to Sentry
```

### Filtering Logic

| Scenario | Action | Reason |
|----------|--------|--------|
| HTTP 400 Bad Request | Drop | Client error, not server issue |
| HTTP 404 Not Found | Drop | Expected for invalid URLs |
| HTTP 500 Internal Server Error | Send | Server error, needs attention |
| HTTP 401 Unauthorized | Send | May indicate auth issues |
| HTTP 403 Forbidden | Send | May indicate permission issues |
| Other exceptions | Send | Unexpected errors need investigation |

### Important: Patch Target

**`before_send` is NOT re-exported from `src.main`** because Sentry SDK holds a direct reference to the function passed to `sentry_sdk.init()`.

Tests must patch the canonical location:
```python
# Correct
with patch("src.extensions.sentry.before_send"):
    ...

# Incorrect (will not work)
with patch("src.main.before_send"):
    ...
```

## Logging Policy

### Log Levels by Environment

| Environment | Sentry Init Success | Sentry Disabled | Init Failure |
|-------------|---------------------|-----------------|--------------|
| Production | `INFO` | `WARNING` (flags ignored) | `WARNING` |
| Staging | `INFO` | `INFO` | `WARNING` |
| Development | `INFO` | `INFO` | `WARNING` |
| Test | `INFO` | `INFO` | `WARNING` |

### Log Messages

**Successful Initialization**:
```
INFO: Sentry initialized successfully with release morningai@{version}
```

**Disabled in Testing Environment**:
```
INFO: Sentry disabled in testing environment (DISABLE_SENTRY_FOR_TESTS or TESTING flag is set).
```

**Production Guard Warning**:
```
WARNING: DISABLE_SENTRY_FOR_TESTS or TESTING is set but environment is production; Sentry will remain enabled to ensure error tracking in production.
```

**Initialization Failure**:
```
WARNING: Failed to initialize Sentry: {error}. Continuing without Sentry integration.
```

### Log Clarity Guidelines

1. **Production**: Always log at `WARNING` level when something unexpected happens (flags being ignored, init failure)
2. **Non-production**: Use `INFO` for expected behavior (disabled for tests)
3. **Include context**: Log messages include the release version and reason for the action
4. **No secrets**: Never log the full DSN, only confirmation of initialization

## Testing

### Unit Testing init_sentry()

```python
from unittest.mock import Mock, patch
from src.extensions.sentry import init_sentry
from src.utils.helpers import _as_bool

def test_sentry_disabled_when_testing_flag_set(monkeypatch):
    """Test Sentry is disabled when TESTING=true in development."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)
    
    mock_settings = Mock()
    mock_settings.sentry_dsn = "https://test@sentry.io/123"
    mock_settings.environment = "development"
    mock_settings.app_version = "8.0.0"
    
    with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
        result = init_sentry(mock_settings, _as_bool)
        
        mock_sentry.init.assert_not_called()
        assert result is None

def test_sentry_enabled_in_production_despite_testing_flag(monkeypatch):
    """Test production guard keeps Sentry enabled."""
    monkeypatch.setenv("TESTING", "true")
    
    mock_settings = Mock()
    mock_settings.sentry_dsn = "https://test@sentry.io/123"
    mock_settings.environment = "production"
    mock_settings.app_version = "8.0.0"
    
    with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
        with patch("src.extensions.sentry.FlaskIntegration"):
            result = init_sentry(mock_settings, _as_bool)
            
            mock_sentry.init.assert_called_once()
            assert result == "https://test@sentry.io/123"
```

### Unit Testing before_send()

```python
from src.extensions.sentry import before_send

def test_before_send_filters_400():
    """Test before_send filters out 400 errors."""
    event = {'request': {'status_code': 400}}
    hint = {}
    
    result = before_send(event, hint)
    assert result is None

def test_before_send_filters_404():
    """Test before_send filters out 404 errors."""
    event = {'request': {'status_code': 404}}
    hint = {}
    
    result = before_send(event, hint)
    assert result is None

def test_before_send_allows_500():
    """Test before_send allows 500 errors."""
    event = {'request': {'status_code': 500}}
    hint = {}
    
    result = before_send(event, hint)
    assert result == event

def test_before_send_with_exc_info():
    """Test before_send with exception info."""
    error = Exception("Test error")
    error.code = 404
    
    event = {}
    hint = {'exc_info': (type(error), error, None)}
    
    result = before_send(event, hint)
    assert result is None
```

### Integration Testing with Sentry SDK Mock

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestSentryIntegration:
    """Integration tests for Sentry initialization with Flask app."""
    
    @pytest.fixture
    def mock_flask_app(self):
        """Create a mock Flask app for testing."""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    def test_sentry_integration_with_flask(self, mock_flask_app, monkeypatch):
        """Test Sentry integrates correctly with Flask app."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)
        
        mock_settings = Mock()
        mock_settings.sentry_dsn = "https://test@sentry.io/123"
        mock_settings.environment = "staging"
        mock_settings.app_version = "8.0.0"
        
        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry
        
        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            mock_flask_integration = MagicMock()
            with patch("src.extensions.sentry.FlaskIntegration", return_value=mock_flask_integration):
                result = init_sentry(mock_settings, _as_bool)
                
                # Verify sentry_sdk.init was called with correct parameters
                mock_sentry.init.assert_called_once()
                call_kwargs = mock_sentry.init.call_args[1]
                
                assert call_kwargs["dsn"] == "https://test@sentry.io/123"
                assert call_kwargs["environment"] == "staging"
                assert call_kwargs["release"] == "morningai@8.0.0"
                assert call_kwargs["traces_sample_rate"] == 1.0
                assert mock_flask_integration in call_kwargs["integrations"]
    
    def test_sentry_captures_errors_correctly(self, mock_flask_app, monkeypatch):
        """Test that Sentry captures errors with correct filtering."""
        monkeypatch.delenv("TESTING", raising=False)
        
        mock_settings = Mock()
        mock_settings.sentry_dsn = "https://test@sentry.io/123"
        mock_settings.environment = "staging"
        mock_settings.app_version = "8.0.0"
        
        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry, before_send
        
        captured_before_send = None
        
        def capture_init(**kwargs):
            nonlocal captured_before_send
            captured_before_send = kwargs.get("before_send")
        
        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            mock_sentry.init.side_effect = capture_init
            with patch("src.extensions.sentry.FlaskIntegration"):
                init_sentry(mock_settings, _as_bool)
        
        # Verify the before_send callback is our function
        assert captured_before_send is before_send
        
        # Test the captured callback filters correctly
        assert captured_before_send({'request': {'status_code': 404}}, {}) is None
        assert captured_before_send({'request': {'status_code': 500}}, {}) is not None
```

### E2E Testing with Real Sentry SDK

For E2E testing with the real Sentry SDK (without sending to production):

```python
import pytest
import sentry_sdk
from unittest.mock import Mock

class TestSentryE2E:
    """E2E tests with real Sentry SDK (transport mocked)."""
    
    @pytest.fixture(autouse=True)
    def reset_sentry(self):
        """Reset Sentry SDK state before each test."""
        # Close any existing client
        client = sentry_sdk.get_client()
        if client:
            client.close()
        yield
        # Cleanup after test
        client = sentry_sdk.get_client()
        if client:
            client.close()
    
    def test_real_sentry_init_with_mock_transport(self, monkeypatch):
        """Test real Sentry SDK initialization with mocked transport."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)
        
        captured_events = []
        
        def mock_transport(event, hint):
            captured_events.append(event)
        
        mock_settings = Mock()
        mock_settings.sentry_dsn = "https://test@sentry.io/123"
        mock_settings.environment = "test"
        mock_settings.app_version = "8.0.0"
        
        from src.utils.helpers import _as_bool
        from src.extensions.sentry import before_send
        
        # Initialize with real SDK but mock transport
        sentry_sdk.init(
            dsn=mock_settings.sentry_dsn,
            environment=mock_settings.environment,
            release=f"morningai@{mock_settings.app_version}",
            before_send=before_send,
            transport=mock_transport,
        )
        
        # Capture a test error
        try:
            raise ValueError("Test error for E2E")
        except ValueError:
            sentry_sdk.capture_exception()
        
        # Verify event was captured (not filtered)
        assert len(captured_events) >= 1
```

## Troubleshooting

### Sentry Not Initializing

**Symptoms**: No errors in Sentry dashboard, `SENTRY_DSN` returns `None`

**Check**:
1. Verify `SENTRY_DSN` environment variable is set
2. Check if `TESTING=true` or `DISABLE_SENTRY_FOR_TESTS=true`
3. Look for log messages about Sentry being disabled

### Events Not Appearing in Sentry

**Symptoms**: Sentry initialized but events not showing

**Check**:
1. Verify the error is not 400/404 (filtered by `before_send`)
2. Check Sentry dashboard filters (environment, time range)
3. Verify DSN is correct and project is active

### Production Guard Not Working

**Symptoms**: Sentry disabled in production despite flags

**Check**:
1. Verify `ENVIRONMENT=production` is set correctly
2. Check logs for production guard warning message
3. Ensure `app_settings.environment` returns `"production"`

## Migration Notes

### From main.py Inline Code

**Before (main.py)**:
```python
# Inline Sentry initialization
TESTING = _as_bool(os.getenv("TESTING"))
DISABLE_SENTRY_FOR_TESTS = _as_bool(os.getenv("DISABLE_SENTRY_FOR_TESTS"))
disable_sentry = DISABLE_SENTRY_FOR_TESTS or TESTING

if sentry_dsn and not disable_sentry:
    sentry_sdk.init(...)
```

**After (main.py)**:
```python
from src.extensions.sentry import init_sentry

SENTRY_DSN = init_sentry(app_settings, _as_bool)
```

### Test Import Path Changes

**Before**:
```python
from src.main import before_send
```

**After**:
```python
from src.extensions.sentry import before_send
```

## Related Documentation

- [Sentry Alert Rules](../sentry-alerts.md) - Alert configuration
- [Settings Module](./settings.md) - Environment variable management
- [Phase 1 Refactoring Plan](../PHASE1_MAIN_PY_REFACTORING_PLAN.md) - Refactoring context
