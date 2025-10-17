#!/usr/bin/env python3
"""
E2E tests for Bug Fix Workflow
Phase 1 Week 6: Bug Fix Workflow
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock

from agents.dev_agent.workflows.bug_fix_workflow import (
    BugFixWorkflow, BugFixState
)
from agents.dev_agent.dev_agent_wrapper import DevAgent


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY') or not os.getenv('SUPABASE_URL'),
    reason="Requires OPENAI_API_KEY and SUPABASE_URL for full E2E test"
)
async def test_bug_fix_workflow_full_e2e():
    """Test complete bug fix workflow with real services."""
    agent = DevAgent()
    workflow = BugFixWorkflow(agent)

    github_issue = {
        "number": 123,
        "title": "Fix: TypeError in user_service.py",
        "body": """When calling get_user(None), a TypeError is raised.

Error: 'NoneType' object has no attribute 'id'

File: agents/user_service.py
Line: 45

Steps to reproduce:
1. Call get_user(None)
2. Observe error
"""
    }

    result = await workflow.execute(github_issue)

    assert result is not None
    assert result['issue_id'] == 123
    assert result['bug_type'] is not None
    assert len(result['affected_files']) > 0


@pytest.mark.asyncio
async def test_bug_fix_workflow_mocked():
    """Test workflow with mocked dependencies."""
    mock_agent = Mock()
    mock_agent.test_tool = Mock()
    mock_agent.test_tool.run_tests = AsyncMock(return_value={
        'success': False,
        'error': 'TypeError: NoneType object has no attribute id',
        'stack_trace': 'Traceback...'
    })

    mock_agent.pattern_learner = Mock()
    mock_agent.pattern_learner.get_similar_bug_patterns = Mock(return_value={
        'success': True,
        'data': {'count': 0, 'patterns': []}
    })
    mock_agent.pattern_learner.get_similar_fix_patterns = Mock(return_value={
        'success': True,
        'data': {'count': 0, 'patterns': []}
    })
    mock_agent.pattern_learner.record_bug_fix = Mock(return_value={
        'success': True,
        'data': {'record_id': 'test-123'}
    })

    mock_agent.fs_tool = Mock()
    mock_agent.fs_tool.read_file = Mock(
        return_value="def get_user(id): return User.query.get(id)"
    )

    mock_agent.llm = Mock()
    mock_agent.llm.generate = AsyncMock(return_value="""
STRATEGY: Add null check before accessing user object
CHANGES: Add if user is None check
""")

    mock_agent.hitl_client = Mock()
    mock_agent.hitl_client.create_approval_request = AsyncMock(
        return_value=Mock(request_id='req-123')
    )

    workflow = BugFixWorkflow(mock_agent)

    github_issue = {
        "number": 456,
        "title": "Fix: TypeError in service",
        "body": "Error when calling function with None"
    }

    result = await workflow.execute(github_issue)

    assert result is not None
    assert result['issue_id'] == 456
    assert result['bug_type'] is not None


@pytest.mark.asyncio
async def test_parse_issue_stage():
    """Test parse issue stage independently."""
    mock_agent = Mock()
    workflow = BugFixWorkflow(mock_agent)

    state: BugFixState = {
        'issue_id': 789,
        'issue_title': 'Bug in code',
        'issue_body': 'TypeError in agents/service.py when calling function',
        'bug_type': None,
        'affected_files': [],
        'root_cause': None,
        'fix_strategy': None,
        'fix_code_diff': None,
        'test_results': None,
        'pr_number': None,
        'pr_url': None,
        'approval_status': None,
        'error': None,
        'execution_start': 0.0,
        'patterns_used': []
    }

    result = await workflow.parse_issue(state)

    assert result['bug_type'] == 'type_error'
    assert 'agents/service.py' in result['affected_files']


def test_classify_bug_type():
    """Test bug type classification."""
    mock_agent = Mock()
    workflow = BugFixWorkflow(mock_agent)

    result = workflow._classify_bug_type("TypeError in function")
    assert result == "type_error"
    result = workflow._classify_bug_type("NoneType error")
    assert result == "null_pointer"
    result = workflow._classify_bug_type("IndexError in list")
    assert result == "index_error"
    result = workflow._classify_bug_type("ImportError: module not found")
    assert result == "import_error"
    assert workflow._classify_bug_type("Invalid syntax") == "syntax_error"
    assert workflow._classify_bug_type("Wrong calculation") == "logic_error"


def test_extract_file_paths():
    """Test file path extraction."""
    mock_agent = Mock()
    workflow = BugFixWorkflow(mock_agent)

    text = """
    Error in `agents/service.py` at line 45.
    Also check `utils/helper.js` for issues.
    The file agents/main.py has a bug.
    """

    files = workflow._extract_file_paths(text)

    assert 'agents/service.py' in files
    assert 'utils/helper.js' in files
    assert 'agents/main.py' in files
