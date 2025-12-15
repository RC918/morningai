import os
import sys
import datetime
import asyncio
import re
import logging
from common.config.settings import settings as app_settings

from pathlib import Path
# Path calculation: main.py -> src/ -> api-backend/ -> 40_App/ -> 20250928/ -> handoff/ -> repo root
repo_root = Path(__file__).resolve().parents[5]  # api-backend/src/main.py -> repo root
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Added repo root to sys.path: {repo_root}")

# Add 40_App directory to sys.path so that 'orchestrator' package can be imported
# The import 'from orchestrator.xxx' requires the parent of 'orchestrator' in sys.path
app_dir = app_settings.orchestrator_path
if not app_dir:
    # Point to 40_App directory (parent of orchestrator), not orchestrator itself
    app_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../..")
    )

if os.path.exists(app_dir) and app_dir not in sys.path:
    sys.path.insert(0, app_dir)
    logging.info(f"Added app directory to sys.path: {app_dir}")
elif not os.path.exists(app_dir):
    logging.warning(
        f"App directory does not exist: {app_dir}. Orchestrator features may not work."
    )

from flask import Flask, send_from_directory, jsonify, request, send_file, Response
from src.models.user import db
# Note: jwt_required, admin_required, analyst_required moved to phase456 blueprint (PR1.6a)
from common.config.settings import get_settings
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}',
)
logger = logging.getLogger(__name__)

# Import _as_bool from utils module (Phase 1 refactoring: PR1a)
# Re-exported at module level for backward compatibility
# Tests should patch via 'src.main._as_bool' (not 'src.utils.helpers._as_bool')
from src.utils.helpers import _as_bool  # noqa: E402

# Sentry initialization (Phase 1 refactoring: PR1f)
# Sentry setup moved to src/extensions/sentry.py
# NOTE: before_send is NOT re-exported because Sentry SDK holds direct reference
# Tests must patch 'src.extensions.sentry.before_send' (not 'src.main.before_send')
from src.extensions.sentry import init_sentry  # noqa: E402

SENTRY_DSN = init_sentry(app_settings, _as_bool)

try:
    from security_manager import SecurityManager

    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from src.persistence.state_manager import PersistentStateManager
    from src.services.monitoring_dashboard import monitoring_dashboard
    from src.services.report_generator import report_generator
    from src.utils.env_schema_validator import validate_environment
    from src.routes.mock_api import mock_api

    BACKEND_SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Backend services not available: {e}")
    BACKEND_SERVICES_AVAILABLE = False

# Phase 4-6 API imports (module-level for availability flag)
try:
    morningai_root = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", ".."
    )
    sys.path.insert(0, morningai_root)
    from phase4_meta_agent_api import (
        api_meta_agent_ooda_cycle,
        api_create_langgraph_workflow,
        api_execute_workflow,
        api_governance_status,
        api_create_governance_policy,
    )
    from phase5_data_intelligence_api import (
        api_create_quicksight_dashboard,
        api_get_dashboard_insights,
        api_generate_automated_report,
        api_create_referral_program,
        api_get_referral_analytics,
        api_generate_marketing_content,
        api_get_business_intelligence,
    )
    from phase6_security_governance_api import (
        api_evaluate_access_request,
        api_review_security_event,
        api_submit_hitl_review,
        api_get_pending_reviews,
        api_perform_security_audit,
    )

    PHASE_456_AVAILABLE = True
    print("Phase 4-6 APIs imported successfully")
except ImportError as e:
    print(f"Phase 4-6 APIs not available: {e}")
    PHASE_456_AVAILABLE = False

# Setup CORS middleware (Phase 1 refactoring: PR1b)
# CORS implementation moved to src/middleware/cors.py
from src.middleware.cors import (  # noqa: E402
    is_vercel_preview as _is_vercel_preview_impl,
    add_cors_headers as _add_cors_headers_impl,
)

# Register all blueprints (Phase 1 refactoring: PR1c)
# Blueprint registration moved to src/routes/__init__.py
from src.routes import register_blueprints  # noqa: E402

# Register error handlers (Phase 1 refactoring: PR1d)
# Error handlers moved to src/middleware/error_handlers.py
from src.middleware.error_handlers import register_error_handlers  # noqa: E402
from src.middleware.error_handlers import handle_exception  # noqa: E402, F401

# Database configuration and initialization (Phase 1 refactoring: PR1e)
# Database setup moved to src/extensions/database.py
from src.extensions.database import (  # noqa: E402
    configure_database,
    initialize_database,
)

from src.services.auth_service import validate_security_config

