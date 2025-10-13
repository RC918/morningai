import os
import sys
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, g
from src.middleware.auth_middleware import jwt_required, roles_required

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
from hitl_approval_system import HITLApprovalSystem, ApprovalChannel, ApprovalStatus

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

bp = Blueprint("hitl", __name__, url_prefix="/api/hitl")

telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
hitl_system = HITLApprovalSystem(telegram_token, admin_chat_id)

def get_current_user():
    """Get current user from request context"""
    return getattr(request, 'current_user', {})

@bp.route("/requests", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_pending_requests():
    """Get all pending approval requests"""
    try:
        priority_filter = request.args.get("priority")
        requests = hitl_system.get_pending_requests(priority_filter=priority_filter)
        
        requests_data = []
        for req in requests:
            requests_data.append({
                "request_id": req.request_id,
                "trace_id": req.trace_id,
                "title": req.title,
                "description": req.description,
                "context": req.context,
                "requester_agent": req.requester_agent,
                "priority": req.priority,
                "created_at": req.created_at.isoformat(),
                "expires_at": req.expires_at.isoformat(),
                "status": req.status.value
            })
        
        return jsonify({
            "requests": requests_data,
            "total_count": len(requests_data),
            "filtered_by_priority": priority_filter
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get pending requests: {e}")
        return jsonify({
            "error": {
                "code": "retrieval_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/requests/<request_id>", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_request_details(request_id):
    """Get details for a specific approval request"""
    try:
        pending = hitl_system.get_pending_requests()
        
        for req in pending:
            if req.request_id == request_id:
                return jsonify({
                    "request_id": req.request_id,
                    "trace_id": req.trace_id,
                    "title": req.title,
                    "description": req.description,
                    "context": req.context,
                    "prompt_details": req.prompt_details,
                    "requester_agent": req.requester_agent,
                    "priority": req.priority,
                    "created_at": req.created_at.isoformat(),
                    "expires_at": req.expires_at.isoformat(),
                    "status": req.status.value
                }), 200
        
        return jsonify({
            "error": {
                "code": "request_not_found",
                "message": f"Request {request_id} not found"
            }
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to get request {request_id}: {e}")
        return jsonify({
            "error": {
                "code": "retrieval_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/approve/<request_id>", methods=["POST"])
@jwt_required
@roles_required("analyst", "admin")
def approve_request(request_id):
    """Approve an approval request"""
    try:
        user = get_current_user()
        payload = request.get_json(silent=True) or {}
        comments = payload.get("comments")
        
        import asyncio
        success = asyncio.run(hitl_system.process_approval(
            request_id=request_id,
            approved=True,
            approver=user.get("username", "unknown"),
            channel=ApprovalChannel.CONSOLE,
            comments=comments
        ))
        
        if not success:
            return jsonify({
                "error": {
                    "code": "approval_failed",
                    "message": "Request not found or already processed/expired"
                }
            }), 404
        
        logger.info(f"Request {request_id} approved by {user.get('username')}")
        
        return jsonify({
            "request_id": request_id,
            "status": "approved",
            "approved_by": user.get("username"),
            "approved_at": datetime.now().isoformat(),
            "comments": comments
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to approve request {request_id}: {e}")
        return jsonify({
            "error": {
                "code": "approval_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/reject/<request_id>", methods=["POST"])
@jwt_required
@roles_required("analyst", "admin")
def reject_request(request_id):
    """Reject an approval request"""
    try:
        user = get_current_user()
        payload = request.get_json(silent=True) or {}
        comments = payload.get("comments", "")
        
        if not comments:
            return jsonify({
                "error": {
                    "code": "invalid_input",
                    "message": "Rejection reason (comments) is required"
                }
            }), 400
        
        import asyncio
        success = asyncio.run(hitl_system.process_approval(
            request_id=request_id,
            approved=False,
            approver=user.get("username", "unknown"),
            channel=ApprovalChannel.CONSOLE,
            comments=comments
        ))
        
        if not success:
            return jsonify({
                "error": {
                    "code": "rejection_failed",
                    "message": "Request not found or already processed/expired"
                }
            }), 404
        
        logger.info(f"Request {request_id} rejected by {user.get('username')}")
        
        return jsonify({
            "request_id": request_id,
            "status": "rejected",
            "rejected_by": user.get("username"),
            "rejected_at": datetime.now().isoformat(),
            "comments": comments
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reject request {request_id}: {e}")
        return jsonify({
            "error": {
                "code": "rejection_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/history", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_approval_history():
    """Get approval history"""
    try:
        limit = int(request.args.get("limit", 100))
        status_filter = request.args.get("status")
        
        history = hitl_system.get_approval_history(limit=limit, status_filter=status_filter)
        
        history_data = []
        for req in history:
            history_data.append({
                "request_id": req.request_id,
                "trace_id": req.trace_id,
                "title": req.title,
                "requester_agent": req.requester_agent,
                "priority": req.priority,
                "status": req.status.value,
                "created_at": req.created_at.isoformat(),
                "approved_by": req.approved_by,
                "approved_at": req.approved_at.isoformat() if req.approved_at else None,
                "approval_channel": req.approval_channel.value if req.approval_channel else None,
                "comments": req.comments
            })
        
        return jsonify({
            "history": history_data,
            "total_count": len(history_data),
            "limit": limit,
            "filtered_by_status": status_filter
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get approval history: {e}")
        return jsonify({
            "error": {
                "code": "retrieval_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/status", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_hitl_status():
    """Get HITL system status"""
    try:
        status = hitl_system.get_system_status()
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Failed to get HITL status: {e}")
        return jsonify({
            "error": {
                "code": "status_retrieval_failed",
                "message": str(e)
            }
        }), 500
