"""Experiments API - A/B Testing experiment management (Phase 5 PR-6)"""
import logging
from flask import Blueprint, jsonify, request
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from orchestrator.experiment_manager import (
        get_experiment_manager,
        ExperimentManager
    )
    EXPERIMENT_MANAGER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Experiment manager module not available: {e}")
    EXPERIMENT_MANAGER_AVAILABLE = False

try:
    from orchestrator.experiment_metrics import (
        get_metrics_collector,
        get_experiment_analyzer
    )
    EXPERIMENT_METRICS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Experiment metrics module not available: {e}")
    EXPERIMENT_METRICS_AVAILABLE = False

try:
    from orchestrator.persistence.planner_events_store import get_metrics_by_provider
    METRICS_STORE_AVAILABLE = True
except Exception as e:
    logger.warning(f"Planner events store not available: {e}")
    METRICS_STORE_AVAILABLE = False

from src.middleware.auth_middleware import jwt_required  # noqa: E402

bp = Blueprint('experiments', __name__, url_prefix='/api/experiments')


def _get_manager() -> "ExperimentManager":
    """Get experiment manager instance"""
    return get_experiment_manager()


@bp.route('', methods=['GET'])
@jwt_required
def list_experiments():
    """
    List all experiments with their configurations

    Returns list of experiment configurations and their status
    """
    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        manager = _get_manager()
        summary = manager.get_experiment_summary()

        return jsonify({
            'experiments': summary['experiments'],
            'environment': summary['environment'],
            'active_experiments': summary['active_experiments'],
            'total_experiments': summary['total_experiments'],
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/summary', methods=['GET'])
@jwt_required
def get_experiment_summary():
    """
    Get experiment summary with metrics

    Returns:
    - Active experiments count
    - Experiment configurations
    - Environment info
    """
    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        manager = _get_manager()
        summary = manager.get_experiment_summary()

        return jsonify({
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get experiment summary: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<experiment_name>', methods=['GET'])
@jwt_required
def get_experiment(experiment_name):
    """
    Get a single experiment configuration by name

    Returns detailed experiment information
    """
    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        manager = _get_manager()

        if experiment_name not in manager.experiments:
            return jsonify({'error': 'Experiment not found'}), 404

        config = manager.experiments[experiment_name]
        is_active = manager.is_experiment_active(experiment_name)

        return jsonify({
            'experiment': {
                'name': config.name,
                'description': config.description,
                'treatment_percent': config.treatment_percent,
                'enabled_environments': config.enabled_environments,
                'treatment_provider': config.treatment_provider,
                'control_provider': config.control_provider,
                'target_component': config.target_component,
                'enabled': config.enabled,
                'created_at': config.created_at,
                'active_in_current_env': is_active
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get experiment {experiment_name}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<experiment_name>/variant', methods=['GET'])
@jwt_required
def get_variant(experiment_name):
    """
    Get variant assignment for a trace_id

    Query parameters:
    - trace_id: Unique trace identifier (required)

    Returns variant assignment (control or treatment)
    """
    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        trace_id = request.args.get('trace_id')
        if not trace_id:
            return jsonify({'error': 'trace_id is required'}), 400

        manager = _get_manager()

        if experiment_name not in manager.experiments:
            return jsonify({'error': 'Experiment not found'}), 404

        variant = manager.get_variant(experiment_name, trace_id)
        provider = manager.get_provider_for_experiment(experiment_name, trace_id)

        return jsonify({
            'experiment_name': experiment_name,
            'trace_id': trace_id,
            'variant': variant,
            'provider': provider,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get variant for {experiment_name}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for experiment manager system"""
    try:
        status = {
            'experiment_manager_available': EXPERIMENT_MANAGER_AVAILABLE,
            'components': {}
        }

        if EXPERIMENT_MANAGER_AVAILABLE:
            try:
                manager = _get_manager()
                status['components']['experiment_manager'] = 'available'
                status['components']['environment'] = manager.environment
                status['components']['active_experiments'] = len(manager.list_active_experiments())
                status['components']['total_experiments'] = len(manager.experiments)
            except Exception as e:
                status['components']['experiment_manager'] = 'unavailable'
                status['components']['error'] = str(e)

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/comparison', methods=['GET'])
@jwt_required
def get_experiment_comparison():
    """
    Get experiment comparison data for dashboard visualization

    This endpoint aggregates real metrics from planner_events table,
    comparing control vs treatment provider performance.

    Query parameters:
    - days: Number of days to look back (default: 7)

    Returns:
    - Control vs treatment performance metrics
    - Success rates by variant
    - Latency comparison
    """
    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        manager = _get_manager()
        active_experiments = manager.list_active_experiments()

        # Get days parameter from query string (default: 7)
        days = request.args.get('days', 7, type=int)

        # Fetch real metrics from planner_events if available
        real_metrics = {}
        metrics_source = "placeholder"
        if METRICS_STORE_AVAILABLE:
            try:
                real_metrics = get_metrics_by_provider(days=days)
                if real_metrics:
                    metrics_source = "planner_events"
                    logger.info(
                        f"[Experiments API] Loaded real metrics for providers: "
                        f"{list(real_metrics.keys())}"
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch real metrics: {e}")

        # Default placeholder metrics (used when no real data available)
        default_metrics = {
            'success_rate': 0.0,
            'avg_latency_ms': 0,
            'total_requests': 0,
            'error_rate': 0.0
        }

        comparison_data = []
        for exp_name in manager.experiments:
            config = manager.experiments[exp_name]
            is_active = manager.is_experiment_active(exp_name)

            # Get control provider metrics
            control_provider = config.control_provider
            control_metrics = real_metrics.get(control_provider, default_metrics)

            # Get treatment provider metrics
            treatment_provider = config.treatment_provider
            treatment_metrics = real_metrics.get(treatment_provider, default_metrics)

            comparison_data.append({
                'experiment_name': exp_name,
                'target_component': config.target_component,
                'treatment_provider': treatment_provider,
                'control_provider': control_provider,
                'treatment_percent': config.treatment_percent,
                'active': is_active,
                'metrics': {
                    'control': control_metrics,
                    'treatment': treatment_metrics
                }
            })

        return jsonify({
            'comparisons': comparison_data,
            'environment': manager.environment,
            'active_experiments': active_experiments,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_source': metrics_source,
            'metrics_period_days': days,
            'note': (
                'Metrics aggregated from planner_events table.'
                if metrics_source == "planner_events"
                else 'No metrics data available yet. Metrics will populate as experiments run.'
            )
        })
    except Exception as e:
        logger.error(f"Failed to get experiment comparison: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<experiment_name>/metrics', methods=['GET'])
@jwt_required
def get_experiment_metrics(experiment_name):
    """
    Get collected metrics for an experiment

    Query parameters:
    - days: Number of days to look back (default: 7)

    Returns:
    - Control and treatment variant metrics
    - Success rate, error rate, latency percentiles
    - Sample sizes
    """
    if not EXPERIMENT_METRICS_AVAILABLE:
        return jsonify({'error': 'Experiment metrics module not available'}), 503

    try:
        collector = get_metrics_collector()
        metrics = collector.get_metrics(experiment_name)

        return jsonify({
            'experiment_name': experiment_name,
            'metrics': {
                'control': metrics['control'].to_dict() if 'control' in metrics else None,
                'treatment': metrics['treatment'].to_dict() if 'treatment' in metrics else None
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get metrics for {experiment_name}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<experiment_name>/metrics', methods=['POST'])
@jwt_required
def record_experiment_metric(experiment_name):
    """
    Record a metric data point for an experiment

    Request body:
    - variant: "control" or "treatment" (required)
    - success: boolean indicating success/failure (required)
    - completion_time_ms: time to complete in milliseconds (optional)
    - merged: boolean indicating if task resulted in merge (optional)
    - trace_id: unique trace identifier (optional)
    - error_type: error classification if failure (optional)
    - metadata: additional metadata dict (optional)

    Returns:
    - Confirmation of recorded metric
    """
    if not EXPERIMENT_METRICS_AVAILABLE:
        return jsonify({'error': 'Experiment metrics module not available'}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        variant = data.get('variant')
        if variant not in ['control', 'treatment']:
            return jsonify({'error': 'variant must be "control" or "treatment"'}), 400

        success = data.get('success')
        if success is None:
            return jsonify({'error': 'success field is required'}), 400

        collector = get_metrics_collector()

        if success:
            collector.record_success(
                experiment_name=experiment_name,
                variant=variant,
                completion_time_ms=data.get('completion_time_ms', 0),
                trace_id=data.get('trace_id'),
                merged=data.get('merged', False),
                metadata=data.get('metadata')
            )
        else:
            collector.record_failure(
                experiment_name=experiment_name,
                variant=variant,
                trace_id=data.get('trace_id'),
                error_type=data.get('error_type'),
                metadata=data.get('metadata')
            )

        return jsonify({
            'status': 'recorded',
            'experiment_name': experiment_name,
            'variant': variant,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Failed to record metric for {experiment_name}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<experiment_name>/analyze', methods=['GET'])
@jwt_required
def analyze_experiment(experiment_name):
    """
    Analyze experiment results and get statistical significance

    Returns:
    - Statistical analysis results
    - P-value, effect size, confidence level
    - Recommendation for experiment conclusion
    """
    if not EXPERIMENT_METRICS_AVAILABLE:
        return jsonify({'error': 'Experiment metrics module not available'}), 503

    try:
        collector = get_metrics_collector()
        analyzer = get_experiment_analyzer()

        metrics = collector.get_metrics(experiment_name)
        control_metrics = metrics.get('control')
        treatment_metrics = metrics.get('treatment')

        if not control_metrics or not treatment_metrics:
            return jsonify({
                'experiment_name': experiment_name,
                'error': 'Insufficient metrics data',
                'control_samples': control_metrics.total_requests if control_metrics else 0,
                'treatment_samples': treatment_metrics.total_requests if treatment_metrics else 0,
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        # Generate full report
        report = analyzer.generate_report(
            experiment_name=experiment_name,
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics
        )

        return jsonify({
            'experiment_name': experiment_name,
            'report': report,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to analyze experiment {experiment_name}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<experiment_name>/report', methods=['GET'])
@jwt_required
def get_experiment_report(experiment_name):
    """
    Get a comprehensive experiment report

    Returns:
    - Full experiment report with metrics, analysis, and conclusion
    - Suitable for dashboard visualization
    """
    if not EXPERIMENT_METRICS_AVAILABLE:
        return jsonify({'error': 'Experiment metrics module not available'}), 503

    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        manager = _get_manager()
        collector = get_metrics_collector()
        analyzer = get_experiment_analyzer()

        # Get experiment config
        if experiment_name not in manager.experiments:
            return jsonify({'error': 'Experiment not found'}), 404

        config = manager.experiments[experiment_name]
        is_active = manager.is_experiment_active(experiment_name)

        # Get metrics
        metrics = collector.get_metrics(experiment_name)
        control_metrics = metrics.get('control')
        treatment_metrics = metrics.get('treatment')

        # Generate report if we have metrics
        report = None
        if control_metrics and treatment_metrics:
            report = analyzer.generate_report(
                experiment_name=experiment_name,
                control_metrics=control_metrics,
                treatment_metrics=treatment_metrics
            )

        return jsonify({
            'experiment_name': experiment_name,
            'config': {
                'name': config.name,
                'description': config.description,
                'treatment_percent': config.treatment_percent,
                'enabled_environments': config.enabled_environments,
                'treatment_provider': config.treatment_provider,
                'control_provider': config.control_provider,
                'target_component': config.target_component,
                'enabled': config.enabled,
                'active_in_current_env': is_active
            },
            'report': report,
            'has_metrics': control_metrics is not None and treatment_metrics is not None,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get report for {experiment_name}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/dashboard', methods=['GET'])
@jwt_required
def get_experiments_dashboard():
    """
    Get dashboard data for all experiments

    Returns:
    - Summary of all experiments with their metrics and status
    - Suitable for A/B testing dashboard visualization
    """
    if not EXPERIMENT_MANAGER_AVAILABLE:
        return jsonify({'error': 'Experiment manager not available'}), 503

    try:
        manager = _get_manager()
        collector = get_metrics_collector() if EXPERIMENT_METRICS_AVAILABLE else None
        analyzer = get_experiment_analyzer() if EXPERIMENT_METRICS_AVAILABLE else None

        dashboard_data = []
        for exp_name, config in manager.experiments.items():
            is_active = manager.is_experiment_active(exp_name)

            exp_data = {
                'name': exp_name,
                'description': config.description,
                'treatment_percent': config.treatment_percent,
                'target_component': config.target_component,
                'treatment_provider': config.treatment_provider,
                'control_provider': config.control_provider,
                'enabled': config.enabled,
                'active': is_active,
                'metrics': None,
                'analysis': None
            }

            # Add metrics if available
            if collector:
                metrics = collector.get_metrics(exp_name)
                control = metrics.get('control')
                treatment = metrics.get('treatment')

                if control and treatment:
                    exp_data['metrics'] = {
                        'control': {
                            'success_rate': control.success_rate,
                            'error_rate': control.error_rate,
                            'total_requests': control.total_requests,
                            'avg_completion_time_ms': control.avg_completion_time_ms
                        },
                        'treatment': {
                            'success_rate': treatment.success_rate,
                            'error_rate': treatment.error_rate,
                            'total_requests': treatment.total_requests,
                            'avg_completion_time_ms': treatment.avg_completion_time_ms
                        }
                    }

                    # Add analysis if we have enough data
                    if analyzer and control.total_requests > 0 and treatment.total_requests > 0:
                        result = analyzer.analyze(control, treatment)
                        exp_data['analysis'] = {
                            'is_significant': result.is_significant,
                            'p_value': result.p_value,
                            'relative_improvement': result.relative_improvement,
                            'effect_size': result.effect_size
                        }

            dashboard_data.append(exp_data)

        return jsonify({
            'experiments': dashboard_data,
            'environment': manager.environment,
            'active_count': len(manager.list_active_experiments()),
            'total_count': len(manager.experiments),
            'metrics_available': EXPERIMENT_METRICS_AVAILABLE,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get experiments dashboard: {e}")
        return jsonify({'error': str(e)}), 500
