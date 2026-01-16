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

import asyncio
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

    def score_batch(
        self,
        entries: List[MemoryEntry],
    ) -> List[ImportanceScore]:
        """
        Calculate importance scores for multiple entries in batch.

        Issue #3976: Batch novelty calculation to reduce N+1 queries.
        Instead of calling search() for each entry, we batch all queries
        and perform a single search operation.

        Args:
            entries: List of memory entries to score

        Returns:
            List of ImportanceScore objects in same order as input
        """
        if not entries:
            return []

        novelty_scores = self._calculate_novelty_batch(entries)

        scores = []
        for i, entry in enumerate(entries):
            metadata = entry.metadata or {}

            debate_confidence = self._extract_debate_confidence(entry, metadata)
            outcome_impact = self._extract_outcome_impact(entry, metadata)
            novelty_score = novelty_scores[i]
            reference_count = self._calculate_reference_score(entry, metadata)

            scores.append(ImportanceScore(
                debate_confidence=debate_confidence,
                outcome_impact=outcome_impact,
                novelty_score=novelty_score,
                reference_count=reference_count,
            ))

        return scores

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

    def _calculate_novelty_batch(
        self,
        entries: List[MemoryEntry],
    ) -> List[float]:
        """
        Calculate novelty scores for multiple entries in batch.

        Issue #3976: Instead of N separate search() calls (N+1 pattern),
        we combine all queries and perform a single batch search.

        Args:
            entries: List of memory entries to calculate novelty for

        Returns:
            List of novelty scores in same order as input entries
        """
        if self.memory is None:
            return [0.5] * len(entries)

        if not entries:
            return []

        try:
            queries = [entry.content[:200] for entry in entries]

            combined_query = " ".join(queries[:10])

            existing = self.memory.search(
                query=combined_query,
                layers=[MemoryLayer.KNOWLEDGE_BASE],
                limit=len(entries) * 3,
            )

            if not existing:
                return [1.0] * len(entries)

            novelty_scores = []
            for entry in entries:
                entry_query = entry.content[:200].lower()

                max_similarity = 0.0
                for e in existing:
                    if entry_query[:50] in e.content.lower():
                        max_similarity = max(max_similarity, e.similarity or 0.0)
                    elif e.similarity and e.similarity > max_similarity:
                        content_overlap = sum(
                            1 for word in entry_query.split()[:10]
                            if word in e.content.lower()
                        )
                        if content_overlap >= 3:
                            max_similarity = max(
                                max_similarity,
                                (e.similarity or 0.0) * 0.8
                            )

                novelty_scores.append(max(0.0, 1.0 - max_similarity))

            return novelty_scores

        except Exception as e:
            logger.debug(f"[Consolidation] Batch novelty check failed: {e}")
            return [0.5] * len(entries)

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

    Issue #3977: Async LLM summarization pipeline
    Issue #3998: Token bucket algorithm for rate limiting
    Issue #3999: Refactored to use separate ConcurrencyManager and TokenBucketRateLimiter (SRP)

    - Supports both sync and async summarization
    - Batch processing for multiple memories
    - Token bucket rate limiting for smooth request distribution
    - Reusable concurrency control via ConcurrencyManager
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

    # Issue #3977: Default concurrency and rate limiting settings
    # Issue #3998: Token bucket defaults (capacity=10, refill_rate=5/sec)
    DEFAULT_MAX_CONCURRENCY = 5
    DEFAULT_RATE_LIMIT_DELAY = 0.2  # seconds between requests (legacy)
    DEFAULT_TOKEN_BUCKET_CAPACITY = 10.0
    DEFAULT_TOKEN_BUCKET_REFILL_RATE = 5.0  # tokens per second

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
        token_bucket_capacity: Optional[float] = None,
        token_bucket_refill_rate: Optional[float] = None,
    ):
        self.model = model
        self.max_concurrency = max_concurrency
        self.rate_limit_delay = rate_limit_delay
        self._client = None

        # Issue #3998: Token bucket rate limiter (replaces simple time-sleep)
        # Issue #3999: Extracted to separate ConcurrencyManager and TokenBucketRateLimiter
        try:
            from memory.concurrency import (
                TokenBucketRateLimiter,
                ConcurrencyManager,
            )
            self._rate_limiter = TokenBucketRateLimiter(
                capacity=token_bucket_capacity or self.DEFAULT_TOKEN_BUCKET_CAPACITY,
                refill_rate=token_bucket_refill_rate or self.DEFAULT_TOKEN_BUCKET_REFILL_RATE,
            )
            self._concurrency_manager = ConcurrencyManager(
                max_concurrency=max_concurrency,
            )
            self._use_token_bucket = True
        except ImportError:
            # Fallback to legacy rate limiting if concurrency module not available
            logger.warning(
                "[LLMSummarizer] Could not import concurrency module, "
                "falling back to legacy rate limiting"
            )
            self._rate_limiter = None
            self._concurrency_manager = None
            self._use_token_bucket = False
            self._semaphore: Optional[asyncio.Semaphore] = None
            self._rate_limit_lock: Optional[asyncio.Lock] = None
            self._last_request_time = 0.0

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

    def _sanitize_for_prompt(self, text: str) -> str:
        """
        Sanitize text to prevent prompt injection attacks.

        Issue #4042: Prompt injection sanitization for LLMSummarizer.

        This method neutralizes common prompt injection patterns that could
        manipulate the LLM's behavior or corrupt the Knowledge Base.

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text safe for use in LLM prompts
        """
        if not text:
            return ""

        import re
        sanitized = text
        sanitization_applied = []

        # Remove/escape chat template delimiters that could confuse the LLM
        # These are common injection vectors
        delimiter_patterns = [
            (r"<\|im_start\|>", "[IM_START]", "im_start_delimiter"),
            (r"<\|im_end\|>", "[IM_END]", "im_end_delimiter"),
            (r"\[INST\]", "[INST_TAG]", "inst_delimiter"),
            (r"\[/INST\]", "[/INST_TAG]", "inst_end_delimiter"),
            (r"<<SYS>>", "[SYS_START]", "sys_start_delimiter"),
            (r"<</SYS>>", "[SYS_END]", "sys_end_delimiter"),
            (r"```system", "```code_system", "system_code_block"),
            (r"```assistant", "```code_assistant", "assistant_code_block"),
            (r"```user", "```code_user", "user_code_block"),
        ]

        for pattern, replacement, name in delimiter_patterns:
            if re.search(pattern, sanitized, flags=re.IGNORECASE):
                sanitized = re.sub(
                    pattern, replacement, sanitized, flags=re.IGNORECASE
                )
                sanitization_applied.append(name)

        # Neutralize instruction override attempts
        instruction_patterns = [
            (r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+"
             r"(instructions?|prompts?|rules?)",
             "[FILTERED: instruction override attempt]",
             "instruction_override"),
            (r"(?i)new\s+instruction\s*:",
             "[FILTERED: new instruction attempt]:",
             "new_instruction"),
            (r"(?i)system\s*:\s*you\s+are",
             "[FILTERED: system prompt attempt]",
             "system_prompt"),
        ]

        for pattern, replacement, name in instruction_patterns:
            if re.search(pattern, sanitized):
                sanitized = re.sub(pattern, replacement, sanitized)
                sanitization_applied.append(name)

        # Escape triple backticks that might break prompt formatting
        # Replace with single backticks to preserve code indication
        if "```" in sanitized:
            sanitized = sanitized.replace("```", "'''")
            sanitization_applied.append("triple_backticks")

        # Limit consecutive newlines to prevent prompt structure manipulation
        if re.search(r"\n{4,}", sanitized):
            sanitized = re.sub(r"\n{4,}", "\n\n\n", sanitized)
            sanitization_applied.append("excessive_newlines")

        # Log sanitization actions for debuggability
        if sanitization_applied:
            logger.debug(
                "[LLMSummarizer] Sanitization applied: %s (text_len=%d)",
                ", ".join(sanitization_applied),
                len(text),
            )

        return sanitized

    def summarize(
        self,
        entry: MemoryEntry,
        memory_type: MemoryType = MemoryType.GENERAL,
    ) -> Optional[Dict[str, Any]]:
        """
        Summarize a memory entry using LLM (synchronous).

        Issue #4042: Added prompt injection sanitization for content and metadata.

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
            # Issue #4042: Sanitize content and metadata before using in prompt
            sanitized_content = self._sanitize_for_prompt(entry.content[:2000])
            sanitized_metadata = self._sanitize_for_prompt(
                json.dumps(entry.metadata or {}, indent=2)[:500]
            )

            prompt = self.SUMMARIZATION_PROMPT.format(
                content=sanitized_content,
                metadata=sanitized_metadata,
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

    async def summarize_async(
        self,
        entry: MemoryEntry,
        memory_type: MemoryType = MemoryType.GENERAL,
    ) -> Optional[Dict[str, Any]]:
        """
        Summarize a memory entry using LLM (asynchronous).

        Issue #3977: Async LLM summarization pipeline
        Issue #3998: Token bucket rate limiting for smooth request distribution
        Issue #3999: Uses ConcurrencyManager for SRP compliance

        Args:
            entry: Memory entry to summarize
            memory_type: Type classification for the memory

        Returns:
            Dictionary with summary, keywords, and memory_type
        """
        if self._use_token_bucket:
            # Issue #3998/#3999: Use token bucket + concurrency manager
            async with await self._concurrency_manager.acquire():
                # Acquire rate limit token (waits if bucket empty)
                await self._rate_limiter.acquire_async()

                # Run synchronous summarize in thread pool
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None,
                    self.summarize,
                    entry,
                    memory_type,
                )
        else:
            # Legacy fallback: simple time-sleep rate limiting
            # Initialize semaphore for concurrency control
            if self._semaphore is None:
                self._semaphore = asyncio.Semaphore(self.max_concurrency)

            # Initialize rate limit lock for thread-safe access
            if self._rate_limit_lock is None:
                self._rate_limit_lock = asyncio.Lock()

            async with self._semaphore:
                # Rate limiting with lock to prevent race conditions
                async with self._rate_limit_lock:
                    # Use monotonic clock for reliable rate limiting
                    current_time = time.monotonic()
                    time_since_last = current_time - self._last_request_time
                    if time_since_last < self.rate_limit_delay:
                        await asyncio.sleep(self.rate_limit_delay - time_since_last)
                    self._last_request_time = time.monotonic()

                # Run synchronous summarize in thread pool
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None,
                    self.summarize,
                    entry,
                    memory_type,
                )

    async def summarize_batch_async(
        self,
        entries: List[Tuple[MemoryEntry, MemoryType]],
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Summarize multiple memory entries concurrently.

        Issue #3977: Async LLM summarization pipeline with batching

        Args:
            entries: List of (MemoryEntry, MemoryType) tuples

        Returns:
            List of summarization results (same order as input)
        """
        if not entries:
            return []

        logger.info(
            f"[Consolidation] Starting batch summarization of {len(entries)} entries "
            f"(max_concurrency={self.max_concurrency})"
        )

        tasks = [
            self.summarize_async(entry, memory_type)
            for entry, memory_type in entries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None and log them
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    f"[Consolidation] Batch summarization failed for entry {i}: {result}"
                )
                entry, memory_type = entries[i]
                processed_results.append(self._fallback_summarize(entry, memory_type))
            else:
                processed_results.append(result)

        logger.info(
            f"[Consolidation] Batch summarization completed: "
            f"{len([r for r in processed_results if r])} successful"
        )

        return processed_results

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

    def get_stats(self) -> Dict[str, Any]:
        """
        Get LLMSummarizer statistics.

        Issue #3998/#3999: Exposes rate limiter and concurrency manager stats.

        Returns:
            Dictionary with rate limiter and concurrency stats
        """
        stats = {
            "model": self.model,
            "max_concurrency": self.max_concurrency,
            "use_token_bucket": self._use_token_bucket,
        }

        if self._use_token_bucket and self._rate_limiter:
            stats["rate_limiter"] = self._rate_limiter.get_stats()
        if self._use_token_bucket and self._concurrency_manager:
            stats["concurrency_manager"] = self._concurrency_manager.get_stats()

        return stats


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

            # Issue #3976: Use batch scoring to reduce N+1 queries
            scores = self.scoring_engine.score_batch(expiring_memories)
            result.memories_evaluated = len(expiring_memories)

            important_memories = []
            for entry, score in zip(expiring_memories, scores):
                if score.total >= self.importance_threshold:
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
                        # Skip entries with malformed expiration timestamps
                        # We can't determine if they're expiring, so don't consolidate
                        logger.debug(
                            f"[Consolidation] Skipping entry with invalid expires_at: "
                            f"{entry.key}"
                        )
                # Skip memories without expiration timestamp
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

    # Issue #3978: Pattern definitions for content-based classification
    _CONTENT_PATTERNS: Dict[MemoryType, List[Tuple[str, float]]] = {
        MemoryType.DEBATE_INSIGHT: [
            ("debate", 2.0),
            ("argument", 1.5),
            ("consensus", 1.5),
            ("winning", 1.0),
            ("agent voted", 1.5),
            ("disagreement", 1.0),
        ],
        MemoryType.ERROR_FIX_PAIR: [
            ("error", 1.5),
            ("exception", 1.5),
            ("fix", 1.5),
            ("resolved", 1.0),
            ("traceback", 2.0),
            ("bug", 1.5),
            ("failed", 1.0),
            ("solution", 1.0),
        ],
        MemoryType.ROUTING_DECISION: [
            ("routing", 2.0),
            ("provider", 1.5),
            ("model selection", 2.0),
            ("fallback", 1.5),
            ("latency", 1.0),
            ("cost optimization", 1.5),
        ],
        MemoryType.SAFETY_PATTERN: [
            ("safety", 2.0),
            ("compliance", 2.0),
            ("pii", 1.5),
            ("sensitive", 1.0),
            ("blocked", 1.5),
            ("violation", 1.5),
            ("policy", 1.0),
        ],
        MemoryType.FLOW_EXECUTION: [
            ("flow", 1.5),
            ("execution", 1.5),
            ("plan", 1.5),
            ("step", 1.0),
            ("workflow", 2.0),
            ("task completed", 1.5),
        ],
        MemoryType.SOLUTION_PATTERN: [
            ("solution", 1.5),
            ("pattern", 1.5),
            ("approach", 1.0),
            ("best practice", 2.0),
            ("recommendation", 1.5),
            ("learned", 1.0),
        ],
    }

    # Issue #3978: Source layer to memory type mapping
    _LAYER_TYPE_MAP: Dict[str, MemoryType] = {
        "governance": MemoryType.SAFETY_PATTERN,
        "debate": MemoryType.DEBATE_INSIGHT,
        "routing": MemoryType.ROUTING_DECISION,
        "planner": MemoryType.FLOW_EXECUTION,
        "executor": MemoryType.FLOW_EXECUTION,
    }

    def _classify_by_explicit_type(self, metadata: Dict[str, Any]) -> Optional[MemoryType]:
        """Check for explicit type in metadata (Factor 1)."""
        explicit_type = metadata.get("memory_type") or metadata.get("type")
        if explicit_type:
            try:
                return MemoryType(explicit_type)
            except ValueError:
                pass
        return None

    def _classify_by_source_layer(self, metadata: Dict[str, Any]) -> Optional[MemoryType]:
        """Check source layer indicators (Factor 2)."""
        source_layer = metadata.get("source_layer") or metadata.get("layer")
        # Ensure source_layer is a string before calling .lower()
        if source_layer and isinstance(source_layer, str):
            if source_layer.lower() in self._LAYER_TYPE_MAP:
                return self._LAYER_TYPE_MAP[source_layer.lower()]
        return None

    def _classify_by_metadata_schema(self, metadata: Dict[str, Any]) -> Optional[MemoryType]:
        """Check metadata schema patterns (Factor 3)."""
        if "debate_id" in metadata or "winning_agent" in metadata:
            return MemoryType.DEBATE_INSIGHT
        if "error_type" in metadata or "stack_trace" in metadata:
            return MemoryType.ERROR_FIX_PAIR
        if "fix_applied" in metadata or "resolution" in metadata:
            return MemoryType.ERROR_FIX_PAIR
        if "provider" in metadata and "model" in metadata:
            if "latency" in metadata or "cost" in metadata:
                return MemoryType.ROUTING_DECISION
        if "safety_score" in metadata or "compliance_check" in metadata:
            return MemoryType.SAFETY_PATTERN
        if "plan_id" in metadata or "flow_id" in metadata:
            return MemoryType.FLOW_EXECUTION
        if "task_id" in metadata and "execution_time" in metadata:
            return MemoryType.FLOW_EXECUTION
        return None

    def _classify_by_content_patterns(self, content_lower: str) -> Optional[MemoryType]:
        """Classify using weighted content pattern scoring (Factor 4)."""
        type_scores: Dict[MemoryType, float] = {t: 0.0 for t in MemoryType}

        for memory_type, patterns in self._CONTENT_PATTERNS.items():
            for pattern, weight in patterns:
                if pattern in content_lower:
                    type_scores[memory_type] += weight

        max_score = max(type_scores.values())
        if max_score >= 2.0:
            for memory_type, score in type_scores.items():
                if score == max_score:
                    return memory_type
        return None

    def _classify_memory_type(self, entry: MemoryEntry) -> MemoryType:
        """
        Classify memory type using multi-factor approach.

        Issue #3978: More robust memory type classification

        Classification factors (in priority order):
        1. Explicit type in metadata (highest confidence)
        2. Source layer indicators
        3. Metadata schema patterns
        4. Content pattern analysis (weighted scoring)

        Args:
            entry: Memory entry to classify

        Returns:
            MemoryType classification
        """
        metadata = entry.metadata or {}

        # Factor 1: Explicit type in metadata (highest priority)
        result = self._classify_by_explicit_type(metadata)
        if result:
            return result

        # Factor 2: Source layer indicators
        result = self._classify_by_source_layer(metadata)
        if result:
            return result

        # Factor 3: Metadata schema patterns
        result = self._classify_by_metadata_schema(metadata)
        if result:
            return result

        # Factor 4: Content pattern analysis with weighted scoring
        content_lower = entry.content.lower()
        result = self._classify_by_content_patterns(content_lower)
        if result:
            return result

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
