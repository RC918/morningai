"""
DeepWiki Service - Core knowledge query and retrieval service.

Issue #1824: DeepWiki 知識庫與 Session Insights

This service provides:
1. Code query capabilities - Answer questions about code using knowledge base
2. Knowledge Graph integration - Query bug/fix patterns
3. Error-fix pairs integration - Query past failures and solutions
4. Session insights - Analyze execution results and provide suggestions
5. Improvement suggestions - Generate actionable recommendations

Feature Flag: ENABLE_DEEPWIKI (default: False)
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Type

try:
    from utils.retry import retry_with_backoff, API_RETRY_CONFIG
    from utils.rate_limit import check_deepwiki_rate_limit
except ImportError:
    from orchestrator.utils.retry import retry_with_backoff, API_RETRY_CONFIG
    from orchestrator.utils.rate_limit import check_deepwiki_rate_limit

logger = logging.getLogger(__name__)


class DeepWikiQueryError(Exception):
    """Base exception for DeepWiki query errors."""
    pass


class DeepWikiTransientError(DeepWikiQueryError):
    """Transient error that may be resolved by retry."""
    pass


class DeepWikiPermanentError(DeepWikiQueryError):
    """Permanent error that should not be retried."""
    pass


DEEPWIKI_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    DeepWikiTransientError,
    ConnectionError,
    TimeoutError,
    OSError,
)


class QueryType(Enum):
    """Types of queries supported by DeepWiki."""
    CODE_QUESTION = "code_question"
    ERROR_LOOKUP = "error_lookup"
    PATTERN_SEARCH = "pattern_search"
    SESSION_INSIGHT = "session_insight"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"


@dataclass
class QueryResult:
    """Result from a DeepWiki query."""
    query_id: str
    query_type: QueryType
    question: str
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInsight:
    """Insight extracted from a session."""
    session_id: str
    insight_type: str
    summary: str
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class DeepWikiService:
    """
    DeepWiki Knowledge Base Service.
    
    Provides unified access to multiple knowledge sources:
    - Knowledge Graph (code patterns, bug/fix patterns)
    - Error-fix pairs (past failures and solutions)
    - Code embeddings (semantic code search)
    - Session data (execution results, task plans)
    """
    
    MAX_CONTEXT_LENGTH = 4000
    MAX_SOURCES = 5
    DEFAULT_CONFIDENCE_THRESHOLD = 0.5
    
    def __init__(
        self,
        enable_kg: bool = True,
        enable_error_pairs: bool = True,
        enable_embeddings: bool = True,
    ):
        """
        Initialize DeepWiki service.
        
        Args:
            enable_kg: Enable Knowledge Graph queries
            enable_error_pairs: Enable error-fix pair queries
            enable_embeddings: Enable code embedding queries
        """
        self.enable_kg = enable_kg
        self.enable_error_pairs = enable_error_pairs
        self.enable_embeddings = enable_embeddings
        
        self._kg_manager = None
        
        logger.info("[DeepWiki] Service initialized", extra={
            "operation": "init",
            "enable_kg": enable_kg,
            "enable_error_pairs": enable_error_pairs,
            "enable_embeddings": enable_embeddings,
        })
    
    def _get_kg_manager(self):
        """Lazy load Knowledge Graph manager."""
        if self._kg_manager is None and self.enable_kg:
            try:
                from agents.dev_agent.knowledge_graph.knowledge_graph_manager import (
                    get_knowledge_graph_manager
                )
                self._kg_manager = get_knowledge_graph_manager()
            except ImportError as e:
                logger.warning(f"[DeepWiki] Knowledge Graph not available: {e}")
                self.enable_kg = False
        return self._kg_manager
    
    def _generate_query_id(self) -> str:
        """Generate unique query ID using UUID for thread safety."""
        return f"dw-{uuid.uuid4()}"
    
    def query(
        self,
        question: str,
        query_type: QueryType = QueryType.CODE_QUESTION,
        language: Optional[str] = None,
        repo: Optional[str] = None,
        limit: int = 5,
        enable_rate_limit: bool = True,
        max_queries_per_minute: int = 60,
        redis_url: Optional[str] = None,
    ) -> QueryResult:
        """
        Query the DeepWiki knowledge base.
        
        Args:
            question: Natural language question or search query
            query_type: Type of query to perform
            language: Optional language filter (e.g., 'python', 'javascript')
            repo: Optional repository filter
            limit: Maximum number of sources to return
            enable_rate_limit: Enable rate limiting (default: True)
            max_queries_per_minute: Maximum queries per minute (default: 60)
            redis_url: Redis URL for rate limiting (optional)
            
        Returns:
            QueryResult with answer, sources, and confidence score
        """
        start_time = time.time()
        query_id = self._generate_query_id()
        
        # Issue #2153: Rate limiting for DeepWiki API calls
        if enable_rate_limit:
            allowed, count = check_deepwiki_rate_limit(
                query_type=query_type.value,
                max_per_minute=max_queries_per_minute,
                redis_url=redis_url,
            )
            if not allowed:
                logger.warning("[DeepWiki] Rate limited", extra={
                    "operation": "query",
                    "query_id": query_id,
                    "query_type": query_type.value,
                    "rate_limit_count": count,
                    "max_per_minute": max_queries_per_minute,
                })
                return QueryResult(
                    query_id=query_id,
                    query_type=query_type,
                    question=question,
                    answer="Rate limit exceeded. Please try again later.",
                    sources=[],
                    confidence=0.0,
                    latency_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "rate_limited": True,
                        "rate_limit_count": count,
                        "max_per_minute": max_queries_per_minute,
                    }
                )
        
        logger.info("[DeepWiki] Processing query", extra={
            "operation": "query",
            "query_id": query_id,
            "query_type": query_type.value,
            "question_length": len(question),
        })
        
        sources = []
        answer_parts = []
        total_confidence = 0.0
        source_count = 0
        
        if query_type == QueryType.ERROR_LOOKUP:
            error_sources = self._query_error_pairs(question, limit)
            sources.extend(error_sources)
            if error_sources:
                answer_parts.append(self._format_error_sources(error_sources))
                total_confidence += sum(s.get("confidence", 0) for s in error_sources)
                source_count += len(error_sources)
        
        elif query_type == QueryType.PATTERN_SEARCH:
            pattern_sources = self._query_knowledge_graph(question, language, limit)
            sources.extend(pattern_sources)
            if pattern_sources:
                answer_parts.append(self._format_pattern_sources(pattern_sources))
                total_confidence += sum(s.get("confidence", 0) for s in pattern_sources)
                source_count += len(pattern_sources)
        
        elif query_type == QueryType.CODE_QUESTION:
            error_sources = self._query_error_pairs(question, limit // 2)
            pattern_sources = self._query_knowledge_graph(question, language, limit // 2)
            
            sources.extend(error_sources)
            sources.extend(pattern_sources)
            
            if error_sources:
                answer_parts.append("## Related Past Issues:\n")
                answer_parts.append(self._format_error_sources(error_sources))
                total_confidence += sum(s.get("confidence", 0) for s in error_sources)
                source_count += len(error_sources)
            
            if pattern_sources:
                answer_parts.append("## Relevant Code Patterns:\n")
                answer_parts.append(self._format_pattern_sources(pattern_sources))
                total_confidence += sum(s.get("confidence", 0) for s in pattern_sources)
                source_count += len(pattern_sources)
        
        elif query_type == QueryType.IMPROVEMENT_SUGGESTION:
            suggestions = self._generate_improvement_suggestions(question, language)
            answer_parts.append(suggestions)
            total_confidence = 0.7
            source_count = 1
        
        answer = "\n".join(answer_parts) if answer_parts else "No relevant information found."
        avg_confidence = total_confidence / source_count if source_count > 0 else 0.0
        
        latency_ms = (time.time() - start_time) * 1000
        
        result = QueryResult(
            query_id=query_id,
            query_type=query_type,
            question=question,
            answer=answer,
            sources=sources[:self.MAX_SOURCES],
            confidence=min(avg_confidence, 1.0),
            latency_ms=latency_ms,
            metadata={
                "language": language,
                "repo": repo,
                "source_count": len(sources),
            }
        )
        
        logger.info("[DeepWiki] Query completed", extra={
            "operation": "query",
            "query_id": query_id,
            "source_count": len(sources),
            "confidence": result.confidence,
            "latency_ms": latency_ms,
        })
        
        return result
    
    def _query_error_pairs(
        self,
        query: str,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Query error-fix pairs for similar past failures."""
        if not self.enable_error_pairs:
            return []
        
        try:
            return self._query_error_pairs_with_retry(query, limit)
        except ImportError as e:
            logger.debug(f"[DeepWiki] Error-fix pairs not available: {e}")
            return []
        except Exception as e:
            logger.warning(f"[DeepWiki] Failed to query error pairs after retries: {e}")
            return []
    
    @retry_with_backoff(
        max_retries=API_RETRY_CONFIG.max_retries,
        initial_delay=API_RETRY_CONFIG.initial_delay,
        backoff_factor=API_RETRY_CONFIG.backoff_factor,
        exceptions=DEEPWIKI_RETRYABLE_EXCEPTIONS,
    )
    def _query_error_pairs_with_retry(
        self,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Internal method to query error-fix pairs with retry logic.
        
        Issue #2152: Implements exponential backoff retry for transient failures.
        """
        from observer_node import query_past_failures, DEFAULT_SIMILARITY_THRESHOLD
        
        past_failures = query_past_failures(
            error_text=query,
            limit=limit,
            threshold=DEFAULT_SIMILARITY_THRESHOLD,
        )
        
        sources = []
        for failure in past_failures:
            sources.append({
                "type": "error_fix_pair",
                "id": failure.get("id"),
                "error_text": failure.get("error_text", "")[:200],
                "fix_text": failure.get("fix_text", "")[:200],
                "error_type": failure.get("error_type"),
                "similarity": failure.get("similarity", 0),
                "confidence": failure.get("confidence_score", 0),
            })
        
        return sources
    
    def _query_knowledge_graph(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Query Knowledge Graph for relevant patterns."""
        if not self.enable_kg:
            return []
        
        kg_manager = self._get_kg_manager()
        if not kg_manager:
            return []
        
        try:
            return self._query_knowledge_graph_with_retry(kg_manager, query, language, limit)
        except Exception as e:
            logger.warning(f"[DeepWiki] Failed to query Knowledge Graph after retries: {e}")
            return []
    
    @retry_with_backoff(
        max_retries=API_RETRY_CONFIG.max_retries,
        initial_delay=API_RETRY_CONFIG.initial_delay,
        backoff_factor=API_RETRY_CONFIG.backoff_factor,
        exceptions=DEEPWIKI_RETRYABLE_EXCEPTIONS,
    )
    def _query_knowledge_graph_with_retry(
        self,
        kg_manager: Any,
        query: str,
        language: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Internal method to query Knowledge Graph with retry logic.
        
        Issue #2152: Implements exponential backoff retry for transient failures.
        """
        result = kg_manager.search_relevant_patterns(
            goal=query,
            error_context=None,
            language=language,
            limit=limit,
        )
        
        if not result.get("success"):
            return []
        
        patterns = result.get("data", {}).get("patterns", [])
        
        sources = []
        for pattern in patterns:
            sources.append({
                "type": "knowledge_graph_pattern",
                "id": pattern.get("id"),
                "pattern_name": pattern.get("pattern_name"),
                "pattern_type": pattern.get("pattern_type"),
                "pattern_template": pattern.get("pattern_template", "")[:200],
                "confidence": pattern.get("confidence_score", 0),
                "frequency": pattern.get("frequency", 0),
                "language": pattern.get("language"),
            })
        
        return sources
    
    def _format_error_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Format error-fix pair sources as readable text."""
        parts = []
        for i, source in enumerate(sources, 1):
            parts.append(f"### Issue {i}")
            parts.append(f"**Error Type:** {source.get('error_type', 'unknown')}")
            parts.append(f"**Similarity:** {source.get('similarity', 0):.2f}")
            
            error_text = source.get("error_text", "")
            if error_text:
                parts.append(f"**Error:** {error_text}")
            
            fix_text = source.get("fix_text", "")
            if fix_text and not fix_text.startswith("[PENDING]"):
                parts.append(f"**Fix:** {fix_text}")
            
            parts.append("")
        
        return "\n".join(parts)
    
    def _format_pattern_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Format Knowledge Graph pattern sources as readable text."""
        parts = []
        for i, source in enumerate(sources, 1):
            parts.append(f"### Pattern {i}: {source.get('pattern_name', 'unnamed')}")
            parts.append(f"**Type:** {source.get('pattern_type', 'unknown')}")
            parts.append(f"**Confidence:** {source.get('confidence', 0):.2f}")
            
            if source.get("language"):
                parts.append(f"**Language:** {source.get('language')}")
            
            template = source.get("pattern_template", "")
            if template:
                parts.append(f"**Description:** {template}")
            
            parts.append("")
        
        return "\n".join(parts)
    
    def _generate_improvement_suggestions(
        self,
        context: str,
        language: Optional[str] = None,
    ) -> str:
        """Generate improvement suggestions based on context."""
        suggestions = ["## Improvement Suggestions\n"]
        
        error_sources = self._query_error_pairs(context, limit=3)
        if error_sources:
            suggestions.append("### Based on Past Issues:")
            for source in error_sources:
                fix_text = source.get("fix_text", "")
                if fix_text and not fix_text.startswith("[PENDING]"):
                    suggestions.append(f"- {fix_text[:150]}")
            suggestions.append("")
        
        pattern_sources = self._query_knowledge_graph(context, language, limit=3)
        if pattern_sources:
            suggestions.append("### Based on Code Patterns:")
            for source in pattern_sources:
                template = source.get("pattern_template", "")
                if template:
                    suggestions.append(f"- {source.get('pattern_name', 'Pattern')}: {template[:150]}")
            suggestions.append("")
        
        if len(suggestions) == 1:
            suggestions.append("No specific suggestions available based on current knowledge base.")
        
        return "\n".join(suggestions)
    
    def get_session_insights(
        self,
        session_id: str,
        execution_result: Optional[Dict[str, Any]] = None,
        task_plan: Optional[Dict[str, Any]] = None,
    ) -> SessionInsight:
        """
        Get insights from a session's execution.
        
        Args:
            session_id: Session identifier
            execution_result: Optional execution result data
            task_plan: Optional task plan data
            
        Returns:
            SessionInsight with summary and recommendations
        """
        logger.info("[DeepWiki] Generating session insights", extra={
            "operation": "get_session_insights",
            "session_id": session_id,
        })
        
        recommendations = []
        metrics = {}
        summary_parts = []
        
        if execution_result:
            status = execution_result.get("status", "unknown")
            summary_parts.append(f"Execution Status: {status}")
            metrics["status"] = status
            
            if status == "error" or status == "failed":
                error = execution_result.get("error", "")
                if error:
                    error_sources = self._query_error_pairs(error, limit=2)
                    for source in error_sources:
                        fix_text = source.get("fix_text", "")
                        if fix_text and not fix_text.startswith("[PENDING]"):
                            recommendations.append(f"Consider: {fix_text[:100]}")
            
            tasks_completed = execution_result.get("tasks_completed", 0)
            tasks_failed = execution_result.get("tasks_failed", 0)
            metrics["tasks_completed"] = tasks_completed
            metrics["tasks_failed"] = tasks_failed
            
            if tasks_failed > 0:
                recommendations.append(
                    f"Review the {tasks_failed} failed task(s) for potential improvements"
                )
        
        if task_plan:
            plan_steps = task_plan.get("steps", [])
            metrics["plan_steps"] = len(plan_steps)
            summary_parts.append(f"Plan Steps: {len(plan_steps)}")
        
        if not recommendations:
            recommendations.append("No specific recommendations at this time")
        
        summary = "; ".join(summary_parts) if summary_parts else "Session analysis complete"
        
        return SessionInsight(
            session_id=session_id,
            insight_type="execution_analysis",
            summary=summary,
            recommendations=recommendations,
            metrics=metrics,
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and dependencies."""
        health = {
            "service": "deepwiki",
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "knowledge_graph": {
                    "enabled": self.enable_kg,
                    "available": False,
                },
                "error_pairs": {
                    "enabled": self.enable_error_pairs,
                    "available": False,
                },
                "embeddings": {
                    "enabled": self.enable_embeddings,
                    "available": False,
                },
            }
        }
        
        if self.enable_kg:
            try:
                kg_manager = self._get_kg_manager()
                if kg_manager:
                    kg_health = kg_manager.health_check()
                    health["components"]["knowledge_graph"]["available"] = kg_health.get("success", False)
            except Exception as e:
                health["components"]["knowledge_graph"]["error"] = str(e)
        
        if self.enable_error_pairs:
            try:
                from observer_node import query_past_failures
                health["components"]["error_pairs"]["available"] = True
            except ImportError:
                pass
        
        unhealthy_components = [
            name for name, comp in health["components"].items()
            if comp["enabled"] and not comp["available"]
        ]
        
        if unhealthy_components:
            health["status"] = "degraded"
            health["unhealthy_components"] = unhealthy_components
        
        return health


_deepwiki_service: Optional[DeepWikiService] = None
_deepwiki_service_lock = threading.Lock()


def get_deepwiki_service() -> DeepWikiService:
    """
    Get or create the DeepWiki service singleton.
    
    Uses double-checked locking pattern for thread safety.
    
    Returns:
        DeepWikiService instance
    """
    global _deepwiki_service
    
    # First check without lock (fast path)
    if _deepwiki_service is not None:
        return _deepwiki_service
    
    # Acquire lock for thread-safe initialization
    with _deepwiki_service_lock:
        # Double-check after acquiring lock
        if _deepwiki_service is None:
            try:
                from common.config.settings import settings
                
                if not getattr(settings, 'enable_deepwiki', False):
                    logger.warning("[DeepWiki] Service disabled via ENABLE_DEEPWIKI flag")
                
                _deepwiki_service = DeepWikiService(
                    enable_kg=getattr(settings, 'enable_knowledge_graph_learning', False),
                    enable_error_pairs=getattr(settings, 'enable_failure_learning_context', True),
                    enable_embeddings=True,
                )
            except ImportError:
                _deepwiki_service = DeepWikiService()
    
    return _deepwiki_service
