#!/usr/bin/env python3
"""
Unit tests for Phase 3 metrics module

Tests Phase3Metrics for ProjectEngineerAgent monitoring.
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Add orchestrator to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase3_metrics import (
    Phase3Metrics,
    DEFAULT_PHASE3_BUCKETS_MS,
    create_phase3_metrics
)


class TestPhase3MetricsInit:
    """Test Phase3Metrics initialization"""

    def test_init_with_defaults(self):
        """Should initialize with default values"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock)
        assert metrics.enabled is True
        assert metrics.ttl_seconds == 7200
        assert metrics.buckets_ms == DEFAULT_PHASE3_BUCKETS_MS

    def test_init_disabled(self):
        """Should respect enabled=False"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        assert metrics.enabled is False

    def test_factory_function(self):
        """Factory function should create instance"""
        redis_mock = Mock()
        metrics = create_phase3_metrics(redis_mock, enabled=True)
        assert isinstance(metrics, Phase3Metrics)
        assert metrics.enabled is True


class TestPhase3CounterMetrics:
    """Test counter increment operations"""

    def test_incr_counter_when_enabled(self):
        """Should increment counter when enabled"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.set = Mock()
        redis_mock.incrby = Mock()
        redis_mock.execute = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=True)
        metrics.incr_counter("pe.task.success")
        assert redis_mock.set.called
        assert redis_mock.incrby.called

    def test_incr_counter_when_disabled(self):
        """Should not increment counter when disabled"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        metrics.incr_counter("pe.task.success")
        assert not redis_mock.pipeline.called

    def test_incr_counter_handles_redis_error(self):
        """Should handle Redis errors gracefully"""
        redis_mock = Mock()
        redis_mock.pipeline.side_effect = Exception("Redis error")
        metrics = Phase3Metrics(redis_mock, enabled=True)
        # Should not raise
        metrics.incr_counter("pe.task.success")


class TestPhase3LatencyMetrics:
    """Test latency observation operations"""

    def test_observe_latency_uses_correct_bucket(self):
        """Should use smallest bucket that fits latency"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.set = Mock()
        redis_mock.incr = Mock()
        redis_mock.execute = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=True)
        # 3000ms should go into 5000ms bucket
        metrics.observe_latency_ms(3000.0)
        call_args = str(redis_mock.incr.call_args)
        assert "bucket_5000" in call_args

    def test_observe_latency_uses_inf_bucket_for_large_values(self):
        """Should use inf bucket for values exceeding all buckets"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.set = Mock()
        redis_mock.incr = Mock()
        redis_mock.execute = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=True)
        # 500000ms exceeds all buckets
        metrics.observe_latency_ms(500000.0)
        call_args = str(redis_mock.incr.call_args)
        assert "bucket_inf" in call_args

    def test_observe_latency_when_disabled(self):
        """Should not observe latency when disabled"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        metrics.observe_latency_ms(1000.0)
        assert not redis_mock.pipeline.called


class TestPhase3TaskExecution:
    """Test task execution recording"""

    def test_record_task_execution_success(self):
        """Should record successful task execution"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.set = Mock()
        redis_mock.incrby = Mock()
        redis_mock.incr = Mock()
        redis_mock.execute = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=True)
        metrics.record_task_execution(
            task_id="test-123",
            status="success",
            task_type="documentation_update",
            elapsed_ms=5000.0,
            mode="analysis_only",
            tenant_id="tenant-456"
        )
        # Should have called pipeline multiple times for different counters
        assert redis_mock.pipeline.call_count >= 3

    def test_record_task_execution_when_disabled(self):
        """Should not record when disabled"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        metrics.record_task_execution(
            task_id="test-123",
            status="success",
            task_type="documentation_update",
            elapsed_ms=5000.0
        )
        assert not redis_mock.pipeline.called


class TestPhase3RuleViolations:
    """Test semantic rule violation recording"""

    def test_record_semantic_rule_violation(self):
        """Should record rule violation"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.set = Mock()
        redis_mock.incrby = Mock()
        redis_mock.execute = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=True)
        metrics.record_semantic_rule_violation(
            task_id="test-123",
            rule_type="repo_whitelist",
            details="Repo not in whitelist"
        )
        assert redis_mock.pipeline.called

    def test_record_timeout(self):
        """Should record timeout event"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.set = Mock()
        redis_mock.incrby = Mock()
        redis_mock.execute = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=True)
        metrics.record_timeout(
            task_id="test-123",
            timeout_seconds=300,
            elapsed_ms=300000.0
        )
        assert redis_mock.pipeline.called


