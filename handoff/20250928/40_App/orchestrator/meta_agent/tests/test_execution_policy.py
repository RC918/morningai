"""
Tests for execution_policy module - Safety Limits and Constraints for Meta Agent

Issue: #1958 - Meta Agent: 新模組單元測試
"""

import pytest
from datetime import timedelta

from meta_agent.execution_policy import (
    AllowedOperation,
    ExecutionPolicy,
    DEFAULT_SAFE_OPERATIONS,
    ALWAYS_REQUIRE_APPROVAL,
    STRICT_POLICY,
    PERMISSIVE_POLICY,
    DRY_RUN_POLICY,
)


class TestAllowedOperation:
    """Tests for AllowedOperation enum"""

    def test_all_operations_exist(self):
        """Verify all expected operations are defined"""
        expected_operations = {
            "READ_FILE",
            "WRITE_FILE",
            "DELETE_FILE",
            "EXECUTE_COMMAND",
            "NETWORK_REQUEST",
            "DATABASE_READ",
            "DATABASE_WRITE",
            "DATABASE_DELETE",
            "DEPLOY_STAGING",
            "DEPLOY_PRODUCTION",
            "CREATE_PR",
            "MERGE_PR",
            "SEND_NOTIFICATION",
        }
        actual_operations = {member.name for member in AllowedOperation}
        assert actual_operations == expected_operations

    def test_operation_values(self):
        """Verify operation values are lowercase strings"""
        assert AllowedOperation.READ_FILE.value == "read_file"
        assert AllowedOperation.DEPLOY_PRODUCTION.value == "deploy_production"
        assert AllowedOperation.DATABASE_DELETE.value == "database_delete"


class TestDefaultOperations:
    """Tests for default operation sets"""

    def test_default_safe_operations(self):
        """Verify default safe operations"""
        assert AllowedOperation.READ_FILE in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.WRITE_FILE in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.EXECUTE_COMMAND in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.NETWORK_REQUEST in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.DATABASE_READ in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.CREATE_PR in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.SEND_NOTIFICATION in DEFAULT_SAFE_OPERATIONS

    def test_default_safe_operations_excludes_dangerous(self):
        """Verify dangerous operations are not in default safe set"""
        assert AllowedOperation.DELETE_FILE not in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.DATABASE_DELETE not in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.DEPLOY_PRODUCTION not in DEFAULT_SAFE_OPERATIONS
        assert AllowedOperation.MERGE_PR not in DEFAULT_SAFE_OPERATIONS

    def test_always_require_approval(self):
        """Verify operations that always require approval"""
        assert AllowedOperation.DELETE_FILE in ALWAYS_REQUIRE_APPROVAL
        assert AllowedOperation.DATABASE_DELETE in ALWAYS_REQUIRE_APPROVAL
        assert AllowedOperation.DEPLOY_PRODUCTION in ALWAYS_REQUIRE_APPROVAL
        assert AllowedOperation.MERGE_PR in ALWAYS_REQUIRE_APPROVAL


