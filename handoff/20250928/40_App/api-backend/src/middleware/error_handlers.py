"""Error handlers module for Flask application.

This module contains global error handlers extracted from main.py
as part of Phase 1 refactoring (PR1d).

See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import logging

from flask import current_app, jsonify

logger = logging.getLogger(__name__)


def handle_exception(e):
    """Global exception handler to capture unhandled errors in Sentry.
    
    This function is exported at module level for backward compatibility
    (can be imported from src.main via re-export).
    
    The Sentry DSN is retrieved from app.extensions["morningai"]["sentry_dsn"],
    which is set by register_error_handlers(). This ensures the DSN respects
    the TESTING/DISABLE_SENTRY_FOR_TESTS logic in main.py.
    """
    if hasattr(e, "code"):
        return jsonify({"error": str(e)}), e.code

    logger.exception("Unhandled exception", extra={"error": str(e)})

    # Get Sentry DSN from app.extensions (set by register_error_handlers)
    # This respects TESTING/DISABLE_SENTRY_FOR_TESTS logic in main.py
    try:
        sentry_dsn = current_app.extensions.get("morningai", {}).get("sentry_dsn")
    except RuntimeError:
        # Working outside of application context - don't send to Sentry
        sentry_dsn = None

    if sentry_dsn:
        import sentry_sdk
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


def register_error_handlers(app, sentry_dsn=None):
    """Register global error handlers on the Flask app.
    
    This function registers all global exception handlers that were
    previously defined in main.py.
    
    Args:
        app: Flask application instance
        sentry_dsn: Sentry DSN string (already processed by main.py's
                    TESTING/DISABLE_SENTRY_FOR_TESTS logic). Pass None
                    to disable Sentry error capture.
    """
    # Store sentry_dsn in app.extensions for per-app storage
    # This allows handle_exception to access it via current_app
    if "morningai" not in app.extensions:
        app.extensions["morningai"] = {}
    app.extensions["morningai"]["sentry_dsn"] = sentry_dsn
    
    app.errorhandler(Exception)(handle_exception)
