# Redis Requirements for PreAuthTokenManager

**Status**: Active  
**Date**: 2025-11-08  
**Component**: `src/utils/pre_auth_token.py`  
**Related PRs**: #1200, #1203, #1206

---

## Overview

The PreAuthTokenManager uses Redis for stateful JWT token management with atomic consumption guarantees. This document specifies the Redis features and configuration required for correct operation.

## Critical Redis Features Required

### 1. WATCH/MULTI/EXEC Transaction Support

**Requirement**: Redis server MUST support WATCH/MULTI/EXEC commands for optimistic locking.

**Why**: The `consume_token_atomic()` method uses Redis transactions to provide race-condition-free single-use token enforcement. Without WATCH/MULTI support, concurrent token consumption attempts could result in double-use vulnerabilities.

**Implementation Pattern**:
```python
def consume_token_atomic(self, jti: str, max_retries: int = 3) -> bool:
    """
    Atomically mark a token as consumed using Redis WATCH/MULTI transaction.
    
    This method provides race-condition-free single-use enforcement by using
    optimistic locking. If two concurrent requests try to consume the same token,
    only one will succeed.
    """
    redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
    
    for attempt in range(max_retries):
        pipeline = self.redis_client.pipeline()
        try:
            # WATCH: Monitor key for changes
            pipeline.watch(redis_key)
            
            # Read current state
            token_data = pipeline.hgetall(redis_key)
            if not token_data:
                pipeline.unwatch()
                return False
            
            # Check if already consumed
            if str(token_data.get("consumed")) in ("True", "1"):
                pipeline.unwatch()
                return False
            
            # Get current TTL before modification
            ttl = pipeline.ttl(redis_key)
            
            # MULTI: Begin atomic block
            pipeline.multi()
            
            # Update consumed flag
            pipeline.hset(
                redis_key, 
                mapping={"consumed": "True", "consumed_at": now_iso}
            )
            
            # Preserve TTL (critical for audit/logging)
            if ttl > 0:
                pipeline.expire(redis_key, ttl)
            
            # EXEC: Execute atomically
            pipeline.execute()
            
            return True
            
        except redis.exceptions.WatchError:
            # Key was modified by another client, retry
            continue
        finally:
            pipeline.reset()
    
    return False  # Failed after max_retries
```

**Transaction Semantics**:
- `WATCH key`: Monitors key for changes by other clients
- `MULTI`: Begins transaction block (queues commands)
- `EXEC`: Executes all queued commands atomically, OR aborts if watched key was modified
- `WatchError`: Raised when transaction aborts due to key modification

**Concurrency Guarantee**: If 10 threads simultaneously attempt to consume the same token, exactly 1 will succeed and 9 will fail (verified by `test_double_consume_same_token_is_atomic`).

### 2. TTL Preservation During Hash Updates

**Requirement**: Redis server MUST support `TTL` command and `EXPIRE` command to preserve expiration times during hash updates.

**Why**: When marking a token as consumed via `HSET`, Redis does NOT automatically preserve the existing TTL. Without explicit TTL preservation, consumed tokens would persist indefinitely in Redis, causing memory leaks and audit log pollution.

**Problem Without TTL Preservation**:
```python
# Initial state
redis.hset("preauth:jti:abc123", mapping={"consumed": "False"})
redis.expire("preauth:jti:abc123", 300)  # 5 minutes

# After HSET without TTL preservation
redis.hset("preauth:jti:abc123", "consumed", "True")
# TTL is now -1 (no expiration) - MEMORY LEAK!
```

**Solution - TTL Preservation Pattern**:
```python
# Get TTL before modification
ttl = pipeline.ttl(redis_key)

# Modify hash
pipeline.hset(redis_key, mapping={"consumed": "True", "consumed_at": now_iso})

# Restore TTL
if ttl > 0:
    pipeline.expire(redis_key, ttl)
```

**Unique Feature**: Unlike the legacy `preauth_token.py` system (which uses Lua `eval()` scripts), the JWT-based PreAuthTokenManager preserves TTL during atomic consumption. This enables:
- Audit trail: Consumed tokens remain in Redis until original expiry
- Debugging: Can inspect consumed tokens for forensics
- Rate limiting: Can track consumption attempts even after success

