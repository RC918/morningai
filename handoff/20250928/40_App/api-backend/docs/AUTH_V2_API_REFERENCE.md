# Auth V2 API Reference

## 2FA Pre-Authentication Flow

### Overview

The 2FA pre-authentication flow uses temporary JWT tokens to manage the multi-step authentication process. These tokens are single-use and have a short TTL (5 minutes).

### Migration from Legacy Endpoints

**IMPORTANT**: The legacy `/api/auth/v2/totp/setup` endpoint is deprecated and will be removed in a future version.

**Why the change?**
- Legacy endpoint requires JWT authentication (`@jwt_required`)
- This breaks forced 2FA flows where users must enroll before getting a JWT
- New pre-auth endpoints use temporary tokens instead, enabling forced enrollment

**Migration Guide:**

| Legacy Endpoint | New Endpoint | Key Difference |
|----------------|--------------|----------------|
| `POST /api/auth/v2/totp/setup` | `POST /api/auth/v2/2fa/enroll` | Uses `pre_auth_token` instead of JWT |
| `POST /api/auth/v2/totp/verify-setup` | `POST /api/auth/v2/2fa/verify-enroll` | Uses `pre_auth_token` instead of JWT |
| N/A | `POST /api/auth/v2/2fa/challenge` | New endpoint for login verification |

**New Flow:**
1. User logs in → receives `tmp_login_token` with `next_step` indicator
2. If `next_step: "enroll_2fa"` → call `/2fa/enroll` with `tmp_login_token`
3. User scans QR code → call `/2fa/verify-enroll` with TOTP code
4. Receive backup codes + full session tokens

**Legacy Flow (deprecated):**
1. User logs in → receives full JWT session
2. Call `/totp/setup` with JWT + password
3. Receive QR code + backup codes immediately (security issue)

### Endpoints

#### POST /api/auth/v2/login
Initial login endpoint that returns either a full session (if 2FA not enabled) or a temporary token for 2FA flow.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (2FA Not Enabled):**
```json
{
  "success": true,
  "user": { ... },
  "tokens": { "expiresAt": 1234567890000 }
}
```

**Response (2FA Enrollment Required):**
```json
{
  "next_step": "enroll_2fa",
  "tmp_login_token": "eyJhbGc...",
  "message": "2FA enrollment required"
}
```

**Response (2FA Challenge Required):**
```json
{
  "next_step": "challenge_2fa",
  "tmp_login_token": "eyJhbGc...",
  "message": "2FA verification required"
}
```

#### POST /api/auth/v2/2fa/enroll
Start 2FA enrollment process. Requires temporary token with `enroll` scope.

**Headers:**
```
Authorization: Bearer <tmp_login_token>
```

**Response:**
```json
{
  "success": true,
  "qr_code": "data:image/png;base64,...",
  "secret": "JBSWY3DPEHPK3PXP",
  "message": "Scan QR code with authenticator app"
}
```

#### POST /api/auth/v2/2fa/verify-enroll
Complete 2FA enrollment by verifying TOTP code. Consumes the temporary token atomically.

**Headers:**
```
Authorization: Bearer <tmp_login_token>
```

**Request:**
```json
{
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "backup_codes": ["XXXX-XXXX-XXXX-XXXX", ...],
  "user": { ... },
  "tokens": { "expiresAt": 1234567890000 }
}
```

#### POST /api/auth/v2/2fa/challenge
Verify 2FA code during login. Consumes the temporary token atomically.

**Headers:**
```
Authorization: Bearer <tmp_login_token>
```

**Request:**
```json
{
  "code": "123456",
  "remember_device": false
}
```

**Response:**
```json
{
  "success": true,
  "user": { ... },
  "tokens": { "expiresAt": 1234567890000 },
  "backup_codes_remaining": 7,
  "device_trusted": false
}
```

### Error Codes

#### TMP_TOKEN_CONSUMED (401)
The temporary token has already been used. This error occurs when attempting to reuse a single-use token.

**Example:**
```json
{
  "error": "TMP_TOKEN_CONSUMED",
  "message": "This token has already been used."
}
```

**Cause:** Concurrent requests or replay attacks attempting to use the same temporary token multiple times.

