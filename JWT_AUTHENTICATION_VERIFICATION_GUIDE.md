# JWT Authentication Verification Guide

## Overview
This guide documents the JWT authentication implementation for Phase 4-6 security endpoints and provides verification procedures.

## Implementation Summary

### Security Endpoints Protected
- `/api/security/reviews/pending` - Analyst+ required
- `/api/security/access/evaluate` - Admin required  
- `/api/security/events/review` - Analyst+ required
- `/api/security/hitl/pending` - Analyst+ required
- `/api/security/audit` - Admin required

### Authentication Middleware
- **Location**: `src/middleware/auth_middleware.py`
- **Decorators**: `@admin_required`, `@analyst_required`, `@jwt_required`
- **Token Generation**: `create_admin_token()`, `create_analyst_token()`

### Expected Behavior
1. **Without Authentication**: Endpoints return 401 (missing token) or 403 (insufficient privileges)
2. **With Valid Admin Token**: All endpoints accessible (200 OK)
3. **With Valid Analyst Token**: Analyst endpoints accessible, admin-only return 403
4. **With Invalid Token**: All endpoints return 401

## Verification Commands

### Quick Status Check
```bash
python test_production_auth_status.py
```

### Comprehensive Post-Merge Test
```bash
python test_jwt_post_merge.py
```

### Manual Token Testing
```bash
# Generate tokens using Python file
cat > generate_tokens.py << 'EOF'
import sys
sys.path.append('/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend/src')
from middleware.auth_middleware import create_admin_token
print(create_admin_token())
EOF
python generate_tokens.py

# Test with curl
curl -H "Authorization: Bearer <token>" https://morningai-backend-v2.onrender.com/api/security/reviews/pending
```

## Success Criteria
- ✅ 80%+ endpoints correctly protected (401/403 without auth)
- ✅ Admin tokens access all endpoints (200 OK)
- ✅ Analyst tokens respect role restrictions (403 for admin-only)
- ✅ Invalid tokens rejected (401)
- ✅ No regression in non-security endpoints

## Troubleshooting

### Common Issues
1. **500 Errors**: Check Content-Type headers for POST requests
2. **Still 200 Without Auth**: JWT middleware not deployed yet
3. **Token Generation Fails**: Check JWT_SECRET_KEY environment variable

### Rollback Plan
If authentication breaks production:
```bash
git revert <commit-hash>
git push origin main
```

## Production Deployment Status
- **PR #23**: JWT authentication implementation
- **CI Status**: All checks passed (7/7)
- **Merge Status**: Pending user approval
- **Production URL**: https://morningai-backend-v2.onrender.com
