#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'handoff/20250928/40_App/api-backend/src'))

try:
    from main import app
    print("✅ Flask app imports successfully")
    
    mock_routes = [rule.rule for rule in app.url_map.iter_rules() if 'mock' in rule.rule]
    print(f"✅ Mock API endpoints available: {mock_routes}")
    
    with app.test_client() as client:
        response = client.get('/health')
        print(f"✅ Health endpoint status: {response.status_code}")
        
        for route in ['/api/dashboard/mock', '/api/checkout/mock', '/api/settings/mock']:
            try:
                response = client.get(route)
                print(f"✅ {route} status: {response.status_code}")
            except Exception as e:
                print(f"❌ {route} error: {e}")
                
except Exception as e:
    print(f"❌ Backend test failed: {e}")
    import traceback
    traceback.print_exc()
