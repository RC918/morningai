"""Action Requests API - Human-in-the-Loop (HITL) for High-Risk Operations

This module provides API endpoints for managing action requests
that require human approval before execution.

Issue: #1816
Phase: Phase 3 - Autonomous Expansion
"""
import logging
import os
import sys
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request

from src.middleware.auth_middleware import jwt_required, admin_required

logger = logging.getLogger(__name__)

# Setup paths for HITL module import
# From routes/ -> src -> api-backend -> 40_App -> 20250928 -> handoff -> repo_root (6 levels)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

orchestrator_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
if orchestrator_path not in sys.path:
    sys.path.insert(0, orchestrator_path)

try:
    from hitl import (  # noqa: E402
        approve_action_request,
        reject_action_request,
        get_pending_requests,
        get_request_status,
        process_timed_out_requests,
        get_action_request_statistics,
        RiskLevel,
    )
    HITL_AVAILABLE = True
except ImportError as e:
    logger.warning("HITL module not available: %s", e)
    HITL_AVAILABLE = False

bp = Blueprint('action_requests', __name__, url_prefix='/api/action-requests')


def require_hitl_available(fn):
    """Decorator to check if HITL system is available before executing endpoint."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not HITL_AVAILABLE:
            return jsonify({
                'error': 'HITL system not available',
                'hitl_available': False,
            }), 503
        return fn(*args, **kwargs)
    return wrapper


@bp.route('', methods=['GET'])
@require_hitl_available
@jwt_required
@admin_required
def list_pending_requests():
    """
    Get pending action requests requiring approval.

    Query parameters:
    - limit: Maximum number of requests (default: 50, max: 200)
    - risk_level: Filter by risk level (low, medium, high, critical)

    Returns list of pending action requests ordered by risk level and creation time.

    Requires: Owner role
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        risk_level_str = request.args.get('risk_level')

        risk_level = None
        if risk_level_str:
            try:
                risk_level = RiskLevel(risk_level_str)
            except ValueError:
                return jsonify({
                    'error': 'Invalid risk_level',
                    'valid_values': ['low', 'medium', 'high', 'critical']
                }), 400

        requests_list = get_pending_requests(limit=limit, risk_level_filter=risk_level)

        return jsonify({
            'requests': requests_list,
            'count': len(requests_list),
            'filters': {
                'limit': limit,
                'risk_level': risk_level_str
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error("Failed to list pending requests: %s", e)
        return jsonify({'error': 'Failed to list pending requests', 'message': str(e)}), 500


@bp.route('/<request_id>', methods=['GET'])
@require_hitl_available
@jwt_required
@admin_required
def get_request_details(request_id):
    """
    Get details of a specific action request.

    Returns:
    - Request details including status, risk level, and action information

    Requires: Owner role
    """
    try:
        request_data = get_request_status(request_id)

        if not request_data:
            return jsonify({'error': 'Request not found'}), 404

        return jsonify(request_data)
    except Exception as e:
        logger.error("Failed to get request details: %s", e)
        return jsonify({'error': 'Failed to get request details', 'message': str(e)}), 500


@bp.route('/<request_id>/approve', methods=['POST'])
@require_hitl_available
@jwt_required
@admin_required
def approve_request(request_id):
    """
    Approve a pending action request.

    The agent will be notified and can proceed with the action.

    Requires: Owner role
    """
    try:
        # Get user info from current_user set by admin_required decorator
        current_user = getattr(request, 'current_user', {}) or {}
        user_id = current_user.get('user_id', 'unknown')
        user_email = current_user.get('username', user_id)  # username contains email

        success = approve_action_request(request_id, approved_by=user_email)

        if success:
            logger.info("Request %s approved by %s", request_id, user_email)
            return jsonify({
                'success': True,
                'request_id': request_id,
                'status': 'approved',
                'approved_by': user_email,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'error': 'Failed to approve request',
                'message': 'Request not found or not in pending status'
            }), 400
    except Exception as e:
        logger.error("Failed to approve request %s: %s", request_id, e)
        return jsonify({'error': 'Failed to approve request', 'message': str(e)}), 500


@bp.route('/<request_id>/reject', methods=['POST'])
@require_hitl_available
@jwt_required
@admin_required
def reject_request(request_id):
    """
    Reject a pending action request.

    Request body (optional):
    - reason: Rejection reason

    The agent will be notified and the action will not be executed.

    Requires: Owner role
    """
    try:
        # Get user info from current_user set by admin_required decorator
        current_user = getattr(request, 'current_user', {}) or {}
        user_id = current_user.get('user_id', 'unknown')
        user_email = current_user.get('username', user_id)  # username contains email

        data = request.get_json() or {}
        reason = data.get('reason')

        success = reject_action_request(request_id, rejected_by=user_email, reason=reason)

        if success:
            logger.info("Request %s rejected by %s: %s", request_id, user_email, reason or "No reason")
            return jsonify({
                'success': True,
                'request_id': request_id,
                'status': 'rejected',
                'rejected_by': user_email,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'error': 'Failed to reject request',
                'message': 'Request not found or not in pending status'
            }), 400
    except Exception as e:
        logger.error("Failed to reject request %s: %s", request_id, e)
        return jsonify({'error': 'Failed to reject request', 'message': str(e)}), 500


@bp.route('/process-timeouts', methods=['POST'])
@require_hitl_available
@jwt_required
@admin_required
def process_timeouts():
    """
    Process and auto-reject timed out requests.

    This endpoint can be called manually or by a scheduled job.

    Returns:
    - count: Number of requests that were timed out

    Requires: Owner role
    """
    try:
        count = process_timed_out_requests()

        return jsonify({
            'success': True,
            'timed_out_count': count,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error("Failed to process timeouts: %s", e)
        return jsonify({'error': 'Failed to process timeouts', 'message': str(e)}), 500


@bp.route('/statistics', methods=['GET'])
@require_hitl_available
@jwt_required
@admin_required
def get_statistics():
    """
    Get statistics about action requests.

    Returns:
    - pending_count: Number of pending requests
    - by_risk_level: Breakdown by risk level

    Requires: Owner role
    """
    try:
        stats = get_action_request_statistics()

        return jsonify({
            'pending_count': stats.get('pending_count', 0),
            'by_risk_level': stats.get('by_risk_level', {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error("Failed to get statistics: %s", e)
        return jsonify({'error': 'Failed to get statistics', 'message': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for HITL system"""
    return jsonify({
        'hitl_available': HITL_AVAILABLE,
        'status': 'healthy' if HITL_AVAILABLE else 'degraded',
        'timestamp': datetime.utcnow().isoformat()
    })
