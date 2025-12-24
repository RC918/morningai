"""
Webhook Routes - External Service Integration Endpoints

This module provides API endpoints for receiving webhooks from external services
(GitHub, Jira, Slack) and routing them to the Meta Agent for processing.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Endpoints:
    POST /api/webhooks/github - Receive GitHub webhook events
    POST /api/webhooks/jira - Receive Jira webhook events
    POST /api/webhooks/slack - Receive Slack webhook events
    GET /api/webhooks/health - Health check for webhook endpoints
"""

import json
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request
from common.config.settings import settings

# Maximum request body size for webhooks (1MB)
MAX_WEBHOOK_PAYLOAD_SIZE = 1 * 1024 * 1024  # 1MB


# Rate limiting configuration
WEBHOOK_RATE_LIMIT = 100  # requests per window
WEBHOOK_RATE_WINDOW = 60  # seconds


class WebhookRateLimiter:
    """
    Simple in-memory rate limiter for webhook endpoints.
    
    Uses sliding window algorithm with thread-safe operations.
    For production with multiple workers, consider using Redis-based rate limiting.
    """
    
    def __init__(self, limit: int = WEBHOOK_RATE_LIMIT, window: int = WEBHOOK_RATE_WINDOW):
        self.limit = limit
        self.window = window
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_rate_limited(self, key: str) -> tuple:
        """
        Check if a key is rate limited.
        
        Args:
            key: Identifier for rate limiting (e.g., IP address, source)
            
        Returns:
            tuple: (is_limited: bool, remaining: int, reset_time: int)
        """
        now = time.time()
        window_start = now - self.window
        
        with self._lock:
            # Clean old requests
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > window_start
            ]
            
            current_count = len(self._requests[key])
            
            if current_count >= self.limit:
                # Calculate reset time
                oldest_in_window = min(self._requests[key]) if self._requests[key] else now
                reset_time = int(oldest_in_window + self.window)
                return True, 0, reset_time
            
            # Record this request
            self._requests[key].append(now)
            remaining = self.limit - current_count - 1
            reset_time = int(now + self.window)
            
            return False, remaining, reset_time


# Global rate limiter instance
_webhook_rate_limiter = WebhookRateLimiter()


