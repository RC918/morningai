"""
Flow Controller v3 - Deterministic Canary Gating (#3431)

Issue #3431: Deterministic Canary Gating for Flow Router v3
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing

This module implements deterministic canary gating for gradual rollout:
- Hash-based bucketing for sticky assignment (same workflow always routes same way)
- Configurable percentage via DYNAMIC_ROUTING_SAMPLE_RATE (0-100)
- Decision made once at workflow start and propagated through context
- Fail-safe: defaults to legacy routing on any error

Key Design Decisions:
1. Deterministic: Uses hash of stable key (trace_id) mod 100 for bucketing
2. Sticky: Same trace_id always routes to same path (no random flipping)
3. Configurable: DYNAMIC_ROUTING_SAMPLE_RATE=5 means 5% canary
4. Safe: Default 0% = disabled, falls back to ENABLE_DYNAMIC_ROUTING flag

Event Codes (greppable):
- [CANARY_GATING] - Canary gating decision made
- [CANARY_BUCKET] - Workflow assigned to bucket
- [CANARY_ENABLED] - Dynamic routing enabled for this workflow
- [CANARY_DISABLED] - Dynamic routing disabled for this workflow

Usage:
    from core.flow.canary_gating import should_enable_dynamic_routing

    # At workflow start, decide once and propagate
    enable_routing = should_enable_dynamic_routing(trace_id="abc123")

    # Or with explicit sample rate override
    enable_routing = should_enable_dynamic_routing(
        trace_id="abc123",
        sample_rate_override=5  # 5% canary
    )
"""
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def compute_bucket(stable_key: str) -> int:
    """Compute deterministic bucket (0-99) from stable key.

    Uses SHA-256 hash of the key, then takes mod 100 to get bucket.
    This ensures:
    - Same key always maps to same bucket (deterministic)
    - Uniform distribution across buckets (good hash function)
    - No random component (reproducible)

    Args:
        stable_key: Stable identifier (e.g., trace_id, job_id)

    Returns:
        Bucket number 0-99
    """
    if not stable_key:
        logger.warning("[CANARY_BUCKET] Empty stable_key, defaulting to bucket 0")
        return 0

    hash_bytes = hashlib.sha256(stable_key.encode('utf-8')).digest()
    hash_int = int.from_bytes(hash_bytes[:8], byteorder='big')
    bucket = hash_int % 100

    logger.debug(f"[CANARY_BUCKET] key={stable_key[:8]}... -> bucket={bucket}")
    return bucket


def is_in_sample(bucket: int, sample_rate: int) -> bool:
    """Check if bucket is within sample rate.

    Args:
        bucket: Bucket number 0-99
        sample_rate: Sample rate percentage 0-100

    Returns:
        True if bucket < sample_rate (i.e., in the sample)
    """
    return bucket < sample_rate


def should_enable_dynamic_routing(
    trace_id: str,
    sample_rate_override: Optional[int] = None,
    enable_flag_override: Optional[bool] = None
) -> bool:
    """Determine if dynamic routing should be enabled for this workflow.

    Decision Logic:
    1. If sample_rate > 0: Use deterministic bucketing
       - Compute bucket from trace_id hash
       - Enable if bucket < sample_rate
    2. If sample_rate == 0: Fall back to ENABLE_DYNAMIC_ROUTING flag

    This ensures:
    - Same trace_id always gets same decision (deterministic)
    - Gradual rollout via sample_rate (5% -> 25% -> 50% -> 100%)
    - Safe default (0% = disabled)

    Args:
        trace_id: Unique workflow identifier (stable key for bucketing)
        sample_rate_override: Override sample rate (for testing)
        enable_flag_override: Override enable flag (for testing)

    Returns:
        True if dynamic routing should be enabled for this workflow
    """
    try:
        from common.config.settings import settings

        sample_rate = sample_rate_override
        if sample_rate is None:
            sample_rate = getattr(settings, 'dynamic_routing_sample_rate', 0)

        enable_flag = enable_flag_override
        if enable_flag is None:
            enable_flag = getattr(settings, 'enable_dynamic_routing', False)

        if sample_rate > 0:
            bucket = compute_bucket(trace_id)
            enabled = is_in_sample(bucket, sample_rate)

            logger.info(
                f"[CANARY_GATING] trace_id={trace_id[:8]}... "
                f"bucket={bucket} sample_rate={sample_rate}% "
                f"-> {'ENABLED' if enabled else 'DISABLED'}"
            )

            if enabled:
                logger.info(f"[CANARY_ENABLED] Dynamic routing enabled for trace_id={trace_id[:8]}...")
            else:
                logger.info(f"[CANARY_DISABLED] Dynamic routing disabled for trace_id={trace_id[:8]}...")

            return enabled

        else:
            logger.info(
                f"[CANARY_GATING] sample_rate=0, using ENABLE_DYNAMIC_ROUTING={enable_flag}"
            )
            return enable_flag

    except Exception as e:
        logger.warning(
            f"[CANARY_GATING] Error determining routing: {e}, "
            f"defaulting to legacy routing (disabled)"
        )
        return False


def get_canary_status(trace_id: str) -> dict:
    """Get detailed canary status for observability.

    Args:
        trace_id: Unique workflow identifier

    Returns:
        Dict with canary status details
    """
    try:
        from common.config.settings import settings

        sample_rate = getattr(settings, 'dynamic_routing_sample_rate', 0)
        enable_flag = getattr(settings, 'enable_dynamic_routing', False)
        bucket = compute_bucket(trace_id)
        enabled = should_enable_dynamic_routing(trace_id)

        return {
            "trace_id": trace_id,
            "bucket": bucket,
            "sample_rate": sample_rate,
            "enable_flag": enable_flag,
            "dynamic_routing_enabled": enabled,
            "decision_source": "sample_rate" if sample_rate > 0 else "enable_flag"
        }

    except Exception as e:
        return {
            "trace_id": trace_id,
            "error": str(e),
            "dynamic_routing_enabled": False,
            "decision_source": "error_fallback"
        }
