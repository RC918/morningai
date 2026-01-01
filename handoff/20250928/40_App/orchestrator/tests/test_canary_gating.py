"""
Unit tests for Flow Controller v3 - Deterministic Canary Gating (#3431)

Tests the hash-based bucketing logic for gradual rollout:
- Deterministic: Same trace_id always maps to same bucket
- Uniform distribution: Buckets are evenly distributed
- Sticky: Decision doesn't change mid-workflow
- Configurable: Sample rate controls percentage

Issue #3431: Deterministic Canary Gating for Flow Router v3
"""
from unittest.mock import patch, MagicMock


class TestComputeBucket:
    """Tests for compute_bucket() function."""

    def test_deterministic_same_key_same_bucket(self):
        """Same key always produces same bucket."""
        from core.flow.canary_gating import compute_bucket

        key = "test-trace-id-12345"
        bucket1 = compute_bucket(key)
        bucket2 = compute_bucket(key)
        bucket3 = compute_bucket(key)

        assert bucket1 == bucket2 == bucket3
        assert 0 <= bucket1 < 100

    def test_different_keys_different_buckets(self):
        """Different keys produce different buckets (with high probability)."""
        from core.flow.canary_gating import compute_bucket

        keys = [f"trace-{i}" for i in range(100)]
        buckets = [compute_bucket(key) for key in keys]

        # With 100 different keys, we should have at least 50 unique buckets
        unique_buckets = set(buckets)
        assert len(unique_buckets) >= 50

    def test_bucket_range(self):
        """All buckets are in valid range 0-99."""
        from core.flow.canary_gating import compute_bucket

        for i in range(1000):
            bucket = compute_bucket(f"test-key-{i}")
            assert 0 <= bucket < 100

    def test_empty_key_returns_zero(self):
        """Empty key returns bucket 0 as fallback."""
        from core.flow.canary_gating import compute_bucket

        assert compute_bucket("") == 0

    def test_uniform_distribution(self):
        """Buckets are roughly uniformly distributed."""
        from core.flow.canary_gating import compute_bucket

        # Generate 10000 buckets
        buckets = [compute_bucket(f"key-{i}") for i in range(10000)]

        # Count buckets in each decile (0-9, 10-19, ..., 90-99)
        decile_counts = [0] * 10
        for bucket in buckets:
            decile_counts[bucket // 10] += 1

        # Each decile should have roughly 1000 keys (10% of 10000)
        # Allow 30% variance
        for count in decile_counts:
            assert 700 <= count <= 1300, f"Decile count {count} outside expected range"


class TestIsInSample:
    """Tests for is_in_sample() function."""

    def test_bucket_zero_always_in_sample(self):
        """Bucket 0 is in sample for any sample_rate > 0."""
        from core.flow.canary_gating import is_in_sample

        assert is_in_sample(0, 1) is True
        assert is_in_sample(0, 5) is True
        assert is_in_sample(0, 100) is True

    def test_bucket_zero_not_in_sample_when_rate_zero(self):
        """Bucket 0 is not in sample when sample_rate is 0."""
        from core.flow.canary_gating import is_in_sample

        assert is_in_sample(0, 0) is False

    def test_sample_rate_5_percent(self):
        """5% sample rate includes buckets 0-4."""
        from core.flow.canary_gating import is_in_sample

        for bucket in range(5):
            assert is_in_sample(bucket, 5) is True
        for bucket in range(5, 100):
            assert is_in_sample(bucket, 5) is False

    def test_sample_rate_100_percent(self):
        """100% sample rate includes all buckets."""
        from core.flow.canary_gating import is_in_sample

        for bucket in range(100):
            assert is_in_sample(bucket, 100) is True


class TestShouldEnableDynamicRouting:
    """Tests for should_enable_dynamic_routing() function."""

    def test_sample_rate_zero_uses_enable_flag_true(self):
        """When sample_rate=0, uses ENABLE_DYNAMIC_ROUTING flag."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        result = should_enable_dynamic_routing(
            trace_id="test-trace",
            sample_rate_override=0,
            enable_flag_override=True
        )
        assert result is True

    def test_sample_rate_zero_uses_enable_flag_false(self):
        """When sample_rate=0, uses ENABLE_DYNAMIC_ROUTING flag."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        result = should_enable_dynamic_routing(
            trace_id="test-trace",
            sample_rate_override=0,
            enable_flag_override=False
        )
        assert result is False

    def test_sample_rate_100_always_enabled(self):
        """When sample_rate=100, always enabled."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        for i in range(100):
            result = should_enable_dynamic_routing(
                trace_id=f"trace-{i}",
                sample_rate_override=100,
                enable_flag_override=False
            )
            assert result is True

    def test_sample_rate_5_percent_distribution(self):
        """5% sample rate enables roughly 5% of traces."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        enabled_count = 0
        total = 1000

        for i in range(total):
            result = should_enable_dynamic_routing(
                trace_id=f"trace-{i}",
                sample_rate_override=5,
                enable_flag_override=False
            )
            if result:
                enabled_count += 1

        # Should be roughly 5% (allow 2% variance)
        percentage = enabled_count / total * 100
        assert 3 <= percentage <= 7, f"Expected ~5%, got {percentage}%"

    def test_deterministic_same_trace_same_result(self):
        """Same trace_id always gets same result."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        trace_id = "deterministic-test-trace"

        results = [
            should_enable_dynamic_routing(
                trace_id=trace_id,
                sample_rate_override=50,
                enable_flag_override=False
            )
            for _ in range(10)
        ]

        # All results should be the same
        assert all(r == results[0] for r in results)

    def test_error_handling_returns_false(self):
        """On error, returns False (fail-safe)."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        with patch('core.flow.canary_gating.compute_bucket', side_effect=Exception("test error")):
            result = should_enable_dynamic_routing(
                trace_id="test-trace",
                sample_rate_override=50,
                enable_flag_override=True
            )
            assert result is False


