"""
Tests for FAQ Agent Tools
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.embedding_tool import EmbeddingTool
from tools.faq_search_tool import FAQSearchTool
from tools.faq_management_tool import FAQManagementTool


class TestEmbeddingTool:
    """Test EmbeddingTool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tool = EmbeddingTool()
            assert tool.api_key == 'test-key'
            assert tool.model == 'text-embedding-3-small'
    
    def test_initialization_with_custom_model(self):
        """Test initialization with custom model"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tool = EmbeddingTool(model='text-embedding-ada-002')
            assert tool.model == 'text-embedding-ada-002'
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                EmbeddingTool()
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self):
        """Test successful embedding generation"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tool = EmbeddingTool()
            
            mock_embedding = [0.1] * 1536
            mock_response = {
                'data': [{'embedding': mock_embedding}]
            }
            
            with patch('openai.Embedding.acreate', new=AsyncMock(return_value=mock_response)):
                result = await tool.generate_embedding("test question")
                
                assert result['success'] is True
                assert 'embedding' in result
                assert len(result['embedding']) == 1536
                assert result['dimensions'] == 1536
    
    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tool = EmbeddingTool()
            
            result = await tool.generate_embedding("")
            
            assert result['success'] is False
            assert 'error' in result
            assert 'Empty text' in result['error']
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self):
        """Test batch embedding generation"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            tool = EmbeddingTool()
            
            mock_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
            mock_response = {
                'data': [{'embedding': emb} for emb in mock_embeddings]
            }
            
            with patch('openai.Embedding.acreate', new=AsyncMock(return_value=mock_response)):
                result = await tool.generate_embeddings_batch([
                    "question 1",
                    "question 2",
                    "question 3"
                ])
                
                assert result['success'] is True
                assert result['count'] == 3
                assert result['successful'] == 3
                assert len(result['embeddings']) == 3


class TestFAQSearchTool:
    """Test FAQSearchTool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            tool = FAQSearchTool()
            assert tool.supabase_url == 'https://test.supabase.co'
            assert tool.supabase_key == 'test-key'
            assert tool.embedding_tool is not None
    
    def test_initialization_missing_env(self):
        """Test initialization with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Supabase URL and key are required"):
                FAQSearchTool()
    
    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful FAQ search"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            mock_emb_tool = Mock()
            mock_emb_tool.generate_embedding = AsyncMock(return_value={
                'success': True,
                'embedding': [0.1] * 1536
            })
            
            tool = FAQSearchTool(embedding_tool=mock_emb_tool)
            
            mock_results = [
                {
                    'id': '123',
                    'question': 'Test question',
                    'answer': 'Test answer',
                    'similarity': 0.95
                }
            ]
            
            mock_response = Mock()
            mock_response.data = mock_results
            
            tool.client.rpc = Mock(return_value=Mock(execute=Mock(return_value=mock_response)))
            tool._log_search = AsyncMock()
            
            result = await tool.search("test query", limit=5)
            
            assert result['success'] is True
            assert result['count'] == 1
            assert result['query'] == 'test query'
            assert len(result['results']) == 1


class TestFAQManagementTool:
    """Test FAQManagementTool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            tool = FAQManagementTool()
            assert tool.supabase_url == 'https://test.supabase.co'
            assert tool.supabase_key == 'test-key'
            assert tool.embedding_tool is not None
    
    @pytest.mark.asyncio
    async def test_create_faq_success(self):
        """Test successful FAQ creation"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            mock_emb_tool = Mock()
            mock_emb_tool.generate_embedding = AsyncMock(return_value={
                'success': True,
                'embedding': [0.1] * 1536
            })
            
            tool = FAQManagementTool(embedding_tool=mock_emb_tool)
            
            mock_faq = {
                'id': '123',
                'question': 'Test question',
                'answer': 'Test answer',
                'category': 'test'
            }
            
            mock_response = Mock()
            mock_response.data = [mock_faq]
            
            tool.client.table = Mock(return_value=Mock(
                insert=Mock(return_value=Mock(
                    execute=Mock(return_value=mock_response)
                ))
            ))
            
            result = await tool.create_faq(
                question="Test question",
                answer="Test answer",
                category="test"
            )
            
            assert result['success'] is True
            assert result['faq']['id'] == '123'
            assert 'message' in result
    
    @pytest.mark.asyncio
    async def test_create_faq_embedding_failure(self):
        """Test FAQ creation with embedding failure"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            mock_emb_tool = Mock()
            mock_emb_tool.generate_embedding = AsyncMock(return_value={
                'success': False,
                'error': 'API error'
            })
            
            tool = FAQManagementTool(embedding_tool=mock_emb_tool)
            
            result = await tool.create_faq(
                question="Test question",
                answer="Test answer"
            )
            
            assert result['success'] is False
            assert 'error' in result
            assert 'Failed to generate embedding' in result['error']
    
    @pytest.mark.asyncio
    async def test_bulk_create_faqs(self):
        """Test bulk FAQ creation"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key',
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            mock_emb_tool = Mock()
            mock_emb_tool.generate_embeddings_batch = AsyncMock(return_value={
                'success': True,
                'embeddings': [[0.1] * 1536, [0.2] * 1536]
            })
            
            tool = FAQManagementTool(embedding_tool=mock_emb_tool)
            
            mock_response = Mock()
            mock_response.data = [{'id': '1'}, {'id': '2'}]
            
            tool.client.table = Mock(return_value=Mock(
                insert=Mock(return_value=Mock(
                    execute=Mock(return_value=mock_response)
                ))
            ))
            
            faqs = [
                {'question': 'Q1', 'answer': 'A1'},
                {'question': 'Q2', 'answer': 'A2'}
            ]
            
            result = await tool.bulk_create_faqs(faqs)
            
            assert result['success'] is True
            assert result['created_count'] == 2
            assert result['failed_count'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
