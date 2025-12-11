from flask import Blueprint, jsonify, request, Response
import logging
from datetime import datetime, timezone
from typing import Dict, Any

DEFAULT_WINDOW_MINUTES = 15
MIN_WINDOW_MINUTES = 1
MAX_WINDOW_MINUTES = 240

logger = logging.getLogger(__name__)

metrics_bp = Blueprint('metrics', __name__)


def _get_redis_client():
    """Get Redis client for metrics retrieval"""
    try:
        from src.utils.redis_client import get_redis_client
        return get_redis_client()
    except Exception as e:
        logger.warning(f"Failed to get Redis client: {e}")
        return None


def _get_orchestrator_metrics():
    """Get OrchestratorMetrics instance"""
    try:
        from orchestrator_metrics import get_orchestrator_metrics
        redis_client = _get_redis_client()
        return get_orchestrator_metrics(redis_client=redis_client, enabled=True)
    except ImportError:
        logger.warning("OrchestratorMetrics not available - ensure PYTHONPATH includes orchestrator")
        return None
    except Exception as e:
        logger.warning(f"Failed to get OrchestratorMetrics: {e}")
        return None


def _get_utc_iso_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_api_metrics(window_minutes: int = 15) -> Dict[str, Any]:
    """Collect API-level metrics from Redis"""
    redis_client = _get_redis_client()
    if not redis_client:
        return {"available": False, "error": "Redis unavailable"}

    try:
        total_queue_depth = 0
        for key in redis_client.scan_iter(match='rq:queue:*'):
            total_queue_depth += redis_client.llen(key)

        failed_count = sum(1 for _ in redis_client.scan_iter(match='rq:failed:*'))

        return {
            "available": True,
            "queue_depth": total_queue_depth,
            "failed_jobs": failed_count,
        }
    except Exception as e:
        logger.warning(f"Failed to collect API metrics: {e}")
        return {"available": False, "error": str(e)}


def _collect_rate_limit_metrics(window_minutes: int = 15) -> Dict[str, Any]:
    """Collect rate limiting metrics from Redis"""
    redis_client = _get_redis_client()
    if not redis_client:
        return {"available": False, "error": "Redis unavailable"}

    try:
        active_limits = sum(1 for _ in redis_client.scan_iter(match='rate_limit:*'))

        return {
            "available": True,
            "active_rate_limits": active_limits,
        }
    except Exception as e:
        logger.warning(f"Failed to collect rate limit metrics: {e}")
        return {"available": False, "error": str(e)}


def _collect_session_command_metrics(window_minutes: int = 15) -> Dict[str, Any]:
    """Collect session command metrics from Redis"""
    redis_client = _get_redis_client()
    if not redis_client:
        return {"available": False, "error": "Redis unavailable"}

    try:
        active_sessions = sum(1 for _ in redis_client.scan_iter(match='session:*:data'))

        pending_commands = 0
        for key in redis_client.scan_iter(match='session:*:commands'):
            pending_commands += redis_client.llen(key)

        return {
            "available": True,
            "active_sessions": active_sessions,
            "pending_commands": pending_commands,
        }
    except Exception as e:
        logger.warning(f"Failed to collect session command metrics: {e}")
        return {"available": False, "error": str(e)}


