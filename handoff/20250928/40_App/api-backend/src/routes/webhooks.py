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
from datetime import datetime
from flask import Blueprint, jsonify, request
from common.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")

# Lazy import to avoid circular dependencies
_normalizer = None


def get_normalizer():
    """
    Get or create the EventNormalizer instance.

    Uses lazy initialization to avoid import issues at module load time.
    """
    global _normalizer
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
            logger.info("[Webhooks] EventNormalizer initialized")
        except ImportError as e:
            logger.warning("[Webhooks] Failed to import EventNormalizer: %s", e)
            _normalizer = None

    return _normalizer


def _enqueue_task(task):
    """
    Enqueue a normalized task for Meta Agent processing.

    Args:
        task: NormalizedTask from EventNormalizer

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
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

        # Enqueue the task
        job = queue.enqueue(
            run_orchestrator_task,
            task.task_id,
            task.goal_text,
            task.context.get("repo", settings.github_repo or "RC918/morningai"),
            "webhook",
            job_id=task.task_id,
            ttl=600,
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info("[Webhooks] Enqueued task %s as job %s", task.task_id, job.id)
        return job.id

    except Exception as e:
        logger.exception("[Webhooks] Failed to enqueue task: %s", e)
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


@bp.route("/github", methods=["POST"])
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
        500: Processing error
    """
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

        # Get headers
        headers = dict(request.headers)

        # Log incoming webhook
        event_type = headers.get("X-GitHub-Event", "unknown")
        delivery_id = headers.get("X-GitHub-Delivery", "unknown")
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
        500: Processing error
    """
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

        # Get headers
        headers = dict(request.headers)

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
        500: Processing error
    """
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

        # Get headers
        headers = dict(request.headers)

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
