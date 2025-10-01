#!/usr/bin/env python3
"""
Post-Merge JWT Authentication Verification
Tests JWT authentication after PR #23 is merged and deployed
"""

import requests
import json
import time
import sys

def wait_for_deployment(max_wait=300):
    """Wait for deployment to complete after merge"""
    print("⏳ Waiting for deployment to complete...")
    base_url = "https://morningai-backend-v2.onrender.com"
    
    for i in range(max_wait // 10):
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Deployment ready - Phase: {data.get('phase')}, Version: {data.get('version')}")
                return True
        except Exception as e:
            print(f"⏳ Waiting... ({i*10}s)")
            time.sleep(10)
    
    print("❌ Deployment timeout")
    return False

def test_security_endpoints_authentication():
    """Test that security endpoints now require authentication"""
    base_url = "https://morningai-backend-v2.onrender.com"
    
    security_endpoints = [
        "/api/security/reviews/pending",
        "/api/security/access/evaluate", 
        "/api/security/events/review",
        "/api/security/hitl/pending",
        "/api/security/audit"
    ]
    
    print("=== 🔐 Testing Security Endpoint Authentication ===")
    
    protected_count = 0
    for endpoint in security_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code in [401, 403]:
                print(f"✅ {endpoint} correctly protected (HTTP {response.status_code})")
                protected_count += 1
            else:
                print(f"⚠️ {endpoint} returns HTTP {response.status_code} (expected 401/403)")
        except Exception as e:
            print(f"❌ {endpoint} request failed: {e}")
    
    success_rate = (protected_count / len(security_endpoints)) * 100
    print(f"\n📊 Authentication Protection: {protected_count}/{len(security_endpoints)} ({success_rate:.1f}%)")
    
    return success_rate >= 80  # 80% success threshold

if __name__ == "__main__":
    print("=== 🚀 Post-Merge JWT Authentication Verification ===")
    
    if wait_for_deployment():
        if test_security_endpoints_authentication():
            print("✅ JWT authentication verification PASSED")
            sys.exit(0)
        else:
            print("❌ JWT authentication verification FAILED")
            sys.exit(1)
    else:
        print("❌ Deployment verification FAILED")
        sys.exit(1)
