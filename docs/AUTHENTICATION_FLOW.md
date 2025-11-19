# Authentication Flow Documentation

## Overview

The MorningAI platform uses a dual authentication system combining JWT-based backend authentication with optional Supabase SSO. This document explains the authentication flow, CSRF protection requirements, and error handling mechanisms.

## Authentication Architecture

### Backend Authentication (Primary)

**Endpoints:** `/api/auth/v2/*`

The backend uses JWT tokens stored in HttpOnly cookies for secure session management:

- **Access Token**: Short-lived token (15 minutes) for API requests
- **Refresh Token**: Long-lived token (7 days) for obtaining new access tokens
- **CSRF Token**: Required for all state-changing operations

### Supabase Authentication (Secondary - SSO Only)

Used exclusively for OAuth/SSO flows (Google, GitHub, etc.). After successful SSO authentication, the frontend still establishes a backend session via `/api/auth/v2/login`.

## CSRF Protection

### Why CSRF Token is Required

The `/api/auth/v2/refresh` endpoint is decorated with `@csrf_protect` to prevent Cross-Site Request Forgery attacks. This requires all refresh requests to include a valid CSRF token.

**Backend Implementation:**
```python
@auth_enhanced_bp.route('/refresh', methods=['POST'])
@csrf_protect  # Requires X-CSRF-Token header
def refresh():
    # Token refresh logic
```

### CSRF Token Flow

1. **Bootstrap CSRF Token**
   - Frontend: `GET /api/auth/v2/csrf`
   - Backend: Sets `csrf_token` cookie (HttpOnly=false for JavaScript access)
   - Cookie name: `csrf_token`
   - Expiry: Same as access token (15 minutes)

2. **Send CSRF Token**
   - Header name: `X-CSRF-Token`
   - Required for: POST, PUT, PATCH, DELETE requests
   - Specifically required for: `/api/auth/v2/refresh`

3. **CSRF Token Retry Mechanism**
   - If CSRF token is missing, frontend attempts to bootstrap it
   - Retries up to 3 times with 150ms delay between attempts
   - If all attempts fail, throws `csrf_unavailable` error

### Frontend Implementation

**Location:** `handoff/20250928/40_App/frontend-dashboard/src/lib/api.ts`

```typescript
async bootstrapCsrf(): Promise<boolean> {
  const maxAttempts = 3
  const delayMs = 150
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await fetch(`${this.baseURL}/api/auth/v2/csrf`, {
      credentials: 'include',
    })
    
    await new Promise(resolve => setTimeout(resolve, delayMs))
    
    if (this.getCsrfToken()) {
      return true
    }
  }
  
  return false
}

private async refreshAccessToken(): Promise<void> {
  let csrfToken = this.getCsrfToken()
  if (!csrfToken) {
    const bootstrapped = await this.bootstrapCsrf()
    if (!bootstrapped) {
      throw new Error('csrf_unavailable')
    }
    csrfToken = this.getCsrfToken()
  }
  
  const response = await fetch(`${this.baseURL}/api/auth/v2/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,
    },
    credentials: 'include',
  })
}
```

## Authentication Error Handling

### Error Flow

1. **401 Unauthorized Detected**
   - API client receives 401 response
   - Attempts token refresh via `/api/auth/v2/refresh`

2. **Refresh Fails**
   - Dispatches `auth-error` CustomEvent
   - Event includes: endpoint, requestId, message

3. **Auth Error Handler** (`App.tsx`)
   - Signs out from Supabase (prevents re-authentication loop)
   - Sets `isAuthenticated=false`
   - Clears user state
   - Shows toast notification: "Session expired. Please sign in again."
   - Sets `redirectToLogin` state with current URL

4. **State-Driven Redirect**
   - `useEffect` watches `isAuthenticated` and `redirectToLogin`
   - When both conditions met, navigates to `/login?returnUrl=...`
   - Uses `navigate()` from react-router (not `window.location.href`)
   - Prevents race conditions and maintains Router state

### Frontend Implementation

**Location:** `handoff/20250928/40_App/frontend-dashboard/src/App.tsx`

```typescript
const [redirectToLogin, setRedirectToLogin] = useState<string | null>(null)

useEffect(() => {
  if (!isAuthenticated && redirectToLogin !== null) {
    const returnUrl = encodeURIComponent(redirectToLogin)
    navigate(`/login?returnUrl=${returnUrl}`, { replace: true })
    setRedirectToLogin(null)
  }
}, [isAuthenticated, redirectToLogin, navigate])

const handleAuthError = async (event: Event) => {
  const customEvent = event as CustomEvent
  const { endpoint, message } = customEvent.detail
  
  // Sign out from Supabase to prevent re-auth loop
  try {
    await supabase.auth.signOut()
  } catch (error) {
    console.error('Supabase signOut error:', error)
  }
  
  // Clear authentication state
  setIsAuthenticated(false)
  setUser({ id: null, name: '', email: '', avatar: '', role: '', tenant_id: '' })
  
  // Set redirect state (triggers useEffect)
  const returnUrl = window.location.pathname + window.location.search
  setRedirectToLogin(returnUrl)
  
  // Show user notification
  addToast({
    title: t('auth.sessionExpired'),
    description: t('auth.pleaseSignInAgain'),
    variant: "destructive"
  })
}

