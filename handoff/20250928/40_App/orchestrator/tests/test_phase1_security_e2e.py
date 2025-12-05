#!/usr/bin/env python3
"""
Phase 1 Security Foundation E2E Tests - Agent Self-Diagnosis

Tests the security guardrails implemented in Phase 1:
- RLS hard gate verification (2FA tables)
- Semantic rules validation (action whitelist, sensitive files, high-risk commands)
- Human-in-the-Loop (HITL) approval mechanism

These tests verify that the "immune system" is functioning correctly.
"""

import pytest
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project_engineer.semantic_rules import (
    SemanticRulesValidator,
    HIGH_RISK_ACTIONS,
    SENSITIVE_FILE_PATTERNS,
    DEFAULT_ALLOWED_ACTIONS,
    validate_action,
    validate_sensitive_file,
    validate_command,
    get_security_summary
)


class TestPhase1SecurityFoundation:
    """Phase 1 Security Foundation E2E Tests"""

    def test_security_summary_returns_expected_structure(self):
        """Should return security configuration summary"""
        summary = get_security_summary()
        assert 'allowed_actions' in summary
        assert 'blocked_file_patterns' in summary
        assert 'high_risk_actions' in summary
        assert 'require_hitl_for_high_risk' in summary
        assert 'version' in summary
        assert 'phase1' in summary['version'].lower()

    def test_default_allowed_actions_are_conservative(self):
        """Default allowed actions should be conservative whitelist"""
        assert 'read_file' in DEFAULT_ALLOWED_ACTIONS
        assert 'write_file' in DEFAULT_ALLOWED_ACTIONS
        assert 'run_tests' in DEFAULT_ALLOWED_ACTIONS
        assert 'create_pr' in DEFAULT_ALLOWED_ACTIONS
        # Should NOT include dangerous actions
        assert 'delete_database' not in DEFAULT_ALLOWED_ACTIONS
        assert 'drop_table' not in DEFAULT_ALLOWED_ACTIONS

    def test_high_risk_actions_include_dangerous_operations(self):
        """High-risk actions should include dangerous operations"""
        assert 'DROP TABLE' in HIGH_RISK_ACTIONS
        assert 'DELETE FROM' in HIGH_RISK_ACTIONS
        assert 'rm -rf' in HIGH_RISK_ACTIONS
        assert 'chmod 777' in HIGH_RISK_ACTIONS

    def test_sensitive_file_patterns_include_credentials(self):
        """Sensitive file patterns should include credential files (minimal blocklist)
        
        Note: PR #1943 revision - minimal blocklist only includes files that should
        NEVER be modified by agents. .env and credentials.json are now allowed.
        """
        # These are in the minimal blocklist (NEVER modify)
        assert 'secrets.yaml' in SENSITIVE_FILE_PATTERNS
        assert 'secrets.yml' in SENSITIVE_FILE_PATTERNS
        assert 'private_key' in SENSITIVE_FILE_PATTERNS
        assert '.pem' in SENSITIVE_FILE_PATTERNS
        assert '.key' in SENSITIVE_FILE_PATTERNS
        assert '.npmrc' in SENSITIVE_FILE_PATTERNS
        assert '.pypirc' in SENSITIVE_FILE_PATTERNS
        # These are NOT in the minimal blocklist (Agent can modify)
        assert '.env' not in SENSITIVE_FILE_PATTERNS
        assert 'credentials.json' not in SENSITIVE_FILE_PATTERNS


