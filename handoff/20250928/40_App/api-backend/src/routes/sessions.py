"""Sessions API - Agent Session Monitoring for Owner Console

This module provides API endpoints for listing and viewing agent execution sessions.
Sessions are stored in Redis by the orchestrator's SessionStore.

Issue: #1823
Phase: M5 - Meta Agent
PR: PR 2 - Sessions API Integration
"""
import logging
import os
import sys
import json
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request

from src.middleware.auth_middleware import jwt_required, admin_required

logger = logging.getLogger(__name__)

# Setup paths for orchestrator module import
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

orchestrator_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
if orchestrator_path not in sys.path:
    sys.path.insert(0, orchestrator_path)

# Try to import Redis client
try:
    from src.utils.redis_client import get_redis_client
    REDIS_AVAILABLE = True
except ImportError as e:
    logger.warning("Redis client not available: %s", e)
    REDIS_AVAILABLE = False

bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')

# Session key pattern used by orchestrator's SessionStore
SESSION_KEY_PREFIX = "dev_agent:session:"


def require_redis_available(fn):
    """Decorator to check if Redis is available before executing endpoint."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not REDIS_AVAILABLE:
            return jsonify({
                'error': 'Redis not available',
                'sessions_available': False,
            }), 503
        return fn(*args, **kwargs)
    return wrapper


def transform_session_for_frontend(session_data: dict) -> dict:
    """
    Transform orchestrator SessionState to frontend format.

    Maps the internal SessionState structure to the format expected by Sessions.jsx.
    """
    # Calculate progress based on actions vs max_iterations
    max_iterations = session_data.get('max_iterations', 10)
    iteration = session_data.get('iteration', 0)
    progress = min(100, int((iteration / max_iterations) * 100)) if max_iterations > 0 else 0

    # Map internal status to frontend status
    status_map = {
        'active': 'running',
        'paused': 'paused',
        'completed': 'completed',
        'failed': 'failed',
        'escalated': 'paused'  # Escalated sessions need human attention
    }
    status = status_map.get(session_data.get('status', 'active'), 'running')

    # Build tasks from decisions/actions
    tasks = []
    decisions = session_data.get('decisions', [])
    actions = session_data.get('actions', [])

    for i, decision in enumerate(decisions):
        action = actions[i] if i < len(actions) else None
        task_status = 'completed' if action and action.get('success') else 'pending'
        if action and not action.get('success'):
            task_status = 'failed'
        if i == len(actions) and status == 'running':
            task_status = 'running'

        tasks.append({
            'id': i + 1,
            'name': decision.get('decision', f'Task {i + 1}'),
            'status': task_status,
            'type': decision.get('action_type', 'ANALYZE_CODE').upper()
        })

    # Build logs from observations and actions
    logs = []
    for obs in session_data.get('observations', [])[-10:]:  # Last 10 observations
        logs.append({
            'timestamp': obs.get('timestamp'),
            'message': obs.get('observation', ''),
            'level': 'info'
        })

    for action in session_data.get('actions', [])[-10:]:  # Last 10 actions
        level = 'success' if action.get('success') else 'error'
        logs.append({
            'timestamp': action.get('timestamp'),
            'message': action.get('result', {}).get('message', f"Action: {action.get('action_type', 'unknown')}"),
            'level': level
        })

    # Sort logs by timestamp descending
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Check if session requires approval (escalated status)
    requires_approval = session_data.get('status') == 'escalated'

    # Calculate confidence based on success rate
    successful_actions = sum(1 for a in actions if a.get('success'))
    total_actions = len(actions)
    confidence = successful_actions / total_actions if total_actions > 0 else 0.5

    return {
        'id': session_data.get('session_id', ''),
        'title': session_data.get('goal', 'Untitled Session')[:50],
        'goal': session_data.get('goal', ''),
        'status': status,
        'user': session_data.get('user', 'system'),
        'agentType': 'LLM',  # Default agent type
        'confidence': round(confidence, 2),
        'startedAt': session_data.get('created_at'),
        'updatedAt': session_data.get('updated_at'),
        'progress': progress,
        'currentTask': tasks[-1]['name'] if tasks else None,
        'requiresApproval': requires_approval,
        'approvalReason': 'Task escalated for human review' if requires_approval else None,
        'plan': {
            'totalTasks': len(tasks),
            'completedTasks': sum(1 for t in tasks if t['status'] == 'completed'),
            'tasks': tasks
        },
        'logs': logs[:20],  # Limit to 20 most recent logs
        'prUrl': session_data.get('context', {}).get('pr_url'),
        'errorMessage': session_data.get('context', {}).get('error_message')
    }


@bp.route('', methods=['GET'])
@jwt_required
@admin_required
@require_redis_available
def list_sessions():
    """
    List all agent sessions.

    Query parameters:
    - status: Filter by status (running, paused, completed, failed)
    - limit: Maximum number of sessions (default: 50, max: 200)
    - page: Page number for pagination (default: 1)

    Returns list of sessions ordered by updated_at descending.

    Requires: Owner role
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        page = max(int(request.args.get('page', 1)), 1)
        status_filter = request.args.get('status')

        redis_client = get_redis_client()

        # Get all session keys
        pattern = f"{SESSION_KEY_PREFIX}*"
        session_keys = list(redis_client.scan_iter(match=pattern, count=1000))

        sessions = []
        for key in session_keys:
            try:
                data = redis_client.get(key)
                if data:
                    session_data = json.loads(data)
                    transformed = transform_session_for_frontend(session_data)

                    # Apply status filter
                    if status_filter and transformed['status'] != status_filter:
                        continue

                    sessions.append(transformed)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Failed to parse session %s: %s", key, e)
                continue

        # Sort by updatedAt descending
        sessions.sort(key=lambda x: x.get('updatedAt', ''), reverse=True)

        # Pagination
        total = len(sessions)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_sessions = sessions[start_idx:end_idx]

        return jsonify({
            'sessions': paginated_sessions,
            'total': total,
            'page': page,
            'perPage': limit,
            'filters': {
                'status': status_filter
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception:
        logger.exception("Failed to list sessions")
        return jsonify({'error': 'Failed to list sessions'}), 500


@bp.route('/<session_id>', methods=['GET'])
@jwt_required
@admin_required
@require_redis_available
def get_session_detail(session_id):
    """
    Get details of a specific session.

    Returns:
    - Full session details including plan, tasks, and logs

    Requires: Owner role
    """
    try:
        redis_client = get_redis_client()

        key = f"{SESSION_KEY_PREFIX}{session_id}"
        data = redis_client.get(key)

        if not data:
            return jsonify({'error': 'Session not found'}), 404

        session_data = json.loads(data)
        transformed = transform_session_for_frontend(session_data)

        return jsonify(transformed)
    except json.JSONDecodeError:
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except Exception:
        logger.exception("Failed to get session details")
        return jsonify({'error': 'Failed to get session details'}), 500


@bp.route('/<session_id>/pause', methods=['POST'])
@jwt_required
@admin_required
@require_redis_available
def pause_session(session_id):
    """
    Pause a running session.

    The agent will stop processing after completing the current action.

    Requires: Owner role
    """
    try:
        user_id = request.jwt_payload.get('sub', 'unknown')
        user_email = request.jwt_payload.get('email', user_id)

        redis_client = get_redis_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        data = redis_client.get(key)

        if not data:
            return jsonify({'error': 'Session not found'}), 404

        session_data = json.loads(data)
        current_status = session_data.get('status', 'active')

        if current_status != 'active':
            return jsonify({
                'error': 'Cannot pause session',
                'message': f'Session is {current_status}, only active sessions can be paused'
            }), 400

        session_data['status'] = 'paused'
        session_data['updated_at'] = datetime.utcnow().isoformat()
        session_data['paused_by'] = user_email

        redis_client.setex(key, 86400, json.dumps(session_data))

        logger.info("Session %s paused by %s", session_id, user_email)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'paused',
            'paused_by': user_email,
            'timestamp': datetime.utcnow().isoformat()
        })
    except json.JSONDecodeError:
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except Exception:
        logger.exception("Failed to pause session")
        return jsonify({'error': 'Failed to pause session'}), 500


@bp.route('/<session_id>/resume', methods=['POST'])
@jwt_required
@admin_required
@require_redis_available
def resume_session(session_id):
    """
    Resume a paused session.

    The agent will continue processing from where it left off.

    Requires: Owner role
    """
    try:
        user_id = request.jwt_payload.get('sub', 'unknown')
        user_email = request.jwt_payload.get('email', user_id)

        redis_client = get_redis_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        data = redis_client.get(key)

        if not data:
            return jsonify({'error': 'Session not found'}), 404

        session_data = json.loads(data)
        current_status = session_data.get('status', 'active')

        if current_status not in ['paused', 'escalated']:
            return jsonify({
                'error': 'Cannot resume session',
                'message': f'Session is {current_status}, only paused/escalated sessions can be resumed'
            }), 400

        session_data['status'] = 'active'
        session_data['updated_at'] = datetime.utcnow().isoformat()
        session_data['resumed_by'] = user_email

        redis_client.setex(key, 86400, json.dumps(session_data))

        logger.info("Session %s resumed by %s", session_id, user_email)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'active',
            'resumed_by': user_email,
            'timestamp': datetime.utcnow().isoformat()
        })
    except json.JSONDecodeError:
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except Exception:
        logger.exception("Failed to resume session")
        return jsonify({'error': 'Failed to resume session'}), 500


