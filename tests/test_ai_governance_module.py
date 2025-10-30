#!/usr/bin/env python3
"""
Comprehensive tests for ai_governance_module.py
Tests AI governance rules, permissions, and multi-tenant access control
"""
import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_governance_module import (
    UserRole, GovernanceRuleType, GovernanceRule, User,
    PermissionManager, GovernanceRuleManager, AIGovernanceModule
)


class TestUserRole:
    """Test UserRole enum"""
    
    def test_user_role_values(self):
        """Test UserRole enum values"""
        assert UserRole.PLATFORM_ADMIN.value == "platform_admin"
        assert UserRole.TENANT_ADMIN.value == "tenant_admin"
        assert UserRole.TENANT_USER.value == "tenant_user"


class TestGovernanceRuleType:
    """Test GovernanceRuleType enum"""
    
    def test_governance_rule_type_values(self):
        """Test GovernanceRuleType enum values"""
        assert GovernanceRuleType.BLACKLIST.value == "blacklist"
        assert GovernanceRuleType.WHITELIST.value == "whitelist"
        assert GovernanceRuleType.CONTENT_FILTER.value == "content_filter"
        assert GovernanceRuleType.USAGE_LIMIT.value == "usage_limit"


class TestGovernanceRule:
    """Test GovernanceRule dataclass"""
    
    def test_governance_rule_creation(self):
        """Test creating a governance rule"""
        rule = GovernanceRule(
            rule_id="test_rule_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Test Blacklist",
            description="Test blacklist rule",
            config={"domains": ["example.com"]}
        )
        
        assert rule.rule_id == "test_rule_1"
        assert rule.rule_type == GovernanceRuleType.BLACKLIST
        assert rule.name == "Test Blacklist"
        assert rule.enabled is True
        assert rule.created_at is not None
        assert rule.updated_at is not None
    
    def test_governance_rule_with_timestamps(self):
        """Test governance rule with custom timestamps"""
        now = datetime.now()
        rule = GovernanceRule(
            rule_id="test_rule_2",
            rule_type=GovernanceRuleType.WHITELIST,
            name="Test Whitelist",
            description="Test whitelist rule",
            config={"domains": ["trusted.com"]},
            enabled=False,
            created_at=now,
            updated_at=now
        )
        
        assert rule.created_at == now
        assert rule.updated_at == now
        assert rule.enabled is False


class TestUser:
    """Test User dataclass"""
    
    def test_platform_admin_permissions(self):
        """Test platform admin default permissions"""
        user = User(
            user_id="admin_1",
            username="admin",
            email="admin@test.com",
            role=UserRole.PLATFORM_ADMIN
        )
        
        assert 'manage_all_tenants' in user.permissions
        assert 'manage_system_settings' in user.permissions
        assert 'view_all_governance_rules' in user.permissions
        assert 'manage_all_governance_rules' in user.permissions
        assert user.created_at is not None
    
    def test_tenant_admin_permissions(self):
        """Test tenant admin default permissions"""
        user = User(
            user_id="tenant_admin_1",
            username="tenant_admin",
            email="admin@tenant.com",
            role=UserRole.TENANT_ADMIN,
            tenant_id="tenant_1"
        )
        
        assert 'manage_tenant_settings' in user.permissions
        assert 'view_tenant_governance_rules' in user.permissions
        assert 'manage_tenant_governance_rules' in user.permissions
        assert 'manage_tenant_users' in user.permissions
        assert user.tenant_id == "tenant_1"
    
    def test_tenant_user_permissions(self):
        """Test tenant user default permissions"""
        user = User(
            user_id="user_1",
            username="user",
            email="user@tenant.com",
            role=UserRole.TENANT_USER,
            tenant_id="tenant_1"
        )
        
        assert 'use_ai_features' in user.permissions
        assert 'view_own_usage' in user.permissions
        assert 'view_tenant_governance_rules' in user.permissions
        assert len(user.permissions) == 3


