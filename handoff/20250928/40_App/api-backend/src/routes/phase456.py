"""Phase 4-6 API routes - Meta Agent, Data Intelligence, Security Governance.

Phase 1.6 refactoring: PR1.6a - Extract Phase 4-6 routes from main.py.

This module provides routes for:
- Phase 4: Meta Agent OODA cycle, LangGraph workflows, governance
- Phase 5: QuickSight dashboards, automated reports, growth/referral, marketing
- Phase 6: Security access evaluation, HITL reviews, security audits

IMPORTANT: Uses lazy imports and runtime gating to avoid import-time crashes
when phase4/5/6 packages are not available in certain environments.
"""
import asyncio
import logging

from flask import Blueprint, jsonify, request

from src.middleware.auth_middleware import admin_required, analyst_required

logger = logging.getLogger(__name__)

bp = Blueprint("phase456", __name__)

PHASE_456_AVAILABLE = False
_api_functions = {}


def init_phase456_routes(phase_456_available, api_funcs):
    """Initialize Phase 4-6 routes with availability flag and API functions.

    This function is called from main.py to pass the shared dependencies.
    The gating flag and API functions are set at app initialization time,
    not at module import time, to avoid import-time crashes.

    Args:
        phase_456_available: Boolean flag indicating if Phase 4-6 APIs are available
        api_funcs: Dictionary of API functions from phase4/5/6 modules
    """
    global PHASE_456_AVAILABLE, _api_functions
    PHASE_456_AVAILABLE = phase_456_available
    _api_functions = api_funcs
    logger.info(f"Phase 4-6 routes initialized: available={phase_456_available}")


@bp.route("/api/meta-agent/ooda-cycle", methods=["POST"])
def meta_agent_ooda_cycle():
    """启动 OODA 循环"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_api_functions["api_meta_agent_ooda_cycle"]())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/langgraph/workflows", methods=["POST"])
def create_langgraph_workflow():
    """创建 LangGraph 工作流"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_create_langgraph_workflow"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/langgraph/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    """执行工作流"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_execute_workflow"](workflow_id, request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/governance/status", methods=["GET"])
def governance_status():
    """获取治理状态"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_api_functions["api_governance_status"]())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/governance/policies", methods=["POST"])
def create_governance_policy():
    """创建治理政策"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_create_governance_policy"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/quicksight/dashboards", methods=["POST"])
def create_quicksight_dashboard():
    """创建 QuickSight 仪表板"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_create_quicksight_dashboard"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/quicksight/dashboards/<dashboard_id>/insights", methods=["GET"])
def get_dashboard_insights(dashboard_id):
    """获取仪表板洞察"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_get_dashboard_insights"](dashboard_id)
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/reports/automated", methods=["POST"])
def generate_automated_report():
    """生成自动化报告"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_generate_automated_report"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/growth/referral-programs", methods=["POST"])
def create_referral_program():
    """创建推荐计划"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_create_referral_program"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/growth/referral-programs/<program_id>/analytics", methods=["GET"])
def get_referral_analytics(program_id):
    """获取推荐分析"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_get_referral_analytics"](program_id)
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/growth/content/generate", methods=["POST"])
def generate_marketing_content():
    """生成营销内容"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_generate_marketing_content"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/business-intelligence/summary", methods=["GET"])
def get_business_intelligence():
    """获取商业智能摘要"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_get_business_intelligence"]()
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/access/evaluate", methods=["GET", "POST"])
@bp.route("/api/security/access-requests/evaluate", methods=["GET", "POST"])
@admin_required
def evaluate_access_request():
    """评估访问请求"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_evaluate_access_request"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/events/review", methods=["POST"])
@analyst_required
def review_security_event():
    """审查安全事件"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_review_security_event"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/hitl/submit", methods=["POST"])
@analyst_required
def submit_hitl_review():
    """提交人工审查"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        data = request.json or {}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_submit_hitl_review"](data)
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/hitl/pending", methods=["GET"])
@analyst_required
def get_pending_reviews():
    """获取待审查项目"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_api_functions["api_get_pending_reviews"]())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/audit", methods=["GET", "POST"])
@bp.route("/api/security/audit/perform", methods=["GET", "POST"])
@admin_required
def perform_security_audit():
    """执行安全审计"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _api_functions["api_perform_security_audit"](request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/security/reviews/pending", methods=["GET"])
@analyst_required
def get_pending_security_reviews():
    """Get pending security reviews"""
    try:
        if not PHASE_456_AVAILABLE:
            return jsonify({"error": "Phase 4-6 APIs not available"}), 503

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_api_functions["api_get_pending_reviews"]())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
