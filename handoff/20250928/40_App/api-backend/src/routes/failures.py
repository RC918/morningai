"""Failures API - Workflow failure recording and retrieval (Phase 5 PR-1)"""
import os
import sys
from flask import Blueprint, jsonify, request
from datetime import datetime

# Add BOTH 40_App and orchestrator directories to sys.path:
# - 40_App is needed for 'from orchestrator.persistence.db_client' imports
# - orchestrator is needed for 'from failure_recorder' imports (failure_recorder is inside orchestrator)
# Path: routes -> src -> api-backend -> 40_App (3 levels up)
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
orchestrator_dir = os.path.join(app_dir, 'orchestrator')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if orchestrator_dir not in sys.path:
    sys.path.insert(0, orchestrator_dir)

import logging  # noqa: E402

logger = logging.getLogger(__name__)

try:
    from failure_recorder import init_failure_recorder_from_env, FailureRecorder
    FAILURE_RECORDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Failure recorder module not available: {e}")
    FAILURE_RECORDER_AVAILABLE = False

try:
    from agent_eval_integration import init_agent_eval_from_env, AgentEvalIntegration
    AGENT_EVAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Agent eval integration module not available: {e}")
    AGENT_EVAL_AVAILABLE = False

from src.middleware.auth_middleware import jwt_required  # noqa: E402

bp = Blueprint('failures', __name__, url_prefix='/api/failures')


def _get_recorder() -> "FailureRecorder":
    """Get failure recorder instance with Redis connection"""
    return init_failure_recorder_from_env()


def _get_agent_eval() -> "AgentEvalIntegration":
    """Get agent eval integration instance with Redis connection"""
    return init_agent_eval_from_env()


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
            failure_dict = failure.to_dict()
            failure_dict.pop('metadata', None)
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

        return jsonify(failure.to_dict())
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


@bp.route('/<failure_id>/replay', methods=['POST'])
@jwt_required
def replay_failure(failure_id):
    """
    Replay a failed workflow by re-enqueuing it to the job queue

    This endpoint retrieves the original failure record and creates a new
    orchestrator task with the same goal but a new trace_id.

    Request body (optional):
    - repo: Override repository (uses original if not provided)

    Returns:
    - success: Whether the replay was successfully enqueued
    - failure_id: ID of the original failure record
    - new_trace_id: New trace ID for the replayed workflow
    - job_id: RQ job ID if successfully enqueued
    """
    if not FAILURE_RECORDER_AVAILABLE:
        return jsonify({'error': 'Failure recorder not available'}), 503

    try:
        recorder = _get_recorder()

        failure = recorder.get_failure(failure_id)
        if not failure:
            return jsonify({'error': 'Failure not found'}), 404

        data = request.get_json() or {}
        repo = data.get('repo')

        result = recorder.replay_failure(failure_id, repo=repo)

        response_data = result.to_dict()
        response_data['timestamp'] = datetime.utcnow().isoformat()

        if result.success:
            response_data['original_goal'] = failure.goal[:100]
            return jsonify(response_data)
        else:
            return jsonify(response_data), 500

    except Exception as e:
        logger.error(f"Failed to replay failure {failure_id}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for failure recorder system"""
    try:
        status = {
            'failure_recorder_available': FAILURE_RECORDER_AVAILABLE,
            'agent_eval_available': AGENT_EVAL_AVAILABLE,
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


@bp.route('/<failure_id>/generate-eval-task', methods=['POST'])
@jwt_required
def generate_eval_task(failure_id):
    """
    Generate an evaluation task from a failure record (Phase 5 PR-3)

    This endpoint creates an evaluation task that can be used by the
    agent_eval harness to test the agent's ability to handle similar tasks.

    Returns:
    - task_id: Generated evaluation task ID
    - failure_id: Original failure record ID
    - description: Task description
    - difficulty: Estimated difficulty level
    """
    if not FAILURE_RECORDER_AVAILABLE:
        return jsonify({'error': 'Failure recorder not available'}), 503

    if not AGENT_EVAL_AVAILABLE:
        return jsonify({'error': 'Agent eval integration not available'}), 503

    try:
        recorder = _get_recorder()
        failure = recorder.get_failure(failure_id)

        if not failure:
            return jsonify({'error': 'Failure not found'}), 404

        agent_eval = _get_agent_eval()
        task = agent_eval.generate_eval_task_from_failure(failure.to_dict())

        if not task:
            return jsonify({'error': 'Failed to generate eval task'}), 500

        return jsonify({
            'task': task.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to generate eval task from failure {failure_id}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/eval/tasks', methods=['GET'])
@jwt_required
def list_eval_tasks():
    """
    List generated evaluation tasks (Phase 5 PR-3)

    Query parameters:
    - limit: Number of tasks to return (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    - format: Output format ('json' or 'jsonl', default: 'json')

    Returns list of evaluation tasks
    """
    if not AGENT_EVAL_AVAILABLE:
        return jsonify({'error': 'Agent eval integration not available'}), 503

    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        output_format = request.args.get('format', 'json')

        agent_eval = _get_agent_eval()

        if output_format == 'jsonl':
            jsonl_data = agent_eval.export_eval_tasks_jsonl(limit=limit)
            return jsonl_data, 200, {'Content-Type': 'application/x-ndjson'}

        tasks = agent_eval.list_eval_tasks(limit=limit, offset=offset)
        tasks_data = [task.to_dict() for task in tasks]

        return jsonify({
            'tasks': tasks_data,
            'count': len(tasks_data),
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to list eval tasks: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/eval/metrics', methods=['GET'])
@jwt_required
def get_eval_metrics():
    """
    Get evaluation metrics summary (Phase 5 PR-3)

    Returns:
    - success_rate: Workflow success rate
    - fixer_metrics: Fixer iteration statistics
    - security_risk_distribution: Security risk level distribution
    - governance_risk_distribution: Governance risk level distribution
    """
    if not AGENT_EVAL_AVAILABLE:
        return jsonify({'error': 'Agent eval integration not available'}), 503

    try:
        agent_eval = _get_agent_eval()
        summary = agent_eval.get_metrics_summary()

        return jsonify({
            'metrics': summary,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get eval metrics: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/eval/metrics/<trace_id>', methods=['GET'])
@jwt_required
def get_workflow_eval_metrics(trace_id):
    """
    Get evaluation metrics for a specific workflow (Phase 5 PR-3)

    Returns detailed metrics for a single workflow execution
    """
    if not AGENT_EVAL_AVAILABLE:
        return jsonify({'error': 'Agent eval integration not available'}), 503

    try:
        agent_eval = _get_agent_eval()
        metrics = agent_eval.get_metrics(trace_id)

        if not metrics:
            return jsonify({'error': 'Metrics not found for trace_id'}), 404

        return jsonify({
            'metrics': metrics.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get eval metrics for {trace_id}: {e}")
        return jsonify({'error': str(e)}), 500
