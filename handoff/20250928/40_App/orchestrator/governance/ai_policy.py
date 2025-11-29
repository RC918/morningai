"""
AI Policy Management - Phase 6 PR-1

Provides tenant-specific AI usage policies including:
- Blacklist/whitelist for AI capabilities
- Content filtering rules
- Usage limits and quotas
- Three-tier permission architecture (Platform Admin / Tenant Admin / Tenant User)

This module enables tenants to customize AI behavior through a guided JSON editor
in the Owner Console.
"""
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PolicyType(str, Enum):
    """Types of AI policies"""
    CAPABILITY_WHITELIST = "capability_whitelist"
    CAPABILITY_BLACKLIST = "capability_blacklist"
    CONTENT_FILTER = "content_filter"
    USAGE_LIMIT = "usage_limit"
    RATE_LIMIT = "rate_limit"
    MODEL_RESTRICTION = "model_restriction"


class PolicyScope(str, Enum):
    """Scope of policy application"""
    PLATFORM = "platform"
    TENANT = "tenant"
    USER = "user"


class PolicyStatus(str, Enum):
    """Status of a policy"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


@dataclass
class AIPolicy:
    """
    Schema for AI usage policies

    Attributes:
        id: Unique policy identifier
        tenant_id: Tenant this policy belongs to (None for platform-level)
        name: Human-readable policy name
        description: Policy description
        policy_type: Type of policy (whitelist, blacklist, filter, limit)
        scope: Scope of application (platform, tenant, user)
        rules: JSON rules configuration
        priority: Priority for conflict resolution (higher = more important)
        status: Policy status (active, inactive, draft)
        created_by: User ID who created the policy
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Additional metadata
    """
    name: str
    policy_type: PolicyType
    rules: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    description: Optional[str] = None
    scope: PolicyScope = PolicyScope.TENANT
    priority: int = 0
    status: PolicyStatus = PolicyStatus.DRAFT
    created_by: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['policy_type'] = self.policy_type.value
        data['scope'] = self.scope.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIPolicy":
        """Create AIPolicy from dictionary"""
        if 'policy_type' in data and isinstance(data['policy_type'], str):
            data['policy_type'] = PolicyType(data['policy_type'])
        if 'scope' in data and isinstance(data['scope'], str):
            data['scope'] = PolicyScope(data['scope'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = PolicyStatus(data['status'])
        return cls(**data)


# Default policy templates for guided editor
DEFAULT_POLICY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "capability_whitelist": {
        "name": "Allowed AI Capabilities",
        "description": "Define which AI capabilities are allowed for this tenant",
        "policy_type": PolicyType.CAPABILITY_WHITELIST.value,
        "rules": {
            "allowed_capabilities": [
                "code_generation",
                "code_review",
                "faq_generation",
                "task_planning"
            ],
            "require_human_approval": ["code_generation"],
            "auto_approve": ["faq_generation"]
        }
    },
    "capability_blacklist": {
        "name": "Blocked AI Capabilities",
        "description": "Define which AI capabilities are blocked for this tenant",
        "policy_type": PolicyType.CAPABILITY_BLACKLIST.value,
        "rules": {
            "blocked_capabilities": [],
            "blocked_file_patterns": [
                "**/.env*",
                "**/secrets/**",
                "**/credentials/**"
            ],
            "blocked_domains": []
        }
    },
    "content_filter": {
        "name": "Content Filtering Rules",
        "description": "Define content filtering rules for AI outputs",
        "policy_type": PolicyType.CONTENT_FILTER.value,
        "rules": {
            "filter_pii": True,
            "filter_profanity": True,
            "filter_sensitive_data": True,
            "custom_blocked_terms": [],
            "output_max_length": 10000
        }
    },
    "usage_limit": {
        "name": "AI Usage Limits",
        "description": "Define usage limits and quotas",
        "policy_type": PolicyType.USAGE_LIMIT.value,
        "rules": {
            "daily_request_limit": 1000,
            "monthly_token_limit": 1000000,
            "max_concurrent_tasks": 5,
            "max_task_duration_seconds": 300
        }
    },
    "rate_limit": {
        "name": "Rate Limiting",
        "description": "Define rate limiting rules",
        "policy_type": PolicyType.RATE_LIMIT.value,
        "rules": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_limit": 10
        }
    },
    "model_restriction": {
        "name": "Model Restrictions",
        "description": "Define which AI models can be used",
        "policy_type": PolicyType.MODEL_RESTRICTION.value,
        "rules": {
            "allowed_providers": ["openai", "gemini"],
            "allowed_models": ["gpt-4", "gpt-4-turbo", "gemini-pro"],
            "default_provider": "openai",
            "default_model": "gpt-4"
        }
    }
}


class AIPolicyManager:
    """
    Manages AI policies for tenants

    Provides CRUD operations and policy evaluation for tenant-specific
    AI usage rules.
    """

    def __init__(self, supabase_client=None):
        """
        Initialize AIPolicyManager

        Args:
            supabase_client: Optional Supabase client for database operations
        """
        self._supabase = supabase_client
        self._cache: Dict[str, List[AIPolicy]] = {}

    def _get_supabase(self):
        """Get Supabase client, initializing if needed"""
        if self._supabase is None:
            try:
                from orchestrator.persistence.db_client import get_client
                self._supabase = get_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")
                return None
        return self._supabase

    def create_policy(
        self,
        tenant_id: str,
        name: str,
        policy_type: PolicyType,
        rules: Dict[str, Any],
        created_by: str,
        description: Optional[str] = None,
        scope: PolicyScope = PolicyScope.TENANT,
        priority: int = 0,
        status: PolicyStatus = PolicyStatus.DRAFT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AIPolicy]:
        """
        Create a new AI policy

        Args:
            tenant_id: Tenant ID
            name: Policy name
            policy_type: Type of policy
            rules: Policy rules configuration
            created_by: User ID creating the policy
            description: Optional description
            scope: Policy scope
            priority: Priority for conflict resolution
            status: Initial status
            metadata: Additional metadata

        Returns:
            Created AIPolicy instance if successful, None if persistence failed
        """
        policy = AIPolicy(
            name=name,
            policy_type=policy_type,
            rules=rules,
            tenant_id=tenant_id,
            description=description,
            scope=scope,
            priority=priority,
            status=status,
            created_by=created_by,
            metadata=metadata or {}
        )

        supabase = self._get_supabase()
        if not supabase:
            logger.error(
                "Failed to create policy: Supabase client not available"
            )
            return None

        try:
            response = supabase.table('ai_policies').insert(
                policy.to_dict()
            ).execute()

            if response.data:
                logger.info(
                    f"Created AI policy {policy.id} for tenant {tenant_id}"
                )
                self._invalidate_cache(tenant_id)
                return policy
            else:
                logger.error(
                    f"Failed to create policy: No data returned from insert"
                )
                return None
        except Exception as e:
            logger.error(f"Failed to save policy to database: {e}")
            return None

    def get_policy(self, policy_id: str) -> Optional[AIPolicy]:
        """
        Get a policy by ID

        Args:
            policy_id: Policy ID

        Returns:
            AIPolicy if found, None otherwise
        """
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            response = supabase.table('ai_policies').select('*').eq(
                'id', policy_id
            ).single().execute()

            if response.data:
                return AIPolicy.from_dict(response.data)
        except Exception as e:
            logger.error(f"Failed to get policy {policy_id}: {e}")

        return None

    def list_policies(
        self,
        tenant_id: str,
        policy_type: Optional[PolicyType] = None,
        status: Optional[PolicyStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AIPolicy]:
        """
        List policies for a tenant

        Args:
            tenant_id: Tenant ID
            policy_type: Optional filter by policy type
            status: Optional filter by status
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of AIPolicy instances
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            query = supabase.table('ai_policies').select('*').eq(
                'tenant_id', tenant_id
            )

            if policy_type:
                query = query.eq('policy_type', policy_type.value)
            if status:
                query = query.eq('status', status.value)

            query = query.order('priority', desc=True).range(
                offset, offset + limit - 1
            )

            response = query.execute()

            if response.data:
                return [AIPolicy.from_dict(p) for p in response.data]
        except Exception as e:
            logger.error(f"Failed to list policies for tenant {tenant_id}: {e}")

        return []

    def update_policy(
        self,
        policy_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Optional[AIPolicy]:
        """
        Update an existing policy

        Args:
            policy_id: Policy ID to update
            updates: Dictionary of fields to update
            updated_by: User ID making the update

        Returns:
            Updated AIPolicy if successful, None otherwise
        """
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            updates['updated_at'] = datetime.utcnow().isoformat()

            if 'policy_type' in updates and isinstance(
                updates['policy_type'], PolicyType
            ):
                updates['policy_type'] = updates['policy_type'].value
            if 'scope' in updates and isinstance(updates['scope'], PolicyScope):
                updates['scope'] = updates['scope'].value
            if 'status' in updates and isinstance(
                updates['status'], PolicyStatus
            ):
                updates['status'] = updates['status'].value

            response = supabase.table('ai_policies').update(updates).eq(
                'id', policy_id
            ).execute()

            if response.data:
                policy = AIPolicy.from_dict(response.data[0])
                logger.info(f"Updated AI policy {policy_id} by {updated_by}")
                self._invalidate_cache(policy.tenant_id)
                return policy
        except Exception as e:
            logger.error(f"Failed to update policy {policy_id}: {e}")

        return None

    def delete_policy(self, policy_id: str, deleted_by: str) -> bool:
        """
        Delete a policy

        Args:
            policy_id: Policy ID to delete
            deleted_by: User ID deleting the policy

        Returns:
            True if deleted successfully, False otherwise
        """
        supabase = self._get_supabase()
        if not supabase:
            return False

        try:
            policy = self.get_policy(policy_id)
            if not policy:
                return False

            response = supabase.table('ai_policies').delete().eq(
                'id', policy_id
            ).execute()

            if response.data:
                logger.info(f"Deleted AI policy {policy_id} by {deleted_by}")
                self._invalidate_cache(policy.tenant_id)
                return True
        except Exception as e:
            logger.error(f"Failed to delete policy {policy_id}: {e}")

        return False

    def get_active_policies(self, tenant_id: str) -> List[AIPolicy]:
        """
        Get all active policies for a tenant

        Args:
            tenant_id: Tenant ID

        Returns:
            List of active AIPolicy instances, sorted by priority
        """
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        policies = self.list_policies(
            tenant_id=tenant_id,
            status=PolicyStatus.ACTIVE,
            limit=100
        )

        self._cache[tenant_id] = policies
        return policies

    def evaluate_request(
        self,
        tenant_id: str,
        capability: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if a request is allowed based on tenant policies

        Args:
            tenant_id: Tenant ID
            capability: Requested capability (e.g., "code_generation")
            context: Additional context for evaluation

        Returns:
            Dictionary with 'allowed' boolean and 'reason' string
        """
        policies = self.get_active_policies(tenant_id)
        context = context or {}

        result = {
            'allowed': True,
            'reason': 'No policies restrict this action',
            'applied_policies': []
        }

        for policy in policies:
            if policy.policy_type == PolicyType.CAPABILITY_BLACKLIST:
                blocked = policy.rules.get('blocked_capabilities', [])
                if capability in blocked:
                    result['allowed'] = False
                    result['reason'] = f"Capability '{capability}' is blocked"
                    result['applied_policies'].append(policy.id)
                    return result

            elif policy.policy_type == PolicyType.CAPABILITY_WHITELIST:
                allowed = policy.rules.get('allowed_capabilities', [])
                if allowed and capability not in allowed:
                    result['allowed'] = False
                    result['reason'] = f"Capability '{capability}' is not allowed"
                    result['applied_policies'].append(policy.id)
                    return result

        return result

    def get_policy_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default policy templates for guided editor

        Returns:
            Dictionary of policy templates
        """
        return DEFAULT_POLICY_TEMPLATES.copy()

    def _invalidate_cache(self, tenant_id: Optional[str]):
        """Invalidate cache for a tenant"""
        if tenant_id and tenant_id in self._cache:
            del self._cache[tenant_id]


_policy_manager: Optional[AIPolicyManager] = None


def get_ai_policy_manager() -> AIPolicyManager:
    """Get or create global AIPolicyManager instance"""
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = AIPolicyManager()
    return _policy_manager
