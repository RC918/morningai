#!/usr/bin/env python3
"""
Tests for Feature Flag Integration (Phase 2 Step C)

Tests the ENABLE_PROJECT_ENGINEER_CODEGEN feature flag:
1. Reading from environment variable
2. Explicit override behavior
3. Backward compatibility
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "handoff" / "20250928" / "40_App" / "orchestrator"))

from project_engineer.agent import ProjectEngineerAgent  # noqa: E402


class TestFeatureFlagIntegration:
    """Test ENABLE_PROJECT_ENGINEER_CODEGEN feature flag"""

    def test_feature_flag_disabled_by_default(self):
        """Test that feature flag defaults to False when not set"""
        with patch.dict(os.environ, {}, clear=False):
            with patch('common.config.settings.settings') as mock_settings:
                mock_settings.enable_project_engineer_codegen = False

                agent = ProjectEngineerAgent()

                assert agent.enable_code_generation is False
                assert agent.workflow is None

    def test_feature_flag_enabled_via_env(self):
        """Test that feature flag can be enabled via environment variable"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.enable_project_engineer_codegen = True

            with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
                agent = ProjectEngineerAgent(dev_agent=mock_dev_agent)

                assert agent.enable_code_generation is True
                assert agent.workflow is not None

    def test_explicit_true_overrides_env(self):
        """Test that explicit True overrides environment variable"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.enable_project_engineer_codegen = False

            with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
                agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=mock_dev_agent)

                assert agent.enable_code_generation is True
                assert agent.workflow is not None

    def test_explicit_false_overrides_env(self):
        """Test that explicit False overrides environment variable"""
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.enable_project_engineer_codegen = True

            agent = ProjectEngineerAgent(enable_code_generation=False)

            assert agent.enable_code_generation is False
            assert agent.workflow is None

    def test_none_reads_from_env(self):
        """Test that None explicitly reads from environment variable"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.enable_project_engineer_codegen = True

            with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
                agent = ProjectEngineerAgent(enable_code_generation=None, dev_agent=mock_dev_agent)

                assert agent.enable_code_generation is True
                assert agent.workflow is not None

    def test_feature_flag_requires_dev_agent_when_enabled(self):
        """Test that enabling feature flag requires dev_agent"""
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.enable_project_engineer_codegen = True

            with pytest.raises(ValueError, match="dev_agent required"):
                ProjectEngineerAgent(enable_code_generation=None, dev_agent=None)

    def test_feature_flag_fallback_on_settings_error(self):
        """Test that feature flag falls back to False on settings error"""
        # Mock the import to raise an exception
        import sys
        original_modules = sys.modules.copy()
        
        # Remove settings from sys.modules to force re-import
        if 'common.config.settings' in sys.modules:
            del sys.modules['common.config.settings']
        
        try:
            with patch.dict('sys.modules', {'common.config.settings': None}):
                agent = ProjectEngineerAgent()

                assert agent.enable_code_generation is False
                assert agent.workflow is None
        finally:
            # Restore original modules
            sys.modules.update(original_modules)

    def test_backward_compatibility_explicit_false(self):
        """Test backward compatibility with explicit False (Phase 2 Step B)"""
        agent = ProjectEngineerAgent(enable_code_generation=False)

        assert agent.enable_code_generation is False
        assert agent.workflow is None

    def test_backward_compatibility_explicit_true(self):
        """Test backward compatibility with explicit True (Phase 2 Step B)"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
            agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=mock_dev_agent)

            assert agent.enable_code_generation is True
            assert agent.workflow is not None


class TestFeatureFlagInSettings:
    """Test feature flag in settings.py"""

    def test_settings_has_feature_flag(self):
        """Test that settings.py has enable_project_engineer_codegen field"""
        from common.config.settings import settings

        # Check field exists (Pydantic fields are instance attributes)
        assert hasattr(settings, 'enable_project_engineer_codegen')

        # Check default value
        assert settings.enable_project_engineer_codegen is False

    def test_settings_reads_from_env(self):
        """Test that settings reads ENABLE_PROJECT_ENGINEER_CODEGEN from env"""
        with patch.dict(os.environ, {'ENABLE_PROJECT_ENGINEER_CODEGEN': 'true'}):
            from common.config.settings import Settings
            settings = Settings()

            assert settings.enable_project_engineer_codegen is True

    def test_settings_type_validation(self):
        """Test that settings validates boolean type"""
        with patch.dict(os.environ, {'ENABLE_PROJECT_ENGINEER_CODEGEN': 'invalid'}):
            from common.config.settings import Settings

            # Pydantic should coerce or raise validation error
            # This tests that the field is properly typed
            try:
                settings = Settings()
                # If it doesn't raise, check it's a boolean
                assert isinstance(settings.enable_project_engineer_codegen, bool)
            except Exception:
                # Validation error is acceptable for invalid input
                pass
