"""
Unit tests for context size boundary conditions and edge cases

Issue #2673 - EPIC #2594: Qwen3 Provider Integration

Tests cover:
- Context size exactly at tier boundary (128000, 32000, 8000)
- Context size just above tier boundary
- Very large context size exceeding all limits
- Zero and negative context sizes
- Context size causing tier upgrade
- Warning logs for context exceeding all limits
"""
import logging
import pytest  # noqa: F401 - pytest fixtures (caplog) are used implicitly

from core.routing import RoutingEngine, Tier, TaskType
from core.routing.engine import TIER_CONTEXT_LIMITS

# Semantic aliases for tier context limits to improve test readability
# while avoiding hardcoded values that could drift from implementation
TIER_0_LIMIT = TIER_CONTEXT_LIMITS[Tier.TIER_0]  # 128000
TIER_1_LIMIT = TIER_CONTEXT_LIMITS[Tier.TIER_1]  # 128000
TIER_2_LIMIT = TIER_CONTEXT_LIMITS[Tier.TIER_2]  # 32000
TIER_3_LIMIT = TIER_CONTEXT_LIMITS[Tier.TIER_3]  # 8000


class TestContextSizeAtExactBoundary:
    """Tests for context size exactly at tier boundaries"""

    def test_context_at_tier_3_limit(self):
        """Context exactly at Tier 3 limit should stay in Tier 3"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        # UX_COPY defaults to Tier 3
        model = engine.select_model(TaskType.UX_COPY, context_size=TIER_3_LIMIT)

        assert model.tier == Tier.TIER_3

    def test_context_at_tier_2_limit(self):
        """Context exactly at Tier 2 limit should stay in Tier 2"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # CHAT defaults to Tier 2
        model = engine.select_model(TaskType.CHAT, context_size=TIER_2_LIMIT)

        assert model.tier == Tier.TIER_2

    def test_context_at_tier_1_limit(self):
        """Context exactly at Tier 1 limit should stay in Tier 1"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # CODING defaults to Tier 1
        model = engine.select_model(TaskType.CODING, context_size=TIER_1_LIMIT)

        assert model.tier == Tier.TIER_1

    def test_context_at_tier_0_limit(self):
        """Context exactly at Tier 0 limit should stay in Tier 0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # PLANNING defaults to Tier 0
        model = engine.select_model(TaskType.PLANNING, context_size=TIER_0_LIMIT)

        assert model.tier == Tier.TIER_0


