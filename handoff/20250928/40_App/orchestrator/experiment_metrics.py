#!/usr/bin/env python3
"""
Experiment Metrics Module - Phase 6 (#1825)

End-to-end metrics collection and automated experiment analysis for A/B testing.

Features:
- MetricsCollector: Collects success rate, completion time, merge rate metrics
- ExperimentAnalyzer: Statistical significance calculation and auto-conclusion
- ExperimentReport: Generates experiment result reports

Dependencies:
- experiment_manager: ExperimentManager for variant assignment
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """Types of experiments supported by the framework"""
    LLM_PROVIDER = "llm_provider"  # LLM provider A/B testing (existing)
    FEATURE_FLAG = "feature_flag"  # Feature flag experiments
    UI_EXPERIMENT = "ui_experiment"  # UI/UX experiments
    ALGORITHM = "algorithm"  # Algorithm comparison experiments
    CANARY = "canary"  # Canary deployment experiments


class MetricType(Enum):
    """Types of metrics that can be collected"""
    SUCCESS_RATE = "success_rate"
    COMPLETION_TIME_MS = "completion_time_ms"
    MERGE_RATE = "merge_rate"
    ERROR_RATE = "error_rate"
    LATENCY_P50 = "latency_p50"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"
    THROUGHPUT = "throughput"
    USER_SATISFACTION = "user_satisfaction"


class ExperimentStatus(Enum):
    """Status of an experiment"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    CONCLUDED = "concluded"
    ROLLED_BACK = "rolled_back"


