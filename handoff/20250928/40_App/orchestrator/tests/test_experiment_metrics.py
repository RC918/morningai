#!/usr/bin/env python3
"""
Unit tests for ExperimentMetrics module - Phase 6 (#1825)

Tests for MetricsCollector, ExperimentAnalyzer, and related classes.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiment_metrics import (  # noqa: E402
    MetricsCollector,
    ExperimentAnalyzer,
    ExperimentMetrics,
    MetricDataPoint,
    StatisticalResult,
    ExperimentConclusion,
    ExperimentType,
    MetricType,
    ExperimentStatus,
    ConclusionReason,
    get_metrics_collector,
    get_experiment_analyzer,
    reset_metrics_collector,
    reset_experiment_analyzer,
)


class TestExperimentMetrics:
    """Tests for ExperimentMetrics dataclass"""

    def test_create_experiment_metrics(self):
        """Test creating experiment metrics"""
        metrics = ExperimentMetrics(
            experiment_name="test_experiment",
            variant="control"
        )
        assert metrics.experiment_name == "test_experiment"
        assert metrics.variant == "control"
        assert metrics.sample_size == 0
        assert metrics.success_count == 0

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=80,
            total_requests=100
        )
        assert metrics.success_rate == 0.8

    def test_success_rate_zero_requests(self):
        """Test success rate with zero requests"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            total_requests=0
        )
        assert metrics.success_rate == 0.0

    def test_error_rate_calculation(self):
        """Test error rate calculation"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            failure_count=20,
            total_requests=100
        )
        assert metrics.error_rate == 0.2

    def test_avg_completion_time(self):
        """Test average completion time calculation"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=10,
            total_completion_time_ms=5000.0
        )
        assert metrics.avg_completion_time_ms == 500.0

    def test_merge_rate_calculation(self):
        """Test merge rate calculation"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=100,
            merge_count=75
        )
        assert metrics.merge_rate == 0.75

    def test_latency_percentiles(self):
        """Test latency percentile calculations"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            latencies=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        )
        # p50 with 10 elements: index = int(10 * 50 / 100) = 5, returns 6th element (600)
        assert metrics.latency_p50 == 600
        assert metrics.latency_p95 == 1000
        assert metrics.latency_p99 == 1000

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=80,
            failure_count=20,
            total_requests=100
        )
        d = metrics.to_dict()
        assert d["experiment_name"] == "test"
        assert d["variant"] == "control"
        assert d["success_rate"] == 0.8
        assert d["error_rate"] == 0.2


class TestMetricsCollector:
    """Tests for MetricsCollector class"""

    def test_init(self):
        """Test MetricsCollector initialization"""
        collector = MetricsCollector(max_data_points=1000)
        assert collector._max_data_points == 1000

    def test_record_success(self):
        """Test recording a success"""
        collector = MetricsCollector()
        collector.record_success(
            experiment_name="test_exp",
            variant="treatment",
            completion_time_ms=1500,
            trace_id="trace-123",
            merged=True
        )

        metrics = collector.get_metrics("test_exp")
        assert metrics["treatment"].success_count == 1
        assert metrics["treatment"].total_requests == 1
        assert metrics["treatment"].merge_count == 1

    def test_record_failure(self):
        """Test recording a failure"""
        collector = MetricsCollector()
        collector.record_failure(
            experiment_name="test_exp",
            variant="control",
            trace_id="trace-456",
            error_type="timeout"
        )

        metrics = collector.get_metrics("test_exp")
        assert metrics["control"].failure_count == 1
        assert metrics["control"].total_requests == 1

    def test_record_latency(self):
        """Test recording latency"""
        collector = MetricsCollector()
        collector.record_latency(
            experiment_name="test_exp",
            variant="treatment",
            latency_ms=250.0
        )

        metrics = collector.get_metrics("test_exp")
        assert 250.0 in metrics["treatment"].latencies

    def test_multiple_records(self):
        """Test recording multiple data points"""
        collector = MetricsCollector()

        for i in range(10):
            collector.record_success(
                experiment_name="test_exp",
                variant="control",
                completion_time_ms=100 + i * 10
            )

        for i in range(5):
            collector.record_success(
                experiment_name="test_exp",
                variant="treatment",
                completion_time_ms=90 + i * 10
            )

        metrics = collector.get_metrics("test_exp")
        assert metrics["control"].success_count == 10
        assert metrics["treatment"].success_count == 5

    def test_get_all_experiments(self):
        """Test getting list of all experiments"""
        collector = MetricsCollector()
        collector.record_success("exp1", "control", 100)
        collector.record_success("exp2", "treatment", 200)

        experiments = collector.get_all_experiments()
        assert "exp1" in experiments
        assert "exp2" in experiments

    def test_clear_metrics(self):
        """Test clearing metrics"""
        collector = MetricsCollector()
        collector.record_success("test_exp", "control", 100)
        collector.clear_metrics("test_exp")

        experiments = collector.get_all_experiments()
        assert "test_exp" not in experiments

    def test_clear_all_metrics(self):
        """Test clearing all metrics"""
        collector = MetricsCollector()
        collector.record_success("exp1", "control", 100)
        collector.record_success("exp2", "treatment", 200)
        collector.clear_metrics()

        experiments = collector.get_all_experiments()
        assert len(experiments) == 0

    def test_max_data_points_limit(self):
        """Test that data points are trimmed when exceeding max"""
        collector = MetricsCollector(max_data_points=10)

        for i in range(20):
            collector.record_success("test_exp", "control", 100)

        # Should only keep last 10 data points
        assert len(collector._data_points["test_exp"]) == 10