# Module-level CORS configuration for backward compatibility
# These are used by module-level wrapper functions that tests can patch
cors_origins = (app_settings.cors_origins or "http://localhost:5173,http://localhost:5174").split(",")
cors_origins = [origin.strip() for origin in cors_origins]
cors_debug_enabled = _as_bool(os.getenv("CORS_DEBUG")) and not app_settings.is_production


# Wrapper functions to maintain backward-compatible signatures
# These use closure variables (cors_origins, cors_debug_enabled, app_settings.environment)
# Tests should patch via 'src.main.is_vercel_preview' (not 'src.middleware.cors.*')
def is_vercel_preview(origin):
    """Check if origin is a Vercel preview URL.

    Allows Vercel preview origins in staging and development environments.
    Blocks them in production for security.

    This is a wrapper that maintains the original function signature for backward compatibility.
    The implementation is in src/middleware/cors.py.
    """
    return _is_vercel_preview_impl(origin, app_settings.environment, cors_debug_enabled)


def add_cors_headers(response):
    """Add CORS headers for allowed origins including Vercel preview URLs.

    This is the single authority source for CORS handling in the application.
    Flask-CORS has been removed to avoid dual-mechanism conflicts.

    This is a wrapper that maintains the original function signature for backward compatibility.
    The implementation is in src/middleware/cors.py.
    """
    return _add_cors_headers_impl(response, cors_origins, app_settings.environment, cors_debug_enabled)


def get_health_payload():
    """Generate health check payload with JSON serializable values.

    This function is exported at module level for backward compatibility.
    It is used by the health check endpoint and can be imported from src.main.
    """
    try:
        db_status = "connected"
        try:
            with db.engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"

        redis_info = {"status": "not_configured"}
        try:
            from src.utils.redis_client import get_redis_connection_info

            redis_info = get_redis_connection_info()
            redis_info["status"] = "connected"
        except Exception as e:
            redis_info = {"status": "error", "error": str(e)[:100]}

        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "database": str(db_status),
            "redis": redis_info,
            "phase": str(
                app_settings.app_phase or "Phase 8: Self-service Dashboard & Reporting Center"
            ),
            "version": str(app_settings.app_version or "8.0.0"),
            "git_commit": str(app_settings.git_commit or app_settings.render_git_commit or "unknown"),
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {
                "phase4_apis": (
                    "available"
                    if "phase4_meta_agent_api" in sys.modules
                    else "unavailable"
                ),
                "phase5_apis": (
                    "available"
                    if "phase5_data_intelligence_api" in sys.modules
                    else "unavailable"
                ),
                "phase6_apis": (
                    "available"
                    if "phase6_security_governance_api" in sys.modules
                    else "unavailable"
                ),
                "security_manager": (
                    "available" if SECURITY_AVAILABLE else "unavailable"
                ),
                "backend_services": (
                    "available" if BACKEND_SERVICES_AVAILABLE else "unavailable"
                ),
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "error",
            "phase": "Phase 8: Self-service Dashboard & Reporting Center",
            "version": "8.0.0",
            "error": str(e)[:200],
            "timestamp": datetime.datetime.now().isoformat(),
        }


