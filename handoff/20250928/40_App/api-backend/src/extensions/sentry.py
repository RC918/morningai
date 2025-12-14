"""Sentry SDK initialization module.

This module provides Sentry error tracking initialization for the Flask application.
Extracted from main.py as part of Phase 1 refactoring (PR1f).

Key functions:
- before_send: Filter out 400/404 errors to reduce noise in Sentry
- init_sentry: Initialize Sentry SDK with proper configuration

IMPORTANT: before_send is NOT re-exported from src.main because Sentry SDK
holds a direct reference to the function passed to sentry_sdk.init().
Tests must patch 'src.extensions.sentry.before_send' (not 'src.main.before_send').

See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md - Patch Canonical Target
"""

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

logger = logging.getLogger(__name__)


def before_send(event, hint):
    """Filter out 400/404 errors to reduce noise in Sentry.
    
    This callback is passed to sentry_sdk.init() and is called before
    each event is sent to Sentry. It filters out common client errors
    (400 Bad Request, 404 Not Found) to reduce noise and focus on
    actual server errors.
    
    Args:
        event: The Sentry event dictionary
        hint: Additional context about the event (may contain exc_info)
    
    Returns:
        The event dict to send to Sentry, or None to drop the event
    
    Example:
        >>> before_send({'request': {'status_code': 404}}, {})
        None  # Event is dropped
        >>> before_send({'request': {'status_code': 500}}, {})
        {'request': {'status_code': 500}}  # Event is sent
    """
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if hasattr(exc_value, "code") and exc_value.code in [400, 404]:
            return None

    if event.get("request", {}).get("status_code") in [400, 404]:
        return None

    return event


def init_sentry(app_settings, _as_bool_func):
    """Initialize Sentry SDK with proper configuration.
    
    This function handles all Sentry initialization logic including:
    - Checking for SENTRY_DSN configuration
    - Respecting TESTING and DISABLE_SENTRY_FOR_TESTS flags
    - Production environment protection (never disable in production)
    - Proper error handling for initialization failures
    
    Args:
        app_settings: The application settings object with sentry_dsn,
                     environment, app_version, and testing attributes
        _as_bool_func: The _as_bool helper function for parsing env vars
    
    Returns:
        str or None: The SENTRY_DSN if Sentry was initialized, None otherwise
    
    Example:
        >>> from common.config.settings import settings as app_settings
        >>> from src.utils.helpers import _as_bool
        >>> sentry_dsn = init_sentry(app_settings, _as_bool)
    """
    sentry_dsn = app_settings.sentry_dsn
    app_version = app_settings.app_version or "8.0.0"
    
    testing = _as_bool_func(os.getenv("TESTING"))
    disable_sentry_for_tests = _as_bool_func(os.getenv("DISABLE_SENTRY_FOR_TESTS"))
    
    # Determine if Sentry should be disabled (either flag can disable it)
    disable_sentry = disable_sentry_for_tests or testing
    
    # Production environment protection: prevent accidentally disabling Sentry in production
    # Default to "development" for consistency with other environment defaults in the codebase
    current_env = app_settings.environment or "development"
    if disable_sentry and current_env == "production":
        logger.warning(
            "DISABLE_SENTRY_FOR_TESTS or TESTING is set but environment is production; "
            "Sentry will remain enabled to ensure error tracking in production."
        )
        disable_sentry = False
    
    if sentry_dsn and sentry_dsn.strip() and not disable_sentry:
        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=current_env,
                release=f"morningai@{app_version}",
                integrations=[FlaskIntegration()],
                traces_sample_rate=1.0,
                before_send=before_send,
            )
            logger.info(
                f"Sentry initialized successfully with release morningai@{app_version}"
            )
            return sentry_dsn
        except Exception as e:
            logger.warning(
                f"Failed to initialize Sentry: {e}. Continuing without Sentry integration."
            )
            return None
    elif disable_sentry:
        logger.info(
            "Sentry disabled in testing environment "
            "(DISABLE_SENTRY_FOR_TESTS or TESTING flag is set)."
        )
        return None
    else:
        return None
