#!/usr/bin/env python3
"""
Unit tests for Semantic Rules v2 - Phase 4 PR-1

Tests for:
- Path normalization and traversal prevention
- Directory validation
- Task type validation
- Repository validation
- Full task validation
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add project_engineer to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from semantic_rules import (
    SemanticRulesValidator,
    SemanticRuleViolation,
    normalize_path,
    validate_directory,
    validate_task_type,
    validate_repo,
    validate_task,
    validate_action,
    validate_sensitive_file,
    validate_command,
    get_validator,
    HIGH_RISK_ACTIONS,
    SENSITIVE_FILE_PATTERNS,
    DEFAULT_ALLOWED_ACTIONS,
)


class TestPathNormalization:
    """Test path normalization and traversal detection"""

    def test_normalize_simple_path(self):
        """Should normalize simple paths correctly"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs/README.md")
        assert is_safe is True
        assert normalized == "docs/README.md"

    def test_normalize_path_with_leading_slash(self):
        """Should remove leading slash"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("/docs/README.md")
        assert is_safe is True
        assert normalized == "docs/README.md"

    def test_detect_double_dot_traversal(self):
        """Should detect .. traversal attempts"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("../etc/passwd")
        assert is_safe is False

    def test_detect_double_dot_in_middle(self):
        """Should detect .. in middle of path"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs/../../../etc/passwd")
        assert is_safe is False

    def test_detect_dot_slash(self):
        """Should detect ./ patterns"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("./docs/README.md")
        assert is_safe is False

    def test_detect_url_encoded_traversal(self):
        """Should detect URL-encoded traversal"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs%2f..%2f..%2fetc")
        assert is_safe is False

    def test_detect_backslash(self):
        """Should detect backslash (Windows path)"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs\\..\\etc")
        assert is_safe is False

    def test_detect_multiple_slashes(self):
        """Should detect multiple consecutive slashes"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs//README.md")
        assert is_safe is False

    def test_empty_path(self):
        """Should handle empty path"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("")
        assert is_safe is True
        assert normalized == ""

    def test_whitespace_path(self):
        """Should handle whitespace path"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("  docs/README.md  ")
        assert is_safe is True
        assert normalized == "docs/README.md"


class TestDirectoryValidation:
    """Test directory validation"""

    def test_validate_allowed_directory(self):
        """Should allow paths in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/", "tests/"]
        
        is_valid, violation = validator.validate_directory("docs/README.md")
        assert is_valid is True
        assert violation is None

    def test_validate_disallowed_directory(self):
        """Should reject paths not in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/", "tests/"]
        
        is_valid, violation = validator.validate_directory("src/main.py")
        assert is_valid is False
        assert violation is not None
        assert violation.rule_type == "directory"

    def test_validate_nested_allowed_directory(self):
        """Should allow nested paths in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/"]
        
        is_valid, violation = validator.validate_directory("docs/api/endpoints.md")
        assert is_valid is True

    def test_validate_empty_allowed_directories(self):
        """Should allow all paths when allowed_directories is empty"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = []
        
        is_valid, violation = validator.validate_directory("any/path/file.py")
        assert is_valid is True

    def test_validate_traversal_in_directory(self):
        """Should reject paths with traversal even in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/"]
        
        is_valid, violation = validator.validate_directory("docs/../etc/passwd")
        assert is_valid is False
        assert violation.rule_type == "path_traversal"


class TestTaskTypeValidation:
    """Test task type validation"""

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_safe_task_type(self, mock_load):
        """Should allow safe task types when allowed_task_types is empty"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = []
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        with patch.object(validator, 'validate_task_type', wraps=validator.validate_task_type):
            # Mock the is_safe_task import inside the method
            with patch('project_engineer.safe_tasks.is_safe_task', return_value=True):
                is_valid, violation = validator.validate_task_type("documentation_update")
                assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_unsafe_task_type(self, mock_load):
        """Should reject unsafe task types"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = []
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        with patch('project_engineer.safe_tasks.is_safe_task', return_value=False):
            is_valid, violation = validator.validate_task_type("refactor")
            assert is_valid is False
            assert violation.rule_type == "task_type"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_explicit_allowed_task_type(self, mock_load):
        """Should allow explicitly allowed task types"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = ["documentation_update", "test_generation"]
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        is_valid, violation = validator.validate_task_type("documentation_update")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_not_in_explicit_allowed_task_types(self, mock_load):
        """Should reject task types not in explicit allowed list"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = ["documentation_update"]
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        is_valid, violation = validator.validate_task_type("test_generation")
        assert is_valid is False
        assert violation.rule_type == "task_type"


