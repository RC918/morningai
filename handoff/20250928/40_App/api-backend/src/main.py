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

from src.routes.billing import bp as billing_bp
from src.routes.tenant import bp as tenant_bp
from src.routes.vectors import bp as vectors_bp
from src.routes.governance import bp as governance_bp, admin_bp as admin_agents_bp
from src.routes.agent_registry import bp as agent_registry_bp
from src.routes.admin import bp as admin_bp
from src.routes.failures import bp as failures_bp
from src.routes.experiments import bp as experiments_bp
from src.routes.ai_policies import bp as ai_policies_bp

from flask import Flask, send_from_directory, jsonify, request, send_file, Response
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.auth_enhanced import auth_enhanced_bp
from src.routes.auth_2fa import auth_2fa_bp
from src.routes.dashboard import dashboard_bp
from src.routes.totp import totp_bp
from src.middleware.auth_middleware import (
    jwt_required,
    admin_required,
    analyst_required,
)
from common.config.settings import get_settings
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}',
)
logger = logging.getLogger(__name__)

SENTRY_DSN = app_settings.sentry_dsn
APP_VERSION = app_settings.app_version or "8.0.0"


def before_send(event, hint):
    """Filter out 400/404 errors to reduce noise"""
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if hasattr(exc_value, "code") and exc_value.code in [400, 404]:
            return None

    if event.get("request", {}).get("status_code") in [400, 404]:
        return None

    return event


# Import _as_bool from utils module (Phase 1 refactoring: PR1a)
# Re-exported at module level for backward compatibility
# Tests should patch via 'src.main._as_bool' (not 'src.utils.helpers._as_bool')
from src.utils.helpers import _as_bool  # noqa: E402


TESTING = _as_bool(os.getenv("TESTING"))
DISABLE_SENTRY_FOR_TESTS = _as_bool(os.getenv("DISABLE_SENTRY_FOR_TESTS"))

# Determine if Sentry should be disabled (either flag can disable it)
disable_sentry = DISABLE_SENTRY_FOR_TESTS or TESTING

# Production environment protection: prevent accidentally disabling Sentry in production
# Default to "development" for consistency with other environment defaults in the codebase
current_env = app_settings.environment or "development"
if disable_sentry and current_env == "production":
    logger.warning(
        "DISABLE_SENTRY_FOR_TESTS or TESTING is set but environment is production; "
        "Sentry will remain enabled to ensure error tracking in production."
    )
    disable_sentry = False

if SENTRY_DSN and SENTRY_DSN.strip() and not disable_sentry:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=current_env,
            release=f"morningai@{APP_VERSION}",
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            before_send=before_send,
        )
        logger.info(
            f"Sentry initialized successfully with release morningai@{APP_VERSION}"
        )
    except Exception as e:
        logger.warning(
            f"Failed to initialize Sentry: {e}. Continuing without Sentry integration."
        )
        SENTRY_DSN = None
elif disable_sentry:
    logger.info(
        "Sentry disabled in testing environment "
        "(DISABLE_SENTRY_FOR_TESTS or TESTING flag is set)."
    )
    SENTRY_DSN = None
else:
    SENTRY_DSN = None

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

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

from src.services.auth_service import validate_security_config

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
        logger.info("✅ Pre-auth token manager initialized successfully")
    except RuntimeError as e:
        logger.error(f"❌ Failed to initialize pre-auth token manager: {e}")
        raise

# NOTE: Module-level get_settings() calls for Flask app initialization
# These calls happen during Flask app setup, which occurs AFTER all imports are complete.
# This is acceptable because:
# 1. Flask app initialization is part of the application startup sequence
# 2. Tests that need to mock settings should import main.py AFTER setting environment variables
# 3. The settings module uses test-aware caching, so tests will get fresh instances
# Import order for tests:
# 1. Set environment variables (os.environ['KEY'] = 'value')
# 2. Import main.py (triggers Flask app initialization with test env vars)
# 3. Run test assertions
# See docs/config/app_settings.md for more details on settings lifecycle and testing.
# SECRET_KEY fallback removed - deadline 2025-11-30 passed
# Use FLASK_SECRET_KEY instead
flask_secret = get_settings().flask_secret_key
if not flask_secret:
    if app_settings.is_production and not app_settings.testing:
        raise RuntimeError("FLASK_SECRET_KEY must be set in production environment.")
    flask_secret = "dev-only-fallback-secret-key"
