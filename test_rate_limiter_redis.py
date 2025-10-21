#!/usr/bin/env python3
"""
Test Rate Limiter Redis Initialization Fix
Tests that the rate limiter properly uses Redis when available
"""
import sys
import asyncio
from unittest.mock import Mock, AsyncMock

sys.path.insert(0, '/home/ubuntu/repos/morningai')

async def test_rate_limiter_lazy_init():
    """Test that RateLimitMiddleware uses lazy initialization"""
    print("=" * 80)
    print("TEST 1: Rate Limiter Lazy Initialization")
    print("=" * 80)
    
    from orchestrator.api.rate_limiter import RateLimitMiddleware
    from redis.asyncio import Redis
    
    mock_app = Mock()
    
    redis_client = Mock(spec=Redis)
    redis_client.pipeline = Mock(return_value=Mock())
    
    def get_redis():
        return redis_client
    
    middleware = RateLimitMiddleware(mock_app, redis_client_getter=get_redis)
    
    if middleware.rate_limiter is None:
        print("✅ PASS: Rate limiter is None on initialization (lazy init)")
    else:
        print("❌ FAIL: Rate limiter should be None initially")
        return False
    
    rate_limiter = middleware._get_rate_limiter()
    
    if rate_limiter is not None:
        print("✅ PASS: Rate limiter created on first access")
    else:
        print("❌ FAIL: Rate limiter should be created")
        return False
    
    if rate_limiter.redis == redis_client:
        print("✅ PASS: Rate limiter uses Redis client from getter")
    else:
        print("❌ FAIL: Rate limiter should use Redis client from getter")
        return False
    
    return True

async def test_rate_limiter_without_redis():
    """Test that RateLimitMiddleware works without Redis (fallback)"""
    print("\n" + "=" * 80)
    print("TEST 2: Rate Limiter Without Redis (Fallback)")
    print("=" * 80)
    
    from orchestrator.api.rate_limiter import RateLimitMiddleware
    
    mock_app = Mock()
    
    middleware = RateLimitMiddleware(mock_app, redis_client_getter=None)
    
    rate_limiter = middleware._get_rate_limiter()
    
    if rate_limiter is not None:
        print("✅ PASS: Rate limiter created without Redis")
    else:
        print("❌ FAIL: Rate limiter should be created")
        return False
    
    if rate_limiter.redis is None:
        print("✅ PASS: Rate limiter has no Redis client (fallback mode)")
    else:
        print("❌ FAIL: Rate limiter should not have Redis client")
        return False
    
    is_limited, remaining = await rate_limiter.is_rate_limited("test_key", 5)
    
    if not is_limited and remaining == 4:
        print("✅ PASS: Local fallback works correctly")
    else:
        print(f"❌ FAIL: Local fallback incorrect: is_limited={is_limited}, remaining={remaining}")
        return False
    
    return True

async def test_main_py_integration():
    """Test that main.py correctly passes redis_client_getter"""
    print("\n" + "=" * 80)
    print("TEST 3: main.py Integration")
    print("=" * 80)
    
    with open("/home/ubuntu/repos/morningai/orchestrator/api/main.py", "r") as f:
        content = f.read()
    
    if "redis_client_getter=get_redis_client" in content:
        print("✅ PASS: main.py uses redis_client_getter parameter")
    else:
        print("❌ FAIL: main.py should use redis_client_getter parameter")
        return False
    
    if "def get_redis_client():" in content:
        print("✅ PASS: get_redis_client function exists")
    else:
        print("❌ FAIL: get_redis_client function should exist")
        return False
    
    if "redis_client=None" in content:
        print("❌ FAIL: Old redis_client=None should be removed")
        return False
    else:
        print("✅ PASS: Old redis_client=None removed")
    
    return True

async def test_rate_limiter_signature():
    """Test that RateLimitMiddleware signature is correct"""
    print("\n" + "=" * 80)
    print("TEST 4: RateLimitMiddleware Signature")
    print("=" * 80)
    
    with open("/home/ubuntu/repos/morningai/orchestrator/api/rate_limiter.py", "r") as f:
        content = f.read()
    
    if "def __init__(self, app, redis_client_getter: Optional[Callable] = None):" in content:
        print("✅ PASS: __init__ signature uses redis_client_getter")
    else:
        print("❌ FAIL: __init__ should use redis_client_getter parameter")
        return False
    
    if "def _get_rate_limiter(self) -> RateLimiter:" in content:
        print("✅ PASS: _get_rate_limiter method exists")
    else:
        print("❌ FAIL: _get_rate_limiter method should exist")
        return False
    
    if "rate_limiter = self._get_rate_limiter()" in content:
        print("✅ PASS: dispatch method uses _get_rate_limiter")
    else:
        print("❌ FAIL: dispatch should use _get_rate_limiter")
        return False
    
    return True

async def main():
    print("\n🚦 RATE LIMITER REDIS INITIALIZATION TEST SUITE")
    print("Testing PR #562 Critical Fix #2\n")
    
    results = []
    results.append(("Lazy Initialization", await test_rate_limiter_lazy_init()))
    results.append(("Fallback Without Redis", await test_rate_limiter_without_redis()))
    results.append(("main.py Integration", await test_main_py_integration()))
    results.append(("Middleware Signature", await test_rate_limiter_signature()))
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Rate Limiter Redis initialization is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