class TestRepoValidation:
    """Test repository validation"""

    def test_validate_allowed_repo(self):
        """Should allow repos in allowed list"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        
        is_valid, violation = validator.validate_repo("RC918/morningai")
        assert is_valid is True

    def test_validate_disallowed_repo(self):
        """Should reject repos not in allowed list"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        
        is_valid, violation = validator.validate_repo("other/repo")
        assert is_valid is False
        assert violation.rule_type == "repo"

    def test_validate_empty_allowed_repos(self):
        """Should allow all repos when allowed_repos is empty"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = []
        
        is_valid, violation = validator.validate_repo("any/repo")
        assert is_valid is True


class TestFullTaskValidation:
    """Test full task validation"""

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_valid_task(self, mock_load):
        """Should validate a fully valid task"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        validator.allowed_directories = ["docs/"]
        validator.allowed_task_types = []
        # Phase 1 Security Foundation attributes
        validator.allowed_actions = []
        validator.blocked_file_patterns = []
        validator.require_hitl_for_high_risk = False
        
        with patch('project_engineer.safe_tasks.is_safe_task', return_value=True):
            is_valid, violations = validator.validate_task(
                repo="RC918/morningai",
                task_type="documentation_update",
                file_paths=["docs/README.md"]
            )
            assert is_valid is True
            assert len(violations) == 0

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_task_with_multiple_violations(self, mock_load):
        """Should collect multiple violations"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        validator.allowed_directories = ["docs/"]
        validator.allowed_task_types = ["documentation_update"]
        # Phase 1 Security Foundation attributes
        validator.allowed_actions = []
        validator.blocked_file_patterns = []
        validator.require_hitl_for_high_risk = False
        
        is_valid, violations = validator.validate_task(
            repo="other/repo",
            task_type="refactor",
            file_paths=["src/main.py", "../etc/passwd"]
        )
        assert is_valid is False
        # Should have violations for: repo, task_type, directory (src/), path_traversal (../)
        assert len(violations) >= 3


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_normalize_path_function(self):
        """Test normalize_path convenience function"""
        normalized, is_safe = normalize_path("docs/README.md")
        assert is_safe is True
        assert normalized == "docs/README.md"

    def test_validate_directory_function(self):
        """Test validate_directory convenience function"""
        # This will use default settings
        is_valid, error = validate_directory("docs/README.md")
        assert is_valid is True

    def test_validate_repo_function(self):
        """Test validate_repo convenience function"""
        # This will use default settings (RC918/morningai allowed)
        is_valid, error = validate_repo("RC918/morningai")
        assert is_valid is True

    def test_get_validator_singleton(self):
        """Test that get_validator returns same instance"""
        validator1 = get_validator()
        validator2 = get_validator()
        assert validator1 is validator2


class TestSemanticRuleViolation:
    """Test SemanticRuleViolation dataclass"""

    def test_violation_creation(self):
        """Should create violation with all fields"""
        violation = SemanticRuleViolation(
            rule_type="directory",
            message="File not in allowed directory",
            severity="error",
            details="Allowed: docs/, tests/"
        )
        assert violation.rule_type == "directory"
        assert violation.message == "File not in allowed directory"
        assert violation.severity == "error"
        assert violation.details == "Allowed: docs/, tests/"

    def test_violation_optional_details(self):
        """Should allow optional details"""
        violation = SemanticRuleViolation(
            rule_type="repo",
            message="Repo not allowed",
            severity="error"
        )
        assert violation.details is None


class TestActionValidation:
    """Test action validation (Phase 1 Security Foundation)"""

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_allowed_action(self, mock_load):
        """Should allow actions in default whitelist"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = []
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_action("read_file")
        assert is_valid is True
        assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_disallowed_action(self, mock_load):
        """Should reject actions not in whitelist"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = []
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_action("execute_arbitrary_code")
        assert is_valid is False
        assert violation is not None
        assert violation.rule_type == "action"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_high_risk_action_requires_approval(self, mock_load):
        """Should require HITL approval for high-risk actions"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = []
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_action("rm -rf /tmp/test")
        assert is_valid is False
        assert violation is not None
        assert violation.rule_type == "high_risk"
        assert violation.requires_approval is True
        assert violation.severity == "critical"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_high_risk_action_allowed_when_hitl_disabled(self, mock_load):
        """Should allow high-risk actions when HITL is disabled"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = list(DEFAULT_ALLOWED_ACTIONS) + ["rm -rf"]
        validator.require_hitl_for_high_risk = False
        
        # When HITL is disabled, high-risk check passes but action must be in whitelist
        is_valid, violation = validator.validate_action("rm -rf")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_explicit_allowed_actions(self, mock_load):
        """Should allow explicitly configured actions"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = ["custom_action", "another_action"]
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_action("custom_action")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_drop_table_high_risk(self, mock_load):
        """Should detect DROP TABLE as high-risk"""
        validator = SemanticRulesValidator()
        validator.allowed_actions = []
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_action("DROP TABLE users")
        assert is_valid is False
        assert violation.rule_type == "high_risk"

    def test_high_risk_actions_constant(self):
        """Should have expected high-risk actions defined"""
        assert "DROP TABLE" in HIGH_RISK_ACTIONS
        assert "rm -rf" in HIGH_RISK_ACTIONS
        assert "sudo rm" in HIGH_RISK_ACTIONS
        assert "chmod 777" in HIGH_RISK_ACTIONS

    def test_default_allowed_actions_constant(self):
        """Should have expected default allowed actions"""
        assert "read_file" in DEFAULT_ALLOWED_ACTIONS
        assert "write_file" in DEFAULT_ALLOWED_ACTIONS
        assert "run_tests" in DEFAULT_ALLOWED_ACTIONS
        assert "create_pr" in DEFAULT_ALLOWED_ACTIONS


