"""
Tests for AI Policy Management - Phase 6 PR-1

Tests the AIPolicy dataclass, AIPolicyManager CRUD operations,
and policy evaluation logic.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest  # noqa: E402
import uuid  # noqa: E402
from datetime import datetime  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from governance.ai_policy import (  # noqa: E402
    AIPolicy,
    AIPolicyManager,
    PolicyType,
    PolicyScope,
    PolicyStatus,
    DEFAULT_POLICY_TEMPLATES,
    get_ai_policy_manager
)


class TestPolicyEnums:
    """Test policy enum values"""

    def test_policy_type_values(self):
        assert PolicyType.CAPABILITY_WHITELIST.value == "capability_whitelist"
        assert PolicyType.CAPABILITY_BLACKLIST.value == "capability_blacklist"
        assert PolicyType.CONTENT_FILTER.value == "content_filter"
        assert PolicyType.USAGE_LIMIT.value == "usage_limit"
        assert PolicyType.RATE_LIMIT.value == "rate_limit"
        assert PolicyType.MODEL_RESTRICTION.value == "model_restriction"

    def test_policy_scope_values(self):
        assert PolicyScope.PLATFORM.value == "platform"
        assert PolicyScope.TENANT.value == "tenant"
        assert PolicyScope.USER.value == "user"

    def test_policy_status_values(self):
        assert PolicyStatus.ACTIVE.value == "active"
        assert PolicyStatus.INACTIVE.value == "inactive"
        assert PolicyStatus.DRAFT.value == "draft"


class TestAIPolicy:
    """Test AIPolicy dataclass"""

    def test_create_policy_with_defaults(self):
        policy = AIPolicy(
            name="Test Policy",
            policy_type=PolicyType.CAPABILITY_WHITELIST,
            rules={"allowed": ["chat", "summarize"]}
        )
        assert policy.name == "Test Policy"
        assert policy.policy_type == PolicyType.CAPABILITY_WHITELIST
        assert policy.scope == PolicyScope.TENANT
        assert policy.status == PolicyStatus.DRAFT
        assert policy.priority == 0
        assert policy.rules == {"allowed": ["chat", "summarize"]}

    def test_create_policy_with_all_fields(self):
        tenant_id = str(uuid.uuid4())
        created_by = str(uuid.uuid4())
        policy = AIPolicy(
            name="Full Policy",
            description="A complete policy",
            policy_type=PolicyType.CONTENT_FILTER,
            scope=PolicyScope.USER,
            rules={"blocked_terms": ["spam"]},
            priority=10,
            status=PolicyStatus.ACTIVE,
            tenant_id=tenant_id,
            created_by=created_by,
            metadata={"version": "1.0"}
        )
        assert policy.name == "Full Policy"
        assert policy.description == "A complete policy"
        assert policy.policy_type == PolicyType.CONTENT_FILTER
        assert policy.scope == PolicyScope.USER
        assert policy.priority == 10
        assert policy.status == PolicyStatus.ACTIVE
        assert policy.tenant_id == tenant_id
        assert policy.created_by == created_by
        assert policy.metadata == {"version": "1.0"}

    def test_policy_to_dict(self):
        policy = AIPolicy(
            name="Dict Test",
            policy_type=PolicyType.RATE_LIMIT,
            rules={"max_requests": 100}
        )
        policy_dict = policy.to_dict()
        assert policy_dict["name"] == "Dict Test"
        assert policy_dict["policy_type"] == "rate_limit"
        assert policy_dict["scope"] == "tenant"
        assert policy_dict["status"] == "draft"
        assert policy_dict["rules"] == {"max_requests": 100}

    def test_policy_from_dict(self):
        data = {
            "id": str(uuid.uuid4()),
            "name": "From Dict",
            "policy_type": "usage_limit",
            "scope": "platform",
            "status": "active",
            "rules": {"daily_limit": 1000},
            "priority": 5,
            "tenant_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        policy = AIPolicy.from_dict(data)
        assert policy.name == "From Dict"
        assert policy.policy_type == PolicyType.USAGE_LIMIT
        assert policy.scope == PolicyScope.PLATFORM
        assert policy.status == PolicyStatus.ACTIVE
        assert policy.priority == 5


class TestAIPolicyManager:
    """Test AIPolicyManager CRUD operations"""

    @pytest.fixture
    def manager(self):
        return AIPolicyManager()

    @pytest.fixture
    def mock_supabase(self):
        with patch('governance.ai_policy.get_supabase_client') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    def test_manager_initialization(self, manager):
        assert manager is not None
        assert hasattr(manager, 'create_policy')
        assert hasattr(manager, 'get_policy')
        assert hasattr(manager, 'list_policies')
        assert hasattr(manager, 'update_policy')
        assert hasattr(manager, 'delete_policy')

    def test_get_policy_templates(self, manager):
        templates = manager.get_policy_templates()
        assert isinstance(templates, dict)
        assert len(templates) > 0
        for key, template in templates.items():
            assert "name" in template
            assert "description" in template
            assert "policy_type" in template
            assert "rules" in template

    def test_evaluate_request_no_policies_returns_allowed(self, manager):
        result = manager.evaluate_request(
            tenant_id=str(uuid.uuid4()),
            capability="chat",
            context={}
        )
        assert result["allowed"] is True


class TestDefaultPolicyTemplates:
    """Test default policy templates"""

    def test_templates_exist(self):
        assert DEFAULT_POLICY_TEMPLATES is not None
        assert len(DEFAULT_POLICY_TEMPLATES) > 0

    def test_template_structure(self):
        for key, template in DEFAULT_POLICY_TEMPLATES.items():
            assert "name" in template
            assert "description" in template
            assert "policy_type" in template
            assert "rules" in template
            assert template["policy_type"] in [t.value for t in PolicyType]

    def test_capability_whitelist_template(self):
        whitelist = DEFAULT_POLICY_TEMPLATES.get("capability_whitelist")
        assert whitelist is not None
        assert "allowed_capabilities" in whitelist["rules"]

    def test_content_filter_template(self):
        content_filter = DEFAULT_POLICY_TEMPLATES.get("content_filter")
        assert content_filter is not None
        assert "filter_pii" in content_filter["rules"]

    def test_rate_limit_template(self):
        rate_limit = DEFAULT_POLICY_TEMPLATES.get("rate_limit")
        assert rate_limit is not None
        assert "requests_per_minute" in rate_limit["rules"]


class TestGetAIPolicyManager:
    """Test singleton pattern for AIPolicyManager"""

    def test_get_manager_returns_instance(self):
        manager = get_ai_policy_manager()
        assert manager is not None
        assert isinstance(manager, AIPolicyManager)

    def test_get_manager_returns_same_instance(self):
        manager1 = get_ai_policy_manager()
        manager2 = get_ai_policy_manager()
        assert manager1 is manager2
