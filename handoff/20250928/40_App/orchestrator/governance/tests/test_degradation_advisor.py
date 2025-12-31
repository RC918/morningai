"""
Tests for EPIC I-4 Degradation Advisor

Tests the DegradationPolicy and DegradationAdvisor classes for:
- Threshold-based severity calculation
- Hysteresis (recovery requires higher score)
- Floor provider protection
- Cooldown mechanism
- Minimum sample size guard
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

repo_root = Path(__file__).resolve().parent
for _ in range(10):
    if (repo_root / 'common').exists():
        break
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from governance.degradation_types import (  # noqa: E402
    DegradationSeverity,
    DegradationRecommendation,
    SEVERITY_MULTIPLIERS,
)
from governance.degradation_advisor import (  # noqa: E402
    DegradationPolicy,
    DegradationAdvisor,
    reset_degradation_advisor,
)


class TestDegradationSeverity:
    """Tests for DegradationSeverity enum and multipliers"""

    def test_severity_values(self):
        """Test severity enum values"""
        assert DegradationSeverity.HEALTHY.value == "healthy"
        assert DegradationSeverity.DEGRADED.value == "degraded"
        assert DegradationSeverity.CRITICAL.value == "critical"
        assert DegradationSeverity.AVOID.value == "avoid"

    def test_severity_multipliers(self):
        """Test severity multipliers are correct"""
        assert SEVERITY_MULTIPLIERS[DegradationSeverity.HEALTHY] == 1.0
        assert SEVERITY_MULTIPLIERS[DegradationSeverity.DEGRADED] == 0.5
        assert SEVERITY_MULTIPLIERS[DegradationSeverity.CRITICAL] == 0.25
        assert SEVERITY_MULTIPLIERS[DegradationSeverity.AVOID] == 0.0


class TestDegradationRecommendation:
    """Tests for DegradationRecommendation dataclass"""

    def test_basic_recommendation(self):
        """Test basic recommendation creation"""
        rec = DegradationRecommendation(
            provider="openai",
            severity=DegradationSeverity.DEGRADED,
            score_multiplier=0.5,
            health_score=60.0,
            health_score_normalized=0.6,
            reason="elevated_error_rate (7.5%)",
            dry_run=True,
        )

        assert rec.provider == "openai"
        assert rec.severity == DegradationSeverity.DEGRADED
        assert rec.score_multiplier == 0.5
        assert rec.health_score == 60.0
        assert rec.dry_run is True
        assert rec.floor_protected is False

    def test_is_state_change(self):
        """Test state change detection"""
        rec_no_change = DegradationRecommendation(
            provider="openai",
            severity=DegradationSeverity.DEGRADED,
            score_multiplier=0.5,
            health_score=60.0,
            health_score_normalized=0.6,
            reason="test",
            previous_severity=DegradationSeverity.DEGRADED,
        )
        assert rec_no_change.is_state_change is False

        rec_with_change = DegradationRecommendation(
            provider="openai",
            severity=DegradationSeverity.DEGRADED,
            score_multiplier=0.5,
            health_score=60.0,
            health_score_normalized=0.6,
            reason="test",
            previous_severity=DegradationSeverity.HEALTHY,
        )
        assert rec_with_change.is_state_change is True

    def test_display_name(self):
        """Test display name mapping"""
        rec = DegradationRecommendation(
            provider="alicloud",
            severity=DegradationSeverity.HEALTHY,
            score_multiplier=1.0,
            health_score=90.0,
            health_score_normalized=0.9,
            reason="all_metrics_normal",
        )
        assert rec.display_name == "AliCloud"

    def test_format_log(self):
        """Test log formatting"""
        rec = DegradationRecommendation(
            provider="openai",
            severity=DegradationSeverity.DEGRADED,
            score_multiplier=0.5,
            health_score=60.0,
            health_score_normalized=0.6,
            reason="elevated_error_rate",
            dry_run=True,
        )
        log = rec.format_log()
        assert "60.0" in log
        assert "DEGRADED" in log
        assert "50%" in log
        assert "Dry-run" in log

    def test_to_dict(self):
        """Test dictionary conversion"""
        rec = DegradationRecommendation(
            provider="gemini",
            severity=DegradationSeverity.CRITICAL,
            score_multiplier=0.25,
            health_score=30.0,
            health_score_normalized=0.3,
            reason="error_rate_spike",
            floor_protected=True,
        )
        d = rec.to_dict()
        assert d["provider"] == "gemini"
        assert d["severity"] == "critical"
        assert d["floor_protected"] is True


class TestDegradationPolicy:
    """Tests for DegradationPolicy class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.policy = DegradationPolicy(
            healthy_threshold=75.0,
            degraded_threshold=50.0,
            critical_threshold=25.0,
            recovery_buffer=10.0,
        )

    def test_simple_severity_healthy(self):
        """Test HEALTHY severity for high scores"""
        assert self.policy.compute_severity(90.0) == DegradationSeverity.HEALTHY
        assert self.policy.compute_severity(75.0) == DegradationSeverity.HEALTHY

    def test_simple_severity_degraded(self):
        """Test DEGRADED severity for medium scores"""
        assert self.policy.compute_severity(74.9) == DegradationSeverity.DEGRADED
        assert self.policy.compute_severity(50.0) == DegradationSeverity.DEGRADED

    def test_simple_severity_critical(self):
        """Test CRITICAL severity for low scores"""
        assert self.policy.compute_severity(49.9) == DegradationSeverity.CRITICAL
        assert self.policy.compute_severity(25.0) == DegradationSeverity.CRITICAL

    def test_simple_severity_avoid(self):
        """Test AVOID severity for very low scores"""
        assert self.policy.compute_severity(24.9) == DegradationSeverity.AVOID
        assert self.policy.compute_severity(0.0) == DegradationSeverity.AVOID

    def test_hysteresis_degraded_to_healthy(self):
        """Test hysteresis: DEGRADED->HEALTHY requires higher score"""
        # At 75, should stay DEGRADED (need 85 to recover)
        assert self.policy.compute_severity(
            75.0, DegradationSeverity.DEGRADED
        ) == DegradationSeverity.DEGRADED

        # At 84, should still stay DEGRADED
        assert self.policy.compute_severity(
            84.0, DegradationSeverity.DEGRADED
        ) == DegradationSeverity.DEGRADED

        # At 85, should recover to HEALTHY
        assert self.policy.compute_severity(
            85.0, DegradationSeverity.DEGRADED
        ) == DegradationSeverity.HEALTHY

    def test_hysteresis_critical_to_degraded(self):
        """Test hysteresis: CRITICAL->DEGRADED requires higher score"""
        # At 50, should stay CRITICAL (need 60 to recover)
        assert self.policy.compute_severity(
            50.0, DegradationSeverity.CRITICAL
        ) == DegradationSeverity.CRITICAL

        # At 60, should recover to DEGRADED
        assert self.policy.compute_severity(
            60.0, DegradationSeverity.CRITICAL
        ) == DegradationSeverity.DEGRADED

    def test_hysteresis_avoid_to_critical(self):
        """Test hysteresis: AVOID->CRITICAL requires higher score"""
        # At 25, should stay AVOID (need 35 to recover)
        assert self.policy.compute_severity(
            25.0, DegradationSeverity.AVOID
        ) == DegradationSeverity.AVOID

        # At 35, should recover to CRITICAL
        assert self.policy.compute_severity(
            35.0, DegradationSeverity.AVOID
        ) == DegradationSeverity.CRITICAL

    def test_degradation_no_hysteresis(self):
        """Test that degradation doesn't require hysteresis"""
        # HEALTHY -> DEGRADED at threshold
        assert self.policy.compute_severity(
            74.0, DegradationSeverity.HEALTHY
        ) == DegradationSeverity.DEGRADED

        # DEGRADED -> CRITICAL at threshold
        assert self.policy.compute_severity(
            49.0, DegradationSeverity.DEGRADED
        ) == DegradationSeverity.CRITICAL

    def test_get_multiplier(self):
        """Test multiplier retrieval"""
        assert self.policy.get_multiplier(DegradationSeverity.HEALTHY) == 1.0
        assert self.policy.get_multiplier(DegradationSeverity.DEGRADED) == 0.5
        assert self.policy.get_multiplier(DegradationSeverity.CRITICAL) == 0.25
        assert self.policy.get_multiplier(DegradationSeverity.AVOID) == 0.0

    def test_determine_reason_healthy(self):
        """Test reason determination for healthy provider"""
        health_data = {
            "health_score": 90.0,
            "error_rate": 1.0,
            "drift_rate": 2.0,
        }
        reason = self.policy.determine_reason(health_data, DegradationSeverity.HEALTHY)
        assert reason == "all_metrics_normal"

    def test_determine_reason_error_rate(self):
        """Test reason determination for high error rate"""
        health_data = {
            "health_score": 60.0,
            "error_rate": 12.0,
            "drift_rate": 2.0,
        }
        reason = self.policy.determine_reason(health_data, DegradationSeverity.DEGRADED)
        assert "error_rate_spike" in reason

    def test_determine_reason_drift_rate(self):
        """Test reason determination for high drift rate"""
        health_data = {
            "health_score": 60.0,
            "error_rate": 2.0,
            "drift_rate": 15.0,
        }
        reason = self.policy.determine_reason(health_data, DegradationSeverity.DEGRADED)
        assert "drift_rate_spike" in reason


