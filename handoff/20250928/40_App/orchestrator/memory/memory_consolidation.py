"""
Memory Consolidation Agent - G-2

EPIC G: Memory v2 (Blueprint Section 5.1, 9, 10)

This module implements the "memory consolidation" mechanism that transfers
important short-term memories to long-term knowledge base, enabling true
"accumulated experience" capability.

The consolidation process:
1. Scans Agent Interaction Memory for expiring memories
2. Evaluates importance using a scoring formula
3. Summarizes important memories using LLM
4. Persists summaries to Knowledge Base (pgvector)
5. Cleans up consolidated Redis entries

Blueprint Alignment:
- Section 5.1: Memory v2 4-layer system
- Section 9: Predictability guarantee (all behavior can be reconstructed)
- Section 10: Deep Memory v3 (long-term knowledge + embedding decay)

Issue: #3973
"""

import json
import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from memory.memory_v2 import (
    MemoryEntry,
    MemoryLayer,
    MemoryV2,
    get_memory_v2,
)

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Memory type classification for consolidated memories"""
    DEBATE_INSIGHT = "debate_insight"
    SOLUTION_PATTERN = "solution_pattern"
    ERROR_FIX_PAIR = "error_fix_pair"
    FLOW_EXECUTION = "flow_execution"
    ROUTING_DECISION = "routing_decision"
    SAFETY_PATTERN = "safety_pattern"
    GENERAL = "general"


@dataclass
class ImportanceScore:
    """
    Importance scoring result for a memory entry.

    Formula (from Issue #3973):
    importance_score = (
        debate_confidence * 0.3 +    # Debate result confidence
        outcome_impact * 0.3 +       # Impact on system
        novelty_score * 0.2 +        # Is this new knowledge?
        reference_count * 0.2        # How often referenced?
    )
    """
    debate_confidence: float = 0.0
    outcome_impact: float = 0.0
    novelty_score: float = 0.0
    reference_count: float = 0.0

    @property
    def total(self) -> float:
        """Calculate total importance score"""
        return (
            self.debate_confidence * 0.3 +
            self.outcome_impact * 0.3 +
            self.novelty_score * 0.2 +
            self.reference_count * 0.2
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "debate_confidence": self.debate_confidence,
            "outcome_impact": self.outcome_impact,
            "novelty_score": self.novelty_score,
            "reference_count": self.reference_count,
            "total": self.total,
        }


@dataclass
class ConsolidationResult:
    """Result of a consolidation run"""
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    memories_scanned: int = 0
    memories_evaluated: int = 0
    memories_consolidated: int = 0
    memories_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    summarization_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "memories_scanned": self.memories_scanned,
            "memories_evaluated": self.memories_evaluated,
            "memories_consolidated": self.memories_consolidated,
            "memories_skipped": self.memories_skipped,
            "errors": self.errors,
            "summarization_latency_ms": self.summarization_latency_ms,
        }


class ImportanceScoringEngine:
    """
    Engine for evaluating memory importance.

    Uses the formula from Issue #3973:
    importance_score = (
        debate_confidence * 0.3 +
        outcome_impact * 0.3 +
        novelty_score * 0.2 +
        reference_count * 0.2
    )
    """

    DEFAULT_THRESHOLD = 0.5

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        memory: Optional[MemoryV2] = None,
    ):
        self.threshold = threshold
        self.memory = memory

    def score(self, entry: MemoryEntry) -> ImportanceScore:
        """
        Calculate importance score for a memory entry.

        Args:
            entry: Memory entry to score

        Returns:
            ImportanceScore with component scores
        """
        metadata = entry.metadata or {}

        debate_confidence = self._extract_debate_confidence(entry, metadata)
        outcome_impact = self._extract_outcome_impact(entry, metadata)
        novelty_score = self._calculate_novelty(entry)
        reference_count = self._calculate_reference_score(entry, metadata)

        return ImportanceScore(
            debate_confidence=debate_confidence,
            outcome_impact=outcome_impact,
            novelty_score=novelty_score,
            reference_count=reference_count,
        )

    def is_important(self, entry: MemoryEntry) -> Tuple[bool, ImportanceScore]:
        """
        Check if a memory entry is important enough to consolidate.

        Args:
            entry: Memory entry to evaluate

        Returns:
            Tuple of (is_important, score)
        """
        score = self.score(entry)
        return score.total >= self.threshold, score

    def _extract_debate_confidence(
        self,
        entry: MemoryEntry,
        metadata: Dict[str, Any],
    ) -> float:
        """Extract debate confidence from metadata"""
        if "debate_confidence" in metadata:
            return min(1.0, max(0.0, float(metadata["debate_confidence"])))

        if "confidence" in metadata:
            return min(1.0, max(0.0, float(metadata["confidence"])))

        if "decision" in metadata:
            return 0.7

        if "debate" in entry.content.lower():
            return 0.5

        return 0.0

    def _extract_outcome_impact(
        self,
        entry: MemoryEntry,
        metadata: Dict[str, Any],
    ) -> float:
        """Extract outcome impact from metadata"""
        if "outcome_impact" in metadata:
            return min(1.0, max(0.0, float(metadata["outcome_impact"])))

        if "impact" in metadata:
            return min(1.0, max(0.0, float(metadata["impact"])))

        if "severity" in metadata:
            severity = metadata["severity"]
            if severity == "critical":
                return 1.0
            elif severity == "high":
                return 0.8
            elif severity == "medium":
                return 0.5
            elif severity == "low":
                return 0.2

        if "success" in metadata and metadata["success"]:
            return 0.6

        return 0.3

    def _calculate_novelty(self, entry: MemoryEntry) -> float:
        """
        Calculate novelty score by checking if similar knowledge exists.

        Higher score = more novel (less similar content in Knowledge Base)
        """
        if self.memory is None:
            return 0.5

        try:
            query = entry.content[:200]
            existing = self.memory.search(
                query=query,
                layers=[MemoryLayer.KNOWLEDGE_BASE],
                limit=3,
            )

            if not existing:
                return 1.0

            max_similarity = max(
                (e.similarity or 0.0) for e in existing
            )

            return max(0.0, 1.0 - max_similarity)

        except Exception as e:
            logger.debug(f"[Consolidation] Novelty check failed: {e}")
            return 0.5

    def _calculate_reference_score(
        self,
        entry: MemoryEntry,
        metadata: Dict[str, Any],
    ) -> float:
        """Calculate reference count score"""
        if "reference_count" in metadata:
            count = int(metadata["reference_count"])
            return min(1.0, count / 10.0)

        if "access_count" in metadata:
            count = int(metadata["access_count"])
            return min(1.0, count / 5.0)

        return 0.0


class LLMSummarizer:
    """
    LLM-based summarization for memory consolidation.

    Summarizes important memories before persisting to Knowledge Base.
    """

    SUMMARIZATION_PROMPT = """You are a memory consolidation agent for an AI coding assistant.
Your task is to summarize the following memory entry into a concise, searchable knowledge entry.

Memory Content:
{content}

Memory Metadata:
{metadata}

Memory Type: {memory_type}

Instructions:
1. Extract the key insight or pattern from this memory
2. Make it searchable - include relevant keywords
3. Keep it concise (2-4 sentences)
4. Focus on actionable knowledge that can help future tasks
5. If this is a debate result, capture the winning argument and reasoning
6. If this is an error-fix pair, capture the problem and solution

Output a JSON object with:
- "summary": The concise summary (2-4 sentences)
- "keywords": List of 3-5 searchable keywords
- "memory_type": One of: debate_insight, solution_pattern, error_fix_pair, flow_execution, routing_decision, safety_pattern, general

Respond with valid JSON only."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self._client = None

    def _get_client(self):
        """Get LLM client lazily"""
        if self._client is not None:
            return self._client

        try:
            from llm.llm_client import get_llm_client
            self._client = get_llm_client()
            return self._client
        except Exception as e:
            logger.warning(f"[Consolidation] Failed to get LLM client: {e}")
            return None

    def summarize(
        self,
        entry: MemoryEntry,
        memory_type: MemoryType = MemoryType.GENERAL,
    ) -> Optional[Dict[str, Any]]:
        """
        Summarize a memory entry using LLM.

        Args:
            entry: Memory entry to summarize
            memory_type: Type classification for the memory

        Returns:
            Dictionary with summary, keywords, and memory_type
        """
        client = self._get_client()
        if client is None:
            return self._fallback_summarize(entry, memory_type)

        try:
            prompt = self.SUMMARIZATION_PROMPT.format(
                content=entry.content[:2000],
                metadata=json.dumps(entry.metadata or {}, indent=2)[:500],
                memory_type=memory_type.value,
            )

            response = client.generate(
                prompt=prompt,
                model=self.model,
                max_tokens=500,
                temperature=0.3,
            )

            result = json.loads(response)

            if "summary" not in result:
                result["summary"] = entry.content[:200]
            if "keywords" not in result:
                result["keywords"] = []
            if "memory_type" not in result:
                result["memory_type"] = memory_type.value

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"[Consolidation] LLM response not valid JSON: {e}")
            return self._fallback_summarize(entry, memory_type)
        except Exception as e:
            logger.warning(f"[Consolidation] LLM summarization failed: {e}")
            return self._fallback_summarize(entry, memory_type)

    def _fallback_summarize(
        self,
        entry: MemoryEntry,
        memory_type: MemoryType,
    ) -> Dict[str, Any]:
        """Fallback summarization without LLM"""
        content = entry.content

        if len(content) > 200:
            summary = content[:197] + "..."
        else:
            summary = content

        words = content.lower().split()
        keywords = list(set(
            word for word in words
            if len(word) > 4 and word.isalnum()
        ))[:5]

        return {
            "summary": summary,
            "keywords": keywords,
            "memory_type": memory_type.value,
        }


