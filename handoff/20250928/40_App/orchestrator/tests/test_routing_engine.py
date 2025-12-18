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
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from unittest.mock import patch  # noqa: E402

from core.routing import RoutingEngine, Tier, TaskType, ModelInfo  # noqa: E402


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
        engine = RoutingEngine(available_providers=["openai"])
        model_info = engine.select_model(TaskType.REVIEW)

        assert model_info.tier == Tier.TIER_1
        assert model_info.model_name == "gpt-4o-mini"


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
        # Only siliconflow available, which doesn't have Tier 0 models
        engine = RoutingEngine(available_providers=["siliconflow"])

        # Planning wants Tier 0, but siliconflow only has Tier 2-3
        model_info = engine.select_model(TaskType.PLANNING)

        # Should fallback to available tier
        assert model_info.is_fallback is True
        assert model_info.provider == "siliconflow"

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

    def test_openai_used_when_alicloud_unavailable(self):
        """Test that OpenAI is used when AliCloud is unavailable"""
        engine = RoutingEngine(available_providers=["openai"])

        model_info = engine.select_model(TaskType.PLANNING)

        assert model_info.provider == "openai"
        assert model_info.model_name == "gpt-4o"


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
