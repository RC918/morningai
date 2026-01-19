"""Database configuration and initialization module.

This module contains database setup logic extracted from main.py
as part of Phase 1 refactoring (PR1e).

See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)


def configure_database(app, app_settings, db):
    """Configure SQLAlchemy database settings for the Flask app.

    This function sets up the database URI and engine options based on
    the environment (production, testing, development).

    Args:
        app: Flask application instance
        app_settings: Application settings object (from common.config.settings)
        db: SQLAlchemy database instance
    """
    from common.config.settings import get_settings

    # Create database directory if needed
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
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
            sqlite_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "database", "app.db"
            )
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
            logger.info(f"ℹ️  Database configured: SQLite (path: {sqlite_path})")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
        # Use configurable DB pool settings from settings.py (P1.3)
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": app_settings.db_pool_pre_ping,
            "pool_recycle": app_settings.db_pool_recycle,
            "pool_size": app_settings.db_pool_size,
            "max_overflow": app_settings.db_pool_max,
            "pool_timeout": app_settings.db_pool_timeout,
        }

    db.init_app(app)


def validate_rate_limit_redis(app_settings):
    """Validate Redis connection for rate limiting in production.

    This provides fail-fast behavior: if Redis is unavailable in production,
    the application will refuse to start rather than running without rate limiting protection.

    Can be disabled by setting RATE_LIMIT_FAIL_FAST=false (not recommended).

    Args:
        app_settings: Application settings object (from common.config.settings)

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


def init_test_database(app, db):
    """Initialize test database with SQLite in-memory and create all tables.

    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    """
    with app.app_context():
        from src.models.agent_registry_db import AgentDB, TaskDB  # noqa: F401

        db.create_all()
        logger.info("✅ Test database tables initialized (SQLite in-memory)")


def init_database_with_retry(app, db, max_retries=6, initial_delay=0.5):
    """Initialize database with exponential backoff retry logic.

    This handles transient connection issues during deployment, especially
    with Supabase Session pooler which may briefly refuse connections during
    cold starts or network blips.

    Retry schedule: 0.5s, 1s, 2s, 4s, 8s, 16s (total ~31.5s)

    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
        max_retries: Maximum number of retry attempts (default: 6)
        initial_delay: Initial delay in seconds before first retry (default: 0.5)
    """
    import time

    for attempt in range(max_retries):
        try:
            with app.app_context():
                from src.models.agent_registry_db import AgentDB, TaskDB  # noqa: F401

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


def _register_test_db_safety_net(app, db):
    """Register before_request handler to ensure tables exist in test mode.

    This is a safety net for test mode to ensure agent_registry tables
    exist before each request.

    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    """
    @app.before_request
    def ensure_tables():
        """Safety net: Ensure agent_registry tables exist before each request in test mode"""
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        if "agents" not in existing_tables or "tasks" not in existing_tables:
            from src.models.agent_registry_db import AgentDB, TaskDB  # noqa: F401

            db.create_all()


def initialize_database(app, db, app_settings):
    """Initialize database based on environment (testing, production, development).

    This function handles the conditional database initialization logic
    that was previously in main.py.

    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
        app_settings: Application settings object (from common.config.settings)
    """
    ENVIRONMENT = app_settings.environment or "development"

    if app.config.get("TESTING"):
        init_test_database(app, db)
        _register_test_db_safety_net(app, db)
    elif ENVIRONMENT == "production":
        validate_rate_limit_redis(app_settings)
        init_database_with_retry(app, db)
    else:
        with app.app_context():
            from src.models.agent_registry_db import AgentDB, TaskDB  # noqa: F401

            db.create_all()
