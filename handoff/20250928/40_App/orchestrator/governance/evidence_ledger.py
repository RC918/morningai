"""
Evidence Ledger - Blueprint Section 4.6 Implementation

Issue: #4095 - [Phase 2] Evidence Ledger: Complete Decision Record + Reasoning Chain

This module implements the Evidence Ledger for tracking all agent decisions
with complete audit trails and reasoning chains.

Key Features:
- Decision Record: Complete schema for every important decision
- Reasoning Chain: Tracks the reasoning process leading to decisions
- Audit Trail: Queryable history of all decisions
- Rollback Support: Evidence preservation for decision rollback
- Retention Policy: Configurable data retention with automatic cleanup

Blueprint Alignment:
- Section 4.6: Evidence Ledger
- Governance Layer: Audit Trail requirements

Integration:
- TelemetryRecordV3: Uses existing telemetry schema for evidence refs
- Redis: Persistent storage for decision records
- Memory v2: Integration with memory system for context
"""

import json
import logging
import os
import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Redis keys for Evidence Ledger
EVIDENCE_LEDGER_KEY = "governance:evidence_ledger"
EVIDENCE_LEDGER_INDEX_KEY = "governance:evidence_ledger:index"
REASONING_CHAIN_KEY = "governance:reasoning_chain"


class DecisionType(str, Enum):
    """Types of decisions tracked in the Evidence Ledger"""
    ROUTING = "routing"  # Model/provider routing decisions
    SAFETY = "safety"  # Safety governor decisions
    AGENT = "agent"  # Agent selection/execution decisions
    MEMORY = "memory"  # Memory read/write decisions
    GOVERNANCE = "governance"  # Policy enforcement decisions
    TOOL = "tool"  # Tool selection/execution decisions
    REVIEW = "review"  # Code review decisions
    PLANNING = "planning"  # Task planning decisions


class DecisionOutcome(str, Enum):
    """Outcome of a decision"""
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    DEFERRED = "deferred"
    ESCALATED = "escalated"
    FAILED = "failed"


class ReasoningStepType(str, Enum):
    """Types of reasoning steps in a chain"""
    OBSERVATION = "observation"  # Input/context observation
    ANALYSIS = "analysis"  # Analysis of the situation
    HYPOTHESIS = "hypothesis"  # Hypothesis formation
    EVALUATION = "evaluation"  # Evaluation of options
    CONCLUSION = "conclusion"  # Final conclusion
    CONSTRAINT = "constraint"  # Constraint application
    FALLBACK = "fallback"  # Fallback reasoning


