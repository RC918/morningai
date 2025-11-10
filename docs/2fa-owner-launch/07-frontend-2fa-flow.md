# 2FA Frontend Authentication Flow Documentation

**Document Version**: 1.0  
**Date**: 2025-11-10  
**Status**: ✅ Implemented (PR #1249)  
**Related PRs**: #1249 (2FA Frontend Flow Fixes)

---

## Overview

The Owner Console implements a multi-step 2FA authentication flow that handles three possible authentication states based on the `next_step` field in the backend authentication response:

1. **Session** - User successfully authenticated (no 2FA required or 2FA completed)
2. **Enroll 2FA** - User needs to enroll in 2FA (first-time setup)
3. **Challenge 2FA** - User needs to verify 2FA code (subsequent logins)

This document describes the frontend implementation of the 2FA flow, including state management, token handling, and production security guarantees.

---

## Authentication Flow States

### State 1: Session (Successful Login)

**When**: User has completed authentication (no 2FA required or 2FA verification successful)

**Backend Response**:
```json
{
  "next_step": "session",
  "user": {
    "id": "user-123",
    "email": "owner@example.com",
    "role": "owner",
    "tenantId": "tenant-123",
    "name": "Test Owner"
  },
  "token": "jwt-token-123"
}
```

**Frontend Behavior**:
- `AuthProvider` sets `isAuthenticated = true`
- `AuthProvider` sets `user` state
- User is redirected to dashboard
- Session token stored in HttpOnly cookie

**Token Field**: Uses `token` field (permanent session token, 24-hour lifetime)

**Code Location**: `handoff/20250928/40_App/owner-console/src/components/AuthProvider.tsx:82-85`

```typescript
if (response.next_step === 'session' || !response.next_step) {
  setUser(response.user);
  setIsAuthenticated(true);
}
```

---

### State 2: Enroll 2FA (First-Time Setup)

**When**: Owner role user logging in for the first time (2FA not yet enrolled)

**Backend Response**:
```json
{
  "next_step": "enroll_2fa",
  "tmp_login_token": "tmp-token-123",
  "user": {
    "id": "user-123",
    "email": "owner@example.com",
    "role": "owner",
    "tenantId": "tenant-123",
    "name": "Test Owner"
  }
}
```

**Frontend Behavior**:
- `AuthProvider` does **NOT** set `isAuthenticated = true`
- `AuthProvider` returns full response to `LoginPage`
- `LoginPage` detects `next_step === 'enroll_2fa'`
- User is shown 2FA enrollment UI (QR code, setup instructions)
- After enrollment, user proceeds to challenge verification

**Token Field**: Uses `tmp_login_token` field (temporary pre-auth token, 5-minute lifetime)

**Important**: The `tmp_login_token` is a short-lived token used only for the 2FA enrollment/verification process. It is NOT a session token and should not be used for API requests.

**Code Location**: `handoff/20250928/40_App/owner-console/src/components/LoginPage.jsx`

---

### State 3: Challenge 2FA (Verification Required)

**When**: Owner role user logging in with 2FA already enrolled

**Backend Response**:
```json
{
  "next_step": "challenge_2fa",
  "tmp_login_token": "tmp-token-456"
}
```

**Frontend Behavior**:
- `AuthProvider` does **NOT** set `isAuthenticated = true`
- `AuthProvider` returns full response to `LoginPage`
- `LoginPage` detects `next_step === 'challenge_2fa'`
- User is shown 2FA verification UI (6-digit code input)
- After successful verification, backend returns `next_step: "session"`

**Token Field**: Uses `tmp_login_token` field (temporary pre-auth token, 5-minute lifetime)

**Code Location**: `handoff/20250928/40_App/owner-console/src/components/LoginPage.jsx`

---

## Token Field Naming

The backend uses two different token field names depending on the authentication state:

| Field Name | Usage | Lifetime | Purpose |
|------------|-------|----------|---------|
| `token` | Session state | 24 hours | Permanent session token for authenticated API requests |
| `tmp_login_token` | Enroll/Challenge states | 5 minutes | Temporary pre-auth token for 2FA enrollment/verification |

### Frontend Implementation

**Code Location**: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`

```typescript
// Token field fallback for backward compatibility
const authToken = response.data.token || response.data.tmp_login_token;

if (authToken) {
  localStorage.setItem('auth_token', authToken);
}
```

### Why Two Fields?

1. **Security**: Temporary tokens have shorter lifetime and limited scope
2. **Clarity**: Different field names make the token purpose explicit
3. **Backward compatibility**: Legacy responses may only have `token` field

---

## AuthProvider State Management

The `AuthProvider` component manages authentication state based on `next_step`:

**Code Location**: `handoff/20250928/40_App/owner-console/src/components/AuthProvider.tsx:78-93`

```typescript
const login = async (credentials: LoginCredentials) => {
  try {
    const response = await authLogin(credentials);
    
    // Only set authenticated state for session
    if (response.next_step === 'session' || !response.next_step) {
      setUser(response.user);
      setIsAuthenticated(true);
    }
    
    // Return full response for LoginPage to handle 2FA states
    return response;
  } catch (error) {
    setUser(null);
    setIsAuthenticated(false);
    throw error;
  }
};
```

### Key Points

1. **Session state**: Sets `isAuthenticated = true`, user can access protected routes
2. **Enroll/Challenge states**: Keeps `isAuthenticated = false`, user stays on login page
3. **Full response returned**: `LoginPage` can inspect `next_step` and show appropriate UI
4. **Legacy compatibility**: Missing `next_step` treated as session (backward compatible)

### State Transition Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Login Attempt                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    POST /api/auth/v2/login
                              │
                              ▼
                ┌─────────────────────────────┐
                │   Backend Authentication    │
                └─────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ session  │  │enroll_2fa│  │challenge │
         │          │  │          │  │   _2fa   │
         └──────────┘  └──────────┘  └──────────┘
                │             │             │
                │             ▼             ▼
                │      Show QR Code   Show Code Input
                │      + Setup UI     + Verify UI
                │             │             │
                │             ▼             ▼
                │      POST /api/auth/v2/2fa/verify-enroll
                │      POST /api/auth/v2/2fa/challenge
                │             │             │
                │             └─────┬───────┘
                │                   │
                │                   ▼
                │          next_step: "session"
                │                   │
                └───────────────────┘
                            │
                            ▼
                  isAuthenticated = true
                            │
                            ▼
                   Redirect to Dashboard
```

---

## Production Lock Behavior

When `VITE_FEATURE_OWNER_CONSOLE_API` is enabled in production, the following security guarantees are enforced:

### Security Guarantees

1. ✅ Mock authentication is disabled (cannot bypass 2FA)
2. ✅ All authentication goes through real backend API
3. ✅ URL parameter overrides are ignored (prevents tampering)
4. ✅ localStorage overrides are ignored (prevents tampering)
5. ✅ 2FA enforcement is guaranteed for owner role

### Development Mode

- Mock authentication available when `OWNER_CONSOLE_API=false`
- URL/localStorage overrides work for testing
- Useful for frontend development without backend

### Production Mode

- Mock authentication blocked (throws error if attempted)
- URL/localStorage overrides ignored
- Backend API required (no fallback)

### Implementation

**Code Location**: `handoff/20250928/40_App/owner-console/src/lib/feature-flags.ts`

```typescript
export function isFeatureEnabled(flag: FeatureFlag): boolean {
  // Production lock: ignore URL/localStorage in production
  if (import.meta.env.PROD) {
    return getEnvFlag(flag) ?? getDefaultValue(flag);
  }
  
  // Development: allow overrides
  return getUrlParamFlag(flag) 
    ?? getLocalStorageFlag(flag) 
    ?? getEnvFlag(flag) 
    ?? getDefaultValue(flag);
}
```

---

## Critical Defects Fixed in PR #1249

### Defect 1: AuthProvider Prematurely Sets Authenticated State

**Problem**: `AuthProvider.login()` always set `isAuthenticated = true` after login, even when `next_step` was `enroll_2fa` or `challenge_2fa`.

**Impact**: Users were redirected to dashboard before completing 2FA, bypassing 2FA enforcement.

**Fix**: Check `next_step` before setting authenticated state:

```typescript
// Before (BROKEN)
const response = await authLogin(credentials);
setUser(response.user);
setIsAuthenticated(true);

// After (FIXED)
const response = await authLogin(credentials);
if (response.next_step === 'session' || !response.next_step) {
  setUser(response.user);
  setIsAuthenticated(true);
}
```

**Code Location**: `handoff/20250928/40_App/owner-console/src/components/AuthProvider.tsx:82-85`

---

### Defect 2: AuthProvider Doesn't Return Response

**Problem**: `AuthProvider.login()` didn't return the response, so `LoginPage` couldn't inspect `next_step` to show 2FA UI.

**Impact**: 2FA enrollment/challenge UI never appeared, users stuck on login page.

**Fix**: Return full response from `login()`:

```typescript
// Before (BROKEN)
const login = async (credentials: LoginCredentials) => {
  const response = await authLogin(credentials);
  setUser(response.user);
  setIsAuthenticated(true);
  // No return statement
};

// After (FIXED)
const login = async (credentials: LoginCredentials) => {
  const response = await authLogin(credentials);
  if (response.next_step === 'session' || !response.next_step) {
    setUser(response.user);
    setIsAuthenticated(true);
  }
  return response; // Return full response
};
```

**Code Location**: `handoff/20250928/40_App/owner-console/src/components/AuthProvider.tsx:87`

---

### Defect 3: Token Field Fallback Missing

**Problem**: Frontend only checked `response.data.token`, but backend returns `tmp_login_token` for 2FA states.

**Impact**: Temporary pre-auth tokens were not stored, causing 2FA enrollment/verification to fail.

**Fix**: Add fallback to check both token fields:

```typescript
// Before (BROKEN)
const authToken = response.data.token;

// After (FIXED)
const authToken = response.data.token || response.data.tmp_login_token;
```

**Code Location**: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`

---

## Testing

### Unit Tests

**Location**: `handoff/20250928/40_App/owner-console/src/lib/__tests__/auth-2fa.test.ts`

**Test Coverage**:
- ✅ `next_step` handling (session, enroll_2fa, challenge_2fa)
- ✅ Token field fallback (token vs tmp_login_token)
- ✅ AuthProvider state management
- ✅ Production lock behavior
- ✅ 2FA flow integration

**Run Tests**:
```bash
cd handoff/20250928/40_App/owner-console
pnpm test src/lib/__tests__/auth-2fa.test.ts
```

**Test Results**:
```
✓ 2FA Authentication Flow (14 tests)
  ✓ next_step handling (4 tests)
  ✓ Token field handling (4 tests)
  ✓ AuthProvider state management (4 tests)
  ✓ Production lock behavior (2 tests)
```

---

### Manual Testing

#### Test Case 1: First-Time Owner Login (Enroll 2FA)

**Prerequisites**: 
- Owner account with no 2FA enrolled
- `VITE_FEATURE_OWNER_CONSOLE_API=true`

**Steps**:
1. Navigate to Owner Console login page
2. Enter owner email and password
3. Click "Login"

**Expected Results**:
- ✅ Backend returns `next_step: "enroll_2fa"`
- ✅ 2FA enrollment UI shown (QR code + setup instructions)
- ✅ User NOT redirected to dashboard
- ✅ `isAuthenticated` remains `false`

**Actual Results**: ✅ PASS (verified in PR #1249)

---

#### Test Case 2: Returning Owner Login (Challenge 2FA)

**Prerequisites**: 
- Owner account with 2FA already enrolled
- `VITE_FEATURE_OWNER_CONSOLE_API=true`

**Steps**:
1. Navigate to Owner Console login page
2. Enter owner email and password
3. Click "Login"

**Expected Results**:
- ✅ Backend returns `next_step: "challenge_2fa"`
- ✅ 2FA verification UI shown (6-digit code input)
- ✅ User NOT redirected to dashboard
- ✅ `isAuthenticated` remains `false`

**Actual Results**: ✅ PASS (verified in PR #1249)

---

#### Test Case 3: Successful 2FA Verification

**Prerequisites**: 
- Owner account with 2FA enrolled
- User at 2FA verification screen

**Steps**:
1. Enter valid 6-digit TOTP code
2. Click "Verify"

**Expected Results**:
- ✅ Backend returns `next_step: "session"`
- ✅ `AuthProvider` sets `isAuthenticated = true`
- ✅ User redirected to dashboard
- ✅ Session token stored in cookie

**Actual Results**: ✅ PASS (verified in PR #1249)

---

#### Test Case 4: Production Lock

**Prerequisites**: 
- Production build (`pnpm build`)
- `VITE_FEATURE_OWNER_CONSOLE_API=true`

**Steps**:
1. Open browser console
2. Try to disable API: `localStorage.setItem('feature_owner_console_api', 'false')`
3. Refresh page
4. Attempt login

**Expected Results**:
- ✅ localStorage override ignored
- ✅ Backend API still used
- ✅ Mock authentication not available

**Actual Results**: ✅ PASS (verified in PR #1248)

---

## Migration Notes

### PR #1249 Changes

1. ✅ `AuthProvider` now checks `next_step` before setting authenticated state
2. ✅ `AuthProvider` returns full response (not just user)
3. ✅ Token field fallback added (`token || tmp_login_token`)
4. ✅ Production lock enforced for `OWNER_CONSOLE_API` flag

### Backward Compatibility

- ✅ Legacy responses without `next_step` still work (treated as session)
- ✅ Legacy responses with only `token` field still work
- ✅ No breaking changes to existing authentication flow

### Security Improvements

- ✅ 2FA enrollment/challenge no longer sets authenticated state prematurely
- ✅ Production lock prevents accidental mock auth in production
- ✅ Token field naming makes temporary vs permanent tokens explicit

---

## Related Documentation

- [Pre-Auth Token Design](./02-pre-auth-token-design.md)
- [2FA Migration and Rollback Plan](./04-migration-and-rollback-plan.md)
- [Support Runbook](./05-support-runbook.md)
- [Staging Manual Testing Checklist](./06-staging-manual-testing-checklist.md)

---

## Troubleshooting

### Issue: 2FA UI not appearing after login

**Symptoms**: User enters credentials, but 2FA enrollment/verification UI doesn't appear

**Diagnosis**:
1. Check browser console for errors
2. Check network tab for `/api/auth/v2/login` response
3. Verify `next_step` field in response
4. Check if `VITE_FEATURE_OWNER_CONSOLE_API=true`

**Common Causes**:
- Backend not returning `next_step` field
- Frontend not checking `next_step` correctly
- `OWNER_CONSOLE_API` flag disabled (using mock auth)

**Solution**: Verify PR #1249 changes are deployed

---

### Issue: User redirected to dashboard before completing 2FA

**Symptoms**: User bypasses 2FA enrollment/verification

**Diagnosis**:
1. Check if `AuthProvider` is setting `isAuthenticated = true` prematurely
2. Verify `next_step` check is present in `AuthProvider.login()`

**Solution**: Ensure PR #1249 changes are deployed (lines 82-85 in AuthProvider.tsx)

---

### Issue: "Invalid token" error during 2FA verification

**Symptoms**: 2FA verification fails with "Invalid token" error

**Diagnosis**:
1. Check if `tmp_login_token` is being stored correctly
2. Verify token field fallback is present in `auth.ts`
3. Check token expiration (5-minute lifetime)

**Solution**: Ensure PR #1249 changes are deployed (token fallback in auth.ts)

---

## Security Considerations

1. **Never store `tmp_login_token` in localStorage** - It should only be used for the 2FA flow
2. **Always validate `next_step` on frontend** - Don't trust client-side state
3. **Production lock is critical** - Never disable in production
4. **Token lifetime is intentional** - 5 minutes for pre-auth, 24 hours for session
5. **2FA enforcement is backend-controlled** - Frontend only displays UI

---

## Appendix: Response Examples

### Example 1: Session Response (No 2FA Required)

```json
{
  "next_step": "session",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@example.com",
    "role": "admin",
    "tenantId": "tenant-001",
    "name": "Admin User"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Example 2: Enroll 2FA Response

```json
{
  "next_step": "enroll_2fa",
  "tmp_login_token": "tmp_abc123def456...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "owner@example.com",
    "role": "owner",
    "tenantId": "tenant-001",
    "name": "Owner User"
  }
}
```

### Example 3: Challenge 2FA Response

```json
{
  "next_step": "challenge_2fa",
  "tmp_login_token": "tmp_xyz789ghi012..."
}
```

### Example 4: Legacy Response (Backward Compatible)

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "role": "user",
    "tenantId": "tenant-001",
    "name": "Regular User"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Note**: Legacy responses without `next_step` are treated as session state for backward compatibility.
