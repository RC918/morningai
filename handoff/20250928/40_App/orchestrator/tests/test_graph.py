"""
Tests for graph.py orchestrator functions
"""
import pytest
import os
import sys
import uuid
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graph import planner, execute, main


class TestPlanner:
    """Test planner function"""
    
    @patch('graph.save_text')
    def test_planner_returns_steps(self, mock_save):
        """Test planner returns correct steps"""
        goal = "Create FAQ documentation"
        
        steps = planner(goal)
        
        assert isinstance(steps, list)
        assert len(steps) == 4
        assert "analyze" in steps
        assert "patch" in steps
        assert "open PR" in steps
        assert "check CI" in steps
        
        mock_save.assert_called_once_with("goal", goal)
    
    @patch('graph.save_text')
    def test_planner_saves_goal_to_memory(self, mock_save):
        """Test planner saves goal to memory"""
        goal = "Update documentation"
        
        planner(goal)
        
        mock_save.assert_called_once_with("goal", goal)


class TestExecute:
    """Test execute function"""
    
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    @patch('subprocess.run')
    def test_execute_success(self, mock_subprocess, mock_get_repo, mock_create_branch, 
                            mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks):
        """Test execute function with successful workflow"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ Content\n\nTest content"
        mock_open_pr.return_value = ("https://github.com/test/pr/1", 1)
        mock_pr_checks.return_value = ("success", {"check1": "passed"})
        
        goal = "Create FAQ"
        repo_full = "owner/repo"
        
        pr_url, state, trace_id = execute(goal, repo_full)
        
        assert pr_url == "https://github.com/test/pr/1"
        assert state == "success"
        assert trace_id is not None
        
        mock_get_repo.assert_called_once()
        mock_create_branch.assert_called_once()
        mock_generate_faq.assert_called_once()
        mock_commit.assert_called_once()
        mock_open_pr.assert_called_once()
        mock_pr_checks.assert_called_once()
    
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    def test_execute_with_trace_id(self, mock_get_repo, mock_create_branch, 
                                   mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks):
        """Test execute with provided trace_id"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ Content"
        mock_open_pr.return_value = ("https://github.com/test/pr/2", 2)
        mock_pr_checks.return_value = ("pending", {})
        
        custom_trace_id = "custom-trace-123"
        pr_url, state, trace_id = execute("Test", "owner/repo", trace_id=custom_trace_id)
        
        assert trace_id == custom_trace_id
    
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    def test_execute_generates_new_trace_id(self, mock_get_repo, mock_create_branch, 
                                           mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks):
        """Test execute generates UUID when trace_id is None"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ"
        mock_open_pr.return_value = ("https://github.com/test/pr/3", 3)
        mock_pr_checks.return_value = ("success", {})
        
        pr_url, state, trace_id = execute("Test", "owner/repo", trace_id=None)
        
        assert trace_id is not None
        assert len(trace_id) > 0
    
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    @patch('subprocess.run')
    def test_execute_auto_merge_enabled(self, mock_subprocess, mock_get_repo, mock_create_branch, 
                                       mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks):
        """Test execute enables auto-merge on PR"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ"
        mock_open_pr.return_value = ("https://github.com/test/pr/4", 4)
        mock_pr_checks.return_value = ("success", {})
        
        execute("Test", "owner/repo")
        
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "gh" in call_args
        assert "pr" in call_args
        assert "merge" in call_args
        assert "--auto" in call_args
        assert "--squash" in call_args
    
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    @patch('subprocess.run')
    def test_execute_handles_auto_merge_failure(self, mock_subprocess, mock_get_repo, mock_create_branch, 
                                                mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks):
        """Test execute handles auto-merge command failure gracefully"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        mock_generate_faq.return_value = "# FAQ"
        mock_open_pr.return_value = ("https://github.com/test/pr/5", 5)
        mock_pr_checks.return_value = ("success", {})
        mock_subprocess.side_effect = Exception("gh command failed")
        
        pr_url, state, trace_id = execute("Test", "owner/repo")
        
        assert pr_url == "https://github.com/test/pr/5"
    
    @patch('graph.get_pr_checks')
    @patch('graph.open_pr')
    @patch('graph.commit_file')
    @patch('graph.generate_faq_content')
    @patch('graph.create_branch')
    @patch('graph.get_repo')
    def test_execute_handles_faq_generation_failure(self, mock_get_repo, mock_create_branch, 
                                                    mock_generate_faq, mock_commit, mock_open_pr, mock_pr_checks):
        """Test execute handles FAQ generation failure with fallback"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_create_branch.return_value = "orchestrator/1234567-faq-update"
        
        mock_generate_faq.side_effect = [
            Exception("Generation failed"),
            "# Fallback FAQ Content"
        ]
        mock_open_pr.return_value = ("https://github.com/test/pr/6", 6)
        mock_pr_checks.return_value = ("success", {})
        
        pr_url, state, trace_id = execute("Test", "owner/repo")
        
        assert pr_url == "https://github.com/test/pr/6"
        assert mock_generate_faq.call_count == 2


