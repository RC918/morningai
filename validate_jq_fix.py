#!/usr/bin/env python3
"""
Validate the jq assertion fix for post-deploy health checks
"""

import requests
import json
import subprocess
import tempfile
import os

def test_jq_assertion_fix():
    """Test the fixed jq assertion logic"""
    
    print("=== 🧪 Testing Fixed jq Assertion Logic ===")
    
    try:
        response = requests.get("https://morningai-backend-v2.onrender.com/healthz", timeout=10)
        health_data = response.json()
        print(f"✅ Health endpoint response: {json.dumps(health_data, indent=2)}")
    except Exception as e:
        print(f"❌ Failed to get health response: {e}")
        return False
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(health_data, f)
        temp_file = f.name
    
    try:
        jq_command = [
            'jq', '-e',
            '(.phase | test("Phase 8")) and ((.version // .app_version // .app_version_tag // .app_build // "") | test("^8[.]0[.]0$")) and ((.status == "healthy") or (.database == "connected"))',
            temp_file
        ]
        
        result = subprocess.run(jq_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Fixed jq assertion works correctly!")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Fixed jq assertion failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing jq assertion: {e}")
        return False
    finally:
        os.unlink(temp_file)

if __name__ == "__main__":
    success = test_jq_assertion_fix()
    exit(0 if success else 1)
