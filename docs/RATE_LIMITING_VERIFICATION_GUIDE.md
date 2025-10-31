# Rate Limiting Verification Guide

## Overview

This guide provides step-by-step instructions for verifying rate limiting functionality in staging and production environments. Rate limiting protects the API from abuse by limiting requests to 60 per minute per IP address by default.

## Quick Reference

**Default Configuration**:
- **Limit**: 60 requests per 60 seconds
- **Scope**: Per IP address (or per user if RATE_LIMIT_BY_USER=true)
- **Algorithm**: Redis sliding window
- **Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- **Retry Mechanism**: Non-blocking retry with exponential backoff (1s, 2s, 3s), then 60s cooldown
- **Thread Safety**: Protected by threading.Lock() for multi-threaded WSGI servers

**Environment Variables**:
```bash
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=true               # Fail on startup if Redis unavailable (production)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

---

## Staging Verification

### Prerequisites

1. **Staging backend is deployed**: https://morningai-backend-v2-stg.onrender.com
2. **Redis is available**: Check health endpoint shows Redis connected
3. **curl or similar HTTP client**: For making test requests

### Step 1: Verify Health Check

```bash
curl -i https://morningai-backend-v2-stg.onrender.com/healthz
```

**Expected Response**:
```json
{
  "status": "healthy",
  "redis": {
    "status": "connected",
    "protocol": "rediss",
    "tls_enabled": true
  }
}
```

✅ **Verify**: Redis status is "connected"

### Step 2: Test Rate Limit Headers

Make a single request to any API endpoint:

```bash
curl -i https://morningai-backend-v2-stg.onrender.com/api/v1/agents
```

**Expected Headers**:
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1730304120
```

✅ **Verify**:
- `X-RateLimit-Limit` is present and equals 60
- `X-RateLimit-Remaining` is present and equals 59 (one less than limit)
- `X-RateLimit-Reset` is present and is a Unix timestamp

### Step 3: Test Rate Limit Enforcement

Use a script to make 61 requests rapidly:

```bash
#!/bin/bash
# test_rate_limit.sh

ENDPOINT="https://morningai-backend-v2-stg.onrender.com/api/v1/agents"

echo "Making 61 requests to test rate limiting..."
for i in {1..61}; do
  response=$(curl -s -w "\n%{http_code}" "$ENDPOINT")
  status_code=$(echo "$response" | tail -n1)
  remaining=$(curl -s -I "$ENDPOINT" | grep -i "X-RateLimit-Remaining" | cut -d' ' -f2 | tr -d '\r')
  
  echo "Request $i: Status=$status_code, Remaining=$remaining"
  
  if [ "$status_code" = "429" ]; then
    echo "✅ Rate limit triggered at request $i"
    break
  fi
done
```

**Expected Output**:
```
Request 1: Status=200, Remaining=59
Request 2: Status=200, Remaining=58
...
Request 60: Status=200, Remaining=0
Request 61: Status=429, Remaining=0
✅ Rate limit triggered at request 61
```

✅ **Verify**:
- First 60 requests return 200 OK
- 61st request returns 429 Too Many Requests
- Remaining count decreases correctly (59, 58, 57, ..., 0)

### Step 4: Test Rate Limit Response

When rate limit is exceeded, verify the error response:

```bash
# After triggering rate limit (61st request)
curl -i https://morningai-backend-v2-stg.onrender.com/api/v1/agents
```

**Expected Response**:
```json
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1730304180

{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Maximum 60 requests per 60 seconds."
  }
}
```

✅ **Verify**:
- Status code is 429
- Error message is clear and actionable
- Headers are present with correct values
- Remaining is 0

### Step 5: Test Rate Limit Reset

Wait for the rate limit window to expire (60 seconds), then make another request:

```bash
# Wait 60 seconds
sleep 60

# Make new request
curl -i https://morningai-backend-v2-stg.onrender.com/api/v1/agents
```