class TestExecutionPolicy:
    """Tests for ExecutionPolicy dataclass"""

    def test_default_policy_creation(self):
        """Test creating policy with default values"""
        policy = ExecutionPolicy()

        assert policy.max_execution_time == timedelta(hours=1)
        assert policy.max_task_timeout == timedelta(minutes=10)
        assert policy.max_blocked_wait_time == timedelta(minutes=5)
        assert policy.max_tasks == 100
        assert policy.max_retries_per_task == 3
        assert policy.max_consecutive_failures == 5
        assert policy.max_loop_iterations == 1000
        assert policy.dry_run is False
        assert policy.allow_production_access is False

    def test_custom_policy_creation(self):
        """Test creating policy with custom values"""
        policy = ExecutionPolicy(
            max_execution_time=timedelta(minutes=30),
            max_tasks=50,
            max_retries_per_task=5,
            dry_run=True,
        )

        assert policy.max_execution_time == timedelta(minutes=30)
        assert policy.max_tasks == 50
        assert policy.max_retries_per_task == 5
        assert policy.dry_run is True

    def test_default_allowed_operations(self):
        """Test default allowed operations"""
        policy = ExecutionPolicy()

        assert AllowedOperation.READ_FILE in policy.allowed_operations
        assert AllowedOperation.WRITE_FILE in policy.allowed_operations
        assert AllowedOperation.DELETE_FILE not in policy.allowed_operations

    def test_custom_allowed_operations(self):
        """Test custom allowed operations"""
        custom_ops = {AllowedOperation.READ_FILE, AllowedOperation.WRITE_FILE}
        policy = ExecutionPolicy(allowed_operations=custom_ops)

        assert policy.allowed_operations == custom_ops
        assert AllowedOperation.EXECUTE_COMMAND not in policy.allowed_operations

    def test_is_operation_allowed_true(self):
        """Test is_operation_allowed returns True for allowed operations"""
        policy = ExecutionPolicy()

        assert policy.is_operation_allowed(AllowedOperation.READ_FILE) is True
        assert policy.is_operation_allowed(AllowedOperation.WRITE_FILE) is True
        assert policy.is_operation_allowed(AllowedOperation.DATABASE_READ) is True

    def test_is_operation_allowed_false(self):
        """Test is_operation_allowed returns False for disallowed operations"""
        policy = ExecutionPolicy()

        assert policy.is_operation_allowed(AllowedOperation.DELETE_FILE) is False
        assert policy.is_operation_allowed(AllowedOperation.DATABASE_DELETE) is False
        assert policy.is_operation_allowed(AllowedOperation.DEPLOY_PRODUCTION) is False

    def test_requires_approval_always_required(self):
        """Test operations that always require approval"""
        policy = ExecutionPolicy(
            require_approval_for_deployment=False,
            require_approval_for_database_writes=False,
            require_approval_for_file_deletes=False,
        )

        # These always require approval regardless of settings
        assert policy.requires_approval(AllowedOperation.DELETE_FILE) is True
        assert policy.requires_approval(AllowedOperation.DATABASE_DELETE) is True
        assert policy.requires_approval(AllowedOperation.DEPLOY_PRODUCTION) is True
        assert policy.requires_approval(AllowedOperation.MERGE_PR) is True

    def test_requires_approval_deployment(self):
        """Test deployment approval requirement"""
        policy_with = ExecutionPolicy(require_approval_for_deployment=True)
        policy_without = ExecutionPolicy(require_approval_for_deployment=False)

        assert policy_with.requires_approval(AllowedOperation.DEPLOY_STAGING) is True
        # DEPLOY_PRODUCTION is in ALWAYS_REQUIRE_APPROVAL
        assert policy_with.requires_approval(AllowedOperation.DEPLOY_PRODUCTION) is True

        assert policy_without.requires_approval(AllowedOperation.DEPLOY_STAGING) is False
        # Still requires approval because it's in ALWAYS_REQUIRE_APPROVAL
        assert policy_without.requires_approval(AllowedOperation.DEPLOY_PRODUCTION) is True

    def test_requires_approval_database_writes(self):
        """Test database write approval requirement"""
        policy_with = ExecutionPolicy(require_approval_for_database_writes=True)
        policy_without = ExecutionPolicy(require_approval_for_database_writes=False)

        assert policy_with.requires_approval(AllowedOperation.DATABASE_WRITE) is True
        assert policy_with.requires_approval(AllowedOperation.DATABASE_DELETE) is True

        assert policy_without.requires_approval(AllowedOperation.DATABASE_WRITE) is False
        # Still requires approval because it's in ALWAYS_REQUIRE_APPROVAL
        assert policy_without.requires_approval(AllowedOperation.DATABASE_DELETE) is True

    def test_requires_approval_file_deletes(self):
        """Test file delete approval requirement"""
        policy_with = ExecutionPolicy(require_approval_for_file_deletes=True)
        policy_without = ExecutionPolicy(require_approval_for_file_deletes=False)

        # DELETE_FILE is in ALWAYS_REQUIRE_APPROVAL, so always True
        assert policy_with.requires_approval(AllowedOperation.DELETE_FILE) is True
        assert policy_without.requires_approval(AllowedOperation.DELETE_FILE) is True

    def test_requires_approval_safe_operations(self):
        """Test that safe operations don't require approval"""
        policy = ExecutionPolicy()

        assert policy.requires_approval(AllowedOperation.READ_FILE) is False
        assert policy.requires_approval(AllowedOperation.WRITE_FILE) is False
        assert policy.requires_approval(AllowedOperation.EXECUTE_COMMAND) is False
        assert policy.requires_approval(AllowedOperation.NETWORK_REQUEST) is False
        assert policy.requires_approval(AllowedOperation.DATABASE_READ) is False
        assert policy.requires_approval(AllowedOperation.CREATE_PR) is False
        assert policy.requires_approval(AllowedOperation.SEND_NOTIFICATION) is False

    def test_validate_success(self):
        """Test validate passes for valid policy"""
        policy = ExecutionPolicy()
        # Should not raise
        policy.validate()

    def test_validate_invalid_max_execution_time(self):
        """Test validate fails for invalid max_execution_time"""
        policy = ExecutionPolicy(max_execution_time=timedelta(seconds=0))

        with pytest.raises(ValueError, match="max_execution_time must be positive"):
            policy.validate()

    def test_validate_negative_max_execution_time(self):
        """Test validate fails for negative max_execution_time"""
        policy = ExecutionPolicy(max_execution_time=timedelta(seconds=-1))

        with pytest.raises(ValueError, match="max_execution_time must be positive"):
            policy.validate()

    def test_validate_invalid_max_tasks(self):
        """Test validate fails for invalid max_tasks"""
        policy = ExecutionPolicy(max_tasks=0)

        with pytest.raises(ValueError, match="max_tasks must be positive"):
            policy.validate()

    def test_validate_negative_max_tasks(self):
        """Test validate fails for negative max_tasks"""
        policy = ExecutionPolicy(max_tasks=-1)

        with pytest.raises(ValueError, match="max_tasks must be positive"):
            policy.validate()

    def test_validate_negative_max_retries(self):
        """Test validate fails for negative max_retries_per_task"""
        policy = ExecutionPolicy(max_retries_per_task=-1)

        with pytest.raises(ValueError, match="max_retries_per_task cannot be negative"):
            policy.validate()

    def test_validate_zero_max_retries_allowed(self):
        """Test validate passes for zero max_retries_per_task"""
        policy = ExecutionPolicy(max_retries_per_task=0)
        # Should not raise - zero retries is valid
        policy.validate()

    def test_validate_invalid_max_loop_iterations(self):
        """Test validate fails for invalid max_loop_iterations"""
        policy = ExecutionPolicy(max_loop_iterations=0)

        with pytest.raises(ValueError, match="max_loop_iterations must be positive"):
            policy.validate()


