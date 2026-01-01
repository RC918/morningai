"""
Unit tests for Routing Engine

EPIC #2594 - Ticket 2: Routing Policy v1.1

Tests cover:
- Tier enum and TaskType enum
- ModelInfo dataclass
- RoutingEngine.select_model() with various task types
- Risk level adjustments
- Context size handling
- Fallback mechanisms
- Provider availability filtering
"""
import pytest
from unittest.mock import patch

from core.routing import RoutingEngine, Tier, TaskType, ModelInfo
from governance.degradation_types import DegradationSeverity


class TestTierEnum:
    """Tests for Tier enum"""

    def test_tier_values(self):
        """Test that Tier enum has correct values"""
        assert Tier.TIER_0.value == 0
        assert Tier.TIER_1.value == 1
        assert Tier.TIER_2.value == 2
        assert Tier.TIER_3.value == 3

    def test_tier_ordering(self):
        """Test that tiers are ordered correctly (lower value = higher capability)"""
        assert Tier.TIER_0.value < Tier.TIER_1.value
        assert Tier.TIER_1.value < Tier.TIER_2.value
        assert Tier.TIER_2.value < Tier.TIER_3.value


class TestTaskTypeEnum:
    """Tests for TaskType enum"""

    def test_task_type_values(self):
        """Test that TaskType enum has correct values"""
        assert TaskType.PLANNING.value == "planning"
        assert TaskType.CODING.value == "coding"
        assert TaskType.REVIEW.value == "review"
        assert TaskType.UX_COPY.value == "ux_copy"
        assert TaskType.TRANSLATION.value == "translation"
        assert TaskType.SUMMARIZATION.value == "summarization"
        assert TaskType.ANALYSIS.value == "analysis"
        assert TaskType.CHAT.value == "chat"


class TestModelInfo:
    """Tests for ModelInfo dataclass"""

    def test_model_info_creation(self):
        """Test ModelInfo creation with required fields"""
        info = ModelInfo(
            model_name="qwen-max",
            provider="alicloud",
            tier=Tier.TIER_0
        )
        assert info.model_name == "qwen-max"
        assert info.provider == "alicloud"
        assert info.tier == Tier.TIER_0
        assert info.is_fallback is False
        assert info.reason == ""

    def test_model_info_with_optional_fields(self):
        """Test ModelInfo creation with optional fields"""
        info = ModelInfo(
            model_name="qwen-plus",
            provider="alicloud",
            tier=Tier.TIER_1,
            is_fallback=True,
            reason="Fallback due to unavailability"
        )
        assert info.is_fallback is True
        assert info.reason == "Fallback due to unavailability"


class TestRoutingEngineBasic:
    """Basic tests for RoutingEngine"""

    def test_engine_initialization(self):
        """Test RoutingEngine initialization"""
        engine = RoutingEngine()
        assert engine is not None

    def test_engine_with_available_providers(self):
        """Test RoutingEngine with specific available providers"""
        engine = RoutingEngine(available_providers=["alicloud", "openai"])
        assert engine._available_providers == ["alicloud", "openai"]

    def test_get_tier_for_task(self):
        """Test getting default tier for task types"""
        engine = RoutingEngine()

        assert engine.get_tier_for_task(TaskType.PLANNING) == Tier.TIER_0
        assert engine.get_tier_for_task(TaskType.CODING) == Tier.TIER_1
        assert engine.get_tier_for_task(TaskType.REVIEW) == Tier.TIER_1
        assert engine.get_tier_for_task(TaskType.UX_COPY) == Tier.TIER_3

    def test_get_models_for_tier(self):
        """Test getting models for a specific tier"""
        engine = RoutingEngine()

        tier_0_models = engine.get_models_for_tier(Tier.TIER_0)
        assert len(tier_0_models) > 0
        assert ("alicloud", "qwen-max") in tier_0_models

        tier_3_models = engine.get_models_for_tier(Tier.TIER_3)
        assert len(tier_3_models) > 0


