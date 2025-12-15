"""Phase 7 API routes - Performance, Growth & Beta Introduction.

Phase 1.6 refactoring: PR1.6b - Extract Phase 7 routes from main.py.

This module provides routes for:
- Phase 7 system status and configuration
- HITL approval system (pending requests, history)
- Beta program management
- Growth strategy metrics
- Operations performance metrics
- Monitoring dashboard and alerts
- Resilience metrics
- Environment validation

NOTE: These routes use synchronous imports from Phase 7 modules.
Unlike Phase 4-6 routes, these don't require async event loop handling.
"""
import datetime
import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

bp = Blueprint("phase7", __name__)


def _get_backend_services_available():
    """Check if backend services are available at runtime.

    This function checks the BACKEND_SERVICES_AVAILABLE flag from src.main
    at runtime to support test patching.

    Returns:
        bool: True if backend services are available
    """
    import src.main
    return src.main.BACKEND_SERVICES_AVAILABLE


def _get_monitoring_dashboard():
    """Get monitoring dashboard service at runtime.

    Returns:
        MonitoringDashboard: The monitoring dashboard service instance
    """
    from src.services.monitoring_dashboard import monitoring_dashboard
    return monitoring_dashboard


def _get_persistent_state_manager():
    """Get PersistentStateManager at runtime.

    Returns:
        PersistentStateManager: The persistent state manager instance
    """
    from src.persistence.state_manager import PersistentStateManager
    return PersistentStateManager()


def init_phase7_routes(backend_services_available):
    """Initialize Phase 7 routes (logging only).

    This function is called from main.py for logging purposes.

    Args:
        backend_services_available: Boolean flag (used for logging only)
    """
    logger.info(f"Phase 7 routes initialized: backend_services_available={backend_services_available}")


@bp.route("/api/phase7/status")
def phase7_status():
    """Phase 7 system status endpoint"""
    try:
        from phase7_startup import Phase7System

        system = Phase7System()

        status = {
            "phase": "Phase 7: Performance, Growth & Beta Introduction",
            "version": "1.0.0",
            "enabled": system.config.get("phase7", {}).get("enabled", False),
            "components": {
                "ops_agent": system.config.get("ops_agent", {}).get("enabled", False),
                "growth_strategist": system.config.get("growth_strategist", {}).get(
                    "enabled", False
                ),
                "pm_agent": system.config.get("pm_agent", {}).get("enabled", False),
                "hitl_approval": system.config.get("hitl_approval", {}).get(
                    "enabled", False
                ),
            },
            "integration": {
                "phase6_security": system.config.get("integration", {}).get(
                    "phase6_security", False
                ),
                "meta_agent_decision_hub": system.config.get("integration", {}).get(
                    "meta_agent_decision_hub", False
                ),
                "monitoring_system": system.config.get("integration", {}).get(
                    "monitoring_system", False
                ),
            },
            "timestamp": datetime.datetime.now().isoformat(),
        }

        return jsonify(status)

    except Exception as e:
        return jsonify({"error": str(e), "phase": "Phase 7", "status": "error"}), 500