**Expected Response**:
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
```

✅ **Verify**:
- Request succeeds (200 OK)
- Remaining is reset to 59
- Rate limiting is working correctly

---

## Production Verification

### Prerequisites

1. **Production backend is deployed**: https://morningai-backend-v2.onrender.com
2. **Redis is available**: Check health endpoint shows Redis connected
3. **Low traffic period**: Verify during off-peak hours to avoid affecting real users
4. **Monitoring enabled**: Sentry and logs are available

### Step 1: Verify Health Check

```bash
curl -i https://morningai-backend-v2.onrender.com/healthz
```

**Expected Response**:
```json
{
  "status": "healthy",
  "redis": {
    "status": "connected",
    "protocol": "rediss",
    "tls_enabled": true
  }
}
```

✅ **Verify**: Redis status is "connected"

### Step 2: Test Rate Limit Headers (Production)

⚠️ **Important**: Use a test endpoint or low-impact endpoint to avoid affecting production data.

```bash
curl -i https://morningai-backend-v2.onrender.com/healthz
```

**Expected Headers**:
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1730304120
```

✅ **Verify**:
- Headers are present and correct
- Remaining decreases with each request

### Step 3: Monitor Rate Limiting in Production

**Check Logs**:
```bash
# In Render dashboard, check logs for rate limit warnings
# Look for: "Rate limit exceeded for IP X.X.X.X: N requests"
```

**Check Sentry**:
- Navigate to Sentry dashboard
- Filter by environment: production
- Look for rate limit related events (should be minimal)

**Check Metrics**:
- Monitor 429 response rate in Render dashboard
- Should be < 1% of total requests under normal conditions

✅ **Verify**:
- No unexpected rate limit errors
- Legitimate users are not being blocked
- Abusive IPs are being rate limited

---

## Troubleshooting

### Issue: Rate Limit Headers Not Present

**Symptoms**:
- No X-RateLimit-* headers in response
- Rate limiting not working

**Diagnosis**:
```bash
# Check Redis connection
curl https://morningai-backend-v2-stg.onrender.com/healthz | jq '.redis'

# Check environment variables
# In Render dashboard → Environment → Check REDIS_URL is set
```

**Fix**:
1. Verify Redis is connected (health check)
2. Check REDIS_URL environment variable is set correctly
3. Verify Redis is accessible from backend service
4. Check logs for Redis connection errors

### Issue: Rate Limit Not Triggering

**Symptoms**:
- Can make > 60 requests without getting 429
- Remaining count not decreasing

**Diagnosis**:
```bash
# Check if Redis is actually being used
# Look for logs: "✅ Rate limit Redis connection established"

# Check if rate limiting is disabled
# RATE_LIMIT_REQUESTS might be set too high
```

**Fix**:
1. Verify RATE_LIMIT_REQUESTS is set to 60 (or desired value)
2. Check Redis pipeline operations are executing correctly
3. Verify sorted set is being created in Redis (use Redis CLI)
4. Check for errors in logs

### Issue: Rate Limit Too Aggressive

**Symptoms**:
- Legitimate users getting 429 errors
- Rate limit triggering too early

**Diagnosis**:
```bash
# Check current rate limit configuration
# RATE_LIMIT_REQUESTS and RATE_LIMIT_WINDOW values
```

**Fix**:
1. Increase RATE_LIMIT_REQUESTS (e.g., 100, 120)
2. Increase RATE_LIMIT_WINDOW (e.g., 120 seconds)
3. Consider implementing user-based rate limiting (future enhancement)

### Issue: Remaining Calculation Incorrect

**Symptoms**:
- Remaining count doesn't match expected value
- Off-by-one errors

**Diagnosis**:
```bash
# Check X-RateLimit-Remaining header
# Should be: RATE_LIMIT_REQUESTS - current_count - 1
```

**Fix**:
- This was fixed in PR #985 and this PR
- Verify you're running the latest version
- Check that remaining = max(0, RATE_LIMIT_REQUESTS - pre_count - 1)

---

## Testing Checklist

Use this checklist when verifying rate limiting in any environment:

### Basic Functionality
- [ ] Health check shows Redis connected
- [ ] X-RateLimit-Limit header present and correct
- [ ] X-RateLimit-Remaining header present and decreases
- [ ] X-RateLimit-Reset header present and is valid Unix timestamp

### Rate Limit Enforcement
- [ ] First 60 requests return 200 OK
- [ ] 61st request returns 429 Too Many Requests
- [ ] Error response includes clear error message
- [ ] Error response includes correct headers