class TestMain:
    """Test main function"""
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_success(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main function with successful execution"""
        mock_planner.return_value = ["step1", "step2"]
        mock_enqueue.return_value = ["job-1", "job-2"]
        mock_execute.return_value = ("https://github.com/pr/1", "success", "trace-123")
        mock_recall.return_value = [{"text": "memory1"}]
        
        main("Test goal", "owner/repo")
        
        mock_planner.assert_called_once_with("Test goal")
        mock_enqueue.assert_called_once()
        mock_execute.assert_called_once()
        mock_recall.assert_called_once_with("recent")
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_redis_unavailable(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main handles Redis unavailability"""
        mock_planner.return_value = ["step1", "step2", "step3"]
        mock_enqueue.side_effect = Exception("Redis connection failed")
        mock_execute.return_value = ("https://github.com/pr/2", "success", "trace-456")
        mock_recall.return_value = []
        
        main("Test goal", "owner/repo")
        
        mock_execute.assert_called_once()
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_github_unavailable(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main handles GitHub API unavailability"""
        mock_planner.return_value = ["step1"]
        mock_enqueue.return_value = ["job-1"]
        mock_execute.side_effect = Exception("GitHub API error")
        mock_recall.return_value = []
        
        main("Test goal", "owner/repo")
        
        mock_execute.assert_called_once()
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_supabase_unavailable(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main handles Supabase unavailability"""
        mock_planner.return_value = ["step1"]
        mock_enqueue.return_value = ["job-1"]
        mock_execute.return_value = ("https://github.com/pr/3", "success", "trace-789")
        mock_recall.side_effect = Exception("Supabase connection failed")
        
        main("Test goal", "owner/repo")
        
        mock_recall.assert_called_once()
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_generates_trace_id(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main generates unique trace ID"""
        mock_planner.return_value = ["step1"]
        mock_enqueue.return_value = ["job-1"]
        
        trace_ids = []
        def capture_trace_id(goal, repo, trace_id):
            trace_ids.append(trace_id)
            return ("https://github.com/pr/1", "success", trace_id)
        
        mock_execute.side_effect = capture_trace_id
        mock_recall.return_value = []
        
        main("Test goal", "owner/repo")
        
        assert len(trace_ids) == 1
        assert trace_ids[0] is not None
    
    @patch('graph.recall_top')
    @patch('graph.execute')
    @patch('graph.enqueue')
    @patch('graph.planner')
    def test_main_uses_idempotency_key(self, mock_planner, mock_enqueue, mock_execute, mock_recall):
        """Test main uses idempotency key for queue"""
        mock_planner.return_value = ["step1", "step2"]
        mock_enqueue.return_value = ["job-1", "job-2"]
        mock_execute.return_value = ("https://github.com/pr/1", "success", "trace-123")
        mock_recall.return_value = []
        
        goal = "Test goal with idempotency"
        main(goal, "owner/repo")
        
        call_args = mock_enqueue.call_args
        assert call_args[1]['idempotency_key'] is not None
