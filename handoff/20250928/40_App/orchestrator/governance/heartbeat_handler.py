"""
Governance Heartbeat Handler - EPIC I-1 Operationalization

This module implements the governance heartbeat that periodically evaluates
provider health and degradation state. It is designed to be called from the
worker heartbeat thread.

Key Features:
- Distributed lock to prevent duplicate execution across workers
- Non-blocking lock acquisition (skip if lock held)
- Health alerting via HealthAlertService
- Degradation advisory via DegradationAdvisor
- Global health snapshot for routing engine consumption

Safety Contract:
- Governance failures MUST NOT affect worker heartbeat
- All operations are wrapped in try/except
- Lock acquisition is non-blocking (nx=True)

Blueprint Alignment:
- Section 4.3: Model Governance Framework v2
- Section 4.4: Autonomous Provisioning v2
- EPIC I-1: Operationalization (Heartbeat + Distributed Lock)

Issue: #3342
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Lock configuration
GOVERNANCE_LOCK_KEY = "governance:evaluator_lock"
GOVERNANCE_LOCK_TTL = 50  # seconds (less than 60s heartbeat interval)

# Snapshot configuration
GOVERNANCE_SNAPSHOT_KEY = "governance:health_snapshot"
GOVERNANCE_SNAPSHOT_TTL = 120  # seconds (2x heartbeat interval)

# Lua script for safe lock release (compare-and-delete)
# Only deletes the lock if we still own it (token matches)
LOCK_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class GovernanceHeartbeatResult:
    """Result of a governance heartbeat cycle"""

    def __init__(
        self,
        executed: bool,
        lock_acquired: bool,
        duration_seconds: float = 0.0,
        alerts_sent: int = 0,
        advisories_logged: int = 0,
        error: Optional[str] = None,
        skipped_reason: Optional[str] = None,
    ):
        self.executed = executed
        self.lock_acquired = lock_acquired
        self.duration_seconds = duration_seconds
        self.alerts_sent = alerts_sent
        self.advisories_logged = advisories_logged
        self.error = error
        self.skipped_reason = skipped_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executed": self.executed,
            "lock_acquired": self.lock_acquired,
            "duration_seconds": self.duration_seconds,
            "alerts_sent": self.alerts_sent,
            "advisories_logged": self.advisories_logged,
            "error": self.error,
            "skipped_reason": self.skipped_reason,
        }


def _acquire_governance_lock(
    redis_client: "Redis",
    evaluator_node_id: str,
) -> Optional[Tuple[str, str]]:
    """
    Acquire distributed lock for governance evaluation.

    Uses Redis SET NX EX for atomic non-blocking acquisition.
    Returns (lock_token, lock_value) tuple if acquired, None otherwise.

    Args:
        redis_client: Redis client instance
        evaluator_node_id: Unique identifier for this evaluator

    Returns:
        Tuple of (lock_token, lock_value) if acquired, None if lock is held by another worker.
        The lock_value is needed for atomic release via Lua script.
    """
    lock_token = uuid.uuid4().hex

    lock_value = json.dumps({
        "token": lock_token,
        "evaluator_node_id": evaluator_node_id,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    })

    try:
        # Non-blocking acquisition: nx=True means "set if not exists"
        acquired = redis_client.set(
            GOVERNANCE_LOCK_KEY,
            lock_value,
            nx=True,
            ex=GOVERNANCE_LOCK_TTL,
        )

        if acquired:
            logger.debug(
                "[Governance] Lock acquired",
                extra={
                    "operation": "governance_lock",
                    "evaluator_node_id": evaluator_node_id,
                    "lock_token": lock_token[:8],
                }
            )
            return (lock_token, lock_value)
        else:
            logger.debug(
                "[Governance] Lock held by another worker, skipping",
                extra={
                    "operation": "governance_lock",
                    "evaluator_node_id": evaluator_node_id,
                }
            )
            return None

    except Exception as e:
        logger.warning(
            f"[Governance] Failed to acquire lock: {e}",
            extra={
                "operation": "governance_lock",
                "evaluator_node_id": evaluator_node_id,
                "error": str(e),
            }
        )
        return None


def _release_governance_lock(
    redis_client: "Redis",
    lock_value: str,
    evaluator_node_id: str,
) -> bool:
    """
    Release distributed lock using atomic compare-and-delete via Lua script.

    Only releases if we still own the lock (lock_value matches exactly).
    This prevents accidentally deleting a lock that expired and was
    re-acquired by another worker.

    Uses Lua script for atomicity - the GET and conditional DELETE happen
    in a single Redis operation, eliminating race conditions.

    Args:
        redis_client: Redis client instance
        lock_value: The exact lock value string that was stored (from _acquire_governance_lock)
        evaluator_node_id: Unique identifier for this evaluator

    Returns:
        True if lock was released or already expired, False if owned by another worker
    """
    try:
        # Use Lua script for atomic compare-and-delete
        # This eliminates the race condition between GET and DELETE
        release_script = redis_client.register_script(LOCK_RELEASE_SCRIPT)
        result = release_script(keys=[GOVERNANCE_LOCK_KEY], args=[lock_value])

        if result == 1:
            logger.debug(
                "[Governance] Lock released (atomic)",
                extra={
                    "operation": "governance_lock_release",
                    "evaluator_node_id": evaluator_node_id,
                }
            )
            return True
        elif result == 0:
            # Lock value didn't match - either expired and re-acquired, or never held
            logger.debug(
                "[Governance] Lock not released (value mismatch or expired)",
                extra={
                    "operation": "governance_lock_release",
                    "evaluator_node_id": evaluator_node_id,
                }
            )
            return False
        else:
            # Unexpected result
            logger.warning(
                f"[Governance] Unexpected lock release result: {result}",
                extra={
                    "operation": "governance_lock_release",
                    "evaluator_node_id": evaluator_node_id,
                }
            )
            return False

    except Exception as e:
        logger.warning(
            f"[Governance] Failed to release lock: {e}",
            extra={
                "operation": "governance_lock_release",
                "evaluator_node_id": evaluator_node_id,
                "error": str(e),
            }
        )
        return False


def _update_health_snapshot(
    redis_client: "Redis",
    evaluator_node_id: str,
    health_results: Dict[str, Any],
    advisory_results: Dict[str, Any],
) -> bool:
    """
    Update global health snapshot in Redis.

    This snapshot is consumed by the routing engine for soft weighting.

    Args:
        redis_client: Redis client instance
        evaluator_node_id: Unique identifier for this evaluator
        health_results: Results from HealthAlertService.check_all_providers()
        advisory_results: Results from DegradationAdvisor.compute_all_advisories()

    Returns:
        True if snapshot was updated, False otherwise
    """
    try:
        snapshot = {
            "version": "1.0.0",
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
            "evaluator_node_id": evaluator_node_id,
            "health_check": {
                "providers_checked": health_results.get("providers_checked", []),
                "alerts_sent": len(health_results.get("alerts_sent", [])),
            },
            "degradation_advisory": {
                "providers_checked": advisory_results.get("providers_checked", []),
                "advisories_logged": advisory_results.get("advisories_logged", 0),
                "advisories": advisory_results.get("advisories", {}),
            },
            "ttl_seconds": GOVERNANCE_SNAPSHOT_TTL,
        }

        redis_client.setex(
            GOVERNANCE_SNAPSHOT_KEY,
            GOVERNANCE_SNAPSHOT_TTL,
            json.dumps(snapshot),
        )

        logger.debug(
            "[Governance] Health snapshot updated",
            extra={
                "operation": "governance_snapshot",
                "evaluator_node_id": evaluator_node_id,
                "providers_checked": len(health_results.get("providers_checked", [])),
            }
        )
        return True

    except Exception as e:
        logger.warning(
            f"[Governance] Failed to update health snapshot: {e}",
            extra={
                "operation": "governance_snapshot",
                "evaluator_node_id": evaluator_node_id,
                "error": str(e),
            }
        )
        return False


def run_governance_cycle(
    redis_client: Optional["Redis"],
    evaluator_node_id: str,
    heartbeat_id: str,
    worker_id: str,
) -> GovernanceHeartbeatResult:
    """
    Execute a single governance evaluation cycle.

    EPIC I-1: Operationalization (Heartbeat + Distributed Lock)

    This function is designed to be called from the worker heartbeat thread.
    It acquires a distributed lock, runs health checks and degradation advisory,
    and updates the global health snapshot.

    Safety Contract:
    - Non-blocking: Returns immediately if lock is held
    - Failure-isolated: Exceptions are caught and logged
    - Observe-only: Does not modify routing behavior (Phase A)

    Args:
        redis_client: Redis client instance (None = skip governance)
        evaluator_node_id: Unique identifier for this evaluator (typically HEARTBEAT_ID)
        heartbeat_id: Worker heartbeat ID for logging
        worker_id: Worker ID for logging

    Returns:
        GovernanceHeartbeatResult with execution details
    """
    start_time = time.monotonic()

    # Skip if Redis is not available
    if redis_client is None:
        return GovernanceHeartbeatResult(
            executed=False,
            lock_acquired=False,
            skipped_reason="redis_unavailable",
        )

    # Try to acquire distributed lock (non-blocking)
    lock_result = _acquire_governance_lock(redis_client, evaluator_node_id)

    if lock_result is None:
        # Lock held by another worker - skip this cycle
        return GovernanceHeartbeatResult(
            executed=False,
            lock_acquired=False,
            skipped_reason="lock_held_by_another_worker",
        )

    # Unpack lock token and value (value needed for atomic release)
    lock_token, lock_value = lock_result

    # Lock acquired - execute governance cycle
    try:
        logger.info(
            "[Governance] Executing health check cycle",
            extra={
                "operation": "governance_cycle",
                "evaluator_node_id": evaluator_node_id,
                "heartbeat_id": heartbeat_id,
                "worker_id": worker_id,
            }
        )

        alerts_sent = 0
        advisories_logged = 0
        health_results: Dict[str, Any] = {"enabled": False}
        advisory_results: Dict[str, Any] = {"enabled": False}

        # Run health alerting
        try:
            from governance.health_alerter import get_health_alert_service

            alert_service = get_health_alert_service()
            if alert_service is not None and alert_service.enabled:
                health_results = alert_service.check_all_providers()
                alerts_sent = len(health_results.get("alerts_sent", []))

                if alerts_sent > 0:
                    logger.info(
                        f"[Governance] Sent {alerts_sent} health alerts",
                        extra={
                            "operation": "governance_health_alert",
                            "evaluator_node_id": evaluator_node_id,
                            "alerts_sent": alerts_sent,
                        }
                    )
        except Exception as e:
            logger.warning(
                f"[Governance] Health alerting failed: {e}",
                extra={
                    "operation": "governance_health_alert",
                    "evaluator_node_id": evaluator_node_id,
                    "error": str(e),
                }
            )

        # Run degradation advisory
        try:
            from governance.degradation_advisor import get_degradation_advisor

            advisor = get_degradation_advisor()
            if advisor is not None and advisor.enabled:
                advisory_results = advisor.compute_all_advisories()
                advisories_logged = advisory_results.get("advisories_logged", 0)

                if advisories_logged > 0:
                    logger.info(
                        f"[Governance] Logged {advisories_logged} degradation advisories",
                        extra={
                            "operation": "governance_degradation_advisory",
                            "evaluator_node_id": evaluator_node_id,
                            "advisories_logged": advisories_logged,
                        }
                    )
        except Exception as e:
            logger.warning(
                f"[Governance] Degradation advisory failed: {e}",
                extra={
                    "operation": "governance_degradation_advisory",
                    "evaluator_node_id": evaluator_node_id,
                    "error": str(e),
                }
            )

        # Update global health snapshot
        _update_health_snapshot(
            redis_client,
            evaluator_node_id,
            health_results,
            advisory_results,
        )

        duration = time.monotonic() - start_time

        # Warn if cycle duration approaches lock TTL (90% threshold to reduce noise)
        if duration > GOVERNANCE_LOCK_TTL * 0.9:
            logger.warning(
                f"[Governance] Cycle duration ({duration:.1f}s) approaching lock TTL ({GOVERNANCE_LOCK_TTL}s)",
                extra={
                    "operation": "governance_cycle",
                    "evaluator_node_id": evaluator_node_id,
                    "duration_seconds": duration,
                    "lock_ttl": GOVERNANCE_LOCK_TTL,
                }
            )

        logger.info(
            f"[Governance] Health check cycle completed in {duration:.2f}s",
            extra={
                "operation": "governance_cycle",
                "evaluator_node_id": evaluator_node_id,
                "duration_seconds": duration,
                "alerts_sent": alerts_sent,
                "advisories_logged": advisories_logged,
            }
        )

        return GovernanceHeartbeatResult(
            executed=True,
            lock_acquired=True,
            duration_seconds=duration,
            alerts_sent=alerts_sent,
            advisories_logged=advisories_logged,
        )

    except Exception as e:
        duration = time.monotonic() - start_time
        logger.error(
            f"[Governance] Cycle failed: {e}",
            extra={
                "operation": "governance_cycle",
                "evaluator_node_id": evaluator_node_id,
                "duration_seconds": duration,
                "error": str(e),
            }
        )

        return GovernanceHeartbeatResult(
            executed=False,
            lock_acquired=True,
            duration_seconds=duration,
            error=str(e),
        )

    finally:
        # Always try to release lock (even on error)
        # Pass lock_value for atomic compare-and-delete via Lua script
        _release_governance_lock(redis_client, lock_value, evaluator_node_id)


def get_health_snapshot(redis_client: Optional["Redis"]) -> Optional[Dict[str, Any]]:
    """
    Get the current global health snapshot.

    This function is used by the routing engine to read the latest
    health state for soft weighting decisions.

    Args:
        redis_client: Redis client instance

    Returns:
        Health snapshot dict if available, None otherwise
    """
    if redis_client is None:
        return None

    try:
        snapshot_json = redis_client.get(GOVERNANCE_SNAPSHOT_KEY)
        if snapshot_json is None:
            return None

        return json.loads(snapshot_json)

    except Exception as e:
        logger.warning(
            f"[Governance] Failed to get health snapshot: {e}",
            extra={
                "operation": "governance_snapshot_read",
                "error": str(e),
            }
        )
        return None
