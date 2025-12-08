"""
LangGraph Advisor Nodes Tests

Tests for the advisor nodes in langgraph_orchestrator.py to improve coverage.
These tests focus on the decision logic, routing functions, and fallback behaviors.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage


class TestDecisionNode:
    """Tests for decision_node"""
    
    def _create_base_state(self):
        """Create a base state for testing"""
        return {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-decision-123",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "https://github.com/test/pr/1",
            "pr_number": 1,
            "ci_state": "success",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {},
            "review_severity": "none",
            "code_quality_score": 85
        }
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_approve_success(self, mock_get_metrics):
        """Test decision_node approves when CI passes and quality is high"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        result = decision_node(state)
        
        assert result["merge_decision"] == "approve"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_needs_fix_ci_failure(self, mock_get_metrics):
        """Test decision_node needs_fix when CI fails"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["ci_state"] = "failure"
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "needs_fix"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_needs_fix_error(self, mock_get_metrics):
        """Test decision_node needs_fix when error exists"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["error"] = "Some error occurred"
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "needs_fix"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_needs_fix_critical_issues(self, mock_get_metrics):
        """Test decision_node needs_fix when critical issues found"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["review_severity"] = "critical"
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "needs_fix"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_needs_fix_low_quality(self, mock_get_metrics):
        """Test decision_node needs_fix when quality score is too low"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["code_quality_score"] = 40
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "needs_fix"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_request_changes_high_severity(self, mock_get_metrics):
        """Test decision_node request_changes when high severity issues found"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["review_severity"] = "high"
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "request_changes"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_request_changes_medium_quality(self, mock_get_metrics):
        """Test decision_node request_changes when quality is medium"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["code_quality_score"] = 60
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "request_changes"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_decision_pending_ci_unknown(self, mock_get_metrics):
        """Test decision_node pending when CI state is unknown"""
        from langgraph_orchestrator import decision_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["ci_state"] = "pending"
        
        result = decision_node(state)
        
        assert result["merge_decision"] == "pending"


