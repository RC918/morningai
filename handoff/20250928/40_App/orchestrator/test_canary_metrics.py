#!/usr/bin/env python3
"""
Unit tests for canary metrics module

Tests histogram logic, percentile calculation, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from metrics import CanaryMetrics, DEFAULT_BUCKETS_MS


class TestHistogramLogic:
    """Test histogram bucket increment logic"""
    
    def test_observe_latency_increments_single_bucket(self):
        """Single observation should increment exactly one bucket"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.incr = Mock()
        redis_mock.expire = Mock()
        redis_mock.execute = Mock()
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        
        metrics.observe_latency_ms(150.0)
        
        assert redis_mock.incr.call_count == 1
        
        call_args = redis_mock.incr.call_args
        assert "latency.bucket_200" in str(call_args)
    
    def test_observe_latency_uses_inf_bucket_for_large_values(self):
        """Latency exceeding all buckets should use inf bucket"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.incr = Mock()
        redis_mock.expire = Mock()
        redis_mock.execute = Mock()
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        
        metrics.observe_latency_ms(10000.0)
        
        call_args = redis_mock.incr.call_args
        assert "latency.bucket_inf" in str(call_args)
    
    def test_observe_latency_uses_smallest_matching_bucket(self):
        """Should use the smallest bucket that fits the latency"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.incr = Mock()
        redis_mock.expire = Mock()
        redis_mock.execute = Mock()
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        
        metrics.observe_latency_ms(50.0)
        
        call_args = redis_mock.incr.call_args
        assert "latency.bucket_50" in str(call_args)
    
    def test_observe_latency_ttl_set_with_nx(self):
        """TTL should be set with nx=True to avoid extending on subsequent increments"""
        redis_mock = Mock()
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=redis_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        redis_mock.incr = Mock()
        redis_mock.expire = Mock()
        redis_mock.execute = Mock()
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        metrics.observe_latency_ms(100.0)
        
        assert redis_mock.expire.call_count == 1
        call_args = redis_mock.expire.call_args
        assert call_args[1]['nx'] is True


class TestPercentileCalculation:
    """Test percentile calculation logic"""
    
    def test_percentiles_with_all_in_one_bucket(self):
        """All observations in one bucket should return that bucket for all percentiles"""
        redis_mock = Mock()
        
        pipeline_mock = Mock()
        results = []
        for bucket in DEFAULT_BUCKETS_MS:
            for _ in range(15):  # 15 minute window
                if bucket == 200:
                    results.append(b'100')
                else:
                    results.append(None)
        for _ in range(15):
            results.append(None)
        
        pipeline_mock.execute.return_value = results
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        percentiles = metrics.get_latency_percentiles(window_minutes=15)
        
        assert percentiles['p50'] == 200.0
        assert percentiles['p90'] == 200.0
        assert percentiles['p95'] == 200.0
        assert percentiles['p99'] == 200.0
    
    def test_percentiles_with_uniform_distribution(self):
        """Uniform distribution across buckets should calculate correctly"""
        redis_mock = Mock()
        
        pipeline_mock = Mock()
        results = []
        for bucket in DEFAULT_BUCKETS_MS:
            for _ in range(15):
                results.append(b'10')
        for _ in range(15):
            results.append(None)
        
        pipeline_mock.execute.return_value = results
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        percentiles = metrics.get_latency_percentiles(window_minutes=15)
        
        assert percentiles['p50'] == 400.0
        assert percentiles['p90'] == 3200.0
        assert percentiles['p95'] == 3200.0
        assert percentiles['p99'] == 3200.0
    
    def test_percentiles_with_no_data(self):
        """Empty buckets should return None for all percentiles"""
        redis_mock = Mock()
        
        pipeline_mock = Mock()
        results = [None] * (len(DEFAULT_BUCKETS_MS) * 15 + 15)
        pipeline_mock.execute.return_value = results
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        percentiles = metrics.get_latency_percentiles(window_minutes=15)
        
        assert percentiles['p50'] is None
        assert percentiles['p90'] is None
        assert percentiles['p95'] is None
        assert percentiles['p99'] is None
    
    def test_percentiles_with_only_inf_bucket(self):
        """All observations in inf bucket should return None (unbounded tail)"""
        redis_mock = Mock()
        
        pipeline_mock = Mock()
        results = []
        for bucket in DEFAULT_BUCKETS_MS:
            for _ in range(15):
                results.append(None)
        for _ in range(15):
            results.append(b'100')
        
        pipeline_mock.execute.return_value = results
        redis_mock.pipeline.return_value.__enter__ = Mock(return_value=pipeline_mock)
        redis_mock.pipeline.return_value.__exit__ = Mock(return_value=False)
        
        metrics = CanaryMetrics(redis_mock, enabled=True)
        percentiles = metrics.get_latency_percentiles(window_minutes=15)
        
        assert percentiles['p50'] is None
        assert percentiles['p90'] is None
        assert percentiles['p95'] is None
        assert percentiles['p99'] is None


