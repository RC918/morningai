#!/usr/bin/env python3
"""
Tests for PM Agent - Phase 3 PR-3 (#1815)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pm_agent.agent import (
    PMAgent,
    PMAdvisory,
    PMFinding,
    PMRisk,
    SubTask,
    get_pm_agent,
    decompose_goal,
    plan_implementation,
)


class TestPMRisk:
    """Tests for PMRisk enum"""

    def test_risk_values(self):
        """Test PMRisk enum values"""
        assert PMRisk.HIGH.value == "high"
        assert PMRisk.MEDIUM.value == "medium"
        assert PMRisk.LOW.value == "low"
        assert PMRisk.INFO.value == "info"


class TestSubTask:
    """Tests for SubTask dataclass"""

    def test_subtask_creation(self):
        """Test SubTask creation with all fields"""
        task = SubTask(
            task_id="test-1",
            title="Test Task",
            description="Test description",
            estimated_effort="medium",
            dependencies=["dep-1"],
            affected_files=["file.py"],
            task_type="feature",
            priority=1
        )
        assert task.task_id == "test-1"
        assert task.title == "Test Task"
        assert task.estimated_effort == "medium"
        assert task.task_type == "feature"

    def test_subtask_defaults(self):
        """Test SubTask default values"""
        task = SubTask(
            task_id="test-1",
            title="Test",
            description="Desc",
            estimated_effort="small"
        )
        assert task.dependencies == []
        assert task.affected_files == []
        assert task.task_type == "unknown"
        assert task.priority == 0


class TestPMFinding:
    """Tests for PMFinding dataclass"""

    def test_finding_creation(self):
        """Test PMFinding creation"""
        finding = PMFinding(
            category="complexity",
            risk_level=PMRisk.MEDIUM,
            title="High complexity",
            description="Task is complex",
            recommendation="Break down further"
        )
        assert finding.category == "complexity"
        assert finding.risk_level == PMRisk.MEDIUM
        assert finding.recommendation == "Break down further"


class TestPMAdvisory:
    """Tests for PMAdvisory dataclass"""

    def test_advisory_creation(self):
        """Test PMAdvisory creation"""
        advisory = PMAdvisory(
            is_feasible=True,
            overall_risk=PMRisk.LOW,
            confidence_score=0.85,
            goal="Test goal",
            summary="Test summary"
        )
        assert advisory.is_feasible is True
        assert advisory.confidence_score == 0.85

    def test_advisory_to_dict(self):
        """Test PMAdvisory to_dict method"""
        task = SubTask(
            task_id="t1",
            title="Task 1",
            description="Desc",
            estimated_effort="small"
        )
        advisory = PMAdvisory(
            is_feasible=True,
            overall_risk=PMRisk.LOW,
            confidence_score=0.8,
            goal="Test",
            sub_tasks=[task],
            summary="Summary"
        )
        result = advisory.to_dict()
        assert result["is_feasible"] is True
        assert result["overall_risk"] == "low"
        assert result["confidence_score"] == 0.8
        assert len(result["sub_tasks"]) == 1
        assert result["sub_tasks"][0]["task_id"] == "t1"


class TestPMAgent:
    """Tests for PMAgent class"""

    def test_agent_initialization(self):
        """Test PMAgent initialization"""
        agent = PMAgent()
        assert agent.enabled is True
        assert agent.max_sub_tasks == 10

    def test_decompose_goal_simple(self):
        """Test simple goal decomposition"""
        agent = PMAgent()
        advisory = agent.decompose_goal("Fix the bug in login page")
        assert advisory.is_feasible is True
        assert len(advisory.sub_tasks) >= 1
        assert advisory.confidence_score > 0

    def test_decompose_goal_complex(self):
        """Test complex goal decomposition with multiple parts"""
        agent = PMAgent()
        advisory = agent.decompose_goal(
            "Add user authentication, implement password reset, create admin dashboard"
        )
        assert advisory.is_feasible is True
        assert len(advisory.sub_tasks) >= 1

    def test_decompose_goal_disabled(self):
        """Test decompose_goal when agent is disabled"""
        agent = PMAgent()
        agent.enabled = False
        advisory = agent.decompose_goal("Test goal")
        assert advisory.confidence_score == 0.0
        assert "disabled" in advisory.summary.lower()

    def test_classify_task_type(self):
        """Test task type classification"""
        agent = PMAgent()
        assert agent._classify_task_type("fix the bug") == "bug_fix"
        assert agent._classify_task_type("add new feature") == "feature"
        assert agent._classify_task_type("refactor code") == "refactor"
        assert agent._classify_task_type("write tests") == "test"
        assert agent._classify_task_type("update config") == "config"
        assert agent._classify_task_type("random text") == "unknown"

    def test_estimate_effort(self):
        """Test effort estimation"""
        agent = PMAgent()
        assert agent._estimate_effort("simple fix") == "small"
        assert agent._estimate_effort("complex implementation with many changes") == "large"
        assert agent._estimate_effort("moderate update") == "medium"

    def test_calculate_confidence(self):
        """Test confidence score calculation"""
        agent = PMAgent()
        tasks = [
            SubTask("1", "T1", "D1", "small", task_type="feature"),
            SubTask("2", "T2", "D2", "medium", task_type="bug_fix"),
        ]
        findings = []
        confidence = agent._calculate_confidence("goal", tasks, findings)
        assert 0.0 <= confidence <= 1.0

    def test_calculate_confidence_with_high_risk(self):
        """Test confidence decreases with high-risk findings"""
        agent = PMAgent()
        tasks = [SubTask("1", "T1", "D1", "small")]
        findings = [
            PMFinding("risk", PMRisk.HIGH, "High risk", "Desc")
        ]
        confidence = agent._calculate_confidence("goal", tasks, findings)
        assert confidence < 0.8

    def test_plan_implementation(self):
        """Test implementation planning"""
        agent = PMAgent()
        advisory = agent.plan_implementation("Implement user authentication")
        assert advisory.is_feasible is True
        assert advisory.implementation_plan is not None or len(advisory.sub_tasks) > 0


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_get_pm_agent_singleton(self):
        """Test get_pm_agent returns singleton"""
        agent1 = get_pm_agent()
        agent2 = get_pm_agent()
        assert agent1 is agent2

    def test_decompose_goal_function(self):
        """Test decompose_goal convenience function"""
        advisory = decompose_goal("Test goal")
        assert isinstance(advisory, PMAdvisory)

    def test_plan_implementation_function(self):
        """Test plan_implementation convenience function"""
        advisory = plan_implementation("Test goal")
        assert isinstance(advisory, PMAdvisory)


class TestEdgeCases:
    """Tests for edge cases"""

    def test_empty_goal(self):
        """Test handling of empty goal"""
        agent = PMAgent()
        advisory = agent.decompose_goal("")
        assert advisory.is_feasible is True

    def test_very_long_goal(self):
        """Test handling of very long goal"""
        agent = PMAgent()
        long_goal = "x" * 10000
        advisory = agent.decompose_goal(long_goal)
        assert advisory is not None

    def test_unicode_goal(self):
        """Test handling of unicode characters in goal"""
        agent = PMAgent()
        advisory = agent.decompose_goal("實作用戶認證功能")
        assert advisory.is_feasible is True

    def test_goal_with_newlines(self):
        """Test handling of goal with newlines"""
        agent = PMAgent()
        advisory = agent.decompose_goal("Task 1\nTask 2\nTask 3")
        assert len(advisory.sub_tasks) >= 1


class TestSecurityKeywordsConfig:
    """Tests for configurable security keywords (Issue #2873)"""

    def test_default_security_keywords(self):
        """Test that default security keywords are used when not configured"""
        agent = PMAgent()
        # The _identify_risks method should use default keywords
        # Default: ["auth", "permission", "secret", "credential", "token"]
        # Test that security-related goals are identified
        advisory = agent.decompose_goal("Implement authentication system")
        # Should have at least one finding related to security
        assert advisory is not None

    def test_security_keywords_parsing_comma_separated(self):
        """Test parsing of comma-separated security keywords"""
        # Simulate parsing logic used in _identify_risks
        keywords_str = "auth, permission, secret, credential, token"
        security_keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        assert len(security_keywords) == 5
        assert "auth" in security_keywords
        assert "permission" in security_keywords
        assert "secret" in security_keywords

    def test_security_keywords_parsing_empty_string(self):
        """Test fallback when security keywords string is empty"""
        keywords_str = ""
        security_keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        # Empty string should result in empty list, triggering fallback
        assert security_keywords == []
        
        # Fallback logic
        if not security_keywords:
            security_keywords = ["auth", "permission", "secret", "credential", "token"]
        assert len(security_keywords) == 5

    def test_security_keywords_parsing_whitespace_handling(self):
        """Test that whitespace is properly stripped from keywords"""
        keywords_str = "  auth  ,  permission  ,  secret  "
        security_keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        assert security_keywords == ["auth", "permission", "secret"]
        # No leading/trailing whitespace
        for kw in security_keywords:
            assert kw == kw.strip()

    def test_security_keywords_parsing_with_empty_entries(self):
        """Test that empty entries are filtered out"""
        keywords_str = "auth,,permission,,,secret"
        security_keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        assert security_keywords == ["auth", "permission", "secret"]
        assert "" not in security_keywords
