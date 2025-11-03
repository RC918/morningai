# 2FA Feature Flag Rollout Guide

## Overview

The Two-Factor Authentication (2FA/TOTP) feature is controlled by the `FEATURE_2FA_ENABLED` environment variable. This allows for gradual rollout and easy rollback if issues are discovered.

## Feature Flag Configuration

### Environment Variable

```bash
FEATURE_2FA_ENABLED=true  # Enable 2FA feature
FEATURE_2FA_ENABLED=false # Disable 2FA feature (default)
```

**Default**: `false` (feature disabled)

### Behavior When Disabled

When `FEATURE_2FA_ENABLED=false`:

1. **All TOTP endpoints return 403 Forbidden** (except `/status` which returns feature_disabled flag)
2. **Existing 2FA configurations remain in database** but are not enforced
3. **Login flow bypasses 2FA verification** even for users with 2FA enabled
4. **Frontend UI should hide 2FA settings** based on `/status` response

### Behavior When Enabled

When `FEATURE_2FA_ENABLED=true`:

1. **All TOTP endpoints are accessible** to authenticated users
2. **Users can enable/disable 2FA** through settings
3. **Login flow enforces 2FA** for users who have it enabled
4. **Frontend UI shows 2FA settings** and setup wizard

## Rollout Strategy

### Phase 1: Internal Testing (Week 1)

**Environment**: Development/Staging

```bash
# Development
FEATURE_2FA_ENABLED=true

# Staging
FEATURE_2FA_ENABLED=true
```

**Actions**:
1. Enable feature flag in development and staging environments
2. Test all 2FA flows with internal team
3. Verify backup codes, trusted devices, and login flows
4. Monitor error logs and performance metrics

**Success Criteria**:
- All E2E tests passing
- No critical bugs reported
- Performance metrics within acceptable range

### Phase 2: Beta Users (Week 2)

**Environment**: Production (limited rollout)

```bash
# Production
FEATURE_2FA_ENABLED=true
```

**Actions**:
1. Enable feature flag in production
2. Announce 2FA availability to beta users via email/notification
3. Monitor adoption rate and user feedback
4. Track support tickets related to 2FA

**Success Criteria**:
- At least 10% of beta users enable 2FA
- Less than 5% support ticket rate
- No P0/P1 bugs reported

### Phase 3: General Availability (Week 3+)

**Environment**: Production (full rollout)

```bash
# Production
FEATURE_2FA_ENABLED=true
```

**Actions**:
1. Announce 2FA availability to all users
2. Send educational content about 2FA benefits
3. Consider making 2FA mandatory for admin accounts
4. Monitor system-wide metrics

**Success Criteria**:
- Stable error rates
- Positive user feedback
- No increase in support burden

## Rollback Procedure

If critical issues are discovered:

### Immediate Rollback

```bash
# Set in production environment
FEATURE_2FA_ENABLED=false
```

**Effects**:
1. All 2FA endpoints immediately return 403
2. Login flow stops requiring 2FA verification
3. Users can still log in with password only
4. Existing 2FA data preserved in database

### Restart Services

```bash
# Restart API backend to pick up new environment variable
# (Exact command depends on deployment platform)
```

### Communication

1. Notify users via status page
2. Send email to users who enabled 2FA
3. Provide timeline for re-enabling feature

## Monitoring

### Key Metrics

1. **Adoption Rate**: % of users with 2FA enabled
2. **Login Success Rate**: % of 2FA login attempts that succeed
3. **Backup Code Usage**: Frequency of backup code usage
4. **Support Tickets**: Number of 2FA-related support requests
5. **Error Rate**: 2FA endpoint error rates

### Alerts

Set up alerts for:
- 2FA endpoint error rate > 5%
- 2FA login failure rate > 10%
- Backup code exhaustion (users with 0 codes remaining)

## Testing Feature Flag

### Backend Tests

```bash
# Run backend tests with feature flag enabled
cd handoff/20250928/40_App/api-backend
export FEATURE_2FA_ENABLED=true
pytest tests/test_totp_routes.py -v

# Run backend tests with feature flag disabled
export FEATURE_2FA_ENABLED=false
pytest tests/test_totp_routes.py -v
```

### Manual Testing

1. **With Feature Enabled**:
   ```bash
   export FEATURE_2FA_ENABLED=true
   # Test all 2FA flows
   ```

2. **With Feature Disabled**:
   ```bash
   export FEATURE_2FA_ENABLED=false
   # Verify all endpoints return 403
   # Verify login works without 2FA
   ```

## Security Considerations

1. **Feature flag should be environment-based**, not user-based
2. **Do not expose feature flag status** to unauthenticated users
3. **Preserve 2FA data** when feature is disabled (for easy re-enabling)
4. **Audit log all feature flag changes** in production

## Database Impact

### When Feature is Disabled

- `user_2fa` table: Records remain but `enabled` flag is not checked during login
- `totp_backup_codes` table: Records remain but are not used
- `trusted_devices` table: Records remain but are not checked

### When Feature is Re-enabled

- All existing 2FA configurations become active again
- Users who previously enabled 2FA will need to verify on next login
- No data migration required

## Support Documentation

### User-Facing Documentation

Create documentation for:
1. How to enable 2FA
2. How to use backup codes
3. How to manage trusted devices
4. What to do if locked out

### Internal Documentation

Maintain documentation for:
1. How to assist users locked out of accounts
2. How to manually disable 2FA for a user (emergency)
3. How to monitor 2FA adoption and health

## Related Documentation

- [2FA Implementation Design](../../../docs/2FA_IMPLEMENTATION_DESIGN.md)
- [TOTP Routes API Documentation](../src/routes/totp.py)
- [TOTP Utils Documentation](../src/utils/totp_utils.py)

## Changelog

- **2025-11-03**: Initial feature flag implementation (Phase C)
- **2025-11-02**: Phase 3 (Testing & QA) completed
- **2025-11-01**: Phase 2 (Settings UI) completed
- **2025-10-31**: Phase 1 (Backend API) completed
