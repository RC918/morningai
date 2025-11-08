#!/usr/bin/env python3
"""
Staging 2FA Configuration Diagnostic Tool

This script diagnoses why staging might not be returning the expected 2FA flow.

Usage:
    export STAGING_API_URL="https://your-staging-api.com"
    export STAGING_TEST_EMAIL="test@example.com"
    export STAGING_TEST_PASSWORD="password123"
    python scripts/diagnose_staging_2fa.py
"""

import os
import sys
import requests
import json
from typing import Dict, Any

from common.config.settings import settings


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_info(message: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def log_success(message: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def log_error(message: str):
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def log_warning(message: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_json(data: Dict[Any, Any], indent: int = 2):
    """Pretty print JSON with colors"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def test_endpoint(api_url: str, email: str, password: str, endpoint: str) -> Dict[str, Any]:
    """Test a login endpoint and return the response"""
    log_info(f"Testing {endpoint}...")
    
    try:
        response = requests.post(
            f"{api_url}{endpoint}",
            json={"email": email, "password": password},
            timeout=10
        )
        
        log_info(f"  Status: {response.status_code}")
        
        try:
            data = response.json()
            log_info(f"  Response body:")
            print_json(data)
            return {
                "status_code": response.status_code,
                "data": data,
                "headers": dict(response.headers),
                "success": True
            }
        except:
            log_warning(f"  Response is not JSON: {response.text[:200]}")
            return {
                "status_code": response.status_code,
                "data": None,
                "text": response.text[:500],
                "success": False
            }
    except Exception as e:
        log_error(f"  Request failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    print(f"\n{Colors.BOLD}Staging 2FA Configuration Diagnostic{Colors.RESET}\n")
    
    api_url = settings.staging_api_url
    email = settings.staging_test_email
    password = settings.staging_test_password
    
    if not all([api_url, email, password]):
        log_error("Missing required environment variables:")
        log_error("  STAGING_API_URL")
        log_error("  STAGING_TEST_EMAIL")
        log_error("  STAGING_TEST_PASSWORD")
        sys.exit(1)
    
    api_url = api_url.rstrip('/')
    
    log_info(f"Testing against: {api_url}")
    log_info(f"Test user: {email}\n")
    
    print("="*70)
    print("TEST 1: Check /api/auth/v2/login (NEW enhanced endpoint)")
    print("="*70)
    
    v2_result = test_endpoint(api_url, email, password, "/api/auth/v2/login")
    
    print("\n" + "="*70)
    print("TEST 2: Check /api/auth/login (OLD legacy endpoint)")
    print("="*70)
    
    legacy_result = test_endpoint(api_url, email, password, "/api/auth/login")
    
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)
    
    if v2_result.get("success") and v2_result.get("status_code") == 200:
        data = v2_result.get("data", {})
        next_step = data.get("next_step")
        
        if next_step == "enroll_2fa":
            log_success("✓ V2 endpoint returns enroll_2fa - Ready for concurrent test!")
        elif next_step == "challenge_2fa":
            log_warning("⚠ V2 endpoint returns challenge_2fa - User already has 2FA enabled")
            log_info("  You need a test account that hasn't enrolled 2FA yet")
        elif next_step == "session":
            log_warning("⚠ V2 endpoint returns session - 2FA not required for this user")
            log_info("  Possible reasons:")
            log_info("    1. FEATURE_2FA_ENABLED=false in staging")
            log_info("    2. User doesn't have 2FA enabled in user_2fa table")
            log_info("    3. check_2fa_required() returns False for this user")
        elif next_step is None:
            log_error("✗ V2 endpoint returns next_step=null - Unexpected!")
            log_info("  This suggests:")
            log_info("    1. Staging might be running old code without next_step field")
            log_info("    2. Or there's an exception being caught")
            log_info("    3. Or response format is different than expected")
        else:
            log_warning(f"⚠ V2 endpoint returns unexpected next_step: {next_step}")
        
        if "token" in data or "tmp_login_token" in data:
            token_key = "token" if "token" in data else "tmp_login_token"
            log_success(f"✓ Temporary token found under key: {token_key}")
        elif next_step in ["enroll_2fa", "challenge_2fa"]:
            log_error("✗ No temporary token found but 2FA flow expected!")
    else:
        log_error("✗ V2 endpoint failed or returned non-200 status")
    
    if legacy_result.get("success") and legacy_result.get("status_code") == 200:
        legacy_data = legacy_result.get("data", {})
        if "next_step" not in legacy_data:
            log_info("\n✓ Legacy endpoint doesn't have next_step (expected)")
        else:
            log_warning("\n⚠ Legacy endpoint has next_step field (unexpected)")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    if v2_result.get("success"):
        data = v2_result.get("data", {})
        next_step = data.get("next_step")
        
        if next_step == "enroll_2fa":
            print(f"\n{Colors.GREEN}✓ Ready to run concurrent consumption test!{Colors.RESET}")
            print("\nRun:")
            print("  python scripts/test_staging_concurrent_consumption.py")
        
        elif next_step == "challenge_2fa":
            print(f"\n{Colors.YELLOW}⚠ Need different test account{Colors.RESET}")
            print("\nOptions:")
            print("  1. Create a new test account that hasn't enrolled 2FA")
            print("  2. Disable 2FA for current test account in staging database")
            print("  3. Modify test script to test challenge flow instead of enroll")
        
        elif next_step == "session":
            print(f"\n{Colors.YELLOW}⚠ 2FA not triggered for this account{Colors.RESET}")
            print("\nCheck staging configuration:")
            print("  1. Verify FEATURE_2FA_ENABLED=true in staging env vars")
            print("  2. Check if user has 2FA enabled in user_2fa table")
            print("  3. Verify check_2fa_required() logic for this user/role")
        
        elif next_step is None:
            print(f"\n{Colors.RED}✗ Unexpected response format{Colors.RESET}")
            print("\nInvestigate:")
            print("  1. Check staging deployment - might be running old code")
            print("  2. Check staging logs for exceptions during login")
            print("  3. Verify blueprint registration order in staging")
            print("  4. Compare staging code version with local branch")
    else:
        print(f"\n{Colors.RED}✗ Cannot connect to staging or authentication failed{Colors.RESET}")
        print("\nCheck:")
        print("  1. STAGING_API_URL is correct")
        print("  2. Test credentials are valid")
        print("  3. Staging server is running")


if __name__ == "__main__":
    main()