class TestExperimentAnalyzer:
    """Tests for ExperimentAnalyzer class"""

    def test_init(self):
        """Test ExperimentAnalyzer initialization"""
        analyzer = ExperimentAnalyzer(
            confidence_level=0.95,
            min_sample_size=100
        )
        assert analyzer.confidence_level == 0.95
        assert analyzer.min_sample_size == 100

    def test_analyze_significant_improvement(self):
        """Test analyzing significant improvement"""
        analyzer = ExperimentAnalyzer(
            confidence_level=0.95,
            min_sample_size=50
        )

        control = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=500,
            total_requests=1000
        )
        treatment = ExperimentMetrics(
            experiment_name="test",
            variant="treatment",
            success_count=600,
            total_requests=1000
        )

        result = analyzer.analyze(control, treatment)
        assert result.is_significant is True
        assert result.relative_improvement > 0
        assert result.p_value < 0.05

    def test_analyze_no_significant_difference(self):
        """Test analyzing no significant difference"""
        analyzer = ExperimentAnalyzer(
            confidence_level=0.95,
            min_sample_size=50
        )

        control = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=500,
            total_requests=1000
        )
        treatment = ExperimentMetrics(
            experiment_name="test",
            variant="treatment",
            success_count=505,
            total_requests=1000
        )

        result = analyzer.analyze(control, treatment)
        # Small difference should not be significant
        assert result.is_significant is False

    def test_analyze_insufficient_sample_size(self):
        """Test analyzing with insufficient sample size"""
        analyzer = ExperimentAnalyzer(
            confidence_level=0.95,
            min_sample_size=100
        )

        control = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            success_count=8,
            total_requests=10
        )
        treatment = ExperimentMetrics(
            experiment_name="test",
            variant="treatment",
            success_count=9,
            total_requests=10
        )

        result = analyzer.analyze(control, treatment)
        assert result.is_significant is False

    def test_analyze_zero_requests(self):
        """Test analyzing with zero requests"""
        analyzer = ExperimentAnalyzer()

        control = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            total_requests=0
        )
        treatment = ExperimentMetrics(
            experiment_name="test",
            variant="treatment",
            total_requests=0
        )

        result = analyzer.analyze(control, treatment)
        assert result.is_significant is False
        assert result.p_value == 1.0

    def test_check_safety_threshold_safe(self):
        """Test safety threshold check - safe"""
        analyzer = ExperimentAnalyzer(safety_threshold=0.1)

        control = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            failure_count=10,
            total_requests=100
        )
        treatment = ExperimentMetrics(
            experiment_name="test",
            variant="treatment",
            failure_count=12,
            total_requests=100
        )

        is_safe, reason = analyzer.check_safety_threshold(control, treatment)
        assert is_safe is True

    def test_check_safety_threshold_unsafe(self):
        """Test safety threshold check - unsafe"""
        analyzer = ExperimentAnalyzer(safety_threshold=0.1)

        control = ExperimentMetrics(
            experiment_name="test",
            variant="control",
            failure_count=10,
            total_requests=100
        )
        treatment = ExperimentMetrics(
            experiment_name="test",
            variant="treatment",
            failure_count=25,
            total_requests=100
        )

        is_safe, reason = analyzer.check_safety_threshold(control, treatment)
        assert is_safe is False
        assert "safety threshold" in reason

    def test_should_conclude_significant(self):
        """Test should_conclude with significant results"""
        analyzer = ExperimentAnalyzer(
            confidence_level=0.95,
            min_sample_size=50
        )

        control = ExperimentMetrics(
            experiment_name="test_exp",
            variant="control",
            success_count=500,
            total_requests=1000
        )
        treatment = ExperimentMetrics(
            experiment_name="test_exp",
            variant="treatment",
            success_count=600,
            total_requests=1000
        )

        conclusion = analyzer.should_conclude(
            "test_exp", control, treatment
        )

        assert conclusion is not None
        assert conclusion.winner == "treatment"
        assert conclusion.reason == ConclusionReason.STATISTICAL_SIGNIFICANCE

    def test_should_conclude_safety_violation(self):
        """Test should_conclude with safety violation"""
        analyzer = ExperimentAnalyzer(safety_threshold=0.1)

        control = ExperimentMetrics(
            experiment_name="test_exp",
            variant="control",
            failure_count=10,
            total_requests=100
        )
        treatment = ExperimentMetrics(
            experiment_name="test_exp",
            variant="treatment",
            failure_count=30,
            total_requests=100
        )

        conclusion = analyzer.should_conclude(
            "test_exp", control, treatment
        )

        assert conclusion is not None
        assert conclusion.winner == "control"
        assert conclusion.reason == ConclusionReason.SAFETY_THRESHOLD

    def test_should_conclude_insufficient_data(self):
        """Test should_conclude with insufficient data"""
        analyzer = ExperimentAnalyzer(min_sample_size=100)

        control = ExperimentMetrics(
            experiment_name="test_exp",
            variant="control",
            success_count=8,
            total_requests=10
        )
        treatment = ExperimentMetrics(
            experiment_name="test_exp",
            variant="treatment",
            success_count=9,
            total_requests=10
        )

        conclusion = analyzer.should_conclude(
            "test_exp", control, treatment
        )

        # Should return None - not enough data yet
        assert conclusion is None

    def test_should_conclude_timeout(self):
        """Test should_conclude with timeout"""
        analyzer = ExperimentAnalyzer(
            min_sample_size=100,
            max_duration_days=30
        )

        control = ExperimentMetrics(
            experiment_name="test_exp",
            variant="control",
            success_count=8,
            total_requests=10
        )
        treatment = ExperimentMetrics(
            experiment_name="test_exp",
            variant="treatment",
            success_count=9,
            total_requests=10
        )

        # Set experiment start to 31 days ago
        experiment_start = datetime.utcnow() - timedelta(days=31)

        conclusion = analyzer.should_conclude(
            "test_exp", control, treatment, experiment_start
        )

        assert conclusion is not None
        assert conclusion.reason == ConclusionReason.INSUFFICIENT_DATA

    def test_generate_report(self):
        """Test generating experiment report"""
        analyzer = ExperimentAnalyzer(min_sample_size=50)

        control = ExperimentMetrics(
            experiment_name="test_exp",
            variant="control",
            success_count=500,
            failure_count=100,
            total_requests=600,
            total_completion_time_ms=50000
        )
        treatment = ExperimentMetrics(
            experiment_name="test_exp",
            variant="treatment",
            success_count=550,
            failure_count=50,
            total_requests=600,
            total_completion_time_ms=45000
        )

        report = analyzer.generate_report(
            "test_exp", control, treatment
        )

        assert report["experiment_name"] == "test_exp"
        assert "metrics" in report
        assert "analysis" in report
        assert "summary" in report
        assert report["metrics"]["control"]["success_rate"] > 0
        assert report["metrics"]["treatment"]["success_rate"] > 0


