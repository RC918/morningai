#!/usr/bin/env python3
"""
Staging Concurrent Token Consumption Test

This script tests the atomic token consumption behavior with real Redis (Upstash)
to verify that WATCH/MULTI operations work correctly in production environment.

Usage:
    export STAGING_API_URL="https://your-staging-api.com"
    export STAGING_TEST_EMAIL="test@example.com"
    export STAGING_TEST_PASSWORD="password123"
    python scripts/test_staging_concurrent_consumption.py

Requirements:
    - Staging environment with Upstash Redis
    - Test user account with 2FA not yet enrolled
    - requests library: pip install requests
"""

import os
import sys
import time
import threading
import requests
from typing import List, Dict, Any
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_info(message: str):
    """Log info message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{Colors.BLUE}[{timestamp}]{Colors.RESET} {message}")


def log_success(message: str):
    """Log success message"""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def log_error(message: str):
    """Log error message"""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def log_warning(message: str):
    """Log warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


class StagingConcurrentTest:
    """Test concurrent token consumption in staging environment"""

    def __init__(self, api_url: str, email: str, password: str):
        self.api_url = api_url.rstrip('/')
        self.email = email
        self.password = password
        self.session = requests.Session()

    def login_and_get_tmp_token(self) -> str:
        """Login and get temporary token for 2FA enrollment"""
        log_info(f"Logging in as {self.email}...")
        
        response = self.session.post(
            f"{self.api_url}/api/auth/v2/login",
            json={"email": self.email, "password": self.password}
        )
        
        if response.status_code != 200:
            log_error(f"Login failed: {response.status_code} {response.text}")
            sys.exit(1)
        
        data = response.json()
        
        if data.get("next_step") != "enroll_2fa":
            log_error(f"Expected next_step=enroll_2fa, got: {data.get('next_step')}")
            log_warning("Make sure test user has 2FA not yet enrolled")
            sys.exit(1)
        
        tmp_token = data.get("tmp_login_token")
        if not tmp_token:
            log_error("No tmp_login_token in response")
            sys.exit(1)
        
        log_success(f"Got temporary token: {tmp_token[:20]}...")
        return tmp_token

    def start_enrollment(self, tmp_token: str) -> Dict[str, Any]:
        """Start 2FA enrollment to get QR code and secret"""
        log_info("Starting 2FA enrollment...")
        
        response = self.session.post(
            f"{self.api_url}/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer {tmp_token}"}
        )
        
        if response.status_code != 200:
            log_error(f"Enrollment start failed: {response.status_code} {response.text}")
            sys.exit(1)
        
        data = response.json()
        log_success("Enrollment started successfully")
        return data

    def verify_enrollment_concurrent(
        self, 
        tmp_token: str, 
        totp_code: str, 
        num_threads: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Attempt to verify enrollment with multiple concurrent requests.
        Only one should succeed due to atomic token consumption.
        """
        log_info(f"Starting {num_threads} concurrent verification requests...")
        
        results = []
        barrier = threading.Barrier(num_threads)
        
        def verify_attempt(thread_id: int):
            """Single verification attempt"""
            barrier.wait()
            
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{self.api_url}/api/auth/v2/2fa/verify-enroll",
                    headers={"Authorization": f"Bearer {tmp_token}"},
                    json={"code": totp_code}
                )
                elapsed = time.time() - start_time
                
                result = {
                    "thread_id": thread_id,
                    "status_code": response.status_code,
                    "elapsed_ms": int(elapsed * 1000),
                    "success": response.status_code == 200,
                    "error": None
                }
                
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        result["error"] = error_data.get("error")
                    except:
                        result["error"] = response.text
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "thread_id": thread_id,
                    "status_code": None,
                    "elapsed_ms": int((time.time() - start_time) * 1000),
                    "success": False,
                    "error": str(e)
                })
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=verify_attempt, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return results

    def analyze_results(self, results: List[Dict[str, Any]]) -> bool:
        """Analyze concurrent test results and return success status"""
        log_info("\n" + "="*60)
        log_info("CONCURRENT TEST RESULTS")
        log_info("="*60)
        
        success_count = sum(1 for r in results if r["success"])
        consumed_count = sum(
            1 for r in results 
            if r.get("error") == "TMP_TOKEN_CONSUMED"
        )
        
        for result in sorted(results, key=lambda x: x["thread_id"]):
            thread_id = result["thread_id"]
            status = result["status_code"]
            elapsed = result["elapsed_ms"]
            
            if result["success"]:
                log_success(
                    f"Thread {thread_id}: SUCCESS (200) in {elapsed}ms"
                )
            elif result.get("error") == "TMP_TOKEN_CONSUMED":
                log_info(
                    f"Thread {thread_id}: CONSUMED (401) in {elapsed}ms - "
                    f"{Colors.GREEN}Expected{Colors.RESET}"
                )
            else:
                log_error(
                    f"Thread {thread_id}: FAILED ({status}) in {elapsed}ms - "
                    f"Error: {result.get('error')}"
                )
        
        log_info("\n" + "-"*60)
        log_info(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
        log_info(f"  Total requests:     {len(results)}")
        log_info(f"  Successful (200):   {success_count}")
        log_info(f"  Consumed (401):     {consumed_count}")
        log_info(f"  Other errors:       {len(results) - success_count - consumed_count}")
        
        test_passed = True
        
        if success_count != 1:
            log_error(
                f"\n✗ FAILED: Expected exactly 1 success, got {success_count}"
            )
            test_passed = False
        else:
            log_success(
                f"\n✓ PASSED: Exactly 1 request succeeded (atomic consumption working)"
            )
        
        if consumed_count != len(results) - 1:
            log_warning(
                f"  Note: Expected {len(results) - 1} TMP_TOKEN_CONSUMED errors, "
                f"got {consumed_count}"
            )
        
        return test_passed


def main():
    """Main test execution"""
    print(f"\n{Colors.BOLD}Staging Concurrent Token Consumption Test{Colors.RESET}\n")
    
    api_url = os.getenv("STAGING_API_URL")
    email = os.getenv("STAGING_TEST_EMAIL")
    password = os.getenv("STAGING_TEST_PASSWORD")
    
    if not all([api_url, email, password]):
        log_error("Missing required environment variables:")
        log_error("  STAGING_API_URL")
        log_error("  STAGING_TEST_EMAIL")
        log_error("  STAGING_TEST_PASSWORD")
        sys.exit(1)
    
    log_info(f"Testing against: {api_url}")
    log_info(f"Test user: {email}\n")
    
    test = StagingConcurrentTest(api_url, email, password)
    
    try:
        tmp_token = test.login_and_get_tmp_token()
        
        enrollment_data = test.start_enrollment(tmp_token)
        
        log_warning(
            "\nNOTE: In a real test, you would scan the QR code with an authenticator app."
        )
        log_warning(
            "For this test, you need to provide a valid TOTP code manually."
        )
        
        totp_code = input(f"\n{Colors.YELLOW}Enter TOTP code from authenticator app: {Colors.RESET}")
        
        if not totp_code or len(totp_code) != 6 or not totp_code.isdigit():
            log_error("Invalid TOTP code format (must be 6 digits)")
            sys.exit(1)
        
        results = test.verify_enrollment_concurrent(tmp_token, totp_code, num_threads=5)
        
        test_passed = test.analyze_results(results)
        
        if test_passed:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ TEST PASSED{Colors.RESET}")
            print(f"{Colors.GREEN}Atomic token consumption is working correctly!{Colors.RESET}\n")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ TEST FAILED{Colors.RESET}")
            print(f"{Colors.RED}Atomic token consumption may not be working correctly.{Colors.RESET}\n")
            sys.exit(1)
    
    except KeyboardInterrupt:
        log_warning("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        log_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