class MemoryConsolidationJob:
    """
    Memory Consolidation Job - G-2

    Runs periodically to consolidate important short-term memories
    into the long-term Knowledge Base.

    Usage:
        job = MemoryConsolidationJob()
        result = job.run()

    Or with scheduler:
        job = MemoryConsolidationJob()
        job.start_scheduler(interval_hours=6)
    """

    DEFAULT_IMPORTANCE_THRESHOLD = 0.5
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_INTERVAL_HOURS = 6

    def __init__(
        self,
        memory: Optional[MemoryV2] = None,
        importance_threshold: float = DEFAULT_IMPORTANCE_THRESHOLD,
        batch_size: int = DEFAULT_BATCH_SIZE,
        dry_run: bool = False,
        interval_hours: float = DEFAULT_INTERVAL_HOURS,
    ):
        self.memory = memory
        self.importance_threshold = importance_threshold
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.interval_hours = interval_hours

        self.scoring_engine = ImportanceScoringEngine(
            threshold=importance_threshold,
            memory=memory,
        )
        self.summarizer = LLMSummarizer()

        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_scheduler = threading.Event()
        self._scheduler_lock = threading.Lock()

        self._last_result: Optional[ConsolidationResult] = None
        self._run_count = 0

    def run(self) -> ConsolidationResult:
        """
        Execute a consolidation run.

        Steps:
        1. Scan Agent Interaction Memory for expiring memories
        2. Evaluate importance for each memory
        3. Summarize important memories using LLM
        4. Persist summaries to Knowledge Base
        5. Clean up consolidated Redis entries

        Returns:
            ConsolidationResult with run statistics
        """
        self._run_count += 1
        run_id = f"consolidation_{int(time.time())}_{self._run_count}"

        result = ConsolidationResult(
            run_id=run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(f"[Consolidation] Starting run {run_id}")

        try:
            memory = self.memory or get_memory_v2()
            if memory is None:
                result.errors.append("Memory v2 not available")
                result.completed_at = datetime.now(timezone.utc).isoformat()
                return result

            self.scoring_engine.memory = memory

            expiring_memories = self._scan_expiring_memories(memory)
            result.memories_scanned = len(expiring_memories)

            logger.info(
                f"[Consolidation] Scanned {result.memories_scanned} expiring memories"
            )

            important_memories = []
            for entry in expiring_memories:
                is_important, score = self.scoring_engine.is_important(entry)
                result.memories_evaluated += 1

                if is_important:
                    important_memories.append((entry, score))
                else:
                    result.memories_skipped += 1

            logger.info(
                f"[Consolidation] Found {len(important_memories)} important memories"
            )

            summarization_start = time.time()
            for entry, score in important_memories:
                try:
                    success = self._consolidate_memory(memory, entry, score)
                    if success:
                        result.memories_consolidated += 1
                    else:
                        result.memories_skipped += 1
                except Exception as e:
                    result.errors.append(f"Failed to consolidate {entry.key}: {e}")
                    result.memories_skipped += 1

            result.summarization_latency_ms = (time.time() - summarization_start) * 1000

            result.completed_at = datetime.now(timezone.utc).isoformat()
            self._last_result = result

            logger.info(
                f"[Consolidation] Completed run {run_id}: "
                f"consolidated={result.memories_consolidated}, "
                f"skipped={result.memories_skipped}, "
                f"errors={len(result.errors)}"
            )

            return result

        except Exception as e:
            result.errors.append(f"Run failed: {e}")
            result.completed_at = datetime.now(timezone.utc).isoformat()
            logger.error(f"[Consolidation] Run {run_id} failed: {e}")
            return result

    def _scan_expiring_memories(self, memory: MemoryV2) -> List[MemoryEntry]:
        """
        Scan Agent Interaction Memory for memories approaching expiration.

        Returns memories that are within 6 hours of TTL expiration.
        """
        try:
            results = memory.agent_interaction.search(
                query="",
                limit=self.batch_size,
            )

            expiring = []
            now = datetime.now(timezone.utc)
            expiration_window = timedelta(hours=6)

            for entry in results:
                if entry.expires_at:
                    try:
                        expires = datetime.fromisoformat(
                            entry.expires_at.replace("Z", "+00:00")
                        )
                        if expires - now <= expiration_window:
                            expiring.append(entry)
                    except (ValueError, TypeError):
                        expiring.append(entry)
                # Bug fix: Skip memories without expiration timestamp
                # They are not "expiring" and should not be consolidated prematurely

            return expiring

        except Exception as e:
            logger.warning(f"[Consolidation] Failed to scan memories: {e}")
            return []

    def _consolidate_memory(
        self,
        memory: MemoryV2,
        entry: MemoryEntry,
        score: ImportanceScore,
    ) -> bool:
        """
        Consolidate a single memory entry.

        Steps:
        1. Classify memory type
        2. Summarize using LLM
        3. Save to Knowledge Base
        4. Delete from Agent Interaction Memory (if not dry_run)
        """
        memory_type = self._classify_memory_type(entry)

        summary_result = self.summarizer.summarize(entry, memory_type)
        if summary_result is None:
            return False

        consolidated_entry = MemoryEntry(
            key=f"consolidated:{entry.key}",
            content=summary_result["summary"],
            layer=MemoryLayer.KNOWLEDGE_BASE,
            scope=entry.scope,
            metadata={
                "source": "consolidation",
                "source_key": entry.key,
                "source_layer": entry.layer.value,
                "memory_type": summary_result["memory_type"],
                "keywords": summary_result["keywords"],
                "importance_score": score.to_dict(),
                "original_created_at": entry.created_at,
                "consolidated_at": datetime.now(timezone.utc).isoformat(),
                **{k: v for k, v in (entry.metadata or {}).items()
                   if k not in ["source", "source_key", "source_layer"]},
            },
            trace_id=entry.trace_id,
            agent_id=entry.agent_id,
        )

        if self.dry_run:
            logger.info(
                f"[Consolidation] DRY RUN - Would consolidate: {entry.key} "
                f"(score={score.total:.2f}, type={memory_type.value})"
            )
            return True

        success = memory.save(consolidated_entry, layer=MemoryLayer.KNOWLEDGE_BASE)

        if success:
            delete_success = memory.delete(
                entry.key, layer=MemoryLayer.AGENT_INTERACTION
            )
            if delete_success:
                logger.debug(
                    f"[Consolidation] Consolidated: {entry.key} -> {consolidated_entry.key}"
                )
            else:
                logger.warning(
                    f"[Consolidation] Saved but failed to delete source: {entry.key}"
                )
                return False

        return success

    def _classify_memory_type(self, entry: MemoryEntry) -> MemoryType:
        """Classify memory type based on content and metadata"""
        metadata = entry.metadata or {}
        content_lower = entry.content.lower()

        if "debate" in metadata or "debate" in content_lower:
            return MemoryType.DEBATE_INSIGHT

        if "error" in metadata or "fix" in metadata:
            return MemoryType.ERROR_FIX_PAIR

        if "routing" in metadata or "routing" in content_lower:
            return MemoryType.ROUTING_DECISION

        if "safety" in metadata or "compliance" in content_lower:
            return MemoryType.SAFETY_PATTERN

        if "flow" in metadata or "execution" in content_lower:
            return MemoryType.FLOW_EXECUTION

        if "solution" in content_lower or "pattern" in content_lower:
            return MemoryType.SOLUTION_PATTERN

        return MemoryType.GENERAL

    def start_scheduler(
        self,
        interval_hours: Optional[float] = None,
    ) -> None:
        """
        Start the consolidation scheduler.

        Args:
            interval_hours: Hours between consolidation runs (uses self.interval_hours if not provided)
        """
        if interval_hours is None:
            interval_hours = self.interval_hours

        with self._scheduler_lock:
            if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
                logger.warning("[Consolidation] Scheduler already running")
                return

            self._stop_scheduler.clear()

            def scheduler_loop():
                logger.info(
                    f"[Consolidation] Scheduler started (interval={interval_hours}h)"
                )
                while not self._stop_scheduler.is_set():
                    try:
                        self.run()
                    except Exception as e:
                        logger.error(f"[Consolidation] Scheduler run failed: {e}")

                    self._stop_scheduler.wait(timeout=interval_hours * 3600)

                logger.info("[Consolidation] Scheduler stopped")

            self._scheduler_thread = threading.Thread(
                target=scheduler_loop,
                name="MemoryConsolidationScheduler",
                daemon=True,
            )
            self._scheduler_thread.start()

    def stop_scheduler(self) -> None:
        """Stop the consolidation scheduler"""
        self._stop_scheduler.set()
        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=5.0)
            self._scheduler_thread = None

    def get_last_result(self) -> Optional[ConsolidationResult]:
        """Get the result of the last consolidation run"""
        return self._last_result

    def get_stats(self) -> Dict[str, Any]:
        """Get consolidation statistics"""
        return {
            "run_count": self._run_count,
            "importance_threshold": self.importance_threshold,
            "batch_size": self.batch_size,
            "dry_run": self.dry_run,
            "scheduler_running": (
                self._scheduler_thread is not None
                and self._scheduler_thread.is_alive()
            ),
            "last_result": (
                self._last_result.to_dict()
                if self._last_result else None
            ),
        }


