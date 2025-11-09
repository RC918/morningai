"""
Sentry Integration Service
Issue #768 - Monitoring Foundation
Feature Flag: MVP_MONITORING_FOUNDATION

Provides comprehensive Sentry integration with custom tags, error filtering,
and performance monitoring for the MorningAI platform.
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
from common.config.settings import settings

logger = logging.getLogger(__name__)

SENTRY_DSN = settings.sentry_dsn
SENTRY_ENVIRONMENT = settings.sentry_environment or "production"
APP_VERSION = settings.app_version or "8.0.0"

sentry_sdk = None
if SENTRY_DSN and SENTRY_DSN.strip():
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        logging_integration = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            release=f"morningai@{APP_VERSION}",
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% of transactions
            integrations=[
                FlaskIntegration(),
                RedisIntegration(),
                logging_integration
            ],
            before_send=scrub_sensitive_data,
            ignore_errors=[
                KeyboardInterrupt,
                SystemExit,
                BrokenPipeError
            ]
        )
        
        logger.info(f"Sentry initialized successfully (environment={SENTRY_ENVIRONMENT}, version={APP_VERSION})")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        sentry_sdk = None
else:
    logger.info("Sentry DSN not configured, monitoring disabled")


def scrub_sensitive_data(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Scrub sensitive data from Sentry events before sending
    
    Args:
        event: Sentry event dictionary
        hint: Additional context about the event
        
    Returns:
        Modified event or None to drop the event
    """
    if not event:
        return None
    
    sensitive_fields = [
        'password', 'api_key', 'secret', 'token', 'authorization',
        'access_token', 'refresh_token', 'jwt', 'bearer'
    ]
    
    if 'request' in event:
        request = event['request']
        
        if 'headers' in request:
            for field in sensitive_fields:
                if field in request['headers']:
                    request['headers'][field] = '[REDACTED]'
        
        if 'query_string' in request:
            for field in sensitive_fields:
                if field in str(request['query_string']).lower():
                    request['query_string'] = '[REDACTED]'
        
        if 'data' in request and isinstance(request['data'], dict):
            for field in sensitive_fields:
                if field in request['data']:
                    request['data'][field] = '[REDACTED]'
    
    if 'extra' in event:
        for field in sensitive_fields:
            if field in event['extra']:
                event['extra'][field] = '[REDACTED]'
    
    return event


def set_user_context(user_id: Optional[str] = None, tenant_id: Optional[str] = None, **kwargs):
    """
    Set user context for Sentry events
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        **kwargs: Additional user context
    """
    if not sentry_sdk:
        return
    
    context = {}
    if user_id:
        context['id'] = user_id
    if tenant_id:
        context['tenant_id'] = tenant_id
    context.update(kwargs)
    
    sentry_sdk.set_user(context)


def set_context(context_name: str, context_data: Dict[str, Any]):
    """
    Set custom context for Sentry events
    
    Args:
        context_name: Name of the context (e.g., 'agent', 'task')
        context_data: Context data dictionary
    """
    if not sentry_sdk:
        return
    
    sentry_sdk.set_context(context_name, context_data)


def add_breadcrumb(category: str, message: str, level: str = 'info', data: Optional[Dict[str, Any]] = None):
    """
    Add breadcrumb to Sentry event trail
    
    Args:
        category: Breadcrumb category (e.g., 'agent_task', 'api_call')
        message: Breadcrumb message
        level: Log level (debug, info, warning, error, critical)
        data: Additional breadcrumb data
    """
    if not sentry_sdk:
        return
    
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data or {}
    )


def capture_exception(exception: Exception, **kwargs):
    """
    Capture exception and send to Sentry
    
    Args:
        exception: Exception to capture
        **kwargs: Additional context
    """
    if not sentry_sdk:
        logger.error(f"Exception (Sentry disabled): {exception}", exc_info=True)
        return
    
    for key, value in kwargs.items():
        sentry_sdk.set_tag(key, value)
    
    sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = 'info', **kwargs):
    """
    Capture message and send to Sentry
    
    Args:
        message: Message to capture
        level: Log level
        **kwargs: Additional context
    """
    if not sentry_sdk:
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
        return
    
    for key, value in kwargs.items():
        sentry_sdk.set_tag(key, value)
    
    sentry_sdk.capture_message(message, level=level)


def monitor_performance(transaction_name: str):
    """
    Decorator to monitor function performance with Sentry
    
    Args:
        transaction_name: Name of the transaction
        
    Example:
        @monitor_performance("agent_task_execution")
        def execute_task(task_id):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not sentry_sdk:
                return func(*args, **kwargs)
            
            with sentry_sdk.start_transaction(op="function", name=transaction_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def start_transaction(op: str, name: str, **kwargs):
    """
    Start a Sentry transaction for performance monitoring
    
    Args:
        op: Operation type (e.g., 'http.server', 'db.query')
        name: Transaction name
        **kwargs: Additional transaction data
        
    Returns:
        Transaction context manager or None
    """
    if not sentry_sdk:
        return None
    
    return sentry_sdk.start_transaction(op=op, name=name, **kwargs)


def start_span(op: str, description: str):
    """
    Start a Sentry span within a transaction
    
    Args:
        op: Operation type
        description: Span description
        
    Returns:
        Span context manager or None
    """
    if not sentry_sdk:
        return None
    
    return sentry_sdk.start_span(op=op, description=description)


class SentryMetrics:
    """Helper class for tracking custom metrics in Sentry"""
    
    @staticmethod
    def increment(metric_name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            tags: Metric tags
        """
        if not sentry_sdk:
            return
        
        try:
            sentry_sdk.metrics.incr(
                key=metric_name,
                value=value,
                tags=tags or {}
            )
        except AttributeError:
            pass
    
    @staticmethod
    def gauge(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Metric tags
        """
        if not sentry_sdk:
            return
        
        try:
            sentry_sdk.metrics.gauge(
                key=metric_name,
                value=value,
                tags=tags or {}
            )
        except AttributeError:
            pass
    
    @staticmethod
    def distribution(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a distribution metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Metric tags
        """
        if not sentry_sdk:
            return
        
        try:
            sentry_sdk.metrics.distribution(
                key=metric_name,
                value=value,
                tags=tags or {}
            )
        except AttributeError:
            pass


__all__ = [
    'sentry_sdk',
    'set_user_context',
    'set_context',
    'add_breadcrumb',
    'capture_exception',
    'capture_message',
    'monitor_performance',
    'start_transaction',
    'start_span',
    'SentryMetrics'
]