class TestRoutingEngineSelectModel:
    """Tests for RoutingEngine.select_model()"""

    def test_planning_task_returns_tier_0_model(self):
        """Test that Planning Task returns Tier 0 model (qwen-max)"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model_info = engine.select_model(TaskType.PLANNING)

        assert model_info.tier == Tier.TIER_0
        assert model_info.model_name == "qwen-max"
        assert model_info.provider == "alicloud"

    def test_ux_copy_task_returns_tier_3_model(self):
        """Test that UX Copy Task returns Tier 3 model (qwen-14b)"""
        engine = RoutingEngine(available_providers=["siliconflow"])
        model_info = engine.select_model(TaskType.UX_COPY)

        assert model_info.tier == Tier.TIER_3
        assert model_info.provider == "siliconflow"
        assert "Qwen" in model_info.model_name

    def test_coding_task_returns_tier_1_model(self):
        """Test that Coding Task returns Tier 1 model"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model_info = engine.select_model(TaskType.CODING)

        assert model_info.tier == Tier.TIER_1
        assert model_info.model_name == "qwen-plus"

    def test_review_task_returns_tier_1_model(self):
        """Test that Review Task returns Tier 1 model"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model_info = engine.select_model(TaskType.REVIEW)

        assert model_info.tier == Tier.TIER_1
        assert model_info.model_name == "qwen-plus"


class TestRoutingEngineRiskLevel:
    """Tests for risk level adjustments"""

    def test_high_risk_upgrades_tier(self):
        """Test that high risk level upgrades to higher capability tier"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Coding is normally Tier 1, high risk should try Tier 0
        model_info = engine.select_model(TaskType.CODING, risk_level="high")

        # Should get Tier 0 model due to high risk
        assert model_info.tier == Tier.TIER_0
        assert model_info.model_name == "qwen-max"

    def test_low_risk_downgrades_tier(self):
        """Test that low risk level downgrades to lower capability tier"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # Coding is normally Tier 1, low risk should try Tier 2
        model_info = engine.select_model(TaskType.CODING, risk_level="low")

        # Should get Tier 2 model due to low risk
        assert model_info.tier == Tier.TIER_2

    def test_medium_risk_keeps_default_tier(self):
        """Test that medium risk level keeps default tier"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_info = engine.select_model(TaskType.CODING, risk_level="medium")

        # Should get default Tier 1 model
        assert model_info.tier == Tier.TIER_1


