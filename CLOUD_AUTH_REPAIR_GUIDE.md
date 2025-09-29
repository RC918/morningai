# Cloud Service Authentication Repair Guide

This guide provides step-by-step instructions to fix authentication issues for all cloud services.

## Quick Diagnosis

Run the authentication repair tool:
```bash
python fix_cloud_auth.py
```

## Service-Specific Repair Instructions

### 🔧 Supabase Authentication Repair

**Issue**: HTTP 401 "Invalid API key"

**Steps to Fix**:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Settings** > **API**
4. Copy the **Project URL** and update `SUPABASE_URL`
5. Copy the **service_role** key and update `SUPABASE_SERVICE_ROLE_KEY`
6. If key is expired, regenerate it

**Environment Variables**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

### 🔧 Cloudflare Authentication Repair

**Issue**: HTTP 403 "Invalid zone identifier"

**Steps to Fix**:
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **My Profile** > **API Tokens**
3. Create new token with **Zone:Read** permissions
4. Go to your domain overview page
5. Copy the **Zone ID** from the right sidebar
6. Update environment variables

**Environment Variables**:
```bash
CLOUDFLARE_API_TOKEN=your-api-token
CLOUDFLARE_ZONE_ID=your-zone-id
```

**Token Permissions Required**:
- Zone:Read
- Zone:Zone Settings:Read (optional)

### 🔧 Vercel Authentication Repair

**Issue**: HTTP 403 "invalidToken":true

**Steps to Fix**:
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to **Settings** > **Tokens**
3. Delete the old token if it exists
4. Create a new token
5. Update environment variables

**Environment Variables**:
```bash
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID=your-project-id
```

## Verification Steps

After making changes:

1. **Validate Environment Variables**:
   ```bash
   python validate_env_vars.py
   ```

2. **Test Authentication**:
   ```bash
   python fix_cloud_auth.py
   ```

3. **Run Full Connection Test**:
   ```bash
   python test_cloud_connections.py
   ```

## Expected Results

After successful repair, you should see:
```
🎯 Overall Status: 6/6 services connected
🎉 All cloud services are properly configured and connected!
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**:
   - Check if `.env` file exists in project root
   - Verify environment variables are exported in shell
   - Restart application after changes

2. **API Keys Still Invalid After Regeneration**:
   - Wait 5-10 minutes for propagation
   - Clear browser cache
   - Try generating new keys

3. **Permission Errors**:
   - Verify API token scopes/permissions
   - Check if account has access to resources
   - Ensure tokens aren't expired

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure secret management
- Regularly rotate API keys
- Use least-privilege principle for token permissions