class TestContextSizeJustAboveBoundary:
    """Tests for context size just above tier boundaries"""

    def test_context_just_above_tier_3_limit(self):
        """Context just above Tier 3 limit should upgrade tier"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # UX_COPY defaults to Tier 3
        # context_size > TIER_3_LIMIT should upgrade to a tier with larger context
        model = engine.select_model(TaskType.UX_COPY, context_size=TIER_3_LIMIT + 1)

        # Should upgrade to Tier 2 or higher (lower tier number = higher capability)
        assert model.tier.value < Tier.TIER_3.value

    def test_context_just_above_tier_2_limit(self):
        """Context just above Tier 2 limit should upgrade tier"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # CHAT defaults to Tier 2
        # context_size > TIER_2_LIMIT should upgrade to Tier 0 or 1
        model = engine.select_model(TaskType.CHAT, context_size=TIER_2_LIMIT + 1)

        # Should upgrade to Tier 0 or 1
        assert model.tier.value < Tier.TIER_2.value

    def test_context_just_above_tier_1_limit(self):
        """Context just above Tier 1 limit should use Tier 0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # CODING defaults to Tier 1
        # context_size > TIER_1_LIMIT exceeds all limits, should use Tier 0
        model = engine.select_model(TaskType.CODING, context_size=TIER_1_LIMIT + 1)

        # Should use Tier 0 (highest capability)
        assert model.tier == Tier.TIER_0


class TestContextSizeExceedsAllLimits:
    """Tests for very large context sizes exceeding all tier limits"""

    def test_context_500000_uses_tier_0(self):
        """Very large context (500000) should use TIER_0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.UX_COPY, context_size=500000)

        assert model.tier == Tier.TIER_0

    def test_context_1000000_uses_tier_0(self):
        """Extremely large context (1000000) should use TIER_0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CHAT, context_size=1000000)

        assert model.tier == Tier.TIER_0

    def test_context_exceeds_all_limits_logs_warning(self, caplog):
        """Very large context should log a warning"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with caplog.at_level(logging.WARNING):
            engine.select_model(TaskType.UX_COPY, context_size=500000)

        assert "exceeds all tier limits" in caplog.text

    def test_context_max_int_uses_tier_0(self):
        """Maximum integer context should use TIER_0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Use a very large but reasonable number
        model = engine.select_model(TaskType.TRANSLATION, context_size=10000000)

        assert model.tier == Tier.TIER_0


class TestZeroContextSize:
    """Tests for zero context size"""

    def test_zero_context_does_not_affect_tier_selection(self):
        """Zero context should not affect tier selection"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # PLANNING defaults to Tier 0
        model = engine.select_model(TaskType.PLANNING, context_size=0)

        assert model.tier == Tier.TIER_0

    def test_zero_context_keeps_default_tier_for_coding(self):
        """Zero context should keep default tier for CODING (Tier 1)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=0)

        assert model.tier == Tier.TIER_1

    def test_zero_context_keeps_default_tier_for_ux_copy(self):
        """Zero context should keep default tier for UX_COPY (Tier 3)"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        model = engine.select_model(TaskType.UX_COPY, context_size=0)

        assert model.tier == Tier.TIER_3

    def test_zero_context_same_as_no_context(self):
        """Zero context should behave same as not specifying context"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_with_zero = engine.select_model(TaskType.CODING, context_size=0)
        model_without = engine.select_model(TaskType.CODING)

        assert model_with_zero.tier == model_without.tier
        assert model_with_zero.model_name == model_without.model_name


class TestNegativeContextSize:
    """Tests for negative context size handling"""

    def test_negative_context_handled_gracefully(self):
        """Negative context should be handled gracefully"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Negative context should not cause errors
        model = engine.select_model(TaskType.PLANNING, context_size=-1)

        # Should use default tier (negative is less than any limit)
        assert model.tier == Tier.TIER_0

    def test_negative_large_context_handled(self):
        """Large negative context should be handled gracefully"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=-10000)

        # Should use default tier
        assert model.tier == Tier.TIER_1

    def test_negative_context_does_not_upgrade_tier(self):
        """Negative context should not cause tier upgrade"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        model = engine.select_model(TaskType.UX_COPY, context_size=-100)

        # Should stay at default Tier 3
        assert model.tier == Tier.TIER_3