def create_app(config=None):
    """Create and configure the Flask application.

    This is the application factory function (Phase 1.5 refactoring).
    It encapsulates all Flask app initialization logic.

    Args:
        config: Optional configuration dictionary to override defaults.

    Returns:
        Flask: The configured Flask application instance.
    """
    flask_app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

    # Security configuration validation (production only)
    if app_settings.is_production and not app_settings.testing:
        try:
            validate_security_config()
        except SystemExit as e:
            logger.error(f"Security configuration validation failed: {e}")
            raise

    if app_settings.is_production and not app_settings.testing:
        from src.utils.pre_auth_token import get_pre_auth_manager

        try:
            get_pre_auth_manager()
            logger.info("Pre-auth token manager initialized successfully")
        except RuntimeError as e:
            logger.error(f"Failed to initialize pre-auth token manager: {e}")
            raise

    # Configure Flask app settings
    flask_secret = get_settings().flask_secret_key
    if not flask_secret:
        if app_settings.is_production and not app_settings.testing:
            raise RuntimeError("FLASK_SECRET_KEY must be set in production environment.")
        flask_secret = "dev-only-fallback-secret-key"
    flask_app.config["SECRET_KEY"] = flask_secret

    enable_mock = os.getenv("ENABLE_MOCK_USERS")
    if enable_mock is not None:
        flask_app.config["ENABLE_MOCK_USERS"] = _as_bool(enable_mock)

    flask_app.config["TESTING"] = _as_bool(os.getenv("TESTING"))
    rate_limit_env = os.getenv("RATE_LIMIT_REQUESTS")
    if rate_limit_env:
        flask_app.config["RATE_LIMIT_REQUESTS"] = int(rate_limit_env)

    # Apply custom config if provided
    if config:
        flask_app.config.update(config)

    # Register CORS after_request handler using the module-level wrapper function
    @flask_app.after_request
    def _cors_after_request(response):
        return add_cors_headers(response)

    # Log CORS startup info if debug enabled
    if cors_debug_enabled:
        logging.debug(f"[CORS DEBUG] Startup: env={app_settings.environment}, allowlist_count={len(cors_origins)}")

    # Security manager setup
    if SECURITY_AVAILABLE:
        encryption_master_key = app_settings.encryption_master_key
        if not encryption_master_key:
            if app_settings.is_production and not app_settings.testing:
                raise RuntimeError("ENCRYPTION_MASTER_KEY must be set in production environment.")
            encryption_master_key = "dev-only-fallback-master-key"

        security_config = {
            "master_key": encryption_master_key,
            "secret_key": flask_app.config["SECRET_KEY"],
            "audit_log_file": "api_audit.log",
        }
        security_manager = SecurityManager(security_config)
        flask_app.security_manager = security_manager

    # Build Phase 4-6 API functions dictionary for blueprint initialization (PR1.6a)
    phase_456_api_funcs = {}
    if PHASE_456_AVAILABLE:
        phase_456_api_funcs = {
            "api_meta_agent_ooda_cycle": api_meta_agent_ooda_cycle,
            "api_create_langgraph_workflow": api_create_langgraph_workflow,
            "api_execute_workflow": api_execute_workflow,
            "api_governance_status": api_governance_status,
            "api_create_governance_policy": api_create_governance_policy,
            "api_create_quicksight_dashboard": api_create_quicksight_dashboard,
            "api_get_dashboard_insights": api_get_dashboard_insights,
            "api_generate_automated_report": api_generate_automated_report,
            "api_create_referral_program": api_create_referral_program,
            "api_get_referral_analytics": api_get_referral_analytics,
            "api_generate_marketing_content": api_generate_marketing_content,
            "api_get_business_intelligence": api_get_business_intelligence,
            "api_evaluate_access_request": api_evaluate_access_request,
            "api_review_security_event": api_review_security_event,
            "api_submit_hitl_review": api_submit_hitl_review,
            "api_get_pending_reviews": api_get_pending_reviews,
            "api_perform_security_audit": api_perform_security_audit,
        }

    # Register blueprints
    register_blueprints(
        flask_app,
        backend_services_available=BACKEND_SERVICES_AVAILABLE,
        phase_456_available=PHASE_456_AVAILABLE,
        phase_456_api_funcs=phase_456_api_funcs,
    )

    # Register error handlers
    register_error_handlers(flask_app, sentry_dsn=SENTRY_DSN)

    # Register inline routes
    _register_inline_routes(flask_app)

    # Database configuration and initialization
    configure_database(flask_app, app_settings, db)
    initialize_database(flask_app, db, app_settings)

    return flask_app


