"""Experiments API - A/B Testing experiment management (Phase 5 PR-6)"""
import os
import sys
from flask import Blueprint, jsonify, request
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

orchestrator_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
if orchestrator_path not in sys.path:
    sys.path.insert(0, orchestrator_path)

import logging  # noqa: E402

logger = logging.getLogger(__name__)

try:
    from experiment_manager import (
        get_experiment_manager,
        ExperimentManager
    )
    EXPERIMENT_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Experiment manager module not available: {e}")
    EXPERIMENT_MANAGER_AVAILABLE = False

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

    This endpoint provides mock data for experiment comparison charts.
    In production, this would aggregate real metrics from the metrics system.

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

        comparison_data = []
        for exp_name in manager.experiments:
            config = manager.experiments[exp_name]
            is_active = manager.is_experiment_active(exp_name)

            comparison_data.append({
                'experiment_name': exp_name,
                'target_component': config.target_component,
                'treatment_provider': config.treatment_provider,
                'control_provider': config.control_provider,
                'treatment_percent': config.treatment_percent,
                'active': is_active,
                'metrics': {
                    'control': {
                        'success_rate': 0.92,
                        'avg_latency_ms': 1250,
                        'total_requests': 0,
                        'error_rate': 0.08
                    },
                    'treatment': {
                        'success_rate': 0.89,
                        'avg_latency_ms': 980,
                        'total_requests': 0,
                        'error_rate': 0.11
                    }
                }
            })

        return jsonify({
            'comparisons': comparison_data,
            'environment': manager.environment,
            'active_experiments': active_experiments,
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Metrics are placeholder values. Real metrics will be populated from the metrics system.'
        })
    except Exception as e:
        logger.error(f"Failed to get experiment comparison: {e}")
        return jsonify({'error': str(e)}), 500
