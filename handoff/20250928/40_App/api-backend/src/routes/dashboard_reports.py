"""Dashboard and Reports API routes blueprint.

Phase 1.6 refactoring: PR1.6c - Extract Dashboard/Reports/Settings routes from main.py.

This module contains routes for:
- Dashboard layouts management (/api/dashboard/layouts)
- Dashboard widgets (/api/dashboard/widgets, /api/dashboard/widgets/available)
- Dashboard data (/api/dashboard/data)
- Report generation (/api/reports/generate)
- Report templates (/api/reports/templates)
- Report history (/api/reports/history)
- User settings (/api/settings)

For full documentation, see docs/api/DASHBOARD_REPORTS_ROUTES.md
"""
import datetime
import logging

from flask import Blueprint, jsonify, request, send_file, Response

logger = logging.getLogger(__name__)

# Blueprint for Dashboard/Reports/Settings routes
# Name: 'dashboard_reports' (globally unique)
bp = Blueprint("dashboard_reports", __name__)


def init_dashboard_reports_routes(backend_services_available):
    """Initialize Dashboard/Reports routes (logging only).

    This function is called from main.py for logging purposes.
    The actual backend services availability is checked at runtime
    via _get_backend_services_available() to support test patching.

    Args:
        backend_services_available: Boolean flag (used for logging only)
    """
    logger.info(f"Dashboard/Reports routes initialized: backend_services_available={backend_services_available}")


def _get_backend_services_available():
    """Check if backend services are available at runtime.

    This function checks the BACKEND_SERVICES_AVAILABLE flag from src.main
    at runtime to support test patching via @patch('src.main.BACKEND_SERVICES_AVAILABLE', False).

    Returns:
        bool: True if backend services are available
    """
    import src.main
    return src.main.BACKEND_SERVICES_AVAILABLE


def _get_persistent_state_manager():
    """Get PersistentStateManager at runtime.

    Uses lazy import to avoid import-time crashes when backend services
    are not available. Tests can patch this function to inject mocks.

    Returns:
        PersistentStateManager instance
    """
    from src.persistence.state_manager import PersistentStateManager
    return PersistentStateManager()


def _get_monitoring_dashboard():
    """Get monitoring_dashboard service at runtime.

    Uses lazy import to avoid import-time crashes when backend services
    are not available. Tests can patch this function to inject mocks.

    Returns:
        monitoring_dashboard service instance
    """
    from src.services.monitoring_dashboard import monitoring_dashboard
    return monitoring_dashboard


def _get_report_generator():
    """Get report_generator service at runtime.

    Uses lazy import to avoid import-time crashes when backend services
    are not available. Tests can patch this function to inject mocks.

    Returns:
        report_generator service instance
    """
    from src.services.report_generator import report_generator
    return report_generator


# =============================================================================
# Dashboard Layout Routes
# =============================================================================