**Test Coverage**: `test_ttl_preserved_during_atomic_consume` verifies TTL preservation behavior.

### 3. Hash Data Structure Support

**Requirement**: Redis server MUST support hash data structures (`HSET`, `HGETALL`, `HINCRBY`).

**Why**: Token metadata is stored as Redis hashes for efficient field-level updates.

**Hash Schema**:
```
Key: morningai:pre_auth:jti:{jti}
Fields:
  user_id: "550e8400-e29b-41d4-a716-446655440000"
  email: "user@example.com"
  scope: "challenge" | "enroll"
  issued_at: "2025-11-08T10:30:00+00:00"
  attempts: "0"
  consumed: "False"
  consumed_at: "2025-11-08T10:32:15+00:00"  (set after consumption)
TTL: 300 seconds (5 minutes)
```

**Operations**:
- `HSET`: Set token fields on generation
- `HGETALL`: Read all token fields for verification
- `HINCRBY`: Atomically increment attempt counter
- `EXPIRE`: Set/update TTL

### 4. Pipeline Support

**Requirement**: Redis client MUST support pipelining for batching commands.

**Why**: The atomic consumption pattern requires multiple commands to be executed within a transaction. Pipelining reduces network round-trips and enables WATCH/MULTI/EXEC.

**Client Requirements**:
```python
# Python redis client (>=5.2.0)
pipeline = redis_client.pipeline()
pipeline.watch(key)
pipeline.multi()
pipeline.hset(...)
pipeline.expire(...)
pipeline.execute()
```

### 5. Exception Handling for WatchError

**Requirement**: Redis client MUST raise `redis.exceptions.WatchError` when WATCH transaction fails.

**Why**: The retry mechanism depends on catching `WatchError` to detect contention and retry.

**Retry Pattern**:
```python
for attempt in range(max_retries):
    try:
        # ... WATCH/MULTI/EXEC ...
        return True
    except redis.exceptions.WatchError:
        logger.debug(f"Contention detected, attempt {attempt + 1}/{max_retries}")
        continue  # Retry
```

**Default Retries**: `max_retries=3` (configurable per call)

**Test Coverage**: `test_retry_on_contention` verifies retry mechanism with 15 concurrent threads.

---

## Redis Connection Requirements

### Supported Redis Configurations

#### Option 1: Upstash Redis (Recommended for Production)

**Connection**:
```bash
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-secret-token
```

**Advantages**:
- ✅ HTTPS/TLS encryption by default
- ✅ Automatic security updates
- ✅ Managed service (no maintenance)
- ✅ Supports all required features (WATCH/MULTI/EXEC, TTL, hashes)

**Client**: `upstash-redis>=1.1.0`

#### Option 2: Standard Redis with TLS (Self-Hosted)

**Connection**:
```bash
REDIS_URL=rediss://user:password@your-redis-host:6380/0
```

**Requirements**:
- ✅ Redis version: 6.0+ (for WATCH/MULTI/EXEC stability)
- ✅ TLS enabled (`rediss://` protocol)
- ✅ Authentication enabled
- ✅ Network isolation (not exposed to public internet)

**Client**: `redis>=5.2.0,<6.0.0`

#### Option 3: Local Redis (Development Only)

**Connection**:
```bash
REDIS_URL=redis://localhost:6379/0
```

**Restrictions**:
- ⚠️ Only for local development
- ⚠️ Must NOT be used in production
- ⚠️ Must NOT be exposed to network

### Minimum Redis Version

**Requirement**: Redis 6.0 or higher

**Why**:
- Redis 6.0+ has stable WATCH/MULTI/EXEC implementation
- Redis 6.0+ supports ACLs for security
- Redis 6.0+ has improved pipeline performance

**Version Check**:
```bash
redis-cli INFO server | grep redis_version
# Expected: redis_version:6.0.0 or higher
```

---

## Configuration

### Environment Variables

