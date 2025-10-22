# SSO Authentication Setup Guide

This guide explains how to configure Single Sign-On (SSO) authentication for Morning AI using Google, Apple, and GitHub OAuth providers.

## Overview

The SSO implementation includes:
- **Google OAuth 2.0** with PKCE (Proof Key for Code Exchange)
- **Apple Sign In** with OpenID Connect
- **GitHub OAuth** for developer-friendly authentication
- **JWT Token Management** with automatic refresh
- **Secure State Validation** to prevent CSRF attacks

## Architecture

### Components

1. **SSOAuthService** (`src/lib/auth/sso.js`)
   - Handles OAuth flow initialization
   - Manages state and code verifier generation
   - Processes OAuth callbacks

2. **TokenManager** (`src/lib/auth/tokenManager.js`)
   - Manages JWT access and refresh tokens
   - Automatic token refresh before expiration
   - Secure token storage in localStorage

3. **SSOCallback** (`src/components/SSOCallback.jsx`)
   - Handles OAuth provider callbacks
   - Displays authentication status
   - Redirects to dashboard on success

4. **LoginPage** (`src/components/LoginPage.jsx`)
   - Updated with SSO buttons
   - Supports traditional username/password login
   - Seamless SSO integration

## Setup Instructions

### 1. Google OAuth 2.0

#### Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure the OAuth consent screen:
   - User Type: External (for public apps) or Internal (for workspace apps)
   - App name: Morning AI
   - User support email: your-email@example.com
   - Developer contact: your-email@example.com

6. Create OAuth 2.0 Client ID:
   - Application type: **Web application**
   - Name: Morning AI Web Client
   - Authorized JavaScript origins:
     - `http://localhost:5173` (development)
     - `https://your-production-domain.com` (production)
   - Authorized redirect URIs:
     - `http://localhost:5173/auth/callback/google` (development)
     - `https://your-production-domain.com/auth/callback/google` (production)

7. Copy the **Client ID** and add to `.env`:
   ```
   VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
   ```

#### Scopes Used
- `openid` - OpenID Connect authentication
- `profile` - User profile information
- `email` - User email address

### 2. Apple Sign In

#### Create Service ID

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list/serviceId)
2. Sign in with your Apple Developer account
3. Click **+** to create a new identifier
4. Select **Services IDs** and click **Continue**
5. Configure the Service ID:
   - Description: Morning AI
   - Identifier: com.morningai.web (or your bundle ID)
   - Enable **Sign In with Apple**

6. Configure Web Authentication:
   - Primary App ID: Select your app's App ID
   - Website URLs:
     - Domains: `localhost:5173`, `your-production-domain.com`
     - Return URLs:
       - `http://localhost:5173/auth/callback/apple`
       - `https://your-production-domain.com/auth/callback/apple`

7. Copy the **Service ID** and add to `.env`:
   ```
   VITE_APPLE_CLIENT_ID=com.morningai.web
   ```

#### Additional Requirements
- Apple Developer Program membership ($99/year)
- Verified domain ownership for production
- Private key for server-side token validation

#### Scopes Used
- `name` - User's full name
- `email` - User's email address

### 3. GitHub OAuth

#### Create OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Configure the OAuth App:
   - Application name: Morning AI
   - Homepage URL: `http://localhost:5173` (development) or `https://your-production-domain.com` (production)
   - Application description: Intelligent Decision System Management Platform
   - Authorization callback URL:
     - `http://localhost:5173/auth/callback/github` (development)
     - `https://your-production-domain.com/auth/callback/github` (production)

4. Click **Register application**
5. Generate a new client secret
6. Copy the **Client ID** and add to `.env`:
   ```
   VITE_GITHUB_CLIENT_ID=your_github_client_id_here
   ```

#### Scopes Used
- `read:user` - Read user profile information
- `user:email` - Access user email addresses

## Backend API Requirements

The frontend SSO implementation requires corresponding backend endpoints:

### Required Endpoints

#### 1. SSO Callback Handler
```
POST /api/auth/sso/callback
```

**Request Body:**
```json
{
  "provider": "google|apple|github",
  "code": "authorization_code",
  "code_verifier": "pkce_code_verifier",
  "redirect_uri": "callback_url"
}
```

