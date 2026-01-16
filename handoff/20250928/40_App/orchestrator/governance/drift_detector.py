"""
Runtime Drift Detection for LLM Responses

EPIC I-1: Runtime Model Governance & Immune System (Blueprint 4.3/4.4)
Issue: #3342

This module provides runtime validation of LLM responses to detect:
1. JSON format drift (when json_mode=True)
2. Schema violations
3. Unexpected response structures

Design Principles:
- Observe-only by default (DRIFT_DETECTION_BLOCK_ON_FAIL=false)
- Sampling support for high-traffic production
- Non-blocking to EPIC D (SimpleCoder/GeneralCoder) development
- Metrics emission for monitoring dashboards

Usage:
    from governance.drift_detector import observe_response, DriftDetector

    # In LLMClient.generate():
    response = self._provider.generate(...)
    observe_response(response, json_mode=json_mode)
    return response
"""

import json
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DriftType(str, Enum):
    """Types of drift that can be detected"""
    JSON_PARSE_ERROR = "json_parse_error"
    SCHEMA_VIOLATION = "schema_violation"
    EMPTY_RESPONSE = "empty_response"
    UNEXPECTED_FORMAT = "unexpected_format"
    MISSING_REQUIRED_FIELD = "missing_required_field"


class DriftSeverity(str, Enum):
    """Severity levels for drift events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftEvent:
    """
    Represents a detected drift event

    Telemetry v2 compatible format for structured logging.
    """
    event_type: str = "drift_detected"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    drift_type: DriftType = DriftType.UNEXPECTED_FORMAT
    severity: DriftSeverity = DriftSeverity.LOW
    provider: Optional[str] = None
    model: Optional[str] = None
    json_mode: bool = False
    error_message: Optional[str] = None
    response_preview: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "provider": self.provider,
            "model": self.model,
            "json_mode": self.json_mode,
            "error_message": self.error_message,
            "response_preview": self.response_preview,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


@dataclass
class DriftValidationResult:
    """Result of drift validation"""
    is_valid: bool
    events: List[DriftEvent] = field(default_factory=list)
    validation_time_ms: float = 0.0

    @property
    def has_drift(self) -> bool:
        """Check if any drift was detected"""
        return len(self.events) > 0


class DriftDetector:
    """
    Runtime drift detector for LLM responses

    EPIC I-1: Implements observe-only drift detection with optional blocking.

    Attributes:
        enabled: Whether drift detection is enabled
        block_on_fail: Whether to raise exceptions on drift (default: False)
        sample_rate: Fraction of requests to check (0.0-1.0)
    """

    def __init__(
        self,
        enabled: bool = False,
        block_on_fail: bool = False,
        sample_rate: float = 1.0
    ):
        """
        Initialize DriftDetector

        Args:
            enabled: Enable drift detection
            block_on_fail: Raise DriftDetectedError on drift (default: False for observe-only)
            sample_rate: Fraction of requests to validate (0.0-1.0)
        """
        self.enabled = enabled
        self.block_on_fail = block_on_fail
        self.sample_rate = max(0.0, min(1.0, sample_rate))
        self._drift_count = 0
        self._check_count = 0

        logger.info(
            f"[DriftDetector] Initialized: enabled={enabled}, "
            f"block_on_fail={block_on_fail}, sample_rate={sample_rate}"
        )

    def should_check(self) -> bool:
        """Determine if this request should be checked based on sampling"""
        if not self.enabled:
            return False
        if self.sample_rate >= 1.0:
            return True
        return random.random() < self.sample_rate

    def validate_response(
        self,
        content: str,
        json_mode: bool = False,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        expected_schema: Optional[Dict[str, Any]] = None
    ) -> DriftValidationResult:
        """
        Validate an LLM response for drift

        Args:
            content: Response content to validate
            json_mode: Whether JSON format was requested
            provider: LLM provider name
            model: Model name
            expected_schema: Optional JSON schema for validation

        Returns:
            DriftValidationResult with validation status and any drift events
        """
        start_time = time.time()
        events: List[DriftEvent] = []
        self._check_count += 1

        # Check for empty response
        if not content or not content.strip():
            events.append(DriftEvent(
                drift_type=DriftType.EMPTY_RESPONSE,
                severity=DriftSeverity.HIGH,
                provider=provider,
                model=model,
                json_mode=json_mode,
                error_message="Empty response received",
                response_preview=repr(content)[:100] if content else "None"
            ))

        # JSON mode validation
        elif json_mode:
            json_events = self._validate_json_response(
                content, provider, model, expected_schema
            )
            events.extend(json_events)

        validation_time_ms = (time.time() - start_time) * 1000

        if events:
            self._drift_count += len(events)
            self._emit_drift_events(events)

        return DriftValidationResult(
            is_valid=len(events) == 0,
            events=events,
            validation_time_ms=validation_time_ms
        )

    def _validate_json_response(
        self,
        content: str,
        provider: Optional[str],
        model: Optional[str],
        expected_schema: Optional[Dict[str, Any]]
    ) -> List[DriftEvent]:
        """Validate JSON response format"""
        events: List[DriftEvent] = []

        # Try to parse JSON
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            events.append(DriftEvent(
                drift_type=DriftType.JSON_PARSE_ERROR,
                severity=DriftSeverity.HIGH,
                provider=provider,
                model=model,
                json_mode=True,
                error_message=f"JSON parse error: {str(e)}",
                response_preview=content[:200] if content else None
            ))
            return events

        # Schema validation (if provided)
        if expected_schema:
            schema_events = self._validate_schema(
                parsed, expected_schema, provider, model
            )
            events.extend(schema_events)

        return events

    def _validate_schema(
        self,
        data: Any,
        schema: Dict[str, Any],
        provider: Optional[str],
        model: Optional[str]
    ) -> List[DriftEvent]:
        """
        Validate data against expected schema

        Simple schema validation - checks for required fields.
        For full JSON Schema validation, consider jsonschema library.
        """
        events: List[DriftEvent] = []

        # Check required fields
        required_fields = schema.get("required", [])
        if isinstance(data, dict):
            for field_name in required_fields:
                if field_name not in data:
                    events.append(DriftEvent(
                        drift_type=DriftType.MISSING_REQUIRED_FIELD,
                        severity=DriftSeverity.MEDIUM,
                        provider=provider,
                        model=model,
                        json_mode=True,
                        error_message=f"Missing required field: {field_name}",
                        metadata={"missing_field": field_name}
                    ))

        return events

    def _emit_drift_events(self, events: List[DriftEvent]) -> None:
        """Emit drift events for telemetry"""
        for event in events:
            logger.warning(
                f"[DriftDetector] DRIFT_DETECTED: type={event.drift_type.value}, "
                f"severity={event.severity.value}, provider={event.provider}, "
                f"model={event.model}",
                extra={
                    "telemetry_v2": True,
                    "event": event.to_dict()
                }
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get drift detection statistics

        Returns a dictionary containing:
            - enabled: Whether drift detection is enabled
            - block_on_fail: Whether to raise exceptions on drift
            - sample_rate: Fraction of requests being checked
            - check_count: Total number of checks performed
            - drift_count: Total number of drift events detected
            - drift_rate: Ratio of drift events to checks (0.0 if no checks)
        """
        return {
            "enabled": self.enabled,
            "block_on_fail": self.block_on_fail,
            "sample_rate": self.sample_rate,
            "check_count": self._check_count,
            "drift_count": self._drift_count,
            "drift_rate": self._drift_count / self._check_count if self._check_count > 0 else 0.0
        }

    def is_active(self) -> bool:
        """Check if drift detection is actively monitoring requests

        Returns True only if drift detection is both enabled and has a
        non-zero sample rate. This is useful for health checks and
        observability dashboards.

        Returns:
            bool: True if drift detection is actively monitoring
        """
        return self.enabled and self.sample_rate > 0.0


