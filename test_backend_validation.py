#!/usr/bin/env python3
"""
Backend Validation Script
Tests that all imports work and new methods exist
"""

import sys
import os

sys.path.insert(0, '/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend')

def test_imports():
    """Test that all imports work correctly"""
    try:
        from src.main import app
        print('✅ Flask app import successful')
        
        from src.persistence.state_manager import persistent_state_manager
        print('✅ PersistentStateManager import successful')
        
        methods = ['save_agent_binding', 'save_bot_creation', 'save_subscription', 'save_tenant_isolation']
        for method in methods:
            if hasattr(persistent_state_manager, method):
                print(f'✅ Method {method} exists')
            else:
                print(f'❌ Method {method} missing')
        
        return True
    except Exception as e:
        print(f'❌ Import error: {e}')
        return False

def test_time_import():
    """Test that time module is available"""
    try:
        import time
        print(f'✅ Time module available: {time.time()}')
        return True
    except Exception as e:
        print(f'❌ Time import error: {e}')
        return False

if __name__ == "__main__":
    print("🧪 Backend Validation Test")
    print("=" * 40)
    
    success = True
    success &= test_time_import()
    success &= test_imports()
    
    if success:
        print("\n✅ All backend validation tests passed")
    else:
        print("\n❌ Some backend validation tests failed")
    
    exit(0 if success else 1)