app.config["SECRET_KEY"] = flask_secret

enable_mock = os.getenv("ENABLE_MOCK_USERS")
if enable_mock is not None:
    app.config["ENABLE_MOCK_USERS"] = _as_bool(enable_mock)

app.config["TESTING"] = _as_bool(os.getenv("TESTING"))
rate_limit_env = os.getenv("RATE_LIMIT_REQUESTS")
if rate_limit_env:
    app.config["RATE_LIMIT_REQUESTS"] = int(rate_limit_env)

cors_origins = (app_settings.cors_origins or "http://localhost:5173,http://localhost:5174").split(",")
cors_origins = [origin.strip() for origin in cors_origins]

# CORS debug logging: disabled by default, force-disabled in production
# Enable with CORS_DEBUG=true for local/staging troubleshooting only
cors_debug_enabled = _as_bool(os.getenv("CORS_DEBUG")) and not app_settings.is_production

if cors_debug_enabled:
    # Sanitized startup log: only counts and environment name, no raw values
    logging.debug(f"[CORS DEBUG] Startup: env={app_settings.environment}, allowlist_count={len(cors_origins)}")


def is_vercel_preview(origin):
    """
    Check if origin is a Vercel preview URL.
    Allows Vercel preview origins in staging and development environments.
    Blocks them in production for security.
    """
    if not origin:
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] is_vercel_preview: origin_present=False")
        return False

    env = (app_settings.environment or "").lower()

    if env == "production":
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] is_vercel_preview: blocked_by_production=True")
        return False

    matches = bool(re.match(r"^https://.*\.vercel\.app$", origin))
    if cors_debug_enabled:
        logging.debug(f"[CORS DEBUG] is_vercel_preview: is_vercel_pattern={matches}")
    return matches


@app.after_request
def add_cors_headers(response):
    """Add CORS headers for allowed origins including Vercel preview URLs.

    This is the single authority source for CORS handling in the application.
    Flask-CORS has been removed to avoid dual-mechanism conflicts.

    Handles:
    - Static origins from CORS_ORIGINS environment variable
    - Dynamic Vercel preview URLs (*.vercel.app) in staging/development
    - OPTIONS preflight requests with 204 status code
    - Access-Control-Expose-Headers for rate limit headers
    """
    origin = request.headers.get("Origin")

    in_allowlist = origin in cors_origins
    is_preview = is_vercel_preview(origin)

    if cors_debug_enabled:
        # Sanitized log: only status flags, no raw values
        logging.debug(
            f"[CORS DEBUG] add_cors_headers: origin_present={bool(origin)}, "
            f"in_allowlist={in_allowlist}, is_preview={is_preview}, "
            f"allowlist_count={len(cors_origins)}"
        )

    if in_allowlist or is_preview:
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] add_cors_headers: headers_added=True")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Request-ID, X-CSRF-Token"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        )
        response.headers["Access-Control-Expose-Headers"] = (
            "Content-Type, Authorization, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset"
        )
        # Merge Vary header instead of overwriting
        existing_vary = response.headers.get("Vary", "")
        if existing_vary:
            if "Origin" not in existing_vary:
                response.headers["Vary"] = f"{existing_vary}, Origin"
        else:
            response.headers["Vary"] = "Origin"

        # Handle OPTIONS preflight requests with 204 No Content
        if request.method == "OPTIONS":
            response.status_code = 204
            response.set_data(b"")  # Clear response body for 204
            if cors_debug_enabled:
                logging.debug("[CORS DEBUG] add_cors_headers: preflight_response=204")
    elif request.method == "OPTIONS" and not origin:
        # Fallback for OPTIONS requests without Origin header (non-browser clients, testing)
        # This maintains backward compatibility with Flask-CORS behavior.
        # Note: Real browser preflight requests always include Origin header.
        # Using "*" without credentials is spec-compliant for this edge case.
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] add_cors_headers: fallback_options_no_origin=True")
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Request-ID, X-CSRF-Token"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        )
        response.status_code = 204
        response.set_data(b"")  # Clear response body for 204
    else:
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] add_cors_headers: headers_added=False")

    return response