class TestActionWhitelistValidation:
    """Test action whitelist validation (Phase 1 Security Foundation)"""

    def test_allowed_action_passes_validation(self):
        """Allowed actions should pass validation"""
        is_valid, error = validate_action('read_file')
        assert is_valid is True
        assert error is None

    def test_disallowed_action_fails_validation(self):
        """Disallowed actions should fail validation"""
        is_valid, error = validate_action('delete_production_database')
        assert is_valid is False
        assert error is not None
        assert 'not in allowed actions' in error.lower()

    def test_validator_action_validation_with_custom_whitelist(self):
        """Validator should respect custom action whitelist"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = ['read_file', 'write_file']

        is_valid, violation = validator.validate_action('read_file')
        assert is_valid is True

        is_valid, violation = validator.validate_action('run_tests')
        assert is_valid is False
        assert violation is not None
        assert violation.rule_type == 'action'


class TestSensitiveFileBlocking:
    """Test sensitive file blocking (Phase 1 Security Foundation)
    
    Note: PR #1943 revision - minimal blocklist only includes files that should
    NEVER be modified by agents. .env and credentials.json are now allowed.
    """

    def test_env_file_is_allowed(self):
        """Should allow .env files (not in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('.env')
        assert is_valid is True
        assert error is None

    def test_env_local_file_is_allowed(self):
        """Should allow .env.local files (not in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('.env.local')
        assert is_valid is True
        assert error is None

    def test_credentials_json_is_allowed(self):
        """Should allow credentials.json (not in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('credentials.json')
        assert is_valid is True
        assert error is None

    def test_secrets_yaml_is_blocked(self):
        """Should block secrets.yaml (in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('secrets.yaml')
        assert is_valid is False
        assert error is not None

    def test_private_key_is_blocked(self):
        """Should block private_key files (in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('private_key')
        assert is_valid is False
        assert error is not None

    def test_pem_file_is_blocked(self):
        """Should block .pem files (in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('server.pem')
        assert is_valid is False
        assert error is not None
        assert 'sensitive' in error.lower()

    def test_npmrc_file_is_blocked(self):
        """Should block .npmrc files (in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('.npmrc')
        assert is_valid is False
        assert error is not None

    def test_normal_file_is_allowed(self):
        """Should allow normal files"""
        is_valid, error = validate_sensitive_file('src/main.py')
        assert is_valid is True
        assert error is None

    def test_docs_file_is_allowed(self):
        """Should allow documentation files"""
        is_valid, error = validate_sensitive_file('docs/README.md')
        assert is_valid is True
        assert error is None

    def test_env_production_file_is_allowed(self):
        """Should allow .env.production files (not in minimal blocklist)"""
        is_valid, error = validate_sensitive_file('config/.env.production')
        assert is_valid is True
        assert error is None


class TestHighRiskCommandBlocking:
    """Test high-risk command blocking (Phase 1 Security Foundation)"""

    def test_drop_table_command_is_blocked(self):
        """Should block DROP TABLE commands"""
        is_valid, error = validate_command('DROP TABLE users;')
        assert is_valid is False
        assert error is not None
        assert 'high-risk' in error.lower()

    def test_delete_from_command_is_blocked(self):
        """Should block DELETE FROM commands"""
        is_valid, error = validate_command('DELETE FROM users WHERE id > 0;')
        assert is_valid is False
        assert error is not None

    def test_rm_rf_command_is_blocked(self):
        """Should block rm -rf commands"""
        is_valid, error = validate_command('rm -rf /important/data')
        assert is_valid is False
        assert error is not None

    def test_chmod_777_command_is_blocked(self):
        """Should block chmod 777 commands"""
        is_valid, error = validate_command('chmod 777 /etc/passwd')
        assert is_valid is False
        assert error is not None

    def test_safe_command_is_allowed(self):
        """Should allow safe commands"""
        is_valid, error = validate_command('ls -la')
        assert is_valid is True
        assert error is None

    def test_git_command_is_allowed(self):
        """Should allow git commands"""
        is_valid, error = validate_command('git status')
        assert is_valid is True
        assert error is None

    def test_pytest_command_is_allowed(self):
        """Should allow pytest commands"""
        is_valid, error = validate_command('pytest tests/')
        assert is_valid is True
        assert error is None


class TestHITLApprovalMechanism:
    """Test Human-in-the-Loop approval mechanism (Phase 1 Security Foundation)"""

    def test_high_risk_violation_requires_approval(self):
        """High-risk violations should require HITL approval"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True

        is_valid, violation = validator.validate_command('DROP TABLE users;')
        assert is_valid is False
        assert violation is not None
        assert violation.requires_approval is True
        assert violation.severity == 'critical'

    def test_sensitive_file_violation_requires_approval(self):
        """Sensitive file violations should require HITL approval"""
        validator = SemanticRulesValidator()

        # Use secrets.yaml which is in the minimal blocklist
        is_valid, violation = validator.validate_sensitive_file('secrets.yaml')
        assert is_valid is False
        assert violation is not None
        assert violation.requires_approval is True
        assert violation.severity == 'critical'

    def test_hitl_disabled_allows_high_risk_with_warning(self):
        """When HITL is disabled, high-risk operations should be allowed with warning"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = False

        # Should not block when HITL is disabled
        is_valid, violation = validator.validate_command('DROP TABLE users;')
        # Note: The current implementation still returns valid when HITL is disabled
        # This is intentional - the operation is logged but not blocked
        assert is_valid is True or violation is None or not violation.requires_approval


class TestIntegratedTaskValidation:
    """Test integrated task validation with all security checks"""

    def test_task_with_sensitive_file_fails(self):
        """Task validation should fail when accessing sensitive files"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']

        # Use secrets.yaml which is in the minimal blocklist
        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            file_paths=['secrets.yaml', 'src/main.py']
        )
        assert is_valid is False
        assert len(violations) > 0
        # Should have sensitive file violation
        sensitive_violations = [v for v in violations if v.rule_type == 'sensitive_file']
        assert len(sensitive_violations) > 0

    def test_task_with_high_risk_command_fails(self):
        """Task validation should fail when using high-risk commands"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']
        validator.require_hitl_for_high_risk = True

        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            command='DROP TABLE users;'
        )
        assert is_valid is False
        assert len(violations) > 0
        # Should have high-risk violation
        high_risk_violations = [v for v in violations if v.rule_type == 'high_risk']
        assert len(high_risk_violations) > 0

    def test_safe_task_passes_all_validations(self):
        """Safe task should pass all validations"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']
        validator.allowed_actions = list(DEFAULT_ALLOWED_ACTIONS)

        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            file_paths=['docs/README.md', 'docs/API.md'],
            action='write_file',
            command='git status'
        )
        assert is_valid is True
        assert len(violations) == 0


class TestPathTraversalPrevention:
    """Test path traversal prevention"""

    def test_path_traversal_is_blocked(self):
        """Should block path traversal attempts"""
        validator = SemanticRulesValidator()

        normalized, is_safe = validator.normalize_path('../../../etc/passwd')
        assert is_safe is False

    def test_double_dot_in_path_is_blocked(self):
        """Should block double dot in path"""
        validator = SemanticRulesValidator()

        normalized, is_safe = validator.normalize_path('src/../../../etc/passwd')
        assert is_safe is False

    def test_normal_path_is_allowed(self):
        """Should allow normal paths"""
        validator = SemanticRulesValidator()

        normalized, is_safe = validator.normalize_path('src/main.py')
        assert is_safe is True


class TestAgentSelfDiagnosis:
    """Test Agent self-diagnosis scenarios (E2E)"""

    def test_happy_path_safe_documentation_task(self):
        """Happy path: Safe documentation update task should succeed"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']

        # Simulate a safe documentation update task
        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            file_paths=['docs/README.md'],
            action='write_file'
        )

        assert is_valid is True
        assert len(violations) == 0

    def test_failure_path_unauthorized_repo(self):
        """Failure path: Unauthorized repo should be blocked"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']

        is_valid, violations = validator.validate_task(
            repo='malicious/repo',
            task_type='documentation_update'
        )

        assert is_valid is False
        repo_violations = [v for v in violations if v.rule_type == 'repo']
        assert len(repo_violations) > 0

    def test_failure_path_sensitive_file_access(self):
        """Failure path: Sensitive file access should be blocked"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']

        # Use secrets.yaml which is in the minimal blocklist
        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            file_paths=['secrets.yaml']
        )

        assert is_valid is False
        sensitive_violations = [v for v in violations if v.rule_type == 'sensitive_file']
        assert len(sensitive_violations) > 0

    def test_failure_path_high_risk_operation(self):
        """Failure path: High-risk operation should be blocked"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']
        validator.require_hitl_for_high_risk = True

        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            command='rm -rf /'
        )

        assert is_valid is False
        high_risk_violations = [v for v in violations if v.rule_type == 'high_risk']
        assert len(high_risk_violations) > 0
        # Should require HITL approval
        assert any(v.requires_approval for v in high_risk_violations)

    def test_rollback_scenario_no_partial_damage(self):
        """Rollback scenario: Security violation should prevent any changes"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ['RC918/morningai']
        validator.allowed_task_types = ['documentation_update']
        validator.require_hitl_for_high_risk = True

        # Simulate a task that tries to:
        # 1. Modify a safe file (should be allowed)
        # 2. Then modify a sensitive file (should be blocked)
        # The entire task should fail, preventing any partial execution
        # Use secrets.yaml which is in the minimal blocklist

        is_valid, violations = validator.validate_task(
            repo='RC918/morningai',
            task_type='documentation_update',
            file_paths=['docs/README.md', 'secrets.yaml']  # Mix of safe and sensitive
        )

        # Task should fail due to sensitive file
        assert is_valid is False
        assert len(violations) > 0

        # Verify the sensitive file violation is present
        sensitive_violations = [v for v in violations if v.rule_type == 'sensitive_file']
        assert len(sensitive_violations) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