class TestDegradationAdvisor:
    """Tests for DegradationAdvisor class"""

    def setup_method(self):
        """Set up test fixtures"""
        reset_degradation_advisor()
        self.advisor = DegradationAdvisor(
            enabled=True,
            cooldown_minutes=15,
            min_requests=10,
            floor_provider_count=1,
        )

    def teardown_method(self):
        """Clean up after tests"""
        reset_degradation_advisor()

    def test_disabled_advisor_returns_none(self):
        """Test that disabled advisor returns None"""
        advisor = DegradationAdvisor(enabled=False)
        result = advisor.compute_advisory("openai", {"health_score": 50.0})
        assert result is None

    def test_no_health_score_returns_none(self):
        """Test that missing health score returns None"""
        result = self.advisor.compute_advisory("openai", {})
        assert result is None

    def test_insufficient_requests_returns_none(self):
        """Test that insufficient requests returns None"""
        result = self.advisor.compute_advisory("openai", {
            "health_score": 50.0,
            "total_requests": 5,  # Less than min_requests=10
        })
        assert result is None

    def test_compute_advisory_healthy(self):
        """Test advisory for healthy provider"""
        result = self.advisor.compute_advisory("openai", {
            "health_score": 90.0,
            "total_requests": 100,
            "error_rate": 1.0,
            "drift_rate": 2.0,
        })

        assert result is not None
        assert result.severity == DegradationSeverity.HEALTHY
        assert result.score_multiplier == 1.0
        assert result.dry_run is True

    def test_compute_advisory_degraded(self):
        """Test advisory for degraded provider"""
        result = self.advisor.compute_advisory("openai", {
            "health_score": 60.0,
            "total_requests": 100,
            "error_rate": 8.0,
            "drift_rate": 5.0,
        })

        assert result is not None
        assert result.severity == DegradationSeverity.DEGRADED
        assert result.score_multiplier == 0.5

    def test_compute_advisory_critical(self):
        """Test advisory for critical provider"""
        result = self.advisor.compute_advisory("openai", {
            "health_score": 30.0,
            "total_requests": 100,
            "error_rate": 15.0,
            "drift_rate": 10.0,
        })

        assert result is not None
        assert result.severity == DegradationSeverity.CRITICAL
        assert result.score_multiplier == 0.25

    def test_compute_advisory_avoid(self):
        """Test advisory for avoid provider"""
        result = self.advisor.compute_advisory("openai", {
            "health_score": 10.0,
            "total_requests": 100,
            "error_rate": 30.0,
            "drift_rate": 20.0,
        })

        assert result is not None
        assert result.severity == DegradationSeverity.AVOID
        assert result.score_multiplier == 0.0

    def test_state_tracking(self):
        """Test that advisor tracks provider states"""
        self.advisor.compute_advisory("openai", {
            "health_score": 60.0,
            "total_requests": 100,
        })

        state = self.advisor.get_provider_state("openai")
        assert state == DegradationSeverity.DEGRADED

    def test_state_change_detection(self):
        """Test state change detection"""
        # First advisory - HEALTHY
        result1 = self.advisor.compute_advisory("openai", {
            "health_score": 90.0,
            "total_requests": 100,
        })
        assert result1.previous_severity is None

        # Second advisory - DEGRADED (state change)
        result2 = self.advisor.compute_advisory("openai", {
            "health_score": 60.0,
            "total_requests": 100,
        })
        assert result2.previous_severity == DegradationSeverity.HEALTHY
        assert result2.is_state_change is True

    def test_clear_state(self):
        """Test state clearing"""
        self.advisor.compute_advisory("openai", {
            "health_score": 60.0,
            "total_requests": 100,
        })

        self.advisor.clear_state("openai")
        assert self.advisor.get_provider_state("openai") is None

    def test_clear_all_states(self):
        """Test clearing all states"""
        self.advisor.compute_advisory("openai", {
            "health_score": 60.0,
            "total_requests": 100,
        })
        self.advisor.compute_advisory("gemini", {
            "health_score": 70.0,
            "total_requests": 100,
        })

        self.advisor.clear_state()
        assert self.advisor.get_all_states() == {}

    def test_floor_protection(self):
        """Test floor provider protection"""
        # Create advisories that would all be AVOID
        advisories = {}
        providers_health = {}

        for provider in ["openai", "gemini"]:
            rec = DegradationRecommendation(
                provider=provider,
                severity=DegradationSeverity.AVOID,
                score_multiplier=0.0,
                health_score=10.0,
                health_score_normalized=0.1,
                reason="test",
            )
            advisories[provider] = rec
            providers_health[provider] = {"health_score": 10.0 if provider == "openai" else 15.0}

        # Apply floor protection
        protected = self.advisor._apply_floor_protection(advisories, providers_health)

        # gemini has higher health score, should be protected
        assert protected["gemini"].severity == DegradationSeverity.CRITICAL
        assert protected["gemini"].floor_protected is True
        assert protected["openai"].severity == DegradationSeverity.AVOID

    def test_floor_protection_disabled(self):
        """Test floor protection when disabled"""
        advisor = DegradationAdvisor(
            enabled=True,
            floor_provider_count=0,  # Disabled
        )

        advisories = {
            "openai": DegradationRecommendation(
                provider="openai",
                severity=DegradationSeverity.AVOID,
                score_multiplier=0.0,
                health_score=10.0,
                health_score_normalized=0.1,
                reason="test",
            )
        }

        protected = advisor._apply_floor_protection(advisories, {})
        assert protected["openai"].severity == DegradationSeverity.AVOID