if SECURITY_AVAILABLE:
    # MASTER_KEY fallback removed - deadline 2025-11-30 passed
    # Use ENCRYPTION_MASTER_KEY instead
    encryption_master_key = app_settings.encryption_master_key
    if not encryption_master_key:
        if app_settings.is_production and not app_settings.testing:
            raise RuntimeError("ENCRYPTION_MASTER_KEY must be set in production environment.")
        encryption_master_key = "dev-only-fallback-master-key"

    security_config = {
        "master_key": encryption_master_key,
        "secret_key": app.config["SECRET_KEY"],
        "audit_log_file": "api_audit.log",
    }
    security_manager = SecurityManager(security_config)
    app.security_manager = security_manager

app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(auth_enhanced_bp, url_prefix="/api/auth/v2")
app.register_blueprint(auth_2fa_bp)
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(totp_bp, url_prefix="/api/auth/v2/totp")
app.register_blueprint(billing_bp)

if os.getenv('ENABLE_ORCHESTRATOR', 'true').lower() in ('true', '1', 'yes', 'on'):
    from src.routes.agent import bp as agent_bp
    from src.routes.agent_evaluation import bp as agent_evaluation_bp
    from src.routes.faq import bp as faq_bp
    app.register_blueprint(agent_bp)
    app.register_blueprint(agent_evaluation_bp)
    app.register_blueprint(faq_bp)
    logger.info("✅ Orchestrator/agent routes enabled")
else:
    logger.info("⚠️ Orchestrator/agent routes disabled (ENABLE_ORCHESTRATOR=false)")

