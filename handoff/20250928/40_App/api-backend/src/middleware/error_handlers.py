"""Error handlers module for Flask application.

This module contains global error handlers extracted from main.py
as part of Phase 1 refactoring (PR1d).

See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import logging
import os

from flask import jsonify

logger = logging.getLogger(__name__)

# Get Sentry DSN from environment
SENTRY_DSN = os.environ.get("SENTRY_DSN")


def handle_exception(e):
    """Global exception handler to capture unhandled errors in Sentry.
    
    This function is exported at module level for backward compatibility
    (can be imported from src.main via re-export).
    """
    if hasattr(e, "code"):
        return jsonify({"error": str(e)}), e.code

    logger.exception("Unhandled exception", extra={"error": str(e)})

    if SENTRY_DSN:
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


def register_error_handlers(app):
    """Register global error handlers on the Flask app.
    
    This function registers all global exception handlers that were
    previously defined in main.py.
    
    Args:
        app: Flask application instance
    """
    app.errorhandler(Exception)(handle_exception)
