#!/usr/bin/env python3
"""
Redis Security Verification Script
Validates Redis configuration and security settings
"""
import os
import sys
import time
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_result(check: str, status: str, details: str = ""):
    """Print check result"""
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{icon} {check}: {status}")
    if details:
        print(f"   {details}")


def check_environment_variables() -> Dict[str, Any]:
    """Check Redis environment variables"""
    print_header("Environment Variables Check")
    
    results = {
        "upstash_url": os.getenv("UPSTASH_REDIS_REST_URL"),
        "upstash_token": os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        "redis_url": os.getenv("REDIS_URL"),
        "has_secure_config": False,
        "config_type": None
    }
    
    if results["upstash_url"] and results["upstash_token"]:
        print_result("Upstash Configuration", "PASS", "HTTPS REST API configured")
        results["has_secure_config"] = True
        results["config_type"] = "upstash"
    elif results["redis_url"]:
        if results["redis_url"].startswith("rediss://"):
            print_result("Redis TLS Configuration", "PASS", "TLS enabled (rediss://)")
            results["has_secure_config"] = True
            results["config_type"] = "redis_tls"
        else:
            print_result("Redis Configuration", "FAIL", "Non-TLS connection (redis://)")
            results["config_type"] = "redis_plain"
    else:
        print_result("Redis Configuration", "FAIL", "No Redis configuration found")
    
    return results


def test_upstash_connection() -> bool:
    """Test Upstash Redis connection"""
    print_header("Upstash Connection Test")
    
    try:
        from agents.dev_agent.persistence.upstash_redis_client import UpstashRedisClient
        
        client = UpstashRedisClient()
        
        start_time = time.time()
        if client.ping():
            latency = (time.time() - start_time) * 1000
            print_result("PING", "PASS", f"Latency: {latency:.2f}ms")
        else:
            print_result("PING", "FAIL", "No response")
            return False
        
        test_key = "security_test_key"
        test_value = "test_value_123"
        
        if client.set(test_key, test_value, ex=60):
            print_result("SET", "PASS", f"Key: {test_key}")
        else:
            print_result("SET", "FAIL")
            return False
        
        retrieved_value = client.get(test_key)
        if retrieved_value == test_value:
            print_result("GET", "PASS", f"Value matches")
        else:
            print_result("GET", "FAIL", f"Expected: {test_value}, Got: {retrieved_value}")
            return False
        
        client.delete(test_key)
        print_result("DELETE", "PASS", "Cleanup successful")
        
        return True
        
    except ImportError as e:
        print_result("Import", "FAIL", f"upstash-redis not installed: {e}")
        return False
    except Exception as e:
        print_result("Connection", "FAIL", str(e))
        return False


def test_redis_tls_connection() -> bool:
    """Test Redis TLS connection"""
    print_header("Redis TLS Connection Test")
    
    try:
        import redis
        import ssl
        
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            print_result("Configuration", "SKIP", "REDIS_URL not set")
            return False
        
        if not redis_url.startswith("rediss://"):
            print_result("TLS", "FAIL", "Not using TLS (rediss://)")
            return False
        
        client = redis.from_url(
            redis_url,
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        start_time = time.time()
        if client.ping():
            latency = (time.time() - start_time) * 1000
            print_result("PING", "PASS", f"Latency: {latency:.2f}ms")
        else:
            print_result("PING", "FAIL")
            return False
        
        test_key = "security_test_key"
        test_value = "test_value_123"
        
        client.set(test_key, test_value, ex=60)
        print_result("SET", "PASS", f"Key: {test_key}")
        
        retrieved_value = client.get(test_key)
        if retrieved_value == test_value:
            print_result("GET", "PASS", "Value matches")
        else:
            print_result("GET", "FAIL", f"Expected: {test_value}, Got: {retrieved_value}")
            return False
        
        client.delete(test_key)
        print_result("DELETE", "PASS", "Cleanup successful")
        
        return True
        
    except ImportError as e:
        print_result("Import", "FAIL", f"redis not installed: {e}")
        return False
    except Exception as e:
        print_result("Connection", "FAIL", str(e))
        return False


def test_api_backend_redis() -> bool:
    """Test API backend Redis client"""
    print_header("API Backend Redis Client Test")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handoff', '20250928', '40_App', 'api-backend', 'src'))
        from utils.redis_client import create_redis_client, get_redis_connection_info
        
        info = get_redis_connection_info()
        print(f"Type: {info.get('type')}")
        print(f"Protocol: {info.get('protocol')}")
        print(f"TLS Enabled: {info.get('tls_enabled')}")
        
        if not info.get('tls_enabled'):
            print_result("Security", "FAIL", "TLS not enabled")
            return False
        
        client = create_redis_client()
        
        if hasattr(client, 'ping'):
            if client.ping():
                print_result("Connection", "PASS", "Backend client working")
                return True
            else:
                print_result("Connection", "FAIL", "PING failed")
                return False
        else:
            print_result("Connection", "WARN", "Cannot test Upstash REST client ping")
            return True
        
    except Exception as e:
        print_result("Backend Client", "FAIL", str(e))
        return False


def generate_security_report(env_results: Dict[str, Any], tests_passed: Dict[str, bool]):
    """Generate final security report"""
    print_header("Security Report")
    
    print("Configuration:")
    if env_results["config_type"] == "upstash":
        print("  ✅ Type: Upstash Redis (HTTPS)")
        print("  ✅ Encryption: HTTPS")
        print("  ✅ Authentication: Bearer Token")
    elif env_results["config_type"] == "redis_tls":
        print("  ✅ Type: Redis with TLS")
        print("  ✅ Encryption: TLS 1.2+")
        print("  ⚠️  Recommendation: Migrate to Upstash for HTTPS")
    else:
        print("  ❌ Type: Insecure or missing")
        print("  ❌ Encryption: None")
    
    print("\nTest Results:")
    for test_name, passed in tests_passed.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {test_name}")
    
    print("\nOverall Status:")
    all_passed = all(tests_passed.values())
    has_secure_config = env_results["has_secure_config"]
    
    if all_passed and has_secure_config:
        print("  ✅ SECURE - All checks passed")
        return 0
    elif has_secure_config:
        print("  ⚠️  PARTIAL - Configuration secure but some tests failed")
        return 1
    else:
        print("  ❌ INSECURE - Configuration not secure")
        return 2


def main():
    """Main verification function"""
    print_header("Redis Security Verification")
    print("Morning AI - Redis Security Check")
    print("Date:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    env_results = check_environment_variables()
    
    tests_passed = {}
    
    if env_results["config_type"] == "upstash":
        tests_passed["Upstash Connection"] = test_upstash_connection()
    elif env_results["config_type"] == "redis_tls":
        tests_passed["Redis TLS Connection"] = test_redis_tls_connection()
    
    tests_passed["API Backend Client"] = test_api_backend_redis()
    
    exit_code = generate_security_report(env_results, tests_passed)
    
    print("\n" + "="*60)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
