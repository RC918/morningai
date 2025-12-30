"""
Tests for Meta Agent integration.

This module tests the Meta Agent feature flags and integration points
for end-to-end autonomous execution via AutonomousExecutor.

Issue: #1822 (Integrate Development Tools)
"""

import pytest
from unittest.mock import MagicMock, patch
import os


class TestMetaAgentFeatureFlags:
    """Tests for Meta Agent feature flag behavior."""

    def test_enable_meta_agent_default_false(self):
        """Test ENABLE_META_AGENT defaults to False."""
        from common.config.settings import Settings

        settings = Settings()
        assert settings.enable_meta_agent is False

    def test_enable_meta_agent_vm_default_false(self):
        """Test ENABLE_META_AGENT_VM defaults to False."""
        from common.config.settings import Settings

        settings = Settings()
        assert settings.enable_meta_agent_vm is False

    def test_meta_agent_vm_provider_default_local(self):
        """Test META_AGENT_VM_PROVIDER defaults to 'local'."""
        from common.config.settings import Settings

        settings = Settings()
        assert settings.meta_agent_vm_provider == "local"

    def test_enable_meta_agent_can_be_enabled(self):
        """Test ENABLE_META_AGENT can be enabled via environment."""
        with patch.dict(os.environ, {"ENABLE_META_AGENT": "true"}):
            from common.config.settings import Settings

            settings = Settings()
            assert settings.enable_meta_agent is True

    def test_meta_agent_vm_provider_can_be_set_to_docker(self):
        """Test META_AGENT_VM_PROVIDER can be set to 'docker'."""
        with patch.dict(os.environ, {"META_AGENT_VM_PROVIDER": "docker"}):
            from common.config.settings import Settings

            settings = Settings()
            assert settings.meta_agent_vm_provider == "docker"

    def test_meta_agent_vm_provider_can_be_set_to_fly(self):
        """Test META_AGENT_VM_PROVIDER can be set to 'fly'."""
        with patch.dict(os.environ, {"META_AGENT_VM_PROVIDER": "fly"}):
            from common.config.settings import Settings

            settings = Settings()
            assert settings.meta_agent_vm_provider == "fly"


class TestMetaAgentWorkerFunction:
    """Tests for run_meta_agent_task worker function existence and signature."""

    def test_run_meta_agent_task_exists(self):
        """Test that run_meta_agent_task function exists in worker module."""
        pytest.importorskip("rq")
        from redis_queue.worker import run_meta_agent_task

        assert callable(run_meta_agent_task)

    def test_run_meta_agent_task_has_correct_parameters(self):
        """Test that run_meta_agent_task has the expected parameters."""
        pytest.importorskip("rq")
        import inspect
        from redis_queue.worker import run_meta_agent_task

        sig = inspect.signature(run_meta_agent_task)
        params = list(sig.parameters.keys())

        assert "task_id" in params
        assert "goal_text" in params
        assert "repo" in params
        assert "tenant_id" in params
        assert "context" in params

    def test_run_meta_agent_task_context_has_default(self):
        """Test that context parameter has a default value."""
        pytest.importorskip("rq")
        import inspect
        from redis_queue.worker import run_meta_agent_task

        sig = inspect.signature(run_meta_agent_task)
        context_param = sig.parameters.get("context")

        assert context_param is not None
        assert context_param.default is None


@pytest.mark.xfail(reason="Pre-existing legacy debt #3251 - routes.webhooks import fails")
class TestWebhookMetaAgentRouting:
    """Tests for webhook Meta Agent routing functions."""

    def test_enqueue_meta_agent_task_exists(self):
        """Test that _enqueue_meta_agent_task function exists."""
        from routes.webhooks import _enqueue_meta_agent_task

        assert callable(_enqueue_meta_agent_task)

    def test_enqueue_task_checks_meta_agent_flag(self):
        """Test that _enqueue_task checks for Meta Agent flag."""
        import inspect
        from routes.webhooks import _enqueue_task

        source = inspect.getsource(_enqueue_task)

        assert "enable_meta_agent" in source
        assert "use_meta_agent" in source
        assert "_enqueue_meta_agent_task" in source

    def test_enqueue_meta_agent_task_handles_missing_redis_url(self):
        """Test that _enqueue_meta_agent_task handles missing Redis URL."""
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Test goal"
        mock_task.context = {"repo": "test/repo"}

        mock_settings = MagicMock()
        mock_settings.redis_url = None

        with patch("routes.webhooks.settings", mock_settings):
            from routes.webhooks import _enqueue_meta_agent_task

            result = _enqueue_meta_agent_task(mock_task)

            assert result is None

    def test_enqueue_task_uses_standard_path_when_meta_agent_disabled(self):
        """Test _enqueue_task uses standard path when Meta Agent disabled."""
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Test goal"
        mock_task.context = {"repo": "test/repo", "use_meta_agent": False}

        mock_settings = MagicMock()
        mock_settings.enable_meta_agent = False
        mock_settings.redis_url = None

        with patch("routes.webhooks.settings", mock_settings):
            from routes.webhooks import _enqueue_task

            result = _enqueue_task(mock_task)

            assert result is None


class TestMetaAgentIntegrationPoints:
    """Tests for Meta Agent integration with other components."""

    def test_autonomous_executor_can_be_imported(self):
        """Test that AutonomousExecutor can be imported."""
        from meta_agent.autonomous_executor import AutonomousExecutor

        assert AutonomousExecutor is not None

    def test_vm_provider_enum_exists(self):
        """Test that VMProvider enum exists with expected values."""
        from meta_agent.vm_provisioner import VMProvider

        assert hasattr(VMProvider, "LOCAL")
        assert hasattr(VMProvider, "DOCKER")
        assert hasattr(VMProvider, "FLY")

    def test_autonomous_executor_has_execute_goal_method(self):
        """Test that AutonomousExecutor has execute_goal method."""
        from meta_agent.autonomous_executor import AutonomousExecutor

        assert hasattr(AutonomousExecutor, "execute_goal")
        assert callable(getattr(AutonomousExecutor, "execute_goal"))

    def test_task_intake_service_exists(self):
        """Test that TaskIntakeService exists."""
        from webhooks.task_intake import TaskIntakeService

        assert TaskIntakeService is not None

    def test_task_intake_service_has_set_task_executor(self):
        """Test that TaskIntakeService has set_task_executor method."""
        from webhooks.task_intake import TaskIntakeService

        assert hasattr(TaskIntakeService, "set_task_executor")
        assert callable(getattr(TaskIntakeService, "set_task_executor"))
