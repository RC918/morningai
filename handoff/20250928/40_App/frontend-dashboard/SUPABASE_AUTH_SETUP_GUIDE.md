# Supabase Auth SSO Setup Guide

**Last Updated**: 2025-10-22  
**Version**: 2.0 (Supabase Auth)

---

## Overview

This guide explains how to set up SSO (Single Sign-On) authentication using **Supabase Auth** for the Morning AI dashboard. Supabase Auth provides a secure, production-ready authentication solution with built-in OAuth support for Google, Apple, GitHub, and many other providers.

### Why Supabase Auth?

✅ **Security Benefits:**
- httpOnly cookies (prevents XSS attacks)
- Automatic refresh token rotation
- Built-in PKCE support for OAuth flows
- Session management and token refresh

✅ **Developer Benefits:**
- No need to implement custom OAuth flows
- No backend API required for authentication
- Automatic token management
- Built-in security best practices

✅ **Supported Providers:**
- Google
- Apple
- GitHub
- Azure
- Facebook
- Twitter
- And 20+ more providers

---

## Architecture

### Authentication Flow

```
User clicks "Login with Google"
    ↓
Frontend calls supabase.auth.signInWithOAuth()
    ↓
Supabase redirects to Google OAuth
    ↓
User authorizes on Google
    ↓
Google redirects back to /auth/callback
    ↓
Supabase validates OAuth response (PKCE)
    ↓
Supabase creates session with httpOnly cookies
    ↓
Frontend redirects to /dashboard
```

### Components

1. **`/src/lib/supabaseClient.js`** - Supabase client configuration
2. **`/src/components/LoginPage.jsx`** - SSO login buttons
3. **`/src/components/AuthCallback.jsx`** - OAuth callback handler
4. **`/src/lib/api.js`** - API client with Supabase session integration

---

## Setup Instructions

### Step 1: Create Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Click "New Project"
3. Fill in project details:
   - **Name**: morning-ai (or your preferred name)
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
4. Wait for project to be created (~2 minutes)

### Step 2: Get Supabase Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

3. Add to your `.env` file:
```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 3: Configure OAuth Providers

#### Google OAuth 2.0

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Create **OAuth 2.0 Client ID**:
   - Application type: **Web application**
   - Name: `Morning AI`
   - Authorized redirect URIs:
     ```
     https://xxxxx.supabase.co/auth/v1/callback
     ```
     (Replace `xxxxx` with your Supabase project ID)

5. Copy **Client ID** and **Client Secret**

6. In Supabase Dashboard:
   - Go to **Authentication** → **Providers**
   - Enable **Google**
   - Paste **Client ID** and **Client Secret**
   - Save

#### Apple Sign In

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list/serviceId)
2. Create a new **Services ID**:
   - Description: `Morning AI`
   - Identifier: `com.morningai.auth`
   - Enable **Sign In with Apple**

3. Configure **Return URLs**:
   ```
   https://xxxxx.supabase.co/auth/v1/callback
   ```

4. Create a **Key** for Sign In with Apple:
   - Go to **Keys** → **Create a key**
   - Enable **Sign In with Apple**
   - Download the `.p8` key file

5. In Supabase Dashboard:
   - Go to **Authentication** → **Providers**
   - Enable **Apple**
   - Enter **Services ID**, **Team ID**, **Key ID**, and upload **Key file**
   - Save

#### GitHub OAuth

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in details:
   - **Application name**: `Morning AI`
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**:
     ```
     https://xxxxx.supabase.co/auth/v1/callback
     ```

4. Copy **Client ID** and **Client Secret**

5. In Supabase Dashboard:
   - Go to **Authentication** → **Providers**
   - Enable **GitHub**
   - Paste **Client ID** and **Client Secret**
   - Save

### Step 4: Configure Site URL

1. In Supabase Dashboard, go to **Authentication** → **URL Configuration**
2. Set **Site URL**:
   - Development: `http://localhost:5173`
   - Production: `https://your-domain.com`

3. Add **Redirect URLs**:
   ```
   http://localhost:5173/auth/callback
   https://your-domain.com/auth/callback
   ```

---

## Testing

### Local Development

1. Start the development server:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm dev
```

2. Open `http://localhost:5173/login`

3. Click on any SSO button (Google, Apple, or GitHub)

4. You should be redirected to the OAuth provider

5. After authorization, you'll be redirected back to `/auth/callback`

6. If successful, you'll be redirected to `/dashboard`

### Testing Checklist

- [ ] Google login works
- [ ] Apple login works
- [ ] GitHub login works
- [ ] Session persists after page refresh
- [ ] Logout works correctly
- [ ] Token automatically refreshes before expiry
- [ ] Error handling works (cancel authorization, network errors)

---

## Security Features

### 1. httpOnly Cookies

Supabase Auth stores tokens in httpOnly cookies by default (when configured). This prevents XSS attacks from stealing tokens.

**Configuration** (optional, for enhanced security):
```javascript
// In supabaseClient.js
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: customCookieStorage, // Implement custom cookie storage
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});
```

### 2. Refresh Token Rotation

Supabase automatically rotates refresh tokens on each use, preventing token replay attacks.

### 3. PKCE (Proof Key for Code Exchange)

Supabase implements PKCE by default for all OAuth flows, protecting against authorization code interception attacks.

### 4. State Parameter Validation

