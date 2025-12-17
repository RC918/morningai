"""
LangGraph Rollout Dashboard API Endpoints (Issue #2283)

Provides API endpoints for monitoring and controlling the LangGraph rollout:
- GET /api/rollout/dashboard - Full dashboard summary
- GET /api/rollout/health - Health status
- POST /api/rollout/circuit-breaker/reset - Manual circuit breaker reset

Part of Phase 4A: Pre-rollout telemetry and controls (Epic #2311)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, jsonify, request
from middleware.auth_middleware import admin_required
from common.config.settings import get_settings

DEFAULT_WINDOW_MINUTES = 15
MIN_WINDOW_MINUTES = 1
MAX_WINDOW_MINUTES = 240

logger = logging.getLogger(__name__)

rollout_bp = Blueprint('rollout', __name__)


def _get_redis_client():
    """Get Redis client for rollout tracker"""
    try:
        from src.utils.redis_client import get_redis_client
        return get_redis_client()
    except Exception as e:
        logger.warning(f"Failed to get Redis client: {e}")
        return None


def _get_rollout_tracker():
    """Get RolloutTracker instance"""
    try:
        from rollout_tracker import create_rollout_tracker
        redis_client = _get_redis_client()
        return create_rollout_tracker(redis_client=redis_client, enabled=True)
    except ImportError:
        logger.warning("RolloutTracker not available - ensure PYTHONPATH includes orchestrator")
        return None
    except Exception as e:
        logger.warning(f"Failed to get RolloutTracker: {e}")
        return None


def _get_utc_iso_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_window_minutes(window_param: Optional[str]) -> int:
    """Parse and validate window parameter with range clamping"""
    if window_param is None:
        return DEFAULT_WINDOW_MINUTES

    try:
        window = int(window_param)
        if window < MIN_WINDOW_MINUTES or window > MAX_WINDOW_MINUTES:
            logger.warning(
                f"Window parameter {window} out of range [{MIN_WINDOW_MINUTES}, "
                f"{MAX_WINDOW_MINUTES}], using default {DEFAULT_WINDOW_MINUTES}"
            )
            return DEFAULT_WINDOW_MINUTES
        return window
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid window parameter '{window_param}', using default {DEFAULT_WINDOW_MINUTES}"
        )
        return DEFAULT_WINDOW_MINUTES


def _get_current_rollout_percent() -> int:
    """Get current LangGraph rollout percentage from settings"""
    try:
        return get_settings().use_langgraph_percent
    except Exception as e:
        logger.warning(f"Failed to get rollout percent from settings: {e}")
        return 0


@rollout_bp.route('/rollout/dashboard', methods=['GET'])
def get_rollout_dashboard():
    """
    Get full LangGraph rollout dashboard summary.

    Query Parameters:
        window: Time window in minutes (default: 15, range: 1-240)

    Returns:
        JSON with complete rollout dashboard data including:
        - timestamp: Current UTC timestamp
        - rollout_info: Current stage and percentage
        - health: Overall health assessment
        - comparison: LangGraph vs Simple Mode metrics
        - circuit_breaker: Circuit breaker state

    Example Response:
        {
            "timestamp": "2025-12-17T07:30:00Z",
            "window_minutes": 15,
            "rollout_info": {
                "current_stage": "STAGE_1",
                "current_percent": 5,
                "can_advance": false,
                "should_rollback": false
            },
            "health": {
                "healthy": true,
                "slo_compliant": true,
                "issues": [],
                "recommendations": []
            },
            "comparison": {
                "langgraph": {...},
                "simple": {...},
                "langgraph_advantage": {...}
            },
            "circuit_breaker": {
                "state": "closed",
                "failure_count": 0,
                "last_state_change": "2025-12-17T07:00:00Z"
            }
        }
    """
    window_minutes = _parse_window_minutes(request.args.get('window'))

    tracker = _get_rollout_tracker()
    if tracker is None:
        return jsonify({
            "error": "RolloutTracker unavailable",
            "timestamp": _get_utc_iso_timestamp(),
            "available": False
        }), 503

    try:
        current_percent = _get_current_rollout_percent()
        dashboard = tracker.get_dashboard_summary(current_percent, window_minutes)

        return jsonify({
            "timestamp": _get_utc_iso_timestamp(),
            "window_minutes": window_minutes,
            "available": True,
            **dashboard
        })
    except Exception as e:
        logger.error(f"Failed to get rollout dashboard: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": _get_utc_iso_timestamp(),
            "available": False
        }), 500


@rollout_bp.route('/rollout/health', methods=['GET'])
def get_rollout_health():
    """
    Get LangGraph rollout health status.

    Query Parameters:
        window: Time window in minutes (default: 15, range: 1-240)

    Returns:
        JSON with health assessment including:
        - status: "healthy", "degraded", or "unhealthy"
        - healthy: Boolean health indicator
        - slo_compliant: Whether SLOs are being met
        - circuit_state: Current circuit breaker state
        - can_advance: Whether rollout can advance to next stage
        - should_rollback: Whether rollback is recommended
        - issues: List of current issues
        - recommendations: List of recommendations

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2025-12-17T07:30:00Z",
            "healthy": true,
            "slo_compliant": true,
            "circuit_state": "closed",
            "can_advance": false,
            "should_rollback": false,
            "issues": [],
            "recommendations": ["Continue monitoring for 7 days before advancing"]
        }
    """
    window_minutes = _parse_window_minutes(request.args.get('window'))

    tracker = _get_rollout_tracker()
    if tracker is None:
        return jsonify({
            "status": "unavailable",
            "timestamp": _get_utc_iso_timestamp(),
            "error": "RolloutTracker unavailable"
        }), 503

    try:
        current_percent = _get_current_rollout_percent()
        health = tracker.get_rollout_health(current_percent, window_minutes)
        health_dict = health.to_dict()

        status = "healthy"
        if not health.healthy:
            status = "unhealthy"
        elif not health.slo_compliant or health.circuit_state.value != "closed":
            status = "degraded"

        return jsonify({
            "status": status,
            "timestamp": _get_utc_iso_timestamp(),
            "window_minutes": window_minutes,
            **health_dict
        })
    except Exception as e:
        logger.error(f"Failed to get rollout health: {e}")
        return jsonify({
            "status": "error",
            "timestamp": _get_utc_iso_timestamp(),
            "error": str(e)
        }), 500


@rollout_bp.route('/rollout/circuit-breaker/reset', methods=['POST'])
@admin_required
def reset_circuit_breaker():
    """
    Manually reset the circuit breaker to closed state.

    This endpoint allows operators to manually reset the circuit breaker
    after investigating and resolving the underlying issue that caused
    it to trip.

    Request Body (optional):
        {
            "reason": "Description of why the reset is being performed"
        }

    Returns:
        JSON with reset confirmation:
        - success: Boolean indicating if reset was successful
        - timestamp: When the reset occurred
        - previous_state: State before reset
        - new_state: State after reset (should be "closed")

    Example Response:
        {
            "success": true,
            "timestamp": "2025-12-17T07:30:00Z",
            "previous_state": "open",
            "new_state": "closed",
            "message": "Circuit breaker manually reset"
        }
    """
    tracker = _get_rollout_tracker()
    if tracker is None:
        return jsonify({
            "success": False,
            "timestamp": _get_utc_iso_timestamp(),
            "error": "RolloutTracker unavailable"
        }), 503

    try:
        previous_state = tracker.get_circuit_breaker_state()
        previous_state_value = previous_state.state.value

        reason = "Manual reset via API"
        if request.is_json and request.json:
            reason = request.json.get("reason", reason)
            # Limit reason length to prevent log pollution
            if len(reason) > 500:
                reason = reason[:500] + "..."

        tracker.reset_circuit_breaker()

        new_state = tracker.get_circuit_breaker_state()
        new_state_value = new_state.state.value

        logger.info(
            f"Circuit breaker manually reset: {previous_state_value} -> {new_state_value}",
            extra={"reason": reason}
        )

        return jsonify({
            "success": True,
            "timestamp": _get_utc_iso_timestamp(),
            "previous_state": previous_state_value,
            "new_state": new_state_value,
            "message": "Circuit breaker manually reset",
            "reason": reason
        })
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {e}")
        return jsonify({
            "success": False,
            "timestamp": _get_utc_iso_timestamp(),
            "error": str(e)
        }), 500


@rollout_bp.route('/rollout/comparison', methods=['GET'])
def get_rollout_comparison():
    """
    Get comparison between LangGraph and Simple Mode metrics.

    Query Parameters:
        window: Time window in minutes (default: 15, range: 1-240)

    Returns:
        JSON with side-by-side comparison of LangGraph vs Simple Mode:
        - langgraph: Metrics for LangGraph mode
        - simple: Metrics for Simple mode
        - langgraph_advantage: Calculated advantages

    Example Response:
        {
            "timestamp": "2025-12-17T07:30:00Z",
            "window_minutes": 15,
            "langgraph": {
                "total_tasks": 100,
                "success_rate": 98.5,
                "p95_latency_ms": 2500
            },
            "simple": {
                "total_tasks": 200,
                "success_rate": 97.0,
                "p95_latency_ms": 3000
            },
            "langgraph_advantage": {
                "success_rate_diff": 1.5,
                "p95_latency_diff_ms": 500
            }
        }
    """
    window_minutes = _parse_window_minutes(request.args.get('window'))

    tracker = _get_rollout_tracker()
    if tracker is None:
        return jsonify({
            "error": "RolloutTracker unavailable",
            "timestamp": _get_utc_iso_timestamp(),
            "available": False
        }), 503

    try:
        comparison = tracker.get_comparison(window_minutes)

        return jsonify({
            "timestamp": _get_utc_iso_timestamp(),
            "window_minutes": window_minutes,
            "available": True,
            **comparison.to_dict()
        })
    except Exception as e:
        logger.error(f"Failed to get rollout comparison: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": _get_utc_iso_timestamp(),
            "available": False
        }), 500


@rollout_bp.route('/rollout/slo', methods=['GET'])
def get_slo_compliance():
    """
    Get SLO compliance status for LangGraph rollout.

    Query Parameters:
        window: Time window in minutes (default: 15, range: 1-240)

    Returns:
        JSON with SLO compliance details:
        - compliant: Overall SLO compliance status
        - thresholds: Current SLO thresholds
        - current_values: Current metric values
        - violations: List of any SLO violations

    Example Response:
        {
            "timestamp": "2025-12-17T07:30:00Z",
            "window_minutes": 15,
            "compliant": true,
            "thresholds": {
                "p95_latency_ms": 5000,
                "failure_rate_percent": 5.0,
                "error_5xx_rate_percent": 1.0
            },
            "current_values": {
                "p95_latency_ms": 2500,
                "failure_rate_percent": 1.5,
                "error_5xx_rate_percent": 0.2
            },
            "violations": []
        }
    """
    window_minutes = _parse_window_minutes(request.args.get('window'))

    tracker = _get_rollout_tracker()
    if tracker is None:
        return jsonify({
            "error": "RolloutTracker unavailable",
            "timestamp": _get_utc_iso_timestamp(),
            "available": False
        }), 503

    try:
        slo_result = tracker.evaluate_slo_compliance(window_minutes)

        return jsonify({
            "timestamp": _get_utc_iso_timestamp(),
            "window_minutes": window_minutes,
            "available": True,
            **slo_result
        })
    except Exception as e:
        logger.error(f"Failed to get SLO compliance: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": _get_utc_iso_timestamp(),
            "available": False
        }), 500
