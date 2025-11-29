#!/usr/bin/env python3
"""
Unit tests for LLM Reviewer Adapter - Phase 6 PR-3
"""
import json
from unittest.mock import patch, MagicMock
from llm_reviewer_adapter import (
    LLMReviewerAdapter,
    generate_llm_review,
    combine_severity,
    SEVERITY_ORDER
)


class TestSeverityHelpers:
    """Test suite for severity helper functions"""

    def test_severity_order_values(self):
        """Test severity order mapping"""
        assert SEVERITY_ORDER["none"] == 0
        assert SEVERITY_ORDER["low"] == 1
        assert SEVERITY_ORDER["medium"] == 2
        assert SEVERITY_ORDER["high"] == 3
        assert SEVERITY_ORDER["critical"] == 4

    def test_combine_severity_same(self):
        """Test combining same severities"""
        assert combine_severity("none", "none") == "none"
        assert combine_severity("high", "high") == "high"

    def test_combine_severity_ci_worse(self):
        """Test combining when CI severity is worse"""
        assert combine_severity("high", "low") == "high"
        assert combine_severity("critical", "medium") == "critical"

    def test_combine_severity_llm_worse(self):
        """Test combining when LLM severity is worse"""
        assert combine_severity("low", "high") == "high"
        assert combine_severity("none", "critical") == "critical"

    def test_combine_severity_unknown_values(self):
        """Test combining with unknown severity values"""
        result = combine_severity("unknown", "low")
        assert result in ["unknown", "low"]


class TestLLMReviewerAdapter:
    """Test suite for LLM Reviewer Adapter"""

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_init_with_client(self, mock_get_client):
        """Test initialization with LLM client"""
        mock_client = MagicMock()
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        adapter = LLMReviewerAdapter(trace_id="test-trace")

        assert adapter.llm_client is not None
        mock_get_client.assert_called_once_with(
            component="reviewer",
            trace_id="test-trace",
            default_provider="openai"
        )

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_init_without_client(self, mock_get_client):
        """Test initialization when LLM client fails"""
        mock_get_client.side_effect = Exception("No API key")

        adapter = LLMReviewerAdapter(trace_id="test-trace")

        assert adapter.llm_client is None

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_no_client(self, mock_get_client):
        """Test review generation without LLM client"""
        mock_get_client.side_effect = Exception("No API key")

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["llm_used"] is False
        assert result["quality_score"] == 80
        assert result["severity"] == "none"
        assert result["provider"] is None

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_client_not_available(self, mock_get_client):
        """Test review generation when client is not available"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_get_client.return_value = mock_client

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["llm_used"] is False
        assert result["quality_score"] == 80

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_success(self, mock_get_client):
        """Test successful LLM review generation"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Code looks good",
            "quality_score": 75,
            "severity": "low",
            "decision": "approve",
            "comments": []
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["llm_used"] is True
        assert result["provider"] == "openai"
        assert result["quality_score"] == 75
        assert result["severity"] == "low"

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_ci_ceiling(self, mock_get_client):
        """Test that CI score acts as ceiling for LLM score"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Code looks excellent",
            "quality_score": 95,
            "severity": "none",
            "decision": "approve",
            "comments": []
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["quality_score"] == 80

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_severity_combination(self, mock_get_client):
        """Test that severities are combined (worse wins)"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Found some issues",
            "quality_score": 60,
            "severity": "high",
            "decision": "needs_changes",
            "comments": []
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="low"
        )

        assert result["severity"] == "high"

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_with_comments(self, mock_get_client):
        """Test review generation with comments"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "gemini"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Found some issues",
            "quality_score": 65,
            "severity": "medium",
            "decision": "needs_changes",
            "comments": [
                {
                    "severity": "warning",
                    "category": "security",
                    "message": "Consider input validation"
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "gemini"
        mock_response.model = "gemini-1.5-pro"
        mock_response.usage = {"total_tokens": 150}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["llm_used"] is True
        assert result["provider"] == "gemini"
        assert len(result["comments"]) == 1
        assert result["comments"][0]["category"] == "security"

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_llm_exception(self, mock_get_client):
        """Test review generation when LLM raises exception"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_client.generate.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["llm_used"] is False
        assert result["quality_score"] == 80
        assert result["severity"] == "none"

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_invalid_json(self, mock_get_client):
        """Test review generation with invalid JSON response"""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 50}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none"
        )

        assert result["llm_used"] is False
        assert result["quality_score"] == 80

    def test_clean_json_response_markdown_blocks(self):
        """Test cleaning JSON response with markdown code blocks"""
        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        content_with_markdown = '''```json
{
  "summary": "Test",
  "quality_score": 75,
  "severity": "low",
  "decision": "approve",
  "comments": []
}
```'''

        cleaned = adapter._clean_json_response(content_with_markdown)
        parsed = json.loads(cleaned)

        assert parsed["summary"] == "Test"
        assert parsed["quality_score"] == 75

    def test_clean_json_response_explanatory_text(self):
        """Test cleaning JSON response with explanatory text"""
        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        content_with_text = '''Here is my review:
{
  "summary": "Test",
  "quality_score": 75,
  "severity": "low",
  "decision": "approve",
  "comments": []
}
Hope this helps!'''

        cleaned = adapter._clean_json_response(content_with_text)
        parsed = json.loads(cleaned)

        assert parsed["summary"] == "Test"

    def test_fallback_result_high_severity(self):
        """Test fallback result with high severity"""
        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        result = adapter._get_fallback_result(40, "high")

        assert result["llm_used"] is False
        assert result["quality_score"] == 40
        assert result["severity"] == "high"
        assert result["decision"] == "needs_changes"

    def test_fallback_result_none_severity(self):
        """Test fallback result with none severity"""
        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        result = adapter._get_fallback_result(80, "none")

        assert result["llm_used"] is False
        assert result["quality_score"] == 80
        assert result["severity"] == "none"
        assert result["decision"] == "approve"