def _format_prometheus_metrics(metrics: Dict[str, Any]) -> str:
    """Format metrics in Prometheus exposition format"""
    lines = []

    lines.append("# HELP morningai_up Whether the MorningAI service is up")
    lines.append("# TYPE morningai_up gauge")
    lines.append("morningai_up 1")
    lines.append("")

    api_metrics = metrics.get("api", {})
    if api_metrics.get("available"):
        lines.append("# HELP morningai_queue_depth Current job queue depth")
        lines.append("# TYPE morningai_queue_depth gauge")
        lines.append(f"morningai_queue_depth {api_metrics.get('queue_depth', 0)}")
        lines.append("")

        lines.append("# HELP morningai_failed_jobs Number of failed jobs")
        lines.append("# TYPE morningai_failed_jobs gauge")
        lines.append(f"morningai_failed_jobs {api_metrics.get('failed_jobs', 0)}")
        lines.append("")

    rate_limit = metrics.get("rate_limit", {})
    if rate_limit.get("available"):
        lines.append("# HELP morningai_active_rate_limits Active rate limit entries")
        lines.append("# TYPE morningai_active_rate_limits gauge")
        lines.append(
            f"morningai_active_rate_limits {rate_limit.get('active_rate_limits', 0)}"
        )
        lines.append("")

    session = metrics.get("session_commands", {})
    if session.get("available"):
        lines.append("# HELP morningai_active_sessions Active session count")
        lines.append("# TYPE morningai_active_sessions gauge")
        lines.append(f"morningai_active_sessions {session.get('active_sessions', 0)}")
        lines.append("")

        lines.append("# HELP morningai_pending_commands Pending session commands")
        lines.append("# TYPE morningai_pending_commands gauge")
        lines.append(
            f"morningai_pending_commands {session.get('pending_commands', 0)}"
        )
        lines.append("")

    orchestrator = metrics.get("orchestrator", {})
    if orchestrator.get("enabled"):
        workflow = orchestrator.get("workflow", {})
        lines.append("# HELP morningai_workflow_started Workflows started")
        lines.append("# TYPE morningai_workflow_started counter")
        lines.append(f"morningai_workflow_started {workflow.get('started', 0)}")
        lines.append("")

        lines.append("# HELP morningai_workflow_success Workflows completed successfully")
        lines.append("# TYPE morningai_workflow_success counter")
        lines.append(f"morningai_workflow_success {workflow.get('success', 0)}")
        lines.append("")

        lines.append("# HELP morningai_workflow_error Workflows with errors")
        lines.append("# TYPE morningai_workflow_error counter")
        lines.append(f"morningai_workflow_error {workflow.get('error', 0)}")
        lines.append("")

        if workflow.get("started", 0) > 0:
            lines.append("# HELP morningai_workflow_success_rate Workflow success rate")
            lines.append("# TYPE morningai_workflow_success_rate gauge")
            lines.append(
                f"morningai_workflow_success_rate {workflow.get('success_rate', 0)}"
            )
            lines.append("")

        decisions = orchestrator.get("decisions", {})
        for outcome in ["approve", "needs_fix", "request_changes", "pending"]:
            count = decisions.get(outcome, 0)
            lines.append(
                f"# HELP morningai_decision_{outcome} Decision outcome count"
            )
            lines.append(f"# TYPE morningai_decision_{outcome} counter")
            lines.append(f"morningai_decision_{outcome} {count}")
            lines.append("")

        fixer = orchestrator.get("fixer", {})
        lines.append("# HELP morningai_fixer_attempts Fixer attempts")
        lines.append("# TYPE morningai_fixer_attempts counter")
        lines.append(f"morningai_fixer_attempts {fixer.get('attempts', 0)}")
        lines.append("")

        lines.append("# HELP morningai_fixer_success Fixer successes")
        lines.append("# TYPE morningai_fixer_success counter")
        lines.append(f"morningai_fixer_success {fixer.get('success', 0)}")
        lines.append("")

        nodes = orchestrator.get("nodes", {})
        for node_name, node_data in nodes.items():
            if isinstance(node_data, dict):
                lines.append(
                    f"# HELP morningai_node_{node_name}_started Node executions started"
                )
                lines.append(f"# TYPE morningai_node_{node_name}_started counter")
                lines.append(
                    f"morningai_node_{node_name}_started {node_data.get('started', 0)}"
                )
                lines.append("")

                lines.append(
                    f"# HELP morningai_node_{node_name}_success Node executions succeeded"
                )
                lines.append(f"# TYPE morningai_node_{node_name}_success counter")
                lines.append(
                    f"morningai_node_{node_name}_success {node_data.get('success', 0)}"
                )
                lines.append("")

    return "\n".join(lines)


def _parse_window_minutes(window_param: str) -> int:
    """Parse and validate window parameter with range clamping"""
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


@metrics_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get system metrics in JSON or Prometheus format.

    Query Parameters:
        format: 'json' (default) or 'prometheus'
        window: Time window in minutes (default: 15, range: 1-240)

    Returns:
        JSON or Prometheus-formatted metrics
    """
    output_format = request.args.get('format', 'json').lower()
    window_minutes = _parse_window_minutes(request.args.get('window', DEFAULT_WINDOW_MINUTES))

    orchestrator_metrics = _get_orchestrator_metrics()

    metrics_data = {
        "timestamp": _get_utc_iso_timestamp(),
        "window_minutes": window_minutes,
        "api": _collect_api_metrics(window_minutes),
        "rate_limit": _collect_rate_limit_metrics(window_minutes),
        "session_commands": _collect_session_command_metrics(window_minutes),
    }

    if orchestrator_metrics:
        metrics_data["orchestrator"] = orchestrator_metrics.get_comprehensive_summary(
            window_minutes
        )
    else:
        metrics_data["orchestrator"] = {
            "enabled": False,
            "message": "OrchestratorMetrics unavailable"
        }

    if output_format == 'prometheus':
        prometheus_output = _format_prometheus_metrics(metrics_data)
        return Response(
            prometheus_output,
            mimetype='text/plain; version=0.0.4; charset=utf-8'
        )

    return jsonify(metrics_data)


@metrics_bp.route('/metrics/health', methods=['GET'])
def get_metrics_health():
    """
    Quick health check for metrics subsystem.

    Returns:
        JSON with metrics subsystem status
    """
    redis_available = _get_redis_client() is not None
    orchestrator_available = _get_orchestrator_metrics() is not None

    status = "healthy" if redis_available else "degraded"

    return jsonify({
        "status": status,
        "timestamp": _get_utc_iso_timestamp(),
        "components": {
            "redis": "available" if redis_available else "unavailable",
            "orchestrator_metrics": (
                "available" if orchestrator_available else "unavailable"
            ),
        }
    })
