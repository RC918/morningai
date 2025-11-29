"""Failures API - Workflow failure recording and retrieval (Phase 5 PR-1)"""
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

try:
    from failure_recorder import get_failure_recorder, FailureRecorder
    FAILURE_RECORDER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Failure recorder module not available: {e}")
    FAILURE_RECORDER_AVAILABLE = False

from src.middleware.auth_middleware import jwt_required  # noqa: E402
import logging  # noqa: E402

logger = logging.getLogger(__name__)

bp = Blueprint('failures', __name__, url_prefix='/api/failures')


def _get_recorder() -> "FailureRecorder":
    """Get failure recorder instance with Redis connection"""
    try:
        import redis
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            redis_client = redis.from_url(redis_url)
            return get_failure_recorder(redis_client=redis_client, enabled=True)
        return get_failure_recorder(redis_client=None, enabled=False)
    except Exception as e:
        logger.warning(f"Failed to initialize failure recorder: {e}")
        return get_failure_recorder(redis_client=None, enabled=False)


@bp.route('', methods=['GET'])
@jwt_required
def list_failures():
    """
    List workflow failures with pagination and filtering

    Query parameters:
    - limit: Number of failures to return (default: 50, max: 200)
    - offset: Pagination offset (default: 0)
    - trace_id: Filter by trace_id
    - error_type: Filter by error_type
    - task_type: Filter by task_type

    Returns list of failure records
    """
    if not FAILURE_RECORDER_AVAILABLE:
        return jsonify({'error': 'Failure recorder not available'}), 503

    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
        trace_id = request.args.get('trace_id')
        error_type = request.args.get('error_type')
        task_type = request.args.get('task_type')

        recorder = _get_recorder()
        failures = recorder.list_failures(
            limit=limit,
            offset=offset,
            trace_id=trace_id,
            error_type=error_type,
            task_type=task_type
        )

        failures_data = []
        for failure in failures:
            failure_dict = {
                'id': failure.id,
                'trace_id': failure.trace_id,
                'goal': failure.goal,
                'error_type': failure.error_type,
                'error_message': failure.error_message,
                'task_type': failure.task_type,
                'fixer_retries': failure.fixer_retries,
                'merge_decision': failure.merge_decision,
                'pr_url': failure.pr_url,
                'status': failure.status,
                'created_at': failure.created_at,
                'env': failure.env,
                'pipeline': failure.pipeline
            }
            failures_data.append(failure_dict)

        return jsonify({
            'failures': failures_data,
            'count': len(failures_data),
            'limit': limit,
            'offset': offset,
            'filters': {
                'trace_id': trace_id,
                'error_type': error_type,
                'task_type': task_type
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to list failures: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<failure_id>', methods=['GET'])
@jwt_required
def get_failure(failure_id):
    """
    Get a single failure record by ID

    Returns detailed failure information
    """
    if not FAILURE_RECORDER_AVAILABLE:
        return jsonify({'error': 'Failure recorder not available'}), 503

    try:
        recorder = _get_recorder()
        failure = recorder.get_failure(failure_id)

        if not failure:
            return jsonify({'error': 'Failure not found'}), 404

        failure_dict = {
            'id': failure.id,
            'trace_id': failure.trace_id,
            'goal': failure.goal,
            'error_type': failure.error_type,
            'error_message': failure.error_message,
            'task_type': failure.task_type,
            'fixer_retries': failure.fixer_retries,
            'merge_decision': failure.merge_decision,
            'pr_url': failure.pr_url,
            'status': failure.status,
            'created_at': failure.created_at,
            'env': failure.env,
            'pipeline': failure.pipeline,
            'metadata': failure.metadata
        }

        return jsonify(failure_dict)
    except Exception as e:
        logger.error(f"Failed to get failure {failure_id}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/summary', methods=['GET'])
@jwt_required
def get_failure_summary():
    """
    Get failure statistics summary

    Returns:
    - Total failure count
    - Failures by error_type
    - Failures by task_type
    - Recent failure rate
    """
    if not FAILURE_RECORDER_AVAILABLE:
        return jsonify({'error': 'Failure recorder not available'}), 503

    try:
        recorder = _get_recorder()
        summary = recorder.get_failure_summary()

        return jsonify({
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get failure summary: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for failure recorder system"""
    try:
        status = {
            'failure_recorder_available': FAILURE_RECORDER_AVAILABLE,
            'components': {}
        }

        if FAILURE_RECORDER_AVAILABLE:
            try:
                recorder = _get_recorder()
                status['components']['redis'] = 'available' if recorder.enabled else 'degraded'
                status['components']['failure_count'] = recorder.get_failure_count()
            except Exception as e:
                status['components']['redis'] = 'unavailable'
                status['components']['error'] = str(e)

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