**Resolution:** Request a new temporary token by logging in again.

#### SCOPE_MISSING (401)
The request is missing the required pre-authentication scope. This typically indicates a middleware configuration error.

**Example:**
```json
{
  "error": "SCOPE_MISSING",
  "message": "Pre-authentication scope not found. Use @pre_auth_required first."
}
```

**Cause:** The endpoint is decorated with `@pre_auth_scope_required` but not `@pre_auth_required`, or the token doesn't contain a scope claim.

**Resolution:** This is typically a server-side configuration issue. Contact support if you encounter this error.

#### SCOPE_MISMATCH (403)
The temporary token has a different scope than required for this endpoint.

**Example:**
```json
{
  "error": "SCOPE_MISMATCH",
  "message": "Token scope 'challenge' does not match required scope 'enroll'"
}
```

**Cause:** Using an enrollment token for challenge endpoint or vice versa.

**Resolution:** Use the correct endpoint for your token's scope.

#### TMP_TOKEN_INVALID (401)
The temporary token is malformed, expired, or invalid.

**Example:**
```json
{
  "error": "TMP_TOKEN_INVALID",
  "message": "Token is expired or malformed"
}
```

**Cause:** Token has expired (5 minute TTL), is malformed, or has been revoked.

**Resolution:** Request a new temporary token by logging in again.

### Post-Consumption Error Semantics

When a temporary token is consumed, concurrent requests may receive:

- TMP_TOKEN_CONSUMED (401): Token exists but consumed
- TMP_TOKEN_INVALID (401): Token key no longer exists

Both indicate the token cannot be used. Clients should handle them identically.

#### TMP_TOKEN_ATTEMPTS_EXCEEDED (401)
Too many failed verification attempts with this temporary token.

**Example:**
```json
{
  "error": "TMP_TOKEN_ATTEMPTS_EXCEEDED",
  "message": "Maximum verification attempts exceeded"
}
```

**Cause:** More than 3 failed TOTP code verification attempts.

**Resolution:** Request a new temporary token by logging in again.

### Security Features

#### Atomic Token Consumption
Temporary tokens are consumed atomically using Redis WATCH/MULTI transactions to prevent race conditions. Only one request can successfully consume a token, even if multiple concurrent requests are made.

**Implementation:** Uses optimistic locking with retry mechanism (max 3 attempts) to handle contention.

#### Production JWT Secret Validation
In production environments, the system validates that `JWT_SECRET_KEY` is set to a secure value (not the default test key). The application will fail to start if this validation fails.

**Configuration Required:**
```bash
export ENVIRONMENT=production
export JWT_SECRET_KEY=<secure-random-key>
```

#### Single-Use Enforcement
Each temporary token can only be used once. After successful verification, the token is marked as consumed and cannot be reused.

#### Short TTL
Temporary tokens expire after 5 minutes to minimize the window for potential attacks.

#### Scope-Based Access Control
Tokens are scoped to specific operations (`enroll` or `challenge`) to prevent misuse across different endpoints.

### Monitoring Recommendations

After deploying the 2FA pre-authentication flow, monitor the following metrics:

1. **Token Consumption Errors**
   - Monitor `TMP_TOKEN_CONSUMED` error rate in Sentry/logs
   - High rates may indicate client-side retry logic issues or potential attacks

2. **JWT Secret Configuration**
   - Monitor application startup logs for JWT secret validation errors
   - Ensure production deployments have proper `JWT_SECRET_KEY` configured

3. **2FA Flow Success Rate**
   - Track successful enrollments vs. failures
   - Monitor challenge verification success rates
   - Alert on unusual patterns (e.g., sudden spike in failures)

4. **Redis Performance**
   - Monitor Redis latency for WATCH/MULTI operations
   - Track contention rates (WatchError occurrences)
   - Ensure Upstash Redis or equivalent supports WATCH/MULTI

### Testing in Staging

Before deploying to production, verify the atomic token consumption behavior with real Redis (Upstash):

```bash
# Run concurrent consumption test
cd handoff/20250928/40_App/api-backend
python scripts/test_staging_concurrent_consumption.py
```

This test simulates concurrent requests to verify that only one succeeds in consuming the token.