class TestRoutingEngineFallback:
    """Tests for fallback mechanisms"""

    def test_fallback_when_tier_unavailable(self):
        """Test fallback when preferred tier is unavailable"""
        # With Cross-Generation Fallback, SiliconFlow is now in Tier 0/1
        # So we test with a provider that's NOT in any tier
        engine = RoutingEngine(available_providers=["siliconflow"])

        # Planning wants Tier 0, SiliconFlow is now in Tier 0 (Cross-Gen Fallback)
        # So this is a direct selection, not a fallback
        model_info = engine.select_model(TaskType.PLANNING)

        # SiliconFlow is now a valid Tier 0 provider (Cross-Generation Fallback)
        assert model_info.provider == "siliconflow"
        assert model_info.tier == Tier.TIER_0

    def test_no_fallback_when_tier_available(self):
        """Test no fallback when preferred tier is available"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_info = engine.select_model(TaskType.PLANNING)

        assert model_info.is_fallback is False
        assert model_info.tier == Tier.TIER_0

    def test_error_when_no_provider_available(self):
        """Test error when no provider is available"""
        engine = RoutingEngine(available_providers=[])

        with pytest.raises(ValueError, match="No suitable model available"):
            engine.select_model(TaskType.PLANNING)


class TestRoutingEngineContextSize:
    """Tests for context size handling"""

    def test_small_context_keeps_tier(self):
        """Test that small context size keeps the default tier"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.UX_COPY, context_size=1000)

        # Small context should keep Tier 3
        assert model_info.tier == Tier.TIER_3

    def test_large_context_upgrades_tier(self):
        """Test that large context size upgrades to tier with larger context window"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Tier 3 has 8000 token limit, 10000 tokens should upgrade
        model_info = engine.select_model(TaskType.UX_COPY, context_size=10000)

        # Should upgrade to tier with larger context window
        assert model_info.tier.value < Tier.TIER_3.value


class TestRoutingEngineProviderPriority:
    """Tests for provider priority"""

    def test_alicloud_preferred_for_qwen(self):
        """Test that AliCloud is preferred for Qwen models when available"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # AliCloud should be preferred for Tier 0
        assert model_info.provider == "alicloud"
        assert model_info.model_name == "qwen-max"

    def test_siliconflow_used_when_alicloud_unavailable(self):
        """Test that SiliconFlow is used when AliCloud is unavailable (Cross-Generation Fallback)"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Cross-Generation Fallback: SiliconFlow (Qwen2.5) is the backup, not OpenAI
        assert model_info.provider == "siliconflow"
        assert "Qwen" in model_info.model_name


class TestRoutingEngineRegisterModel:
    """Tests for dynamic model registration"""

    def test_register_new_model(self):
        """Test registering a new model for a tier"""
        engine = RoutingEngine(available_providers=["custom"])

        engine.register_model(Tier.TIER_0, "custom", "custom-model-v1")

        tier_0_models = engine.get_models_for_tier(Tier.TIER_0)
        assert ("custom", "custom-model-v1") in tier_0_models

    def test_set_available_providers(self):
        """Test updating available providers"""
        engine = RoutingEngine(available_providers=["openai"])

        engine.set_available_providers(["alicloud", "siliconflow"])

        assert engine._available_providers == ["alicloud", "siliconflow"]


class TestRoutingEngineIntegration:
    """Integration tests for RoutingEngine with LLMClient"""

    @patch('llm.providers.alicloud_provider.settings')
    @patch('llm.providers.siliconflow_provider.settings')
    @patch('llm.providers.openai_provider.settings')
    @patch('llm.providers.gemini_provider.settings')
    def test_get_client_for_task_planning(
        self,
        mock_gemini_settings,
        mock_openai_settings,
        mock_siliconflow_settings,
        mock_alicloud_settings
    ):
        """Test get_client_for_task returns correct client for planning"""
        mock_alicloud_settings.dashscope_api_key = "test-key"
        mock_alicloud_settings.dashscope_base_url = "https://test.com"
        mock_siliconflow_settings.siliconflow_api_key = None
        mock_openai_settings.openai_api_key = None
        mock_gemini_settings.gemini_api_key = None

        from llm.client import get_client_for_task

        client = get_client_for_task(TaskType.PLANNING, risk_level="high")

        assert client.provider_name == "alicloud"

    @patch('llm.providers.alicloud_provider.settings')
    @patch('llm.providers.siliconflow_provider.settings')
    @patch('llm.providers.openai_provider.settings')
    @patch('llm.providers.gemini_provider.settings')
    def test_get_client_for_task_ux_copy(
        self,
        mock_gemini_settings,
        mock_openai_settings,
        mock_siliconflow_settings,
        mock_alicloud_settings
    ):
        """Test get_client_for_task returns correct client for UX copy"""
        mock_alicloud_settings.dashscope_api_key = None
        mock_siliconflow_settings.siliconflow_api_key = "test-key"
        mock_siliconflow_settings.siliconflow_base_url = "https://test.com"
        mock_openai_settings.openai_api_key = None
        mock_gemini_settings.gemini_api_key = None

        from llm.client import get_client_for_task

        client = get_client_for_task(TaskType.UX_COPY)

        assert client.provider_name == "siliconflow"


class TestRoutingEngineCandidateScoring:
    """Tests for candidate scoring and selection (Issue #2874)"""

    def test_score_candidate_default_weights(self):
        """Test _score_candidate with default weights (0.3 cost, 0.7 preference)"""
        engine = RoutingEngine()

        # alicloud: cost=0.5, preference=1.0
        # cost_score = 1.0 - 0.5 = 0.5
        # score = (1.0 * 0.7 + 0.5 * 0.3) / 1.0 = 0.85
        score = engine._score_candidate("alicloud", cost_weight=0.3, preference_weight=0.7)
        assert 0.84 <= score <= 0.86  # Allow small floating point variance

    def test_score_candidate_cost_only(self):
        """Test _score_candidate with cost_weight=1.0, preference_weight=0"""
        engine = RoutingEngine()

        # alicloud: cost=0.5, cost_score = 0.5
        score_alicloud = engine._score_candidate("alicloud", cost_weight=1.0, preference_weight=0.0)
        # openai: cost=1.0, cost_score = 0.0
        score_openai = engine._score_candidate("openai", cost_weight=1.0, preference_weight=0.0)

        # Lower cost provider should have higher score
        assert score_alicloud > score_openai

    def test_score_candidate_preference_only(self):
        """Test _score_candidate with cost_weight=0, preference_weight=1.0"""
        engine = RoutingEngine()

        # alicloud: preference=1.0
        score_alicloud = engine._score_candidate("alicloud", cost_weight=0.0, preference_weight=1.0)
        # openai: preference=0.7
        score_openai = engine._score_candidate("openai", cost_weight=0.0, preference_weight=1.0)

        # Higher preference provider should have higher score
        assert score_alicloud > score_openai
        assert score_alicloud == 1.0
        assert score_openai == 0.7

    def test_score_candidate_zero_weights_fallback(self):
        """Test _score_candidate falls back to preference when both weights are 0"""
        engine = RoutingEngine()

        # When both weights are 0, should return preference value
        score = engine._score_candidate("alicloud", cost_weight=0.0, preference_weight=0.0)
        assert score == 1.0  # alicloud preference is 1.0

    def test_score_candidate_unknown_provider(self):
        """Test _score_candidate with unknown provider uses defaults"""
        engine = RoutingEngine()

        # Unknown provider: cost=1.0 (default), preference=0.5 (default)
        score = engine._score_candidate("unknown_provider", cost_weight=0.5, preference_weight=0.5)
        # cost_score = 1.0 - 1.0 = 0.0
        # score = (0.5 * 0.5 + 0.0 * 0.5) / 1.0 = 0.25
        assert 0.24 <= score <= 0.26

    def test_find_available_model_selects_highest_score(self):
        """Test _find_available_model selects the candidate with highest score"""
        engine = RoutingEngine(available_providers=["alicloud", "openai", "siliconflow"])

        # With default weights, alicloud should be selected (highest preference + good cost)
        model_info = engine.select_model(TaskType.PLANNING)

        assert model_info.provider == "alicloud"

    def test_find_available_model_respects_availability(self):
        """Test _find_available_model only considers available providers"""
        # Only siliconflow available, even though alicloud has higher score
        # (With Cross-Generation Fallback, OpenAI is no longer in Tier 0/1)
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # SiliconFlow is now in Tier 0 (Cross-Generation Fallback)
        assert model_info.provider == "siliconflow"

    def test_score_candidate_weights_affect_ranking(self):
        """Test that different weights produce different rankings"""
        engine = RoutingEngine()

        # With cost_weight=1.0, preference_weight=0.0:
        # alicloud: cost_score = 1.0 - 0.5 = 0.5
        # openai: cost_score = 1.0 - 1.0 = 0.0
        # alicloud should score higher
        score_alicloud_cost = engine._score_candidate("alicloud", cost_weight=1.0, preference_weight=0.0)
        score_openai_cost = engine._score_candidate("openai", cost_weight=1.0, preference_weight=0.0)
        assert score_alicloud_cost > score_openai_cost

        # With cost_weight=0.0, preference_weight=1.0:
        # alicloud: preference = 1.0
        # openai: preference = 0.7
        # alicloud should still score higher (it wins on both axes)
        score_alicloud_pref = engine._score_candidate("alicloud", cost_weight=0.0, preference_weight=1.0)
        score_openai_pref = engine._score_candidate("openai", cost_weight=0.0, preference_weight=1.0)
        assert score_alicloud_pref > score_openai_pref

        # Verify the actual scores match expected values
        assert score_alicloud_cost == 0.5  # cost_score only
        assert score_openai_cost == 0.0    # cost_score only
        assert score_alicloud_pref == 1.0  # preference only
        assert score_openai_pref == 0.7    # preference only


class TestCrossGenerationFallback:
    """
    Tests for Cross-Generation Fallback (Routing Policy v1.2)

    Strategy:
    - Primary: AliCloud (Qwen3) for Tier 0/1
    - Backup: SiliconFlow (Qwen2.5) as degraded fallback
    - OpenAI/Gemini should NOT be in the fallback path for Tier 0/1

    This ensures that when AliCloud times out or is unavailable,
    the system falls back to SiliconFlow (our "backup generator"),
    not to expensive external providers like OpenAI.
    """

    def test_tier_0_fallback_to_siliconflow_not_openai(self):
        """
        Test that Tier 0 falls back to SiliconFlow when AliCloud is unavailable.

        Verifies: When AliCloud is down, system should use SiliconFlow (Qwen2.5-72B)
        as the backup, NOT OpenAI or Gemini.
        """
        # Only SiliconFlow available (simulating AliCloud timeout)
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Should fallback to SiliconFlow, not OpenAI/Gemini
        assert model_info.provider == "siliconflow"
        assert "Qwen" in model_info.model_name
        # Verify it's the 72B model (highest capability in SiliconFlow)
        assert "72B" in model_info.model_name or "32B" in model_info.model_name

    def test_tier_1_fallback_to_siliconflow_not_openai(self):
        """
        Test that Tier 1 falls back to SiliconFlow when AliCloud is unavailable.

        Verifies: When AliCloud is down, coding/review tasks should use
        SiliconFlow (Qwen2.5-32B) as the backup.
        """
        # Only SiliconFlow available (simulating AliCloud timeout)
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.CODING)

        # Should fallback to SiliconFlow, not OpenAI/Gemini
        assert model_info.provider == "siliconflow"
        assert "Qwen" in model_info.model_name

    def test_tier_0_models_only_contain_alicloud_and_siliconflow(self):
        """
        Test that Tier 0 model list only contains AliCloud and SiliconFlow.

        Verifies: OpenAI and Gemini are NOT in Tier 0 fallback path.
        """
        engine = RoutingEngine()

        tier_0_models = engine.get_models_for_tier(Tier.TIER_0)
        providers_in_tier_0 = [provider for provider, _ in tier_0_models]

        # Should only have alicloud and siliconflow
        assert "alicloud" in providers_in_tier_0
        assert "siliconflow" in providers_in_tier_0
        # Should NOT have openai or gemini
        assert "openai" not in providers_in_tier_0
        assert "gemini" not in providers_in_tier_0

    def test_tier_1_models_only_contain_alicloud_and_siliconflow(self):
        """
        Test that Tier 1 model list only contains AliCloud and SiliconFlow.

        Verifies: OpenAI and Gemini are NOT in Tier 1 fallback path.
        """
        engine = RoutingEngine()

        tier_1_models = engine.get_models_for_tier(Tier.TIER_1)
        providers_in_tier_1 = [provider for provider, _ in tier_1_models]

        # Should only have alicloud and siliconflow
        assert "alicloud" in providers_in_tier_1
        assert "siliconflow" in providers_in_tier_1
        # Should NOT have openai or gemini
        assert "openai" not in providers_in_tier_1
        assert "gemini" not in providers_in_tier_1

    def test_alicloud_primary_siliconflow_backup_for_planning(self):
        """
        Test that AliCloud is primary and SiliconFlow is backup for planning tasks.

        Verifies: With both providers available, AliCloud (Qwen3) is selected first.
        """
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # AliCloud should be primary (higher preference score)
        assert model_info.provider == "alicloud"
        assert model_info.model_name == "qwen-max"
        assert model_info.is_fallback is False

    def test_alicloud_primary_siliconflow_backup_for_coding(self):
        """
        Test that AliCloud is primary and SiliconFlow is backup for coding tasks.

        Verifies: With both providers available, AliCloud (Qwen3) is selected first.
        """
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        model_info = engine.select_model(TaskType.CODING)

        # AliCloud should be primary (higher preference score)
        assert model_info.provider == "alicloud"
        assert model_info.model_name == "qwen-plus"
        assert model_info.is_fallback is False

    def test_cross_generation_fallback_logs_correctly(self, caplog):
        """
        Test that cross-generation fallback selection is logged correctly.

        Verifies: When AliCloud is unavailable and SiliconFlow is selected,
        the log should indicate 'Cross-generation fallback' with 'alicloud unavailable'
        and 'siliconflow' (not OpenAI).

        This satisfies the acceptance criteria:
        "模擬 AliCloud Timeout，確認系統 Log 顯示 Fallback to SiliconFlow，而不是 OpenAI"
        """
        import logging
        caplog.set_level(logging.INFO)

        # Only SiliconFlow available (simulating AliCloud unavailable/timeout)
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # SiliconFlow is now in Tier 0 (Cross-Generation Fallback)
        assert model_info.provider == "siliconflow"
        assert model_info.tier == Tier.TIER_0

        # Verify log message contains cross-generation fallback info
        log_messages = [record.message for record in caplog.records]
        cross_gen_logs = [msg for msg in log_messages if "Cross-generation fallback" in msg]

        # Should have at least one cross-generation fallback log
        assert len(cross_gen_logs) >= 1, f"Expected cross-generation fallback log, got: {log_messages}"

        # The log should mention alicloud unavailable and siliconflow
        fallback_log = cross_gen_logs[0]
        assert "alicloud" in fallback_log.lower(), f"Log should mention alicloud: {fallback_log}"
        assert "siliconflow" in fallback_log.lower(), f"Log should mention siliconflow: {fallback_log}"
        assert "unavailable" in fallback_log.lower(), f"Log should mention unavailable: {fallback_log}"

        # Should NOT mention OpenAI in the fallback log
        assert "openai" not in fallback_log.lower(), f"Log should NOT mention openai: {fallback_log}"

        # Verify reason field is set correctly
        assert "Cross-generation fallback" in model_info.reason
        assert "alicloud" in model_info.reason.lower()
        assert "siliconflow" in model_info.reason.lower()

    def test_resilience_when_alicloud_unavailable(self):
        """
        Test system resilience when AliCloud is unavailable.

        Verifies: System does NOT crash when primary provider is down,
        and gracefully falls back to SiliconFlow.
        """
        # Simulate AliCloud being completely unavailable
        engine = RoutingEngine(available_providers=["siliconflow"])

        # All task types should still work with SiliconFlow fallback
        for task_type in [TaskType.PLANNING, TaskType.CODING, TaskType.REVIEW, TaskType.ANALYSIS]:
            model_info = engine.select_model(task_type)
            assert model_info is not None
            assert model_info.provider == "siliconflow"

    def test_no_openai_gemini_in_tier_0_1_fallback_path(self):
        """
        Test that OpenAI and Gemini are completely excluded from Tier 0/1.

        Verifies: Even if OpenAI/Gemini are available, they should NOT be
        selected for Tier 0/1 tasks (Cross-Generation Fallback policy).
        """
        # All providers available
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow", "openai", "gemini"])

        # For Tier 0 (planning), should use alicloud (not openai/gemini)
        model_info = engine.select_model(TaskType.PLANNING)
        assert model_info.provider in ["alicloud", "siliconflow"]
        assert model_info.provider not in ["openai", "gemini"]

        # For Tier 1 (coding), should use alicloud (not openai/gemini)
        model_info = engine.select_model(TaskType.CODING)
        assert model_info.provider in ["alicloud", "siliconflow"]
        assert model_info.provider not in ["openai", "gemini"]