class TestStatisticalResult:
    """Tests for StatisticalResult dataclass"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = StatisticalResult(
            is_significant=True,
            p_value=0.01,
            confidence_level=0.95,
            effect_size=0.2,
            relative_improvement=10.0,
            sample_size_control=1000,
            sample_size_treatment=1000,
            power=0.8
        )

        d = result.to_dict()
        assert d["is_significant"] is True
        assert d["p_value"] == 0.01
        assert d["confidence_level"] == 0.95
        assert d["relative_improvement"] == 10.0


class TestExperimentConclusion:
    """Tests for ExperimentConclusion dataclass"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        conclusion = ExperimentConclusion(
            experiment_name="test_exp",
            winner="treatment",
            reason=ConclusionReason.STATISTICAL_SIGNIFICANCE,
            statistical_result=None,
            recommendation="Roll out treatment"
        )

        d = conclusion.to_dict()
        assert d["experiment_name"] == "test_exp"
        assert d["winner"] == "treatment"
        assert d["reason"] == "statistical_significance"
        assert d["recommendation"] == "Roll out treatment"


class TestEnums:
    """Tests for enum types"""

    def test_experiment_type_values(self):
        """Test ExperimentType enum values"""
        assert ExperimentType.LLM_PROVIDER.value == "llm_provider"
        assert ExperimentType.FEATURE_FLAG.value == "feature_flag"
        assert ExperimentType.UI_EXPERIMENT.value == "ui_experiment"
        assert ExperimentType.ALGORITHM.value == "algorithm"
        assert ExperimentType.CANARY.value == "canary"

    def test_metric_type_values(self):
        """Test MetricType enum values"""
        assert MetricType.SUCCESS_RATE.value == "success_rate"
        assert MetricType.COMPLETION_TIME_MS.value == "completion_time_ms"
        assert MetricType.MERGE_RATE.value == "merge_rate"
        assert MetricType.ERROR_RATE.value == "error_rate"

    def test_experiment_status_values(self):
        """Test ExperimentStatus enum values"""
        assert ExperimentStatus.DRAFT.value == "draft"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.CONCLUDED.value == "concluded"

    def test_conclusion_reason_values(self):
        """Test ConclusionReason enum values"""
        assert ConclusionReason.STATISTICAL_SIGNIFICANCE.value == "statistical_significance"
        assert ConclusionReason.SAFETY_THRESHOLD.value == "safety_threshold"
        assert ConclusionReason.TIMEOUT.value == "timeout"


