#!/usr/bin/env python3
"""
Production Authentication Status Checker
Quick check of current authentication status in production
"""

import requests
import json

def check_production_auth_status():
    """Check current authentication status of security endpoints"""
    base_url = "https://morningai-backend-v2.onrender.com"
    
    print("=== 🔍 Production Authentication Status Check ===")
    
    # Test key security endpoints
    endpoints = [
        "/api/security/reviews/pending",
        "/api/security/access/evaluate",
        "/api/security/hitl/pending"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            status = response.status_code
            
            if status in [401, 403]:
                auth_status = "🔒 PROTECTED"
            elif status == 200:
                auth_status = "⚠️ UNPROTECTED"
            else:
                auth_status = f"❓ HTTP {status}"
                
            print(f"{endpoint}: {auth_status}")
            
        except Exception as e:
            print(f"{endpoint}: ❌ ERROR - {e}")
    
    print("\n📊 Summary:")
    print("🔒 PROTECTED = JWT authentication working (401/403)")
    print("⚠️ UNPROTECTED = No authentication required (200)")
    print("❓ OTHER = Unexpected response code")

if __name__ == "__main__":
    check_production_auth_status()
