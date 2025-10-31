# PWA Environment Variables Documentation

**Issue**: #966 - Document PWA environment variables  
**Date**: 2025-10-30  
**Application**: Owner Console  
**Feature Flag**: `OWNER_CONSOLE_PWA` (Issue #774)

## Executive Summary

This document provides comprehensive documentation for all Progressive Web App (PWA) related environment variables in the MorningAI platform. The PWA implementation is currently available for the Owner Console application and provides offline capability, push notifications, and native app-like experience.

## PWA Overview

The Owner Console implements PWA functionality using:
- **Build Tool**: Vite with `vite-plugin-pwa`
- **Service Worker**: Workbox-powered service worker with runtime caching
- **Manifest**: Auto-generated web app manifest
- **Push Notifications**: Web Push API with VAPID authentication
- **Offline Support**: Cache-first strategy for static assets, network-first for API calls

**Current Status**: Development only (not enabled in staging/production)

---

## Environment Variables

### 1. Feature Flag Control

#### `OWNER_CONSOLE_PWA`
**Type**: Boolean (Feature Flag)  
**Default**: `false`  
**Required**: No  
**Security**: Public  
**Environments**:
- Development: `true`
- Staging: `false`
- Production: `false`

**Description**: Master feature flag that enables/disables all PWA functionality in the Owner Console. When disabled, PWA features (service worker, install prompt, push notifications) are not initialized.

**Configuration Location**: `config/feature_flags.yaml:127-139`

**Usage**:
```typescript
// src/lib/pwa.ts
import { isFeatureEnabled } from './feature-flags';

export function initPWA(): void {
  if (!isFeatureEnabled('OWNER_CONSOLE_PWA')) {
    console.log('PWA features disabled by feature flag');
    return;
  }
  // ... initialize PWA
}
```

**Related Code**:
- Feature flag check: `handoff/20250928/40_App/owner-console/src/lib/pwa.ts:46`
- Feature flag definition: `config/feature_flags.yaml:127`

---

### 2. Push Notifications (VAPID Keys)

#### `VITE_VAPID_PUBLIC_KEY`
**Type**: String (Base64-encoded public key)  
**Default**: None  
**Required**: Yes (if push notifications are enabled)  
**Security**: Public (safe to expose in frontend)  
**Environments**: All

**Description**: VAPID (Voluntary Application Server Identification) public key for Web Push API authentication. This key is used by the browser to verify push notification subscriptions. The public key can be safely exposed in the frontend code.

**Format**: Base64-encoded string (URL-safe)  
**Example**: `BEl62iUYgUivxIkv69yViEuiBIa-Ib27SzV8-jnLSeZP...`

**Generation**:
```bash
# Generate VAPID key pair using web-push library
npx web-push generate-vapid-keys

# Output:
# Public Key: BEl62iUYgUivxIkv69yViEuiBIa-Ib27SzV8-jnLSeZP...
# Private Key: (keep this secret on backend)
```

**Usage**:
```typescript
// Frontend: Subscribe to push notifications
import { subscribeToPushNotifications } from './lib/pwa';

const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY;
const subscription = await subscribeToPushNotifications(vapidPublicKey);
```

**Related Code**:
- Usage: `handoff/20250928/40_App/owner-console/src/lib/pwa.ts:164-193`
- Base64 conversion: `handoff/20250928/40_App/owner-console/src/lib/pwa.ts:300-312`

**Security Notes**:
- Public key is safe to expose in frontend code
- Private key must be kept secret on backend (not documented here)
- Keys should be rotated periodically (recommended: every 6-12 months)

---

#### `VAPID_PRIVATE_KEY` (Backend Only)
**Type**: String (Base64-encoded private key)  
**Default**: None  
**Required**: Yes (if push notifications are enabled)  
**Security**: Critical (never expose in frontend)  
**Environments**: All (backend only)

**Description**: VAPID private key for signing push notification requests from the backend. This key must be kept secret and should only be used on the backend server to send push notifications.

**Format**: Base64-encoded string (URL-safe)  
**Example**: `(secret - do not expose)`

**Storage**: 
- Store in backend environment variables only
- Never commit to git
- Use secure secret management (e.g., Render secrets, AWS Secrets Manager)

**Usage** (Backend):
```python
# Backend: Send push notification
import webpush

vapid_private_key = os.getenv('VAPID_PRIVATE_KEY')
vapid_claims = {
    "sub": "mailto:admin@morningai.com"
}

webpush.send_web_push(
    subscription_info,
    message_body,
    vapid_private_key=vapid_private_key,
    vapid_claims=vapid_claims
)
```

**Security Notes**:
- Never expose in frontend code or logs
- Rotate keys if compromised
- Use different keys for development/staging/production

---

### 3. PWA Manifest Configuration

#### `VITE_PWA_NAME`
**Type**: String  
**Default**: `"Morning AI - Intelligent Decision Support"`  
**Required**: No (has default)  
**Security**: Public  
**Environments**: All

**Description**: Full application name displayed when installing the PWA. This appears in the browser's install prompt and on the device's home screen.

**Current Value**: Hardcoded in `vite.config.js:16`

**Usage**:
```javascript
// vite.config.js
VitePWA({
  manifest: {
    name: process.env.VITE_PWA_NAME || 'Morning AI - Intelligent Decision Support',
    // ...
  }
})
```

**Recommendation**: Make this configurable via environment variable for different deployments (e.g., "Morning AI - Staging" for staging environment).

---

#### `VITE_PWA_SHORT_NAME`
**Type**: String  
**Default**: `"Morning AI"`  
**Required**: No (has default)  
**Security**: Public  
**Environments**: All

**Description**: Short application name displayed on device home screen when space is limited (typically 12 characters or less).

**Current Value**: Hardcoded in `vite.config.js:17`

**Usage**: Same as `VITE_PWA_NAME`

---

#### `VITE_PWA_DESCRIPTION`
**Type**: String  
**Default**: `"AI-powered decision support platform with real-time analytics and insights"`  
**Required**: No (has default)  
**Security**: Public  
**Environments**: All

**Description**: Application description shown in app stores and install prompts.

**Current Value**: Hardcoded in `vite.config.js:18`

---

#### `VITE_PWA_THEME_COLOR`
**Type**: String (Hex color)  
**Default**: `"#000000"` (black)  
**Required**: No (has default)  
**Security**: Public  
**Environments**: All

**Description**: Theme color for the browser UI when the PWA is running. This affects the browser's address bar and system UI elements.

**Current Value**: Hardcoded in `vite.config.js:19`

**Recommendation**: Use brand color (e.g., `#7C3AED` for purple theme in Owner Console).

---

#### `VITE_PWA_BACKGROUND_COLOR`
**Type**: String (Hex color)  
**Default**: `"#ffffff"` (white)  
**Required**: No (has default)  
**Security**: Public  
**Environments**: All

**Description**: Background color displayed while the PWA is loading. Should match the app's main background color for smooth loading experience.

**Current Value**: Hardcoded in `vite.config.js:20`

---

### 4. Service Worker Configuration

#### `VITE_SW_ENABLED`
**Type**: Boolean  
**Default**: `true` (in development), `true` (in production)  
**Required**: No  
**Security**: Public  
**Environments**: All

**Description**: Enable/disable service worker registration. When disabled, the PWA will not have offline capability or caching.

**Current Configuration**: 
```javascript
// vite.config.js:82-84
devOptions: {
  enabled: true  // Service worker enabled in development
}
```

**Usage**:
```typescript
// Conditional service worker registration
if (import.meta.env.VITE_SW_ENABLED !== 'false') {
  registerServiceWorker();
}
```

**Note**: Currently hardcoded to `true`. Consider making this configurable for testing scenarios where service worker should be disabled.

---

#### `VITE_SW_CACHE_NAME`
**Type**: String  
**Default**: Auto-generated by Workbox  
**Required**: No  
**Security**: Public  
**Environments**: All

**Description**: Custom cache name prefix for service worker caches. Useful for versioning and cache invalidation.

**Current Behavior**: Workbox auto-generates cache names like:
- `google-fonts-cache`
- `gstatic-fonts-cache`
- `api-cache`

**Recommendation**: Add version-based cache naming:
```javascript
VITE_SW_CACHE_NAME=morningai-v8-cache
```

---

### 5. API and Backend Configuration

#### `VITE_API_BASE_URL`
**Type**: String (URL)  
**Default**: `http://localhost:5001`  
**Required**: Yes  
**Security**: Public  
**Environments**: All

**Description**: Backend API base URL for all API requests. The service worker uses this to determine which requests should be cached with network-first strategy.

**Configuration**: Already documented in `.env.example:171`

**PWA Impact**: The service worker caches API requests matching `/api/*` pattern with network-first strategy (5-minute cache, 10-second timeout).

**Service Worker Configuration**:
```javascript
// vite.config.js:68-79
{
  urlPattern: /\/api\/.*/i,
  handler: 'NetworkFirst',
  options: {
    cacheName: 'api-cache',
    expiration: {
      maxEntries: 50,
      maxAgeSeconds: 60 * 5  // 5 minutes
    },
    networkTimeoutSeconds: 10
  }
}
```

---

### 6. Notification Configuration

#### `VITE_NOTIFICATION_ICON`
**Type**: String (URL path)  
**Default**: `"/icon-192.png"`  
**Required**: No (has default)  
**Security**: Public  
**Environments**: All

**Description**: Icon displayed in push notifications. Should be a 192x192 PNG image.

**Current Value**: Hardcoded in `pwa.ts:146, 152`

**Usage**:
```typescript
// src/lib/pwa.ts:145-149
await registration.showNotification(title, {
  icon: '/icon-192.png',
  badge: '/icon-192.png',
  ...options,
});
```

**Recommendation**: Make configurable via environment variable:
```env
VITE_NOTIFICATION_ICON=/icon-192.png
VITE_NOTIFICATION_BADGE=/icon-192.png
```

---

### 7. PWA Install Prompt Configuration

#### `VITE_PWA_INSTALL_PROMPT_DELAY`
**Type**: Number (milliseconds)  
**Default**: `0` (immediate)  
**Required**: No  
**Security**: Public  
**Environments**: All

**Description**: Delay before showing the PWA install prompt after page load. Helps avoid interrupting the user immediately.

**Current Behavior**: Install prompt shows immediately when PWA is installable.

**Recommendation**: Add configurable delay:
```env
VITE_PWA_INSTALL_PROMPT_DELAY=5000  # 5 seconds
```

**Implementation**:
```typescript
// src/components/PWAInstallPrompt.tsx
useEffect(() => {
  const delay = parseInt(import.meta.env.VITE_PWA_INSTALL_PROMPT_DELAY || '0');
  const timer = setTimeout(() => {
    if (isPWAInstallable()) {
      setShowPrompt(true);
    }
  }, delay);
  return () => clearTimeout(timer);
}, []);
```

---

#### `VITE_PWA_INSTALL_DISMISS_DURATION`
**Type**: Number (days)  
**Default**: `7` (7 days)  
**Required**: No  
**Security**: Public  
**Environments**: All

**Description**: Number of days to wait before showing the install prompt again after user dismisses it.

**Current Value**: Hardcoded in `PWAInstallPrompt.tsx:71`

**Usage**:
```typescript
// src/components/PWAInstallPrompt.tsx:68-76
const dismissed = localStorage.getItem('pwa-install-dismissed');
if (dismissed) {
  const dismissedTime = parseInt(dismissed, 10);
  const sevenDays = 7 * 24 * 60 * 60 * 1000;
  
  if (Date.now() - dismissedTime < sevenDays) {
    setShowPrompt(false);
  }
}
```

**Recommendation**: Make configurable:
```env
VITE_PWA_INSTALL_DISMISS_DURATION=7  # days
```

---

## Environment Variable Summary Table

| Variable | Type | Default | Required | Security | Status |
|----------|------|---------|----------|----------|--------|
| `OWNER_CONSOLE_PWA` | Boolean | `false` | No | Public | ✅ Implemented |
| `VITE_VAPID_PUBLIC_KEY` | String | None | Yes* | Public | ⚠️ Not implemented |
| `VAPID_PRIVATE_KEY` | String | None | Yes* | Critical | ⚠️ Backend only |
| `VITE_PWA_NAME` | String | "Morning AI..." | No | Public | ⚠️ Hardcoded |
| `VITE_PWA_SHORT_NAME` | String | "Morning AI" | No | Public | ⚠️ Hardcoded |
| `VITE_PWA_DESCRIPTION` | String | "AI-powered..." | No | Public | ⚠️ Hardcoded |
| `VITE_PWA_THEME_COLOR` | String | "#000000" | No | Public | ⚠️ Hardcoded |
| `VITE_PWA_BACKGROUND_COLOR` | String | "#ffffff" | No | Public | ⚠️ Hardcoded |
| `VITE_SW_ENABLED` | Boolean | `true` | No | Public | ⚠️ Hardcoded |
| `VITE_SW_CACHE_NAME` | String | Auto | No | Public | ⚠️ Not implemented |
| `VITE_API_BASE_URL` | String | localhost:5001 | Yes | Public | ✅ Implemented |
| `VITE_NOTIFICATION_ICON` | String | "/icon-192.png" | No | Public | ⚠️ Hardcoded |
| `VITE_PWA_INSTALL_PROMPT_DELAY` | Number | `0` | No | Public | ⚠️ Not implemented |
| `VITE_PWA_INSTALL_DISMISS_DURATION` | Number | `7` | No | Public | ⚠️ Hardcoded |

*Required only if push notifications are enabled

**Legend**:
- ✅ Implemented: Variable is configurable via environment
- ⚠️ Hardcoded: Value is hardcoded in source code
- ⚠️ Not implemented: Variable is not yet implemented

---

## Configuration Files

### 1. Feature Flag Configuration
**File**: `config/feature_flags.yaml`  
**Lines**: 127-139

```yaml
owner_console_pwa_enabled:
  category: ui_features
  type: boolean
  default: false
  description: 'Enable PWA features for Owner Console'
  environments:
    development: true
    staging: false
    production: false
  rollout_percentage: 0
  dependencies: ['owner_console_enabled']
  owner: 'Owner Console Squad'
```

### 2. Vite PWA Plugin Configuration
**File**: `handoff/20250928/40_App/owner-console/vite.config.js`  
**Lines**: 12-85

```javascript
VitePWA({
  registerType: 'autoUpdate',
  includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'],
  manifest: {
    name: 'Morning AI - Intelligent Decision Support',
    short_name: 'Morning AI',
    description: 'AI-powered decision support platform with real-time analytics and insights',
    theme_color: '#000000',
    background_color: '#ffffff',
    display: 'standalone',
    icons: [...]
  },
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
    runtimeCaching: [...]
  },
  devOptions: {
    enabled: true
  }
})
```

### 3. PWA Library
**File**: `handoff/20250928/40_App/owner-console/src/lib/pwa.ts`  
**Lines**: 1-329

Contains all PWA functionality:
- Service worker initialization
- Install prompt handling
- Push notification subscription
- Offline detection
- Cache management

### 4. PWA Install Prompt Component
**File**: `handoff/20250928/40_App/owner-console/src/components/PWAInstallPrompt.tsx`  
**Lines**: 1-126

UI component for PWA installation prompt.

---

## Setup Instructions

### Development Environment

1. **Enable PWA Feature Flag**:
```yaml
# config/feature_flags.yaml
owner_console_pwa_enabled:
  environments:
    development: true
```

2. **Configure Environment Variables** (Optional):
```env
# .env.local (Owner Console)
VITE_VAPID_PUBLIC_KEY=BEl62iUYgUivxIkv69yViEuiBIa-Ib27SzV8-jnLSeZP...
VITE_PWA_NAME=Morning AI - Development
VITE_PWA_THEME_COLOR=#7C3AED
```

3. **Start Development Server**:
```bash
cd handoff/20250928/40_App/owner-console
npm run dev
```

4. **Test PWA Features**:
- Open Chrome DevTools → Application → Service Workers
- Check "Update on reload" for development
- Test offline mode by toggling "Offline" in Network tab

### Staging Environment

1. **Update Feature Flag**:
```yaml
owner_console_pwa_enabled:
  environments:
    staging: true
```

2. **Configure Staging Variables**:
```env
VITE_VAPID_PUBLIC_KEY=<staging-public-key>
VITE_PWA_NAME=Morning AI - Staging
VITE_API_BASE_URL=https://staging-api.morningai.com
```

3. **Deploy**:
```bash
npm run build
# Deploy to staging environment
```

### Production Environment

1. **Generate VAPID Keys**:
```bash
npx web-push generate-vapid-keys
```

2. **Configure Production Variables**:
```env
# Frontend (.env.production)
VITE_VAPID_PUBLIC_KEY=<production-public-key>
VITE_PWA_NAME=Morning AI
VITE_PWA_THEME_COLOR=#7C3AED
VITE_API_BASE_URL=https://api.morningai.com

# Backend (Render secrets)
VAPID_PRIVATE_KEY=<production-private-key>
VAPID_SUBJECT=mailto:admin@morningai.com
```

3. **Update Feature Flag**:
```yaml
owner_console_pwa_enabled:
  environments:
    production: true
  rollout_percentage: 100
```

4. **Deploy with Monitoring**:
```bash
npm run build
# Deploy to production
# Monitor error rates and user adoption
```

---

## Testing

### Manual Testing Checklist

- [ ] **Install Prompt**
  - [ ] Prompt appears after page load
  - [ ] Dismiss button works
  - [ ] Install button triggers browser install flow
  - [ ] Prompt doesn't reappear for 7 days after dismiss

- [ ] **Offline Functionality**
  - [ ] App loads when offline
  - [ ] Cached pages are accessible
  - [ ] Offline indicator appears
  - [ ] API requests queue when offline

- [ ] **Push Notifications**
  - [ ] Permission request appears
  - [ ] Notifications display correctly
  - [ ] Notification icon and badge are correct
  - [ ] Click on notification opens app

- [ ] **Service Worker**
  - [ ] Service worker registers successfully
  - [ ] Updates apply automatically
  - [ ] Cache invalidation works
  - [ ] No console errors

### Automated Testing

```bash
# Run Lighthouse PWA audit
npm run lighthouse -- --only-categories=pwa

# Expected scores:
# - PWA: 100
# - Performance: 90+
# - Accessibility: 95+
```

---

## Troubleshooting

### Issue: Service Worker Not Registering

**Symptoms**: PWA features not working, no service worker in DevTools

**Solutions**:
1. Check feature flag: `OWNER_CONSOLE_PWA` must be `true`
2. Verify HTTPS: Service workers require HTTPS (except localhost)
3. Clear browser cache and hard reload
4. Check console for registration errors

### Issue: Install Prompt Not Appearing

**Symptoms**: PWA is installable but prompt doesn't show

**Solutions**:
1. Check if already installed: PWA won't prompt if already installed
2. Check dismiss timestamp: Prompt hidden for 7 days after dismiss
3. Verify manifest: Check DevTools → Application → Manifest
4. Check browser support: Some browsers don't support install prompts

### Issue: Push Notifications Not Working

**Symptoms**: Notifications don't appear or subscription fails

**Solutions**:
1. Verify VAPID keys: Public key must match private key
2. Check permissions: User must grant notification permission
3. Verify service worker: Must be registered and active
4. Check backend: Backend must send notifications with correct VAPID signature

### Issue: Offline Mode Not Working

**Symptoms**: App doesn't work offline or shows errors

**Solutions**:
1. Check service worker: Must be registered and caching assets
2. Verify cache strategy: Check Workbox configuration
3. Clear cache: DevTools → Application → Clear storage
4. Check network requests: Verify requests are being cached

---

## Security Considerations

### VAPID Keys
- **Public Key**: Safe to expose in frontend code
- **Private Key**: Must be kept secret on backend
- **Rotation**: Rotate keys every 6-12 months
- **Storage**: Use secure secret management (Render secrets, AWS Secrets Manager)

### Service Worker
- **Scope**: Service worker has access to all requests within its scope
- **HTTPS**: Always use HTTPS in production (service workers require it)
- **Cache Poisoning**: Validate cached responses before serving
- **Updates**: Implement automatic service worker updates

### Push Notifications
- **User Consent**: Always request permission before subscribing
- **Unsubscribe**: Provide easy way to unsubscribe
- **Content**: Don't send sensitive data in notifications
- **Rate Limiting**: Implement rate limiting to prevent spam

---

## Performance Considerations

### Cache Strategy
- **Static Assets**: Cache-first (fonts, images, CSS, JS)
- **API Requests**: Network-first with 5-minute cache fallback
- **HTML Pages**: Network-first with cache fallback

### Cache Limits
- **Google Fonts**: 10 entries, 1 year expiration
- **API Cache**: 50 entries, 5 minutes expiration
- **Total Cache Size**: Monitor and limit to ~50MB

### Service Worker Updates
- **Auto-update**: Service worker checks for updates every 24 hours
- **Manual Update**: Provide "Check for updates" button
- **Skip Waiting**: New service worker activates immediately

---

## Future Enhancements

### Phase 1: Configuration Improvements
- [ ] Make all hardcoded values configurable via environment variables
- [ ] Add `VITE_VAPID_PUBLIC_KEY` to `.env.example`
- [ ] Update `vite.config.js` to use environment variables
- [ ] Add validation for required PWA environment variables

### Phase 2: Advanced Features
- [ ] Background sync for offline actions
- [ ] Periodic background sync for data updates
- [ ] Share target API for sharing content to app
- [ ] Shortcuts API for quick actions
- [ ] Badge API for notification counts

### Phase 3: Analytics and Monitoring
- [ ] Track PWA install rate
- [ ] Monitor offline usage patterns
- [ ] Track push notification engagement
- [ ] Service worker error monitoring with Sentry

### Phase 4: Multi-App Support
- [ ] Extend PWA to Tenant Dashboard
- [ ] Shared service worker for both apps
- [ ] Unified push notification system
- [ ] Cross-app offline data sync

---

## References

### Documentation
- [MDN: Progressive Web Apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Web.dev: PWA](https://web.dev/progressive-web-apps/)
- [Vite PWA Plugin](https://vite-pwa-org.netlify.app/)
- [Workbox Documentation](https://developer.chrome.com/docs/workbox/)
- [Web Push Protocol](https://datatracker.ietf.org/doc/html/rfc8030)
- [VAPID Specification](https://datatracker.ietf.org/doc/html/rfc8292)

### Related Issues
- Issue #774: PWA Implementation (Owner Console)
- Issue #767: Owner Console Development
- Issue #966: Document PWA Environment Variables (This document)

### Related Files
- `config/feature_flags.yaml` - Feature flag configuration
- `handoff/20250928/40_App/owner-console/vite.config.js` - Vite PWA configuration
- `handoff/20250928/40_App/owner-console/src/lib/pwa.ts` - PWA library
- `handoff/20250928/40_App/owner-console/src/components/PWAInstallPrompt.tsx` - Install prompt
- `handoff/20250928/40_App/owner-console/src/components/OfflineIndicator.tsx` - Offline indicator

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-30 | 1.0.0 | Initial documentation | CTO (Issue #966) |

---

## Contact

For questions or issues related to PWA configuration:
- **Owner**: Owner Console Squad
- **Issue**: #966
- **Email**: ryan2939z@gmail.com
- **GitHub**: @RC918
