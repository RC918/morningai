"""CORS middleware for Flask application.

This module provides CORS (Cross-Origin Resource Sharing) handling for the Flask app.
It is the single authority source for CORS in the application (Flask-CORS has been removed).

Note: These functions are re-exported from src.main for backward compatibility.
Tests should patch via 'src.main.is_vercel_preview' and 'src.main.add_cors_headers'
(not 'src.middleware.cors.*').
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md - Patch Canonical Target
"""

import re
import logging
from flask import request


def is_vercel_preview(origin, environment, cors_debug_enabled=False):
    """Check if origin is a Vercel preview URL.

    Allows Vercel preview origins in staging and development environments.
    Blocks them in production for security.

    Args:
        origin: The Origin header value from the request.
        environment: The current environment (e.g., 'production', 'staging', 'development').
        cors_debug_enabled: Whether to enable debug logging.

    Returns:
        bool: True if the origin is a valid Vercel preview URL in non-production env.
    """
    if not origin:
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] is_vercel_preview: origin_present=False")
        return False

    env = (environment or "").lower()

    if env == "production":
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] is_vercel_preview: blocked_by_production=True")
        return False

    matches = bool(re.match(r"^https://.*\.vercel\.app$", origin))
    if cors_debug_enabled:
        logging.debug(f"[CORS DEBUG] is_vercel_preview: is_vercel_pattern={matches}")
    return matches


def add_cors_headers(response, cors_origins, environment, cors_debug_enabled=False):
    """Add CORS headers for allowed origins including Vercel preview URLs.

    This is the single authority source for CORS handling in the application.
    Flask-CORS has been removed to avoid dual-mechanism conflicts.

    Handles:
    - Static origins from CORS_ORIGINS environment variable
    - Dynamic Vercel preview URLs (*.vercel.app) in staging/development
    - OPTIONS preflight requests with 204 status code
    - Access-Control-Expose-Headers for rate limit headers

    Args:
        response: The Flask response object.
        cors_origins: List of allowed origin strings.
        environment: The current environment string.
        cors_debug_enabled: Whether to enable debug logging.

    Returns:
        The modified response object with CORS headers.
    """
    origin = request.headers.get("Origin")

    in_allowlist = origin in cors_origins
    is_preview = is_vercel_preview(origin, environment, cors_debug_enabled)

    if cors_debug_enabled:
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
        existing_vary = response.headers.get("Vary", "")
        if existing_vary:
            if "Origin" not in existing_vary:
                response.headers["Vary"] = f"{existing_vary}, Origin"
        else:
            response.headers["Vary"] = "Origin"

        if request.method == "OPTIONS":
            response.status_code = 204
            response.set_data(b"")
            if cors_debug_enabled:
                logging.debug("[CORS DEBUG] add_cors_headers: preflight_response=204")
    elif request.method == "OPTIONS" and not origin:
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
        response.set_data(b"")
    else:
        if cors_debug_enabled:
            logging.debug("[CORS DEBUG] add_cors_headers: headers_added=False")

    return response


def setup_cors(app, cors_origins, environment, cors_debug_enabled=False):
    """Set up CORS handling for the Flask application.

    This function registers an after_request handler that adds CORS headers
    to all responses. It should be called once during app initialization.

    Args:
        app: The Flask application instance.
        cors_origins: List of allowed origin strings.
        environment: The current environment string (e.g., 'production', 'staging').
        cors_debug_enabled: Whether to enable debug logging.

    Example:
        >>> from src.middleware.cors import setup_cors
        >>> setup_cors(app, ['http://localhost:5173'], 'development', False)
    """
    if cors_debug_enabled:
        logging.debug(
            f"[CORS DEBUG] Startup: env={environment}, allowlist_count={len(cors_origins)}"
        )

    @app.after_request
    def cors_after_request(response):
        return add_cors_headers(response, cors_origins, environment, cors_debug_enabled)

    return cors_after_request