class TestDegradationAdvisorIntegration:
    """Integration tests for DegradationAdvisor with mocked metrics"""

    def setup_method(self):
        """Set up test fixtures"""
        reset_degradation_advisor()

    def teardown_method(self):
        """Clean up after tests"""
        reset_degradation_advisor()

    @patch('metrics.get_canary_metrics')
    def test_compute_all_advisories_metrics_unavailable(self, mock_get_metrics):
        """Test compute_all_advisories when metrics unavailable"""
        mock_get_metrics.return_value = None

        advisor = DegradationAdvisor(enabled=True)
        result = advisor.compute_all_advisories()

        assert result["enabled"] is True
        assert result["error"] == "metrics_unavailable"

    @patch('metrics.get_canary_metrics')
    def test_compute_all_advisories_success(self, mock_get_metrics):
        """Test compute_all_advisories with mocked metrics"""
        mock_metrics = MagicMock()
        mock_metrics.get_all_providers_health.return_value = {
            "enabled": True,
            "providers": {
                "openai": {
                    "health_score": 90.0,
                    "metrics": {
                        "total_requests": 100,
                        "error_rate": 1.0,
                        "drift_rate": 2.0,
                        "latency": {"p95_ms": 500},
                    },
                },
                "gemini": {
                    "health_score": 60.0,
                    "metrics": {
                        "total_requests": 50,
                        "error_rate": 8.0,
                        "drift_rate": 5.0,
                        "latency": {"p95_ms": 1000},
                    },
                },
            },
        }
        mock_get_metrics.return_value = mock_metrics

        advisor = DegradationAdvisor(enabled=True, min_requests=10)
        result = advisor.compute_all_advisories(providers=["openai", "gemini"])

        assert result["enabled"] is True
        assert "openai" in result["advisories"]
        assert "gemini" in result["advisories"]
        assert result["advisories"]["openai"]["severity"] == "healthy"
        assert result["advisories"]["gemini"]["severity"] == "degraded"