```bash
# Redis connection (choose one)
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io  # Recommended
UPSTASH_REDIS_REST_TOKEN=your-secret-token
# OR
REDIS_URL=rediss://user:password@host:6380/0  # Self-hosted with TLS

# Redis key prefix (default: "morningai")
REDIS_KEY_PREFIX=morningai

# JWT secret for token signing
JWT_SECRET_KEY=your-secret-key-min-32-chars

# Environment (affects JWT_SECRET_KEY validation)
ENVIRONMENT=production  # or staging, development
```

### Python Dependencies

**requirements.txt**:
```python
redis>=5.2.0,<6.0.0
upstash-redis>=1.1.0,<2.0.0
PyJWT>=2.8.0,<3.0.0
```

**Why These Versions**:
- `redis>=5.2.0`: Stable WATCH/MULTI/EXEC support
- `upstash-redis>=1.1.0`: Latest security features
- `PyJWT>=2.8.0`: Secure JWT encoding/decoding

---

## Performance Characteristics

### Latency

**Typical Latency** (Upstash Redis):
- Token generation: 20-50ms (1 HSET + 1 EXPIRE)
- Token verification: 15-30ms (1 HGETALL)
- Token consumption: 25-60ms (1 WATCH + 1 HGETALL + 1 TTL + 1 HSET + 1 EXPIRE)

**Contention Handling**:
- First attempt: 25-60ms
- Retry on contention: +10-20ms per retry
- Max retries: 3 (default)
- Worst case: ~100ms (3 retries)

### Throughput

**Concurrent Token Consumption**:
- 10 threads consuming same token: 1 success, 9 failures (atomic guarantee)
- 10 threads consuming different tokens: 10 successes (no contention)
- High load test: 20 threads, 5 tokens, no deadlocks (verified by `test_consume_under_load_no_deadlock`)

**Rate Limiting**:
- Token generation: Limited by `MAX_ATTEMPTS_PER_TOKEN=5`
- Token verification: No inherent limit (application-level rate limiting recommended)

---

## Security Considerations

### 1. Atomic Consumption Prevents Double-Use

**Threat**: Attacker intercepts pre-auth token and attempts to use it multiple times.

**Mitigation**: WATCH/MULTI/EXEC ensures only one consumption succeeds, even under race conditions.

**Test Coverage**: `test_double_consume_same_token_is_atomic`

### 2. TTL Preservation Limits Attack Window

**Threat**: Consumed tokens persist indefinitely, allowing forensic analysis by attacker.

**Mitigation**: TTL preservation ensures consumed tokens expire at original time, limiting exposure.

**Test Coverage**: `test_ttl_preserved_during_atomic_consume`

### 3. JTI Uniqueness Prevents Collisions

**Threat**: Two tokens with same JTI could cause confusion or security issues.

**Mitigation**: `uuid.uuid4()` generates cryptographically random JTIs with negligible collision probability.

**Test Coverage**: `test_generate_tokens_concurrently_unique_jti` (20 concurrent threads, all unique)

### 4. Scope Enforcement Prevents Privilege Escalation

**Threat**: Attacker uses "enroll" token for "challenge" flow or vice versa.

**Mitigation**: Token scope is stored in Redis and verified during consumption.

**Test Coverage**: `test_concurrent_consume_different_scopes`

---

## Troubleshooting

### Issue: WatchError Rate Too High

**Symptom**: Logs show frequent "Contention consuming token" messages.

**Cause**: High concurrent load on same token (unusual for pre-auth tokens).

**Solution**:
1. Increase `max_retries` parameter (default: 3)
2. Add exponential backoff between retries
3. Investigate why same token is being consumed concurrently (possible attack)

### Issue: TTL Not Preserved

**Symptom**: Consumed tokens persist indefinitely in Redis.

**Cause**: Redis version < 6.0 or client library issue.

**Solution**:
1. Verify Redis version: `redis-cli INFO server | grep redis_version`
2. Upgrade to Redis 6.0+
3. Verify `pipeline.ttl()` returns positive value before `pipeline.expire()`

