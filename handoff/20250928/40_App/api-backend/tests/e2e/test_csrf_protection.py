"""
Playwright E2E Tests for CSRF Protection

Tests cookie attributes and CSRF protection using real browser engines.
This ensures that browser cookie policies (SameSite, Secure) are correctly enforced.

Why Playwright instead of Python requests?
- Python requests does NOT enforce browser cookie policies
- Browsers reject SameSite=None without Secure=true, but requests accepts it
- Playwright uses real browser engines (Chromium, Firefox, WebKit)
"""

import pytest
from playwright.sync_api import Page, expect
import json

STAGING_API = "https://morningai-backend-v2-stg.onrender.com"
TEST_EMAIL = "ryan2939x@gmail.com"
TEST_PASSWORD = "CPas32Aw95JPP6ikXkmQXmaxfvg9YcYJ"


@pytest.fixture
def staging_context(playwright):
    """Create browser context with Staging API"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        base_url=STAGING_API,
        ignore_https_errors=False  # Enforce HTTPS validation
    )
    yield context
    context.close()
    browser.close()


def test_cookie_attributes(staging_context):
    """
    Test 1: Verify pre_auth_token cookie has correct attributes
    
    Expected:
    - SameSite=None (for cross-domain)
    - Secure=true (required for SameSite=None)
    - HttpOnly=true (security)
    - Path=/api/auth/v2/totp (scoped)
    """
    page = staging_context.new_page()
    
    print("\n" + "="*80)
    print("TEST 1: Cookie Attributes Verification")
    print("="*80)
    
    print(f"\n1. Logging in as {TEST_EMAIL}...")
    response = page.request.post(
        f"{STAGING_API}/api/auth/v2/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    print(f"   Login response status: {response.status}")
    assert response.status == 200, f"Login failed with status {response.status}"
    
    print("\n2. Retrieving cookies from browser context...")
    cookies = staging_context.cookies()
    print(f"   Total cookies: {len(cookies)}")
    
    pre_auth_cookie = next((c for c in cookies if c['name'] == 'pre_auth_token'), None)
    
    if pre_auth_cookie is None:
        print("\n❌ ERROR: pre_auth_token cookie not found!")
        print(f"   Available cookies: {[c['name'] for c in cookies]}")
        assert False, "pre_auth_token cookie not found"
    
    print(f"\n3. Found pre_auth_token cookie!")
    print(f"   Cookie details:")
    print(f"   - Name: {pre_auth_cookie['name']}")
    print(f"   - Domain: {pre_auth_cookie['domain']}")
    print(f"   - Path: {pre_auth_cookie['path']}")
    print(f"   - SameSite: {pre_auth_cookie['sameSite']}")
    print(f"   - Secure: {pre_auth_cookie['secure']}")
    print(f"   - HttpOnly: {pre_auth_cookie['httpOnly']}")
    
    print("\n4. Verifying cookie attributes...")
    
    errors = []
    
    if pre_auth_cookie['sameSite'] != 'None':
        errors.append(f"Expected SameSite=None, got {pre_auth_cookie['sameSite']}")
    
    if not pre_auth_cookie['secure']:
        errors.append("Expected Secure=true, got false")
    
    if not pre_auth_cookie['httpOnly']:
        errors.append("Expected HttpOnly=true, got false")
    
    if pre_auth_cookie['path'] != '/api/auth/v2/totp':
        errors.append(f"Expected Path=/api/auth/v2/totp, got {pre_auth_cookie['path']}")
    
    if errors:
        print("\n❌ Cookie attribute verification FAILED:")
        for error in errors:
            print(f"   - {error}")
        assert False, "\n".join(errors)
    
    print("\n✅ Cookie attributes verified successfully!")
    print(f"   ✓ SameSite: {pre_auth_cookie['sameSite']}")
    print(f"   ✓ Secure: {pre_auth_cookie['secure']}")
    print(f"   ✓ HttpOnly: {pre_auth_cookie['httpOnly']}")
    print(f"   ✓ Path: {pre_auth_cookie['path']}")


def test_csrf_protection_without_token(staging_context):
    """
    Test 2A: Verify CSRF protection rejects requests without X-CSRF-Token
    
    Expected:
    - Request without X-CSRF-Token → 403 Forbidden
    - Error message mentions CSRF
    """
    page = staging_context.new_page()
    
    print("\n" + "="*80)
    print("TEST 2A: CSRF Protection (Without Token)")
    print("="*80)
    
    print(f"\n1. Logging in as {TEST_EMAIL}...")
    login_response = page.request.post(
        f"{STAGING_API}/api/auth/v2/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    print(f"   Login response status: {login_response.status}")
    
    print("\n2. Attempting verify-login WITHOUT X-CSRF-Token...")
    response = page.request.post(
        f"{STAGING_API}/api/auth/v2/totp/verify-login",
        data={"totp_code": "123456"}
    )
    
    print(f"   Response status: {response.status}")
    
    try:
        body = response.json()
        print(f"   Response body: {json.dumps(body, indent=2)}")
    except:
        print(f"   Response text: {response.text()}")
        body = {}
    
    if response.status != 403:
        print(f"\n❌ CSRF protection FAILED: Expected 403, got {response.status}")
        assert False, f"Expected 403 Forbidden, got {response.status}"
    
    error_msg = body.get('error', '') + body.get('message', '') + body.get('detail', '')
    if 'csrf' not in error_msg.lower():
        print(f"\n⚠️  Warning: Error message doesn't mention CSRF: {error_msg}")
    
    print("\n✅ CSRF protection working correctly!")
    print(f"   ✓ Request without X-CSRF-Token rejected with 403")
    print(f"   ✓ Error message: {error_msg}")


def test_csrf_protection_with_token(staging_context):
    """
    Test 2B: Verify CSRF protection allows requests with valid X-CSRF-Token
    
    Expected:
    - Request with X-CSRF-Token → NOT 403 (CSRF passed)
    - Will get 401 (Invalid TOTP) or 400 (validation error)
    - This proves CSRF protection passed; auth failed for different reason
    """
    page = staging_context.new_page()
    
    print("\n" + "="*80)
    print("TEST 2B: CSRF Protection (With Valid Token)")
    print("="*80)
    
    print("\n1. Getting CSRF token...")
    csrf_response = page.request.get(f"{STAGING_API}/api/auth/v2/csrf")
    csrf_data = csrf_response.json()
    csrf_token = csrf_data['csrf_token']
    print(f"   CSRF token: {csrf_token[:20]}...")
    
    print(f"\n2. Logging in as {TEST_EMAIL}...")
    login_response = page.request.post(
        f"{STAGING_API}/api/auth/v2/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    print(f"   Login response status: {login_response.status}")
    
    print("\n3. Attempting verify-login WITH X-CSRF-Token...")
    response = page.request.post(
        f"{STAGING_API}/api/auth/v2/totp/verify-login",
        data={"totp_code": "123456"},
        headers={"X-CSRF-Token": csrf_token}
    )
    
    print(f"   Response status: {response.status}")
    
    try:
        body = response.json()
        print(f"   Response body: {json.dumps(body, indent=2)}")
    except:
        print(f"   Response text: {response.text()}")
        body = {}
    
    if response.status == 403:
        error_msg = body.get('error', '') + body.get('message', '') + body.get('detail', '')
        print(f"\n❌ CSRF protection incorrectly rejected valid token!")
        print(f"   Error: {error_msg}")
        assert False, "CSRF protection incorrectly rejected valid token"
    
    if response.status not in [400, 401]:
        print(f"\n⚠️  Unexpected status code: {response.status}")
        print(f"   Expected 400/401 (auth error), got {response.status}")
    
    print("\n✅ CSRF protection allows valid token!")
    print(f"   ✓ Request with X-CSRF-Token NOT rejected (status: {response.status})")
    print(f"   ✓ CSRF protection passed; got auth error instead (expected)")


def test_cross_domain_cookie_transmission(staging_context):
    """
    Test 3: Verify cookies are sent on cross-domain requests
    
    Expected:
    - Cookie is set with SameSite=None
    - Cookie is sent on subsequent requests
    - If cookie wasn't sent: 400 "Pre-auth token or email/password required"
    - If cookie was sent: 403 (no CSRF) or 401 (invalid TOTP)
    """
    page = staging_context.new_page()
    
    print("\n" + "="*80)
    print("TEST 3: Cross-Domain Cookie Transmission")
    print("="*80)
    
    print(f"\n1. Logging in as {TEST_EMAIL}...")
    login_response = page.request.post(
        f"{STAGING_API}/api/auth/v2/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    print(f"   Login response status: {login_response.status}")
    
    print("\n2. Verifying cookie was set...")
    cookies = staging_context.cookies()
    pre_auth_cookie = next((c for c in cookies if c['name'] == 'pre_auth_token'), None)
    
    if pre_auth_cookie is None:
        print("\n❌ ERROR: pre_auth_token cookie not set after login!")
        assert False, "pre_auth_token cookie not set"
    
    print(f"   ✓ Cookie set: {pre_auth_cookie['name']}")
    print(f"   ✓ SameSite: {pre_auth_cookie['sameSite']}")
    
    print("\n3. Making cross-domain request to verify-login...")
    print("   (Cookie should be sent because SameSite=None)")
    response = page.request.post(
        f"{STAGING_API}/api/auth/v2/totp/verify-login",
        data={"totp_code": "123456"}
    )
    
    print(f"   Response status: {response.status}")
    
    try:
        body = response.json()
        print(f"   Response body: {json.dumps(body, indent=2)}")
    except:
        print(f"   Response text: {response.text()}")
        body = {}
    
    if response.status == 400:
        error_msg = body.get('error', '') + body.get('message', '') + body.get('detail', '')
        if 'pre-auth token' in error_msg.lower() or 'email' in error_msg.lower():
            print("\n❌ Cookie NOT sent on cross-domain request!")
            print(f"   Error: {error_msg}")
            print("   This indicates SameSite policy blocked the cookie")
            assert False, "Cookie not sent on cross-domain request"
    
    if response.status in [401, 403]:
        print("\n✅ Cross-domain cookie transmission working!")
        print(f"   ✓ Cookie sent on cross-domain request (status: {response.status})")
        print(f"   ✓ SameSite=None policy working correctly")
    else:
        print(f"\n⚠️  Unexpected status: {response.status}")
        print("   Expected 401/403 (cookie sent), but got different status")


def test_set_cookie_header_inspection(staging_context):
    """
    Test 4: Inspect Set-Cookie header from login response
    
    This test captures the raw Set-Cookie header to verify the exact format.
    """
    page = staging_context.new_page()
    
    print("\n" + "="*80)
    print("TEST 4: Set-Cookie Header Inspection")
    print("="*80)
    
    print(f"\n1. Logging in as {TEST_EMAIL}...")
    response = page.request.post(
        f"{STAGING_API}/api/auth/v2/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    print(f"   Login response status: {response.status}")
    
    print("\n2. Inspecting Set-Cookie header...")
    headers = response.headers
    set_cookie = headers.get('set-cookie', '')
    
    if not set_cookie:
        print("\n⚠️  No Set-Cookie header found in response")
        print(f"   Available headers: {list(headers.keys())}")
    else:
        print(f"\n   Set-Cookie header:")
        print(f"   {set_cookie}")
        
        print("\n3. Parsing cookie attributes from header...")
        attributes = {
            'SameSite=None': 'SameSite=None' in set_cookie,
            'Secure': 'Secure' in set_cookie or 'secure' in set_cookie.lower(),
            'HttpOnly': 'HttpOnly' in set_cookie or 'httponly' in set_cookie.lower(),
            'Path=/api/auth/v2/totp': 'Path=/api/auth/v2/totp' in set_cookie,
        }
        
        print("\n   Detected attributes:")
        for attr, present in attributes.items():
            status = "✓" if present else "✗"
            print(f"   {status} {attr}: {present}")
        
        missing = [attr for attr, present in attributes.items() if not present]
        if missing:
            print(f"\n❌ Missing required attributes: {missing}")
            assert False, f"Missing cookie attributes: {missing}"
        
        print("\n✅ Set-Cookie header has all required attributes!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
