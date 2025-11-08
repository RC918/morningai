# Deprecated Modules

This document lists modules that have been deprecated and should not be used in new code.

## Authentication & Security

### `src/utils/preauth_token.py` (Deprecated)

**Status**: Deprecated as of 2025-11-08  
**Replacement**: `src/utils/pre_auth_token.py`

**Reason**: The opaque token-based pre-auth system has been replaced with a JWT-based system that provides better security features:
- TTL preservation on token consumption
- Scope-based access control (enroll vs challenge)
- Atomic token consumption with race condition protection
- Better observability and debugging

**Migration Guide**:

| Deprecated Function | Replacement |
|---------------------|-------------|
| `generate_preauth_token(user_id, email, ttl)` | `PreAuthTokenManager.generate_token(user_id, email, scope)` |
| `validate_and_consume_preauth_token(token)` | `PreAuthTokenManager.verify_token(token)` + `PreAuthTokenManager.consume_token_atomic(jti)` |
| `revoke_preauth_tokens_for_user(user_id)` | `PreAuthTokenManager.revoke_token(jti)` |

**Example Migration**:

```python
# OLD (Deprecated)
from src.utils.preauth_token import generate_preauth_token, validate_and_consume_preauth_token

token = generate_preauth_token(user_id, email, ttl=300)
user_data = validate_and_consume_preauth_token(token)

# NEW (Recommended)
from src.utils.pre_auth_token import get_pre_auth_manager

pre_auth_manager = get_pre_auth_manager()
token = pre_auth_manager.generate_token(user_id, email, scope='challenge')
payload = pre_auth_manager.verify_token(token)
if payload:
    jti = payload.get('jti')
    success = pre_auth_manager.consume_token_atomic(jti)
```

**CI Enforcement**: A lint check (`tests/lint/test_no_deprecated_imports.py`) will fail if production code (`src/**`) imports this module.

---

## How to Add a Deprecated Module

When deprecating a module:

1. **Add deprecation warnings** to the module:
   ```python
   import warnings
   
   def deprecated_function():
       warnings.warn(
           "deprecated_function() is deprecated. Use new_function() instead.",
           DeprecationWarning,
           stacklevel=2
       )
       # ... existing implementation
   ```

2. **Update this document** with:
   - Module path
   - Deprecation date
   - Replacement module/function
   - Migration guide with examples

3. **Add to lint check** in `tests/lint/test_no_deprecated_imports.py`:
   ```python
   DEPRECATED_MODULES = [
       "utils.old_module",
       "src.utils.old_module",
   ]
   ```

4. **Update PR template** to include the deprecated module in the checklist

5. **Communicate** the deprecation to the team via:
   - PR description
   - Team chat/Slack
   - Code review comments

## Enforcement

Deprecated modules are enforced through:

1. **CI Lint Check**: `tests/lint/test_no_deprecated_imports.py` scans `src/**` for imports of deprecated modules and fails CI if found
2. **PR Template**: Checklist item reminds developers to avoid deprecated modules
3. **Deprecation Warnings**: Runtime warnings when deprecated functions are called
4. **Documentation**: This file serves as the source of truth for deprecated modules

## Testing Deprecated Modules

Tests (`tests/**`) are allowed to import deprecated modules for backward compatibility testing. The lint check excludes the `tests/` directory.