### Rate Limit Reset
- [ ] After 60 seconds, rate limit resets
- [ ] New requests succeed after reset
- [ ] Remaining count resets to 59

### Edge Cases
- [ ] Multiple IPs are tracked independently
- [ ] X-Forwarded-For header is respected
- [ ] Redis connection errors don't break API
- [ ] Rate limiting works with tuple responses

### Production Specific
- [ ] No impact on legitimate users
- [ ] Monitoring shows expected 429 rate (< 1%)
- [ ] Logs show rate limit warnings for abusive IPs
- [ ] Sentry shows no rate limit related errors

---

## Advanced Testing

### Test with Multiple IPs

Use different X-Forwarded-For headers to simulate multiple clients:

```bash
# Client 1
for i in {1..61}; do
  curl -H "X-Forwarded-For: 1.2.3.4" https://morningai-backend-v2-stg.onrender.com/api/v1/agents
done

# Client 2 (should have independent rate limit)
curl -H "X-Forwarded-For: 5.6.7.8" https://morningai-backend-v2-stg.onrender.com/api/v1/agents
```

✅ **Verify**: Each IP has independent rate limit

### Test Sliding Window

Verify sliding window algorithm (not fixed window):

```bash
# Make 30 requests at T=0
for i in {1..30}; do
  curl https://morningai-backend-v2-stg.onrender.com/api/v1/agents
done

# Wait 30 seconds
sleep 30

# Make 30 more requests at T=30 (should succeed)
for i in {1..30}; do
  curl https://morningai-backend-v2-stg.onrender.com/api/v1/agents
done

# Make 1 more request at T=30 (should fail - 61 requests in 60s window)
curl -i https://morningai-backend-v2-stg.onrender.com/api/v1/agents
```

✅ **Verify**: Sliding window correctly tracks requests over time

---

## Monitoring Dashboard

### Key Metrics to Track

1. **Rate Limit Hit Rate**: % of requests that receive 429
   - **Target**: < 1% under normal conditions
   - **Alert**: > 5% indicates potential issue

2. **Redis Connection Status**: Uptime of Redis connection
   - **Target**: 99.9% uptime
   - **Alert**: Any disconnections

3. **Average Remaining Count**: Average X-RateLimit-Remaining across requests
   - **Target**: > 30 (indicates healthy usage patterns)
   - **Alert**: < 10 (indicates users approaching limits)

4. **Top Rate Limited IPs**: IPs receiving most 429 responses
   - **Action**: Investigate for abuse or legitimate high-volume users

---

## Enhanced Features (Available)

### User-Based Rate Limiting

Enable user-based rate limiting instead of IP-based:

```bash
# In environment variables
RATE_LIMIT_BY_USER=true
```

**How it works**:
- If user is authenticated (has `g.user_id` set), rate limit is per user
- If user is not authenticated, falls back to IP-based rate limiting
- Provides more granular control for authenticated users
- Prevents abuse from shared IPs (e.g., corporate networks)

**Testing**:
```bash
# Test with authenticated user
curl -H "Authorization: Bearer <token>" https://morningai-backend-v2-stg.onrender.com/api/v1/agents

# Check logs for: "Rate limit exceeded for user <user_id>"
```

### Redis Connection Retry Mechanism

Automatic retry with exponential backoff for transient Redis failures:

```bash
# Configure retry behavior
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Default: 3 attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Default: 1 second base delay
```

**How it works**:
- First failure: Retry after 1 second
- Second failure: Retry after 2 seconds
- Third failure: Retry after 3 seconds
- After max retries: Disable rate limiting (graceful degradation)

**Monitoring**:
```bash
# Check logs for retry attempts
# Look for: "⚠️ Rate limit Redis connection failed (attempt N/3), will retry"
```

### Monitoring Integration

Rate limit metrics are automatically tracked in `g.metrics` for monitoring:

**Metrics Available**:
- `rate_limit_exceeded`: Boolean indicating if rate limit was hit
- `rate_limit_remaining`: Number of requests remaining in window
- `rate_limit_identifier`: IP or user_id that was rate limited

**Integration with Owner Console**:
- Metrics can be consumed by monitoring middleware
- Track rate limit hit rate over time
- Identify top rate-limited IPs/users
- Alert on unusual rate limit patterns