def rate_limit_webhook(f):
    """
    Decorator to apply rate limiting to webhook endpoints.
    
    Rate limits by client IP address and webhook source.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client IP
        client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        if not client_ip:
            client_ip = request.headers.get('X-Real-IP', request.remote_addr or 'unknown')
        
        # Create rate limit key based on IP and endpoint
        rate_key = f"webhook:{client_ip}:{request.endpoint}"
        
        is_limited, remaining, reset_time = _webhook_rate_limiter.is_rate_limited(rate_key)
        
        if is_limited:
            logger.warning(
                "[Webhooks] Rate limit exceeded for %s on %s",
                client_ip,
                request.endpoint
            )
            # Calculate retry_after once and clamp to non-negative
            now = int(time.time())
            retry_after = max(0, reset_time - now)
            
            response = jsonify({
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after
            })
            response.status_code = 429
            response.headers['X-RateLimit-Limit'] = str(_webhook_rate_limiter.limit)
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(reset_time)
            response.headers['Retry-After'] = str(retry_after)
            return response
        
        # Execute the actual function
        response = f(*args, **kwargs)
        
        # Add rate limit headers to successful responses
        if hasattr(response, 'headers'):
            response.headers['X-RateLimit-Limit'] = str(_webhook_rate_limiter.limit)
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(reset_time)
        
        return response
    
    return decorated_function


def check_payload_size():
    """
    Check if the request payload exceeds the maximum allowed size.
    
    Returns:
        tuple: (is_valid: bool, error_response: Response or None)
    """
    content_length = request.content_length
    if content_length and content_length > MAX_WEBHOOK_PAYLOAD_SIZE:
        logger.warning(
            "[Webhooks] Payload too large: %d bytes (max: %d)",
            content_length,
            MAX_WEBHOOK_PAYLOAD_SIZE
        )
        return False, (jsonify({
            "error": "Payload too large",
            "message": f"Request body exceeds maximum size of {MAX_WEBHOOK_PAYLOAD_SIZE} bytes",
            "max_size": MAX_WEBHOOK_PAYLOAD_SIZE
        }), 413)
    return True, None


logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")

# Lazy import to avoid circular dependencies
# Thread-safe singleton initialization using double-checked locking pattern
_normalizer = None
_normalizer_lock = threading.Lock()


def get_normalizer():
    """
    Get or create the EventNormalizer instance.

    Uses lazy initialization with thread-safe double-checked locking
    to avoid import issues at module load time and prevent race conditions
    in multi-threaded environments.
    """
    global _normalizer
    
    # Fast path: return cached instance without acquiring the lock
    if _normalizer is not None:
        return _normalizer
    
    # Slow path: initialize under lock
    with _normalizer_lock:
        # Double-check after acquiring lock
        if _normalizer is None:
            try:
                from orchestrator.webhooks.normalizer import EventNormalizer
                from orchestrator.webhooks.bot_protocol import WebhookConfig

                # Load configurations from settings
                github_config = WebhookConfig(
                    secret=getattr(settings, 'github_webhook_secret', None),
                    verify_signature=getattr(settings, 'webhook_verify_signature', True),
                )
                jira_config = WebhookConfig(
                    secret=getattr(settings, 'jira_webhook_secret', None),
                    verify_signature=getattr(settings, 'webhook_verify_signature', True),
                )
                slack_config = WebhookConfig(
                    secret=getattr(settings, 'slack_signing_secret', None),
                    verify_signature=getattr(settings, 'webhook_verify_signature', True),
                )

                _normalizer = EventNormalizer(
                    github_config=github_config,
                    jira_config=jira_config,
                    slack_config=slack_config,
                )
                logger.info("[Webhooks] EventNormalizer initialized (thread-safe)")
            except ImportError as e:
                logger.warning("[Webhooks] Failed to import EventNormalizer: %s", e)
                # Intentionally leave _normalizer as None

    return _normalizer


def _enqueue_task(task):
    """
    Enqueue a normalized task for Meta Agent processing.

    Args:
        task: NormalizedTask from EventNormalizer

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    # Check if Meta Agent path is enabled and should be used
    enable_meta_agent = getattr(settings, 'enable_meta_agent', False)
    use_meta_agent = enable_meta_agent and task.context.get("use_meta_agent", False)

    if use_meta_agent:
        return _enqueue_meta_agent_task(task)

    # Phase B-B: Check if this is a PR_UPDATED event that needs delayed job
    pr_updated_should_schedule = task.context.get("pr_updated_should_schedule_job", False)
    if pr_updated_should_schedule:
        return _enqueue_pr_updated_delayed_task(task)

    try:
        from redis import Redis
        from rq import Queue
        from rq.serializers import JSONSerializer

        redis_url = settings.redis_url
        if not redis_url:
            logger.warning("[Webhooks] Redis URL not configured, skipping task enqueue")
            return None

        redis_client = Redis.from_url(redis_url, decode_responses=False)
        queue_name = settings.rq_queue_name or "orchestrator"
        queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())

        # Import the worker function
        from redis_queue.worker import run_orchestrator_task

        # Get repository from task context or settings
        # Fail explicitly if no repository is configured to prevent tasks
        # from being sent to the wrong repository
        repo = task.context.get("repo") or settings.github_repo
        if not repo:
            logger.error(
                "[Webhooks] No repository specified in task context or settings; "
                "cannot enqueue task %s",
                task.task_id,
            )
            return None

        # Enqueue the task
        # Issue: Phase B-B - Pass task.context to worker for PR info
        job = queue.enqueue(
            run_orchestrator_task,
            task.task_id,
            task.goal_text,
            repo,
            "webhook",
            task.context,  # Pass context containing resource_id (PR number), url, etc.
            job_id=task.task_id,
            ttl=600,
            job_timeout=settings.rq_job_timeout,
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info(
            "[Webhooks] Enqueued task %s as job %s for repo %s (pr_number=%s)",
            task.task_id,
            job.id,
            repo,
            task.context.get("resource_id", "none"),
        )
        return job.id

    except Exception as e:
        logger.exception("[Webhooks] Failed to enqueue task: %s", e)
        return None


def _enqueue_pr_updated_delayed_task(task):
    """
    Enqueue a PR_UPDATED task with delayed execution for debounce.

    This implements the non-blocking delayed scheduling pattern:
    - First PR_UPDATED event schedules a delayed job using enqueue_in()
    - Job is automatically enqueued after debounce_seconds (no worker blocking)
    - Subsequent events only update the payload in Redis (no new job)
    - Worker checks if new push happened within debounce window

    Issue: Phase B-B - PR_UPDATED support with debounce/throttle
    CTO Decision: Prohibit time.sleep() inside worker - use enqueue_in() instead

    Args:
        task: NormalizedTask from EventNormalizer with PR_UPDATED metadata

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        from datetime import timedelta
        from redis import Redis
        from rq import Queue
        from rq.serializers import JSONSerializer

        redis_url = settings.redis_url
        if not redis_url:
            logger.warning("[Webhooks] Redis URL not configured, skipping PR_UPDATED task enqueue")
            return None

        redis_client = Redis.from_url(redis_url, decode_responses=False)
        queue_name = settings.rq_queue_name or "orchestrator"
        queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())

        from redis_queue.worker import run_pr_updated_delayed_task

        repo = task.context.get("repo") or settings.github_repo
        if not repo:
            logger.error(
                "[Webhooks] No repository specified for PR_UPDATED task %s",
                task.task_id,
            )
            return None

        pr_number = task.context.get("resource_id")
        if not pr_number:
            logger.error(
                "[Webhooks] No PR number specified for PR_UPDATED task %s",
                task.task_id,
            )
            return None

        try:
            pr_number = int(pr_number)
        except (ValueError, TypeError):
            logger.error(
                "[Webhooks] Invalid PR number for PR_UPDATED task %s: %s",
                task.task_id,
                pr_number,
            )
            return None

        job_token = task.context.get("pr_updated_job_token")
        if not job_token:
            logger.error(
                "[Webhooks] No job token for PR_UPDATED task %s",
                task.task_id,
            )
            return None

        debounce_seconds = task.context.get("pr_updated_debounce_seconds", 30)

        # Use enqueue_in for non-blocking delayed scheduling
        # Job will be automatically enqueued after debounce_seconds
        # This avoids blocking worker threads with time.sleep()
        job = queue.enqueue_in(
            timedelta(seconds=debounce_seconds),
            run_pr_updated_delayed_task,
            task.task_id,
            repo,
            pr_number,
            job_token,
            debounce_seconds,
            task.goal_text,
            task.context,
            job_id=task.task_id,
            ttl=debounce_seconds + 600,
            job_timeout=settings.rq_job_timeout,
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info(
            "[Webhooks] Scheduled PR_UPDATED delayed task %s as job %s for repo %s PR #%s (delay=%ds, non-blocking)",
            task.task_id,
            job.id,
            repo,
            pr_number,
            debounce_seconds,
        )
        return job.id

    except Exception as e:
        logger.exception("[Webhooks] Failed to enqueue PR_UPDATED delayed task: %s", e)
        return None


def _enqueue_meta_agent_task(task):
    """
    Enqueue a normalized task for Meta Agent autonomous execution.

    This is the entry point for #1822 integrated development tools flow:
    Webhook → _enqueue_meta_agent_task → run_meta_agent_task → AutonomousExecutor

    Args:
        task: NormalizedTask from EventNormalizer

    Returns:
        Job ID if enqueued successfully, None otherwise

    Feature Flags:
        - ENABLE_META_AGENT: Must be True to enable this path
        - ENABLE_META_AGENT_VM: Controls VM provisioning
    """
    try:
        from redis import Redis
        from rq import Queue
        from rq.serializers import JSONSerializer

        redis_url = settings.redis_url
        if not redis_url:
            logger.warning("[Webhooks] Redis URL not configured, skipping meta agent task enqueue")
            return None

        redis_client = Redis.from_url(redis_url, decode_responses=False)
        queue_name = settings.rq_queue_name or "orchestrator"
        queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())

        # Import the worker function
        from redis_queue.worker import run_meta_agent_task

        # Get repository from task context or settings
        repo = task.context.get("repo") or settings.github_repo
        if not repo:
            logger.error(
                "[Webhooks] No repository specified in task context or settings; "
                "cannot enqueue meta agent task %s",
                task.task_id,
            )
            return None

        # Get tenant_id from task context (required for multi-tenant isolation)
        tenant_id = task.context.get("tenant_id", "default")

        # Build context for Meta Agent
        meta_agent_context = {
            "branch": task.context.get("branch"),
            "labels": task.context.get("labels", []),
            "priority": task.context.get("priority", "normal"),
            "source": task.context.get("source", "webhook"),
            "pr_number": task.context.get("pr_number"),
            "issue_number": task.context.get("issue_number"),
        }

        # Enqueue the task
        job = queue.enqueue(
            run_meta_agent_task,
            task.task_id,
            task.goal_text,
            repo,
            tenant_id,
            meta_agent_context,
            job_id=task.task_id,
            ttl=1800,  # 30 minutes for autonomous execution
            job_timeout=1800,  # 30 minutes for autonomous execution
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info(
            "[Webhooks] Enqueued meta agent task %s as job %s for repo %s (tenant: %s)",
            task.task_id,
            job.id,
            repo,
            tenant_id,
        )
        return job.id

    except Exception as e:
        logger.exception("[Webhooks] Failed to enqueue meta agent task: %s", e)
        return None


@bp.route("/health", methods=["GET"])
def webhook_health():
    """Health check endpoint for webhook routes"""
    normalizer = get_normalizer()
    return jsonify({
        "status": "healthy",
        "normalizer_available": normalizer is not None,
        "timestamp": datetime.utcnow().isoformat(),
        "handlers": {
            "github": normalizer is not None,
            "jira": normalizer is not None,
            "slack": normalizer is not None,
        }
    })


def _check_webhook_delivery_idempotency(delivery_id: str) -> bool:
    """
    Check if a webhook delivery has already been processed (idempotency check).

    Issue: #2879 - Add idempotency to webhook handler
    This prevents duplicate processing of the same webhook event, which can occur
    due to GitHub retries, network issues, or race conditions.

    Args:
        delivery_id: The X-GitHub-Delivery header value (unique per delivery)

    Returns:
        True if this delivery was already processed (should skip)
        False if this is a new delivery (should process)
    """
    if not delivery_id or delivery_id == "unknown":
        # No delivery ID, can't deduplicate - allow processing
        return False

    try:
        from redis import Redis
        redis_url = settings.redis_url
        if not redis_url:
            # Redis not configured, allow processing
            return False

        redis_client = Redis.from_url(redis_url, decode_responses=True)

        # Key format: webhook:delivery:{delivery_id}
        # TTL: 7 days to handle delayed retries
        dedup_key = f"webhook:delivery:{delivery_id}"
        ttl_seconds = 7 * 24 * 60 * 60  # 7 days

        # Use SET with NX and EX for atomic check-and-set with TTL
        # This is more reliable than setnx + expire (no crash window)
        # Returns True if key was set (new delivery), None if key exists (duplicate)
        result = redis_client.set(dedup_key, "1", nx=True, ex=ttl_seconds)

        if result:
            return False  # New delivery, should process
        else:
            logger.info(
                "[Webhooks] Duplicate webhook delivery detected, skipping: %s",
                delivery_id,
            )
            return True  # Duplicate, should skip

    except Exception as e:
        # Redis error, allow processing (graceful degradation / fail-open)
        # Issue #2882: Enhanced observability with structured logging + Sentry breadcrumbs
        error_type = type(e).__name__
        logger.warning(
            "[Webhooks] Redis error during idempotency check, fail-open",
            extra={
                "delivery_id": delivery_id,
                "error_type": error_type,
                "error_message": str(e),
                "fail_open": True,
            }
        )

        # Add Sentry breadcrumb for fail-open correlation
        try:
            import sentry_sdk
            sentry_sdk.add_breadcrumb(
                category="webhook.idempotency",
                message="Fail-open due to Redis error",
                level="warning",
                data={
                    "delivery_id": delivery_id,
                    "error_type": error_type,
                }
            )
        except ImportError:
            pass  # Sentry not available, skip breadcrumb

        return False


@bp.route("/github", methods=["POST"])
@rate_limit_webhook
def github_webhook():
    """
    Receive GitHub webhook events.

    Headers:
        X-GitHub-Event: Event type (e.g., "push", "pull_request")
        X-GitHub-Delivery: Unique delivery ID
        X-Hub-Signature-256: HMAC signature for validation

    Returns:
        200: Event received and processed
        400: Invalid request
        401: Invalid signature
        413: Payload too large
        429: Rate limit exceeded
        500: Processing error
    """
    # Check payload size
    is_valid, error_response = check_payload_size()
    if not is_valid:
        return error_response

    # Layer 1: Webhook Delivery Idempotency
    # Issue: #2879 - Prevent duplicate processing of the same webhook event
    delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
    if _check_webhook_delivery_idempotency(delivery_id):
        return jsonify({
            "status": "duplicate",
            "message": f"Webhook delivery {delivery_id} already processed",
            "delivery_id": delivery_id,
        }), 200

    try:
        normalizer = get_normalizer()
        if not normalizer:
            return jsonify({
                "error": "Webhook processing not available",
                "message": "EventNormalizer not initialized"
            }), 503

        # Get raw payload for signature validation
        payload = request.get_data()

        # Parse JSON payload
        try:
            parsed_payload = request.get_json(force=True) or {}
        except Exception as e:
            logger.warning("[Webhooks] Failed to parse GitHub payload: %s", e)
            return jsonify({
                "error": "Invalid JSON payload",
                "message": str(e)
            }), 400

        # Get headers - normalize to lowercase keys for consistent access
        # Fix: Phase B-B - HTTP headers are case-insensitive, but dict keys are not
        # Using lowercase keys is the best practice for header handling
        headers = {k.lower(): v for k, v in request.headers}

        # Log incoming webhook - use request.headers directly for case-insensitive access
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        logger.info(
            "[Webhooks] Received GitHub webhook: event=%s, delivery=%s",
            event_type,
            delivery_id,
        )

        # Process through normalizer
        from orchestrator.webhooks.bot_protocol import WebhookSource
        response = normalizer.process_webhook(
            WebhookSource.GITHUB,
            headers,
            payload,
            parsed_payload,
        )

        if not response.success:
            status_code = 401 if "signature" in response.message.lower() else 400
            return jsonify(response.to_dict()), status_code

        # Parse event and extract task if actionable
        event = normalizer.parse_event(WebhookSource.GITHUB, headers, parsed_payload)
        if event:
            task = normalizer.extract_task(event)
            if task:
                _enqueue_task(task)
                response.task_id = task.task_id
                response.message = f"Event processed, task created: {task.task_id}"

        return jsonify(response.to_dict()), 200

    except Exception as e:
        logger.exception("[Webhooks] Error processing GitHub webhook: %s", e)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@bp.route("/jira", methods=["POST"])
@rate_limit_webhook
def jira_webhook():
    """
    Receive Jira webhook events.

    Headers:
        X-Atlassian-Webhook-Identifier: Webhook identifier
        X-Hub-Signature: HMAC signature (if configured)

    Returns:
        200: Event received and processed
        400: Invalid request
        401: Invalid signature
        413: Payload too large
        429: Rate limit exceeded
        500: Processing error
    """
    # Check payload size
    is_valid, error_response = check_payload_size()
    if not is_valid:
        return error_response

    try:
        normalizer = get_normalizer()
        if not normalizer:
            return jsonify({
                "error": "Webhook processing not available",
                "message": "EventNormalizer not initialized"
            }), 503

        # Get raw payload for signature validation
        payload = request.get_data()

        # Parse JSON payload
        try:
            parsed_payload = request.get_json(force=True) or {}
        except Exception as e:
            logger.warning("[Webhooks] Failed to parse Jira payload: %s", e)
            return jsonify({
                "error": "Invalid JSON payload",
                "message": str(e)
            }), 400

        # Get headers - normalize to lowercase keys for consistent access
        headers = {k.lower(): v for k, v in request.headers}

        # Log incoming webhook
        webhook_event = parsed_payload.get("webhookEvent", "unknown")
        issue_key = parsed_payload.get("issue", {}).get("key", "unknown")
        logger.info(
            "[Webhooks] Received Jira webhook: event=%s, issue=%s",
            webhook_event,
            issue_key,
        )

        # Process through normalizer
        from orchestrator.webhooks.bot_protocol import WebhookSource
        response = normalizer.process_webhook(
            WebhookSource.JIRA,
            headers,
            payload,
            parsed_payload,
        )

        if not response.success:
            status_code = 401 if "signature" in response.message.lower() else 400
            return jsonify(response.to_dict()), status_code

        # Parse event and extract task if actionable
        event = normalizer.parse_event(WebhookSource.JIRA, headers, parsed_payload)
        if event:
            task = normalizer.extract_task(event)
            if task:
                _enqueue_task(task)
                response.task_id = task.task_id
                response.message = f"Event processed, task created: {task.task_id}"

        return jsonify(response.to_dict()), 200

    except Exception as e:
        logger.exception("[Webhooks] Error processing Jira webhook: %s", e)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@bp.route("/slack", methods=["POST"])
@rate_limit_webhook
def slack_webhook():
    """
    Receive Slack webhook events.

    Handles:
        - URL verification challenges
        - Event callbacks
        - Slash commands
        - Interactive components

    Headers:
        X-Slack-Signature: HMAC signature
        X-Slack-Request-Timestamp: Request timestamp

    Returns:
        200: Event received and processed
        200 + challenge: URL verification response
        400: Invalid request
        401: Invalid signature
        413: Payload too large
        429: Rate limit exceeded
        500: Processing error
    """
    # Check payload size
    is_valid, error_response = check_payload_size()
    if not is_valid:
        return error_response

    try:
        normalizer = get_normalizer()
        if not normalizer:
            return jsonify({
                "error": "Webhook processing not available",
                "message": "EventNormalizer not initialized"
            }), 503

        # Get raw payload for signature validation
        payload = request.get_data()

        # Parse payload (Slack can send form-encoded or JSON)
        content_type = request.content_type or ""
        if "application/json" in content_type:
            try:
                parsed_payload = request.get_json(force=True) or {}
            except Exception as e:
                logger.warning("[Webhooks] Failed to parse Slack JSON payload: %s", e)
                return jsonify({
                    "error": "Invalid JSON payload",
                    "message": str(e)
                }), 400
        else:
            # Form-encoded (slash commands, interactive components)
            parsed_payload = dict(request.form)
            # Handle nested payload for interactive components
            if "payload" in parsed_payload:
                try:
                    parsed_payload = json.loads(parsed_payload["payload"])
                except Exception:
                    pass

        # Get headers - normalize to lowercase keys for consistent access
        headers = {k.lower(): v for k, v in request.headers}

        # Handle URL verification challenge
        if parsed_payload.get("type") == "url_verification":
            challenge = parsed_payload.get("challenge", "")
            logger.info("[Webhooks] Responding to Slack URL verification")
            return jsonify({"challenge": challenge}), 200

        # Log incoming webhook
        event_type = parsed_payload.get("event", {}).get("type", "unknown")
        team_id = parsed_payload.get("team_id", "unknown")
        logger.info(
            "[Webhooks] Received Slack webhook: event=%s, team=%s",
            event_type,
            team_id,
        )

        # Process through normalizer
        from orchestrator.webhooks.bot_protocol import WebhookSource
        handler = normalizer.get_handler(WebhookSource.SLACK)
        if handler:
            # Use Slack handler's special handling for signature validation
            response = handler.handle(headers, payload, parsed_payload)

            # Handle challenge response from handler
            if isinstance(response, dict) and "challenge" in response:
                return jsonify(response), 200
        else:
            from orchestrator.webhooks.bot_protocol import WebhookResponse
            response = WebhookResponse(
                success=False,
                message="Slack handler not available",
            )

        if not response.success:
            status_code = 401 if "signature" in response.message.lower() else 400
            return jsonify(response.to_dict()), status_code

        # Parse event and extract task if actionable
        event = normalizer.parse_event(WebhookSource.SLACK, headers, parsed_payload)
        if event:
            task = normalizer.extract_task(event)
            if task:
                _enqueue_task(task)
                response.task_id = task.task_id
                response.message = f"Event processed, task created: {task.task_id}"

        return jsonify(response.to_dict()), 200

    except Exception as e:
        logger.exception("[Webhooks] Error processing Slack webhook: %s", e)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@bp.route("/test", methods=["POST"])
def test_webhook():
    """
    Test endpoint for webhook processing.

    This endpoint allows testing webhook processing without external services.
    Only available in non-production environments.

    Request Body:
        {
            "source": "github" | "jira" | "slack",
            "headers": {...},
            "payload": {...}
        }
    """
    # Only allow in non-production
    if settings.environment == "production":
        return jsonify({
            "error": "Not available in production",
            "message": "Test endpoint is disabled in production environment"
        }), 403

    try:
        data = request.get_json() or {}
        source_str = data.get("source", "github")
        headers = data.get("headers", {})
        payload = data.get("payload", {})

        normalizer = get_normalizer()
        if not normalizer:
            return jsonify({
                "error": "Webhook processing not available",
                "message": "EventNormalizer not initialized"
            }), 503

        # Map source string to enum
        from orchestrator.webhooks.bot_protocol import WebhookSource
        source_map = {
            "github": WebhookSource.GITHUB,
            "jira": WebhookSource.JIRA,
            "slack": WebhookSource.SLACK,
        }
        source = source_map.get(source_str.lower())
        if not source:
            return jsonify({
                "error": "Invalid source",
                "message": f"Source must be one of: {list(source_map.keys())}"
            }), 400

        # Parse event
        event = normalizer.parse_event(source, headers, payload)
        if not event:
            return jsonify({
                "error": "Failed to parse event",
                "message": "Could not parse webhook payload"
            }), 400

        # Extract task
        task = normalizer.extract_task(event)

        return jsonify({
            "success": True,
            "event": event.to_dict(),
            "task": task.to_dict() if task else None,
            "is_actionable": task is not None,
        }), 200

    except Exception as e:
        logger.exception("[Webhooks] Error in test endpoint: %s", e)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