@dataclass
class ReasoningStep:
    """
    A single step in a reasoning chain.

    Tracks the progression of thought that led to a decision,
    enabling audit and debugging of AI behavior.
    """
    step_id: str
    step_type: ReasoningStepType
    description: str
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "description": self.description,
            "evidence_refs": self.evidence_refs,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningStep":
        """Create from dictionary"""
        return cls(
            step_id=data["step_id"],
            step_type=ReasoningStepType(data["step_type"]),
            description=data["description"],
            evidence_refs=data.get("evidence_refs", []),
            confidence=data.get("confidence", 1.0),
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class ReasoningChain:
    """
    A complete reasoning chain for a decision.

    Blueprint Section 4.6: Reasoning Chain
    Tracks the full reasoning process from observation to conclusion.
    """
    chain_id: str
    decision_id: str
    steps: List[ReasoningStep] = field(default_factory=list)
    total_confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def add_step(
        self,
        step_type: ReasoningStepType,
        description: str,
        evidence_refs: Optional[List[str]] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Add a step to the reasoning chain"""
        step = ReasoningStep(
            step_id=f"{self.chain_id}:step:{len(self.steps)}",
            step_type=step_type,
            description=description,
            evidence_refs=evidence_refs or [],
            confidence=confidence,
            metadata=metadata or {},
        )
        self.steps.append(step)
        self._update_total_confidence()
        return step

    def _update_total_confidence(self) -> None:
        """Update total confidence based on all steps"""
        if not self.steps:
            self.total_confidence = 1.0
            return
        self.total_confidence = min(step.confidence for step in self.steps)

    def complete(self) -> None:
        """Mark the reasoning chain as complete"""
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "chain_id": self.chain_id,
            "decision_id": self.decision_id,
            "steps": [step.to_dict() for step in self.steps],
            "total_confidence": self.total_confidence,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningChain":
        """Create from dictionary"""
        chain = cls(
            chain_id=data["chain_id"],
            decision_id=data["decision_id"],
            total_confidence=data.get("total_confidence", 1.0),
            created_at=data["created_at"],
            completed_at=data.get("completed_at"),
        )
        chain.steps = [
            ReasoningStep.from_dict(step_data)
            for step_data in data.get("steps", [])
        ]
        return chain


@dataclass
class DecisionRecord:
    """
    Complete record of a decision for audit purposes.

    Blueprint Section 4.6: Decision Record
    Every important decision is fully recorded with:
    - What was decided
    - Why it was decided (reasoning chain)
    - What evidence was used
    - What the outcome was
    - Who/what made the decision
    """
    decision_id: str
    decision_type: DecisionType
    component: str
    agent_id: Optional[str]
    trace_id: str
    span_id: str

    # Decision details
    input_summary: str
    output_summary: str
    outcome: DecisionOutcome
    confidence: float = 1.0

    # Reasoning and evidence
    reasoning_chain_id: Optional[str] = None
    evidence_hashes: List[str] = field(default_factory=list)
    policy_refs: List[str] = field(default_factory=list)

    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None

    # Rollback support
    rollback_available: bool = False
    rollback_data: Optional[Dict[str, Any]] = None
    rolled_back_at: Optional[str] = None
    rolled_back_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "component": self.component,
            "agent_id": self.agent_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "outcome": self.outcome.value,
            "confidence": self.confidence,
            "reasoning_chain_id": self.reasoning_chain_id,
            "evidence_hashes": self.evidence_hashes,
            "policy_refs": self.policy_refs,
            "context": self.context,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "rollback_available": self.rollback_available,
            "rollback_data": self.rollback_data,
            "rolled_back_at": self.rolled_back_at,
            "rolled_back_by": self.rolled_back_by,
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionRecord":
        """Create from dictionary"""
        return cls(
            decision_id=data["decision_id"],
            decision_type=DecisionType(data["decision_type"]),
            component=data["component"],
            agent_id=data.get("agent_id"),
            trace_id=data["trace_id"],
            span_id=data["span_id"],
            input_summary=data["input_summary"],
            output_summary=data["output_summary"],
            outcome=DecisionOutcome(data["outcome"]),
            confidence=data.get("confidence", 1.0),
            reasoning_chain_id=data.get("reasoning_chain_id"),
            evidence_hashes=data.get("evidence_hashes", []),
            policy_refs=data.get("policy_refs", []),
            context=data.get("context", {}),
            metadata=data.get("metadata", {}),
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            rollback_available=data.get("rollback_available", False),
            rollback_data=data.get("rollback_data"),
            rolled_back_at=data.get("rolled_back_at"),
            rolled_back_by=data.get("rolled_back_by"),
        )


@dataclass
class AuditQuery:
    """Query parameters for audit trail searches"""
    decision_type: Optional[DecisionType] = None
    component: Optional[str] = None
    agent_id: Optional[str] = None
    trace_id: Optional[str] = None
    outcome: Optional[DecisionOutcome] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_confidence: Optional[float] = None
    limit: int = 100
    offset: int = 0


@dataclass
class RetentionPolicy:
    """
    Retention policy for Evidence Ledger data.

    Blueprint Section 4.6: Retention policy implementation
    """
    default_ttl_days: int = 90
    routing_ttl_days: int = 30
    safety_ttl_days: int = 180
    governance_ttl_days: int = 365
    min_records_to_keep: int = 1000
    cleanup_batch_size: int = 100

    def get_ttl_for_type(self, decision_type: DecisionType) -> int:
        """Get TTL in seconds for a decision type"""
        ttl_days = {
            DecisionType.ROUTING: self.routing_ttl_days,
            DecisionType.SAFETY: self.safety_ttl_days,
            DecisionType.GOVERNANCE: self.governance_ttl_days,
        }.get(decision_type, self.default_ttl_days)
        return ttl_days * 86400


class EvidenceLedger:
    """
    Evidence Ledger for tracking all agent decisions.

    Blueprint Section 4.6: Evidence Ledger

    This class manages the complete audit trail of all decisions made
    by agents in the MorningAI system. It provides:
    - Decision recording with full context
    - Reasoning chain capture
    - Audit trail queries
    - Retention policy enforcement
    - Rollback support

    Thread-safe: All operations are protected by locks.
    """

    def __init__(
        self,
        redis_client: Optional["Redis"] = None,
        retention_policy: Optional[RetentionPolicy] = None,
        max_memory_records: int = 10000,
        enabled: bool = True,
    ):
        """
        Initialize the Evidence Ledger.

        Args:
            redis_client: Redis client for persistent storage
            retention_policy: Retention policy configuration
            max_memory_records: Maximum records to keep in memory
            enabled: Whether the ledger is enabled
        """
        self.redis_client = redis_client
        self.retention_policy = retention_policy or RetentionPolicy()
        self.max_memory_records = max_memory_records
        self.enabled = enabled

        # In-memory storage (fallback when Redis unavailable)
        self._decisions: Deque[DecisionRecord] = deque(maxlen=max_memory_records)
        self._reasoning_chains: Dict[str, ReasoningChain] = {}
        self._lock = threading.Lock()

        # Statistics
        self._total_decisions = 0
        self._decisions_by_type: Dict[str, int] = {}
        self._decisions_by_outcome: Dict[str, int] = {}

        logger.info(
            f"[EvidenceLedger] Initialized: enabled={enabled}, "
            f"redis={'connected' if redis_client else 'none'}, "
            f"retention_default={self.retention_policy.default_ttl_days}d"
        )

    def record_decision(
        self,
        decision_type: DecisionType,
        component: str,
        trace_id: str,
        span_id: str,
        input_summary: str,
        output_summary: str,
        outcome: DecisionOutcome,
        agent_id: Optional[str] = None,
        confidence: float = 1.0,
        reasoning_chain: Optional[ReasoningChain] = None,
        evidence_hashes: Optional[List[str]] = None,
        policy_refs: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        rollback_data: Optional[Dict[str, Any]] = None,
    ) -> DecisionRecord:
        """
        Record a decision in the Evidence Ledger.

        Args:
            decision_type: Type of decision
            component: Component that made the decision
            trace_id: Trace ID for correlation
            span_id: Span ID for correlation
            input_summary: Summary of input to the decision
            output_summary: Summary of decision output
            outcome: Outcome of the decision
            agent_id: Optional agent identifier
            confidence: Confidence level (0.0-1.0)
            reasoning_chain: Optional reasoning chain
            evidence_hashes: Optional list of evidence hashes
            policy_refs: Optional list of policy references
            context: Optional context dictionary
            metadata: Optional metadata dictionary
            rollback_data: Optional data for rollback support

        Returns:
            DecisionRecord with generated ID
        """
        if not self.enabled:
            return self._create_disabled_record(
                decision_type, component, trace_id, span_id,
                input_summary, output_summary, outcome
            )

        decision_id = f"dec:{uuid.uuid4().hex[:16]}"

        # Store reasoning chain if provided
        reasoning_chain_id = None
        if reasoning_chain:
            reasoning_chain.decision_id = decision_id
            reasoning_chain.complete()
            self._store_reasoning_chain(reasoning_chain)
            reasoning_chain_id = reasoning_chain.chain_id

        record = DecisionRecord(
            decision_id=decision_id,
            decision_type=decision_type,
            component=component,
            agent_id=agent_id,
            trace_id=trace_id,
            span_id=span_id,
            input_summary=input_summary,
            output_summary=output_summary,
            outcome=outcome,
            confidence=confidence,
            reasoning_chain_id=reasoning_chain_id,
            evidence_hashes=evidence_hashes or [],
            policy_refs=policy_refs or [],
            context=context or {},
            metadata=metadata or {},
            rollback_available=rollback_data is not None,
            rollback_data=rollback_data,
        )

        self._store_decision(record)

        logger.info(
            f"[EvidenceLedger] Decision recorded: id={decision_id}, "
            f"type={decision_type.value}, outcome={outcome.value}, "
            f"component={component}",
            extra={
                "operation": "evidence_ledger_record",
                "decision_id": decision_id,
                "decision_type": decision_type.value,
                "outcome": outcome.value,
                "component": component,
                "trace_id": trace_id,
            }
        )

        return record

    def _create_disabled_record(
        self,
        decision_type: DecisionType,
        component: str,
        trace_id: str,
        span_id: str,
        input_summary: str,
        output_summary: str,
        outcome: DecisionOutcome,
    ) -> DecisionRecord:
        """Create a minimal record when ledger is disabled"""
        return DecisionRecord(
            decision_id=f"disabled:{uuid.uuid4().hex[:8]}",
            decision_type=decision_type,
            component=component,
            agent_id=None,
            trace_id=trace_id,
            span_id=span_id,
            input_summary=input_summary,
            output_summary=output_summary,
            outcome=outcome,
        )

    def _store_decision(self, record: DecisionRecord) -> bool:
        """Store a decision record"""
        with self._lock:
            # Update statistics
            self._total_decisions += 1
            type_key = record.decision_type.value
            self._decisions_by_type[type_key] = self._decisions_by_type.get(type_key, 0) + 1
            outcome_key = record.outcome.value
            self._decisions_by_outcome[outcome_key] = self._decisions_by_outcome.get(outcome_key, 0) + 1

            # Store in memory
            self._decisions.append(record)

        # Store in Redis if available
        if self.redis_client:
            try:
                ttl = self.retention_policy.get_ttl_for_type(record.decision_type)
                key = f"{EVIDENCE_LEDGER_KEY}:{record.decision_id}"
                self.redis_client.setex(key, ttl, json.dumps(record.to_dict()))

                # Add to index for queries
                index_key = f"{EVIDENCE_LEDGER_INDEX_KEY}:{record.decision_type.value}"
                self.redis_client.zadd(
                    index_key,
                    {record.decision_id: datetime.fromisoformat(record.created_at).timestamp()}
                )

                return True
            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Failed to store in Redis: {e}",
                    extra={"operation": "evidence_ledger_store", "error": str(e)}
                )

        return False

    def _update_decision(self, record: DecisionRecord) -> bool:
        """
        Update an existing decision record in storage.

        Unlike _store_decision, this does not increment statistics or append
        to the deque. It updates the record in-place in memory and Redis.

        Args:
            record: The updated DecisionRecord

        Returns:
            True if Redis update succeeded, False otherwise
        """
        # Update in memory (find and replace)
        with self._lock:
            for i, existing in enumerate(self._decisions):
                if existing.decision_id == record.decision_id:
                    self._decisions[i] = record
                    break

        # Update in Redis if available
        if self.redis_client:
            try:
                ttl = self.retention_policy.get_ttl_for_type(record.decision_type)
                key = f"{EVIDENCE_LEDGER_KEY}:{record.decision_id}"
                self.redis_client.setex(key, ttl, json.dumps(record.to_dict()))
                return True
            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Failed to update in Redis: {e}",
                    extra={"operation": "evidence_ledger_update", "error": str(e)}
                )

        return False

    def _store_reasoning_chain(self, chain: ReasoningChain) -> bool:
        """Store a reasoning chain"""
        with self._lock:
            self._reasoning_chains[chain.chain_id] = chain

        if self.redis_client:
            try:
                key = f"{REASONING_CHAIN_KEY}:{chain.chain_id}"
                ttl = self.retention_policy.default_ttl_days * 86400
                self.redis_client.setex(key, ttl, json.dumps(chain.to_dict()))
                return True
            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Failed to store reasoning chain: {e}",
                    extra={"operation": "evidence_ledger_store_chain", "error": str(e)}
                )

        return False

    def create_reasoning_chain(self, decision_id: Optional[str] = None) -> ReasoningChain:
        """
        Create a new reasoning chain.

        Args:
            decision_id: Optional decision ID to associate with

        Returns:
            New ReasoningChain instance
        """
        chain_id = f"chain:{uuid.uuid4().hex[:16]}"
        return ReasoningChain(
            chain_id=chain_id,
            decision_id=decision_id or "",
        )

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """
        Get a decision record by ID.

        Args:
            decision_id: Decision ID to retrieve

        Returns:
            DecisionRecord if found, None otherwise
        """
        # Check Redis first
        if self.redis_client:
            try:
                key = f"{EVIDENCE_LEDGER_KEY}:{decision_id}"
                data = self.redis_client.get(key)
                if data:
                    return DecisionRecord.from_dict(json.loads(data))
            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Failed to get from Redis: {e}",
                    extra={"operation": "evidence_ledger_get", "error": str(e)}
                )

        # Check memory
        with self._lock:
            for record in self._decisions:
                if record.decision_id == decision_id:
                    return record

        return None

    def get_reasoning_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """
        Get a reasoning chain by ID.

        Args:
            chain_id: Chain ID to retrieve

        Returns:
            ReasoningChain if found, None otherwise
        """
        # Check Redis first
        if self.redis_client:
            try:
                key = f"{REASONING_CHAIN_KEY}:{chain_id}"
                data = self.redis_client.get(key)
                if data:
                    return ReasoningChain.from_dict(json.loads(data))
            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Failed to get chain from Redis: {e}",
                    extra={"operation": "evidence_ledger_get_chain", "error": str(e)}
                )

        # Check memory
        with self._lock:
            return self._reasoning_chains.get(chain_id)

    def query_decisions(self, query: AuditQuery) -> List[DecisionRecord]:
        """
        Query decisions based on audit criteria.

        Blueprint Section 4.6: Audit Trail query API

        Args:
            query: AuditQuery with filter criteria

        Returns:
            List of matching DecisionRecords
        """
        results: List[DecisionRecord] = []

        # Query from Redis if available
        if self.redis_client and query.decision_type:
            try:
                index_key = f"{EVIDENCE_LEDGER_INDEX_KEY}:{query.decision_type.value}"

                # Get decision IDs from index
                start_score = query.start_time.timestamp() if query.start_time else "-inf"
                end_score = query.end_time.timestamp() if query.end_time else "+inf"

                decision_ids = self.redis_client.zrangebyscore(
                    index_key,
                    start_score,
                    end_score,
                    start=query.offset,
                    num=query.limit,
                )

                for decision_id in decision_ids:
                    if isinstance(decision_id, bytes):
                        decision_id = decision_id.decode()
                    record = self.get_decision(decision_id)
                    if record and self._matches_query(record, query):
                        results.append(record)

                return results

            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Redis query failed, falling back to memory: {e}",
                    extra={"operation": "evidence_ledger_query", "error": str(e)}
                )

        # Fall back to memory query
        with self._lock:
            for record in self._decisions:
                if self._matches_query(record, query):
                    results.append(record)

        return results[query.offset:query.offset + query.limit]

    def _matches_query(self, record: DecisionRecord, query: AuditQuery) -> bool:
        """Check if a record matches query criteria"""
        if query.decision_type and record.decision_type != query.decision_type:
            return False
        if query.component and record.component != query.component:
            return False
        if query.agent_id and record.agent_id != query.agent_id:
            return False
        if query.trace_id and record.trace_id != query.trace_id:
            return False
        if query.outcome and record.outcome != query.outcome:
            return False
        if query.min_confidence and record.confidence < query.min_confidence:
            return False

        record_time = datetime.fromisoformat(record.created_at)
        if query.start_time and record_time < query.start_time:
            return False
        if query.end_time and record_time > query.end_time:
            return False

        return True

    def rollback_decision(
        self,
        decision_id: str,
        rolled_back_by: str,
        reason: Optional[str] = None,
    ) -> Optional[DecisionRecord]:
        """
        Mark a decision as rolled back.

        Blueprint Section 4.6: Rollback Support

        Args:
            decision_id: Decision ID to rollback
            rolled_back_by: Identifier of who initiated rollback
            reason: Optional reason for rollback

        Returns:
            Updated DecisionRecord if successful, None otherwise
        """
        record = self.get_decision(decision_id)
        if not record:
            logger.warning(
                f"[EvidenceLedger] Decision not found for rollback: {decision_id}"
            )
            return None

        if not record.rollback_available:
            logger.warning(
                f"[EvidenceLedger] Rollback not available for decision: {decision_id}"
            )
            return None

        record.rolled_back_at = datetime.now(timezone.utc).isoformat()
        record.rolled_back_by = rolled_back_by
        record.updated_at = datetime.now(timezone.utc).isoformat()

        if reason:
            record.metadata["rollback_reason"] = reason

        # Update in storage (use _update_decision instead of _store_decision)
        self._update_decision(record)

        # Sanitize rolled_back_by for log injection prevention
        safe_rolled_back_by = rolled_back_by.replace('\n', '_').replace('\r', '_')
        logger.info(
            f"[EvidenceLedger] Decision rolled back: id={decision_id}, by={safe_rolled_back_by}",
            extra={
                "operation": "evidence_ledger_rollback",
                "decision_id": decision_id,
                "rolled_back_by": rolled_back_by,
            }
        )

        return record

    def cleanup_expired(self) -> int:
        """
        Clean up expired records based on retention policy.

        Blueprint Section 4.6: Retention policy implementation

        Returns:
            Number of records cleaned up
        """
        cleaned = 0

        if self.redis_client:
            try:
                # Redis handles TTL automatically, but we clean up indexes
                for decision_type in DecisionType:
                    index_key = f"{EVIDENCE_LEDGER_INDEX_KEY}:{decision_type.value}"
                    ttl = self.retention_policy.get_ttl_for_type(decision_type)
                    cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl)

                    removed = self.redis_client.zremrangebyscore(
                        index_key,
                        "-inf",
                        cutoff.timestamp(),
                    )
                    cleaned += removed

            except Exception as e:
                logger.warning(
                    f"[EvidenceLedger] Cleanup failed: {e}",
                    extra={"operation": "evidence_ledger_cleanup", "error": str(e)}
                )

        # Clean up memory (keep min_records_to_keep)
        # Use per-type TTL for consistency with Redis storage
        with self._lock:
            if len(self._decisions) > self.retention_policy.min_records_to_keep:
                now = datetime.now(timezone.utc)
                original_count = len(self._decisions)

                # Filter to keep records that haven't expired based on their type-specific TTL
                recent_decisions = [
                    d for d in self._decisions
                    if datetime.fromisoformat(d.created_at) > (
                        now - timedelta(
                            seconds=self.retention_policy.get_ttl_for_type(d.decision_type)
                        )
                    )
                ]

                # Ensure we keep minimum records
                if len(recent_decisions) < self.retention_policy.min_records_to_keep:
                    recent_decisions = list(self._decisions)[
                        -self.retention_policy.min_records_to_keep:
                    ]

                self._decisions = deque(recent_decisions, maxlen=self.max_memory_records)
                cleaned += original_count - len(self._decisions)

        logger.info(
            f"[EvidenceLedger] Cleanup completed: removed={cleaned} records",
            extra={"operation": "evidence_ledger_cleanup", "removed": cleaned}
        )

        return cleaned

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the Evidence Ledger.

        Returns:
            Dictionary with ledger statistics
        """
        with self._lock:
            return {
                "enabled": self.enabled,
                "total_decisions": self._total_decisions,
                "memory_records": len(self._decisions),
                "reasoning_chains": len(self._reasoning_chains),
                "decisions_by_type": dict(self._decisions_by_type),
                "decisions_by_outcome": dict(self._decisions_by_outcome),
                "retention_policy": {
                    "default_ttl_days": self.retention_policy.default_ttl_days,
                    "safety_ttl_days": self.retention_policy.safety_ttl_days,
                    "governance_ttl_days": self.retention_policy.governance_ttl_days,
                },
                "redis_connected": self.redis_client is not None,
            }

    def verify_evidence_hash(
        self,
        decision_id: str,
        evidence_hash: str,
    ) -> bool:
        """
        Verify that an evidence hash exists in a decision record.

        Blueprint Section 4.6: Evidence hash verification

        Args:
            decision_id: Decision ID to check
            evidence_hash: Hash to verify

        Returns:
            True if hash is found in decision's evidence_hashes
        """
        record = self.get_decision(decision_id)
        if not record:
            return False
        return evidence_hash in record.evidence_hashes


# Global singleton instance
_evidence_ledger: Optional[EvidenceLedger] = None
_evidence_ledger_lock = threading.Lock()


def get_evidence_ledger(
    redis_client: Optional["Redis"] = None,
    retention_policy: Optional[RetentionPolicy] = None,
) -> EvidenceLedger:
    """
    Get the global EvidenceLedger instance.

    Thread-safe singleton using double-checked locking pattern.

    Note: The redis_client and retention_policy parameters are only used
    on the FIRST call that initializes the singleton. Subsequent calls
    will return the already-initialized instance and ignore these parameters.
    To reconfigure, call reset_evidence_ledger() first.

    Args:
        redis_client: Optional Redis client for persistent storage.
            **Only used on first initialization.**
        retention_policy: Optional retention policy configuration.
            **Only used on first initialization.**

    Returns:
        The global EvidenceLedger singleton
    """
    global _evidence_ledger
    if _evidence_ledger is None:
        with _evidence_ledger_lock:
            if _evidence_ledger is None:
                enabled = os.environ.get(
                    "EVIDENCE_LEDGER_ENABLED", "true"
                ).lower() not in ("false", "0", "no", "off")
                _evidence_ledger = EvidenceLedger(
                    redis_client=redis_client,
                    retention_policy=retention_policy,
                    enabled=enabled,
                )
    return _evidence_ledger


def reset_evidence_ledger() -> None:
    """Reset the global EvidenceLedger instance (for testing)"""
    global _evidence_ledger
    with _evidence_ledger_lock:
        _evidence_ledger = None
