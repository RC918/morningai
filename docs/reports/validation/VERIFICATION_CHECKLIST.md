# Cloud Service Authentication Verification Checklist

## Pre-Verification Status
- ✅ **3/6 services connected**: Upstash Redis, Sentry, Render
- ❌ **3/6 services need repair**: Supabase, Cloudflare, Vercel

## User Action Required

### 1. Supabase Authentication Repair
**Issue**: HTTP 401 "Invalid API key"

**Steps**:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Settings** > **API**
4. Copy the **Project URL** and verify `SUPABASE_URL` is correct
5. Copy the **service_role** key and update `SUPABASE_SERVICE_ROLE_KEY`
6. If key is expired, regenerate it

### 2. Cloudflare Authentication Repair
**Issue**: HTTP 403 "Token lacks zone access permissions"

**Steps**:
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **My Profile** > **API Tokens**
3. Create new token with **Zone:Read** permissions
4. Go to your domain overview page
5. Copy the **Zone ID** from the right sidebar
6. Update `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID`

### 3. Vercel Authentication Repair
**Issue**: HTTP 403 "Invalid or expired token"

**Steps**:
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to **Settings** > **Tokens**
3. Delete the old token if it exists
4. Create a new token
5. Update `VERCEL_TOKEN`

## Verification Commands

After making changes, run these commands in order:

### Step 1: Validate Environment Variables
```bash
python validate_env_vars.py
```
**Expected**: All variables should show as "SET"

### Step 2: Test Authentication Repairs
```bash
python fix_cloud_auth.py
```
**Expected**: All 3 services should show ✅ status

### Step 3: Run Full Connection Test
```bash
python test_cloud_connections.py
```
**Expected**: "🎯 Overall Status: 6/6 services connected"

## Success Criteria
- [ ] All environment variables validated
- [ ] Supabase authentication successful
- [ ] Cloudflare authentication successful  
- [ ] Vercel authentication successful
- [ ] All 6 cloud services connected
- [ ] Existing services (Redis, Sentry, Render) remain functional

## Final Verification
When all repairs are complete, you should see:
```
🎯 Overall Status: 6/6 services connected
🎉 All cloud services are properly configured and connected!
```

## Troubleshooting
If issues persist after following repair steps:
1. Wait 5-10 minutes for API key propagation
2. Verify token permissions and scopes
3. Check for typos in environment variables
4. Ensure tokens haven't expired immediately after creation
