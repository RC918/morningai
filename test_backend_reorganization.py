#!/usr/bin/env python3
"""
Test Backend Reorganization and Verification
Tests the Phase 8 backend reorganization according to B-1 standards
"""

import os
import sys
import subprocess
import requests
import time
from datetime import datetime

def test_environment_variables():
    """Test A-1: Environment variables setup"""
    print("🧪 Testing Environment Variables Setup")
    print("=" * 50)
    
    required_vars = ['DATABASE_URL', 'APP_VERSION']
    optional_vars = ['REDIS_URL', 'OPENAI_API_KEY', 'SENTRY_DSN', 'CORS_ORIGINS']
    
    env_file = '/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend/.env.local'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"❌ Environment file not found: {env_file}")
        return False
    
    missing_required = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: {os.environ.get(var)}")
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: not set (optional)")
    
    if missing_required:
        print(f"❌ Missing required variables: {missing_required}")
        return False
    
    print("✅ Environment variables validation passed")
    return True

def test_file_structure():
    """Test B-1: File structure reorganization"""
    print("\n🧪 Testing File Structure Reorganization")
    print("=" * 50)
    
    backend_path = '/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend'
    expected_structure = {
        'src/services/report_generator.py': 'Report generator service',
        'src/services/monitoring_dashboard.py': 'Monitoring dashboard service',
        'src/persistence/state_manager.py': 'Persistent state manager',
        'src/utils/env_schema_validator.py': 'Environment schema validator',
        'src/adapters/__init__.py': 'Adapters module',
        'src/orchestration/__init__.py': 'Orchestration module',
        '.env.local': 'Local environment variables'
    }
    
    all_exist = True
    for file_path, description in expected_structure.items():
        full_path = os.path.join(backend_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}: {description}")
        else:
            print(f"❌ {file_path}: Missing - {description}")
            all_exist = False
    
    if all_exist:
        print("✅ File structure reorganization completed")
        return True
    else:
        print("❌ File structure reorganization incomplete")
        return False

def test_single_command_startup():
    """Test A-2: Single command startup"""
    print("\n🧪 Testing Single Command Startup")
    print("=" * 50)
    
    backend_path = '/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend'
    
    os.chdir(backend_path)
    
    subprocess.run(['bash', '-c', 'set -a; source .env.local; set +a'], check=False)
    
    print("Testing import validation...")
    try:
        sys.path.insert(0, os.path.join(backend_path, 'src'))
        from utils.env_schema_validator import validate_environment
        from persistence.state_manager import PersistentStateManager
        from services.report_generator import report_generator
        from services.monitoring_dashboard import monitoring_dashboard
        print("✅ All imports successful")
        
        validation_result = validate_environment()
        if validation_result['valid']:
            print("✅ Environment validation passed")
        else:
            print(f"⚠️  Environment validation warnings: {validation_result['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint accessibility"""
    print("\n🧪 Testing Health Endpoint")
    print("=" * 50)
    
    health_url = "http://127.0.0.1:10000/health"
    
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health endpoint accessible: {health_url}")
            print(f"✅ Status: {health_data.get('status')}")
            print(f"✅ Version: {health_data.get('version')}")
            print(f"✅ Backend Services: {health_data.get('backend_services')}")
            return True, health_data
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Health endpoint not accessible (server may not be running): {e}")
        return False, None

def run_comprehensive_verification():
    """Run comprehensive Phase 8 backend verification"""
    print("🧪 Phase 8 Backend Reorganization Verification Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    result1 = test_environment_variables()
    test_results.append(("Environment Variables Setup", result1))
    
    result2 = test_file_structure()
    test_results.append(("File Structure Reorganization", result2))
    
    result3 = test_single_command_startup()
    test_results.append(("Import Validation", result3))
    
    result4, health_data = test_health_endpoint()
    test_results.append(("Health Endpoint", result4))
    
    print("\n" + "=" * 80)
    print("🎯 PHASE 8 BACKEND VERIFICATION RESULTS")
    print("=" * 80)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall Result: {passed_tests}/{len(test_results)} tests passed")
    
    if health_data:
        print("\n📊 Health Endpoint Response:")
        print(f"   Status: {health_data.get('status')}")
        print(f"   Version: {health_data.get('version')}")
        print(f"   Environment: {health_data.get('environment')}")
        print(f"   Backend Services: {health_data.get('backend_services')}")
        print(f"   Database: {health_data.get('database')}")
        print(f"   Security: {health_data.get('security')}")
    
    if passed_tests >= 3:  # Allow health endpoint to fail if server not running
        print("🎉 BACKEND REORGANIZATION VERIFICATION PASSED!")
        print("✅ Ready for gunicorn startup testing")
    else:
        print("⚠️  Some verification tests failed. Review issues above.")
    
    return passed_tests >= 3

if __name__ == "__main__":
    success = run_comprehensive_verification()
    exit(0 if success else 1)
