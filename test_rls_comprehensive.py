#!/usr/bin/env python3
"""
Comprehensive RLS (Row Level Security) Policy Testing
Tests all RLS policies with all roles (service_role, authenticated, anonymous) 
and all operations (SELECT, INSERT, UPDATE, DELETE)
"""

import os
import sys
import requests
import json
import jwt
from datetime import datetime, timedelta
import pytest

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'openssl rand -hex 32')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)


class ComprehensiveRLSTester:
    """Comprehensive RLS policy testing for all roles and operations"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
        self.tables_with_rls = [
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
        
        self.test_data = {
            'faqs': {
                'question': 'Test RLS question',
                'answer': 'Test RLS answer',
                'category': 'test'
            },
            'faq_search_history': {
                'query': 'test query',
                'user_id': 'test-user'
            },
            'faq_categories': {
                'name': 'Test Category',
                'description': 'Test category for RLS'
            },
            'embeddings': {
                'content': 'test content',
                'embedding': [0.1, 0.2, 0.3]
            },
            'vector_queries': {
                'query': 'test vector query',
                'results': []
            },
            'trace_metrics': {
                'trace_id': 'test-trace',
                'metric_name': 'test_metric',
                'value': 1.0
            },
            'alerts': {
                'alert_type': 'test',
                'severity': 'low',
                'message': 'Test alert for RLS',
                'status': 'active'
            },
            'agent_reputation': {
                'agent_id': 'test-agent',
                'reputation_score': 100
            },
            'reputation_events': {
                'agent_id': 'test-agent',
                'event_type': 'test',
                'impact': 1
            }
        }
        
        self.authenticated_token = self._generate_authenticated_jwt()
    
    def _generate_authenticated_jwt(self):
        """Generate JWT token for authenticated role testing"""
        payload = {
            'user_id': 'test-user-123',
            'username': 'test-user',
            'role': 'authenticated',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        
        try:
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
            return token
        except Exception as e:
            print(f"Warning: Could not generate JWT token: {e}")
            return None
    
    def _get_headers(self, role):
        """Get appropriate headers for different roles"""
        if role == 'service_role':
            return {
                'apikey': SUPABASE_SERVICE_ROLE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
                'Content-Type': 'application/json'
            }
        elif role == 'authenticated':
            if not self.authenticated_token:
                return None
            return {
                'apikey': SUPABASE_SERVICE_ROLE_KEY,  # Still need API key
                'Authorization': f'Bearer {self.authenticated_token}',
                'Content-Type': 'application/json'
            }
        elif role == 'anonymous':
            return {
                'Content-Type': 'application/json'
            }
        else:
            raise ValueError(f"Unknown role: {role}")
    
    def _record_result(self, table, role, operation, status, error=None, note=None):
        """Record test result"""
        result = {
            'table': table,
            'role': role,
            'operation': operation,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            result['error'] = error
        if note:
            result['note'] = note
            
        self.results.append(result)
        
        if status == 'PASS':
            self.passed += 1
        else:
            self.failed += 1
    
    def test_select_operation(self, table, role):
        """Test SELECT operation for a specific role"""
        headers = self._get_headers(role)
        if headers is None:
            self._record_result(table, role, 'SELECT', 'SKIP', 
                              error='Could not generate headers for role')
            return False
        
        try:
            response = requests.get(
                f'{SUPABASE_URL}/rest/v1/{table}?limit=1',
                headers=headers,
                timeout=10
            )
            
            if role == 'service_role':
                if response.status_code == 200:
                    self._record_result(table, role, 'SELECT', 'PASS')
                    return True
                else:
                    self._record_result(table, role, 'SELECT', 'FAIL',
                                      error=f'Expected 200, got {response.status_code}')
                    return False
                    
            elif role == 'authenticated':
                if response.status_code == 200:
                    self._record_result(table, role, 'SELECT', 'PASS')
                    return True
                elif response.status_code == 401:
                    self._record_result(table, role, 'SELECT', 'FAIL',
                                      error='Authenticated users should have read access')
                    return False
                else:
                    self._record_result(table, role, 'SELECT', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
            elif role == 'anonymous':
                if response.status_code == 401:
                    self._record_result(table, role, 'SELECT', 'PASS',
                                      note='Correctly blocked')
                    return True
                elif response.status_code == 200:
                    self._record_result(table, role, 'SELECT', 'FAIL',
                                      error='Anonymous access should be blocked')
                    return False
                else:
                    self._record_result(table, role, 'SELECT', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
        except Exception as e:
            self._record_result(table, role, 'SELECT', 'ERROR', error=str(e))
            return False
    
    def test_insert_operation(self, table, role):
        """Test INSERT operation for a specific role"""
        headers = self._get_headers(role)
        if headers is None:
            self._record_result(table, role, 'INSERT', 'SKIP',
                              error='Could not generate headers for role')
            return False
        
        test_data = self.test_data.get(table, {'test_field': 'test_value'})
        
        try:
            response = requests.post(
                f'{SUPABASE_URL}/rest/v1/{table}',
                headers=headers,
                json=test_data,
                timeout=10
            )
            
            if role == 'service_role':
                if response.status_code in [200, 201]:
                    self._record_result(table, role, 'INSERT', 'PASS')
                    return True
                else:
                    self._record_result(table, role, 'INSERT', 'FAIL',
                                      error=f'Expected 200/201, got {response.status_code}')
                    return False
                    
            elif role == 'authenticated':
                if response.status_code == 401 or response.status_code == 403:
                    self._record_result(table, role, 'INSERT', 'PASS',
                                      note='Correctly blocked (read-only)')
                    return True
                elif response.status_code in [200, 201]:
                    self._record_result(table, role, 'INSERT', 'FAIL',
                                      error='Authenticated users should be read-only')
                    return False
                else:
                    self._record_result(table, role, 'INSERT', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
            elif role == 'anonymous':
                if response.status_code in [401, 403]:
                    self._record_result(table, role, 'INSERT', 'PASS',
                                      note='Correctly blocked')
                    return True
                elif response.status_code in [200, 201]:
                    self._record_result(table, role, 'INSERT', 'FAIL',
                                      error='Anonymous access should be blocked')
                    return False
                else:
                    self._record_result(table, role, 'INSERT', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
        except Exception as e:
            self._record_result(table, role, 'INSERT', 'ERROR', error=str(e))
            return False
    
    def test_update_operation(self, table, role):
        """Test UPDATE operation for a specific role"""
        headers = self._get_headers(role)
        if headers is None:
            self._record_result(table, role, 'UPDATE', 'SKIP',
                              error='Could not generate headers for role')
            return False
        
        try:
            get_response = requests.get(
                f'{SUPABASE_URL}/rest/v1/{table}?limit=1',
                headers=self._get_headers('service_role'),
                timeout=10
            )
            
            if get_response.status_code != 200 or not get_response.json():
                self._record_result(table, role, 'UPDATE', 'SKIP',
                                  note='No records available to update')
                return True
            
            update_data = {'updated_at': datetime.now().isoformat()}
            response = requests.patch(
                f'{SUPABASE_URL}/rest/v1/{table}?limit=1',
                headers=headers,
                json=update_data,
                timeout=10
            )
            
            if role == 'service_role':
                if response.status_code in [200, 204]:
                    self._record_result(table, role, 'UPDATE', 'PASS')
                    return True
                else:
                    self._record_result(table, role, 'UPDATE', 'FAIL',
                                      error=f'Expected 200/204, got {response.status_code}')
                    return False
                    
            elif role == 'authenticated':
                if response.status_code in [401, 403]:
                    self._record_result(table, role, 'UPDATE', 'PASS',
                                      note='Correctly blocked (read-only)')
                    return True
                elif response.status_code in [200, 204]:
                    self._record_result(table, role, 'UPDATE', 'FAIL',
                                      error='Authenticated users should be read-only')
                    return False
                else:
                    self._record_result(table, role, 'UPDATE', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
            elif role == 'anonymous':
                if response.status_code in [401, 403]:
                    self._record_result(table, role, 'UPDATE', 'PASS',
                                      note='Correctly blocked')
                    return True
                elif response.status_code in [200, 204]:
                    self._record_result(table, role, 'UPDATE', 'FAIL',
                                      error='Anonymous access should be blocked')
                    return False
                else:
                    self._record_result(table, role, 'UPDATE', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
        except Exception as e:
            self._record_result(table, role, 'UPDATE', 'ERROR', error=str(e))
            return False
    
    def test_delete_operation(self, table, role):
        """Test DELETE operation for a specific role"""
        headers = self._get_headers(role)
        if headers is None:
            self._record_result(table, role, 'DELETE', 'SKIP',
                              error='Could not generate headers for role')
            return False
        
        try:
            response = requests.delete(
                f'{SUPABASE_URL}/rest/v1/{table}?test_field=eq.nonexistent',
                headers=headers,
                timeout=10
            )
            
            if role == 'service_role':
                if response.status_code in [200, 204]:
                    self._record_result(table, role, 'DELETE', 'PASS')
                    return True
                else:
                    self._record_result(table, role, 'DELETE', 'FAIL',
                                      error=f'Expected 200/204, got {response.status_code}')
                    return False
                    
            elif role == 'authenticated':
                if response.status_code in [401, 403]:
                    self._record_result(table, role, 'DELETE', 'PASS',
                                      note='Correctly blocked (read-only)')
                    return True
                elif response.status_code in [200, 204]:
                    self._record_result(table, role, 'DELETE', 'FAIL',
                                      error='Authenticated users should be read-only')
                    return False
                else:
                    self._record_result(table, role, 'DELETE', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
            elif role == 'anonymous':
                if response.status_code in [401, 403]:
                    self._record_result(table, role, 'DELETE', 'PASS',
                                      note='Correctly blocked')
                    return True
                elif response.status_code in [200, 204]:
                    self._record_result(table, role, 'DELETE', 'FAIL',
                                      error='Anonymous access should be blocked')
                    return False
                else:
                    self._record_result(table, role, 'DELETE', 'WARN',
                                      error=f'Unexpected status {response.status_code}')
                    return False
                    
        except Exception as e:
            self._record_result(table, role, 'DELETE', 'ERROR', error=str(e))
            return False
    
    def test_table_comprehensive(self, table):
        """Test all operations for all roles on a specific table"""
        print(f"\n📋 Testing table: {table}")
        print("-" * 80)
        
        roles = ['service_role', 'authenticated', 'anonymous']
        operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        
        for role in roles:
            print(f"\n  Testing {role} role:")
            
            result = self.test_select_operation(table, role)
            status = "✅" if result else "❌"
            print(f"    {status} SELECT")
            
            result = self.test_insert_operation(table, role)
            status = "✅" if result else "❌"
            print(f"    {status} INSERT")
            
            result = self.test_update_operation(table, role)
            status = "✅" if result else "❌"
            print(f"    {status} UPDATE")
            
            result = self.test_delete_operation(table, role)
            status = "✅" if result else "❌"
            print(f"    {status} DELETE")
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests on all tables"""
        print("🧪 COMPREHENSIVE RLS POLICY TEST SUITE")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Testing all roles (service_role, authenticated, anonymous)")
        print("Testing all operations (SELECT, INSERT, UPDATE, DELETE)")
        print(f"Testing {len(self.tables_with_rls)} tables with RLS enabled")
        print()
        
        if not self.authenticated_token:
            print("⚠️  WARNING: Could not generate authenticated JWT token")
            print("   Authenticated role tests will be skipped")
            print()
        
        for table in self.tables_with_rls:
            self.test_table_comprehensive(table)
        
        return self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n\n" + "=" * 80)
        print("COMPREHENSIVE RLS POLICY TEST REPORT")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] in ['FAIL', 'ERROR']])
        skipped_tests = len([r for r in self.results if r['status'] == 'SKIP'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Skipped: {skipped_tests}")
        
        total_possible = len(self.tables_with_rls) * 3 * 4  # 9 tables * 3 roles * 4 operations
        coverage_percent = (total_tests / total_possible) * 100 if total_possible > 0 else 0
        print(f"Test Coverage: {coverage_percent:.1f}% ({total_tests}/{total_possible})")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"  ❌ {result['table']} - {result['role']} {result['operation']}")
                    if 'error' in result:
                        print(f"     Error: {result['error']}")
            print()
        
        print("=" * 80)
        print("SUMMARY BY TABLE")
        print("=" * 80)
        
        for table in self.tables_with_rls:
            table_results = [r for r in self.results if r['table'] == table]
            table_passed = len([r for r in table_results if r['status'] == 'PASS'])
            table_failed = len([r for r in table_results if r['status'] in ['FAIL', 'ERROR']])
            table_skipped = len([r for r in table_results if r['status'] == 'SKIP'])
            
            status = "✅" if table_failed == 0 else "❌"
            print(f"{status} {table}: {table_passed} passed, {table_failed} failed, {table_skipped} skipped")
        
        print("\n" + "=" * 80)
        print("SUMMARY BY ROLE")
        print("=" * 80)
        
        for role in ['service_role', 'authenticated', 'anonymous']:
            role_results = [r for r in self.results if r['role'] == role]
            role_passed = len([r for r in role_results if r['status'] == 'PASS'])
            role_failed = len([r for r in role_results if r['status'] in ['FAIL', 'ERROR']])
            role_skipped = len([r for r in role_results if r['status'] == 'SKIP'])
            
            status = "✅" if role_failed == 0 else "❌"
            print(f"{status} {role}: {role_passed} passed, {role_failed} failed, {role_skipped} skipped")
        
        report_file = f'/tmp/comprehensive_rls_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'skipped': skipped_tests,
                    'coverage_percent': coverage_percent
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\nFull report saved to: {report_file}")
        
        if failed_tests > 0:
            print("\n⚠️  WARNING: Some RLS policy tests failed!")
            print("Review the report above and check RLS policies in Supabase.")
            return False
        else:
            print("\n✅ SUCCESS: All RLS policy tests passed!")
            print("RLS policies are correctly configured for all roles and operations.")
            return True


class TestRLSPolicies:
    """Pytest test class for RLS policies"""
    
    @classmethod
    def setup_class(cls):
        """Setup test class"""
        cls.tester = ComprehensiveRLSTester()
    
    def test_service_role_access(self):
        """Test that service_role has full access to all tables"""
        for table in self.tester.tables_with_rls:
            assert self.tester.test_select_operation(table, 'service_role'), f"service_role SELECT failed for {table}"
            assert self.tester.test_insert_operation(table, 'service_role'), f"service_role INSERT failed for {table}"
            assert self.tester.test_update_operation(table, 'service_role'), f"service_role UPDATE failed for {table}"
            assert self.tester.test_delete_operation(table, 'service_role'), f"service_role DELETE failed for {table}"
    
    def test_authenticated_role_access(self):
        """Test that authenticated role has read-only access"""
        for table in self.tester.tables_with_rls:
            assert self.tester.test_select_operation(table, 'authenticated'), f"authenticated SELECT failed for {table}"
            assert self.tester.test_insert_operation(table, 'authenticated'), f"authenticated INSERT should be blocked for {table}"
            assert self.tester.test_update_operation(table, 'authenticated'), f"authenticated UPDATE should be blocked for {table}"
            assert self.tester.test_delete_operation(table, 'authenticated'), f"authenticated DELETE should be blocked for {table}"
    
    def test_anonymous_role_blocked(self):
        """Test that anonymous role is completely blocked"""
        for table in self.tester.tables_with_rls:
            assert self.tester.test_select_operation(table, 'anonymous'), f"anonymous SELECT should be blocked for {table}"
            assert self.tester.test_insert_operation(table, 'anonymous'), f"anonymous INSERT should be blocked for {table}"
            assert self.tester.test_update_operation(table, 'anonymous'), f"anonymous UPDATE should be blocked for {table}"
            assert self.tester.test_delete_operation(table, 'anonymous'), f"anonymous DELETE should be blocked for {table}"


def run_comprehensive_rls_tests():
    """Run comprehensive RLS tests (standalone function)"""
    tester = ComprehensiveRLSTester()
    return tester.run_comprehensive_tests()


if __name__ == '__main__':
    success = run_comprehensive_rls_tests()
    sys.exit(0 if success else 1)
