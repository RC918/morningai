#!/usr/bin/env python3
"""
Backend API Testing Script - Tests all critical endpoints after RLS deployment
Tests with service_role authentication to ensure RLS policies work correctly
"""

import os
import sys
import requests
import json
from datetime import datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://morningai-backend-v2.onrender.com')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)


class APITester:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def test_supabase_table_access(self, table_name, operation='select'):
        """Test direct Supabase table access with service_role"""
        print(f"\nTesting {table_name} ({operation})...")

        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json'
        }

        try:
            if operation == 'select':
                response = requests.get(
                    f'{SUPABASE_URL}/rest/v1/{table_name}?limit=1',
                    headers=headers,
                    timeout=10
                )
            elif operation == 'insert':
                test_data = self._get_test_data(table_name)
                response = requests.post(
                    f'{SUPABASE_URL}/rest/v1/{table_name}',
                    headers=headers,
                    json=test_data,
                    timeout=10
                )

            if response.status_code in [200, 201]:
                print(f"  ✅ {table_name} {operation}: SUCCESS (status {response.status_code})")
                self.results.append({
                    'test': f'{table_name}_{operation}',
                    'status': 'PASS',
                    'status_code': response.status_code,
                    'message': 'Service role can access table'
                })
                self.passed += 1
                return True
            elif response.status_code == 401:
                print(f"  ❌ {table_name} {operation}: FAILED - 401 Unauthorized")
                print("     This indicates RLS is blocking service_role access!")
                self.results.append({
                    'test': f'{table_name}_{operation}',
                    'status': 'FAIL',
                    'status_code': 401,
                    'message': 'RLS blocking service_role - CRITICAL',
                    'response': response.text[:200]
                })
                self.failed += 1
                return False
            else:
                print(f"  ⚠️  {table_name} {operation}: Unexpected status {response.status_code}")
                self.results.append({
                    'test': f'{table_name}_{operation}',
                    'status': 'WARN',
                    'status_code': response.status_code,
                    'message': 'Unexpected status code',
                    'response': response.text[:200]
                })
                self.failed += 1
                return False

        except Exception as e:
            print(f"  ❌ {table_name} {operation}: ERROR - {str(e)}")
            self.results.append({
                'test': f'{table_name}_{operation}',
                'status': 'ERROR',
                'message': str(e)
            })
            self.failed += 1
            return False

    def test_backend_endpoint(self, endpoint, method='GET', data=None):
        """Test backend API endpoint"""
        print(f"\nTesting backend endpoint: {method} {endpoint}...")

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            url = f'{BACKEND_URL}{endpoint}'

            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code in [200, 201, 202]:
                print(f"  ✅ {endpoint}: SUCCESS (status {response.status_code})")
                self.results.append({
                    'test': f'backend_{endpoint}',
                    'status': 'PASS',
                    'status_code': response.status_code,
                    'message': 'Backend endpoint accessible'
                })
                self.passed += 1
                return True
            elif response.status_code == 401:
                print(f"  ❌ {endpoint}: FAILED - 401 Unauthorized")
                self.results.append({
                    'test': f'backend_{endpoint}',
                    'status': 'FAIL',
                    'status_code': 401,
                    'message': 'Backend endpoint returning 401',
                    'response': response.text[:200]
                })
                self.failed += 1
                return False
            else:
                print(f"  ⚠️  {endpoint}: Status {response.status_code}")
                self.results.append({
                    'test': f'backend_{endpoint}',
                    'status': 'WARN',
                    'status_code': response.status_code,
                    'response': response.text[:200]
                })
                return True

        except Exception as e:
            print(f"  ❌ {endpoint}: ERROR - {str(e)}")
            self.results.append({
                'test': f'backend_{endpoint}',
                'status': 'ERROR',
                'message': str(e)
            })
            self.failed += 1
            return False

    def _get_test_data(self, table_name):
        """Get test data for insert operations"""
        test_data = {
            'faqs': {
                'question': 'Test question for RLS validation',
                'answer': 'Test answer',
                'category': 'test'
            },
            'alerts': {
                'alert_type': 'test',
                'severity': 'low',
                'message': 'Test alert for RLS validation',
                'status': 'active'
            }
        }
        return test_data.get(table_name, {})

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 80)
        print("BACKEND API TEST REPORT")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print()

        if self.failed > 0:
            print("FAILED TESTS:")
            for result in self.results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  ❌ {result['test']}: {result['message']}")
                    if 'response' in result:
                        print(f"     Response: {result['response']}")

        report_file = f'/tmp/backend_api_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': self.passed + self.failed,
                'passed': self.passed,
                'failed': self.failed,
                'results': self.results
            }, f, indent=2)

        print(f"\nFull report saved to: {report_file}")

        if self.failed > 0:
            print("\n⚠️  WARNING: Some tests failed! Review the report above.")
            return False
        else:
            print("\n✅ SUCCESS: All backend API tests passed!")
            return True


def main():
    print("=" * 80)
    print("Backend API Testing - Post RLS Deployment")
    print("=" * 80)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Backend URL: {BACKEND_URL}")
    print()

    tester = APITester()

    print("Testing Supabase Tables with service_role...")
    print("-" * 80)

    tables_to_test = [
        'faqs',
        'faq_search_history',
        'faq_categories',
        'embeddings',
        'vector_queries',
        'trace_metrics',
        'alerts',
        'agent_reputation',
        'reputation_events'
    ]

    for table in tables_to_test:
        tester.test_supabase_table_access(table, 'select')

    print("\n\nTesting Backend API Endpoints...")
    print("-" * 80)

    tester.test_backend_endpoint('/healthz')
    tester.test_backend_endpoint('/api/agent/faq', 'POST', {
        'question': 'Test question',
        'context': 'Test context'
    })

    success = tester.generate_report()
    sys.exit(0 if success else 1)

if __name__ == '__main__':

    main()
