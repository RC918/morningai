"""
Tests for DeepWiki Service.

Issue #1824: DeepWiki 知識庫與 Session Insights
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deepwiki.service import (
    DeepWikiService,
    QueryType,
    QueryResult,
    SessionInsight,
    get_deepwiki_service,
)


class TestQueryType:
    """Tests for QueryType enum."""

    def test_query_type_values(self):
        """Test QueryType enum has expected values."""
        assert QueryType.CODE_QUESTION.value == "code_question"
        assert QueryType.ERROR_LOOKUP.value == "error_lookup"
        assert QueryType.PATTERN_SEARCH.value == "pattern_search"
        assert QueryType.SESSION_INSIGHT.value == "session_insight"
        assert QueryType.IMPROVEMENT_SUGGESTION.value == "improvement_suggestion"

    def test_query_type_count(self):
        """Test QueryType has expected number of values."""
        assert len(QueryType) == 5


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_query_result_creation(self):
        """Test QueryResult can be created with required fields."""
        result = QueryResult(
            query_id="test-123",
            query_type=QueryType.CODE_QUESTION,
            question="How do I fix this error?",
            answer="Try checking the logs.",
        )
        assert result.query_id == "test-123"
        assert result.query_type == QueryType.CODE_QUESTION
        assert result.question == "How do I fix this error?"
        assert result.answer == "Try checking the logs."
        assert result.sources == []
        assert result.confidence == 0.0
        assert result.latency_ms == 0.0
        assert result.metadata == {}

    def test_query_result_with_all_fields(self):
        """Test QueryResult with all fields populated."""
        result = QueryResult(
            query_id="test-456",
            query_type=QueryType.ERROR_LOOKUP,
            question="What causes TypeError?",
            answer="Type mismatch in function call.",
            sources=[{"type": "error_fix_pair", "id": "1"}],
            confidence=0.85,
            latency_ms=150.5,
            metadata={"language": "python"},
        )
        assert result.confidence == 0.85
        assert result.latency_ms == 150.5
        assert len(result.sources) == 1
        assert result.metadata["language"] == "python"


class TestSessionInsight:
    """Tests for SessionInsight dataclass."""

    def test_session_insight_creation(self):
        """Test SessionInsight can be created with required fields."""
        insight = SessionInsight(
            session_id="session-123",
            insight_type="execution_analysis",
            summary="Task completed successfully",
        )
        assert insight.session_id == "session-123"
        assert insight.insight_type == "execution_analysis"
        assert insight.summary == "Task completed successfully"
        assert insight.recommendations == []
        assert insight.metrics == {}

    def test_session_insight_with_all_fields(self):
        """Test SessionInsight with all fields populated."""
        insight = SessionInsight(
            session_id="session-456",
            insight_type="failure_analysis",
            summary="Task failed due to timeout",
            recommendations=["Increase timeout", "Check network"],
            metrics={"duration_ms": 5000, "retries": 3},
        )
        assert len(insight.recommendations) == 2
        assert insight.metrics["duration_ms"] == 5000


class TestDeepWikiService:
    """Tests for DeepWikiService class."""

    def test_service_initialization_default(self):
        """Test service initializes with default settings."""
        service = DeepWikiService()
        assert service.enable_kg is True
        assert service.enable_error_pairs is True
        assert service.enable_embeddings is True
        assert service._kg_manager is None

    def test_service_initialization_custom(self):
        """Test service initializes with custom settings."""
        service = DeepWikiService(
            enable_kg=False,
            enable_error_pairs=False,
            enable_embeddings=False,
        )
        assert service.enable_kg is False
        assert service.enable_error_pairs is False
        assert service.enable_embeddings is False

    def test_generate_query_id(self):
        """Test query ID generation is unique."""
        service = DeepWikiService()
        id1 = service._generate_query_id()
        id2 = service._generate_query_id()
        
        assert id1.startswith("dw-")
        assert id2.startswith("dw-")
        assert id1 != id2

    def test_query_code_question_no_sources(self):
        """Test CODE_QUESTION query when no sources available."""
        service = DeepWikiService(enable_kg=False, enable_error_pairs=False)
        
        result = service.query(
            question="How do I implement a singleton?",
            query_type=QueryType.CODE_QUESTION,
        )
        
        assert isinstance(result, QueryResult)
        assert result.query_type == QueryType.CODE_QUESTION
        assert result.answer == "No relevant information found."
        assert result.sources == []
        assert result.confidence == 0.0

    def test_query_error_lookup_no_sources(self):
        """Test ERROR_LOOKUP query when no sources available."""
        service = DeepWikiService(enable_error_pairs=False)
        
        result = service.query(
            question="TypeError: cannot read property",
            query_type=QueryType.ERROR_LOOKUP,
        )
        
        assert result.query_type == QueryType.ERROR_LOOKUP
        assert result.answer == "No relevant information found."

    def test_query_pattern_search_no_sources(self):
        """Test PATTERN_SEARCH query when no sources available."""
        service = DeepWikiService(enable_kg=False)
        
        result = service.query(
            question="retry pattern",
            query_type=QueryType.PATTERN_SEARCH,
        )
        
        assert result.query_type == QueryType.PATTERN_SEARCH
        assert result.answer == "No relevant information found."

    def test_query_improvement_suggestion(self):
        """Test IMPROVEMENT_SUGGESTION query."""
        service = DeepWikiService(enable_kg=False, enable_error_pairs=False)
        
        result = service.query(
            question="How can I improve error handling?",
            query_type=QueryType.IMPROVEMENT_SUGGESTION,
        )
        
        assert result.query_type == QueryType.IMPROVEMENT_SUGGESTION
        assert "Improvement Suggestions" in result.answer
        assert result.confidence == 0.7

    def test_query_latency_tracking(self):
        """Test query latency is tracked."""
        service = DeepWikiService(enable_kg=False, enable_error_pairs=False)
        
        result = service.query(
            question="test query",
            query_type=QueryType.CODE_QUESTION,
        )
        
        assert result.latency_ms > 0

    def test_query_metadata(self):
        """Test query metadata is populated."""
        service = DeepWikiService(enable_kg=False, enable_error_pairs=False)
        
        result = service.query(
            question="test query",
            query_type=QueryType.CODE_QUESTION,
            language="python",
            repo="test/repo",
        )
        
        assert result.metadata["language"] == "python"
        assert result.metadata["repo"] == "test/repo"

    @patch("deepwiki.service.DeepWikiService._query_error_pairs")
    def test_query_error_lookup_with_sources(self, mock_query_error_pairs):
        """Test ERROR_LOOKUP query with sources."""
        mock_query_error_pairs.return_value = [
            {
                "type": "error_fix_pair",
                "id": "1",
                "error_text": "TypeError: cannot read property",
                "fix_text": "Check if object is null before accessing",
                "error_type": "TypeError",
                "similarity": 0.9,
                "confidence": 0.85,
            }
        ]
        
        service = DeepWikiService()
        result = service.query(
            question="TypeError: cannot read property",
            query_type=QueryType.ERROR_LOOKUP,
        )
        
        assert len(result.sources) == 1
        assert result.sources[0]["type"] == "error_fix_pair"
        assert result.confidence > 0

    @patch("deepwiki.service.DeepWikiService._query_knowledge_graph")
    def test_query_pattern_search_with_sources(self, mock_query_kg):
        """Test PATTERN_SEARCH query with sources."""
        mock_query_kg.return_value = [
            {
                "type": "knowledge_graph_pattern",
                "id": "1",
                "pattern_name": "Retry Pattern",
                "pattern_type": "resilience",
                "pattern_template": "Implement exponential backoff",
                "confidence": 0.8,
                "frequency": 10,
                "language": "python",
            }
        ]
        
        service = DeepWikiService()
        result = service.query(
            question="retry pattern",
            query_type=QueryType.PATTERN_SEARCH,
            language="python",
        )
        
        assert len(result.sources) == 1
        assert result.sources[0]["type"] == "knowledge_graph_pattern"


class TestDeepWikiServiceErrorPairs:
    """Tests for error-fix pair querying."""

    def test_query_error_pairs_disabled(self):
        """Test error pairs query when disabled."""
        service = DeepWikiService(enable_error_pairs=False)
        result = service._query_error_pairs("test error")
        assert result == []

    def test_query_error_pairs_success(self):
        """Test successful error pairs query."""
        mock_observer = MagicMock()
        mock_observer.query_past_failures.return_value = [
            {
                "id": "1",
                "error_text": "Connection timeout",
                "fix_text": "Increase timeout value",
                "error_type": "TimeoutError",
                "similarity": 0.85,
                "confidence_score": 0.9,
            }
        ]
        mock_observer.DEFAULT_SIMILARITY_THRESHOLD = 0.6
        
        service = DeepWikiService()
        with patch.dict("sys.modules", {"observer_node": mock_observer}):
            result = service._query_error_pairs("Connection timeout")
        
        assert len(result) == 1
        assert result[0]["type"] == "error_fix_pair"
        assert result[0]["error_type"] == "TimeoutError"

    def test_query_error_pairs_import_error(self):
        """Test error pairs query handles import error gracefully."""
        service = DeepWikiService()
        result = service._query_error_pairs("test error")
        assert result == []


class TestDeepWikiServiceKnowledgeGraph:
    """Tests for Knowledge Graph querying."""

    def test_query_kg_disabled(self):
        """Test KG query when disabled."""
        service = DeepWikiService(enable_kg=False)
        result = service._query_knowledge_graph("test query")
        assert result == []

    def test_query_kg_no_manager(self):
        """Test KG query when manager not available."""
        service = DeepWikiService()
        service._kg_manager = None
        service.enable_kg = False
        result = service._query_knowledge_graph("test query")
        assert result == []

    @patch("deepwiki.service.DeepWikiService._get_kg_manager")
    def test_query_kg_success(self, mock_get_manager):
        """Test successful KG query."""
        mock_manager = Mock()
        mock_manager.search_relevant_patterns.return_value = {
            "success": True,
            "data": {
                "patterns": [
                    {
                        "id": "1",
                        "pattern_name": "Singleton",
                        "pattern_type": "creational",
                        "pattern_template": "Ensure single instance",
                        "confidence_score": 0.9,
                        "frequency": 5,
                        "language": "python",
                    }
                ]
            }
        }
        mock_get_manager.return_value = mock_manager
        
        service = DeepWikiService()
        result = service._query_knowledge_graph("singleton pattern", "python", 3)
        
        assert len(result) == 1
        assert result[0]["pattern_name"] == "Singleton"

    @patch("deepwiki.service.DeepWikiService._get_kg_manager")
    def test_query_kg_failure(self, mock_get_manager):
        """Test KG query handles failure gracefully."""
        mock_manager = Mock()
        mock_manager.search_relevant_patterns.return_value = {"success": False}
        mock_get_manager.return_value = mock_manager
        
        service = DeepWikiService()
        result = service._query_knowledge_graph("test query")
        
        assert result == []


class TestDeepWikiServiceFormatting:
    """Tests for source formatting methods."""

    def test_format_error_sources_empty(self):
        """Test formatting empty error sources."""
        service = DeepWikiService()
        result = service._format_error_sources([])
        assert result == ""

    def test_format_error_sources_single(self):
        """Test formatting single error source."""
        service = DeepWikiService()
        sources = [
            {
                "error_type": "TypeError",
                "similarity": 0.85,
                "error_text": "Cannot read property",
                "fix_text": "Check for null",
            }
        ]
        result = service._format_error_sources(sources)
        
        assert "Issue 1" in result
        assert "TypeError" in result
        assert "0.85" in result
        assert "Cannot read property" in result
        assert "Check for null" in result

    def test_format_error_sources_pending_fix(self):
        """Test formatting error source with pending fix."""
        service = DeepWikiService()
        sources = [
            {
                "error_type": "ValueError",
                "similarity": 0.7,
                "error_text": "Invalid value",
                "fix_text": "[PENDING] Fix not yet available",
            }
        ]
        result = service._format_error_sources(sources)
        
        assert "Invalid value" in result
        assert "[PENDING]" not in result

    def test_format_pattern_sources_empty(self):
        """Test formatting empty pattern sources."""
        service = DeepWikiService()
        result = service._format_pattern_sources([])
        assert result == ""

    def test_format_pattern_sources_single(self):
        """Test formatting single pattern source."""
        service = DeepWikiService()
        sources = [
            {
                "pattern_name": "Factory",
                "pattern_type": "creational",
                "confidence": 0.9,
                "language": "python",
                "pattern_template": "Create objects without specifying class",
            }
        ]
        result = service._format_pattern_sources(sources)
        
        assert "Factory" in result
        assert "creational" in result
        assert "0.90" in result
        assert "python" in result


class TestDeepWikiServiceSessionInsights:
    """Tests for session insights functionality."""

    def test_get_session_insights_minimal(self):
        """Test session insights with minimal data."""
        service = DeepWikiService()
        insight = service.get_session_insights("session-123")
        
        assert isinstance(insight, SessionInsight)
        assert insight.session_id == "session-123"
        assert insight.insight_type == "execution_analysis"
        assert "No specific recommendations" in insight.recommendations[0]

    def test_get_session_insights_with_success(self):
        """Test session insights with successful execution."""
        service = DeepWikiService()
        execution_result = {
            "status": "success",
            "tasks_completed": 5,
            "tasks_failed": 0,
        }
        
        insight = service.get_session_insights(
            "session-123",
            execution_result=execution_result,
        )
        
        assert insight.metrics["status"] == "success"
        assert insight.metrics["tasks_completed"] == 5
        assert insight.metrics["tasks_failed"] == 0

    def test_get_session_insights_with_failure(self):
        """Test session insights with failed execution."""
        service = DeepWikiService(enable_error_pairs=False)
        execution_result = {
            "status": "failed",
            "error": "Connection timeout",
            "tasks_completed": 2,
            "tasks_failed": 3,
        }
        
        insight = service.get_session_insights(
            "session-123",
            execution_result=execution_result,
        )
        
        assert insight.metrics["status"] == "failed"
        assert insight.metrics["tasks_failed"] == 3
        assert any("failed task" in r.lower() for r in insight.recommendations)

    def test_get_session_insights_with_task_plan(self):
        """Test session insights with task plan."""
        service = DeepWikiService()
        task_plan = {
            "steps": [
                {"name": "step1"},
                {"name": "step2"},
                {"name": "step3"},
            ]
        }
        
        insight = service.get_session_insights(
            "session-123",
            task_plan=task_plan,
        )
        
        assert insight.metrics["plan_steps"] == 3


class TestDeepWikiServiceHealthCheck:
    """Tests for health check functionality."""

    def test_health_check_all_disabled(self):
        """Test health check with all components disabled."""
        service = DeepWikiService(
            enable_kg=False,
            enable_error_pairs=False,
            enable_embeddings=False,
        )
        
        health = service.health_check()
        
        assert health["service"] == "deepwiki"
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert not health["components"]["knowledge_graph"]["enabled"]
        assert not health["components"]["error_pairs"]["enabled"]

    def test_health_check_degraded(self):
        """Test health check returns degraded when components unavailable."""
        service = DeepWikiService(enable_kg=True, enable_error_pairs=True)
        
        health = service.health_check()
        
        assert health["status"] == "degraded"
        assert "unhealthy_components" in health

    @patch("deepwiki.service.DeepWikiService._get_kg_manager")
    def test_health_check_kg_available(self, mock_get_manager):
        """Test health check with KG available."""
        mock_manager = Mock()
        mock_manager.health_check.return_value = {"success": True}
        mock_get_manager.return_value = mock_manager
        
        service = DeepWikiService(enable_kg=True, enable_error_pairs=False)
        health = service.health_check()
        
        assert health["components"]["knowledge_graph"]["available"] is True


class TestGetDeepWikiService:
    """Tests for get_deepwiki_service singleton factory."""

    def test_get_deepwiki_service_creates_instance(self):
        """Test factory creates service instance."""
        import deepwiki.service as service_module
        service_module._deepwiki_service = None
        
        with patch("deepwiki.service.settings", create=True) as mock_settings:
            mock_settings.enable_deepwiki = True
            mock_settings.enable_knowledge_graph_learning = False
            mock_settings.enable_failure_learning_context = True
            
            service = get_deepwiki_service()
            
            assert isinstance(service, DeepWikiService)

    def test_get_deepwiki_service_returns_singleton(self):
        """Test factory returns same instance."""
        import deepwiki.service as service_module
        service_module._deepwiki_service = None
        
        with patch("deepwiki.service.settings", create=True) as mock_settings:
            mock_settings.enable_deepwiki = True
            mock_settings.enable_knowledge_graph_learning = False
            mock_settings.enable_failure_learning_context = True
            
            service1 = get_deepwiki_service()
            service2 = get_deepwiki_service()
            
            assert service1 is service2

    def test_get_deepwiki_service_handles_import_error(self):
        """Test factory handles settings import error by creating default service."""
        import deepwiki.service as service_module
        service_module._deepwiki_service = None
        
        original_modules = sys.modules.copy()
        try:
            if "common.config.settings" in sys.modules:
                del sys.modules["common.config.settings"]
            
            service = get_deepwiki_service()
            assert isinstance(service, DeepWikiService)
        finally:
            sys.modules.update(original_modules)
            service_module._deepwiki_service = None


class TestDeepWikiServiceImprovementSuggestions:
    """Tests for improvement suggestion generation."""

    def test_generate_improvement_suggestions_no_sources(self):
        """Test suggestions with no sources available."""
        service = DeepWikiService(enable_kg=False, enable_error_pairs=False)
        result = service._generate_improvement_suggestions("test context")
        
        assert "Improvement Suggestions" in result
        assert "No specific suggestions" in result

    @patch("deepwiki.service.DeepWikiService._query_error_pairs")
    def test_generate_improvement_suggestions_with_errors(self, mock_query):
        """Test suggestions with error sources."""
        mock_query.return_value = [
            {
                "fix_text": "Add null check before accessing property",
            }
        ]
        
        service = DeepWikiService(enable_kg=False)
        result = service._generate_improvement_suggestions("null pointer error")
        
        assert "Based on Past Issues" in result
        assert "null check" in result

    @patch("deepwiki.service.DeepWikiService._query_knowledge_graph")
    def test_generate_improvement_suggestions_with_patterns(self, mock_query):
        """Test suggestions with pattern sources."""
        mock_query.return_value = [
            {
                "pattern_name": "Null Object Pattern",
                "pattern_template": "Use null object instead of null checks",
            }
        ]
        
        service = DeepWikiService(enable_error_pairs=False)
        result = service._generate_improvement_suggestions("null handling")
        
        assert "Based on Code Patterns" in result
        assert "Null Object Pattern" in result


class TestDeepWikiThreadSafety:
    """Tests for thread safety improvements (#2147, #2148)."""

    def test_generate_query_id_uses_uuid(self):
        """Test query ID uses UUID format for thread safety (#2147)."""
        service = DeepWikiService()
        
        id1 = service._generate_query_id()
        id2 = service._generate_query_id()
        
        # Should start with dw- prefix
        assert id1.startswith("dw-")
        assert id2.startswith("dw-")
        
        # Should be unique (UUID guarantees this)
        assert id1 != id2
        
        # Should contain UUID format (36 chars after prefix)
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        uuid_part = id1[3:]  # Remove "dw-" prefix
        assert len(uuid_part) == 36
        assert uuid_part.count("-") == 4

    def test_generate_query_id_thread_safe(self):
        """Test query ID generation is thread-safe (#2147)."""
        import threading
        
        service = DeepWikiService()
        query_ids = []
        lock = threading.Lock()
        
        def generate_ids():
            for _ in range(100):
                qid = service._generate_query_id()
                with lock:
                    query_ids.append(qid)
        
        threads = [threading.Thread(target=generate_ids) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All IDs should be unique
        assert len(query_ids) == 1000
        assert len(set(query_ids)) == 1000

    def test_get_deepwiki_service_thread_safe_singleton(self):
        """Test singleton factory is thread-safe (#2148)."""
        import threading
        import deepwiki.service as service_module
        
        # Reset singleton
        service_module._deepwiki_service = None
        
        instances = []
        lock = threading.Lock()
        
        def get_service():
            service = get_deepwiki_service()
            with lock:
                instances.append(service)
        
        with patch("deepwiki.service.settings", create=True) as mock_settings:
            mock_settings.enable_deepwiki = True
            mock_settings.enable_knowledge_graph_learning = False
            mock_settings.enable_failure_learning_context = True
            
            threads = [threading.Thread(target=get_service) for _ in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        
        # All instances should be the same object
        assert len(instances) == 20
        assert all(inst is instances[0] for inst in instances)
        
        # Cleanup
        service_module._deepwiki_service = None