## Next Steps

After verifying rate limiting works correctly:

1. **Monitor Production**: Watch for any issues in first 24-48 hours
2. **Adjust Limits**: Based on actual usage patterns, adjust RATE_LIMIT_REQUESTS if needed
3. **User Communication**: Update API documentation with rate limit information
4. **Consider Additional Features**:
   - Different limits for authenticated vs anonymous users
   - Rate limit bypass for trusted IPs
   - Retry-After header in 429 responses
   - Per-endpoint rate limits

---

## P0 Fixes (PR #989)

### Issue 1: Blocking Retry Mechanism

**Problem**: The original implementation used `time.sleep()` which blocked request threads for 1s/2s/3s during Redis connection retries, causing request latency spikes in multi-threaded WSGI servers.

**Solution**: Implemented non-blocking retry mechanism using `time.monotonic()` deadlines:
- Requests check `next_retry_deadline` without blocking
- Only one thread attempts reconnection at a time (`redis_connecting` flag)
- After max retries (3), uses 60s cooldown instead of permanent disable
- No `time.sleep()` calls in request path

**Verification**:
```python
# Test that retry mechanism doesn't block
import time
start = time.time()
# Make request during backoff window
response = requests.get(endpoint)
elapsed = time.time() - start
assert elapsed < 0.1  # Should return immediately, not block
```

### Issue 2: Global Variable Race Condition

**Problem**: Module-level globals (`redis_retry_count`, `redis_connecting`, etc.) were not thread-safe, causing race conditions in multi-threaded WSGI servers (gunicorn, uwsgi).

**Solution**: Added `threading.Lock()` to protect all shared state:
- `redis_state_lock = threading.Lock()` protects all retry state
- Lock acquired before checking/modifying: `redis_client`, `redis_connecting`, `retry_attempts`, `next_retry_deadline`
- Lock never held during slow operations (Redis connection attempt)
- Early return for `redis_client is not None` before lock for test compatibility

**Verification**:
```python
# Test thread safety with concurrent requests
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(requests.get, endpoint) for _ in range(100)]
    results = [f.result() for f in futures]
    # All requests should succeed without race conditions
    assert all(r.status_code in [200, 429] for r in results)
```

### Issue 3: Incorrect User ID Extraction

**Problem**: Code checked `g.user_id` but auth middleware actually sets `request.user_id` and `request.current_user`, causing user-based rate limiting to fail.

**Solution**: Implemented robust user ID extraction with fallbacks:
```python
def _extract_user_id():
    # 1. Try request.user_id (set by auth middleware)
    uid = getattr(request, 'user_id', None)
    if uid:
        return str(uid)
    
    # 2. Try request.current_user dict
    cu = getattr(request, 'current_user', None)
    if isinstance(cu, dict) and cu.get('user_id'):
        return str(cu['user_id'])
    
    # 3. Fallback to g.user_id for compatibility
    uid = getattr(g, 'user_id', None)
    if uid:
        return str(uid)
    
    return None
```

**Verification**:
```bash
# Test user-based rate limiting with authenticated user
export RATE_LIMIT_BY_USER=true
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -i https://morningai-backend-v2-stg.onrender.com/api/v1/agents

# Check that rate limit key uses user ID, not IP
# Expected: rate_limit:user:{user_id} in Redis
```

### Test Coverage

Added 8 new tests for P0 fixes:
- `test_non_blocking_retry`: Verifies no `time.sleep()` calls
- `test_retry_backoff_window`: Verifies requests return immediately during backoff
- `test_single_thread_connection_attempt`: Verifies only one thread attempts reconnection
- `test_user_id_extraction_from_request`: Tests `request.user_id` extraction
- `test_user_id_extraction_from_current_user_dict`: Tests `request.current_user` extraction
- `test_user_id_extraction_fallback_to_g`: Tests `g.user_id` fallback
- `test_user_id_extraction_returns_none_when_not_found`: Tests None return
- `test_rate_limit_with_user_id`: Tests end-to-end user-based rate limiting

All 23 rate limit tests pass ✅

---

**Last Updated**: 2025-10-30  
**Related PRs**: #985, #989  
**Maintained By**: Backend Team
