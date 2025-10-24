"""
Integration tests for FAQ Agent OODA Loop
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def mock_tools():
    """Mock all FAQ tools"""
    with patch('faq_agent_ooda.FAQ_TOOLS_AVAILABLE', True):
        with patch('faq_agent_ooda.FAQSearchTool') as mock_search:
            with patch('faq_agent_ooda.FAQManagementTool') as mock_mgmt:
                with patch('faq_agent_ooda.EmbeddingTool') as mock_embed:
                    search_instance = AsyncMock()
                    mgmt_instance = AsyncMock()
                    embed_instance = AsyncMock()
                    
                    mock_search.return_value = search_instance
                    mock_mgmt.return_value = mgmt_instance
                    mock_embed.return_value = embed_instance
                    
                    yield {
                        'search': search_instance,
                        'mgmt': mgmt_instance,
                        'embed': embed_instance
                    }


@pytest.mark.asyncio
class TestFAQOODALoop:
    """Test FAQ Agent OODA Loop implementation"""

    async def test_search_task_execution(self, mock_tools):
        """Test OODA loop for search task"""
        from faq_agent_ooda import FAQAgentOODA, FAQTaskType
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {
                'total_faqs': 50,
                'category_count': 5
            }
        }
        
        mock_tools['mgmt'].get_categories.return_value = {
            'success': True,
            'categories': ['billing', 'technical'],
            'count': 2
        }
        
        mock_tools['search'].search.return_value = {
            'success': True,
            'results': [
                {'id': '1', 'question': 'Test Q', 'answer': 'Test A', 'score': 0.95}
            ],
            'count': 1
        }
        
        agent = FAQAgentOODA()
        result = await agent.execute_task(
            task="search for billing questions",
            task_type=FAQTaskType.SEARCH.value,
            max_iterations=2
        )
        
        assert result['success'] == True
        assert result['task_type'] == FAQTaskType.SEARCH.value
        assert 'decision_trace' in result
        assert len(result['decision_trace']) > 0
        
        trace_phases = [t['phase'] for t in result['decision_trace']]
        assert 'observe' in trace_phases
        assert 'orient' in trace_phases
        assert 'decide' in trace_phases
        assert 'act' in trace_phases

    async def test_create_task_execution(self, mock_tools):
        """Test OODA loop for create task"""
        from faq_agent_ooda import FAQAgentOODA, FAQTaskType
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {'total_faqs': 50}
        }
        
        mock_tools['mgmt'].create_faq.return_value = {
            'success': True,
            'faq_id': '123'
        }
        
        agent = FAQAgentOODA()
        result = await agent.execute_task(
            task="create new FAQ about pricing",
            task_type=FAQTaskType.CREATE.value,
            max_iterations=2
        )
        
        assert result['success'] == True
        assert result['task_type'] == FAQTaskType.CREATE.value
        assert result['iterations'] >= 1

    async def test_analyze_task_execution(self, mock_tools):
        """Test OODA loop for analyze task"""
        from faq_agent_ooda import FAQAgentOODA, FAQTaskType
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {
                'total_faqs': 100,
                'category_count': 10,
                'avg_answer_length': 200
            }
        }
        
        mock_tools['mgmt'].get_categories.return_value = {
            'success': True,
            'categories': [
                {'name': 'billing', 'count': 30},
                {'name': 'technical', 'count': 70}
            ],
            'count': 2
        }
        
        agent = FAQAgentOODA()
        result = await agent.execute_task(
            task="analyze FAQ statistics",
            task_type=FAQTaskType.ANALYZE.value,
            max_iterations=2
        )
        
        assert result['success'] == True
        assert 'decision_trace' in result

    async def test_task_type_inference(self, mock_tools):
        """Test automatic task type inference"""
        from faq_agent_ooda import FAQAgentOODA, FAQTaskType
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {}
        }
        
        mock_tools['search'].search.return_value = {
            'success': True,
            'results': [],
            'count': 0
        }
        
        agent = FAQAgentOODA()
        
        result = await agent.execute_task("find information about billing")
        assert result['task_type'] == FAQTaskType.SEARCH.value
        
        result = await agent.execute_task("create a new FAQ")
        assert result['task_type'] == FAQTaskType.CREATE.value

    async def test_max_iterations_limit(self, mock_tools):
        """Test that OODA loop respects max iterations"""
        from faq_agent_ooda import FAQAgentOODA
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {}
        }
        
        mock_tools['search'].search.return_value = {
            'success': False,
            'error': 'Simulated failure'
        }
        
        agent = FAQAgentOODA()
        result = await agent.execute_task(
            task="search failing task",
            max_iterations=2
        )
        
        assert result['iterations'] <= 2
        assert 'error' in result or result['success'] == False

    async def test_observe_phase_data_collection(self, mock_tools):
        """Test that observe phase collects appropriate data"""
        from faq_agent_ooda import FAQAgentOODA, FAQAgentState
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {'total_faqs': 42}
        }
        
        mock_tools['mgmt'].get_categories.return_value = {
            'success': True,
            'categories': ['test'],
            'count': 1
        }
        
        agent = FAQAgentOODA()
        
        state: FAQAgentState = {
            'task': 'test task',
            'task_type': 'search',
            'context': {},
            'observations': [],
            'orientation': {},
            'strategy': None,
            'actions': [],
            'action_results': [],
            'result': None,
            'error': None,
            'iteration': 0,
            'max_iterations': 1,
            'decision_trace': []
        }
        
        result_state = await agent._observe_node(state)
        
        assert len(result_state['observations']) > 0
        assert 'observation_data' in result_state['context']
        assert len(result_state['decision_trace']) == 1
        assert result_state['decision_trace'][0]['phase'] == 'observe'

    async def test_orient_phase_strategy_generation(self, mock_tools):
        """Test that orient phase generates strategies"""
        from faq_agent_ooda import FAQAgentOODA, FAQAgentState
        
        agent = FAQAgentOODA()
        
        state: FAQAgentState = {
            'task': 'search for help',
            'task_type': 'search',
            'context': {},
            'observations': ['Test observation'],
            'orientation': {},
            'strategy': None,
            'actions': [],
            'action_results': [],
            'result': None,
            'error': None,
            'iteration': 0,
            'max_iterations': 1,
            'decision_trace': []
        }
        
        result_state = await agent._orient_node(state)
        
        assert 'orientation' in result_state
        assert 'strategies' in result_state['orientation']
        assert len(result_state['orientation']['strategies']) > 0
        assert 'complexity' in result_state['orientation']

    async def test_decide_phase_action_planning(self, mock_tools):
        """Test that decide phase creates action plan"""
        from faq_agent_ooda import FAQAgentOODA, FAQAgentState
        
        agent = FAQAgentOODA()
        
        state: FAQAgentState = {
            'task': 'search test',
            'task_type': 'search',
            'context': {},
            'observations': [],
            'orientation': {
                'strategies': [
                    {
                        'name': 'test_strategy',
                        'confidence': 0.9,
                        'priority': 1
                    }
                ]
            },
            'strategy': None,
            'actions': [],
            'action_results': [],
            'result': None,
            'error': None,
            'iteration': 0,
            'max_iterations': 1,
            'decision_trace': []
        }
        
        result_state = await agent._decide_node(state)
        
        assert result_state['strategy'] is not None
        assert len(result_state['actions']) > 0

    async def test_act_phase_execution(self, mock_tools):
        """Test that act phase executes actions"""
        from faq_agent_ooda import FAQAgentOODA, FAQAgentState
        
        mock_tools['search'].search.return_value = {
            'success': True,
            'results': [],
            'count': 0
        }
        
        agent = FAQAgentOODA()
        
        state: FAQAgentState = {
            'task': 'test',
            'task_type': 'search',
            'context': {},
            'observations': [],
            'orientation': {},
            'strategy': 'test',
            'actions': [
                {
                    'type': 'search_faq',
                    'query': 'test',
                    'limit': 10,
                    'critical': False
                }
            ],
            'action_results': [],
            'result': None,
            'error': None,
            'iteration': 0,
            'max_iterations': 1,
            'decision_trace': []
        }
        
        result_state = await agent._act_node(state)
        
        assert len(result_state['action_results']) == 1
        assert result_state['iteration'] == 1
        assert result_state['result'] is not None

    async def test_error_handling(self, mock_tools):
        """Test error handling in OODA loop"""
        from faq_agent_ooda import FAQAgentOODA
        
        mock_tools['mgmt'].get_stats.side_effect = Exception("Simulated error")
        
        agent = FAQAgentOODA()
        result = await agent.execute_task(
            task="test error handling",
            max_iterations=1
        )
        
        assert 'error' in result

    async def test_decision_trace_completeness(self, mock_tools):
        """Test that decision trace captures all phases"""
        from faq_agent_ooda import FAQAgentOODA
        
        mock_tools['mgmt'].get_stats.return_value = {
            'success': True,
            'stats': {}
        }
        
        mock_tools['search'].search.return_value = {
            'success': True,
            'results': [],
            'count': 0
        }
        
        agent = FAQAgentOODA()
        result = await agent.execute_task(
            task="search test",
            max_iterations=1
        )
        
        trace = result.get('decision_trace', [])
        phases = [entry['phase'] for entry in trace]
        
        assert 'observe' in phases
        assert 'orient' in phases
        assert 'decide' in phases
        assert 'act' in phases
        
        for entry in trace:
            assert 'timestamp' in entry
            assert 'phase' in entry


def test_faq_agent_ooda_creation():
    """Test FAQ Agent OODA factory function"""
    from faq_agent_ooda import create_faq_agent_ooda, FAQ_TOOLS_AVAILABLE
    
    if FAQ_TOOLS_AVAILABLE:
        agent = create_faq_agent_ooda()
        assert agent is not None
        assert hasattr(agent, 'execute_task')
        assert hasattr(agent, 'graph')
