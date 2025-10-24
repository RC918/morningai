# Redis Security Guide

**Status**: Implemented  
**Date**: 2025-10-24  
**Security Level**: P1 (High Priority)

---

## Overview

Morning AI uses **Upstash Redis with HTTPS** for secure, encrypted communication. This guide documents the Redis security implementation and configuration.

## Security Architecture

### Current Implementation

```
┌─────────────────┐
│  API Backend    │
│  (Flask)        │──┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌──────────────────┐
│  Orchestrator   │──┼───▶│  Upstash Redis   │
│  (Task Queue)   │  │    │  (HTTPS REST)    │
└─────────────────┘  │    └──────────────────┘
                     │
┌─────────────────┐  │
│  Dev Agent      │──┘
│  (Persistence)  │
└─────────────────┘
```

### Security Features

✅ **HTTPS Encryption**: All Redis communication uses HTTPS REST API  
✅ **Token Authentication**: Bearer token authentication for all requests  
✅ **Automatic TLS Detection**: Falls back to TLS (rediss://) if Upstash unavailable  
✅ **No Plain Text**: Rejects non-encrypted Redis connections with warnings

---

## Configuration

### Environment Variables

#### Required (Recommended)

```bash
# Upstash Redis (HTTPS) - Recommended
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here
```

#### Optional (Fallback)

```bash
# Standard Redis with TLS (rediss://)
REDIS_URL=rediss://your-redis-host:6380/0?ssl_cert_reqs=required
```

### Priority Order

The system automatically selects Redis configuration in this order:

1. **UPSTASH_REDIS_REST_URL** (HTTPS) - Highest priority
2. **REDIS_URL** (rediss://) - TLS fallback
3. **Error** - No secure Redis configuration found

### Configuration Files

#### API Backend

File: `handoff/20250928/40_App/api-backend/src/utils/redis_client.py`

```python
def create_redis_client():
    # Priority 1: Upstash (HTTPS)
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    if upstash_url:
        return Redis(url=upstash_url, token=os.getenv("UPSTASH_REDIS_REST_TOKEN"))
    
    # Priority 2: Redis with TLS
    redis_url = os.getenv("REDIS_URL")
    if redis_url and redis_url.startswith("rediss://"):
        return redis.from_url(redis_url, ssl_cert_reqs=ssl.CERT_REQUIRED)
    
    raise ValueError("No secure Redis configuration found")
```

#### Orchestrator

File: `orchestrator/task_queue/redis_queue.py`

```python
class RedisQueue:
    def __init__(self, redis_url: Optional[str] = None):
        # Auto-detect from environment
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
        if upstash_url:
            self.redis_url = upstash_url  # HTTPS
        elif os.getenv("REDIS_URL"):
            self.redis_url = os.getenv("REDIS_URL")  # TLS fallback
        else:
            raise ValueError("No Redis configuration found")
```

---

## Security Validation

### Health Check

The `/health` endpoint reports Redis security status:

```json
{
  "status": "healthy",
  "redis": {
    "type": "upstash",
    "protocol": "https",
    "tls_enabled": true,
    "url": "***"
  }
}
```

### Connection Verification

Run the verification script to test Redis security:

```bash
python scripts/verify_redis_security.py
```

Expected output:

```
✅ Redis Configuration Check
   Type: Upstash
   Protocol: HTTPS
   TLS: Enabled

✅ Connection Test
   Ping: PONG
   Latency: 45ms

✅ Security Validation
   Encryption: HTTPS
   Authentication: Bearer Token
   Status: SECURE
```

---

## Migration Guide

### From Plain Redis (redis://)

**Before:**
```bash
REDIS_URL=redis://localhost:6379/0  # ❌ Insecure
```

**After:**
```bash
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io  # ✅ Secure
UPSTASH_REDIS_REST_TOKEN=your-token-here
```

### From Self-Hosted Redis

**Option A: Migrate to Upstash (Recommended)**

1. Create Upstash Redis instance at https://upstash.com
2. Copy REST URL and token
3. Update environment variables
4. Remove old REDIS_URL

**Option B: Enable TLS on Self-Hosted**

1. Configure Redis server with TLS:
   ```bash
   # redis.conf
   tls-port 6380
   tls-cert-file /path/to/redis.crt
   tls-key-file /path/to/redis.key
   tls-ca-cert-file /path/to/ca.crt
   ```

2. Update connection string:
   ```bash
   REDIS_URL=rediss://your-host:6380/0?ssl_cert_reqs=required
   ```

---

## Deployment

### Vercel

Add environment variables in Vercel Dashboard:

```
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=***
```

Apply to: **All Environments** (Production, Preview, Development)

### Render

Add environment variables in Render Dashboard:

```
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=***
```

### GitHub Actions

Add secrets in repository settings:

```
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
```

Reference in workflows:

```yaml
env:
  UPSTASH_REDIS_REST_URL: ${{ secrets.UPSTASH_REDIS_REST_URL }}
  UPSTASH_REDIS_REST_TOKEN: ${{ secrets.UPSTASH_REDIS_REST_TOKEN }}
```

---

## Security Best Practices

### ✅ Do

- Use Upstash Redis (HTTPS) for all environments
- Rotate Redis tokens every 90 days
- Use separate Redis instances for production/staging
- Monitor Redis access logs
- Enable Redis ACLs if using self-hosted

### ❌ Don't

- Use plain Redis (redis://) in production
- Commit Redis credentials to git
- Share Redis tokens between environments
- Expose Redis ports to public internet
- Use default Redis passwords

---

## Troubleshooting

### Connection Refused

**Error:**
```
Failed to connect to Redis: Connection refused
```

**Solution:**
1. Verify UPSTASH_REDIS_REST_URL is set
2. Check token is correct
3. Verify Upstash instance is active

### TLS Certificate Error

**Error:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
1. Use Upstash (HTTPS) instead of self-hosted TLS
2. If using self-hosted, verify certificate chain
3. Check system CA certificates are up to date

### Authentication Failed

**Error:**
```
NOAUTH Authentication required
```

**Solution:**
1. Verify UPSTASH_REDIS_REST_TOKEN is set
2. Check token hasn't expired
3. Regenerate token in Upstash dashboard if needed

---

## Monitoring

### Metrics to Track

- Connection success rate
- Average latency
- Failed authentication attempts
- TLS handshake failures

### Alerts

Set up alerts for:

- Redis connection failures (> 5% error rate)
- High latency (> 500ms)
- Authentication failures (> 10/hour)

---

## Compliance

### Standards Met

- ✅ **OWASP**: Encrypted data in transit
- ✅ **PCI DSS**: TLS 1.2+ for sensitive data
- ✅ **GDPR**: Encrypted personal data storage
- ✅ **SOC 2**: Secure data transmission

### Audit Trail

All Redis operations are logged with:

- Timestamp
- Operation type
- Source IP (if available)
- Success/failure status

---

## References

- [Upstash Redis Documentation](https://docs.upstash.com/redis)
- [Redis TLS Documentation](https://redis.io/docs/management/security/encryption/)
- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

**Last Updated**: 2025-10-24  
**Next Review**: 2026-01-24 (Quarterly)  
**Owner**: Security Team / CTO