class TestConvenienceFunction:
    """Test suite for convenience function"""

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_llm_review_function(self, mock_get_client):
        """Test convenience function generate_llm_review"""
        mock_get_client.side_effect = Exception("No API key")

        result = generate_llm_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            trace_id="test-trace",
            base_quality_score=80,
            base_severity="none"
        )

        assert isinstance(result, dict)
        assert "quality_score" in result
        assert "severity" in result
        assert "llm_used" in result


class TestReviewerNodeIntegration:
    """Test suite for reviewer_node integration"""

    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator.generate_llm_review')
    def test_reviewer_node_llm_disabled(self, mock_generate, mock_settings):
        """Test reviewer_node with LLM disabled"""
        mock_settings.use_llm_reviewer = False

        from langgraph_orchestrator import reviewer_node

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "pr_url": "https://github.com/owner/repo/pull/123",
            "ci_state": "success",
            "messages": []
        }

        result = reviewer_node(state)

        mock_generate.assert_not_called()
        assert result["code_quality_score"] == 80
        assert result["review_severity"] == "none"

    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator.generate_llm_review')
    def test_reviewer_node_llm_enabled_success(self, mock_generate, mock_settings):
        """Test reviewer_node with LLM enabled and successful"""
        mock_settings.use_llm_reviewer = True

        mock_generate.return_value = {
            "quality_score": 75,
            "severity": "low",
            "summary": "LLM review",
            "decision": "approve",
            "comments": [],
            "llm_used": True,
            "provider": "openai",
            "review_time_ms": 500
        }

        from langgraph_orchestrator import reviewer_node

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "pr_url": "https://github.com/owner/repo/pull/123",
            "ci_state": "success",
            "goal": "Add feature",
            "repo": "owner/repo",
            "messages": []
        }

        result = reviewer_node(state)

        mock_generate.assert_called_once()
        assert result["code_quality_score"] == 75
        assert result["review_severity"] == "low"

    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator.generate_llm_review')
    def test_reviewer_node_llm_enabled_fallback(self, mock_generate, mock_settings):
        """Test reviewer_node with LLM enabled but falling back"""
        mock_settings.use_llm_reviewer = True

        mock_generate.return_value = {
            "quality_score": 80,
            "severity": "none",
            "summary": "Fallback",
            "decision": "approve",
            "comments": [],
            "llm_used": False,
            "provider": None,
            "review_time_ms": 0
        }

        from langgraph_orchestrator import reviewer_node

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "pr_url": "https://github.com/owner/repo/pull/123",
            "ci_state": "success",
            "goal": "Add feature",
            "repo": "owner/repo",
            "messages": []
        }

        result = reviewer_node(state)

        assert result["code_quality_score"] == 80
        assert result["review_severity"] == "none"

    def test_ci_only_review_success(self):
        """Test CI-only review with success state"""
        from langgraph_orchestrator import _ci_only_review

        result = _ci_only_review("success")

        assert result["code_quality_score"] == 80
        assert result["review_severity"] == "none"
        assert result["review_result"]["status"] == "passed"

    def test_ci_only_review_failure(self):
        """Test CI-only review with failure state"""
        from langgraph_orchestrator import _ci_only_review

        result = _ci_only_review("failure")

        assert result["code_quality_score"] == 40
        assert result["review_severity"] == "high"
        assert result["review_result"]["status"] == "needs_attention"

    def test_ci_only_review_pending(self):
        """Test CI-only review with pending state"""
        from langgraph_orchestrator import _ci_only_review

        result = _ci_only_review("pending")

        assert result["code_quality_score"] == 60
        assert result["review_severity"] == "medium"
        assert result["review_result"]["status"] == "pending"

    def test_ci_only_review_unknown(self):
        """Test CI-only review with unknown state"""
        from langgraph_orchestrator import _ci_only_review

        result = _ci_only_review("unknown")

        assert result["code_quality_score"] == 60
        assert result["review_severity"] == "medium"
