"""Routes package for MorningAI API backend.

This module provides the register_blueprints function for Flask app initialization.
Phase 1 refactoring: PR1c - Extract blueprint registration from main.py.
Phase 1.6 refactoring: PR1.6a - Add Phase 4-6 blueprint registration.
"""
import os
import logging

logger = logging.getLogger(__name__)


def register_blueprints(
    app,
    backend_services_available=False,
    phase_456_available=False,
    phase_456_api_funcs=None,
):
    """Register all blueprints to the Flask app.

    IMPORTANT: Uses lazy imports inside the function to avoid circular dependencies
    and import-time side effects. All blueprint imports MUST be inside this function,
    not at module level.

    Args:
        app: Flask application instance
        backend_services_available: Whether backend services (mock_api, etc.) are available
        phase_456_available: Whether Phase 4-6 APIs are available (PR1.6a)
        phase_456_api_funcs: Dictionary of Phase 4-6 API functions (PR1.6a)

    Note:
        - Registration order is preserved from original main.py for consistency
        - Conditional blueprints (orchestrator, optional modules) use same logic as before
        - Tests should NOT patch this function; use route-map guard for verification
    """
    # Core blueprints - lazy imports to avoid circular dependencies
    from src.routes.billing import bp as billing_bp
    from src.routes.tenant import bp as tenant_bp
    from src.routes.vectors import bp as vectors_bp
    from src.routes.governance import bp as governance_bp, admin_bp as admin_agents_bp
    from src.routes.agent_registry import bp as agent_registry_bp
    from src.routes.admin import bp as admin_bp
    from src.routes.failures import bp as failures_bp
    from src.routes.experiments import bp as experiments_bp
    from src.routes.ai_policies import bp as ai_policies_bp
    from src.routes.user import user_bp
    from src.routes.auth import auth_bp
    from src.routes.auth_enhanced import auth_enhanced_bp
    from src.routes.auth_2fa import auth_2fa_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.totp import totp_bp

    # Register core blueprints (order preserved from main.py)
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(auth_enhanced_bp, url_prefix="/api/auth/v2")
    app.register_blueprint(auth_2fa_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(totp_bp, url_prefix="/api/auth/v2/totp")
    app.register_blueprint(billing_bp)

    # Conditional orchestrator blueprints
    if os.getenv('ENABLE_ORCHESTRATOR', 'true').lower() in ('true', '1', 'yes', 'on'):
        from src.routes.agent import bp as agent_bp
        from src.routes.agent_evaluation import bp as agent_evaluation_bp
        from src.routes.faq import bp as faq_bp
        app.register_blueprint(agent_bp)
        app.register_blueprint(agent_evaluation_bp)
        app.register_blueprint(faq_bp)
        logger.info("\u2705 Orchestrator/agent routes enabled")
    else:
        logger.info("\u26a0\ufe0f Orchestrator/agent routes disabled (ENABLE_ORCHESTRATOR=false)")

    # More core blueprints
    app.register_blueprint(agent_registry_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(vectors_bp)
    app.register_blueprint(governance_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_agents_bp)
    app.register_blueprint(failures_bp)
    app.register_blueprint(experiments_bp)
    app.register_blueprint(ai_policies_bp)

    # Optional blueprints with try/except for graceful degradation
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

    # Phase 7 monitoring dashboard URL rule
    from src.routes.dashboard import get_dashboard_data as monitoring_dashboard_handler
    app.add_url_rule(
        "/api/phase7/monitoring/dashboard",
        view_func=monitoring_dashboard_handler,
        methods=["GET"],
        endpoint="phase7_monitoring_dashboard",
    )

    # Mock API for backend services (conditional)
    # Only import mock_api - other services are already imported in main.py
    # when BACKEND_SERVICES_AVAILABLE is True
    if backend_services_available:
        try:
            from src.routes.mock_api import mock_api
            app.register_blueprint(mock_api)
        except (ImportError, NameError):
            pass

    # Phase 4-6 API routes (PR1.6a)
    # Uses lazy import and runtime gating to avoid import-time crashes
    # when phase4/5/6 packages are not available in certain environments
    from src.routes.phase456 import bp as phase456_bp, init_phase456_routes
    init_phase456_routes(phase_456_available, phase_456_api_funcs or {})
    app.register_blueprint(phase456_bp)
    logger.info(f"Phase 4-6 routes registered: available={phase_456_available}")
