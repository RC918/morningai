#!/usr/bin/env python3
"""
Deployment verification script for Morning AI Flask backend
"""
import os
import sys
import requests
import time
from datetime import datetime

def test_local_build():
    """Test the build process locally"""
    print("🔍 Testing local build process...")
    original_dir = os.getcwd()
    
    try:
        os.chdir("handoff/20250928/40_App/api-backend")
        
        result = os.system("pip install --upgrade pip && pip install -r requirements.txt")
        if result != 0:
            print("❌ Local build failed")
            return False
        
        print("✅ Local build successful")
        return True
    except Exception as e:
        print(f"❌ Local build error: {e}")
        return False
    finally:
        os.chdir(original_dir)

def test_local_start():
    """Test the start command locally"""
    print("🔍 Testing local start process...")
    original_dir = os.getcwd()
    
    try:
        os.chdir("handoff/20250928/40_App/api-backend/src")
        
        sys.path.insert(0, os.getcwd())
        
        import main
        print("✅ main.py imports successfully")
        
        if hasattr(main, 'app'):
            print("✅ Flask app object found")
            return True
        else:
            print("❌ Flask app object not found")
            return False
            
    except Exception as e:
        print(f"❌ main.py import failed: {e}")
        return False
    finally:
        os.chdir(original_dir)
        if os.getcwd() in sys.path:
            sys.path.remove(os.getcwd())

def test_deployed_endpoints(base_url):
    """Test deployed endpoints"""
    endpoints = ["/health", "/healthz", "/api/auth/login"]
    
    print(f"🔍 Testing deployed endpoints at {base_url}...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"✅ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def check_directory_structure():
    """Verify the expected directory structure exists"""
    print("🔍 Checking directory structure...")
    
    required_paths = [
        "handoff/20250928/40_App/api-backend",
        "handoff/20250928/40_App/api-backend/src",
        "handoff/20250928/40_App/api-backend/src/main.py",
        "handoff/20250928/40_App/api-backend/requirements.txt"
    ]
    
    all_exist = True
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - NOT FOUND")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Morning AI Deployment Verification")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    if not check_directory_structure():
        print("❌ Directory structure check failed")
        sys.exit(1)
    
    if test_local_build() and test_local_start():
        print("🎉 Local testing passed - ready for deployment")
        
        if len(sys.argv) > 1:
            deployment_url = sys.argv[1]
            test_deployed_endpoints(deployment_url)
    else:
        print("❌ Local testing failed")
        sys.exit(1)