**Response:**
```json
{
  "user": {
    "id": "user_id",
    "name": "User Name",
    "email": "user@example.com",
    "avatar": "avatar_url"
  },
  "token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "expires_in": 3600
}
```

#### 2. Token Refresh
```
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_access_token",
  "refresh_token": "new_jwt_refresh_token",
  "expires_in": 3600
}
```

#### 3. Token Verification
```
GET /api/auth/verify
```

**Headers:**
```
Authorization: Bearer {jwt_access_token}
```

**Response:**
```json
{
  "id": "user_id",
  "name": "User Name",
  "email": "user@example.com",
  "avatar": "avatar_url"
}
```

## Security Considerations

### PKCE (Proof Key for Code Exchange)

The implementation uses PKCE for Google OAuth to prevent authorization code interception attacks:

1. **Code Verifier**: Random 32-byte string
2. **Code Challenge**: SHA-256 hash of code verifier, base64url encoded
3. **Code Challenge Method**: S256

### State Parameter

All OAuth flows use a cryptographically secure random state parameter to prevent CSRF attacks:

1. Generated using `crypto.getRandomValues()`
2. Stored in `sessionStorage` during authorization
3. Validated on callback
4. Cleared after successful authentication

### Token Storage

- **Access Token**: Stored in `localStorage` with expiration time
- **Refresh Token**: Stored in `localStorage` (consider using `httpOnly` cookies in production)
- **Automatic Refresh**: Tokens are refreshed 5 minutes before expiration

### Best Practices

1. **HTTPS Only**: Always use HTTPS in production
2. **Secure Cookies**: Consider using `httpOnly` cookies for refresh tokens
3. **Token Rotation**: Implement refresh token rotation
4. **Rate Limiting**: Implement rate limiting on auth endpoints
5. **Audit Logging**: Log all authentication attempts
6. **Session Management**: Implement proper session timeout

## Testing

### Development Testing

1. Start the frontend development server:
   ```bash
   cd handoff/20250928/40_App/frontend-dashboard
   npm run dev
   ```

2. Navigate to `http://localhost:5173/login`

3. Click on any SSO button (Google, Apple, or GitHub)

4. Complete the OAuth flow on the provider's page

5. You should be redirected back to the callback URL and then to the dashboard

### Mock Testing

For testing without real OAuth credentials, the login page includes a development test account:
- Username: `admin`
- Password: `admin123`

## Troubleshooting

### Common Issues

#### 1. "Invalid state parameter" Error
- **Cause**: State mismatch or expired session
- **Solution**: Clear browser storage and try again

#### 2. "Redirect URI mismatch" Error
- **Cause**: Callback URL not registered with OAuth provider
- **Solution**: Verify redirect URIs in provider console match exactly

#### 3. "Token refresh failed" Error
- **Cause**: Refresh token expired or invalid
- **Solution**: User needs to log in again

#### 4. CORS Errors
- **Cause**: Backend not configured for CORS
- **Solution**: Add frontend origin to backend CORS whitelist

### Debug Mode

Enable debug logging by adding to `.env`:
```
VITE_DEBUG_AUTH=true
```

This will log:
- OAuth flow initialization
- State and code verifier generation
- Callback processing
- Token refresh attempts

## Production Deployment

### Checklist

- [ ] Update OAuth redirect URIs with production domain
- [ ] Enable HTTPS
- [ ] Configure secure cookie settings
- [ ] Implement rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure Sentry for error tracking
- [ ] Test all OAuth flows in production
- [ ] Document recovery procedures

### Environment Variables

Production `.env` example:
```
VITE_API_BASE_URL=https://api.your-domain.com
VITE_USE_MOCK=false

VITE_GOOGLE_CLIENT_ID=your_production_google_client_id
VITE_APPLE_CLIENT_ID=com.morningai.web
VITE_GITHUB_CLIENT_ID=your_production_github_client_id

VITE_SENTRY_DSN=your_sentry_dsn
```

## Support

For issues or questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review provider documentation:
   - [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
   - [Apple Sign In](https://developer.apple.com/sign-in-with-apple/)
   - [GitHub OAuth](https://docs.github.com/en/developers/apps/building-oauth-apps)
3. Contact the development team

## License

© 2024 Morning AI. All rights reserved.