class DriftDetectedError(Exception):
    """
    Exception raised when drift is detected and block_on_fail=True

    This exception should only be raised when DRIFT_DETECTION_BLOCK_ON_FAIL=true.
    By default, drift detection is observe-only.
    """

    def __init__(self, events: List[DriftEvent]):
        self.events = events
        message = f"Drift detected: {len(events)} event(s)"
        if events:
            message += f" - {events[0].drift_type.value}: {events[0].error_message}"
        super().__init__(message)


# Global singleton instance with thread-safe initialization
_drift_detector: Optional[DriftDetector] = None
_drift_detector_lock = threading.Lock()


def get_drift_detector() -> DriftDetector:
    """
    Get or create the global DriftDetector instance (thread-safe)

    Reads configuration from settings on first call.
    Uses double-checked locking for thread-safe singleton initialization.

    Safety guarantees:
    - Falls back to disabled detector on ANY initialization error
    - Only logs warning once (not on every request)
    - Never blocks service operation due to configuration issues
    """
    global _drift_detector

    # Double-checked locking pattern for thread-safe singleton
    if _drift_detector is None:
        with _drift_detector_lock:
            if _drift_detector is None:
                try:
                    from common.config.settings import settings
                    _drift_detector = DriftDetector(
                        enabled=settings.drift_detection_enabled,
                        block_on_fail=settings.drift_detection_block_on_fail,
                        sample_rate=settings.drift_detection_sample_rate
                    )
                except ImportError:
                    logger.warning(
                        "[DriftDetector] Could not import settings, using defaults (disabled)"
                    )
                    _drift_detector = DriftDetector(enabled=False)
                except Exception as e:
                    # Catch ALL initialization errors (ValidationError, etc.)
                    # to prevent repeated initialization attempts and log spam
                    logger.warning(
                        f"[DriftDetector] Initialization error, using defaults (disabled): "
                        f"{type(e).__name__}"  # Only log exception type, not value (may contain secrets)
                    )
                    _drift_detector = DriftDetector(enabled=False)

    return _drift_detector