class TestContextSizeCausingTierUpgrade:
    """Tests for context size causing tier upgrade from lower to higher capability"""

    def test_tier_3_task_with_large_context_upgrades_to_tier_0(self):
        """Tier 3 task with large context should upgrade to Tier 0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # UX_COPY defaults to Tier 3, but 50000 tokens exceeds Tier 3 limit (8000)
        # and Tier 2 limit (32000), so should upgrade to Tier 0/1
        model = engine.select_model(TaskType.UX_COPY, context_size=50000)

        # Should upgrade to Tier 0 or 1 (128000 limit)
        assert model.tier.value <= Tier.TIER_1.value

    def test_tier_2_task_with_large_context_upgrades(self):
        """Tier 2 task with large context should upgrade"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # CHAT defaults to Tier 2, but 100000 tokens exceeds Tier 2 limit (32000)
        model = engine.select_model(TaskType.CHAT, context_size=100000)

        # Should upgrade to Tier 0 or 1
        assert model.tier.value < Tier.TIER_2.value

    def test_context_upgrade_preserves_provider_preference(self):
        """Context-based tier upgrade should still respect provider availability"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.UX_COPY, context_size=50000)

        # Should use alicloud provider
        assert model.provider == "alicloud"


class TestContextSizeLogging:
    """Tests for logging during context size adjustments"""

    def test_context_upgrade_logs_info(self, caplog):
        """Context-based tier upgrade should log info message"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with caplog.at_level(logging.INFO):
            engine.select_model(TaskType.UX_COPY, context_size=50000)

        # Should log the tier adjustment
        assert "Adjusted tier" in caplog.text or "context size" in caplog.text.lower()

    def test_no_log_when_context_within_limit(self, caplog):
        """No adjustment log when context is within tier limit"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with caplog.at_level(logging.INFO):
            engine.select_model(TaskType.PLANNING, context_size=1000)

        # Should not log tier adjustment (context is small)
        assert "Adjusted tier" not in caplog.text


class TestTierContextLimitsConstants:
    """Tests for TIER_CONTEXT_LIMITS constant values"""

    def test_tier_0_limit_is_128000(self):
        """Verify Tier 0 context limit is 128000"""
        assert TIER_CONTEXT_LIMITS[Tier.TIER_0] == 128000

    def test_tier_1_limit_is_128000(self):
        """Verify Tier 1 context limit is 128000"""
        assert TIER_CONTEXT_LIMITS[Tier.TIER_1] == 128000

    def test_tier_2_limit_is_32000(self):
        """Verify Tier 2 context limit is 32000"""
        assert TIER_CONTEXT_LIMITS[Tier.TIER_2] == 32000

    def test_tier_3_limit_is_8000(self):
        """Verify Tier 3 context limit is 8000"""
        assert TIER_CONTEXT_LIMITS[Tier.TIER_3] == 8000

    def test_all_tiers_have_limits(self):
        """Verify all tiers have defined context limits"""
        for tier in Tier:
            assert tier in TIER_CONTEXT_LIMITS


class TestContextSizeWithRiskLevel:
    """Tests for context size interaction with risk level"""

    def test_high_risk_with_large_context(self):
        """High risk with large context should still respect context limits"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # CODING with high risk would normally try Tier 0
        # Large context should not downgrade from Tier 0
        model = engine.select_model(
            TaskType.CODING,
            risk_level="high",
            context_size=100000
        )

        assert model.tier == Tier.TIER_0

    def test_low_risk_with_large_context_upgrades(self):
        """Low risk with large context should upgrade tier for context"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # CODING with low risk would try Tier 2 (32000 limit)
        # 50000 tokens exceeds Tier 2 limit, should upgrade
        model = engine.select_model(
            TaskType.CODING,
            risk_level="low",
            context_size=50000
        )

        # Should upgrade to Tier 0 or 1 due to context size
        assert model.tier.value < Tier.TIER_2.value


class TestContextSizeEdgeCases:
    """Additional edge case tests for context size"""

    def test_context_size_one(self):
        """Context size of 1 should not affect tier selection"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=1)

        assert model.tier == Tier.TIER_1

    def test_context_size_at_each_boundary_minus_one(self):
        """Context size at boundary-1 should stay in current tier"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        # Just under Tier 3 limit
        model = engine.select_model(TaskType.UX_COPY, context_size=TIER_3_LIMIT - 1)

        assert model.tier == Tier.TIER_3

    def test_context_size_at_tier_2_boundary_minus_one(self):
        """Context size at Tier 2 boundary-1 should stay in Tier 2"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        # Just under Tier 2 limit
        model = engine.select_model(TaskType.CHAT, context_size=TIER_2_LIMIT - 1)

        assert model.tier == Tier.TIER_2

    def test_context_size_at_tier_0_boundary_minus_one(self):
        """Context size at Tier 0 boundary-1 should stay in Tier 0"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Just under Tier 0/1 limit
        model = engine.select_model(TaskType.PLANNING, context_size=TIER_0_LIMIT - 1)

        assert model.tier == Tier.TIER_0