Supabase validates the OAuth state parameter to prevent CSRF attacks.

---

## API Integration

### Getting the Current Session

```javascript
import { supabase } from '@/lib/supabaseClient';

// Get current session
const { data: { session }, error } = await supabase.auth.getSession();

if (session) {
  const accessToken = session.access_token;
  const user = session.user;
}
```

### Using Session in API Calls

The API client automatically includes the Supabase session token:

```javascript
// In api.js
const { data: { session } } = await supabase.auth.getSession();
if (session?.access_token) {
  config.headers.Authorization = `Bearer ${session.access_token}`;
}
```

### Listening to Auth State Changes

```javascript
import { onAuthStateChange } from '@/lib/supabaseClient';

// Listen to auth state changes
const { data: { subscription } } = onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    console.log('User signed in:', session.user);
  } else if (event === 'SIGNED_OUT') {
    console.log('User signed out');
  } else if (event === 'TOKEN_REFRESHED') {
    console.log('Token refreshed');
  }
});

// Cleanup
subscription.unsubscribe();
```

---

## Troubleshooting

### Issue: "Invalid redirect URL"

**Cause**: The redirect URL is not configured in Supabase or OAuth provider.

**Solution**:
1. Check Supabase **Authentication** → **URL Configuration**
2. Verify redirect URLs match exactly (including protocol and port)
3. Check OAuth provider settings (Google, Apple, GitHub)

### Issue: "Session not found after callback"

**Cause**: OAuth flow was interrupted or state parameter mismatch.

**Solution**:
1. Clear browser cookies and localStorage
2. Try the login flow again
3. Check browser console for errors
4. Verify Supabase project URL is correct

### Issue: "Token expired"

**Cause**: Session expired and auto-refresh failed.

**Solution**:
1. Check network connectivity
2. Verify Supabase project is active
3. Check browser console for refresh errors
4. User should log in again

### Issue: "CORS error"

**Cause**: Supabase project URL or site URL misconfigured.

**Solution**:
1. Verify `VITE_SUPABASE_URL` in `.env`
2. Check Supabase **Authentication** → **URL Configuration**
3. Ensure site URL matches your frontend URL

---

## Production Deployment

### Environment Variables

Set these in your production environment (Vercel, Netlify, etc.):

```bash
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_production_anon_key
```

### OAuth Provider Configuration

Update redirect URLs in each OAuth provider:

**Google:**
- Add: `https://your-domain.com/auth/callback`
- Add: `https://xxxxx.supabase.co/auth/v1/callback`

**Apple:**
- Add: `https://your-domain.com/auth/callback`
- Add: `https://xxxxx.supabase.co/auth/v1/callback`

**GitHub:**
- Add: `https://your-domain.com/auth/callback`
- Add: `https://xxxxx.supabase.co/auth/v1/callback`

### Supabase Configuration

1. Go to **Authentication** → **URL Configuration**
2. Set **Site URL**: `https://your-domain.com`
3. Add **Redirect URLs**:
   - `https://your-domain.com/auth/callback`
   - `https://your-domain.com/*` (wildcard for all routes)

### Security Checklist

- [ ] Environment variables are set in production
- [ ] OAuth redirect URLs are configured for production domain
- [ ] Supabase site URL is set to production domain
- [ ] HTTPS is enabled (required for OAuth)
- [ ] Rate limiting is configured in Supabase
- [ ] Email templates are customized (optional)

---

## Migration from Custom SSO

If you're migrating from the previous custom SSO implementation:

### Removed Files
- ❌ `/src/lib/auth/sso.js` (replaced by Supabase)
- ❌ `/src/lib/auth/tokenManager.js` (replaced by Supabase)
- ❌ `/src/components/SSOCallback.jsx` (replaced by AuthCallback)

### Updated Files
- ✅ `/src/lib/supabaseClient.js` (new)
- ✅ `/src/components/AuthCallback.jsx` (new)
- ✅ `/src/components/LoginPage.jsx` (uses Supabase)
- ✅ `/src/lib/api.js` (uses Supabase session)
- ✅ `/src/App.jsx` (simplified routes)

### Benefits of Migration
- ✅ **Security**: httpOnly cookies, token rotation, PKCE
- ✅ **Simplicity**: No custom OAuth implementation
- ✅ **Reliability**: Battle-tested by thousands of apps
- ✅ **Maintenance**: Supabase handles updates and security patches

---

## Resources

### Documentation
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase Auth with OAuth](https://supabase.com/docs/guides/auth/social-login)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/auth-signinwithoauth)

### OAuth Provider Docs
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Apple Sign In](https://developer.apple.com/sign-in-with-apple/)
- [GitHub OAuth](https://docs.github.com/en/developers/apps/building-oauth-apps)

### Support
- [Supabase Discord](https://discord.supabase.com/)
- [Supabase GitHub](https://github.com/supabase/supabase)

---

## Credits

**Implementation**: Devin AI (devin-ai-integration[bot])  
**Requested By**: Ryan Chen (ryan2939z@gmail.com) / @RC918  
**Devin Run**: https://app.devin.ai/sessions/6d970144dd4c4def9839fe3f8a573ab8  
**Pull Request**: https://github.com/RC918/morningai/pull/589

---

**Last Updated**: 2025-10-22  
**Version**: 2.0 (Supabase Auth)
