"""Sessions API - Agent Session Monitoring for Owner Console

This module provides API endpoints for listing and viewing agent execution sessions.
Sessions are stored in Redis by the orchestrator's SessionStore.

Issue: #1823
Phase: M5 - Meta Agent
PR: PR 2 - Sessions API Integration
"""
import logging
import json
import uuid
from collections import Counter
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request

from src.middleware.auth_middleware import jwt_required, admin_required

logger = logging.getLogger(__name__)

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

# Session TTL in seconds (24 hours) - Issue #1992
SESSION_TTL_SECONDS = 86400

# Status mapping from internal to frontend format - shared across endpoints
STATUS_MAP = {
    'active': 'running',
    'paused': 'paused',
    'completed': 'completed',
    'failed': 'failed',
    'escalated': 'paused'  # Escalated sessions need human attention
}


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


def _get_session_and_user(session_id: str) -> tuple:
    """
    Get session data and user info from Redis and request context.

    DRY helper for control endpoints (pause/resume/cancel) - Issue #1990

    Args:
        session_id: The session ID to fetch

    Returns:
        tuple: (session_data: dict, user_info: dict, redis_key: str)

    Raises:
        ValueError: If session is not found (caller should return 404)
    """
    current_user = getattr(request, 'current_user', {})
    user_info = {
        'user_id': current_user.get('user_id', 'unknown'),
        'user_email': current_user.get('username', current_user.get('user_id', 'unknown'))
    }

    redis_client = get_redis_client()
    key = f"{SESSION_KEY_PREFIX}{session_id}"
    data = redis_client.get(key)

    if not data:
        raise ValueError(f"Session {session_id} not found")

    session_data = json.loads(data)
    return session_data, user_info, key


def transform_session_for_frontend(session_data: dict) -> dict:
    """
    Transform orchestrator SessionState to frontend format.

    Maps the internal SessionState structure to the format expected by Sessions.jsx.
    """
    # Calculate progress based on actions vs max_iterations
    max_iterations = session_data.get('max_iterations', 10)
    iteration = session_data.get('iteration', 0)
    progress = min(100, int((iteration / max_iterations) * 100)) if max_iterations > 0 else 0

    # Map internal status to frontend status using shared STATUS_MAP
    status = STATUS_MAP.get(session_data.get('status', 'active'), 'running')

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

    Performance optimization (#1980):
    - Uses MGET for batch fetching instead of individual GET calls
    - Returns counts for all statuses regardless of filter (#1981)

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

        if not session_keys:
            return jsonify({
                'sessions': [],
                'total': 0,
                'page': page,
                'perPage': limit,
                'counts': {
                    'all': 0,
                    'running': 0,
                    'paused': 0,
                    'completed': 0,
                    'failed': 0
                },
                'filters': {
                    'status': status_filter
                },
                'timestamp': datetime.utcnow().isoformat()
            })

        # Batch fetch all sessions using MGET for better performance
        session_data_list = redis_client.mget(session_keys)

        all_sessions = []
        for key, data in zip(session_keys, session_data_list):
            if data is None:
                continue
            try:
                session_data = json.loads(data)
                transformed = transform_session_for_frontend(session_data)
                all_sessions.append(transformed)
            except (json.JSONDecodeError, KeyError, TypeError, IndexError) as e:
                logger.warning("Failed to process session data for key %s: %s", key, e)
                continue

        # Calculate counts for all statuses (regardless of filter)
        # Use Counter for single-pass iteration (performance optimization)
        status_counts = Counter(s.get('status') for s in all_sessions)
        counts = {
            'all': len(all_sessions),
            'running': status_counts.get('running', 0),
            'paused': status_counts.get('paused', 0),
            'completed': status_counts.get('completed', 0),
            'failed': status_counts.get('failed', 0)
        }

        # Apply status filter
        if status_filter:
            sessions = [s for s in all_sessions if s['status'] == status_filter]
        else:
            sessions = all_sessions

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
            'counts': counts,
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
        # Use DRY helper for session and user retrieval - Issue #1990
        session_data, user_info, key = _get_session_and_user(session_id)
        user_email = user_info['user_email']

        current_status = session_data.get('status', 'active')

        if current_status != 'active':
            return jsonify({
                'error': 'Cannot pause session',
                'message': f'Session is {current_status}, only active sessions can be paused'
            }), 400

        session_data['status'] = 'paused'
        session_data['updated_at'] = datetime.utcnow().isoformat()
        session_data['paused_by'] = user_email

        redis_client = get_redis_client()
        redis_client.setex(key, SESSION_TTL_SECONDS, json.dumps(session_data))

        logger.info("Session %s paused by %s", session_id, user_email)
        # Use STATUS_MAP for frontend-consistent status - Issue #1989
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': STATUS_MAP.get('paused', 'paused'),
            'paused_by': user_email,
            'timestamp': datetime.utcnow().isoformat()
        })
    except json.JSONDecodeError:
        # Must be caught before ValueError since JSONDecodeError is a subclass of ValueError
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except ValueError:
        return jsonify({'error': 'Session not found'}), 404
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
        # Use DRY helper for session and user retrieval - Issue #1990
        session_data, user_info, key = _get_session_and_user(session_id)
        user_email = user_info['user_email']

        current_status = session_data.get('status', 'active')

        if current_status not in ['paused', 'escalated']:
            return jsonify({
                'error': 'Cannot resume session',
                'message': f'Session is {current_status}, only paused/escalated sessions can be resumed'
            }), 400

        session_data['status'] = 'active'
        session_data['updated_at'] = datetime.utcnow().isoformat()
        session_data['resumed_by'] = user_email

        redis_client = get_redis_client()
        redis_client.setex(key, SESSION_TTL_SECONDS, json.dumps(session_data))

        logger.info("Session %s resumed by %s", session_id, user_email)
        # Use STATUS_MAP for frontend-consistent status - Issue #1989
        # Note: 'active' maps to 'running' in frontend
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': STATUS_MAP.get('active', 'running'),
            'resumed_by': user_email,
            'timestamp': datetime.utcnow().isoformat()
        })
    except json.JSONDecodeError:
        # Must be caught before ValueError since JSONDecodeError is a subclass of ValueError
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except ValueError:
        return jsonify({'error': 'Session not found'}), 404
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
        # Use DRY helper for session and user retrieval - Issue #1990
        session_data, user_info, key = _get_session_and_user(session_id)
        user_email = user_info['user_email']

        req_data = request.get_json(silent=True) or {}
        reason = req_data.get('reason')

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

        redis_client = get_redis_client()
        redis_client.setex(key, SESSION_TTL_SECONDS, json.dumps(session_data))

        logger.info("Session %s cancelled by %s: %s", session_id, user_email, reason or "No reason")
        # Use STATUS_MAP for frontend-consistent status - Issue #1989
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': STATUS_MAP.get('failed', 'failed'),
            'cancelled_by': user_email,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
    except json.JSONDecodeError:
        # Must be caught before ValueError since JSONDecodeError is a subclass of ValueError
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except ValueError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception:
        logger.exception("Failed to cancel session")
        return jsonify({'error': 'Failed to cancel session'}), 500