@bp.route("/api/phase7/approvals/pending")
def get_pending_approvals():
    """Get pending HITL approval requests"""
    try:
        from hitl_approval_system import HITLApprovalSystem

        hitl_system = HITLApprovalSystem()

        pending = hitl_system.get_pending_requests()
        return jsonify(
            {
                "pending_requests": [
                    {
                        "request_id": req.request_id,
                        "trace_id": req.trace_id,
                        "title": req.title,
                        "description": req.description,
                        "priority": req.priority,
                        "requester_agent": req.requester_agent,
                        "created_at": req.created_at.isoformat(),
                        "expires_at": req.expires_at.isoformat(),
                    }
                    for req in pending
                ],
                "count": len(pending),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/approvals/history")
def get_approval_history():
    """Get HITL approval history"""
    try:
        from hitl_approval_system import HITLApprovalSystem

        hitl_system = HITLApprovalSystem()

        limit = int(request.args.get("limit", 50))
        history = hitl_system.get_approval_history(limit=limit)

        return jsonify(
            {
                "approval_history": [
                    {
                        "request_id": req.request_id,
                        "trace_id": req.trace_id,
                        "title": req.title,
                        "status": req.status.value,
                        "approved_by": req.approved_by,
                        "approved_at": (
                            req.approved_at.isoformat() if req.approved_at else None
                        ),
                        "approval_channel": (
                            req.approval_channel.value if req.approval_channel else None
                        ),
                        "created_at": req.created_at.isoformat(),
                    }
                    for req in history
                ],
                "count": len(history),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/beta/candidates")
def get_beta_candidates():
    """Get Beta program candidates"""
    try:
        from pm_agent import PMAgent

        pm_agent = PMAgent()

        status = pm_agent.get_beta_program_status()
        return jsonify(status)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/growth/metrics")
def get_growth_metrics():
    """Get growth strategy metrics"""
    try:
        from growth_strategist import GrowthStrategist

        growth_strategist = GrowthStrategist()

        report = growth_strategist.get_growth_report()
        return jsonify(report)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/ops/metrics")
def get_ops_metrics():
    """Get operations performance metrics"""
    try:
        from ops_agent import OpsAgent

        ops_agent = OpsAgent()

        report = ops_agent.get_performance_report()
        return jsonify(report)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/monitoring/dashboard")
def get_monitoring_dashboard():
    """Get monitoring dashboard data"""
    try:
        if not _get_backend_services_available():
            return jsonify({"error": "Backend services not available"}), 500

        monitoring_dashboard = _get_monitoring_dashboard()
        hours = int(request.args.get("hours", 1))
        dashboard_data = monitoring_dashboard.get_dashboard_data(hours=hours)

        return jsonify(dashboard_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/monitoring/metrics")
def get_resilience_metrics():
    """Get resilience pattern metrics"""
    try:
        from resilience_patterns import resilience_manager
        from saga_orchestrator import saga_orchestrator

        persistent_state_manager = _get_persistent_state_manager()

        metrics = {
            "resilience": resilience_manager.get_all_metrics(),
            "storage": persistent_state_manager.get_storage_stats(),
            "saga": saga_orchestrator.get_orchestrator_metrics(),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        return jsonify(metrics)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/monitoring/alerts")
def get_monitoring_alerts():
    """Get current monitoring alerts"""
    try:
        if not _get_backend_services_available():
            return jsonify({"error": "Backend services not available"}), 500

        monitoring_dashboard = _get_monitoring_dashboard()
        if monitoring_dashboard.metrics_history:
            latest_metrics = monitoring_dashboard.metrics_history[-1]
            alerts = monitoring_dashboard._generate_alerts(latest_metrics)
            return jsonify({"alerts": alerts, "count": len(alerts)})
        else:
            return jsonify({"alerts": [], "count": 0})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/environment/validate", methods=["GET", "POST"])
def validate_environment_route():
    """Validate environment configuration"""
    try:
        from env_schema_validator import env_schema_validator

        validation_result = env_schema_validator.validate_environment()
        config_summary = env_schema_validator.get_config_summary()

        return jsonify(
            {
                "validation": {
                    "valid": validation_result.valid,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                    "missing_required": validation_result.missing_required,
                    "invalid_values": validation_result.invalid_values,
                },
                "summary": config_summary,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/phase7/resilience/metrics", methods=["GET"])
def get_phase7_resilience_metrics():
    """Get Phase 7 resilience metrics"""
    try:
        return jsonify(
            {
                "circuit_breakers": {
                    "database": {"status": "closed", "failure_count": 0},
                    "external_api": {"status": "closed", "failure_count": 0},
                },
                "retry_patterns": {"exponential_backoff": "enabled", "max_retries": 3},
                "bulkhead_isolation": {
                    "thread_pools": {"api": 10, "background": 5},
                    "connection_pools": {"database": 20},
                },
                "status": "operational",
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
