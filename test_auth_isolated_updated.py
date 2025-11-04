#!/usr/bin/env python3
"""
Updated Security Audit for PR #562
Tests authentication and rate limiting security after fixes
"""
import os
import sys

os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-for-audit-only-32chars-long"

def audit_jwt_secret():
    """Audit JWT Secret configuration"""
    print("=" * 60)
    print("JWT Secret Configuration Audit")
    print("=" * 60)
    
    issues = []
    warnings = []
    passed = []
    
    with open("/home/ubuntu/repos/morningai/orchestrator/api/auth.py", "r") as f:
        auth_content = f.read()
    
    if "change-me-in-production" in auth_content:
        issues.append({
            "severity": "CRITICAL",
            "title": "Default JWT Secret Present",
            "location": "auth.py",
            "description": "Default secret 'change-me-in-production' still exists",
            "impact": "Attackers can forge JWT tokens using known default secret",
            "recommendation": "Remove default secret"
        })
    else:
        passed.append("✅ No default JWT secret in code")
    
    if "def validate_config(cls):" in auth_content:
        passed.append("✅ JWT secret validation function exists")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "Missing JWT Secret Validation",
            "location": "auth.py",
            "description": "No validation function for JWT secret",
            "impact": "System may start without JWT secret",
            "recommendation": "Add validate_config() method"
        })
    
    if "AuthConfig.validate_config()" in auth_content:
        passed.append("✅ JWT secret validation is called on startup")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "JWT Secret Validation Not Called",
            "location": "auth.py",
            "description": "validate_config() is not called on module load",
            "impact": "System may start without JWT secret",
            "recommendation": "Call AuthConfig.validate_config() after load_api_keys()"
        })
    
    if "raise RuntimeError" in auth_content and "ORCHESTRATOR_JWT_SECRET" in auth_content:
        passed.append("✅ Raises RuntimeError when JWT secret is missing")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "No RuntimeError on Missing Secret",
            "location": "auth.py",
            "description": "System doesn't raise error when JWT secret is missing",
            "impact": "System may start with None secret",
            "recommendation": "Raise RuntimeError in validate_config()"
        })
    
    if "len(cls.JWT_SECRET_KEY) < 32" in auth_content:
        passed.append("✅ Warns when JWT secret is too short")
    else:
        warnings.append({
            "severity": "WARNING",
            "title": "No Short Secret Warning",
            "location": "auth.py",
            "description": "System doesn't warn about short JWT secrets",
            "impact": "Weak secrets may be used",
            "recommendation": "Add length check in validate_config()"
        })
    
    return issues, warnings, passed

def audit_rate_limiter():
    """Audit Rate Limiter Redis initialization"""
    print("\n" + "=" * 60)
    print("Rate Limiter Redis Initialization Audit")
    print("=" * 60)
    
    issues = []
    warnings = []
    passed = []
    
    with open("/home/ubuntu/repos/morningai/orchestrator/api/rate_limiter.py", "r") as f:
        rate_limiter_content = f.read()
    
    with open("/home/ubuntu/repos/morningai/orchestrator/api/main.py", "r") as f:
        main_content = f.read()
    
    if "redis_client_getter" in rate_limiter_content:
        passed.append("✅ Uses redis_client_getter for lazy initialization")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "No Lazy Initialization",
            "location": "rate_limiter.py",
            "description": "RateLimitMiddleware doesn't use lazy initialization",
            "impact": "Redis client may not be available at middleware init time",
            "recommendation": "Use redis_client_getter parameter"
        })
    
    if "def _get_rate_limiter(self)" in rate_limiter_content:
        passed.append("✅ _get_rate_limiter method exists")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "Missing _get_rate_limiter Method",
            "location": "rate_limiter.py",
            "description": "No method to get rate limiter with current Redis client",
            "impact": "Cannot dynamically get Redis client",
            "recommendation": "Add _get_rate_limiter() method"
        })
    
    if "redis_client_getter=get_redis_client" in main_content:
        passed.append("✅ main.py passes redis_client_getter to middleware")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "Rate Limiter Not Initialized with Redis",
            "location": "main.py",
            "description": "RateLimitMiddleware not initialized with redis_client_getter",
            "impact": "Falls back to local memory, losing distributed rate limiting",
            "recommendation": "Pass redis_client_getter=get_redis_client"
        })
    
    if "def get_redis_client():" in main_content:
        passed.append("✅ get_redis_client function exists in main.py")
    else:
        issues.append({
            "severity": "CRITICAL",
            "title": "Missing get_redis_client Function",
            "location": "main.py",
            "description": "No function to get Redis client",
            "impact": "Cannot pass Redis client to middleware",
            "recommendation": "Add get_redis_client() function"
        })
    
    if "redis_client=None" in main_content:
        issues.append({
            "severity": "CRITICAL",
            "title": "Old Initialization Still Present",
            "location": "main.py",
            "description": "Old redis_client=None initialization still in code",
            "impact": "May override correct initialization",
            "recommendation": "Remove redis_client=None"
        })
    else:
        passed.append("✅ Old redis_client=None removed")
    
    return issues, warnings, passed

def print_results(issues, warnings, passed):
    """Print audit results"""
    print("\n" + "=" * 60)
    print("SECURITY AUDIT RESULTS")
    print("=" * 60)
    
    if issues:
        print("\n🔴 CRITICAL ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. 🔴 {issue['severity']}: {issue['title']}")
            print(f"   Location: {issue['location']}")
            print(f"   Description: {issue['description']}")
            print(f"   Impact: {issue['impact']}")
            print(f"   Recommendation: {issue['recommendation']}")
    else:
        print("\n🔴 CRITICAL ISSUES:")
        print("   None found ✅")
    
    if warnings:
        print("\n🟡 WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"\n{i}. 🟡 {warning['severity']}: {warning['title']}")
            print(f"   Location: {warning['location']}")
            print(f"   Description: {warning['description']}")
            print(f"   Impact: {warning['impact']}")
            print(f"   Recommendation: {warning['recommendation']}")
    
    if passed:
        print("\n✅ PASSED CHECKS:")
        for check in passed:
            print(f"   {check}")
    
    print("\n" + "=" * 60)
    print("FINAL ASSESSMENT")
    print("=" * 60)
    print(f"🔴 Critical Issues: {len(issues)}")
    print(f"🟡 Warnings: {len(warnings)}")
    print(f"✅ Passed Checks: {len(passed)}")
    
    if issues:
        print("\n❌ RECOMMENDATION: DO NOT MERGE")
        print("   Critical security issues must be fixed before production deployment")
        return 1
    else:
        print("\n✅ RECOMMENDATION: APPROVED FOR MERGE")
        print("   All critical security issues have been resolved")
        if warnings:
            print(f"   Note: {len(warnings)} warning(s) can be addressed in future PRs")
        return 0

def main():
    print("\n🔐 PR #562 SECURITY AUDIT - UPDATED")
    print("Verifying fixes for critical security issues\n")
    
    jwt_issues, jwt_warnings, jwt_passed = audit_jwt_secret()
    
    rl_issues, rl_warnings, rl_passed = audit_rate_limiter()
    
    all_issues = jwt_issues + rl_issues
    all_warnings = jwt_warnings + rl_warnings
    all_passed = jwt_passed + rl_passed
    
    exit_code = print_results(all_issues, all_warnings, all_passed)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