class TestGlobalInstances:
    """Tests for global instance functions"""

    def test_get_metrics_collector(self):
        """Test get_metrics_collector returns singleton"""
        reset_metrics_collector()
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    def test_get_experiment_analyzer(self):
        """Test get_experiment_analyzer returns singleton"""
        reset_experiment_analyzer()
        analyzer1 = get_experiment_analyzer()
        analyzer2 = get_experiment_analyzer()
        assert analyzer1 is analyzer2

    def test_reset_metrics_collector(self):
        """Test reset_metrics_collector clears singleton"""
        collector1 = get_metrics_collector()
        reset_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is not collector2

    def test_reset_experiment_analyzer(self):
        """Test reset_experiment_analyzer clears singleton"""
        analyzer1 = get_experiment_analyzer()
        reset_experiment_analyzer()
        analyzer2 = get_experiment_analyzer()
        assert analyzer1 is not analyzer2


class TestMetricDataPoint:
    """Tests for MetricDataPoint dataclass"""

    def test_create_data_point(self):
        """Test creating a metric data point"""
        dp = MetricDataPoint(
            experiment_name="test_exp",
            variant="treatment",
            metric_type=MetricType.SUCCESS_RATE,
            value=1.0,
            trace_id="trace-123"
        )

        assert dp.experiment_name == "test_exp"
        assert dp.variant == "treatment"
        assert dp.metric_type == MetricType.SUCCESS_RATE
        assert dp.value == 1.0
        assert dp.trace_id == "trace-123"
        assert dp.timestamp is not None

    def test_data_point_with_metadata(self):
        """Test creating a data point with metadata"""
        dp = MetricDataPoint(
            experiment_name="test_exp",
            variant="control",
            metric_type=MetricType.COMPLETION_TIME_MS,
            value=500.0,
            metadata={"component": "planner", "model": "gpt-4"}
        )

        assert dp.metadata["component"] == "planner"
        assert dp.metadata["model"] == "gpt-4"