# Valid quick command IDs - must match frontend SessionCommandInput.jsx QUICK_COMMANDS
# Issue #2179 - API endpoint for SessionCommandInput
VALID_QUICK_COMMAND_IDS = {'continue', 'explain', 'skip', 'retry'}


@bp.route('/<session_id>/command', methods=['POST'])
@jwt_required
@admin_required
@require_redis_available
def send_command(session_id):
    """
    Send a command to a running session.

    The command will be queued for the agent to process.

    Request body:
    - command: The command text or quick command ID (required)
    - type: Command type - 'user_command' or 'quick_command' (default: 'user_command')
    - timestamp: Client timestamp (optional)

    Quick Command IDs (when type='quick_command'):
    - continue: Continue execution
    - explain: Explain current step
    - skip: Skip this task
    - retry: Retry last action

    Requires: Owner role

    Issue: #2179 - API endpoint for SessionCommandInput
    """
    VALID_COMMAND_TYPES = {'user_command', 'quick_command'}

    try:
        session_data, user_info, key = _get_session_and_user(session_id)
        user_email = user_info['user_email']
        user_id = user_info['user_id']

        req_data = request.get_json(silent=True) or {}
        command = req_data.get('command', '')
        command_type = req_data.get('type', 'user_command')
        client_timestamp = req_data.get('timestamp')

        if not command or not command.strip():
            return jsonify({
                'error': 'Missing required field',
                'message': 'command is required and cannot be empty or whitespace only'
            }), 400

        command = command.strip()

        if command_type not in VALID_COMMAND_TYPES:
            return jsonify({
                'error': 'Invalid command type',
                'message': f'type must be one of: {", ".join(sorted(VALID_COMMAND_TYPES))}'
            }), 400

        # Validate quick command IDs - Issue #2179
        if command_type == 'quick_command' and command not in VALID_QUICK_COMMAND_IDS:
            return jsonify({
                'error': 'Invalid quick command',
                'message': f'quick command must be one of: {", ".join(sorted(VALID_QUICK_COMMAND_IDS))}'
            }), 400

        current_status = session_data.get('status', 'active')

        if current_status in ['completed', 'failed', 'cancelled']:
            return jsonify({
                'error': 'Cannot send command',
                'message': f'Session is {current_status}, commands can only be sent to active/paused sessions'
            }), 400

        command_id = str(uuid.uuid4())
        server_timestamp = datetime.utcnow().isoformat()

        command_entry = {
            'command_id': command_id,
            'command': command,
            'type': command_type,
            'sent_by': user_email,
            'user_id': user_id,
            'client_timestamp': client_timestamp,
            'server_timestamp': server_timestamp
        }

        session_data.setdefault('commands', []).append(command_entry)
        session_data['updated_at'] = server_timestamp

        redis_client = get_redis_client()
        redis_client.setex(key, SESSION_TTL_SECONDS, json.dumps(session_data))

        logger.info(
            "Command sent to session %s by %s: type=%s, length=%d",
            session_id, user_email, command_type, len(command)
        )

        return jsonify({
            'success': True,
            'command_id': command_id,
            'session_id': session_id,
            'status': 'accepted',
            'sent_by': user_email,
            'timestamp': server_timestamp
        })
    except json.JSONDecodeError:
        logger.exception("Failed to parse session %s", session_id)
        return jsonify({'error': 'Failed to parse session data'}), 500
    except ValueError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception:
        logger.exception("Failed to send command to session")
        return jsonify({'error': 'Failed to send command'}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for Sessions API"""
    return jsonify({
        'sessions_available': REDIS_AVAILABLE,
        'status': 'healthy' if REDIS_AVAILABLE else 'degraded',
        'timestamp': datetime.utcnow().isoformat()
    })
