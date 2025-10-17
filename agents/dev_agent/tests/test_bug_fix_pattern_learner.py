#!/usr/bin/env python3
"""
Unit tests for BugFixPatternLearner
Phase 1 Week 6: Bug Fix Workflow
"""
import pytest
import os
from unittest.mock import Mock, MagicMock

from agents.dev_agent.knowledge_graph.bug_fix_pattern_learner import (
    BugFixPatternLearner
)
from agents.dev_agent.knowledge_graph.knowledge_graph_manager import (
    KnowledgeGraphManager
)


@pytest.mark.skipif(
    not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_DB_PASSWORD'),
    reason="Requires SUPABASE_URL and SUPABASE_DB_PASSWORD"
)
def test_learn_bug_pattern_real():
    """Test learning a bug pattern with real database."""
    kg = KnowledgeGraphManager()
    learner = BugFixPatternLearner(kg)

    result = learner.learn_bug_pattern(
        bug_description="NoneType has no attribute 'id'",
        root_cause="Missing null check before accessing object attribute",
        bug_type="type_error",
        affected_code="user.id",
        metadata={"severity": "high"}
    )

    assert result['success']
    assert 'pattern_id' in result['data']
    assert 'pattern_name' in result['data']


@pytest.mark.skipif(
    not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_DB_PASSWORD'),
    reason="Requires SUPABASE_URL and SUPABASE_DB_PASSWORD"
)
def test_learn_fix_pattern_real():
    """Test learning a fix pattern with real database."""
    kg = KnowledgeGraphManager()
    learner = BugFixPatternLearner(kg)

    result = learner.learn_fix_pattern(
        bug_description="NoneType error",
        fix_strategy="Add null check before accessing attribute",
        fix_code="if user is not None:\n    return user.id",
        success=True,
        metadata={"files_changed": 1}
    )

    assert result['success']
    assert 'pattern_id' in result['data']


def test_learn_bug_pattern_mocked():
    """Test learning bug pattern with mocked database."""
    mock_kg = Mock()
    mock_kg.db_pool = MagicMock()

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [123]

    mock_conn.cursor.return_value = mock_cursor
    mock_kg._get_connection.return_value = mock_conn
    mock_kg._return_connection = Mock()

    learner = BugFixPatternLearner(mock_kg)

    result = learner.learn_bug_pattern(
        bug_description="Test bug",
        root_cause="Test cause",
        bug_type="test_error"
    )

    assert result['success']
    assert result['pattern_id'] == 123


def test_learn_fix_pattern_mocked():
    """Test learning fix pattern with mocked database."""
    mock_kg = Mock()
    mock_kg.db_pool = MagicMock()

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [456]

    mock_conn.cursor.return_value = mock_cursor
    mock_kg._get_connection.return_value = mock_conn
    mock_kg._return_connection = Mock()

    learner = BugFixPatternLearner(mock_kg)

    result = learner.learn_fix_pattern(
        bug_description="Test bug",
        fix_strategy="Test fix",
        fix_code="test code",
        success=True
    )

    assert result['success']
    assert result['pattern_id'] == 456


def test_get_similar_bug_patterns_no_db():
    """Test getting similar patterns without database."""
    mock_kg = Mock()
    mock_kg.db_pool = None

    learner = BugFixPatternLearner(mock_kg)

    result = learner.get_similar_bug_patterns(
        bug_description="Test bug",
        bug_type="test_error"
    )

    assert not result['success']
    assert 'error' in result


def test_record_bug_fix_no_db():
    """Test recording bug fix without database."""
    mock_kg = Mock()
    mock_kg.db_pool = None

    learner = BugFixPatternLearner(mock_kg)

    result = learner.record_bug_fix(
        issue_number=123,
        issue_title="Test Issue",
        bug_description="Test description",
        bug_type="test_error",
        affected_files=["test.py"],
        root_cause="Test cause",
        fix_strategy="Test strategy",
        fix_code_diff="Test diff",
        pr_number=456,
        pr_url="https://github.com/test/repo/pull/456",
        success=True,
        execution_time_seconds=60
    )

    assert not result['success']
    assert 'error' in result
