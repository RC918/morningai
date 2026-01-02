"""Phase 4-6 API routes - Meta Agent, Data Intelligence, Security Governance.

Phase 1.6 refactoring: PR1.6a - Extract Phase 4-6 routes from main.py.

This module provides routes for:
- Phase 4: Meta Agent OODA cycle, LangGraph workflows, governance
- Phase 5: QuickSight dashboards, automated reports, growth/referral, marketing
- Phase 6: Security access evaluation, HITL reviews, security audits

IMPORTANT: Uses lazy imports and runtime gating to avoid import-time crashes
when phase4/5/6 packages are not available in certain environments.

NOTE: All API function calls and availability checks use runtime lookup via
src.main to ensure tests can patch the functions and have it take effect.
This is critical for maintaining test compatibility with the original inline
route behavior where functions were called directly from src.main.
"""
import asyncio
import logging
from functools import lru_cache
from typing import Optional

from flask import Blueprint, jsonify, request

from src.middleware.auth_middleware import admin_required, analyst_required

logger = logging.getLogger(__name__)

bp = Blueprint("phase456", __name__)


@lru_cache(maxsize=1)
def _get_cached_redis_client(redis_url: str):
    """Get a cached Redis client to avoid per-request object churn.

    Issue #3486: RouterMetrics Operationalization Gap
    Reviewer feedback: Creating new Redis client on every API request is inefficient.

    Args:
        redis_url: Redis connection URL

    Returns:
        Redis client instance (cached)
    """
    import redis
    return redis.from_url(redis_url)


def _get_main():
    """Get the src.main module at runtime.

    This function imports src.main lazily to avoid circular imports
    and to ensure tests can patch module-level attributes.

    Returns:
        module: The src.main module
    """
    import src.main
    return src.main


def init_phase456_routes(phase_456_available, api_funcs):
    """Initialize Phase 4-6 routes (logging only).

    This function is called from main.py for logging purposes.
    The actual API functions are resolved at runtime via src.main
    to support test patching.

    Note: The api_funcs parameter is kept for backward compatibility
    but is not used - functions are resolved via src.main at runtime.

    Args:
        phase_456_available: Boolean flag (used for logging only)
        api_funcs: Dictionary of API functions (not used, kept for compatibility)
    """
    logger.info(f"Phase 4-6 routes initialized: available={phase_456_available}")


@bp.route("/api/meta-agent/ooda-cycle", methods=["POST"])
def meta_agent_ooda_cycle():
    """Start OODA cycle"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(main.api_meta_agent_ooda_cycle())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/langgraph/workflows", methods=["POST"])
def create_langgraph_workflow():
    """Create LangGraph workflow"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_create_langgraph_workflow(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/langgraph/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    """Execute workflow"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_execute_workflow(workflow_id, request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/governance/status", methods=["GET"])
def governance_status():
    """Get governance status"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(main.api_governance_status())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/governance/policies", methods=["POST"])
def create_governance_policy():
    """Create governance policy"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_create_governance_policy(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/governance/router-metrics", methods=["GET"])
@analyst_required
def get_router_metrics():
    """Get router metrics summary for Flow Controller v3.

    Issue #3486: RouterMetrics Operationalization Gap
    EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing

    Returns router decision metrics including:
    - total_decisions: Total routing decisions in the time window
    - success_rate: Percentage of successful routing decisions
    - fallback_rate: Percentage of fallback decisions
    - average_latency_ms: Average routing decision latency
    - latency_p99_ms: 99th percentile latency
    - node_distribution: Distribution of decisions by target node
    - decision_mode_distribution: Distribution by decision mode (fast_path, slow_path, etc.)

    Query Parameters:
        window_minutes (int): Time window in minutes (default: 15, max: 60)

    Returns:
        JSON object with router metrics summary
    """
    try:
        from common.config.settings import settings

        window_minutes = request.args.get("window_minutes", 15, type=int)
        window_minutes = min(max(window_minutes, 1), 60)

        redis_url = getattr(settings, "REDIS_URL", None)
        if not redis_url:
            return jsonify({
                "enabled": False,
                "message": "Redis not configured - router metrics unavailable"
            }), 200

        try:
            from metrics import CanaryMetrics

            redis_client = _get_cached_redis_client(redis_url)
            canary_metrics = CanaryMetrics(redis_client=redis_client)
            result = canary_metrics.get_router_metrics_summary(window_minutes)
            return jsonify(result)
        except ImportError as e:
            logger.warning(f"Failed to import metrics dependencies: {e}")
            return jsonify({
                "enabled": False,
                "message": "Metrics dependencies not available"
            }), 200
        except Exception as e:
            logger.error(f"Failed to get router metrics: {e}")
            return jsonify({
                "enabled": True,
                "error": str(e)
            }), 500

    except Exception as e:
        logger.error(f"Router metrics endpoint error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/api/quicksight/dashboards", methods=["POST"])
def create_quicksight_dashboard():
    """Create QuickSight dashboard"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_create_quicksight_dashboard(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/quicksight/dashboards/<dashboard_id>/insights", methods=["GET"])
def get_dashboard_insights(dashboard_id):
    """Get dashboard insights"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_get_dashboard_insights(dashboard_id)
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/reports/automated", methods=["POST"])
def generate_automated_report():
    """Generate automated report"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_generate_automated_report(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/growth/referral-programs", methods=["POST"])
def create_referral_program():
    """Create referral program"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_create_referral_program(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/growth/referral-programs/<program_id>/analytics", methods=["GET"])
def get_referral_analytics(program_id):
    """Get referral analytics"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_get_referral_analytics(program_id)
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/growth/content/generate", methods=["POST"])
def generate_marketing_content():
    """Generate marketing content"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_generate_marketing_content(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/business-intelligence/summary", methods=["GET"])
def get_business_intelligence():
    """Get business intelligence summary"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_get_business_intelligence()
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/access/evaluate", methods=["GET", "POST"])
@bp.route("/api/security/access-requests/evaluate", methods=["GET", "POST"])
@admin_required
def evaluate_access_request():
    """Evaluate access request"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_evaluate_access_request(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/events/review", methods=["POST"])
@analyst_required
def review_security_event():
    """Review security event"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_review_security_event(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/hitl/submit", methods=["POST"])
@analyst_required
def submit_hitl_review():
    """Submit HITL review"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        data = request.json or {}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_submit_hitl_review(data)
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/hitl/pending", methods=["GET"])
@analyst_required
def get_pending_reviews():
    """Get pending reviews"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(main.api_get_pending_reviews())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/audit", methods=["GET", "POST"])
@bp.route("/api/security/audit/perform", methods=["GET", "POST"])
@admin_required
def perform_security_audit():
    """Perform security audit"""
    main = _get_main()
    if not main.PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            main.api_perform_security_audit(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/reviews/pending", methods=["GET"])
@analyst_required
def get_pending_security_reviews():
    """Get pending security reviews"""
    main = _get_main()
    try:
        if not main.PHASE_456_AVAILABLE:
            return jsonify({"error": "Phase 4-6 APIs not available"}), 503

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(main.api_get_pending_reviews())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
