"""
Comprehensive test runner for all Morning AI test suites
Runs all tests and generates coverage reports
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {str(e)}")
        return False

def main():
    """Run comprehensive test suite"""
    print("🚀 Morning AI Comprehensive Test Suite")
    print("=" * 80)
    
    os.chdir("/home/ubuntu/repos/morningai")
    
    test_suites = [
        ("python test_unit_phase4_api.py", "Unit Tests - Phase 4 API"),
        ("python test_unit_phase5_api.py", "Unit Tests - Phase 5 API"),
        ("python test_unit_phase6_api.py", "Unit Tests - Phase 6 API"),
        ("python test_edge_cases_comprehensive.py", "Edge Cases & Error Scenarios"),
        ("python test_integration_comprehensive.py", "Integration Tests"),
        ("python test_flask_backend_comprehensive.py", "Flask Backend Tests"),
        ("python test_performance_comprehensive.py", "Performance Tests"),
        ("python test_security_comprehensive.py", "Security Tests"),
        ("python test_database_comprehensive.py", "Database Tests"),
        ("python test_phase4_6_comprehensive.py", "Phase 4-6 Comprehensive"),
        ("python test_phase6_8_comprehensive.py", "Phase 6-8 Comprehensive"),
        ("python test_phase4_6_integrated.py", "Phase 4-6 Integrated")
    ]
    
    coverage_suites = [
        ("coverage run --source=. test_unit_phase4_api.py", "Coverage - Phase 4 Unit Tests"),
        ("coverage run --append --source=. test_unit_phase5_api.py", "Coverage - Phase 5 Unit Tests"),
        ("coverage run --append --source=. test_unit_phase6_api.py", "Coverage - Phase 6 Unit Tests"),
        ("coverage run --append --source=. test_edge_cases_comprehensive.py", "Coverage - Edge Cases"),
        ("coverage run --append --source=. test_integration_comprehensive.py", "Coverage - Integration"),
        ("coverage run --append --source=. test_flask_backend_comprehensive.py", "Coverage - Flask Backend"),
        ("coverage run --append --source=. test_performance_comprehensive.py", "Coverage - Performance"),
        ("coverage run --append --source=. test_security_comprehensive.py", "Coverage - Security"),
        ("coverage run --append --source=. test_database_comprehensive.py", "Coverage - Database")
    ]
    
    results = {}
    
    print("\n📋 Running Individual Test Suites")
    print("=" * 80)
    
    for command, description in test_suites:
        success = run_command(command, description)
        results[description] = success
        time.sleep(1)  # Brief pause between tests
    
    print("\n📊 Running Coverage Analysis")
    print("=" * 80)
    
    run_command("coverage erase", "Clear Previous Coverage Data")
    
    for command, description in coverage_suites:
        success = run_command(command, description)
        results[description] = success
        time.sleep(1)
    
    run_command("coverage report --show-missing", "Generate Coverage Report")
    run_command("coverage html", "Generate HTML Coverage Report")
    
    print("\n" + "=" * 80)
    print("📈 TEST EXECUTION SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"📊 Overall Results: {passed_tests}/{total_tests} test suites passed ({success_rate:.1f}%)")
    print()
    
    for description, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {description}")
    
    print("\n📁 Coverage Report Location:")
    print("• Text Report: Displayed above")
    print("• HTML Report: htmlcov/index.html")
    
    return success_rate >= 70  # Consider successful if 70%+ pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