app.register_blueprint(agent_registry_bp)
app.register_blueprint(tenant_bp)
app.register_blueprint(vectors_bp)
app.register_blueprint(governance_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(admin_agents_bp)
app.register_blueprint(failures_bp)
app.register_blueprint(experiments_bp)
app.register_blueprint(ai_policies_bp)

try:
    from src.routes.action_requests import bp as action_requests_bp
    app.register_blueprint(action_requests_bp)
    logger.info("HITL action requests routes enabled")
except ImportError as e:
    logger.warning("HITL action requests routes not available: %s", e)

# Sessions API for agent session monitoring (Owner Console)
try:
    from src.routes.sessions import bp as sessions_bp
    app.register_blueprint(sessions_bp)
    logger.info("Sessions API routes enabled")
except ImportError as e:
    logger.warning("Sessions API routes not available: %s", e)

# Webhook routes for external service integration (GitHub, Jira, Slack)
try:
    from src.routes.webhooks import bp as webhooks_bp
    app.register_blueprint(webhooks_bp)
    logger.info("Webhook routes enabled")
except ImportError as e:
    logger.warning("Webhook routes not available: %s", e)

# DeepWiki API for knowledge base queries (Issue #2158)
try:
    from src.routes.deepwiki import bp as deepwiki_bp
    app.register_blueprint(deepwiki_bp)
    logger.info("DeepWiki API routes enabled")
except ImportError as e:
    logger.warning("DeepWiki API routes not available: %s", e)

# Metrics API for system observability (Epic #2311 Phase 1)
try:
    from src.routes.metrics import metrics_bp
    app.register_blueprint(metrics_bp, url_prefix="/api")
    logger.info("Metrics API routes enabled")
except ImportError as e:
    logger.warning("Metrics API routes not available: %s", e)

from src.routes.dashboard import get_dashboard_data as monitoring_dashboard_handler

app.add_url_rule(
    "/api/phase7/monitoring/dashboard",
    view_func=monitoring_dashboard_handler,
    methods=["GET"],
    endpoint="phase7_monitoring_dashboard",
)

if BACKEND_SERVICES_AVAILABLE:
    try:
        app.register_blueprint(mock_api)
    except NameError:
        pass


@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler to capture unhandled errors in Sentry"""
    if hasattr(e, "code"):
        return jsonify({"error": str(e)}), e.code

    logger.exception("Unhandled exception", extra={"error": str(e)})

    if SENTRY_DSN:
        sentry_sdk.capture_exception(e)

    return (
        jsonify(
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred",
                }
            }
        ),
        500,
    )


def get_health_payload():
    """Generate health check payload with JSON serializable values"""
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


@app.route("/health", methods=["GET", "HEAD"])
@app.route("/healthz", methods=["GET", "HEAD"])
@app.route("/api/health", methods=["GET", "HEAD"])
@app.route("/api/healthz", methods=["GET", "HEAD"])
def health_check():
    """Health check endpoint with comprehensive system status

    Supports both GET and HEAD methods for compatibility with various
    health check systems (e.g., Render, Kubernetes, load balancers).
    """
    health_payload = get_health_payload()
    if health_payload.get("status") == "unhealthy":
        return jsonify(health_payload), 500
    return jsonify(health_payload)


db_dir = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(db_dir, exist_ok=True)

DATABASE_URL = get_settings().database_url
ENVIRONMENT = app_settings.environment or "development"

if ENVIRONMENT == "production" and not app_settings.testing:
    if not DATABASE_URL:
        logger.critical(
            "❌ FATAL: Production environment requires DATABASE_URL to be set"
        )
        raise RuntimeError("Production must have DATABASE_URL configured")

    if DATABASE_URL.startswith("sqlite"):
        logger.critical(
            "❌ FATAL: Production environment cannot use SQLite (ephemeral storage)"
        )
        raise RuntimeError("Production must use PostgreSQL, not SQLite")

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

    try:
        from urllib.parse import urlparse

        parsed = urlparse(DATABASE_URL)
        db_driver = parsed.scheme
        db_host = parsed.hostname or "unknown"
        logger.info(f"✅ Database configured: {db_driver} (host: {db_host})")
    except Exception as e:
        logger.warning(f"⚠️  Could not parse DATABASE_URL for logging: {e}")
        logger.info("✅ Database configured: PostgreSQL")
else:
    if DATABASE_URL and not DATABASE_URL.startswith("sqlite"):
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
        try:
            from urllib.parse import urlparse

            parsed = urlparse(DATABASE_URL)
            db_driver = parsed.scheme
            db_host = parsed.hostname or "unknown"
            logger.info(f"ℹ️  Database configured: {db_driver} (host: {db_host})")
        except Exception:
            logger.info("ℹ️  Database configured: PostgreSQL")
    else:
        sqlite_path = os.path.join(os.path.dirname(__file__), "database", "app.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        logger.info(f"ℹ️  Database configured: SQLite (path: {sqlite_path})")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

import sys

if "pytest" in sys.modules or app_settings.testing:
    from sqlalchemy.pool import StaticPool

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    logger.info("ℹ️  Test mode detected: Using SQLite in-memory with StaticPool")
else:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 10,
    }

db.init_app(app)


def validate_rate_limit_redis():
    """
    Validate Redis connection for rate limiting in production.

    This provides fail-fast behavior: if Redis is unavailable in production,
    the application will refuse to start rather than running without rate limiting protection.

    Can be disabled by setting RATE_LIMIT_FAIL_FAST=false (not recommended).

    Raises:
        RuntimeError: If Redis is unavailable in production environment
    """
    if not app_settings.rate_limit_fail_fast:
        logger.info("ℹ️  Rate limit fail-fast disabled via RATE_LIMIT_FAIL_FAST=false")
        return

    try:
        from src.utils.redis_client import get_redis_client

        redis_client = get_redis_client()
        redis_client.ping()
        logger.info("✅ Rate limiting Redis connection validated at startup")
    except Exception as e:
        logger.critical(f"❌ FATAL: Rate limiting Redis unavailable in production: {e}")
        logger.critical(
            "   This is a security issue - production requires rate limiting to prevent DoS attacks"
        )
        logger.critical(
            "   Solution: Ensure REDIS_URL or UPSTASH_REDIS_REST_URL is configured"
        )
        logger.critical(
            "   Emergency override (not recommended): Set RATE_LIMIT_FAIL_FAST=false"
        )
        raise RuntimeError("Production environment requires Redis for rate limiting")


def init_test_database():
    """Initialize test database with SQLite in-memory and create all tables"""
    with app.app_context():
        from src.models.agent_registry_db import AgentDB, TaskDB

        db.create_all()
        logger.info("✅ Test database tables initialized (SQLite in-memory)")


def init_database_with_retry(max_retries=6, initial_delay=0.5):
    """
    Initialize database with exponential backoff retry logic.

    This handles transient connection issues during deployment, especially
    with Supabase Session pooler which may briefly refuse connections during
    cold starts or network blips.

    Retry schedule: 0.5s, 1s, 2s, 4s, 8s, 16s (total ~31.5s)
    """
    import time

    for attempt in range(max_retries):
        try:
            with app.app_context():
                from src.models.agent_registry_db import AgentDB, TaskDB

                db.create_all()
            logger.info("✅ Database tables initialized successfully")
            return
        except Exception as e:
            delay = initial_delay * (2**attempt)
            is_last_attempt = attempt == max_retries - 1

            if is_last_attempt:
                logger.critical(
                    f"❌ FATAL: Failed to initialize database after {max_retries} attempts: {e}"
                )
                raise
            else:
                logger.warning(
                    f"⚠️  Database initialization attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                logger.info(f"🔄 Retrying in {delay}s...")
                time.sleep(delay)


if app.config.get("TESTING"):
    init_test_database()

    @app.before_request
    def ensure_tables():
        """Safety net: Ensure agent_registry tables exist before each request in test mode"""
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        if "agents" not in existing_tables or "tasks" not in existing_tables:
            from src.models.agent_registry_db import AgentDB, TaskDB

            db.create_all()

elif ENVIRONMENT == "production":
    validate_rate_limit_redis()
    init_database_with_retry()
else:
    with app.app_context():
        from src.models.agent_registry_db import AgentDB, TaskDB

        db.create_all()


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
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


@app.route("/api/phase7/status")
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


@app.route("/api/phase7/approvals/pending")
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


@app.route("/api/phase7/approvals/history")
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


@app.route("/api/phase7/beta/candidates")
def get_beta_candidates():
    """Get Beta program candidates"""
    try:
        from pm_agent import PMAgent

        pm_agent = PMAgent()

        status = pm_agent.get_beta_program_status()
        return jsonify(status)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/phase7/growth/metrics")
def get_growth_metrics():
    """Get growth strategy metrics"""
    try:
        from growth_strategist import GrowthStrategist

        growth_strategist = GrowthStrategist()

        report = growth_strategist.get_growth_report()
        return jsonify(report)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/phase7/ops/metrics")
def get_ops_metrics():
    """Get operations performance metrics"""
    try:
        from ops_agent import OpsAgent

        ops_agent = OpsAgent()

        report = ops_agent.get_performance_report()
        return jsonify(report)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/phase7/monitoring/dashboard")
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


@app.route("/api/phase7/monitoring/metrics")
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


@app.route("/api/phase7/monitoring/alerts")
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


@app.route("/api/phase7/environment/validate", methods=["GET", "POST"])
def validate_environment():
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


@app.route("/api/dashboard/layouts", methods=["GET", "POST"])
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


@app.route("/api/dashboard/widgets/available")
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


@app.route(
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


@app.route("/api/reports/generate", methods=["POST"])
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


@app.route("/api/reports/templates")
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


@app.route("/api/reports/history")
def get_report_history():
    """Get report generation history"""
    try:
        persistent_state_manager = PersistentStateManager()

        history = persistent_state_manager.get_report_history()
        return jsonify(history)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    print("✅ Phase 4-6 APIs imported successfully")
except ImportError as e:
    print(f"⚠️ Phase 4-6 APIs not available: {e}")
    PHASE_456_AVAILABLE = False


@app.route("/api/meta-agent/ooda-cycle", methods=["POST"])
def meta_agent_ooda_cycle():
    """启动 OODA 循环"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_meta_agent_ooda_cycle())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/langgraph/workflows", methods=["POST"])