@bp.route("/api/dashboard/layouts", methods=["GET", "POST"])
def manage_dashboard_layouts():
    """Get or save user dashboard layouts.

    GET: Retrieve dashboard layout for a user (default layout if none saved)
    POST: Save dashboard layout for a user

    Query Parameters (GET):
        user_id: User ID (default: "default")

    Request Body (POST):
        user_id: User ID (default: "default")
        layout: Layout configuration object

    Returns:
        JSON response with layout data or success message
    """
    try:
        persistent_state_manager = _get_persistent_state_manager()

        if request.method == "GET":
            user_id = request.args.get("user_id", "default")
            layout = persistent_state_manager.load_dashboard_layout(user_id)
            if not layout:
                layout = {
                    "widgets": [
                        {
                            "id": "cpu_usage",
                            "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                        },
                        {
                            "id": "memory_usage",
                            "position": {"x": 6, "y": 0, "w": 6, "h": 4},
                        },
                        {
                            "id": "response_time",
                            "position": {"x": 0, "y": 4, "w": 6, "h": 4},
                        },
                        {
                            "id": "error_rate",
                            "position": {"x": 6, "y": 4, "w": 6, "h": 4},
                        },
                        {
                            "id": "active_strategies",
                            "position": {"x": 0, "y": 8, "w": 4, "h": 3},
                        },
                        {
                            "id": "pending_approvals",
                            "position": {"x": 4, "y": 8, "w": 4, "h": 3},
                        },
                        {
                            "id": "circuit_breakers",
                            "position": {"x": 8, "y": 8, "w": 4, "h": 3},
                        },
                    ]
                }
            return jsonify(layout)

        elif request.method == "POST":
            data = request.get_json()
            user_id = data.get("user_id", "default")
            layout = data.get("layout", {})

            persistent_state_manager.save_dashboard_layout(user_id, layout)
            return jsonify({"status": "success", "message": "Layout saved"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# Dashboard Widget Routes
# =============================================================================

@bp.route("/api/dashboard/widgets/available")
def get_available_widgets():
    """Get list of available dashboard widgets.

    Returns a list of all widgets that can be added to a dashboard,
    including their type and category.

    Returns:
        JSON array of widget definitions
    """
    widgets = [
        {"id": "cpu_usage", "name": "CPU使用率", "type": "gauge", "category": "system"},
        {
            "id": "memory_usage",
            "name": "內存使用率",
            "type": "gauge",
            "category": "system",
        },
        {
            "id": "response_time",
            "name": "響應時間",
            "type": "line_chart",
            "category": "performance",
        },
        {
            "id": "error_rate",
            "name": "錯誤率",
            "type": "area_chart",
            "category": "reliability",
        },
        {
            "id": "active_strategies",
            "name": "活躍策略",
            "type": "counter",
            "category": "ai",
        },
        {
            "id": "pending_approvals",
            "name": "待審批",
            "type": "counter",
            "category": "workflow",
        },
        {
            "id": "circuit_breakers",
            "name": "熔斷器狀態",
            "type": "status_grid",
            "category": "resilience",
        },
        {
            "id": "cost_today",
            "name": "今日成本",
            "type": "counter",
            "category": "financial",
        },
        {
            "id": "performance_trend",
            "name": "性能趨勢",
            "type": "line_chart",
            "category": "performance",
        },
    ]
    return jsonify(widgets)


@bp.route(
    "/api/dashboard/data", methods=["GET", "POST"], endpoint="get_dashboard_data_legacy"
)
def get_dashboard_data_legacy():
    """Get real-time dashboard data (legacy endpoint).

    This endpoint returns dashboard data including system metrics.
    It's marked as "legacy" because newer dashboard data should use
    the /api/dashboard route from the dashboard blueprint.

    Query Parameters:
        hours: Number of hours of data to retrieve (default: 1)

    Returns:
        JSON response with dashboard data and system metrics
    """
    try:
        if not _get_backend_services_available():
            return jsonify({"error": "Backend services not available"}), 500

        monitoring_dashboard = _get_monitoring_dashboard()
        hours = int(request.args.get("hours", 1))
        dashboard_data = monitoring_dashboard.get_dashboard_data(hours=hours)

        dashboard_data["system_metrics"] = {
            "cpu_usage": 72,
            "memory_usage": 68,
            "response_time": 145,
            "error_rate": 0.02,
            "active_strategies": 12,
            "pending_approvals": 3,
            "cost_today": 45.67,
        }

        return jsonify(dashboard_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/dashboard/widgets", methods=["GET"])
def get_dashboard_widgets():
    """Get available dashboard widgets with configuration.

    Returns a list of widgets with their configuration options,
    different from /api/dashboard/widgets/available which returns
    a simpler list.

    Returns:
        JSON object with widgets array
    """
    widgets = [
        {
            "id": "performance_metrics",
            "name": "性能指標",
            "type": "chart",
            "description": "系統性能監控圖表",
            "config": {"chart_type": "line", "data_points": 24},
        },
        {
            "id": "recent_decisions",
            "name": "最近決策",
            "type": "list",
            "description": "AI系統最近執行的決策",
            "config": {"max_items": 5},
        },
        {
            "id": "system_status",
            "name": "系統狀態",
            "type": "status",
            "description": "整體系統健康狀態",
            "config": {"refresh_interval": 30},
        },
    ]
    return jsonify({"widgets": widgets})


# =============================================================================
# Report Routes
# =============================================================================

@bp.route("/api/reports/generate", methods=["POST"])
def generate_report():
    """Generate custom reports.

    Generates reports in various formats (JSON, PDF, CSV) based on
    the specified report type and time range.

    Request Body:
        type: Report type (default: "performance")
        time_range: Time range for report data (default: "24h")
        format: Output format - "json", "pdf", or "csv" (default: "json")

    Returns:
        JSON report data, PDF file, or CSV file depending on format
    """
    try:
        if not _get_backend_services_available():
            return jsonify({"error": "Backend services not available"}), 500

        report_generator = _get_report_generator()
        data = request.get_json()
        report_type = data.get("type", "performance")
        time_range = data.get("time_range", "24h")
        format_type = data.get("format", "json")

        report_data = report_generator.generate_report(report_type, time_range)

        if format_type == "pdf":
            pdf_path = report_generator.export_pdf(report_data, report_type)
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"report_{report_type}_{time_range}.pdf",
            )
        elif format_type == "csv":
            csv_data = report_generator.export_csv(report_data)
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{report_type}_{time_range}.csv"
                },
            )
        else:
            from dataclasses import asdict

            report_dict = asdict(report_data)

            def serialize_datetime(obj):
                if isinstance(obj, datetime.datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_datetime(item) for item in obj]
                return obj

            report_dict = serialize_datetime(report_dict)
            return jsonify(report_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/reports/templates")
def get_report_templates():
    """Get available report templates.

    Returns a list of predefined report templates that users can
    use to generate reports.

    Returns:
        JSON array of report template definitions
    """
    templates = [
        {
            "id": "performance",
            "name": "系統性能報告",
            "description": "包含CPU、內存、響應時間等系統性能指標",
            "metrics": ["cpu_usage", "memory_usage", "response_time", "error_rate"],
        },
        {
            "id": "task_tracking",
            "name": "任務追蹤報告",
            "description": "顯示AI Agent任務執行狀態和成功率",
            "metrics": ["task_success_rate", "avg_duration", "agent_performance"],
        },
        {
            "id": "resilience",
            "name": "韌性模式報告",
            "description": "熔斷器、隔艙模式和系統韌性指標",
            "metrics": [
                "circuit_breaker_status",
                "bulkhead_utilization",
                "retry_rates",
            ],
        },
        {
            "id": "financial",
            "name": "成本分析報告",
            "description": "系統運行成本和資源使用分析",
            "metrics": ["daily_cost", "resource_utilization", "cost_trends"],
        },
    ]
    return jsonify(templates)


@bp.route("/api/reports/history")
def get_report_history():
    """Get report generation history.

    Returns a list of previously generated reports.

    Returns:
        JSON array of report history entries
    """
    try:
        persistent_state_manager = _get_persistent_state_manager()

        history = persistent_state_manager.get_report_history()
        return jsonify(history)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# Settings Routes
# =============================================================================

@bp.route("/api/settings", methods=["GET", "POST"], endpoint="settings")
def settings_route():
    """Get or update user settings.

    GET: Retrieve current user settings (profile and preferences)
    POST: Update user settings

    Request Body (POST):
        Any settings data to save

    Returns:
        JSON response with settings data or success message
    """
    if request.method == "GET":
        return jsonify(
            {
                "profile": {
                    "name": "Ryan Chen",
                    "email": "ryan@morningai.com",
                    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan",
                    "role": "Owner",
                },
                "preferences": {
                    "language": "zh-TW",
                    "theme": "light",
                    "notifications": {
                        "email": True,
                        "desktop": True,
                        "aiSuggestions": True,
                    },
                },
            }
        )

    elif request.method == "POST":
        data = request.get_json()
        return jsonify({"message": "Settings saved successfully", "data": data})
