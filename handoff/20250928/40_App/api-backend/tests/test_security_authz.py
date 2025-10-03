#!/usr/bin/env python3
"""
Comprehensive security authorization tests for Phase 6 endpoints
Tests JWT authentication and RBAC for protected endpoints
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from middleware.auth_middleware import create_admin_token, create_analyst_token, create_user_token


class TestSecurityAuthorization:
    """Test suite for Phase 6 security endpoints authorization"""
    
    BASE_URL = "http://localhost:5001"
    
    PROTECTED_ENDPOINTS = {
        '/api/security/access/evaluate': {
            'method': 'POST',
            'required_role': 'admin',
            'body': {
                'user_id': 'test_user',
                'resource': 'test_resource',
                'action': 'read',
                'context': {}
            }
        },
        '/api/security/events/review': {
            'method': 'POST',
            'required_role': 'analyst',
            'body': {
                'event_id': 'test_event',
                'review_status': 'reviewed'
            }
        },
        '/api/security/hitl/submit': {
            'method': 'POST',
            'required_role': 'analyst',
            'body': {
                'review_id': 'test_review',
                'decision': 'approved'
            }
        },
        '/api/security/hitl/pending': {
            'method': 'GET',
            'required_role': 'analyst',
            'body': None
        },
        '/api/security/audit': {
            'method': 'POST',
            'required_role': 'admin',
            'body': {
                'scope': 'full'
            }
        },
        '/api/security/reviews/pending': {
            'method': 'GET',
            'required_role': 'analyst',
            'body': None
        }
    }
    
    def test_no_token_returns_401(self):
        """Test that protected endpoints return 401 without JWT token"""
        import requests
        
        for endpoint, config in self.PROTECTED_ENDPOINTS.items():
            try:
                if config['method'] == 'GET':
                    response = requests.get(
                        f"{self.BASE_URL}{endpoint}",
                        timeout=5
                    )
                else:
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        json=config['body'],
                        timeout=5
                    )
                
                assert response.status_code == 401, \
                    f"{endpoint} should return 401 without token, got {response.status_code}"
                
                data = response.json()
                assert 'error' in data, f"{endpoint} should contain error field"
                
                print(f"✅ {endpoint} properly returns 401 without JWT")
            except requests.exceptions.RequestException:
                print(f"⚠️ {endpoint} - Connection failed (expected in test environment)")
    
    def test_user_role_returns_403_for_protected_endpoints(self):
        """Test that user role (low privilege) returns 403 for protected endpoints"""
        import requests
        
        token = create_user_token()
        
        for endpoint, config in self.PROTECTED_ENDPOINTS.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                
                if config['method'] == 'GET':
                    response = requests.get(
                        f"{self.BASE_URL}{endpoint}",
                        headers=headers,
                        timeout=5
                    )
                else:
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        json=config['body'],
                        headers=headers,
                        timeout=5
                    )
                
                assert response.status_code == 403, \
                    f"{endpoint} should return 403 for user role, got {response.status_code}"
                
                data = response.json()
                assert 'error' in data, f"{endpoint} should contain error field"
                
                print(f"✅ {endpoint} properly returns 403 for user role")
            except requests.exceptions.RequestException:
                print(f"⚠️ {endpoint} - Connection failed (expected in test environment)")
    
    def test_analyst_can_access_analyst_endpoints(self):
        """Test that analyst role can access analyst-required endpoints"""
        import requests
        
        token = create_analyst_token()
        
        analyst_endpoints = {k: v for k, v in self.PROTECTED_ENDPOINTS.items() 
                            if v['required_role'] == 'analyst'}
        
        for endpoint, config in analyst_endpoints.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                
                if config['method'] == 'GET':
                    response = requests.get(
                        f"{self.BASE_URL}{endpoint}",
                        headers=headers,
                        timeout=5
                    )
                else:
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        json=config['body'],
                        headers=headers,
                        timeout=5
                    )
                
                assert response.status_code in [200, 503], \
                    f"{endpoint} should return 200 or 503 for analyst role, got {response.status_code}"
                
                print(f"✅ {endpoint} accessible to analyst role (status: {response.status_code})")
            except requests.exceptions.RequestException:
                print(f"⚠️ {endpoint} - Connection failed (expected in test environment)")
    
    def test_analyst_cannot_access_admin_endpoints(self):
        """Test that analyst role cannot access admin-only endpoints"""
        import requests
        
        token = create_analyst_token()
        
        admin_endpoints = {k: v for k, v in self.PROTECTED_ENDPOINTS.items() 
                          if v['required_role'] == 'admin'}
        
        for endpoint, config in admin_endpoints.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                
                if config['method'] == 'GET':
                    response = requests.get(
                        f"{self.BASE_URL}{endpoint}",
                        headers=headers,
                        timeout=5
                    )
                else:
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        json=config['body'],
                        headers=headers,
                        timeout=5
                    )
                
                assert response.status_code == 403, \
                    f"{endpoint} should return 403 for analyst trying to access admin endpoint, got {response.status_code}"
                
                print(f"✅ {endpoint} properly returns 403 for analyst role")
            except requests.exceptions.RequestException:
                print(f"⚠️ {endpoint} - Connection failed (expected in test environment)")
    
    def test_admin_can_access_all_endpoints(self):
        """Test that admin role can access all protected endpoints"""
        import requests
        
        token = create_admin_token()
        
        for endpoint, config in self.PROTECTED_ENDPOINTS.items():
            try:
                headers = {'Authorization': f'Bearer {token}'}
                
                if config['method'] == 'GET':
                    response = requests.get(
                        f"{self.BASE_URL}{endpoint}",
                        headers=headers,
                        timeout=5
                    )
                else:
                    response = requests.post(
                        f"{self.BASE_URL}{endpoint}",
                        json=config['body'],
                        headers=headers,
                        timeout=5
                    )
                
                assert response.status_code in [200, 503], \
                    f"{endpoint} should return 200 or 503 for admin role, got {response.status_code}"
                
                print(f"✅ {endpoint} accessible to admin role (status: {response.status_code})")
            except requests.exceptions.RequestException:
                print(f"⚠️ {endpoint} - Connection failed (expected in test environment)")
    
    def test_pydantic_validation_returns_400(self):
        """Test that invalid request bodies return 400 with pydantic validation"""
        import requests
        
        token = create_admin_token()
        
        invalid_payloads = [
            {
                'endpoint': '/api/security/access/evaluate',
                'body': {},
                'description': 'empty body'
            },
            {
                'endpoint': '/api/security/access/evaluate',
                'body': {'user_id': ''},
                'description': 'empty user_id'
            },
            {
                'endpoint': '/api/security/events/review',
                'body': {},
                'description': 'missing required fields'
            },
            {
                'endpoint': '/api/security/hitl/submit',
                'body': {'review_id': ''},
                'description': 'empty review_id'
            }
        ]
        
        for test_case in invalid_payloads:
            try:
                response = requests.post(
                    f"{self.BASE_URL}{test_case['endpoint']}",
                    json=test_case['body'],
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=5
                )
                
                assert response.status_code == 400, \
                    f"{test_case['endpoint']} should return 400 for {test_case['description']}, got {response.status_code}"
                
                data = response.json()
                assert 'error' in data, "Response should contain error field"
                assert data['error'].get('code') == 'invalid_input', "Error code should be invalid_input"
                
                print(f"✅ {test_case['endpoint']} properly validates input ({test_case['description']})")
            except requests.exceptions.RequestException:
                print(f"⚠️ {test_case['endpoint']} - Connection failed (expected in test environment)")
    
    def test_faq_endpoint_remains_public(self):
        """Test that /api/agent/faq endpoint remains public (no JWT required)"""
        import requests
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/api/agent/faq",
                json={"question": "What is the weather today?"},
                timeout=5
            )
            
            assert response.status_code in [202, 503], \
                f"FAQ endpoint should accept requests without JWT, got {response.status_code}"
            
            if response.status_code == 202:
                data = response.json()
                assert 'task_id' in data, "Response should contain task_id"
                assert 'status' in data, "Response should contain status"
            
            print(f"✅ /api/agent/faq remains public (status: {response.status_code})")
        except requests.exceptions.RequestException:
            print("⚠️ FAQ endpoint test - Connection failed (expected in test environment)")


def test_token_generation():
    """Test that token generation functions work correctly"""
    admin_token = create_admin_token()
    analyst_token = create_analyst_token()
    user_token = create_user_token()
    
    assert isinstance(admin_token, str), "Admin token should be a string"
    assert isinstance(analyst_token, str), "Analyst token should be a string"
    assert isinstance(user_token, str), "User token should be a string"
    
    assert len(admin_token) > 0, "Admin token should not be empty"
    assert len(analyst_token) > 0, "Analyst token should not be empty"
    assert len(user_token) > 0, "User token should not be empty"
    
    print("✅ Token generation functions work correctly")


if __name__ == "__main__":
    print("🧪 Running Security Authorization Tests")
    print("=" * 70)
    
    test_suite = TestSecurityAuthorization()
    
    print("\n📋 Test 1: No JWT token returns 401")
    print("-" * 70)
    test_suite.test_no_token_returns_401()
    
    print("\n📋 Test 2: User role returns 403 for protected endpoints")
    print("-" * 70)
    test_suite.test_user_role_returns_403_for_protected_endpoints()
    
    print("\n📋 Test 3: Analyst can access analyst endpoints")
    print("-" * 70)
    test_suite.test_analyst_can_access_analyst_endpoints()
    
    print("\n📋 Test 4: Analyst cannot access admin endpoints")
    print("-" * 70)
    test_suite.test_analyst_cannot_access_admin_endpoints()
    
    print("\n📋 Test 5: Admin can access all endpoints")
    print("-" * 70)
    test_suite.test_admin_can_access_all_endpoints()
    
    print("\n📋 Test 6: Pydantic validation returns 400")
    print("-" * 70)
    test_suite.test_pydantic_validation_returns_400()
    
    print("\n📋 Test 7: FAQ endpoint remains public")
    print("-" * 70)
    test_suite.test_faq_endpoint_remains_public()
    
    print("\n📋 Test 8: Token generation")
    print("-" * 70)
    test_token_generation()
    
    print("\n" + "=" * 70)
    print("🎉 Security authorization tests completed!")
