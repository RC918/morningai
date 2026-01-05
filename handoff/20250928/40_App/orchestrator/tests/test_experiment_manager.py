#!/usr/bin/env python3
"""
Unit tests for ExperimentManager module - Phase 5 PR-5
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiment_manager import (  # noqa: E402
    ExperimentManager,
    ExperimentConfig,
    EXPERIMENT_CONFIGS,
    get_experiment_manager,
    reset_experiment_manager,
    get_provider_for_component,
)


class TestExperimentConfig:
    """Tests for ExperimentConfig dataclass"""

    def test_create_experiment_config(self):
        """Test creating an experiment config"""
        config = ExperimentConfig(
            name="test_experiment",
            description="Test experiment",
            treatment_percent=50,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner"
        )

        assert config.name == "test_experiment"
        assert config.treatment_percent == 50
        assert config.enabled_environments == ["staging"]
        assert config.treatment_provider == "gemini"
        assert config.control_provider == "openai"
        assert config.target_component == "planner"
        assert config.enabled is True

    def test_predefined_configs_exist(self):
        """Test that predefined experiment configs exist"""
        assert "gemini_planner_10pct_staging" in EXPERIMENT_CONFIGS
        assert "gemini_reviewer_staging_only" in EXPERIMENT_CONFIGS

    def test_gemini_planner_config(self):
        """Test gemini_planner_10pct_staging config"""
        config = EXPERIMENT_CONFIGS["gemini_planner_10pct_staging"]
        assert config.treatment_percent == 10
        assert config.enabled_environments == ["staging"]
        assert config.treatment_provider == "gemini"
        assert config.control_provider == "openai"
        assert config.target_component == "planner"

    def test_gemini_reviewer_config(self):
        """Test gemini_reviewer_staging_only config"""
        config = EXPERIMENT_CONFIGS["gemini_reviewer_staging_only"]
        assert config.treatment_percent == 100
        assert config.enabled_environments == ["staging"]
        assert config.treatment_provider == "gemini"
        assert config.target_component == "reviewer"


class TestExperimentManagerInit:
    """Tests for ExperimentManager initialization"""

    def test_init_with_default_environment(self):
        """Test initialization with default production environment"""
        manager = ExperimentManager()
        assert manager.environment == "production"
        assert len(manager.experiments) > 0

    def test_init_with_staging_environment(self):
        """Test initialization with staging environment"""
        manager = ExperimentManager(environment="staging")
        assert manager.environment == "staging"

    def test_init_with_custom_experiments(self):
        """Test initialization with custom experiments"""
        custom_config = ExperimentConfig(
            name="custom_test",
            description="Custom test",
            treatment_percent=25,
            enabled_environments=["staging", "production"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner"
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"custom_test": custom_config}
        )
        assert "custom_test" in manager.experiments
        assert len(manager.experiments) == 1


class TestIsExperimentActive:
    """Tests for is_experiment_active method"""

    def test_experiment_active_in_staging(self):
        """Test experiment is active in staging (using test-specific experiment)"""
        # Create a test-specific experiment to avoid coupling to production config
        config = ExperimentConfig(
            name="test_active_experiment",
            description="Test active experiment",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_active_experiment": config}
        )
        assert manager.is_experiment_active("test_active_experiment") is True

    def test_experiment_inactive_in_production(self):
        """Test staging-only experiment is inactive in production"""
        manager = ExperimentManager(environment="production")
        assert manager.is_experiment_active("gemini3_planner_10pct_staging") is False

    def test_unknown_experiment_inactive(self):
        """Test unknown experiment returns False"""
        manager = ExperimentManager(environment="staging")
        assert manager.is_experiment_active("nonexistent_experiment") is False

    def test_disabled_experiment_inactive(self):
        """Test disabled experiment returns False"""
        config = ExperimentConfig(
            name="disabled_test",
            description="Disabled test",
            treatment_percent=50,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=False
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"disabled_test": config}
        )
        assert manager.is_experiment_active("disabled_test") is False

    def test_gemini3_experiment_disabled_by_kill_switch(self):
        """Test DISABLE_GEMINI3 kill switch disables Gemini 3 experiments (Phase 4)"""
        manager = ExperimentManager(environment="staging")

        # Mock settings with DISABLE_GEMINI3=True
        mock_settings = MagicMock()
        mock_settings.disable_gemini3 = True

        with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
            # Gemini 3 experiment should be disabled by kill switch
            assert manager.is_experiment_active("gemini3_planner_10pct_staging") is False
            assert manager.is_experiment_active("gemini3_reviewer_5pct_staging") is False

    def test_gemini3_experiment_active_without_kill_switch(self):
        """Test Gemini 3 experiment is active when kill switch is off (using test-specific experiment)"""
        # Create a test-specific Gemini 3 experiment to test kill switch behavior
        config = ExperimentConfig(
            name="test_gemini3_experiment",
            description="Test Gemini 3 experiment for kill switch",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True,
            treatment_model="gemini-3-pro-preview"  # Gemini 3 model
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_gemini3_experiment": config}
        )

        # Mock settings with DISABLE_GEMINI3=False
        mock_settings = MagicMock()
        mock_settings.disable_gemini3 = False

        with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
            # Gemini 3 experiment should be active when kill switch is off
            assert manager.is_experiment_active("test_gemini3_experiment") is True


class TestGetVariant:
    """Tests for get_variant method"""

    def test_get_variant_returns_control_when_inactive(self):
        """Test returns control when experiment is inactive"""
        manager = ExperimentManager(environment="production")
        variant = manager.get_variant("gemini_planner_10pct_staging", "trace-123")
        assert variant == "control"

    def test_get_variant_deterministic(self):
        """Test variant assignment is deterministic for same trace_id"""
        manager = ExperimentManager(environment="staging")
        trace_id = "test-trace-abc123"

        variant1 = manager.get_variant("gemini_planner_10pct_staging", trace_id)
        variant2 = manager.get_variant("gemini_planner_10pct_staging", trace_id)

        assert variant1 == variant2

    def test_get_variant_different_traces_can_differ(self):
        """Test different trace_ids can get different variants (using test-specific experiment)"""
        # Create a test-specific experiment to avoid coupling to production config
        config = ExperimentConfig(
            name="test_variant_experiment",
            description="Test variant distribution",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_variant_experiment": config}
        )

        variants = set()
        for i in range(100):
            variant = manager.get_variant("test_variant_experiment", f"trace-{i}")
            variants.add(variant)

        assert len(variants) == 2

    def test_get_variant_100_percent_treatment(self):
        """Test 100% treatment returns treatment for all (using custom enabled config)"""
        # Create a custom 100% treatment experiment since gemini_reviewer_staging_only is now disabled
        config = ExperimentConfig(
            name="test_100_percent",
            description="Test 100% treatment",
            treatment_percent=100,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="test"
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_100_percent": config}
        )

        for i in range(10):
            variant = manager.get_variant("test_100_percent", f"trace-{i}")
            assert variant == "treatment"

    def test_get_variant_0_percent_treatment(self):
        """Test 0% treatment returns control for all"""
        config = ExperimentConfig(
            name="zero_percent",
            description="Zero percent test",
            treatment_percent=0,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner"
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"zero_percent": config}
        )

        for i in range(10):
            variant = manager.get_variant("zero_percent", f"trace-{i}")
            assert variant == "control"

    def test_get_variant_caching(self):
        """Test variant assignment is cached (using test-specific experiment)"""
        # Create a test-specific experiment to avoid coupling to production config
        config = ExperimentConfig(
            name="test_caching_experiment",
            description="Test caching",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_caching_experiment": config}
        )
        trace_id = "cache-test-trace"

        manager.get_variant("test_caching_experiment", trace_id)

        cache_key = f"test_caching_experiment:{trace_id}"
        assert cache_key in manager._assignment_cache


class TestGetProviderForExperiment:
    """Tests for get_provider_for_experiment method"""

    def test_get_provider_control(self):
        """Test getting control provider"""
        manager = ExperimentManager(environment="production")
        provider = manager.get_provider_for_experiment(
            "gemini_planner_10pct_staging",
            "trace-123"
        )
        assert provider == "openai"

    def test_get_provider_treatment(self):
        """Test getting treatment provider for 100% experiment (using custom enabled config)"""
        # Create a custom 100% treatment experiment since gemini_reviewer_staging_only is now disabled
        config = ExperimentConfig(
            name="test_treatment_provider",
            description="Test treatment provider",
            treatment_percent=100,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="test"
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_treatment_provider": config}
        )
        provider = manager.get_provider_for_experiment(
            "test_treatment_provider",
            "trace-123"
        )
        assert provider == "gemini"

    def test_get_provider_unknown_experiment(self):
        """Test getting provider for unknown experiment returns openai"""
        manager = ExperimentManager(environment="staging")
        provider = manager.get_provider_for_experiment(
            "nonexistent_experiment",
            "trace-123"
        )
        assert provider == "openai"


class TestGetExperimentForComponent:
    """Tests for get_experiment_for_component method"""

    def test_get_experiment_for_planner(self):
        """Test getting experiment for planner component (using test-specific experiment)"""
        # Create a test-specific experiment to avoid coupling to production config
        config = ExperimentConfig(
            name="test_planner_experiment",
            description="Test planner experiment",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_planner_experiment": config}
        )
        result = manager.get_experiment_for_component("planner", "trace-123")

        assert result is not None
        assert result["experiment_name"] == "test_planner_experiment"
        assert result["component"] == "planner"
        assert result["variant"] in ["control", "treatment"]
        assert result["provider"] in ["openai", "gemini"]

    def test_get_experiment_for_reviewer(self):
        """Test getting experiment for reviewer component returns None (experiments disabled)"""
        # Both gemini_reviewer_staging_only and gemini3_reviewer_5pct_staging are now disabled
        # because LLMReviewerAdapter uses task-based routing via RoutingEngine
        manager = ExperimentManager(environment="staging")
        result = manager.get_experiment_for_component("reviewer", "trace-123")

        # No active experiment for reviewer component
        assert result is None

    def test_get_experiment_for_unknown_component(self):
        """Test getting experiment for unknown component returns None"""
        manager = ExperimentManager(environment="staging")
        result = manager.get_experiment_for_component("unknown_component", "trace-123")
        assert result is None

    def test_get_experiment_inactive_in_production(self):
        """Test no experiment returned in production"""
        manager = ExperimentManager(environment="production")
        result = manager.get_experiment_for_component("planner", "trace-123")
        assert result is None


class TestGetMetricsLabels:
    """Tests for get_metrics_labels method"""

    def test_get_metrics_labels(self):
        """Test getting metrics labels"""
        manager = ExperimentManager(environment="staging")
        labels = manager.get_metrics_labels("gemini_planner_10pct_staging", "trace-123")

        assert "experiment_name" in labels
        assert "variant" in labels
        assert "environment" in labels
        assert labels["experiment_name"] == "gemini_planner_10pct_staging"
        assert labels["variant"] in ["control", "treatment"]
        assert labels["environment"] == "staging"


class TestRegisterExperiment:
    """Tests for register_experiment method"""

    def test_register_new_experiment(self):
        """Test registering a new experiment"""
        manager = ExperimentManager(environment="staging")
        initial_count = len(manager.experiments)

        new_config = ExperimentConfig(
            name="new_experiment",
            description="New experiment",
            treatment_percent=50,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="executor"
        )
        manager.register_experiment(new_config)

        assert len(manager.experiments) == initial_count + 1
        assert "new_experiment" in manager.experiments


class TestListActiveExperiments:
    """Tests for list_active_experiments method"""

    def test_list_active_experiments_staging(self):
        """Test listing active experiments in staging (using test-specific experiment)"""
        # Create test-specific experiments to avoid coupling to production config
        enabled_config = ExperimentConfig(
            name="test_enabled_experiment",
            description="Test enabled experiment",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True
        )
        disabled_config = ExperimentConfig(
            name="test_disabled_experiment",
            description="Test disabled experiment",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="reviewer",
            enabled=False
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={
                "test_enabled_experiment": enabled_config,
                "test_disabled_experiment": disabled_config
            }
        )
        active = manager.list_active_experiments()

        # Only enabled experiment should be in active list
        assert "test_enabled_experiment" in active
        assert "test_disabled_experiment" not in active

    def test_list_active_experiments_production(self):
        """Test listing active experiments in production (should be empty)"""
        manager = ExperimentManager(environment="production")
        active = manager.list_active_experiments()

        assert len(active) == 0


class TestGetExperimentSummary:
    """Tests for get_experiment_summary method"""

    def test_get_experiment_summary(self):
        """Test getting experiment summary"""
        manager = ExperimentManager(environment="staging")
        summary = manager.get_experiment_summary()

        assert "environment" in summary
        assert "total_experiments" in summary
        assert "active_experiments" in summary
        assert "experiments" in summary
        assert summary["environment"] == "staging"
        assert summary["total_experiments"] >= 2


class TestGlobalExperimentManager:
    """Tests for global experiment manager functions"""

    def test_get_experiment_manager_creates_instance(self):
        """Test get_experiment_manager creates instance with correct environment"""
        reset_experiment_manager()

        with patch("experiment_manager.ExperimentManager") as mock_manager_class:
            manager = get_experiment_manager(environment="test")
            mock_manager_class.assert_called_once_with(environment="test")
            assert manager is not None

    def test_get_experiment_manager_from_settings(self):
        """Test get_experiment_manager reads environment from settings.environment"""
        reset_experiment_manager()

        with patch("experiment_manager.ExperimentManager") as mock_manager_class:
            mock_settings = MagicMock()
            mock_settings.environment = "staging"

            with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
                get_experiment_manager()
                mock_manager_class.assert_called_once_with(environment="staging")

    def test_reset_experiment_manager(self):
        """Test reset_experiment_manager clears instance"""
        reset_experiment_manager()

    def test_get_provider_for_component_staging(self):
        """Test get_provider_for_component in staging"""
        reset_experiment_manager()

        with patch("experiment_manager._experiment_manager", None):
            with patch("experiment_manager.get_experiment_manager") as mock_get:
                mock_manager = MagicMock()
                mock_manager.get_experiment_for_component.return_value = {
                    "provider": "gemini"
                }
                mock_get.return_value = mock_manager

                provider = get_provider_for_component("reviewer", "trace-123")
                assert provider == "gemini"

    def test_get_provider_for_component_no_experiment(self):
        """Test get_provider_for_component returns default when no experiment"""
        reset_experiment_manager()

        with patch("experiment_manager._experiment_manager", None):
            with patch("experiment_manager.get_experiment_manager") as mock_get:
                mock_manager = MagicMock()
                mock_manager.get_experiment_for_component.return_value = None
                mock_get.return_value = mock_manager

                provider = get_provider_for_component(
                    "unknown",
                    "trace-123",
                    default_provider="openai"
                )
                assert provider == "openai"


class TestExperimentDistribution:
    """Tests for experiment distribution accuracy"""

    def test_25_percent_distribution(self):
        """Test 25% treatment distribution is approximately correct (using test-specific experiment)"""
        # Create a test-specific experiment to avoid coupling to production config
        config = ExperimentConfig(
            name="test_distribution_experiment",
            description="Test distribution accuracy",
            treatment_percent=25,
            enabled_environments=["staging"],
            treatment_provider="gemini",
            control_provider="openai",
            target_component="planner",
            enabled=True
        )
        manager = ExperimentManager(
            environment="staging",
            experiments={"test_distribution_experiment": config}
        )

        treatment_count = 0
        total = 1000

        for i in range(total):
            variant = manager.get_variant("test_distribution_experiment", f"dist-test-{i}")
            if variant == "treatment":
                treatment_count += 1

        treatment_rate = treatment_count / total * 100
        # 25% treatment rate should be within 20-30% range
        assert 20 <= treatment_rate <= 30