class ConclusionReason(Enum):
    """Reason for experiment conclusion"""
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    MANUAL = "manual"
    TIMEOUT = "timeout"
    SAFETY_THRESHOLD = "safety_threshold"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class MetricDataPoint:
    """A single metric data point"""
    experiment_name: str
    variant: str  # "control" or "treatment"
    metric_type: MetricType
    value: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentMetrics:
    """Aggregated metrics for an experiment variant"""
    experiment_name: str
    variant: str
    sample_size: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_completion_time_ms: float = 0.0
    merge_count: int = 0
    total_requests: int = 0
    latencies: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests
    
    @property
    def avg_completion_time_ms(self) -> float:
        """Calculate average completion time"""
        if self.success_count == 0:
            return 0.0
        return self.total_completion_time_ms / self.success_count
    
    @property
    def merge_rate(self) -> float:
        """Calculate merge rate"""
        if self.success_count == 0:
            return 0.0
        return self.merge_count / self.success_count
    
    @property
    def latency_p50(self) -> float:
        """Calculate 50th percentile latency"""
        return self._percentile(50)
    
    @property
    def latency_p95(self) -> float:
        """Calculate 95th percentile latency"""
        return self._percentile(95)
    
    @property
    def latency_p99(self) -> float:
        """Calculate 99th percentile latency"""
        return self._percentile(99)
    
    def _percentile(self, p: int) -> float:
        """Calculate percentile from latencies"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * p / 100)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "experiment_name": self.experiment_name,
            "variant": self.variant,
            "sample_size": self.sample_size,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_requests": self.total_requests,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "avg_completion_time_ms": self.avg_completion_time_ms,
            "merge_rate": self.merge_rate,
            "merge_count": self.merge_count,
            "latency_p50": self.latency_p50,
            "latency_p95": self.latency_p95,
            "latency_p99": self.latency_p99
        }


@dataclass
class StatisticalResult:
    """Result of statistical significance test"""
    is_significant: bool
    p_value: float
    confidence_level: float
    effect_size: float
    relative_improvement: float  # Percentage improvement of treatment over control
    sample_size_control: int
    sample_size_treatment: int
    power: float  # Statistical power of the test
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_significant": self.is_significant,
            "p_value": self.p_value,
            "confidence_level": self.confidence_level,
            "effect_size": self.effect_size,
            "relative_improvement": self.relative_improvement,
            "sample_size_control": self.sample_size_control,
            "sample_size_treatment": self.sample_size_treatment,
            "power": self.power
        }


@dataclass
class ExperimentConclusion:
    """Conclusion of an experiment"""
    experiment_name: str
    winner: Optional[str]  # "control", "treatment", or None (no winner)
    reason: ConclusionReason
    statistical_result: Optional[StatisticalResult]
    recommendation: str
    concluded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "experiment_name": self.experiment_name,
            "winner": self.winner,
            "reason": self.reason.value,
            "statistical_result": self.statistical_result.to_dict() if self.statistical_result else None,
            "recommendation": self.recommendation,
            "concluded_at": self.concluded_at
        }


class MetricsCollector:
    """
    Collects end-to-end metrics for A/B testing experiments.
    
    Features:
    - Record success/failure events
    - Track completion times
    - Track merge rates
    - Aggregate metrics by experiment and variant
    
    Usage:
        collector = MetricsCollector()
        
        # Record a successful task completion
        collector.record_success(
            experiment_name="gemini_planner_10pct_staging",
            variant="treatment",
            completion_time_ms=1500,
            trace_id="trace-123"
        )
        
        # Get aggregated metrics
        metrics = collector.get_metrics("gemini_planner_10pct_staging")
    """
    
    def __init__(self, max_data_points: int = 100000):
        """
        Initialize MetricsCollector
        
        Args:
            max_data_points: Maximum number of data points to store per experiment
        """
        self._data_points: Dict[str, List[MetricDataPoint]] = defaultdict(list)
        self._metrics_cache: Dict[str, Dict[str, ExperimentMetrics]] = {}
        self._max_data_points = max_data_points
        
        logger.info(
            f"[MetricsCollector] Initialized with max_data_points={max_data_points}"
        )
    
    def record_success(
        self,
        experiment_name: str,
        variant: str,
        completion_time_ms: float,
        trace_id: Optional[str] = None,
        merged: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a successful task completion
        
        Args:
            experiment_name: Name of the experiment
            variant: Variant ("control" or "treatment")
            completion_time_ms: Time to complete the task in milliseconds
            trace_id: Optional trace identifier
            merged: Whether the task resulted in a merge
            metadata: Optional additional metadata
        """
        self._record_data_point(
            experiment_name=experiment_name,
            variant=variant,
            metric_type=MetricType.SUCCESS_RATE,
            value=1.0,
            trace_id=trace_id,
            metadata={
                "completion_time_ms": completion_time_ms,
                "merged": merged,
                **(metadata or {})
            }
        )
        
        # Invalidate cache
        self._invalidate_cache(experiment_name)
        
        logger.debug(
            f"[MetricsCollector] Recorded success for experiment={experiment_name}, "
            f"variant={variant}, completion_time_ms={completion_time_ms}"
        )
    
    def record_failure(
        self,
        experiment_name: str,
        variant: str,
        trace_id: Optional[str] = None,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a task failure
        
        Args:
            experiment_name: Name of the experiment
            variant: Variant ("control" or "treatment")
            trace_id: Optional trace identifier
            error_type: Optional error type classification
            metadata: Optional additional metadata
        """
        self._record_data_point(
            experiment_name=experiment_name,
            variant=variant,
            metric_type=MetricType.ERROR_RATE,
            value=1.0,
            trace_id=trace_id,
            metadata={
                "error_type": error_type,
                **(metadata or {})
            }
        )
        
        # Invalidate cache
        self._invalidate_cache(experiment_name)
        
        logger.debug(
            f"[MetricsCollector] Recorded failure for experiment={experiment_name}, "
            f"variant={variant}, error_type={error_type}"
        )
    
    def record_latency(
        self,
        experiment_name: str,
        variant: str,
        latency_ms: float,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a latency measurement
        
        Args:
            experiment_name: Name of the experiment
            variant: Variant ("control" or "treatment")
            latency_ms: Latency in milliseconds
            trace_id: Optional trace identifier
            metadata: Optional additional metadata
        """
        self._record_data_point(
            experiment_name=experiment_name,
            variant=variant,
            metric_type=MetricType.COMPLETION_TIME_MS,
            value=latency_ms,
            trace_id=trace_id,
            metadata=metadata or {}
        )
        
        # Invalidate cache
        self._invalidate_cache(experiment_name)
    
    def _record_data_point(
        self,
        experiment_name: str,
        variant: str,
        metric_type: MetricType,
        value: float,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a single data point"""
        data_point = MetricDataPoint(
            experiment_name=experiment_name,
            variant=variant,
            metric_type=metric_type,
            value=value,
            trace_id=trace_id,
            metadata=metadata or {}
        )
        
        key = experiment_name
        self._data_points[key].append(data_point)
        
        # Trim old data points if exceeding max
        if len(self._data_points[key]) > self._max_data_points:
            self._data_points[key] = self._data_points[key][-self._max_data_points:]
    
    def _invalidate_cache(self, experiment_name: str) -> None:
        """Invalidate metrics cache for an experiment"""
        if experiment_name in self._metrics_cache:
            del self._metrics_cache[experiment_name]
    
    def get_metrics(
        self,
        experiment_name: str,
        since: Optional[datetime] = None
    ) -> Dict[str, ExperimentMetrics]:
        """
        Get aggregated metrics for an experiment
        
        Args:
            experiment_name: Name of the experiment
            since: Optional datetime to filter data points from
        
        Returns:
            Dict mapping variant to ExperimentMetrics
        """
        # Check cache
        cache_key = experiment_name
        if cache_key in self._metrics_cache and since is None:
            return self._metrics_cache[cache_key]
        
        # Aggregate metrics
        metrics: Dict[str, ExperimentMetrics] = {
            "control": ExperimentMetrics(experiment_name=experiment_name, variant="control"),
            "treatment": ExperimentMetrics(experiment_name=experiment_name, variant="treatment")
        }
        
        data_points = self._data_points.get(experiment_name, [])
        
        for dp in data_points:
            # Filter by time if specified
            if since is not None:
                dp_time = datetime.fromisoformat(dp.timestamp.replace('Z', '+00:00'))
                if dp_time < since:
                    continue
            
            variant = dp.variant
            if variant not in metrics:
                continue
            
            m = metrics[variant]
            m.sample_size += 1
            m.total_requests += 1
            
            if dp.metric_type == MetricType.SUCCESS_RATE:
                m.success_count += 1
                completion_time = dp.metadata.get("completion_time_ms", 0)
                m.total_completion_time_ms += completion_time
                m.latencies.append(completion_time)
                if dp.metadata.get("merged", False):
                    m.merge_count += 1
            elif dp.metric_type == MetricType.ERROR_RATE:
                m.failure_count += 1
            elif dp.metric_type == MetricType.COMPLETION_TIME_MS:
                m.latencies.append(dp.value)
        
        # Cache results (only if no time filter)
        if since is None:
            self._metrics_cache[cache_key] = metrics
        
        return metrics
    
    def get_all_experiments(self) -> List[str]:
        """Get list of all experiments with recorded metrics"""
        return list(self._data_points.keys())
    
    def clear_metrics(self, experiment_name: Optional[str] = None) -> None:
        """
        Clear metrics data
        
        Args:
            experiment_name: Optional experiment to clear (clears all if None)
        """
        if experiment_name:
            if experiment_name in self._data_points:
                del self._data_points[experiment_name]
            self._invalidate_cache(experiment_name)
        else:
            self._data_points.clear()
            self._metrics_cache.clear()
        
        logger.info(
            f"[MetricsCollector] Cleared metrics for "
            f"experiment={experiment_name or 'all'}"
        )


class ExperimentAnalyzer:
    """
    Analyzes experiment results and determines statistical significance.
    
    Features:
    - Two-proportion z-test for success rate comparison
    - Effect size calculation (Cohen's h)
    - Automatic conclusion based on significance threshold
    - Safety threshold monitoring
    
    Usage:
        analyzer = ExperimentAnalyzer(confidence_level=0.95)
        
        # Analyze experiment results
        result = analyzer.analyze(control_metrics, treatment_metrics)
        
        # Check if experiment should conclude
        conclusion = analyzer.should_conclude(
            experiment_name="gemini_planner_10pct_staging",
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics
        )
    """
    
    def __init__(
        self,
        confidence_level: float = 0.95,
        min_sample_size: int = 100,
        min_effect_size: float = 0.05,
        safety_threshold: float = 0.1,  # Max acceptable error rate increase
        max_duration_days: int = 30
    ):
        """
        Initialize ExperimentAnalyzer
        
        Args:
            confidence_level: Required confidence level for significance (default 95%)
            min_sample_size: Minimum sample size per variant before analysis
            min_effect_size: Minimum detectable effect size
            safety_threshold: Maximum acceptable error rate increase before rollback
            max_duration_days: Maximum experiment duration before auto-conclusion
        """
        self.confidence_level = confidence_level
        self.min_sample_size = min_sample_size
        self.min_effect_size = min_effect_size
        self.safety_threshold = safety_threshold
        self.max_duration_days = max_duration_days
        
        # Z-score for confidence level (two-tailed)
        self._z_score = self._get_z_score(confidence_level)
        
        logger.info(
            f"[ExperimentAnalyzer] Initialized with confidence_level={confidence_level}, "
            f"min_sample_size={min_sample_size}, safety_threshold={safety_threshold}"
        )
    
    def _get_z_score(self, confidence_level: float) -> float:
        """Get z-score for given confidence level"""
        # Common z-scores for two-tailed tests
        z_scores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }
        return z_scores.get(confidence_level, 1.96)
    
    def analyze(
        self,
        control_metrics: ExperimentMetrics,
        treatment_metrics: ExperimentMetrics,
        metric_type: MetricType = MetricType.SUCCESS_RATE
    ) -> StatisticalResult:
        """
        Analyze experiment results using two-proportion z-test
        
        Args:
            control_metrics: Metrics for control variant
            treatment_metrics: Metrics for treatment variant
            metric_type: Type of metric to analyze
        
        Returns:
            StatisticalResult with significance test results
        """
        # Get metric values based on type
        if metric_type == MetricType.SUCCESS_RATE:
            p_control = control_metrics.success_rate
            p_treatment = treatment_metrics.success_rate
        elif metric_type == MetricType.ERROR_RATE:
            p_control = control_metrics.error_rate
            p_treatment = treatment_metrics.error_rate
        elif metric_type == MetricType.MERGE_RATE:
            p_control = control_metrics.merge_rate
            p_treatment = treatment_metrics.merge_rate
        else:
            # Default to success rate
            p_control = control_metrics.success_rate
            p_treatment = treatment_metrics.success_rate
        
        n_control = control_metrics.total_requests
        n_treatment = treatment_metrics.total_requests
        
        # Calculate pooled proportion
        if n_control + n_treatment == 0:
            return StatisticalResult(
                is_significant=False,
                p_value=1.0,
                confidence_level=self.confidence_level,
                effect_size=0.0,
                relative_improvement=0.0,
                sample_size_control=n_control,
                sample_size_treatment=n_treatment,
                power=0.0
            )
        
        p_pooled = (
            (p_control * n_control + p_treatment * n_treatment) /
            (n_control + n_treatment)
        )
        
        # Calculate standard error
        if n_control == 0 or n_treatment == 0:
            se = 0.0
        else:
            se = math.sqrt(
                p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment)
            )
        
        # Calculate z-statistic
        if se == 0:
            z_stat = 0.0
        else:
            z_stat = (p_treatment - p_control) / se
        
        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - self._normal_cdf(abs(z_stat)))
        
        # Calculate effect size (Cohen's h)
        effect_size = self._cohens_h(p_control, p_treatment)
        
        # Calculate relative improvement
        if p_control == 0:
            relative_improvement = 0.0 if p_treatment == 0 else float('inf')
        else:
            relative_improvement = (p_treatment - p_control) / p_control * 100
        
        # Calculate statistical power
        power = self._calculate_power(
            p_control, p_treatment, n_control, n_treatment
        )
        
        # Determine significance
        is_significant = (
            p_value < (1 - self.confidence_level) and
            abs(effect_size) >= self.min_effect_size and
            n_control >= self.min_sample_size and
            n_treatment >= self.min_sample_size
        )
        
        return StatisticalResult(
            is_significant=is_significant,
            p_value=p_value,
            confidence_level=self.confidence_level,
            effect_size=effect_size,
            relative_improvement=relative_improvement,
            sample_size_control=n_control,
            sample_size_treatment=n_treatment,
            power=power
        )
    
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF using error function approximation"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _cohens_h(self, p1: float, p2: float) -> float:
        """Calculate Cohen's h effect size for proportions"""
        phi1 = 2 * math.asin(math.sqrt(max(0, min(1, p1))))
        phi2 = 2 * math.asin(math.sqrt(max(0, min(1, p2))))
        return phi2 - phi1
    
    def _calculate_power(
        self,
        p_control: float,
        p_treatment: float,
        n_control: int,
        n_treatment: int
    ) -> float:
        """Calculate statistical power of the test"""
        if n_control == 0 or n_treatment == 0:
            return 0.0
        
        # Effect size
        effect = abs(p_treatment - p_control)
        
        # Pooled standard error under alternative hypothesis
        se_alt = math.sqrt(
            p_control * (1 - p_control) / n_control +
            p_treatment * (1 - p_treatment) / n_treatment
        )
        
        if se_alt == 0:
            return 1.0 if effect > 0 else 0.0
        
        # Non-centrality parameter
        ncp = effect / se_alt
        
        # Power calculation (approximate)
        power = self._normal_cdf(ncp - self._z_score) + self._normal_cdf(-ncp - self._z_score)
        
        return max(0.0, min(1.0, power))
    
    def check_safety_threshold(
        self,
        control_metrics: ExperimentMetrics,
        treatment_metrics: ExperimentMetrics
    ) -> Tuple[bool, str]:
        """
        Check if treatment variant exceeds safety threshold
        
        Args:
            control_metrics: Metrics for control variant
            treatment_metrics: Metrics for treatment variant
        
        Returns:
            Tuple of (is_safe, reason)
        """
        error_rate_diff = treatment_metrics.error_rate - control_metrics.error_rate
        
        if error_rate_diff > self.safety_threshold:
            return (
                False,
                f"Treatment error rate ({treatment_metrics.error_rate:.2%}) exceeds "
                f"control ({control_metrics.error_rate:.2%}) by more than "
                f"safety threshold ({self.safety_threshold:.2%})"
            )
        
        return (True, "Within safety threshold")
    
    def should_conclude(
        self,
        experiment_name: str,
        control_metrics: ExperimentMetrics,
        treatment_metrics: ExperimentMetrics,
        experiment_start: Optional[datetime] = None
    ) -> Optional[ExperimentConclusion]:
        """
        Determine if experiment should be concluded
        
        Args:
            experiment_name: Name of the experiment
            control_metrics: Metrics for control variant
            treatment_metrics: Metrics for treatment variant
            experiment_start: Optional experiment start time
        
        Returns:
            ExperimentConclusion if experiment should conclude, None otherwise
        """
        # Check safety threshold first
        is_safe, safety_reason = self.check_safety_threshold(
            control_metrics, treatment_metrics
        )
        
        if not is_safe:
            return ExperimentConclusion(
                experiment_name=experiment_name,
                winner="control",
                reason=ConclusionReason.SAFETY_THRESHOLD,
                statistical_result=None,
                recommendation=f"Rollback treatment variant. {safety_reason}"
            )
        
        # Check if we have enough data
        if (control_metrics.total_requests < self.min_sample_size or
                treatment_metrics.total_requests < self.min_sample_size):
            
            # Check timeout
            if experiment_start:
                duration = datetime.utcnow() - experiment_start
                if duration.days >= self.max_duration_days:
                    return ExperimentConclusion(
                        experiment_name=experiment_name,
                        winner=None,
                        reason=ConclusionReason.INSUFFICIENT_DATA,
                        statistical_result=None,
                        recommendation=(
                            f"Experiment timed out after {duration.days} days with "
                            f"insufficient data. Consider increasing traffic allocation."
                        )
                    )
            
            return None  # Not enough data yet
        
        # Analyze statistical significance
        result = self.analyze(control_metrics, treatment_metrics)
        
        if result.is_significant:
            # Determine winner
            if result.relative_improvement > 0:
                winner = "treatment"
                recommendation = (
                    f"Treatment variant shows {result.relative_improvement:.1f}% improvement "
                    f"with {result.confidence_level:.0%} confidence. "
                    f"Recommend rolling out treatment to 100%."
                )
            else:
                winner = "control"
                recommendation = (
                    f"Control variant performs better by {abs(result.relative_improvement):.1f}%. "
                    f"Recommend keeping control variant."
                )
            
            return ExperimentConclusion(
                experiment_name=experiment_name,
                winner=winner,
                reason=ConclusionReason.STATISTICAL_SIGNIFICANCE,
                statistical_result=result,
                recommendation=recommendation
            )
        
        # Check timeout
        if experiment_start:
            duration = datetime.utcnow() - experiment_start
            if duration.days >= self.max_duration_days:
                return ExperimentConclusion(
                    experiment_name=experiment_name,
                    winner=None,
                    reason=ConclusionReason.TIMEOUT,
                    statistical_result=result,
                    recommendation=(
                        f"Experiment timed out after {duration.days} days without "
                        f"reaching statistical significance. Consider increasing "
                        f"traffic allocation or accepting current results."
                    )
                )
        
        return None  # Continue experiment
    
    def generate_report(
        self,
        experiment_name: str,
        control_metrics: ExperimentMetrics,
        treatment_metrics: ExperimentMetrics,
        experiment_start: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive experiment report
        
        Args:
            experiment_name: Name of the experiment
            control_metrics: Metrics for control variant
            treatment_metrics: Metrics for treatment variant
            experiment_start: Optional experiment start time
        
        Returns:
            Dict containing full experiment report
        """
        # Analyze results
        success_rate_result = self.analyze(
            control_metrics, treatment_metrics, MetricType.SUCCESS_RATE
        )
        
        # Check for conclusion
        conclusion = self.should_conclude(
            experiment_name, control_metrics, treatment_metrics, experiment_start
        )
        
        # Calculate duration
        duration_days = None
        if experiment_start:
            duration_days = (datetime.utcnow() - experiment_start).days
        
        return {
            "experiment_name": experiment_name,
            "generated_at": datetime.utcnow().isoformat(),
            "duration_days": duration_days,
            "metrics": {
                "control": control_metrics.to_dict(),
                "treatment": treatment_metrics.to_dict()
            },
            "analysis": {
                "success_rate": success_rate_result.to_dict()
            },
            "conclusion": conclusion.to_dict() if conclusion else None,
            "status": "concluded" if conclusion else "running",
            "summary": {
                "total_samples": (
                    control_metrics.total_requests + treatment_metrics.total_requests
                ),
                "control_success_rate": f"{control_metrics.success_rate:.2%}",
                "treatment_success_rate": f"{treatment_metrics.success_rate:.2%}",
                "relative_improvement": f"{success_rate_result.relative_improvement:.1f}%",
                "is_significant": success_rate_result.is_significant
            }
        }


# Global instances (lazy initialization)
_metrics_collector: Optional[MetricsCollector] = None
_experiment_analyzer: Optional[ExperimentAnalyzer] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global MetricsCollector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_experiment_analyzer(
    confidence_level: float = 0.95,
    min_sample_size: int = 100
) -> ExperimentAnalyzer:
    """Get or create the global ExperimentAnalyzer instance"""
    global _experiment_analyzer
    if _experiment_analyzer is None:
        _experiment_analyzer = ExperimentAnalyzer(
            confidence_level=confidence_level,
            min_sample_size=min_sample_size
        )
    return _experiment_analyzer


def reset_metrics_collector() -> None:
    """Reset the global metrics collector (useful for testing)"""
    global _metrics_collector
    _metrics_collector = None


def reset_experiment_analyzer() -> None:
    """Reset the global experiment analyzer (useful for testing)"""
    global _experiment_analyzer
    _experiment_analyzer = None