def _register_inline_routes(flask_app):
    """Register all inline routes on the Flask app.

    This function contains all routes that are currently defined inline in main.py.
    These routes will be moved to separate blueprint modules in Phase 1.6.

    Args:
        flask_app: The Flask application instance.
    """

    @flask_app.route("/health", methods=["GET", "HEAD"])
    @flask_app.route("/healthz", methods=["GET", "HEAD"])
    @flask_app.route("/api/health", methods=["GET", "HEAD"])
    @flask_app.route("/api/healthz", methods=["GET", "HEAD"])
    def health_check():
        """Health check endpoint with comprehensive system status"""
        health_payload = get_health_payload()
        if health_payload.get("status") == "unhealthy":
            return jsonify(health_payload), 500
        return jsonify(health_payload)

    @flask_app.route("/", defaults={"path": ""})
    @flask_app.route("/<path:path>")
    def serve(path):
        static_folder_path = flask_app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, "index.html")
            else:
                return "index.html not found", 404


    @flask_app.route("/api/phase7/status")
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

    @flask_app.route("/api/phase7/approvals/pending")
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

    @flask_app.route("/api/phase7/approvals/history")
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

    @flask_app.route("/api/phase7/beta/candidates")
    def get_beta_candidates():
        """Get Beta program candidates"""
        try:
            from pm_agent import PMAgent

            pm_agent = PMAgent()

            status = pm_agent.get_beta_program_status()
            return jsonify(status)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @flask_app.route("/api/phase7/growth/metrics")
    def get_growth_metrics():
        """Get growth strategy metrics"""
        try:
            from growth_strategist import GrowthStrategist

            growth_strategist = GrowthStrategist()

            report = growth_strategist.get_growth_report()
            return jsonify(report)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @flask_app.route("/api/phase7/ops/metrics")
    def get_ops_metrics():
        """Get operations performance metrics"""
        try:
            from ops_agent import OpsAgent

            ops_agent = OpsAgent()

            report = ops_agent.get_performance_report()
            return jsonify(report)

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @flask_app.route("/api/phase7/monitoring/dashboard")
    def get_monitoring_dashboard():
        """Get monitoring dashboard data"""
        try:
            if not BACKEND_SERVICES_AVAILABLE:
                return jsonify({"error": "Backend services not available"}), 500

            hours = int(request.args.get("hours", 1))
            dashboard_data = monitoring_dashboard.get_dashboard_data(hours=hours)

            return jsonify(dashboard_data)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @flask_app.route("/api/phase7/monitoring/metrics")
    def get_resilience_metrics():
        """Get resilience pattern metrics"""
        try:
            from resilience_patterns import resilience_manager

            persistent_state_manager = PersistentStateManager()
            from saga_orchestrator import saga_orchestrator

            metrics = {
                "resilience": resilience_manager.get_all_metrics(),
                "storage": persistent_state_manager.get_storage_stats(),
                "saga": saga_orchestrator.get_orchestrator_metrics(),
                "timestamp": datetime.datetime.now().isoformat(),
            }

            return jsonify(metrics)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @flask_app.route("/api/phase7/monitoring/alerts")
    def get_monitoring_alerts():
        """Get current monitoring alerts"""
        try:
            if not BACKEND_SERVICES_AVAILABLE:
                return jsonify({"error": "Backend services not available"}), 500

            if monitoring_dashboard.metrics_history:
                latest_metrics = monitoring_dashboard.metrics_history[-1]
                alerts = monitoring_dashboard._generate_alerts(latest_metrics)
                return jsonify({"alerts": alerts, "count": len(alerts)})
            else:
                return jsonify({"alerts": [], "count": 0})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @flask_app.route("/api/phase7/environment/validate", methods=["GET", "POST"])
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


    @flask_app.route("/api/dashboard/layouts", methods=["GET", "POST"])
    def manage_dashboard_layouts():
        """Get or save user dashboard layouts"""
        try:
            persistent_state_manager = PersistentStateManager()

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

    @flask_app.route("/api/dashboard/widgets/available")
    def get_available_widgets():
        """Get list of available dashboard widgets"""
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

    @flask_app.route(
        "/api/dashboard/data", methods=["GET", "POST"], endpoint="get_dashboard_data_legacy"
    )
    def get_dashboard_data_legacy():
        """Get real-time dashboard data (legacy endpoint)"""
        try:
            if not BACKEND_SERVICES_AVAILABLE:
                return jsonify({"error": "Backend services not available"}), 500

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


    @flask_app.route("/api/reports/generate", methods=["POST"])
    def generate_report():
        """Generate custom reports"""
        try:
            if not BACKEND_SERVICES_AVAILABLE:
                return jsonify({"error": "Backend services not available"}), 500

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

    @flask_app.route("/api/reports/templates")
    def get_report_templates():
        """Get available report templates"""
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

    @flask_app.route("/api/reports/history")
    def get_report_history():
        """Get report generation history"""
        try:
            persistent_state_manager = PersistentStateManager()

            history = persistent_state_manager.get_report_history()
            return jsonify(history)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @flask_app.route("/api/dashboard/widgets", methods=["GET"])
    def get_dashboard_widgets():
        """Get available dashboard widgets"""
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

    @flask_app.route("/api/phase7/resilience/metrics", methods=["GET"])
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

    @flask_app.route("/api/settings", methods=["GET", "POST"], endpoint="settings")
    def settings_route():
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


# Create the Flask application using the factory function
# This maintains backward compatibility - app can still be imported from src.main
app = create_app()


if __name__ == "__main__":
    try:
        from src.utils.redis_client import check_redis_security

        redis_security = check_redis_security()

        if redis_security["status"] == "vulnerable":
            logger.critical(f"Redis Security Warning: {redis_security['message']}")
            logger.critical(
                f"CVE-2025-49844 Risk: {redis_security['cve_2025_49844_risk']}"
            )
            for rec in redis_security.get("recommendations", []):
                logger.warning(f"  - {rec}")
        elif redis_security["status"] == "secure":
            logger.info(f"Redis Security Check: {redis_security['message']}")
        else:
            logger.warning(f"Redis Security Check: {redis_security['message']}")
    except Exception as e:
        logger.warning(f"Failed to check Redis security on startup: {e}")

    port = app_settings.port or 5001
    debug = app_settings.flask_env != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
