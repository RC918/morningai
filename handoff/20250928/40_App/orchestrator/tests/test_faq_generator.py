"""
Tests for FAQ generator using GPT-4
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'llm'))

from llm.faq_generator import (
    _get_openai_client,
    generate_faq_content,
    generate_fallback_faq,
    get_cached_or_generate,
    SYSTEM_PROMPT,
    _faq_cache
)


class TestGetOpenAIClient:
    """Test _get_openai_client function"""
    
    @patch('llm.faq_generator.OpenAI')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    def test_get_client_with_api_key(self, mock_openai):
        """Test getting OpenAI client with API key"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = _get_openai_client()
        
        assert client == mock_client
        mock_openai.assert_called_once_with(api_key='test-api-key')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_client_without_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            _get_openai_client()


class TestGenerateFaqContent:
    """Test generate_faq_content function"""
    
    @patch('llm.faq_generator._get_openai_client')
    def test_generate_faq_success(self, mock_get_client):
        """Test successful FAQ generation with GPT-4"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "# Test FAQ\n\nThis is a test FAQ content."
        mock_response.usage.total_tokens = 150
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = generate_faq_content(
            question="How to setup MorningAI?",
            trace_id="test-trace-123",
            repo="owner/repo"
        )
        
        assert "# Test FAQ" in result
        assert "test-trace-123" in result
        assert "owner/repo" in result
        assert "Metadata" in result
        
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        assert call_args[1]['model'] == 'gpt-4-turbo-preview'
        assert len(call_args[1]['messages']) == 2
        assert call_args[1]['messages'][0]['role'] == 'system'
        assert call_args[1]['messages'][1]['role'] == 'user'
        assert 'How to setup MorningAI?' in call_args[1]['messages'][1]['content']
    
    @patch('llm.faq_generator._get_openai_client')
    def test_generate_faq_with_custom_model(self, mock_get_client):
        """Test FAQ generation with custom model"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "FAQ content"
        mock_response.usage.total_tokens = 100
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        generate_faq_content(
            question="Test",
            trace_id="trace-456",
            model="gpt-4"
        )
        
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4'
    
    @patch('llm.faq_generator.generate_fallback_faq')
    @patch('llm.faq_generator._get_openai_client')
    def test_generate_faq_falls_back_on_error(self, mock_get_client, mock_fallback):
        """Test FAQ generation falls back to template on OpenAI error"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        mock_fallback.return_value = "# Fallback FAQ\n\nTemplate content"
        
        result = generate_faq_content(
            question="Test question",
            trace_id="trace-789",
            repo="owner/repo"
        )
        
        assert result == "# Fallback FAQ\n\nTemplate content"
        mock_fallback.assert_called_once_with("Test question", "trace-789", "owner/repo")
    
    @patch('llm.faq_generator._get_openai_client')
    def test_generate_faq_includes_metadata(self, mock_get_client):
        """Test that generated FAQ includes metadata section"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Content"
        mock_response.usage.total_tokens = 50
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = generate_faq_content(
            question="Test",
            trace_id="trace-meta",
            repo="test/repo"
        )
        
        assert "Metadata" in result
        assert "Task: Test" in result
        assert "Trace ID: `trace-meta`" in result
        assert "Repository: test/repo" in result
    
    @patch('llm.faq_generator._get_openai_client')
    def test_generate_faq_uses_correct_parameters(self, mock_get_client):
        """Test that GPT-4 is called with correct parameters"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Content"
        mock_response.usage.total_tokens = 50
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        generate_faq_content("Test", "trace-123")
        
        call_args = mock_client.chat.completions.create.call_args
        
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 2000
        assert call_args[1]['top_p'] == 0.9
        assert call_args[1]['frequency_penalty'] == 0.3
        assert call_args[1]['presence_penalty'] == 0.3


class TestGenerateFallbackFaq:
    """Test generate_fallback_faq function"""
    
    def test_fallback_faq_structure(self):
        """Test fallback FAQ has correct structure"""
        result = generate_fallback_faq(
            question="How to use the API?",
            trace_id="fallback-123",
            repo="owner/repo"
        )
        
        assert "# Frequently Asked Questions (FAQ)" in result
        assert "How to use the API?" in result
        assert "fallback-123" in result
        assert "owner/repo" in result
        assert "Metadata" in result
        assert "Fallback Template" in result
    
    def test_fallback_includes_tech_stack(self):
        """Test fallback FAQ includes technology stack"""
        result = generate_fallback_faq("Test", "trace", "repo")
        
        assert "React" in result
        assert "Flask" in result
        assert "PostgreSQL" in result
        assert "Redis" in result
        assert "GPT-4" in result
        assert "LangGraph" in result
    
    def test_fallback_includes_documentation_links(self):
        """Test fallback FAQ includes documentation links"""
        result = generate_fallback_faq("Test", "trace", "repo")
        
        assert "README" in result
        assert "CONTRIBUTING" in result
        assert "RLS_IMPLEMENTATION_GUIDE" in result
    
    def test_fallback_includes_code_examples(self):
        """Test fallback FAQ includes code examples"""
        result = generate_fallback_faq("Test", "trace", "repo")
        
        assert "```bash" in result or "```" in result
        assert "gunicorn" in result
        assert "pytest" in result
    
    def test_fallback_includes_architecture_diagram(self):
        """Test fallback FAQ includes architecture diagram"""
        result = generate_fallback_faq("Test", "trace", "repo")
        
        assert "Frontend" in result
        assert "API Backend" in result
        assert "Supabase" in result
        assert "Orchestrator" in result


class TestGetCachedOrGenerate:
    """Test get_cached_or_generate function with caching"""
    
    def setup_method(self):
        """Clear cache before each test"""
        _faq_cache.clear()
    
    @patch('llm.faq_generator.generate_faq_content')
    def test_cache_miss_generates_new_content(self, mock_generate):
        """Test cache miss generates new content"""
        mock_generate.return_value = "# New FAQ Content"
        
        result = get_cached_or_generate(
            question="New question",
            trace_id="trace-new",
            use_cache=True
        )
        
        assert result == "# New FAQ Content"
        mock_generate.assert_called_once()
    
    @patch('llm.faq_generator.generate_faq_content')
    def test_cache_hit_returns_cached_content(self, mock_generate):
        """Test cache hit returns cached content without generating"""
        question = "Cached question"
        
        mock_generate.return_value = "# Cached FAQ Content"
        
        result1 = get_cached_or_generate(question, "trace-1", use_cache=True)
        result2 = get_cached_or_generate(question, "trace-2", use_cache=True)
        
        assert "# Cached FAQ Content" in result1
        assert "# Cached FAQ Content" in result2
        mock_generate.assert_called_once()
    
    @patch('llm.faq_generator.generate_faq_content')
    def test_cache_disabled_always_generates(self, mock_generate):
        """Test that disabling cache always generates new content"""
        mock_generate.return_value = "# Fresh FAQ"
        
        question = "Same question"
        
        get_cached_or_generate(question, "trace-1", use_cache=False)
        get_cached_or_generate(question, "trace-2", use_cache=False)
        
        assert mock_generate.call_count == 2
    
    @patch('llm.faq_generator.generate_faq_content')
    def test_cache_key_is_case_insensitive(self, mock_generate):
        """Test cache key is case-insensitive"""
        mock_generate.return_value = "# FAQ Content"
        
        get_cached_or_generate("Test Question", "trace-1", use_cache=True)
        get_cached_or_generate("TEST QUESTION", "trace-2", use_cache=True)
        
        assert mock_generate.call_count == 1
    
    @patch('llm.faq_generator.generate_faq_content')
    def test_cache_key_strips_whitespace(self, mock_generate):
        """Test cache key strips leading/trailing whitespace"""
        mock_generate.return_value = "# FAQ Content"
        
        get_cached_or_generate("  Test  ", "trace-1", use_cache=True)
        get_cached_or_generate("Test", "trace-2", use_cache=True)
        
        assert mock_generate.call_count == 1
    
    @patch('llm.faq_generator.generate_faq_content')
    def test_cache_stores_content_correctly(self, mock_generate):
        """Test that cache stores content correctly"""
        content = "# Stored FAQ Content\n\nTrace ID: `{trace_id}`"
        mock_generate.return_value = content
        
        question = "Store test"
        
        get_cached_or_generate(question, "trace-1", use_cache=True)
        
        cache_key = question.lower().strip()
        assert cache_key in _faq_cache
        assert _faq_cache[cache_key] == content


class TestSystemPrompt:
    """Test SYSTEM_PROMPT constant"""
    
    def test_system_prompt_exists(self):
        """Test that SYSTEM_PROMPT is defined"""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 0
    
    def test_system_prompt_includes_platform_info(self):
        """Test SYSTEM_PROMPT includes platform information"""
        assert "MorningAI" in SYSTEM_PROMPT
        assert "multi-tenant" in SYSTEM_PROMPT or "Multi-tenant" in SYSTEM_PROMPT
    
    def test_system_prompt_includes_tech_stack(self):
        """Test SYSTEM_PROMPT includes technology stack"""
        assert "React" in SYSTEM_PROMPT
        assert "Flask" in SYSTEM_PROMPT
        assert "GPT-4" in SYSTEM_PROMPT
        assert "LangGraph" in SYSTEM_PROMPT
    
    def test_system_prompt_includes_guidelines(self):
        """Test SYSTEM_PROMPT includes generation guidelines"""
        assert "FAQ" in SYSTEM_PROMPT
        assert "Markdown" in SYSTEM_PROMPT
