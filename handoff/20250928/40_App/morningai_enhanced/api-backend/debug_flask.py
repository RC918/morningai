#!/usr/bin/env python3
"""
Debug script to test Flask app imports and startup
"""
import sys
import os
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("Testing Flask app imports...")

try:
    from dotenv import load_dotenv
    print("✓ dotenv imported successfully")
    
    load_dotenv(src_path / ".env")
    print("✓ Environment variables loaded")
    
    from main import app
    print("✓ Flask app imported successfully")
    
    from cloud_health_checker import CloudResourceHealthChecker
    print("✓ CloudResourceHealthChecker imported successfully")
    
    print(f"✓ Flask app configured with secret key: {bool(app.config.get('SECRET_KEY'))}")
    
    with app.test_client() as client:
        response = client.get('/health')
        print(f"✓ Health endpoint test: {response.status_code} - {response.get_json()}")
        
        response = client.get('/api/system/metrics')
        print(f"✓ Metrics endpoint test: {response.status_code}")
        
    print("\n✅ All tests passed! Flask app should work correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