class TestShouldFixOrFinalize:
    """Tests for should_fix_or_finalize"""
    
    def test_fix_when_needs_fix_and_retries_available(self):
        """Test routing to fix when needs_fix and retries available"""
        from langgraph_orchestrator import should_fix_or_finalize
        
        state = {
            "merge_decision": "needs_fix",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics
            
            result = should_fix_or_finalize(state)
        
        assert result == "fix"
    
    def test_finalize_when_needs_fix_max_retries(self):
        """Test routing to finalize when max retries reached"""
        from langgraph_orchestrator import should_fix_or_finalize
        
        state = {
            "merge_decision": "needs_fix",
            "retry_count": 3,
            "trace_id": "test-123"
        }
        
        with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics
            
            result = should_fix_or_finalize(state)
        
        assert result == "finalize"
    
    def test_monitor_ci_when_pending(self):
        """Test routing to monitor_ci when decision is pending"""
        from langgraph_orchestrator import should_fix_or_finalize
        
        state = {
            "merge_decision": "pending",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics
            
            result = should_fix_or_finalize(state)
        
        assert result == "monitor_ci"
    
    def test_finalize_when_approved(self):
        """Test routing to finalize when approved"""
        from langgraph_orchestrator import should_fix_or_finalize
        
        state = {
            "merge_decision": "approve",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics
            
            result = should_fix_or_finalize(state)
        
        assert result == "finalize"
    
    def test_finalize_when_request_changes(self):
        """Test routing to finalize when request_changes"""
        from langgraph_orchestrator import should_fix_or_finalize
        
        state = {
            "merge_decision": "request_changes",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics
            
            result = should_fix_or_finalize(state)
        
        assert result == "finalize"


class TestPolicyEnforcementNode:
    """Tests for policy_enforcement_node"""
    
    def _create_base_state(self):
        """Create a base state for testing"""
        return {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-policy-123",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {},
            "task_type": "faq_update",
            "security_risk": "info",
            "governance_risk": "info",
            "cost_risk": "info",
            "permission_risk": "info"
        }
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_policy_enforcement_all_pass(self, mock_get_metrics):
        """Test policy_enforcement_node when all checks pass (advisory mode - default)"""
        from langgraph_orchestrator import policy_enforcement_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        result = policy_enforcement_node(state)
        
        # In advisory mode (default), policy is never blocked
        assert result["policy_blocked"] is False
        assert result["policy_block_reason"] == ""
        mock_metrics.record_node_start.assert_called_once()
    
    @patch('common.config.settings.get_settings')
    @patch('langgraph_orchestrator._get_metrics')
    def test_policy_enforcement_security_blocked_in_block_critical_mode(self, mock_get_metrics, mock_get_settings):
        """Test policy_enforcement_node blocks when security risk is critical in block_critical mode"""
        from langgraph_orchestrator import policy_enforcement_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings = Mock()
        mock_settings.security_enforcement_mode = "block_critical"
        mock_get_settings.return_value = mock_settings
        
        state = self._create_base_state()
        state["security_risk"] = "critical"
        
        result = policy_enforcement_node(state)
        
        assert result["policy_blocked"] is True
        assert "security" in result["policy_block_reason"].lower()
    
    @patch('common.config.settings.get_settings')
    @patch('langgraph_orchestrator._get_metrics')
    def test_policy_enforcement_governance_blocked_in_block_high_mode(self, mock_get_metrics, mock_get_settings):
        """Test policy_enforcement_node blocks when governance risk is high in block_high mode"""
        from langgraph_orchestrator import policy_enforcement_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings = Mock()
        mock_settings.security_enforcement_mode = "block_high"
        mock_get_settings.return_value = mock_settings
        
        state = self._create_base_state()
        state["governance_risk"] = "high"
        
        result = policy_enforcement_node(state)
        
        assert result["policy_blocked"] is True
        assert "governance" in result["policy_block_reason"].lower()
    
    @patch('common.config.settings.get_settings')
    @patch('langgraph_orchestrator._get_metrics')
    def test_policy_enforcement_cost_blocked_in_block_all_mode(self, mock_get_metrics, mock_get_settings):
        """Test policy_enforcement_node blocks when cost risk is low in block_all mode"""
        from langgraph_orchestrator import policy_enforcement_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings = Mock()
        mock_settings.security_enforcement_mode = "block_all"
        mock_get_settings.return_value = mock_settings
        
        state = self._create_base_state()
        state["cost_risk"] = "low"
        
        result = policy_enforcement_node(state)
        
        assert result["policy_blocked"] is True
        assert "cost" in result["policy_block_reason"].lower()
    
    @patch('common.config.settings.get_settings')
    @patch('langgraph_orchestrator._get_metrics')
    def test_policy_enforcement_permission_blocked_in_block_all_mode(self, mock_get_metrics, mock_get_settings):
        """Test policy_enforcement_node blocks when permission risk is medium in block_all mode"""
        from langgraph_orchestrator import policy_enforcement_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings = Mock()
        mock_settings.security_enforcement_mode = "block_all"
        mock_get_settings.return_value = mock_settings
        
        state = self._create_base_state()
        state["permission_risk"] = "medium"
        
        result = policy_enforcement_node(state)
        
        assert result["policy_blocked"] is True
        assert "permission" in result["policy_block_reason"].lower()


class TestShouldProceedAfterPolicy:
    """Tests for should_proceed_after_policy"""
    
    def test_execute_when_not_blocked(self):
        """Test routing when policy is not blocked"""
        from langgraph_orchestrator import should_proceed_after_policy
        
        state = {
            "policy_blocked": False,
            "trace_id": "test-123"
        }
        
        result = should_proceed_after_policy(state)
        
        # Returns "execute" when not blocked
        assert result == "execute"
    
    def test_finalize_when_blocked(self):
        """Test routing when policy is blocked"""
        from langgraph_orchestrator import should_proceed_after_policy
        
        state = {
            "policy_blocked": True,
            "trace_id": "test-123"
        }
        
        result = should_proceed_after_policy(state)
        
        assert result == "finalize"


class TestFinalizerNode:
    """Tests for finalizer_node"""
    
    def _create_base_state(self):
        """Create a base state for testing"""
        return {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-finalizer-123",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "https://github.com/test/pr/1",
            "pr_number": 1,
            "ci_state": "success",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {},
            "merge_decision": "approve",
            "policy_blocked": False
        }
    
    @patch('langgraph_orchestrator._observe_failure_for_learning')
    @patch('langgraph_orchestrator._get_metrics')
    def test_finalizer_success(self, mock_get_metrics, mock_observe):
        """Test finalizer_node with successful completion"""
        from langgraph_orchestrator import finalizer_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        result = finalizer_node(state)
        
        assert "final_result" in result
        assert result["final_result"]["status"] == "success"
        mock_metrics.record_node_start.assert_called_once()
        mock_metrics.record_node_complete.assert_called_once()
    
    @patch('langgraph_orchestrator._observe_failure_for_learning')
    @patch('langgraph_orchestrator._get_metrics')
    def test_finalizer_error(self, mock_get_metrics, mock_observe):
        """Test finalizer_node with error"""
        from langgraph_orchestrator import finalizer_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["error"] = "Some error"
        state["merge_decision"] = "needs_fix"
        
        result = finalizer_node(state)
        
        # Status is "error" when error exists (not "failure")
        assert result["final_result"]["status"] == "error"
        mock_observe.assert_called_once()
    
    @patch('langgraph_orchestrator._observe_failure_for_learning')
    @patch('langgraph_orchestrator._get_metrics')
    def test_finalizer_policy_blocked(self, mock_get_metrics, mock_observe):
        """Test finalizer_node when policy blocked"""
        from langgraph_orchestrator import finalizer_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["policy_blocked"] = True
        state["policy_block_reason"] = "Security violation"
        
        result = finalizer_node(state)
        
        assert result["final_result"]["status"] == "blocked"


class TestCIMonitorNode:
    """Tests for ci_monitor_node"""
    
    def _create_base_state(self):
        """Create a base state for testing"""
        return {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-ci-123",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "https://github.com/test/pr/1",
            "pr_number": 1,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
    
    @patch('langgraph_orchestrator._get_metrics')
    @patch('tools.github_api.get_pr_checks')
    @patch('tools.github_api.get_repo')
    def test_ci_monitor_success(self, mock_get_repo, mock_get_checks, mock_get_metrics):
        """Test ci_monitor_node with successful CI check"""
        from langgraph_orchestrator import ci_monitor_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_get_checks.return_value = ("success", {"check1": "passed"})
        
        state = self._create_base_state()
        result = ci_monitor_node(state)
        
        assert result["ci_state"] == "success"
        assert result["ci_checks"] == {"check1": "passed"}
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_ci_monitor_no_pr_number(self, mock_get_metrics):
        """Test ci_monitor_node when no PR number available"""
        from langgraph_orchestrator import ci_monitor_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["pr_number"] = None
        
        result = ci_monitor_node(state)
        
        assert result["ci_state"] == "unknown"
    
    @patch('langgraph_orchestrator._get_metrics')
    @patch('tools.github_api.get_pr_checks')
    @patch('tools.github_api.get_repo')
    def test_ci_monitor_exception(self, mock_get_repo, mock_get_checks, mock_get_metrics):
        """Test ci_monitor_node handles exceptions gracefully"""
        from langgraph_orchestrator import ci_monitor_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_get_repo.side_effect = Exception("GitHub API error")
        
        state = self._create_base_state()
        result = ci_monitor_node(state)
        
        assert result["ci_state"] == "error"
        assert result["error"] == "GitHub API error"


class TestReviewerNode:
    """Tests for reviewer_node
    
    The reviewer_node always calls _ci_only_review first, then optionally
    enhances with LLM review if use_llm_reviewer is True.
    """
    
    def _create_base_state(self):
        """Create a base state for testing"""
        return {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-reviewer-123",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "https://github.com/test/pr/1",
            "pr_number": 1,
            "ci_state": "success",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_reviewer_node_ci_only(self, mock_get_metrics):
        """Test reviewer_node with CI-only review (default)"""
        from langgraph_orchestrator import reviewer_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        result = reviewer_node(state)
        
        # CI-only review with success state gives score of 80
        assert result["code_quality_score"] == 80
        assert result["review_severity"] == "none"
        mock_metrics.record_node_start.assert_called_once()
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_reviewer_node_no_pr(self, mock_get_metrics):
        """Test reviewer_node when no PR available"""
        from langgraph_orchestrator import reviewer_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["pr_number"] = None
        state["pr_url"] = None
        
        result = reviewer_node(state)
        
        # No PR means default score of 100 (no review needed)
        assert result["code_quality_score"] == 100
        assert result["review_severity"] == "none"
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_reviewer_node_ci_failure(self, mock_get_metrics):
        """Test reviewer_node with CI failure"""
        from langgraph_orchestrator import reviewer_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        state = self._create_base_state()
        state["ci_state"] = "failure"
        
        result = reviewer_node(state)
        
        # CI failure gives lower score
        assert result["code_quality_score"] < 80
        assert result["review_severity"] in ["high", "critical"]


class TestEvaluationNode:
    """Tests for evaluation_node"""
    
    def _create_base_state(self):
        """Create a base state for testing"""
        return {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-eval-123",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "https://github.com/test/pr/1",
            "pr_number": 1,
            "ci_state": "success",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {"status": "success"}
        }
    
    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator._get_agent_eval')
    @patch('langgraph_orchestrator._get_metrics')
    def test_evaluation_node_success(self, mock_get_metrics, mock_get_eval, mock_settings):
        """Test evaluation_node with successful evaluation (no regression)"""
        from langgraph_orchestrator import evaluation_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings.enable_agent_eval = True
        mock_settings.agent_eval_success_rate_threshold = 0.8
        mock_settings.agent_eval_ci_pass_rate_threshold = 0.8
        mock_settings.agent_eval_fixer_success_threshold = 0.5
        mock_settings.agent_eval_baseline_sample_size = 100
        mock_settings.agent_eval_regression_alert_enabled = True
        
        mock_eval = Mock()
        mock_eval.detect_capability_regression.return_value = {
            "has_regression": False,
            "has_critical_regression": False,
            "metrics": {}
        }
        mock_get_eval.return_value = mock_eval
        
        state = self._create_base_state()
        result = evaluation_node(state)
        
        assert result["evaluation_health_status"] == "healthy"
        assert result["evaluation_has_regression"] is False
        mock_metrics.record_node_start.assert_called_once()
    
    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator._get_agent_eval')
    @patch('langgraph_orchestrator._get_metrics')
    def test_evaluation_node_regression_detected(self, mock_get_metrics, mock_get_eval, mock_settings):
        """Test evaluation_node when regression is detected"""
        from langgraph_orchestrator import evaluation_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings.enable_agent_eval = True
        mock_settings.agent_eval_success_rate_threshold = 0.8
        mock_settings.agent_eval_ci_pass_rate_threshold = 0.8
        mock_settings.agent_eval_fixer_success_threshold = 0.5
        mock_settings.agent_eval_baseline_sample_size = 100
        mock_settings.agent_eval_regression_alert_enabled = True
        
        mock_eval = Mock()
        mock_eval.detect_capability_regression.return_value = {
            "has_regression": True,
            "has_critical_regression": False,
            "metrics": {"success_rate": 0.7}
        }
        mock_get_eval.return_value = mock_eval
        
        state = self._create_base_state()
        result = evaluation_node(state)
        
        assert result["evaluation_health_status"] == "degraded"
        assert result["evaluation_has_regression"] is True
    
    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator._get_agent_eval')
    @patch('langgraph_orchestrator._get_metrics')
    def test_evaluation_node_critical_regression(self, mock_get_metrics, mock_get_eval, mock_settings):
        """Test evaluation_node when critical regression is detected"""
        from langgraph_orchestrator import evaluation_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings.enable_agent_eval = True
        mock_settings.agent_eval_success_rate_threshold = 0.8
        mock_settings.agent_eval_ci_pass_rate_threshold = 0.8
        mock_settings.agent_eval_fixer_success_threshold = 0.5
        mock_settings.agent_eval_baseline_sample_size = 100
        mock_settings.agent_eval_regression_alert_enabled = True
        
        mock_eval = Mock()
        mock_eval.detect_capability_regression.return_value = {
            "has_regression": True,
            "has_critical_regression": True,
            "metrics": {"success_rate": 0.3}
        }
        mock_get_eval.return_value = mock_eval
        
        state = self._create_base_state()
        result = evaluation_node(state)
        
        assert result["evaluation_health_status"] == "critical"
        assert result["evaluation_has_regression"] is True
    
    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator._get_agent_eval')
    @patch('langgraph_orchestrator._get_metrics')
    def test_evaluation_node_disabled(self, mock_get_metrics, mock_get_eval, mock_settings):
        """Test evaluation_node when agent eval is disabled"""
        from langgraph_orchestrator import evaluation_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings.enable_agent_eval = False
        
        state = self._create_base_state()
        result = evaluation_node(state)
        
        assert result["evaluation_health_status"] == "unknown"
        assert result["evaluation_has_regression"] is False
    
    @patch('langgraph_orchestrator.settings')
    @patch('langgraph_orchestrator._get_agent_eval')
    @patch('langgraph_orchestrator._get_metrics')
    def test_evaluation_node_exception(self, mock_get_metrics, mock_get_eval, mock_settings):
        """Test evaluation_node handles exceptions gracefully"""
        from langgraph_orchestrator import evaluation_node
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_settings.enable_agent_eval = True
        mock_settings.agent_eval_success_rate_threshold = 0.8
        mock_settings.agent_eval_ci_pass_rate_threshold = 0.8
        mock_settings.agent_eval_fixer_success_threshold = 0.5
        mock_settings.agent_eval_baseline_sample_size = 100
        
        mock_eval = Mock()
        mock_eval.detect_capability_regression.side_effect = Exception("Evaluation failed")
        mock_get_eval.return_value = mock_eval
        
        state = self._create_base_state()
        result = evaluation_node(state)
        
        assert result["evaluation_health_status"] == "unknown"
        assert result["evaluation_has_regression"] is False


class TestNodeMetricsDecorator:
    """Tests for node_metrics decorator"""
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_node_metrics_decorator(self, mock_get_metrics):
        """Test node_metrics decorator records metrics correctly"""
        from langgraph_orchestrator import node_metrics
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        @node_metrics("test_node")
        def test_func(state, success):
            success[0] = True
            return state
        
        state = {"trace_id": "test-123"}
        result = test_func(state)
        
        assert result == state
        mock_metrics.record_node_start.assert_called_once_with("test_node", "test-123")
        mock_metrics.record_node_complete.assert_called_once()
    
    @patch('langgraph_orchestrator._get_metrics')
    def test_node_metrics_decorator_failure(self, mock_get_metrics):
        """Test node_metrics decorator records failure correctly"""
        from langgraph_orchestrator import node_metrics
        
        mock_metrics = Mock()
        mock_get_metrics.return_value = mock_metrics
        
        @node_metrics("test_node")
        def test_func(state, success):
            # Don't set success[0] = True, simulating failure
            return state
        
        state = {"trace_id": "test-123"}
        result = test_func(state)
        
        assert result == state
        mock_metrics.record_node_start.assert_called_once()
        # record_node_complete should be called with success=False
        call_args = mock_metrics.record_node_complete.call_args
        assert call_args[1]["success"] is False


class TestGetLearningContextForPlanner:
    """Tests for _get_learning_context_for_planner"""
    
    @patch('langgraph_orchestrator.settings')
    def test_learning_context_disabled(self, mock_settings):
        """Test learning context returns empty when disabled"""
        from langgraph_orchestrator import _get_learning_context_for_planner
        
        mock_settings.enable_failure_learning_context = False
        
        result = _get_learning_context_for_planner("test goal")
        
        assert result == ""
    
    @patch('langgraph_orchestrator.settings')
    def test_learning_context_import_error(self, mock_settings):
        """Test learning context handles import error gracefully"""
        from langgraph_orchestrator import _get_learning_context_for_planner
        
        mock_settings.enable_failure_learning_context = True
        
        # This should handle the ImportError gracefully
        result = _get_learning_context_for_planner("test goal")
        
        # Should return empty string on error
        assert isinstance(result, str)


class TestObserveFailureForLearning:
    """Tests for _observe_failure_for_learning
    
    This function calls observe_failure from observer_node module
    to record failures to pgvector for future learning.
    The import happens inside the function, so we test the resilience behavior.
    """
    
    def test_observe_failure_does_not_raise(self):
        """Test _observe_failure_for_learning doesn't raise exceptions"""
        from langgraph_orchestrator import _observe_failure_for_learning
        
        state = {
            "trace_id": "test-123",
            "goal": "Test goal",
            "error": "Test error",
            "repo": "test/repo",
            "task_type": "faq_update"
        }
        
        # The function is designed to never raise exceptions
        # It catches ImportError and other exceptions gracefully
        _observe_failure_for_learning(state)
        # If we get here without exception, the test passes
    
    def test_observe_failure_with_saved_result(self):
        """Test _observe_failure_for_learning with mocked observer_node"""
        import sys
        from unittest.mock import MagicMock
        
        # Create a mock module
        mock_observer = MagicMock()
        mock_observer.observe_failure.return_value = {
            "saved_to_pgvector": True,
            "pair_id": "test-pair-123",
            "error_type": "workflow_error"
        }
        
        # Temporarily inject the mock module
        original = sys.modules.get('observer_node')
        sys.modules['observer_node'] = mock_observer
        
        try:
            # Need to reimport to pick up the mock
            import importlib
            import langgraph_orchestrator
            importlib.reload(langgraph_orchestrator)
            
            state = {
                "trace_id": "test-123",
                "goal": "Test goal",
                "error": "Test error",
                "repo": "test/repo",
                "task_type": "faq_update"
            }
            
            langgraph_orchestrator._observe_failure_for_learning(state)
            
            mock_observer.observe_failure.assert_called_once()
        finally:
            # Restore original module state
            if original is not None:
                sys.modules['observer_node'] = original
            elif 'observer_node' in sys.modules:
                del sys.modules['observer_node']
            # Reload to restore original state
            import importlib
            import langgraph_orchestrator
            importlib.reload(langgraph_orchestrator)


class TestShouldRetryOrFinish:
    """Tests for should_retry_or_finish
    
    This function determines CI monitoring flow:
    - Returns "finalize" if error exists or CI success
    - Returns "fix" if CI failure and retries available
    - Returns "monitor_ci" otherwise (pending state)
    """
    
    def test_finalize_when_error_exists(self):
        """Test routing to finalize when error exists"""
        from langgraph_orchestrator import should_retry_or_finish
        
        state = {
            "error": "Some error",
            "ci_state": "pending",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "finalize"
    
    def test_finalize_when_ci_success(self):
        """Test routing to finalize when CI succeeds"""
        from langgraph_orchestrator import should_retry_or_finish
        
        state = {
            "error": None,
            "ci_state": "success",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "finalize"
    
    def test_fix_when_ci_failure_and_retries_available(self):
        """Test routing to fix when CI fails and retries available"""
        from langgraph_orchestrator import should_retry_or_finish
        
        state = {
            "error": None,
            "ci_state": "failure",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "fix"
    
    def test_finalize_when_ci_failure_max_retries(self):
        """Test routing to finalize when CI fails but max retries reached"""
        from langgraph_orchestrator import should_retry_or_finish
        
        state = {
            "error": None,
            "ci_state": "failure",
            "retry_count": 3,
            "trace_id": "test-123"
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "finalize"
    
    def test_monitor_ci_when_pending(self):
        """Test routing to monitor_ci when CI is pending"""
        from langgraph_orchestrator import should_retry_or_finish
        
        state = {
            "error": None,
            "ci_state": "pending",
            "retry_count": 0,
            "trace_id": "test-123"
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "monitor_ci"