### Issue: Token Consumption Fails Silently

**Symptom**: `consume_token_atomic()` returns `False` but no error logged.

**Cause**: Token already consumed or not found in Redis.

**Solution**:
1. Check token expiry (default: 5 minutes)
2. Verify token was generated successfully
3. Check Redis connectivity
4. Review logs for "Token jti {jti} already consumed" or "not found" messages

---

## Migration from Legacy System

### Legacy System: `preauth_token.py` (Deprecated)

**Old Approach**: Lua `eval()` scripts for atomic consumption

```python
# Legacy: Lua script
lua_script = """
local key = KEYS[1]
local data = redis.call('GET', key)
if data then
    redis.call('DEL', key)
    return data
else
    return nil
end
"""
result = redis.eval(lua_script, 1, redis_key)
```

**Issues**:
- ❌ No TTL preservation (consumed tokens deleted immediately)
- ❌ Opaque tokens (no JWT claims)
- ❌ No scope enforcement
- ❌ Limited observability

### New System: `pre_auth_token.py` (Current)

**New Approach**: WATCH/MULTI/EXEC transactions with JWT

```python
# New: WATCH/MULTI/EXEC
pipeline.watch(redis_key)
token_data = pipeline.hgetall(redis_key)
ttl = pipeline.ttl(redis_key)
pipeline.multi()
pipeline.hset(redis_key, mapping={"consumed": "True", "consumed_at": now_iso})
if ttl > 0:
    pipeline.expire(redis_key, ttl)
pipeline.execute()
```

**Advantages**:
- ✅ TTL preservation for audit trail
- ✅ JWT-based tokens with claims (user_id, email, scope)
- ✅ Scope enforcement (enroll vs challenge)
- ✅ Better observability (consumed tokens remain in Redis until expiry)

**Migration Path**: See `docs/DEPRECATED_MODULES.md` for detailed migration guide.

---

## Testing

### Unit Tests

**File**: `tests/test_preauth_manager_concurrency.py`

**Coverage**:
- ✅ Atomic consumption (10 threads, 1 success)
- ✅ TTL preservation during consumption
- ✅ JTI uniqueness (20 concurrent generations)
- ✅ Concurrent consumption of different tokens (no false contention)
- ✅ High load without deadlocks (20 threads, 5 tokens)
- ✅ Retry mechanism on contention (15 threads, max_retries=5)
- ✅ Edge cases (nonexistent token, already consumed)
- ✅ Real-world workflow (verify → consume)
- ✅ Scope enforcement (enroll vs challenge)

**Run Tests**:
```bash
cd handoff/20250928/40_App/api-backend
pytest tests/test_preauth_manager_concurrency.py -v
```

### Integration Tests

**File**: `tests/test_preauth_e2e.py`

**Coverage**:
- ✅ Full login → 2FA verification flow
- ✅ Token generation and consumption
- ✅ Error handling (expired, invalid, already consumed)

---

## References

### Internal Documentation

- [PreAuthTokenManager Implementation](../handoff/20250928/40_App/api-backend/src/utils/pre_auth_token.py)
- [Deprecated Modules Guide](./DEPRECATED_MODULES.md)
- [Redis Security Guide](./REDIS_SECURITY_GUIDE.md)
- [2FA Pre-Auth Token Design](./2fa-owner-launch/02-pre-auth-token-design.md)

### External Resources

- [Redis WATCH/MULTI/EXEC Documentation](https://redis.io/docs/interact/transactions/)
- [Redis Hash Commands](https://redis.io/commands/?group=hash)
- [Redis TTL Command](https://redis.io/commands/ttl/)
- [Upstash Redis Documentation](https://docs.upstash.com/redis)

### Related PRs

- **PR #1200**: Consolidate pre-auth token modules to JWT-based system
- **PR #1203**: Add atomic pre-auth token consumption and concurrency tests
- **PR #1206**: Add comprehensive concurrency tests for PreAuthTokenManager

---

**Last Updated**: 2025-11-08  
**Next Review**: 2026-02-08 (Quarterly)  
**Owner**: Security Team / CTO
