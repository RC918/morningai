# Environment Variables Configuration

This document describes all environment variables used by the Owner Console application.

## Core Configuration

### `VITE_API_BASE_URL`

**Required**: Yes (for production/staging)  
**Type**: String (URL)  
**Example**: `https://morningai-backend-v2-stg.onrender.com`

The base URL for the backend API. This is used for all API requests including authentication, CSRF token fetching, and data operations.

**Environment-specific values**:
- **Production**: `https://api.morningai.com` (or production backend URL)
- **Staging/Preview**: `https://morningai-backend-v2-stg.onrender.com`
- **Development**: `http://localhost:5000` (automatically used when MODE=development and not explicitly set)

**Important**: If this variable is not set in non-development environments, CSRF bootstrap will be skipped and authentication may fail.

### `VITE_PREVIEW_PUBLIC_METRICS`

**Required**: No (only for preview environments)  
**Type**: String (`'true'` or `'false'`)  
**Default**: `undefined`  
**Example**: `true`

Enables preview-only bypass for the UX Metrics Dashboard route (`/ux-metrics`). When set to `'true'`, the application will:

1. Skip CSRF token bootstrap for `/ux-metrics` route
2. Skip authentication checks in AuthProvider for `/ux-metrics` route
3. Use a mock user for preview mode (static metrics JSON only)
4. Allow access to `/ux-metrics` without backend authentication

**Security Considerations**:
- This bypass is **tightly scoped** to only the `/ux-metrics` route
- All other routes remain fully protected and require authentication
- The UX Metrics Dashboard only reads static JSON files from the public directory
- No sensitive data or API calls are made from this page
- This should **only be enabled in preview/staging environments**, never in production

**When to use**:
- Vercel Preview deployments where you want to test the UX Metrics Dashboard without backend authentication
- Staging environments where the backend may not be available
- Demo environments where you want to showcase the UX Metrics Dashboard

**When NOT to use**:
- Production environments
- Any environment where real user authentication is required
- Environments with access to sensitive data

### `VITE_FEATURES`

**Required**: No  
**Type**: String (comma-separated feature flags)  
**Example**: `governance,tenants,monitoring,settings`

Feature flags to enable/disable specific features in the Owner Console.

### Feature-specific flags

- `VITE_FEATURE_OWNER_CONSOLE_API`: Enable API integration
- `VITE_FEATURE_OWNER_CONSOLE_GOVERNANCE`: Enable Agent Governance features
- `VITE_FEATURE_OWNER_CONSOLE_TENANTS`: Enable Tenant Management features
- `VITE_FEATURE_OWNER_CONSOLE_MONITORING`: Enable System Monitoring features
- `VITE_FEATURE_OWNER_CONSOLE_SETTINGS`: Enable Platform Settings features
- `VITE_FEATURE_OWNER_CONSOLE_SECURITY`: Enable Security features (2FA, etc.)
- `VITE_FEATURE_OWNER_CONSOLE_PWA`: Enable PWA features

## Vercel Configuration

### Preview Environment Setup

For Vercel Preview deployments, configure the following environment variables in the Vercel dashboard:

1. Go to your Vercel project settings
2. Navigate to "Environment Variables"
3. Add the following variables with scope set to **Preview**:

```
VITE_API_BASE_URL=https://morningai-backend-v2-stg.onrender.com
VITE_PREVIEW_PUBLIC_METRICS=true
```

4. Redeploy your preview branch to apply the changes

### Production Environment Setup

For production deployments:

```
VITE_API_BASE_URL=https://api.morningai.com
```

**Do NOT set** `VITE_PREVIEW_PUBLIC_METRICS` in production.

## Testing Without Backend

The UX Metrics Dashboard can be tested without a backend connection when `VITE_PREVIEW_PUBLIC_METRICS=true` is set. This is useful for:

1. **Frontend-only testing**: Test the dashboard UI, layout, and interactions without backend dependencies
2. **Preview deployments**: Share preview links with stakeholders without requiring backend access
3. **Demo environments**: Showcase the UX Metrics Dashboard with static data

### How it works

When `VITE_PREVIEW_PUBLIC_METRICS=true`:

1. The application checks if the current route is `/ux-metrics`
2. If yes, it skips CSRF token bootstrap and authentication checks
3. A mock user is created with the following properties:
   ```typescript
   {
     id: 'preview-user',
     email: 'preview@morningai.com',
     role: 'owner',
     tenantId: 'preview-tenant',
     name: 'Preview User',
   }
   ```
4. The UX Metrics Dashboard loads static JSON data from `/ux-metrics-data.json`
5. All other routes continue to require full authentication

### Testing procedure

1. Set `VITE_PREVIEW_PUBLIC_METRICS=true` in your environment
2. Deploy or run the application locally
3. Navigate directly to `/ux-metrics`
4. Verify the dashboard loads without authentication errors
5. Test language switching (English ↔ Traditional Chinese)
6. Test responsive layout on different screen sizes
7. Verify all metrics are displayed correctly

### Limitations

- Only the `/ux-metrics` route is accessible without authentication
- Attempting to navigate to other routes will redirect to the login page
- No real-time data or API calls are made
- The mock user has limited permissions and cannot perform actions outside `/ux-metrics`

## Troubleshooting

### "Failed to bootstrap CSRF token" error

**Cause**: `VITE_API_BASE_URL` is not set or is incorrect.

**Solution**: 
1. Check that `VITE_API_BASE_URL` is set in your environment
2. Verify the URL is correct and accessible
3. For preview environments, ensure the staging backend is running

### "CSRF bootstrap skipped: VITE_API_BASE_URL not configured" warning

**Cause**: `VITE_API_BASE_URL` is not set.

**Solution**: This is expected in development mode (localhost fallback is used). For other environments, set `VITE_API_BASE_URL`.

### Cannot access /ux-metrics in preview

**Cause**: `VITE_PREVIEW_PUBLIC_METRICS` is not set to `'true'`.

**Solution**: 
1. Set `VITE_PREVIEW_PUBLIC_METRICS=true` in Vercel environment variables
2. Ensure the scope is set to "Preview"
3. Redeploy the preview branch

### Authentication still required for /ux-metrics

**Cause**: Environment variable not properly loaded or preview bypass logic not triggered.

**Solution**:
1. Check browser console for "Skipping CSRF bootstrap for /ux-metrics in preview mode" message
2. Verify `import.meta.env.VITE_PREVIEW_PUBLIC_METRICS === 'true'`
3. Ensure you're navigating directly to `/ux-metrics` (not redirected from another route)
4. Clear browser cache and hard reload

## Security Best Practices

1. **Never enable preview bypass in production**: Always keep `VITE_PREVIEW_PUBLIC_METRICS` undefined or `'false'` in production
2. **Use environment-specific API URLs**: Don't use production API URLs in preview/staging environments
3. **Rotate secrets regularly**: If you add authentication secrets, rotate them regularly
4. **Audit environment variables**: Regularly review which environment variables are set and where
5. **Limit preview access**: Use Vercel's password protection or authentication for preview deployments if needed

## Related Documentation

- [UX Pipeline Documentation](../../../../docs/UX_PIPELINE.md)
- [Design Tokens Unification](../../../../docs/DESIGN_TOKENS_UNIFICATION.md)
- [Authentication Architecture](../../../../docs/CURRENT_AUTH_ARCHITECTURE.md)