class TestSensitiveFileValidation:
    """Test sensitive file validation (Phase 1 Security Foundation)
    
    Note: The minimal blocklist only includes files that should NEVER be modified:
    - Private keys and certificates
    - Explicit secrets files (secrets.yaml, secrets.yml)
    - Package manager auth tokens (.npmrc, .pypirc)
    
    Files like .env, deployment configs, and cloud credentials are NOT blocked
    to allow Agent flexibility in modifying configuration files.
    """

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_normal_file(self, mock_load):
        """Should allow normal files"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("src/main.py")
        assert is_valid is True
        assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_env_file_allowed(self, mock_load):
        """Should allow .env files (not in minimal blocklist)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file(".env")
        assert is_valid is True
        assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_deployment_config_allowed(self, mock_load):
        """Should allow deployment config files (not in minimal blocklist)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # These are now allowed for Agent modification
        is_valid, violation = validator.validate_sensitive_file("fly.toml")
        assert is_valid is True
        
        is_valid, violation = validator.validate_sensitive_file("docker-compose.yml")
        assert is_valid is True
        
        is_valid, violation = validator.validate_sensitive_file("render.yaml")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_private_key_blocked(self, mock_load):
        """Should block private key files"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("id_rsa")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_pem_file_blocked(self, mock_load):
        """Should block .pem files"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("server.pem")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_secrets_yaml_blocked(self, mock_load):
        """Should block secrets.yaml files"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("k8s/secrets.yaml")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_npmrc_blocked(self, mock_load):
        """Should block .npmrc files (contains auth tokens)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file(".npmrc")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_empty_path(self, mock_load):
        """Should allow empty path"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_path_traversal_in_sensitive_file(self, mock_load):
        """Should detect path traversal in sensitive file validation"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("../../../etc/passwd")
        assert is_valid is False
        assert violation.rule_type == "path_traversal"

    def test_sensitive_file_patterns_constant(self):
        """Should have expected sensitive file patterns defined (minimal blocklist)"""
        # Private keys and certificates (MUST be blocked)
        assert "private_key" in SENSITIVE_FILE_PATTERNS
        assert "id_rsa" in SENSITIVE_FILE_PATTERNS
        assert "id_ed25519" in SENSITIVE_FILE_PATTERNS
        assert ".pem" in SENSITIVE_FILE_PATTERNS
        assert ".key" in SENSITIVE_FILE_PATTERNS
        assert ".p12" in SENSITIVE_FILE_PATTERNS
        assert ".pfx" in SENSITIVE_FILE_PATTERNS
        # Explicit secrets files (MUST be blocked)
        assert "secrets.yaml" in SENSITIVE_FILE_PATTERNS
        assert "secrets.yml" in SENSITIVE_FILE_PATTERNS
        # Package manager auth tokens (MUST be blocked)
        assert ".npmrc" in SENSITIVE_FILE_PATTERNS
        assert ".pypirc" in SENSITIVE_FILE_PATTERNS
        
    def test_files_not_in_minimal_blocklist(self):
        """Verify files that should NOT be in minimal blocklist"""
        # Environment files - Agent can modify
        assert ".env" not in SENSITIVE_FILE_PATTERNS
        assert ".env.local" not in SENSITIVE_FILE_PATTERNS
        # Deployment configs - Agent can modify
        assert "fly.toml" not in SENSITIVE_FILE_PATTERNS
        assert "render.yaml" not in SENSITIVE_FILE_PATTERNS
        assert "vercel.json" not in SENSITIVE_FILE_PATTERNS
        assert "docker-compose.yml" not in SENSITIVE_FILE_PATTERNS
        # Cloud credentials - Agent can read (not blocked)
        assert ".aws/credentials" not in SENSITIVE_FILE_PATTERNS
        assert "kubeconfig" not in SENSITIVE_FILE_PATTERNS


class TestMinimalBlocklistBehavior:
    """Test minimal blocklist behavior (PR #1943 revision)
    
    The minimal blocklist only blocks files that should NEVER be modified:
    - Private keys and certificates
    - Explicit secrets files (secrets.yaml, secrets.yml)
    - Package manager auth tokens (.npmrc, .pypirc)
    
    Deployment configs, .env files, and cloud credentials are NOT blocked
    to allow Agent flexibility in modifying configuration files.
    """

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_private_key_files_blocked(self, mock_load):
        """Should block all private key file types"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # Test various private key patterns
        key_files = ["id_rsa", "id_ed25519", "server.pem", "cert.key", "auth.p12", "cert.pfx"]
        for key_file in key_files:
            is_valid, violation = validator.validate_sensitive_file(key_file)
            assert is_valid is False, f"Expected {key_file} to be blocked"
            assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_secrets_files_blocked(self, mock_load):
        """Should block explicit secrets files"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # secrets.yaml and secrets.yml should be blocked
        is_valid, violation = validator.validate_sensitive_file("k8s/secrets.yaml")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"
        
        is_valid, violation = validator.validate_sensitive_file("config/secrets.yml")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_package_manager_auth_blocked(self, mock_load):
        """Should block package manager auth token files"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # .npmrc and .pypirc contain auth tokens
        is_valid, violation = validator.validate_sensitive_file(".npmrc")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"
        
        is_valid, violation = validator.validate_sensitive_file(".pypirc")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_deployment_configs_allowed(self, mock_load):
        """Should allow deployment config files (not in minimal blocklist)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # All deployment configs should be allowed
        allowed_files = [
            "render.yaml", "vercel.json", "fly.toml",
            "docker-compose.yml", "docker-compose.yaml",
            "railway.json", "netlify.toml", "heroku.yml", "app.yaml"
        ]
        for config_file in allowed_files:
            is_valid, violation = validator.validate_sensitive_file(config_file)
            assert is_valid is True, f"Expected {config_file} to be allowed"
            assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_env_files_allowed(self, mock_load):
        """Should allow .env files (not in minimal blocklist)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # All .env files should be allowed
        env_files = [".env", ".env.local", ".env.production", ".env.staging", ".env.development"]
        for env_file in env_files:
            is_valid, violation = validator.validate_sensitive_file(env_file)
            assert is_valid is True, f"Expected {env_file} to be allowed"
            assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_cloud_credentials_allowed(self, mock_load):
        """Should allow cloud credential files (not in minimal blocklist)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # Cloud credentials are read-only in practice, but not blocked
        cloud_files = [
            ".aws/credentials",
            "application_default_credentials.json",
            ".kube/kubeconfig",
            "credentials.json"
        ]
        for cloud_file in cloud_files:
            is_valid, violation = validator.validate_sensitive_file(cloud_file)
            assert is_valid is True, f"Expected {cloud_file} to be allowed"
            assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_infrastructure_files_allowed(self, mock_load):
        """Should allow infrastructure-as-code files (not in minimal blocklist)"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        # IaC files should be allowed
        is_valid, violation = validator.validate_sensitive_file("terraform.tfvars")
        assert is_valid is True
        assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_private_key_in_subdirectory_blocked(self, mock_load):
        """Should block private keys even in subdirectories"""
        validator = SemanticRulesValidator()
        validator.blocked_file_patterns = list(SENSITIVE_FILE_PATTERNS)
        
        is_valid, violation = validator.validate_sensitive_file("ssh/id_rsa")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"
        
        is_valid, violation = validator.validate_sensitive_file("certs/server.pem")
        assert is_valid is False
        assert violation.rule_type == "sensitive_file"

    def test_minimal_blocklist_size(self):
        """Verify minimal blocklist has expected number of patterns"""
        # Minimal blocklist should have exactly 11 patterns:
        # 7 private key patterns + 2 secrets patterns + 2 package manager patterns
        assert len(SENSITIVE_FILE_PATTERNS) == 11


class TestCommandValidation:
    """Test command validation (Phase 1 Security Foundation)"""

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_safe_command(self, mock_load):
        """Should allow safe commands"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("ls -la")
        assert is_valid is True
        assert violation is None

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_rm_rf_command_blocked(self, mock_load):
        """Should block rm -rf commands"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("rm -rf /tmp/test")
        assert is_valid is False
        assert violation is not None
        assert violation.rule_type == "high_risk"
        assert violation.requires_approval is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_drop_table_command_blocked(self, mock_load):
        """Should block DROP TABLE commands"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("psql -c 'DROP TABLE users'")
        assert is_valid is False
        assert violation.rule_type == "high_risk"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_sudo_rm_command_blocked(self, mock_load):
        """Should block sudo rm commands"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("sudo rm -rf /var/log")
        assert is_valid is False
        assert violation.rule_type == "high_risk"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_chmod_777_command_blocked(self, mock_load):
        """Should block chmod 777 commands"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("chmod 777 /etc/passwd")
        assert is_valid is False
        assert violation.rule_type == "high_risk"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_truncate_command_blocked(self, mock_load):
        """Should block TRUNCATE commands"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("TRUNCATE TABLE logs")
        assert is_valid is False
        assert violation.rule_type == "high_risk"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_empty_command(self, mock_load):
        """Should allow empty command"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = True
        
        is_valid, violation = validator.validate_command("")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_high_risk_command_allowed_when_hitl_disabled(self, mock_load):
        """Should allow high-risk commands when HITL is disabled"""
        validator = SemanticRulesValidator()
        validator.require_hitl_for_high_risk = False
        
        is_valid, violation = validator.validate_command("rm -rf /tmp/test")
        assert is_valid is True


class TestConvenienceFunctionsPhase1:
    """Test Phase 1 Security Foundation convenience functions"""

    def test_validate_action_function(self):
        """Test validate_action convenience function"""
        is_valid, error = validate_action("read_file")
        assert is_valid is True

    def test_validate_sensitive_file_function(self):
        """Test validate_sensitive_file convenience function"""
        is_valid, error = validate_sensitive_file("src/main.py")
        assert is_valid is True

    def test_validate_command_function(self):
        """Test validate_command convenience function"""
        is_valid, error = validate_command("ls -la")
        assert is_valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
