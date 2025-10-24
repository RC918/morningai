"""
Shared test fixtures and configuration for FAQ Agent tests
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
api_backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'handoff', '20250928', '40_App', 'api-backend')
sys.path.insert(0, os.path.join(api_backend_path, 'src'))
sys.path.insert(0, api_backend_path)

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-ci'
os.environ['TESTING'] = 'true'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-key'
os.environ['OPENAI_API_KEY'] = 'test-openai-key'


@pytest.fixture(scope='session', autouse=True)
def mock_external_services():
    """Mock external services (Supabase, OpenAI) for all tests"""
    from unittest.mock import AsyncMock
    
    with patch('agents.faq_agent.tools.faq_search_tool.create_client') as mock_supabase_search:
        mock_search_client = MagicMock()
        mock_rpc_response = MagicMock()
        mock_rpc_response.data = []
        mock_search_client.rpc.return_value.execute.return_value = mock_rpc_response
        mock_search_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {}
        mock_supabase_search.return_value = mock_search_client
        
        with patch('agents.faq_agent.tools.faq_management_tool.create_client') as mock_supabase_mgmt:
            mock_mgmt_client = MagicMock()
            mock_insert_response = MagicMock()
            mock_insert_response.data = [{'id': 'test-id', 'question': 'Q', 'answer': 'A'}]
            mock_mgmt_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response
            mock_update_response = MagicMock()
            mock_update_response.data = [{'id': 'test-id', 'updated': True}]
            mock_mgmt_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
            mock_delete_response = MagicMock()
            mock_delete_response.data = [{'id': 'test-id', 'deleted': True}]
            mock_mgmt_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_delete_response
            mock_supabase_mgmt.return_value = mock_mgmt_client
            
            with patch('agents.faq_agent.tools.embedding_tool.AsyncOpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_embeddings = MagicMock()
                
                mock_response = MagicMock()
                mock_data_item = MagicMock()
                mock_data_item.embedding = [0.1] * 1536
                mock_response.data = [mock_data_item]
                
                mock_embeddings.create = AsyncMock(return_value=mock_response)
                mock_client.embeddings = mock_embeddings
                mock_openai.return_value = mock_client
                
                yield