class TestPhase3Summary:
    """Test Phase 3 summary generation"""

    def test_get_phase3_summary_when_disabled(self):
        """Should return disabled message when disabled"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        summary = metrics.get_phase3_summary()
        assert summary['enabled'] is False
        assert 'disabled' in summary.get('message', '').lower()

    def test_get_phase3_summary_with_no_data(self):
        """Should return zeros when no data"""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        pipeline_mock = Mock()
        pipeline_mock.execute.return_value = [None] * 200
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        metrics = Phase3Metrics(redis_mock, enabled=True)
        summary = metrics.get_phase3_summary()
        assert summary['enabled'] is True
        assert summary['counts']['total_tasks'] == 0
        assert summary['rates']['success_rate'] == 0

    def test_get_phase3_summary_structure(self):
        """Should return correct structure"""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        pipeline_mock = Mock()
        pipeline_mock.execute.return_value = [None] * 200
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        metrics = Phase3Metrics(redis_mock, enabled=True)
        summary = metrics.get_phase3_summary()
        # Check structure
        assert 'enabled' in summary
        assert 'window_minutes' in summary
        assert 'timestamp' in summary
        assert 'counts' in summary
        assert 'rates' in summary
        assert 'latency' in summary
        assert 'rule_violations' in summary
        # Check counts structure
        counts = summary['counts']
        assert 'task_success' in counts
        assert 'task_failed' in counts
        assert 'task_timeout' in counts
        assert 'total_tasks' in counts
        # Check rates structure
        rates = summary['rates']
        assert 'success_rate' in rates
        assert 'failure_rate' in rates
        assert 'timeout_rate' in rates
        # Check latency structure
        latency = summary['latency']
        assert 'p50_ms' in latency
        assert 'p90_ms' in latency
        assert 'p95_ms' in latency
        assert 'p99_ms' in latency


class TestPhase3PercentileCalculation:
    """Test percentile calculation for Phase 3"""

    def test_percentiles_with_no_data(self):
        """Should return None for all percentiles when no data"""
        redis_mock = Mock()
        pipeline_mock = Mock()
        # No data in any bucket
        results = [None] * (len(DEFAULT_PHASE3_BUCKETS_MS) * 15 + 15)
        pipeline_mock.execute.return_value = results
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        metrics = Phase3Metrics(redis_mock, enabled=True)
        percentiles = metrics.get_latency_percentiles(window_minutes=15)
        assert percentiles['p50'] is None
        assert percentiles['p90'] is None
        assert percentiles['p95'] is None
        assert percentiles['p99'] is None

    def test_percentiles_when_disabled(self):
        """Should return None for all percentiles when disabled"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        percentiles = metrics.get_latency_percentiles()
        assert percentiles['p50'] is None
        assert percentiles['p90'] is None
        assert percentiles['p95'] is None
        assert percentiles['p99'] is None


class TestPhase3WindowCounts:
    """Test window count retrieval"""

    def test_get_window_counts_when_disabled(self):
        """Should return 0 when disabled"""
        redis_mock = Mock()
        metrics = Phase3Metrics(redis_mock, enabled=False)
        count = metrics.get_window_counts("pe.task.success")
        assert count == 0

    def test_get_window_counts_aggregates_minutes(self):
        """Should aggregate counts across minute buckets"""
        redis_mock = Mock()
        # Return 10 for each minute bucket
        redis_mock.get.return_value = "10"
        metrics = Phase3Metrics(redis_mock, enabled=True)
        count = metrics.get_window_counts("pe.task.success", window_minutes=15)
        # 15 minutes * 10 per minute = 150
        assert count == 150

    def test_get_window_counts_handles_none_values(self):
        """Should handle None values in buckets"""
        redis_mock = Mock()
        # Alternate between 10 and None
        redis_mock.get.side_effect = [
            "10", None, "10", None, "10", None, "10", None,
            "10", None, "10", None, "10", None, "10"
        ]
        metrics = Phase3Metrics(redis_mock, enabled=True)
        count = metrics.get_window_counts("pe.task.success", window_minutes=15)
        # 8 buckets with 10 = 80
        assert count == 80


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