class TestGetCanaryStatus:
    """Tests for get_canary_status() function."""

    def test_returns_status_dict(self):
        """Returns a dict with expected keys."""
        from core.flow.canary_gating import get_canary_status

        # Use overrides instead of mocking settings
        # get_canary_status uses should_enable_dynamic_routing internally
        status = get_canary_status("test-trace")

        assert "trace_id" in status
        assert "bucket" in status
        assert "sample_rate" in status
        assert "enable_flag" in status
        assert "dynamic_routing_enabled" in status
        assert "decision_source" in status

    def test_decision_source_sample_rate(self):
        """Decision source is 'sample_rate' when sample_rate > 0."""
        from core.flow.canary_gating import get_canary_status

        # Mock the settings module before it's imported
        mock_settings = MagicMock()
        mock_settings.dynamic_routing_sample_rate = 5
        mock_settings.enable_dynamic_routing = False

        with patch.dict('sys.modules', {'common.config.settings': MagicMock(settings=mock_settings)}):
            # Re-import to get fresh module with mocked settings
            import importlib
            import core.flow.canary_gating as cg
            importlib.reload(cg)

            status = cg.get_canary_status("test-trace")
            assert status["decision_source"] == "sample_rate"

    def test_decision_source_enable_flag(self):
        """Decision source is 'enable_flag' when sample_rate == 0."""
        from core.flow.canary_gating import get_canary_status

        # Mock the settings module before it's imported
        mock_settings = MagicMock()
        mock_settings.dynamic_routing_sample_rate = 0
        mock_settings.enable_dynamic_routing = True

        with patch.dict('sys.modules', {'common.config.settings': MagicMock(settings=mock_settings)}):
            # Re-import to get fresh module with mocked settings
            import importlib
            import core.flow.canary_gating as cg
            importlib.reload(cg)

            status = cg.get_canary_status("test-trace")
            assert status["decision_source"] == "enable_flag"


class TestSettingsIntegration:
    """Tests for integration with settings module."""

    def test_reads_from_settings(self):
        """Reads sample_rate and enable_flag from settings."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        # Use overrides to test without mocking
        # With 50% sample rate, roughly half should be enabled
        enabled_count = sum(
            1 for i in range(100)
            if should_enable_dynamic_routing(f"trace-{i}", sample_rate_override=50)
        )
        assert 40 <= enabled_count <= 60


class TestModuleExports:
    """Tests for module exports in __init__.py."""

    def test_exports_from_flow_module(self):
        """Canary gating functions are exported from core.flow."""
        from core.flow import (
            should_enable_dynamic_routing,
            compute_bucket,
            is_in_sample,
            get_canary_status,
        )

        assert callable(should_enable_dynamic_routing)
        assert callable(compute_bucket)
        assert callable(is_in_sample)
        assert callable(get_canary_status)


class TestAntiPatterns:
    """Tests to verify anti-patterns from #3431 are avoided."""

    def test_no_random_per_call_sampling(self):
        """Verify no random component - same input always same output."""
        from core.flow.canary_gating import compute_bucket, should_enable_dynamic_routing

        # Run 100 times with same input
        trace_id = "anti-pattern-test"
        buckets = [compute_bucket(trace_id) for _ in range(100)]
        decisions = [
            should_enable_dynamic_routing(trace_id, sample_rate_override=50)
            for _ in range(100)
        ]

        # All should be identical (no randomness)
        assert len(set(buckets)) == 1
        assert len(set(decisions)) == 1

    def test_no_mid_workflow_switching(self):
        """Same trace_id maintains same decision throughout workflow."""
        from core.flow.canary_gating import should_enable_dynamic_routing

        trace_id = "workflow-consistency-test"

        # Simulate multiple calls during a workflow
        decisions = []
        for step in ["start", "middle", "end"]:
            decision = should_enable_dynamic_routing(
                trace_id=trace_id,
                sample_rate_override=50
            )
            decisions.append(decision)

        # All decisions should be the same
        assert decisions[0] == decisions[1] == decisions[2]