class TestSoftWeighting:
    """
    Tests for EPIC I-4 Phase B-2: Soft Weighting

    Soft Weighting applies score multipliers based on provider degradation state:
    - HEALTHY: 1.0x (no change)
    - DEGRADED: 0.7x (30% reduction)
    - CRITICAL: 0.3x (70% reduction)
    - AVOID: 0.0x (handled by Hard Gating)

    Fail-open: If DegradationAdvisor is unavailable, use original scores.
    """

    def test_soft_weighting_healthy_provider_no_change(self):
        """Test that HEALTHY providers have no score reduction"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.HEALTHY

            multiplier = engine._get_degradation_multiplier("alicloud")

            assert multiplier == 1.0

    def test_soft_weighting_degraded_provider_70_percent(self):
        """Test that DEGRADED providers get 0.7x multiplier"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.DEGRADED

            multiplier = engine._get_degradation_multiplier("alicloud")

            assert multiplier == 0.7

    def test_soft_weighting_critical_provider_30_percent(self):
        """Test that CRITICAL providers get 0.3x multiplier"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.CRITICAL

            multiplier = engine._get_degradation_multiplier("alicloud")

            assert multiplier == 0.3

    def test_soft_weighting_avoid_provider_zero(self):
        """Test that AVOID providers get 0.0x multiplier (handled by Hard Gating)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.AVOID

            multiplier = engine._get_degradation_multiplier("alicloud")

            assert multiplier == 0.0

    def test_soft_weighting_fail_open_when_advisor_unavailable(self):
        """Test fail-open behavior when DegradationAdvisor is unavailable"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_get_advisor.return_value = None

            multiplier = engine._get_degradation_multiplier("alicloud")

            # Should return 1.0 (no penalty) when advisor is unavailable
            assert multiplier == 1.0

    def test_soft_weighting_fail_open_on_exception(self):
        """Test fail-open behavior when DegradationAdvisor raises exception"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_get_advisor.side_effect = RuntimeError("Advisor error")

            multiplier = engine._get_degradation_multiplier("alicloud")

            # Should return 1.0 (no penalty) on exception
            assert multiplier == 1.0

    def test_soft_weighting_affects_score_candidate(self):
        """Test that Soft Weighting affects _score_candidate output"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # Get base score without degradation
        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_get_advisor.return_value = None
            base_score = engine._score_candidate("alicloud")

        # Get score with DEGRADED state
        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.DEGRADED
            degraded_score = engine._score_candidate("alicloud")

        # Degraded score should be 70% of base score
        expected_degraded = base_score * 0.7
        assert abs(degraded_score - expected_degraded) < 0.001

    def test_soft_weighting_changes_provider_ranking(self):
        """Test that Soft Weighting can change provider selection order"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # Normally alicloud has higher score than siliconflow
        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_get_advisor.return_value = None
            alicloud_base = engine._score_candidate("alicloud")
            siliconflow_base = engine._score_candidate("siliconflow")

        assert alicloud_base > siliconflow_base, "AliCloud should normally score higher"

        # With alicloud CRITICAL and siliconflow HEALTHY, siliconflow should win
        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value

            def get_state(provider):
                if provider == "alicloud":
                    return DegradationSeverity.CRITICAL
                return DegradationSeverity.HEALTHY

            mock_advisor.get_provider_state.side_effect = get_state

            alicloud_critical = engine._score_candidate("alicloud")
            siliconflow_healthy = engine._score_candidate("siliconflow")

        # AliCloud with CRITICAL (0.3x) should now score lower than healthy SiliconFlow
        assert alicloud_critical < siliconflow_healthy, \
            f"CRITICAL alicloud ({alicloud_critical}) should score lower than HEALTHY siliconflow ({siliconflow_healthy})"

    def test_soft_weighting_logs_non_healthy_state(self, caplog):
        """Test that non-HEALTHY states are logged"""
        import logging
        caplog.set_level(logging.INFO)

        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.DEGRADED

            engine._get_degradation_multiplier("alicloud")

        # Check that log contains soft weighting info
        log_messages = [record.message for record in caplog.records]
        soft_weight_logs = [msg for msg in log_messages if "I-4-SOFT-WEIGHTING" in msg]

        assert len(soft_weight_logs) >= 1, f"Expected soft weighting log, got: {log_messages}"
        assert "degraded" in soft_weight_logs[0].lower()
        assert "0.7" in soft_weight_logs[0]

    def test_soft_weighting_does_not_log_healthy_state(self, caplog):
        """Test that HEALTHY state does not produce log spam"""
        import logging
        caplog.set_level(logging.INFO)

        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value
            mock_advisor.get_provider_state.return_value = DegradationSeverity.HEALTHY

            engine._get_degradation_multiplier("alicloud")

        # Should NOT have soft weighting log for HEALTHY state
        log_messages = [record.message for record in caplog.records]
        soft_weight_logs = [msg for msg in log_messages if "I-4-SOFT-WEIGHTING" in msg]

        assert len(soft_weight_logs) == 0, f"Should not log for HEALTHY state: {soft_weight_logs}"

    def test_soft_weighting_integration_with_select_model(self):
        """Test that Soft Weighting integrates correctly with select_model"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # With alicloud CRITICAL, siliconflow should be selected for planning
        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value

            def get_state(provider):
                if provider == "alicloud":
                    return DegradationSeverity.CRITICAL
                return DegradationSeverity.HEALTHY

            mock_advisor.get_provider_state.side_effect = get_state

            model_info = engine.select_model(TaskType.PLANNING)

        # SiliconFlow should be selected because alicloud has CRITICAL state
        assert model_info.provider == "siliconflow", \
            f"Expected siliconflow due to alicloud CRITICAL state, got {model_info.provider}"
