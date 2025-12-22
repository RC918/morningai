import os
import sys
import datetime
import logging
from common.config.settings import settings as app_settings, get_settings

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
if app_dir:
    # Resolve relative paths to absolute paths using repo_root
    app_dir_path = Path(app_dir)
    if not app_dir_path.is_absolute():
        app_dir_path = repo_root / app_dir
    app_dir_path = app_dir_path.resolve()
    # If path points to orchestrator directory, use its parent (40_App) for imports
    if app_dir_path.name == 'orchestrator':
        app_dir_path = app_dir_path.parent
    app_dir = str(app_dir_path)
else:
    # Fallback: compute 40_App directory from this file's location
    # Path: main.py -> src/ -> api-backend/ -> 40_App/
    app_dir = str(Path(__file__).resolve().parent.parent.parent)

if os.path.exists(app_dir) and app_dir not in sys.path:
    sys.path.insert(0, app_dir)
    logging.info(f"Added app directory to sys.path: {app_dir}")
elif not os.path.exists(app_dir):
    logging.warning(
        f"App directory does not exist: {app_dir}. Orchestrator features may not work."
    )

from flask import Flask
from src.models.user import db
# Note: jwt_required, admin_required, analyst_required moved to phase456 blueprint (PR1.6a)
# Note: get_settings is imported at line 5 along with settings as app_settings
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
cors_debug_enabled = app_settings.cors_debug and not app_settings.is_production


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

    settings_instance = get_settings()
    if 'enable_mock_users' in settings_instance.model_fields_set:
        flask_app.config["ENABLE_MOCK_USERS"] = app_settings.enable_mock_users

    flask_app.config["TESTING"] = app_settings.testing
    
    if 'rate_limit_requests' in settings_instance.model_fields_set:
        flask_app.config["RATE_LIMIT_REQUESTS"] = app_settings.rate_limit_requests

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

    # Database configuration and initialization
    configure_database(flask_app, app_settings, db)
    initialize_database(flask_app, db, app_settings)

    return flask_app


# Phase 1.6 Route Modularization Complete:
# All inline routes have been moved to dedicated blueprint modules:
# - PR1.6a: Phase 4-6 routes → src/routes/phase456.py
# - PR1.6b: Phase 7 routes → src/routes/phase7.py
# - PR1.6c: Dashboard/Reports/Settings routes → src/routes/dashboard_reports.py
# - PR1.6d: Health/Static routes → src/routes/health_static.py


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