def create_langgraph_workflow():
    """创建 LangGraph 工作流"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_create_langgraph_workflow(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/langgraph/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    """执行工作流"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_execute_workflow(workflow_id, request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/governance/status", methods=["GET"])
def governance_status():
    """获取治理状态"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_governance_status())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/governance/policies", methods=["POST"])
def create_governance_policy():
    """创建治理政策"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_create_governance_policy(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/quicksight/dashboards", methods=["POST"])
def create_quicksight_dashboard():
    """创建 QuickSight 仪表板"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_create_quicksight_dashboard(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/quicksight/dashboards/<dashboard_id>/insights", methods=["GET"])
def get_dashboard_insights(dashboard_id):
    """获取仪表板洞察"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_dashboard_insights(dashboard_id))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/automated", methods=["POST"])
def generate_automated_report():
    """生成自动化报告"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_generate_automated_report(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/growth/referral-programs", methods=["POST"])
def create_referral_program():
    """创建推荐计划"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_create_referral_program(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/growth/referral-programs/<program_id>/analytics", methods=["GET"])
def get_referral_analytics(program_id):
    """获取推荐分析"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_referral_analytics(program_id))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/growth/content/generate", methods=["POST"])
def generate_marketing_content():
    """生成营销内容"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_generate_marketing_content(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/business-intelligence/summary", methods=["GET"])