class TestPermissionManager:
    """Test PermissionManager class"""
    
    def test_create_user(self):
        """Test creating a user"""
        pm = PermissionManager()
        user = pm.create_user(
            username="testuser",
            email="test@example.com",
            role=UserRole.TENANT_USER,
            tenant_id="tenant_1"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.TENANT_USER
        assert user.tenant_id == "tenant_1"
        assert user.user_id in pm.users
    
    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        pm = PermissionManager()
        user = pm.create_user(
            username="testuser",
            email="test@example.com",
            role=UserRole.TENANT_USER
        )
        
        session_token = pm.authenticate_user("testuser", "password")
        assert session_token is not None
        assert session_token in pm.sessions
        assert user.last_login is not None
    
    def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        pm = PermissionManager()
        session_token = pm.authenticate_user("nonexistent", "password")
        assert session_token is None
    
    def test_get_user_from_session(self):
        """Test getting user from session token"""
        pm = PermissionManager()
        user = pm.create_user(
            username="testuser",
            email="test@example.com",
            role=UserRole.TENANT_USER
        )
        
        session_token = pm.authenticate_user("testuser", "password")
        retrieved_user = pm.get_user_from_session(session_token)
        
        assert retrieved_user is not None
        assert retrieved_user.user_id == user.user_id
    
    def test_get_user_from_invalid_session(self):
        """Test getting user from invalid session token"""
        pm = PermissionManager()
        user = pm.get_user_from_session("invalid_token")
        assert user is None
    
    def test_check_permission(self):
        """Test checking user permissions"""
        pm = PermissionManager()
        user = pm.create_user(
            username="admin",
            email="admin@example.com",
            role=UserRole.PLATFORM_ADMIN
        )
        
        assert pm.check_permission(user, 'manage_all_tenants') is True
        assert pm.check_permission(user, 'nonexistent_permission') is False
    
    def test_get_accessible_tenants_platform_admin(self):
        """Test getting accessible tenants for platform admin"""
        pm = PermissionManager()
        admin = pm.create_user(
            username="admin",
            email="admin@example.com",
            role=UserRole.PLATFORM_ADMIN
        )
        
        pm.create_user(
            username="user1",
            email="user1@tenant1.com",
            role=UserRole.TENANT_USER,
            tenant_id="tenant_1"
        )
        pm.create_user(
            username="user2",
            email="user2@tenant2.com",
            role=UserRole.TENANT_USER,
            tenant_id="tenant_2"
        )
        
        accessible_tenants = pm.get_accessible_tenants(admin)
        assert "tenant_1" in accessible_tenants
        assert "tenant_2" in accessible_tenants
    
    def test_get_accessible_tenants_tenant_admin(self):
        """Test getting accessible tenants for tenant admin"""
        pm = PermissionManager()
        tenant_admin = pm.create_user(
            username="tenant_admin",
            email="admin@tenant1.com",
            role=UserRole.TENANT_ADMIN,
            tenant_id="tenant_1"
        )
        
        accessible_tenants = pm.get_accessible_tenants(tenant_admin)
        assert accessible_tenants == ["tenant_1"]
    
    def test_get_accessible_tenants_tenant_user(self):
        """Test getting accessible tenants for tenant user"""
        pm = PermissionManager()
        tenant_user = pm.create_user(
            username="user",
            email="user@tenant1.com",
            role=UserRole.TENANT_USER,
            tenant_id="tenant_1"
        )
        
        accessible_tenants = pm.get_accessible_tenants(tenant_user)
        assert accessible_tenants == ["tenant_1"]


class TestGovernanceRuleManager:
    """Test GovernanceRuleManager class"""
    
    def test_create_rule(self):
        """Test creating a governance rule"""
        grm = GovernanceRuleManager()
        rule = grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Test Blacklist",
            description="Block malicious domains",
            config={"domains": ["malicious.com"]}
        )
        
        assert rule.rule_id in grm.rules
        assert rule.name == "Test Blacklist"
        assert "tenant_1" in grm.tenant_rules
        assert rule.rule_id in grm.tenant_rules["tenant_1"]
    
    def test_update_rule(self):
        """Test updating a governance rule"""
        grm = GovernanceRuleManager()
        rule = grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Test Rule",
            description="Test",
            config={"domains": []}
        )
        
        success = grm.update_rule(rule.rule_id, {
            "name": "Updated Rule",
            "enabled": False
        })
        
        assert success is True
        assert grm.rules[rule.rule_id].name == "Updated Rule"
        assert grm.rules[rule.rule_id].enabled is False
    
    def test_update_nonexistent_rule(self):
        """Test updating a nonexistent rule"""
        grm = GovernanceRuleManager()
        success = grm.update_rule("nonexistent_rule", {"name": "Test"})
        assert success is False
    
    def test_delete_rule(self):
        """Test deleting a governance rule"""
        grm = GovernanceRuleManager()
        rule = grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Test Rule",
            description="Test",
            config={"domains": []}
        )
        
        success = grm.delete_rule(rule.rule_id)
        assert success is True
        assert rule.rule_id not in grm.rules
        assert rule.rule_id not in grm.tenant_rules.get("tenant_1", [])
    
    def test_delete_nonexistent_rule(self):
        """Test deleting a nonexistent rule"""
        grm = GovernanceRuleManager()
        success = grm.delete_rule("nonexistent_rule")
        assert success is False
    
    def test_get_tenant_rules(self):
        """Test getting tenant rules"""
        grm = GovernanceRuleManager()
        rule1 = grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Rule 1",
            description="Test",
            config={"domains": []}
        )
        rule2 = grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.WHITELIST,
            name="Rule 2",
            description="Test",
            config={"domains": []}
        )
        
        rules = grm.get_tenant_rules("tenant_1")
        assert len(rules) == 2
        assert rule1 in rules
        assert rule2 in rules
    
    def test_validate_blacklist_config(self):
        """Test validating blacklist rule config"""
        grm = GovernanceRuleManager()
        
        valid_config = {"domains": ["example.com"]}
        assert grm.validate_rule_config(GovernanceRuleType.BLACKLIST, valid_config) is True
        
        invalid_config = {"keywords": ["test"]}
        assert grm.validate_rule_config(GovernanceRuleType.BLACKLIST, invalid_config) is False
    
    def test_validate_whitelist_config(self):
        """Test validating whitelist rule config"""
        grm = GovernanceRuleManager()
        
        valid_config = {"domains": ["trusted.com"]}
        assert grm.validate_rule_config(GovernanceRuleType.WHITELIST, valid_config) is True
        
        invalid_config = {}
        assert grm.validate_rule_config(GovernanceRuleType.WHITELIST, invalid_config) is False
    
    def test_validate_content_filter_config(self):
        """Test validating content filter rule config"""
        grm = GovernanceRuleManager()
        
        valid_config = {"keywords": ["badword"]}
        assert grm.validate_rule_config(GovernanceRuleType.CONTENT_FILTER, valid_config) is True
        
        invalid_config = {"domains": []}
        assert grm.validate_rule_config(GovernanceRuleType.CONTENT_FILTER, invalid_config) is False
    
    def test_validate_usage_limit_config(self):
        """Test validating usage limit rule config"""
        grm = GovernanceRuleManager()
        
        valid_config = {"max_tokens": 1000}
        assert grm.validate_rule_config(GovernanceRuleType.USAGE_LIMIT, valid_config) is True
        
        invalid_config = {"max_tokens": "invalid"}
        assert grm.validate_rule_config(GovernanceRuleType.USAGE_LIMIT, invalid_config) is False
    
    def test_apply_rules_blacklist_blocked(self):
        """Test applying blacklist rule that blocks request"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Block Malicious",
            description="Test",
            config={"domains": ["malicious.com"]}
        )
        
        request_data = {"url": "https://malicious.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is False
        assert "Block Malicious" in result['blocked_by']
    
    def test_apply_rules_blacklist_allowed(self):
        """Test applying blacklist rule that allows request"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Block Malicious",
            description="Test",
            config={"domains": ["malicious.com"]}
        )
        
        request_data = {"url": "https://safe.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is True
        assert len(result['blocked_by']) == 0
    
    def test_apply_rules_whitelist_allowed(self):
        """Test applying whitelist rule that allows request"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.WHITELIST,
            name="Allow Trusted",
            description="Test",
            config={"domains": ["trusted.com"]}
        )
        
        request_data = {"url": "https://trusted.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is True
    
    def test_apply_rules_whitelist_blocked(self):
        """Test applying whitelist rule that blocks request"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.WHITELIST,
            name="Allow Trusted",
            description="Test",
            config={"domains": ["example.com"]}
        )
        
        request_data = {"url": "https://different-site.org/api"}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is False
        assert "Allow Trusted" in result['blocked_by']
    
    @pytest.mark.xfail(strict=True, reason="Tracking: #949 - Security: Whitelist substring matching allows untrusted domains")
    def test_whitelist_substring_attack_prevention(self):
        """Test that whitelist prevents substring matching attacks (SECURITY TEST)
        
        This test verifies that the whitelist implementation uses proper domain matching
        instead of substring matching. A malicious actor should not be able to bypass
        whitelist restrictions by registering domains that contain whitelisted domains
        as substrings.
        
        Example attack: If 'trusted.com' is whitelisted, 'untrusted.com' should be blocked
        because 'trusted.com' is a substring of 'untrusted.com'.
        
        NOTE: This test expects CORRECT behavior (substring attack prevented).
        The current implementation has a security vulnerability where it uses substring
        matching. This test is marked as xfail until the bug is fixed.
        """
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.WHITELIST,
            name="Allow Trusted Domain",
            description="Security test for substring matching",
            config={"domains": ["trusted.com"]}
        )
        
        request_data = {"url": "https://trusted.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        assert result['allowed'] is True, "Exact domain match should be allowed"
        
        request_data = {"url": "https://api.trusted.com/v1"}
        result = grm.apply_rules("tenant_1", request_data)
        assert result['allowed'] is True, "Subdomain should be allowed"
        
        request_data = {"url": "https://untrusted.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        assert result['allowed'] is False, "Domain containing whitelist as substring should be BLOCKED"
        assert "Allow Trusted Domain" in result['blocked_by']
        
        request_data = {"url": "https://not-trusted.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        assert result['allowed'] is False, "Domain with whitelist as substring should be BLOCKED"
        
        request_data = {"url": "https://trusted.com.evil.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        assert result['allowed'] is False, "Domain with whitelist as prefix should be BLOCKED"
    
    def test_apply_rules_content_filter(self):
        """Test applying content filter rule"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.CONTENT_FILTER,
            name="Filter Bad Words",
            description="Test",
            config={"keywords": ["badword", "offensive"]}
        )
        
        request_data = {"content": "This contains badword and offensive text"}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is True
        assert "badword" not in result['modified_request']['content']
        assert "offensive" not in result['modified_request']['content']
        assert "*******" in result['modified_request']['content']
    
    def test_apply_rules_usage_limit_allowed(self):
        """Test applying usage limit rule that allows request"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.USAGE_LIMIT,
            name="Token Limit",
            description="Test",
            config={"max_tokens": 1000}
        )
        
        request_data = {"estimated_tokens": 500}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is True
    
    def test_apply_rules_usage_limit_blocked(self):
        """Test applying usage limit rule that blocks request"""
        grm = GovernanceRuleManager()
        grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.USAGE_LIMIT,
            name="Token Limit",
            description="Test",
            config={"max_tokens": 1000}
        )
        
        request_data = {"estimated_tokens": 2000}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is False
        assert "Token Limit" in result['blocked_by']
    
    def test_apply_rules_disabled_rule(self):
        """Test that disabled rules are not applied"""
        grm = GovernanceRuleManager()
        rule = grm.create_rule(
            tenant_id="tenant_1",
            rule_type=GovernanceRuleType.BLACKLIST,
            name="Disabled Rule",
            description="Test",
            config={"domains": ["blocked.com"]}
        )
        grm.update_rule(rule.rule_id, {"enabled": False})
        
        request_data = {"url": "https://blocked.com/api"}
        result = grm.apply_rules("tenant_1", request_data)
        
        assert result['allowed'] is True


class TestAIGovernanceModule:
    """Test AIGovernanceModule class"""
    
    def test_initialization(self):
        """Test AI Governance Module initialization"""
        module = AIGovernanceModule()
        
        assert module.permission_manager is not None
        assert module.rule_manager is not None
        assert module.app is not None
        
        admin_user = None
        for user in module.permission_manager.users.values():
            if user.username == "admin":
                admin_user = user
                break
        
        assert admin_user is not None
        assert admin_user.role == UserRole.PLATFORM_ADMIN
    
    def test_login_endpoint_success(self):
        """Test login endpoint with valid credentials"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        response = client.post('/governance/login', 
                              json={'username': 'admin', 'password': 'test'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session_token' in data
    
    def test_login_endpoint_failure(self):
        """Test login endpoint with invalid credentials"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        response = client.post('/governance/login',
                              json={'username': 'invalid', 'password': 'wrong'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_get_rules_unauthorized(self):
        """Test get rules endpoint without authentication"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        response = client.get('/governance/rules')
        assert response.status_code == 401
    
    def test_get_rules_platform_admin(self):
        """Test get rules endpoint as platform admin"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        login_response = client.post('/governance/login',
                                    json={'username': 'admin', 'password': 'test'})
        session_token = json.loads(login_response.data)['session_token']
        
        response = client.get('/governance/rules',
                            headers={'Authorization': f'Bearer {session_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'rules' in data
    
    def test_create_rule_unauthorized(self):
        """Test create rule endpoint without authentication"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        response = client.post('/governance/rules',
                              json={'name': 'Test', 'rule_type': 'blacklist'})
        assert response.status_code == 401
    
    def test_create_rule_success(self):
        """Test create rule endpoint with valid data
        
        NOTE: This test currently expects the CORRECT behavior (200 response with rule data).
        The actual implementation has a bug where GovernanceRuleType Enum cannot be serialized
        by Flask's jsonify(), causing a 500 error. This test is marked as xfail until the bug
        is fixed. Once fixed, remove the xfail marker.
        """
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        login_response = client.post('/governance/login',
                                    json={'username': 'admin', 'password': 'test'})
        session_token = json.loads(login_response.data)['session_token']
        
        response = client.post('/governance/rules',
                              headers={'Authorization': f'Bearer {session_token}'},
                              json={
                                  'tenant_id': 'tenant_1',
                                  'rule_type': 'blacklist',
                                  'name': 'Test Blacklist',
                                  'description': 'Test rule',
                                  'config': {'domains': ['test.com']}
                              })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'rule' in data
        assert data['rule']['name'] == 'Test Blacklist'
        assert data['rule']['rule_type'] == 'blacklist'
    
    def test_create_rule_invalid_config(self):
        """Test create rule endpoint with invalid config"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        login_response = client.post('/governance/login',
                                    json={'username': 'admin', 'password': 'test'})
        session_token = json.loads(login_response.data)['session_token']
        
        response = client.post('/governance/rules',
                              headers={'Authorization': f'Bearer {session_token}'},
                              json={
                                  'tenant_id': 'tenant_1',
                                  'rule_type': 'blacklist',
                                  'name': 'Test Blacklist',
                                  'description': 'Test rule',
                                  'config': {'invalid': 'config'}
                              })
        
        assert response.status_code == 400
    
    def test_dashboard_endpoint(self):
        """Test dashboard endpoint"""
        module = AIGovernanceModule()
        client = module.app.test_client()
        
        response = client.get('/governance/dashboard')
        assert response.status_code == 200
        assert b'Morning AI' in response.data