class TestCanaryAlerting:
    """Test canary alerting cooldown logic"""
    
    def test_cooldown_prevents_duplicate_alerts(self):
        """Alert should not fire twice within cooldown period"""
        from canary_alerting import CanaryAlerting
        
        redis_mock = Mock()
        redis_mock.exists.return_value = 0  # First check: not in cooldown
        redis_mock.setex = Mock()
        
        alerting = CanaryAlerting(redis_mock, enabled=True, cooldown_seconds=300)
        
        assert not alerting._is_in_cooldown("test_alert")
        
        alerting._set_cooldown("test_alert")
        assert redis_mock.setex.called
        
        redis_mock.exists.return_value = 1
        assert alerting._is_in_cooldown("test_alert")
    
    def test_slo_evaluation_skips_insufficient_data(self):
        """SLO evaluation should skip when total_planner < 5"""
        from canary_alerting import CanaryAlerting
        
        redis_mock = Mock()
        alerting = CanaryAlerting(redis_mock, enabled=True, sentry_dsn="test")
        alerting.sentry_sdk = Mock()
        
        canary_summary = {
            'enabled': True,
            'counts': {'total_planner': 2},  # Less than 5
            'latency': {'p95_ms': 5000},
            'rates': {'error_5xx_rate': 10, 'failure_rate': 10}
        }
        
        thresholds = {'p95_ms': 2500, 'error_5xx_rate': 1.0, 'failure_rate': 5.0}
        
        alerting.evaluate_slos(canary_summary, thresholds)
        assert not alerting.sentry_sdk.capture_message.called
    
    def test_none_p95_triggers_unbounded_alert(self):
        """p95_ms=None (unbounded tail) should trigger critical alert"""
        from canary_alerting import CanaryAlerting
        
        redis_mock = Mock()
        redis_mock.exists.return_value = 0
        redis_mock.setex = Mock()
        
        alerting = CanaryAlerting(redis_mock, enabled=True, sentry_dsn="test")
        alerting.sentry_sdk = Mock()
        
        canary_summary = {
            'enabled': True,
            'counts': {'total_planner': 10},
            'latency': {'p95_ms': None, 'p90_ms': None, 'p50_ms': None, 'p99_ms': None},
            'rates': {'error_5xx_rate': 0, 'failure_rate': 0},
            'window_minutes': 15
        }
        
        thresholds = {'p95_ms': 2500, 'error_5xx_rate': 1.0, 'failure_rate': 5.0}
        
        alerting.evaluate_slos(canary_summary, thresholds)
        
        assert alerting.sentry_sdk.capture_message.called
        call_args = alerting.sentry_sdk.capture_message.call_args
        assert "unbounded" in call_args[0][0].lower()
        assert call_args[1]['level'] == 'error'
        
        assert redis_mock.setex.called
    
    def test_none_p95_does_not_trigger_normal_threshold_alert(self):
        """p95_ms=None should only trigger unbounded alert, not threshold alert"""
        from canary_alerting import CanaryAlerting
        
        redis_mock = Mock()
        redis_mock.exists.return_value = 0
        redis_mock.setex = Mock()
        
        alerting = CanaryAlerting(redis_mock, enabled=True, sentry_dsn="test")
        alerting.sentry_sdk = Mock()
        
        canary_summary = {
            'enabled': True,
            'counts': {'total_planner': 10},
            'latency': {'p95_ms': None},
            'rates': {'error_5xx_rate': 0, 'failure_rate': 0},
            'window_minutes': 15
        }
        
        thresholds = {'p95_ms': 2500, 'error_5xx_rate': 1.0, 'failure_rate': 5.0}
        
        alerting.evaluate_slos(canary_summary, thresholds)
        
        assert alerting.sentry_sdk.capture_message.call_count == 1
        call_args = alerting.sentry_sdk.capture_message.call_args
        assert "unbounded" in call_args[0][0].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
