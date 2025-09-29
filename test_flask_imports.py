#!/usr/bin/env python3
"""
Test Flask imports for Phase 8 API endpoints
"""

import sys
import os

def test_flask_imports():
    """Test Flask application imports"""
    print("🧪 Testing Flask Imports")
    print("=" * 50)
    
    try:
        backend_path = os.path.join(os.path.dirname(__file__), 'handoff/20250928/40_App/api-backend')
        sys.path.insert(0, backend_path)
        
        print(f"Added path: {backend_path}")
        
        from src.models.user import db
        print("✅ Models import successful")
        
        from src.main import app
        print("✅ Flask app import successful")
        
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        phase8_routes = [r for r in routes if 'dashboard' in r or 'reports' in r]
        print(f"✅ Phase 8 routes registered: {len(phase8_routes)} routes")
        for route in phase8_routes:
            print(f"   - {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flask_imports()
    exit(0 if success else 1)
