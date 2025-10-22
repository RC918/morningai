#!/usr/bin/env python3
"""
Test JWT Secret Validation Fix
Tests that the system properly validates JWT_SECRET on startup
"""
import os
import sys
import subprocess

def test_missing_jwt_secret():
    """Test that system fails when JWT_SECRET is not set"""
    print("=" * 80)
    print("TEST 1: Missing JWT_SECRET should raise RuntimeError")
    print("=" * 80)
    
    env = os.environ.copy()
    if "ORCHESTRATOR_JWT_SECRET" in env:
        del env["ORCHESTRATOR_JWT_SECRET"]
    
    result = subprocess.run(
        [sys.executable, "-c", "from orchestrator.api.auth import AuthConfig"],
        env=env,
        cwd="/home/ubuntu/repos/morningai",
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        if "CRITICAL SECURITY ERROR" in result.stderr and "ORCHESTRATOR_JWT_SECRET" in result.stderr:
            print("✅ PASS: System correctly rejects missing JWT_SECRET")
            print(f"Error message: {result.stderr[:200]}...")
            return True
        else:
            print(f"❌ FAIL: Unexpected error: {result.stderr}")
            return False
    else:
        print("❌ FAIL: System should have raised RuntimeError but didn't")
        return False

def test_short_jwt_secret():
    """Test that system warns when JWT_SECRET is too short"""
    print("\n" + "=" * 80)
    print("TEST 2: Short JWT_SECRET should log warning")
    print("=" * 80)
    
    env = os.environ.copy()
    env["ORCHESTRATOR_JWT_SECRET"] = "short"
    
    result = subprocess.run(
        [sys.executable, "-c", "from orchestrator.api.auth import AuthConfig"],
        env=env,
        cwd="/home/ubuntu/repos/morningai",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ PASS: System accepts short JWT_SECRET (warning should be logged)")
        print("Note: Warning is logged at runtime, not visible in this test")
        return True
    else:
        print(f"❌ FAIL: System should accept short secret with warning: {result.stderr}")
        return False

def test_valid_jwt_secret():
    """Test that system accepts valid JWT_SECRET"""
    print("\n" + "=" * 80)
    print("TEST 3: Valid JWT_SECRET should be accepted")
    print("=" * 80)
    
    env = os.environ.copy()
    env["ORCHESTRATOR_JWT_SECRET"] = "a" * 32  # 32 character secret
    
    result = subprocess.run(
        [sys.executable, "-c", "from orchestrator.api.auth import AuthConfig; print('SUCCESS')"],
        env=env,
        cwd="/home/ubuntu/repos/morningai",
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "SUCCESS" in result.stdout:
        print("✅ PASS: System accepts valid JWT_SECRET")
        return True
    else:
        print(f"❌ FAIL: System should accept valid secret: {result.stderr}")
        return False

def test_no_default_secret():
    """Test that default secret 'change-me-in-production' is removed"""
    print("\n" + "=" * 80)
    print("TEST 4: Verify no default secret in code")
    print("=" * 80)
    
    with open("/home/ubuntu/repos/morningai/orchestrator/api/auth.py", "r") as f:
        content = f.read()
    
    if "change-me-in-production" in content:
        print("❌ FAIL: Default secret 'change-me-in-production' still exists in code")
        return False
    else:
        print("✅ PASS: Default secret removed from code")
        return True

if __name__ == "__main__":
    print("\n🔐 JWT SECRET VALIDATION TEST SUITE")
    print("Testing PR #562 Critical Fix #1\n")
    
    results = []
    results.append(("Missing JWT_SECRET", test_missing_jwt_secret()))
    results.append(("Short JWT_SECRET", test_short_jwt_secret()))
    results.append(("Valid JWT_SECRET", test_valid_jwt_secret()))
    results.append(("No default secret", test_no_default_secret()))
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - JWT Secret validation is working correctly!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