_consolidation_job: Optional[MemoryConsolidationJob] = None
_consolidation_lock = threading.Lock()


def get_consolidation_job(
    importance_threshold: Optional[float] = None,
    batch_size: Optional[int] = None,
    dry_run: Optional[bool] = None,
) -> Optional[MemoryConsolidationJob]:
    """
    Get or create the global MemoryConsolidationJob instance.

    Args:
        importance_threshold: Override default importance threshold
        batch_size: Override default batch size
        dry_run: Override default dry_run mode

    Returns:
        MemoryConsolidationJob instance or None if disabled
    """
    global _consolidation_job

    if _consolidation_job is not None:
        return _consolidation_job

    with _consolidation_lock:
        if _consolidation_job is not None:
            return _consolidation_job

        try:
            import os

            enabled = os.getenv(
                "ENABLE_MEMORY_CONSOLIDATION", "false"
            ).lower() == "true"

            if not enabled:
                logger.debug("[Consolidation] Memory consolidation disabled")
                return None

            threshold = importance_threshold
            if threshold is None:
                threshold = float(os.getenv(
                    "MEMORY_CONSOLIDATION_THRESHOLD",
                    str(MemoryConsolidationJob.DEFAULT_IMPORTANCE_THRESHOLD),
                ))

            batch = batch_size
            if batch is None:
                batch = int(os.getenv(
                    "MEMORY_CONSOLIDATION_BATCH_SIZE",
                    str(MemoryConsolidationJob.DEFAULT_BATCH_SIZE),
                ))

            is_dry_run = dry_run
            if is_dry_run is None:
                is_dry_run = os.getenv(
                    "MEMORY_CONSOLIDATION_DRY_RUN", "true"
                ).lower() == "true"

            interval = float(os.getenv(
                "MEMORY_CONSOLIDATION_INTERVAL_HOURS",
                str(MemoryConsolidationJob.DEFAULT_INTERVAL_HOURS),
            ))

            _consolidation_job = MemoryConsolidationJob(
                importance_threshold=threshold,
                batch_size=batch,
                dry_run=is_dry_run,
                interval_hours=interval,
            )

            logger.info(
                f"[Consolidation] Initialized (threshold={threshold}, "
                f"batch_size={batch}, dry_run={is_dry_run}, interval={interval}h)"
            )

            return _consolidation_job

        except Exception as e:
            logger.warning(f"[Consolidation] Failed to initialize: {e}")
            return None


def reset_consolidation_job() -> None:
    """Reset the global MemoryConsolidationJob singleton (for testing)"""
    global _consolidation_job
    with _consolidation_lock:
        if _consolidation_job is not None:
            _consolidation_job.stop_scheduler()
        _consolidation_job = None