def get_business_intelligence():
    """获取商业智能摘要"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_business_intelligence())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/security/access/evaluate", methods=["GET", "POST"])
@app.route("/api/security/access-requests/evaluate", methods=["GET", "POST"])
@admin_required
def evaluate_access_request():
    """评估访问请求"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            api_evaluate_access_request(request.json or {})
        )
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/security/events/review", methods=["POST"])
@analyst_required
def review_security_event():
    """审查安全事件"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_review_security_event(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/security/hitl/submit", methods=["POST"])
@analyst_required
def submit_hitl_review():
    """提交人工审查"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        data = request.json or {}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_submit_hitl_review(data))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/security/hitl/pending", methods=["GET"])
@analyst_required
def get_pending_reviews():
    """获取待审查项目"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_pending_reviews())
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/security/audit", methods=["GET", "POST"])
@app.route("/api/security/audit/perform", methods=["GET", "POST"])
@admin_required
def perform_security_audit():
    """执行安全审计"""
    if not PHASE_456_AVAILABLE:
        return jsonify({"error": "Phase 4-6 APIs not available"}), 503
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_perform_security_audit(request.json or {}))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/security/reviews/pending", methods=["GET"])
@analyst_required
def get_pending_security_reviews():
    """Get pending security reviews"""
    try:
        if not PHASE_456_AVAILABLE:
            return jsonify({"error": "Phase 4-6 APIs not available"}), 503

        from phase6_security_governance_api import api_get_pending_reviews

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(api_get_pending_reviews())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard/widgets", methods=["GET"])
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


@app.route("/api/phase7/resilience/metrics", methods=["GET"])
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


@app.route("/api/settings", methods=["GET", "POST"], endpoint="settings")
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


if __name__ == "__main__":
    try:
        from src.utils.redis_client import check_redis_security

        redis_security = check_redis_security()

        if redis_security["status"] == "vulnerable":
            logger.critical(f"⚠️ Redis Security Warning: {redis_security['message']}")
            logger.critical(
                f"CVE-2025-49844 Risk: {redis_security['cve_2025_49844_risk']}"
            )
            for rec in redis_security.get("recommendations", []):
                logger.warning(f"  - {rec}")
        elif redis_security["status"] == "secure":
            logger.info(f"✅ Redis Security Check: {redis_security['message']}")
        else:
            logger.warning(f"⚠️ Redis Security Check: {redis_security['message']}")
    except Exception as e:
        logger.warning(f"Failed to check Redis security on startup: {e}")

    port = app_settings.port or 5001
    debug = app_settings.flask_env != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
