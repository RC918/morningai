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
        """Test that UX Copy Task returns Tier 3 model (gemini-2.0-flash)"""
        engine = RoutingEngine(available_providers=["gemini"])
        model_info = engine.select_model(TaskType.UX_COPY)

        assert model_info.tier == Tier.TIER_3
        assert model_info.provider == "gemini"
        assert "gemini" in model_info.model_name

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
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

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
        # With Gemini-First routing, Gemini is the primary provider
        engine = RoutingEngine(available_providers=["gemini"])

        # Planning wants Tier 0, Gemini is now the primary Tier 0 provider
        model_info = engine.select_model(TaskType.PLANNING)

        # Gemini is the primary Tier 0 provider
        assert model_info.provider == "gemini"
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
        engine = RoutingEngine(available_providers=["gemini"])

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
    """Tests for provider priority (Gemini-First)"""

    def test_gemini_preferred_as_primary(self):
        """Test that Gemini is preferred as primary provider when available"""
        engine = RoutingEngine(available_providers=["gemini", "alicloud", "openai"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Gemini should be preferred for Tier 0 (Gemini-First policy)
        assert model_info.provider == "gemini"
        assert "gemini" in model_info.model_name

    def test_alicloud_used_when_gemini_unavailable(self):
        """Test that AliCloud is used when Gemini is unavailable (Gemini-First Fallback)"""
        engine = RoutingEngine(available_providers=["alicloud", "openai"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Gemini-First Fallback: AliCloud is the secondary provider
        assert model_info.provider == "alicloud"
        assert model_info.model_name == "qwen-max"


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
        mock_siliconflow_settings.siliconflow_api_key = None
        mock_openai_settings.openai_api_key = None
        mock_gemini_settings.gemini_api_key = "test-key"

        from llm.client import get_client_for_task

        client = get_client_for_task(TaskType.UX_COPY)

        assert client.provider_name == "gemini"


class TestRoutingEngineCandidateScoring:
    """Tests for candidate scoring and selection (Issue #2874)"""

    def test_score_candidate_default_weights(self):
        """Test _score_candidate with default weights (0.3 cost, 0.7 preference)"""
        engine = RoutingEngine()

        # gemini: cost=0.5, preference=1.0 (Gemini-First policy)
        # cost_score = 1.0 - 0.5 = 0.5
        # score = (1.0 * 0.7 + 0.5 * 0.3) / 1.0 = 0.85
        score = engine._score_candidate("gemini", cost_weight=0.3, preference_weight=0.7)
        assert 0.84 <= score <= 0.86  # Allow small floating point variance

    def test_score_candidate_cost_only(self):
        """Test _score_candidate with cost_weight=1.0, preference_weight=0"""
        engine = RoutingEngine()

        # gemini: cost=0.5, cost_score = 0.5 (Gemini-First policy)
        score_gemini = engine._score_candidate("gemini", cost_weight=1.0, preference_weight=0.0)
        # openai: cost=1.0, cost_score = 0.0
        score_openai = engine._score_candidate("openai", cost_weight=1.0, preference_weight=0.0)

        # Lower cost provider should have higher score
        assert score_gemini > score_openai

    def test_score_candidate_preference_only(self):
        """Test _score_candidate with cost_weight=0, preference_weight=1.0"""
        engine = RoutingEngine()

        # gemini: preference=1.0 (Gemini-First policy)
        score_gemini = engine._score_candidate("gemini", cost_weight=0.0, preference_weight=1.0)
        # openai: preference=0.7
        score_openai = engine._score_candidate("openai", cost_weight=0.0, preference_weight=1.0)

        # Higher preference provider should have higher score
        assert score_gemini > score_openai
        assert score_gemini == 1.0
        assert score_openai == 0.7

    def test_score_candidate_zero_weights_fallback(self):
        """Test _score_candidate falls back to preference when both weights are 0"""
        engine = RoutingEngine()

        # When both weights are 0, should return preference value
        score = engine._score_candidate("gemini", cost_weight=0.0, preference_weight=0.0)
        assert score == 1.0  # gemini preference is 1.0 (Gemini-First policy)

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
        engine = RoutingEngine(available_providers=["gemini", "alicloud", "openai"])

        # With default weights, gemini should be selected (highest preference + good cost)
        model_info = engine.select_model(TaskType.PLANNING)

        assert model_info.provider == "gemini"

    def test_find_available_model_respects_availability(self):
        """Test _find_available_model only considers available providers"""
        # Only alicloud available, even though gemini has higher score
        engine = RoutingEngine(available_providers=["alicloud"])

        model_info = engine.select_model(TaskType.PLANNING)

        # AliCloud is the secondary provider in Gemini-First policy
        assert model_info.provider == "alicloud"

    def test_score_candidate_weights_affect_ranking(self):
        """Test that different weights produce different rankings"""
        engine = RoutingEngine()

        # With cost_weight=1.0, preference_weight=0.0:
        # gemini: cost_score = 1.0 - 0.5 = 0.5
        # openai: cost_score = 1.0 - 1.0 = 0.0
        # gemini should score higher
        score_gemini_cost = engine._score_candidate("gemini", cost_weight=1.0, preference_weight=0.0)
        score_openai_cost = engine._score_candidate("openai", cost_weight=1.0, preference_weight=0.0)
        assert score_gemini_cost > score_openai_cost

        # With cost_weight=0.0, preference_weight=1.0:
        # gemini: preference = 1.0
        # openai: preference = 0.7
        # gemini should still score higher (it wins on both axes)
        score_gemini_pref = engine._score_candidate("gemini", cost_weight=0.0, preference_weight=1.0)
        score_openai_pref = engine._score_candidate("openai", cost_weight=0.0, preference_weight=1.0)
        assert score_gemini_pref > score_openai_pref

        # Verify the actual scores match expected values
        assert score_gemini_cost == 0.5  # cost_score only
        assert score_openai_cost == 0.0    # cost_score only
        assert score_gemini_pref == 1.0  # preference only
        assert score_openai_pref == 0.7    # preference only


class TestGeminiFirstFallback:
    """
    Tests for Gemini-First Fallback (Routing Policy v1.3)

    Strategy:
    - Primary: Gemini for all tiers
    - Secondary: AliCloud (Qwen) as fallback
    - Tertiary: OpenAI as final fallback

    This ensures that Gemini is always preferred when available,
    with AliCloud as the secondary option.
    """

    def test_tier_0_uses_gemini_as_primary(self):
        """
        Test that Tier 0 uses Gemini as primary provider.

        Verifies: When Gemini is available, it should be selected first.
        """
        engine = RoutingEngine(available_providers=["gemini", "alicloud", "openai"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Should use Gemini as primary
        assert model_info.provider == "gemini"
        assert "gemini" in model_info.model_name

    def test_tier_1_uses_gemini_as_primary(self):
        """
        Test that Tier 1 uses Gemini as primary provider.

        Verifies: When Gemini is available, coding/review tasks should use Gemini.
        """
        engine = RoutingEngine(available_providers=["gemini", "alicloud", "openai"])

        model_info = engine.select_model(TaskType.CODING)

        # Should use Gemini as primary
        assert model_info.provider == "gemini"
        assert "gemini" in model_info.model_name

    def test_tier_0_models_contain_gemini_alicloud_openai(self):
        """
        Test that Tier 0 model list contains Gemini, AliCloud, and OpenAI.

        Verifies: All three providers are available in Tier 0.
        """
        engine = RoutingEngine()

        tier_0_models = engine.get_models_for_tier(Tier.TIER_0)
        providers_in_tier_0 = [provider for provider, _ in tier_0_models]

        # Should have gemini, alicloud, and openai
        assert "gemini" in providers_in_tier_0
        assert "alicloud" in providers_in_tier_0
        assert "openai" in providers_in_tier_0

    def test_tier_1_models_contain_gemini_alicloud_openai(self):
        """
        Test that Tier 1 model list contains Gemini, AliCloud, and OpenAI.

        Verifies: All three providers are available in Tier 1.
        """
        engine = RoutingEngine()

        tier_1_models = engine.get_models_for_tier(Tier.TIER_1)
        providers_in_tier_1 = [provider for provider, _ in tier_1_models]

        # Should have gemini, alicloud, and openai
        assert "gemini" in providers_in_tier_1
        assert "alicloud" in providers_in_tier_1
        assert "openai" in providers_in_tier_1

    def test_gemini_primary_alicloud_backup_for_planning(self):
        """
        Test that Gemini is primary and AliCloud is backup for planning tasks.

        Verifies: With both providers available, Gemini is selected first.
        """
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Gemini should be primary (highest preference score)
        assert model_info.provider == "gemini"
        assert "gemini" in model_info.model_name
        assert model_info.is_fallback is False

    def test_gemini_primary_alicloud_backup_for_coding(self):
        """
        Test that Gemini is primary and AliCloud is backup for coding tasks.

        Verifies: With both providers available, Gemini is selected first.
        """
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

        model_info = engine.select_model(TaskType.CODING)

        # Gemini should be primary (highest preference score)
        assert model_info.provider == "gemini"
        assert "gemini" in model_info.model_name
        assert model_info.is_fallback is False

    def test_fallback_to_alicloud_when_gemini_unavailable(self):
        """
        Test that AliCloud is used when Gemini is unavailable.

        Verifies: When Gemini is down, system should use AliCloud as backup.
        """
        # Only AliCloud available (simulating Gemini unavailable)
        engine = RoutingEngine(available_providers=["alicloud", "openai"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Should fallback to AliCloud
        assert model_info.provider == "alicloud"
        assert model_info.model_name == "qwen-max"

    def test_resilience_when_gemini_unavailable(self):
        """
        Test system resilience when Gemini is unavailable.

        Verifies: System does NOT crash when primary provider is down,
        and gracefully falls back to AliCloud.
        """
        # Simulate Gemini being completely unavailable
        engine = RoutingEngine(available_providers=["alicloud"])

        # All task types should still work with AliCloud fallback
        for task_type in [TaskType.PLANNING, TaskType.CODING, TaskType.REVIEW, TaskType.ANALYSIS]:
            model_info = engine.select_model(task_type)
            assert model_info is not None
            assert model_info.provider == "alicloud"

    def test_gemini_preferred_over_all_providers(self):
        """
        Test that Gemini is preferred over all other providers.

        Verifies: Even if all providers are available, Gemini should be selected.
        """
        # All providers available
        engine = RoutingEngine(available_providers=["gemini", "alicloud", "openai"])

        # For Tier 0 (planning), should use gemini
        model_info = engine.select_model(TaskType.PLANNING)
        assert model_info.provider == "gemini"

        # For Tier 1 (coding), should use gemini
        model_info = engine.select_model(TaskType.CODING)
        assert model_info.provider == "gemini"


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
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

        # With gemini CRITICAL, alicloud should be selected for planning
        with patch('governance.degradation_advisor.get_degradation_advisor') as mock_get_advisor:
            mock_advisor = mock_get_advisor.return_value

            def get_state(provider):
                if provider == "gemini":
                    return DegradationSeverity.CRITICAL
                return DegradationSeverity.HEALTHY

            mock_advisor.get_provider_state.side_effect = get_state

            model_info = engine.select_model(TaskType.PLANNING)

        # AliCloud should be selected because gemini has CRITICAL state
        assert model_info.provider == "alicloud", \
            f"Expected alicloud due to gemini CRITICAL state, got {model_info.provider}"


class TestEscalationLadderHardCap:
    """Tests for Escalation Ladder Hard Cap (Cost Optimization)"""

    def test_tier_floor_enforced_for_medium_risk(self):
        """Test that tier floor is enforced for medium-risk tasks"""
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = True
            mock_settings.routing_tier_floor = 2

            # Coding is normally Tier 1, but tier floor should enforce Tier 2
            model_info = engine.select_model(TaskType.CODING, risk_level="medium")

            # Should be at least Tier 2 due to tier floor
            assert model_info.tier.value >= 2, \
                f"Expected tier >= 2 due to tier floor, got {model_info.tier.value}"

    def test_tier_floor_bypassed_for_high_risk(self):
        """Test that tier floor is bypassed for high-risk tasks"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = True
            mock_settings.routing_tier_floor = 2

            # High-risk tasks should bypass tier floor
            model_info = engine.select_model(TaskType.CODING, risk_level="high")

            # Should be Tier 0 (high-risk bypasses floor)
            assert model_info.tier == Tier.TIER_0, \
                f"Expected Tier 0 for high-risk, got {model_info.tier}"

    def test_escalation_cap_blocks_further_escalation(self):
        """Test that escalation cap blocks further tier escalation"""
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = False  # Disable floor for this test
            mock_settings.routing_tier_floor = 2

            # With escalation_count=1 (already escalated once), should not escalate further
            model_info = engine.select_model(
                TaskType.CODING,
                risk_level="high",
                escalation_count=1
            )

            # Should stay at original tier (Tier 1 for coding) due to escalation cap
            assert model_info.tier == Tier.TIER_1, \
                f"Expected Tier 1 due to escalation cap, got {model_info.tier}"

    def test_retry_cap_returns_lowest_cost_tier(self):
        """Test that retry cap returns lowest-cost tier (Tier 3)"""
        engine = RoutingEngine(available_providers=["gemini"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = False
            mock_settings.routing_tier_floor = 2

            # With retry_count=2 (at max), should return Tier 3
            model_info = engine.select_model(
                TaskType.PLANNING,
                retry_count=2
            )

            # Should be Tier 3 (lowest cost) due to retry cap
            assert model_info.tier == Tier.TIER_3, \
                f"Expected Tier 3 due to retry cap, got {model_info.tier}"
            assert "Retry cap reached" in model_info.reason

    def test_escalation_count_zero_allows_escalation(self):
        """Test that escalation_count=0 allows normal escalation"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = False
            mock_settings.routing_tier_floor = 2

            # With escalation_count=0, high-risk should escalate to Tier 0
            model_info = engine.select_model(
                TaskType.CODING,
                risk_level="high",
                escalation_count=0
            )

            # Should escalate to Tier 0
            assert model_info.tier == Tier.TIER_0, \
                f"Expected Tier 0 with escalation_count=0, got {model_info.tier}"

    def test_tier_floor_disabled_allows_escalation(self):
        """Test that tier floor can be disabled via settings"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 3
            mock_settings.routing_max_retries = 5
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = False  # Disabled
            mock_settings.routing_tier_floor = 2

            # With floor disabled, medium-risk coding should stay at Tier 1
            model_info = engine.select_model(TaskType.CODING, risk_level="medium")

            # Should be Tier 1 (no floor enforcement)
            assert model_info.tier == Tier.TIER_1, \
                f"Expected Tier 1 with floor disabled, got {model_info.tier}"

    def test_default_settings_when_import_fails(self):
        """Test that default settings are used when import fails"""
        engine = RoutingEngine(available_providers=["gemini", "alicloud"])

        # Explicitly set settings to None to test fallback defaults
        # Default: tier_floor=2, force_tier_floor=True
        with patch('core.routing.engine.settings', None):
            model_info = engine.select_model(TaskType.CODING, risk_level="medium")

            # With default settings (settings=None), should be at least Tier 2
            assert model_info.tier.value >= 2, \
                f"Expected tier >= 2 with default settings, got {model_info.tier.value}"

    def test_max_escalations_zero_disables_escalation(self):
        """Test that max_escalations=0 disables all escalation"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 0
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = False
            mock_settings.routing_tier_floor = 2

            # With max_escalations=0, even high-risk should not escalate
            model_info = engine.select_model(
                TaskType.CODING,
                risk_level="high",
                escalation_count=0
            )

            # Should stay at original tier (Tier 1 for coding)
            assert model_info.tier == Tier.TIER_1, \
                f"Expected Tier 1 with max_escalations=0, got {model_info.tier}"

    def test_retry_cap_returns_tier3_when_available(self):
        """Test that retry cap returns Tier 3 model when available"""
        # With Gemini-First policy, all providers have Tier 3 models
        engine = RoutingEngine(available_providers=["gemini"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = False
            mock_settings.routing_tier_floor = 2

            # With retry_count=2 (at max), should return Tier 3 model
            model_info = engine.select_model(
                TaskType.PLANNING,
                retry_count=2
            )

            # Should return Tier 3 model since all providers now have Tier 3
            assert model_info is not None, "Expected a model to be returned"
            assert model_info.tier == Tier.TIER_3, \
                f"Expected Tier 3, got {model_info.tier}"
            assert "Retry cap reached" in model_info.reason
            # is_fallback should be False since Tier 3 is available
            assert model_info.is_fallback is False, \
                "Expected is_fallback=False when Tier 3 is available"
