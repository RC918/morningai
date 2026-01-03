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

    # Issue: #3366 - CI Failure Reflex Integration
    # Route CI failure events to dedicated auto-fix flow
    ci_failure_trigger = task.context.get("ci_failure_trigger", False)
    if ci_failure_trigger:
        return _enqueue_ci_failure_task(task)

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


def _enqueue_ci_failure_task(task):
    """
    Enqueue a CI failure task for auto-fix processing.

    This implements the CI failure reflex flow:
    Webhook (check_suite.completed) → EventNormalizer → _enqueue_ci_failure_task
    → run_orchestrator_task → LangGraph orchestrator → GeneralCoder/SeniorCoder

    The task is routed to the standard orchestrator with CI failure context,
    which triggers the auto-fix flow when the orchestrator detects:
    - ci_failure_trigger=True in context
    - ci_failure_pr_number for the target PR

    Issue: #3366 - CI Failure Reflex Integration

    Args:
        task: NormalizedTask from EventNormalizer with CI failure metadata

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        from redis import Redis
        from rq import Queue
        from rq.serializers import JSONSerializer

        redis_url = settings.redis_url
        if not redis_url:
            logger.warning("[Webhooks] Redis URL not configured, skipping CI failure task enqueue")
            return None

        redis_client = Redis.from_url(redis_url, decode_responses=False)
        queue_name = settings.rq_queue_name or "orchestrator"
        queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())

        # Import the worker function
        from redis_queue.worker import run_orchestrator_task

        # Get repository from task context or settings
        repo = task.context.get("repo") or settings.github_repo
        if not repo:
            logger.error(
                "[Webhooks] No repository specified for CI failure task %s",
                task.task_id,
            )
            return None

        # Extract CI failure metadata
        pr_number = task.context.get("ci_failure_pr_number")
        if not pr_number:
            logger.error(
                "[Webhooks] No PR number specified for CI failure task %s",
                task.task_id,
            )
            return None

        # Build context for orchestrator with CI failure info
        # The orchestrator will detect ci_failure_trigger and route to auto-fix flow
        ci_context = {
            **task.context,
            "resource_type": "pull_request",
            "resource_id": str(pr_number),
            "pr_number": pr_number,
            "ci_failure_trigger": True,
            "source": "ci_failure_webhook",
        }

        # Enqueue the task
        job = queue.enqueue(
            run_orchestrator_task,
            task.task_id,
            task.goal_text,
            repo,
            "ci_failure",  # task_type for metrics/logging
            ci_context,
            job_id=task.task_id,
            ttl=600,
            job_timeout=settings.rq_job_timeout,
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info(
            "[Webhooks] Enqueued CI failure task %s as job %s for repo %s PR #%s",
            task.task_id,
            job.id,
            repo,
            pr_number,
            extra={
                "operation": "enqueue_ci_failure_task",
                "task_id": task.task_id,
                "job_id": job.id,
                "repo": repo,
                "pr_number": pr_number,
            }
        )
        return job.id

    except Exception as e:
        logger.exception("[Webhooks] Failed to enqueue CI failure task: %s", e)
        return None


MANUAL_FIX_ACK_MARKER = "<!-- MORNINGAI_MANUAL_FIX_ACK -->"


def _enqueue_manual_fix_task(
    repo: str,
    pr_number: int,
    head_sha: str,
    manual_fix_context: dict,
    task_id: str,
):
    """
    Enqueue a manual fix task for auto-fix processing.

    This implements the manual /fix command flow:
    Webhook (issue_comment) → CommandRouter → EventNormalizer → _enqueue_manual_fix_task
    → run_orchestrator_task → LangGraph orchestrator → GeneralCoder/SeniorCoder

    Issue: #3518 - Manual /fix command for AutoFixer trigger

    Args:
        repo: Repository in owner/repo format
        pr_number: PR number
        head_sha: Current PR head SHA
        manual_fix_context: Context from EventNormalizer.handle_manual_fix_command()
        task_id: Unique task ID

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        from redis import Redis
        from rq import Queue
        from rq.serializers import JSONSerializer

        redis_url = settings.redis_url
        if not redis_url:
            logger.warning("[Webhooks] Redis URL not configured, skipping manual fix task enqueue")
            return None

        redis_client = Redis.from_url(redis_url, decode_responses=False)
        queue_name = settings.rq_queue_name or "orchestrator"
        queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())

        from redis_queue.worker import run_orchestrator_task

        actor = manual_fix_context.get('manual_trigger_actor', 'unknown')
        actor = (actor or 'unknown')[:39]
        goal_text = f"Fix CI failures for PR #{pr_number} (manual trigger by {actor})"

        ci_context = {
            **manual_fix_context,
            "resource_type": "pull_request",
            "resource_id": str(pr_number),
            "pr_number": pr_number,
            "ci_failure_trigger": True,
            "ci_head_sha": head_sha,
        }

        job = queue.enqueue(
            run_orchestrator_task,
            task_id,
            goal_text,
            repo,
            "manual_fix",
            ci_context,
            job_id=task_id,
            ttl=600,
            job_timeout=settings.rq_job_timeout,
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info(
            "[Webhooks] Enqueued manual fix task %s as job %s for repo %s PR #%s",
            task_id,
            job.id,
            repo,
            pr_number,
            extra={
                "operation": "enqueue_manual_fix_task",
                "task_id": task_id,
                "job_id": job.id,
                "repo": repo,
                "pr_number": pr_number,
                "actor": manual_fix_context.get("manual_trigger_actor"),
            }
        )
        return job.id

    except Exception as e:
        logger.exception("[Webhooks] Failed to enqueue manual fix task: %s", e)
        return None


def _post_manual_fix_acknowledgment(repo: str, pr_number: int, actor: str, task_id: str):
    """
    Post an acknowledgment comment to the PR after successful manual fix enqueue.

    The comment includes a marker to prevent self-trigger loops.

    Issue: #3518 - Acknowledgment comment for manual fix trigger

    Args:
        repo: Repository in owner/repo format
        pr_number: PR number
        actor: User who triggered the fix
        task_id: Task ID for reference

    Returns:
        True if comment posted successfully, False otherwise
    """
    try:
        github_token = settings.github_token
        if not github_token:
            logger.warning("[Webhooks] No GitHub token configured, skipping acknowledgment comment")
            return False

        import requests

        comment_body = f"""{MANUAL_FIX_ACK_MARKER}
**MorningAI AutoFixer triggered** by @{actor}

Task ID: `{task_id}`

The AutoFixer is now analyzing CI failures and will attempt to fix them automatically.
"""

        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

        response = requests.post(
            url,
            headers=headers,
            json={"body": comment_body},
            timeout=10,
        )

        if response.status_code in (200, 201):
            logger.info(
                "[Webhooks] Posted manual fix acknowledgment comment to %s PR #%s",
                repo,
                pr_number,
                extra={
                    "operation": "post_manual_fix_ack",
                    "repo": repo,
                    "pr_number": pr_number,
                    "actor": actor,
                    "task_id": task_id,
                }
            )
            return True
        else:
            logger.warning(
                "[Webhooks] Failed to post acknowledgment comment: %s %s",
                response.status_code,
                response.text[:200],
            )
            return False

    except Exception as e:
        logger.warning("[Webhooks] Error posting acknowledgment comment: %s", e)
        return False


def _get_pr_head_sha(repo: str, pr_number: int) -> str:
    """
    Fetch the current head SHA of a PR via GitHub API.

    Issue: #3518 - Need head SHA for manual fix dedup

    Args:
        repo: Repository in owner/repo format
        pr_number: PR number

    Returns:
        Head SHA string, or None if fetch failed
    """
    try:
        github_token = settings.github_token
        if not github_token:
            logger.warning("[Webhooks] No GitHub token configured, cannot fetch PR head SHA")
            return None

        import requests

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            head_sha = data.get("head", {}).get("sha")
            if head_sha:
                logger.debug(
                    "[Webhooks] Fetched PR head SHA: %s for %s PR #%s",
                    head_sha[:8],
                    repo,
                    pr_number,
                )
                return head_sha

        logger.warning(
            "[Webhooks] Failed to fetch PR head SHA: %s %s",
            response.status_code,
            response.text[:200] if response.text else "no response",
        )
        return None

    except Exception as e:
        logger.warning("[Webhooks] Error fetching PR head SHA: %s", e)
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


def _sanitize_dedup_key_component(value: str, component_name: str) -> str:
    """
    Sanitize a component for use in Redis dedup key.

    Issue: #3366 - Prevent malformed keys from entering Redis

    Args:
        value: The raw value to sanitize
        component_name: Name of the component for logging (e.g., "delivery_id", "hook_id")

    Returns:
        Sanitized value safe for Redis key, or empty string if invalid
    """
    if not value:
        return ""

    # Strip whitespace
    sanitized = value.strip()

    # Check for empty after strip
    if not sanitized:
        return ""

    # Reject values with characters that could cause Redis key issues
    # Allow alphanumeric, hyphens, and underscores (covers UUID format and numeric IDs)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', sanitized):
        logger.warning(
            "[Webhooks] Invalid %s format, skipping: %s",
            component_name,
            sanitized[:50],  # Truncate for safety in logs
        )
        return ""

    return sanitized


def _check_webhook_delivery_idempotency(delivery_id: str, hook_id: str = "") -> bool:
    """
    Check if a webhook delivery has already been processed (idempotency check).

    Issue: #2879 - Add idempotency to webhook handler
    Issue: #3366 - Fix prod/stg webhook dedup key collision

    This prevents duplicate processing of the same webhook event, which can occur
    due to GitHub retries, network issues, or race conditions.

    The dedup key now includes hook_id to prevent cross-environment collisions
    when prod and stg share the same Redis instance. GitHub sends the same
    delivery_id (guid) to different webhook subscriptions (prod/stg), so we
    need to namespace the dedup key by hook_id.

    Args:
        delivery_id: The X-GitHub-Delivery header value (unique per delivery)
        hook_id: The X-GitHub-Hook-ID header value (unique per webhook subscription)

    Returns:
        True if this delivery was already processed (should skip)
        False if this is a new delivery (should process)
    """
    # Sanitize inputs to prevent malformed Redis keys
    sanitized_delivery_id = _sanitize_dedup_key_component(delivery_id, "delivery_id")
    sanitized_hook_id = _sanitize_dedup_key_component(hook_id, "hook_id")

    if not sanitized_delivery_id or sanitized_delivery_id == "unknown":
        # No valid delivery ID, can't deduplicate - allow processing
        return False

    try:
        # Use shared Redis client singleton for:
        # - Connection reuse (avoids creating new connection per request)
        # - Consistent configuration across codebase
        # - Supports both Upstash Redis (REST) and standard Redis (TCP)
        from utils.redis_client import get_redis_client
        redis_client = get_redis_client()

        # Key format: webhook:delivery:{hook_id}:{delivery_id}
        # Include hook_id to prevent cross-environment collisions (prod/stg sharing Redis)
        # Fallback to delivery_id only if hook_id is not available (backward compatibility)
        # TTL: 7 days to handle delayed retries
        if sanitized_hook_id:
            dedup_key = f"webhook:delivery:{sanitized_hook_id}:{sanitized_delivery_id}"
        else:
            dedup_key = f"webhook:delivery:{sanitized_delivery_id}"
        ttl_seconds = 7 * 24 * 60 * 60  # 7 days

        # Use SET with NX and EX for atomic check-and-set with TTL
        # This is more reliable than setnx + expire (no crash window)
        # Returns True if key was set (new delivery), None if key exists (duplicate)
        result = redis_client.set(dedup_key, "1", nx=True, ex=ttl_seconds)

        if result:
            return False  # New delivery, should process
        else:
            logger.info(
                "[Webhooks] Duplicate webhook delivery detected, skipping: %s (hook_id=%s)",
                delivery_id,
                hook_id or "unknown",
            )
            return True  # Duplicate, should skip

    except Exception as e:
        # Redis error, allow processing (graceful degradation / fail-open)
        # Enhanced observability: structured logging + Sentry breadcrumbs
        error_type = type(e).__name__
        logger.warning(
            "[Webhooks] Redis error during idempotency check, fail-open",
            extra={
                "delivery_id": delivery_id,
                "hook_id": hook_id,
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
                    "hook_id": hook_id,
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
    # Issue: #3366 - Include hook_id to prevent cross-environment collisions (prod/stg)
    delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
    hook_id = request.headers.get("X-GitHub-Hook-ID", "")
    if _check_webhook_delivery_idempotency(delivery_id, hook_id):
        return jsonify({
            "status": "duplicate",
            "message": f"Webhook delivery {delivery_id} already processed",
            "delivery_id": delivery_id,
            "hook_id": hook_id,
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
            # Issue #3518: Check for manual /fix or /retry command first
            from orchestrator.webhooks.command_router import CommandType
            command_trigger = normalizer.route_command(event)

            if command_trigger and command_trigger.command_type == CommandType.FIX:
                # Handle manual fix command
                is_bare_fix = command_trigger.metadata.get("is_bare_fix", False)
                if is_bare_fix or command_trigger.metadata.get("event_type") in ("issue_commented", "pr_commented"):
                    # Fetch PR head SHA for dedup
                    head_sha = _get_pr_head_sha(command_trigger.repo, command_trigger.pr_number)
                    if head_sha:
                        # Check rate limit and dedup via normalizer
                        manual_fix_context = normalizer.handle_manual_fix_command(
                            command_trigger, head_sha
                        )

                        if manual_fix_context:
                            # Generate task ID
                            import uuid
                            repo_slug = command_trigger.repo.replace('/', '_')
                            pr_num = command_trigger.pr_number
                            task_id = f"manual_fix_{repo_slug}_{pr_num}_{uuid.uuid4().hex[:8]}"

                            # Enqueue the manual fix task
                            job_id = _enqueue_manual_fix_task(
                                command_trigger.repo,
                                command_trigger.pr_number,
                                head_sha,
                                manual_fix_context,
                                task_id,
                            )

                            if job_id:
                                # Post acknowledgment comment
                                _post_manual_fix_acknowledgment(
                                    command_trigger.repo,
                                    command_trigger.pr_number,
                                    command_trigger.actor,
                                    task_id,
                                )
                                response.task_id = task_id
                                response.message = f"Manual fix triggered, task created: {task_id}"
                                return jsonify(response.to_dict()), 200
                            else:
                                response.message = "Manual fix command received but failed to enqueue task"
                                return jsonify(response.to_dict()), 200
                        else:
                            # Rate limited or deduped
                            response.message = "Manual fix command rate limited or already processed"
                            return jsonify(response.to_dict()), 200
                    else:
                        logger.warning(
                            "[Webhooks] Could not fetch PR head SHA for manual fix command",
                            extra={
                                "repo": command_trigger.repo,
                                "pr_number": command_trigger.pr_number,
                            }
                        )
                        response.message = "Manual fix command received but could not fetch PR info"
                        return jsonify(response.to_dict()), 200

            # Normal task extraction flow
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
