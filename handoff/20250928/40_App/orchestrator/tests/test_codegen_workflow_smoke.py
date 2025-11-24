#!/usr/bin/env python3
"""
Smoke tests for Code Generation Workflow - P0 Missing Tests
Phase 0-Lite Supplement: Basic smoke tests for CodeGenerationWorkflow

Note: These are smoke tests focusing on initialization, classification, and security validation.
Full integration tests are deferred to P1/P2 as CodeGen workflow is currently disabled (USE_CODEGEN_WORKFLOW_PERCENT=0).
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow, CodeGenState
from agents.dev_agent.workflows.task_classifier import TaskType


class TestCodeGenerationWorkflowInitialization:
    """Test CodeGenerationWorkflow initialization"""
    
    def test_init_creates_workflow(self):
        """Test that initialization creates workflow components"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            assert workflow.agent == mock_dev_agent
            assert hasattr(workflow, 'classifier')
            assert hasattr(workflow, 'test_generator')
            assert hasattr(workflow, 'workflow')
            assert hasattr(workflow, 'repo_root')
    
    def test_init_creates_task_classifier(self):
        """Test that initialization creates TaskClassifier instance"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            assert workflow.classifier is not None
            assert hasattr(workflow.classifier, 'classify')
    
    def test_init_creates_test_generator(self):
        """Test that initialization creates LLMTestGenerator instance"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            assert workflow.test_generator is not None
    
    def test_init_sets_repo_root(self):
        """Test that initialization sets repo_root correctly"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            assert workflow.repo_root is not None
            assert isinstance(workflow.repo_root, str)


class TestCodeGenerationWorkflowSecurityValidation:
    """Test security validation (_is_safe_file_path)"""
    
    def test_is_safe_file_path_valid_python(self):
        """Test that valid Python files are accepted"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            valid_paths = [
                "src/utils.py",
                "lib/helpers.py",
                "tests/test_utils.py",
                "app/models/user.py"
            ]
            
            for path in valid_paths:
                assert workflow._is_safe_file_path(path) is True, f"Failed for: {path}"
    
    def test_is_safe_file_path_valid_javascript(self):
        """Test that valid JavaScript/TypeScript files are accepted"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            valid_paths = [
                "src/components/Button.jsx",
                "src/components/Card.tsx",
                "lib/utils.js",
                "tests/unit.test.ts"
            ]
            
            for path in valid_paths:
                assert workflow._is_safe_file_path(path) is True, f"Failed for: {path}"
    
    def test_is_safe_file_path_rejects_path_traversal(self):
        """Test that path traversal attempts are rejected"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            traversal_paths = [
                "../utils.py",
                "../../lib/helpers.py",
                "src/../../../etc/passwd",
                "./../../sensitive.py"
            ]
            
            for path in traversal_paths:
                assert workflow._is_safe_file_path(path) is False, f"Should reject: {path}"
    
    def test_is_safe_file_path_allows_relative_safe_paths(self):
        """Test that safe relative paths within project are allowed"""
        mock_dev_agent = MagicMock()
        
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"
            
            workflow = CodeGenerationWorkflow(mock_dev_agent)
            
            safe_paths = [
                "src/utils.py",
                "lib/helpers.py",
                "app/models/user.py",
                "tests/test_integration.py"
            ]
            
            for path in safe_paths:
                assert workflow._is_safe_file_path(path) is True, f"Should allow: {path}"


class TestCodeGenerationWorkflowDangerousPatterns:
    """Test dangerous pattern detection in security validation"""
    
    def test_dangerous_patterns_defined(self):
        """Test that dangerous patterns are defined"""
        assert hasattr(CodeGenerationWorkflow, 'DANGEROUS_PATTERNS')
        assert isinstance(CodeGenerationWorkflow.DANGEROUS_PATTERNS, list)
        assert len(CodeGenerationWorkflow.DANGEROUS_PATTERNS) > 0
    
    def test_dangerous_patterns_include_eval(self):
        """Test that dangerous patterns include eval/exec"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS
        
        # Check for eval/exec patterns
        has_eval = any('eval' in pattern for pattern in patterns)
        has_exec = any('exec' in pattern for pattern in patterns)
        
        assert has_eval, "Should include eval pattern"
        assert has_exec, "Should include exec pattern"
    
    def test_dangerous_patterns_include_system_calls(self):
        """Test that dangerous patterns include system calls"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS
        
        # Check for system call patterns
        has_os_system = any('os.system' in pattern or 'os\\.system' in pattern for pattern in patterns)
        has_subprocess = any('subprocess' in pattern for pattern in patterns)
        
        assert has_os_system or has_subprocess, "Should include system call patterns"
    
    def test_dangerous_patterns_include_sql_injection(self):
        """Test that dangerous patterns include SQL injection risks"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS
        
        # Check for SQL injection patterns
        has_drop = any('DROP' in pattern for pattern in patterns)
        has_delete = any('DELETE' in pattern for pattern in patterns)
        
        assert has_drop or has_delete, "Should include SQL injection patterns"


class TestCodeGenerationWorkflowStateStructure:
    """Test CodeGenState structure"""
    
    def test_codegen_state_has_required_fields(self):
        """Test that CodeGenState has all required fields"""
        required_fields = [
            'task_id',
            'task_title',
            'task_description',
            'task_type',
            'task_metadata',
            'target_files',
            'generated_code',
            'generated_tests',
            'code_diff',
            'test_results',
            'pr_number',
            'pr_url',
            'error',
            'execution_start',
            'file_backups',
            'security_validated'
        ]
        
        # Get annotations from CodeGenState
        annotations = CodeGenState.__annotations__
        
        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