class TestPresetPolicies:
    """Tests for preset policy configurations"""

    def test_strict_policy(self):
        """Test STRICT_POLICY configuration"""
        assert STRICT_POLICY.max_execution_time == timedelta(minutes=30)
        assert STRICT_POLICY.max_tasks == 50
        assert STRICT_POLICY.max_retries_per_task == 2
        assert STRICT_POLICY.max_consecutive_failures == 3
        assert STRICT_POLICY.require_approval_for_deployment is True
        assert STRICT_POLICY.require_approval_for_database_writes is True
        assert STRICT_POLICY.require_approval_for_file_deletes is True
        assert STRICT_POLICY.allow_production_access is False

    def test_strict_policy_validates(self):
        """Test STRICT_POLICY passes validation"""
        STRICT_POLICY.validate()

    def test_permissive_policy(self):
        """Test PERMISSIVE_POLICY configuration"""
        assert PERMISSIVE_POLICY.max_execution_time == timedelta(hours=4)
        assert PERMISSIVE_POLICY.max_tasks == 200
        assert PERMISSIVE_POLICY.max_retries_per_task == 5
        assert PERMISSIVE_POLICY.max_consecutive_failures == 10
        assert PERMISSIVE_POLICY.require_approval_for_deployment is False
        assert PERMISSIVE_POLICY.require_approval_for_database_writes is False
        assert PERMISSIVE_POLICY.require_approval_for_file_deletes is False
        assert PERMISSIVE_POLICY.allow_production_access is True

    def test_permissive_policy_validates(self):
        """Test PERMISSIVE_POLICY passes validation"""
        PERMISSIVE_POLICY.validate()

    def test_dry_run_policy(self):
        """Test DRY_RUN_POLICY configuration"""
        assert DRY_RUN_POLICY.max_execution_time == timedelta(minutes=15)
        assert DRY_RUN_POLICY.max_tasks == 100
        assert DRY_RUN_POLICY.dry_run is True
        assert DRY_RUN_POLICY.allow_production_access is False

    def test_dry_run_policy_validates(self):
        """Test DRY_RUN_POLICY passes validation"""
        DRY_RUN_POLICY.validate()

    def test_strict_vs_permissive_approval_requirements(self):
        """Test approval requirements differ between strict and permissive"""
        # Strict requires approval for staging deployment
        assert STRICT_POLICY.requires_approval(AllowedOperation.DEPLOY_STAGING) is True
        # Permissive doesn't require approval for staging deployment
        assert PERMISSIVE_POLICY.requires_approval(AllowedOperation.DEPLOY_STAGING) is False

        # Both require approval for production deployment (ALWAYS_REQUIRE_APPROVAL)
        assert STRICT_POLICY.requires_approval(AllowedOperation.DEPLOY_PRODUCTION) is True
        assert PERMISSIVE_POLICY.requires_approval(AllowedOperation.DEPLOY_PRODUCTION) is True

    def test_strict_vs_permissive_database_writes(self):
        """Test database write approval differs between strict and permissive"""
        # Strict requires approval for database writes
        assert STRICT_POLICY.requires_approval(AllowedOperation.DATABASE_WRITE) is True
        # Permissive doesn't require approval for database writes
        assert PERMISSIVE_POLICY.requires_approval(AllowedOperation.DATABASE_WRITE) is False