def observe_response(
    response: Any,
    json_mode: bool = False,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    expected_schema: Optional[Dict[str, Any]] = None
) -> DriftValidationResult:
    """
    Observe an LLM response for drift detection

    This is the main entry point for drift detection in LLMClient.generate().
    It is designed to be non-blocking by default (observe-only mode).

    Args:
        response: LLMResponse object or response content string
        json_mode: Whether JSON format was requested
        provider: LLM provider name
        model: Model name
        expected_schema: Optional JSON schema for validation

    Returns:
        DriftValidationResult with validation status

    Raises:
        DriftDetectedError: Only if block_on_fail=True and drift is detected

    Example:
        # In LLMClient.generate():
        response = self._provider.generate(...)

        # Observe response (non-blocking by default)
        from governance.drift_detector import observe_response
        result = observe_response(
            response,
            json_mode=json_mode,
            provider=self._provider_name,
            model=self.model
        )

        return response
    """
    detector = get_drift_detector()

    # Check if we should validate this request
    if not detector.should_check():
        return DriftValidationResult(is_valid=True)

    # Extract content from response and normalize to string
    # This handles various response types without raising AttributeError
    if hasattr(response, 'content'):
        content = response.content
    elif isinstance(response, str):
        content = response
    else:
        content = str(response)

    # Normalize content to string (some providers may return dict/list in json_mode)
    if not isinstance(content, str):
        try:
            content = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
        except (TypeError, ValueError):
            content = str(content)

    # Validate
    result = detector.validate_response(
        content=content,
        json_mode=json_mode,
        provider=provider,
        model=model,
        expected_schema=expected_schema
    )

    # Block if configured and drift detected
    if detector.block_on_fail and result.has_drift:
        raise DriftDetectedError(result.events)

    return result


def reset_drift_detector() -> None:
    """Reset the global drift detector (useful for testing)

    Thread-safe reset using the same lock as initialization.
    """
    global _drift_detector
    with _drift_detector_lock:
        _drift_detector = None
