"""Health check and static file serving routes.

Phase 1.6d: Extract health check and static serve routes from main.py
to a dedicated blueprint module.

Routes:
- /health (GET, HEAD) - Health check endpoint
- /healthz (GET, HEAD) - Kubernetes-style health check
- /api/health (GET, HEAD) - API health check
- /api/healthz (GET, HEAD) - API Kubernetes-style health check
- / (GET) - Static file serving (SPA fallback)
- /<path:path> (GET) - Static file serving
"""
import os
import logging
from flask import Blueprint, jsonify, send_from_directory, current_app
from werkzeug.utils import safe_join

logger = logging.getLogger(__name__)

bp = Blueprint("health_static", __name__)


def init_health_static_routes():
    """Initialize Health/Static routes (logging only).

    This function is called from routes/__init__.py for logging purposes.
    No configuration is needed as routes use runtime imports.
    """
    logger.info("Health/Static routes initialized")


def _get_health_payload():
    """Get health payload from src.main at runtime.

    This function imports get_health_payload from src.main at runtime
    to avoid circular imports and support test patching.

    Returns:
        dict: Health check payload
    """
    import src.main
    return src.main.get_health_payload()


# Health check routes
# Multiple route decorators for the same endpoint to support various health check patterns
@bp.route("/health", methods=["GET", "HEAD"])
@bp.route("/healthz", methods=["GET", "HEAD"])
@bp.route("/api/health", methods=["GET", "HEAD"])
@bp.route("/api/healthz", methods=["GET", "HEAD"])
def health_check():
    """Health check endpoint with comprehensive system status.

    Returns:
        tuple: JSON response with health payload and appropriate status code.
               Returns 500 if status is "unhealthy", 200 otherwise.
    """
    health_payload = _get_health_payload()
    if health_payload.get("status") == "unhealthy":
        return jsonify(health_payload), 500
    return jsonify(health_payload)


# Static file serving routes
# These routes serve the SPA frontend and static assets
@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve(path):
    """Serve static files and SPA fallback.

    This route serves static files from the Flask app's static folder.
    For paths that don't match a file, it falls back to index.html
    to support SPA routing.

    Security: Uses werkzeug.utils.safe_join to prevent path traversal attacks.
    The safe_join function returns None if the path would escape the base directory,
    preventing information disclosure via os.path.exists checks.

    Args:
        path: The requested path

    Returns:
        Response: The static file or index.html fallback
    """
    static_folder_path = current_app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Use safe_join to prevent path traversal attacks (e.g., ../../etc/passwd)
    # safe_join returns None if the path would escape the base directory
    if path != "":
        safe_path = safe_join(static_folder_path, path)
        if safe_path is not None and os.path.isfile(safe_path):
            return send_from_directory(static_folder_path, path)

    # Fallback to index.html for SPA routing
    index_path = safe_join(static_folder_path, "index.html")
    if index_path is not None and os.path.exists(index_path):
        return send_from_directory(static_folder_path, "index.html")
    else:
        return "index.html not found", 404