@bp.route('/<session_id>/cancel', methods=['POST'])
@jwt_required
@admin_required
@require_redis_available
def cancel_session(session_id):
    """
    Cancel a session.

    The session will be marked as failed and the agent will stop processing.

    Request body (optional):
    - reason: Cancellation reason

    Requires: Owner role
    """
    try:
        user_id = request.jwt_payload.get('sub', 'unknown')
        user_email = request.jwt_payload.get('email', user_id)

        req_data = request.get_json() or {}
        reason = req_data.get('reason')

        redis_client = get_redis_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        data = redis_client.get(key)

        if not data:
            return jsonify({'error': 'Session not found'}), 404

        session_data = json.loads(data)
        current_status = session_data.get('status', 'active')

        if current_status in ['completed', 'failed']:
            return jsonify({
                'error': 'Cannot cancel session',
                'message': f'Session is already {current_status}'
            }), 400

        session_data['status'] = 'failed'
        session_data['updated_at'] = datetime.utcnow().isoformat()
        session_data['cancelled_by'] = user_email
        if reason:
            session_data['context'] = session_data.get('context', {})
            session_data['context']['cancellation_reason'] = reason

        redis_client.setex(key, 86400, json.dumps(session_data))

        logger.info("Session %s cancelled by %s: %s", session_id, user_email, reason or "No reason")
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': 'failed',
            'cancelled_by': user_email,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
    except json.JSONDecodeError:
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except Exception:
        logger.exception("Failed to cancel session")
        return jsonify({'error': 'Failed to cancel session'}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for Sessions API"""
    return jsonify({
        'sessions_available': REDIS_AVAILABLE,
        'status': 'healthy' if REDIS_AVAILABLE else 'degraded',
        'timestamp': datetime.utcnow().isoformat()
    })