window.addEventListener('auth-error', handleAuthError as EventListener)
```

## Cross-Site Cookie Considerations

### Vercel Preview ↔ Render Staging

When deploying to Vercel preview environments (`*.vercel.app`) that communicate with Render staging backend (`*.onrender.com`), cross-site cookie restrictions apply:

**Required Cookie Attributes:**
- `SameSite=None` - Allow cross-site requests
- `Secure` - HTTPS only (required when SameSite=None)

**Backend Configuration:**
```python
def create_cookie_config(name, value, max_age, httponly=True):
    return {
        'key': name,
        'value': value,
        'max_age': max_age,
        'httponly': httponly,
        'secure': True,  # Required for SameSite=None
        'samesite': 'None'  # Allow cross-site
    }
```

**CORS Configuration:**
```python
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
# Must include: https://*.vercel.app
```

## Token Rotation

The backend implements refresh token rotation for enhanced security:

1. Client sends refresh token to `/api/auth/v2/refresh`
2. Backend validates refresh token
3. Backend generates new access token AND new refresh token
4. Old refresh token is blacklisted
5. New tokens returned to client

**Backend Implementation:** `handoff/20250928/40_App/api-backend/src/routes/auth_enhanced.py:289`

## 2FA/TOTP Flow

When 2FA is enabled for a user:

1. **Login Request** → `/api/auth/v2/login`
   - Backend returns: `{ requires_2fa: true, next_step: 'challenge_2fa' | 'enroll_2fa', tmp_login_token: '...' }`

2. **2FA Challenge** → `/api/auth/v2/2fa/challenge`
   - Client sends: `{ tmp_login_token, totp_code }`
   - Backend validates TOTP code
   - Returns: Full authentication tokens

3. **Frontend Handling** (`LoginPage.tsx:64-86`)
   - Shows TwoFactorVerify dialog for challenge
   - Shows TwoFactorEnroll dialog for enrollment

## Testing Checklist

### Manual Testing

1. **Login Flow**
   - ✅ Login with valid credentials
   - ✅ Verify cookies are set (check Application tab)
   - ✅ Verify CSRF token is present

2. **Token Refresh**
   - ✅ Navigate to dashboard
   - ✅ Verify `/api/tenant/me` succeeds
   - ✅ Wait for token expiry or simulate
   - ✅ Verify refresh request includes `X-CSRF-Token` header
   - ✅ Verify new tokens are received

3. **Error Handling**
   - ✅ Simulate token expiry
   - ✅ Verify auth-error event is dispatched
   - ✅ Verify redirect to `/login` with returnUrl
   - ✅ Verify no "No routes matched" errors
   - ✅ Verify sidebar navigation doesn't crash

### Automated Testing (PR #2)

**Unit Tests:**
- Mock `getCsrfToken()` returning null, verify `bootstrapCsrf()` is called
- Verify `bootstrapCsrf()` retries 3 times before failing
- Verify `refreshAccessToken()` throws `csrf_unavailable` when bootstrap fails
- Verify auth-error is dispatched once (no infinite loops)

**E2E Tests (Playwright):**
- Test complete login → token expiry → refresh → logout flow
- Test sidebar navigation after token refresh
- Test cross-site cookies in staging environment
- Test 2FA challenge flow

## Environment Variables

**Backend:**
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `ENVIRONMENT` - `development` | `staging` | `production`
- `ACCESS_TOKEN_EXPIRY_MINUTES` - Default: 15
- `REFRESH_TOKEN_EXPIRY_DAYS` - Default: 7

**Frontend:**
- `VITE_API_BASE_URL` - Backend API URL
- `VITE_USE_MOCK` - Enable mock API responses (development only)

## Troubleshooting

### Issue: 401 on refresh requests

**Symptoms:** Refresh requests return 401, user is logged out

**Causes:**
1. Missing CSRF token in request headers
2. CSRF token expired
3. Cross-site cookie blocked by browser

**Solutions:**
1. Verify `X-CSRF-Token` header is present in refresh request
2. Check CSRF token cookie exists and is not expired
3. Verify `SameSite=None; Secure` attributes for cross-site deployments
4. Check CORS configuration includes frontend origin

### Issue: Infinite redirect loop

**Symptoms:** User is redirected to `/login` repeatedly

**Causes:**
1. Auth-error handler doesn't clear authentication state
2. Supabase re-authenticates while backend cookies are invalid
3. `/login` route not accessible in current router branch

**Solutions:**
1. Ensure `setIsAuthenticated(false)` is called before redirect
2. Call `supabase.auth.signOut()` in auth-error handler
3. Verify `/login` route exists in unauthenticated router branch

### Issue: CSRF bootstrap fails

**Symptoms:** `csrf_unavailable` error, cannot refresh tokens

**Causes:**
1. Backend `/api/auth/v2/csrf` endpoint not responding
2. Cookie not being set by backend
3. Browser blocking third-party cookies

**Solutions:**
1. Verify backend endpoint is accessible
2. Check backend cookie configuration
3. Test in incognito mode to rule out browser extensions
4. Verify `credentials: 'include'` in fetch requests

## References

- Backend Auth API: `handoff/20250928/40_App/api-backend/src/routes/auth_enhanced.py`
- Frontend API Client: `handoff/20250928/40_App/frontend-dashboard/src/lib/api.ts`
- Frontend App Router: `handoff/20250928/40_App/frontend-dashboard/src/App.tsx`
- 2FA Implementation: `handoff/20250928/40_App/api-backend/src/routes/totp.py`
- OpenAPI Spec: `docs/openapi.auth.yaml`
