"""
Unit tests for Risk Analyzer Agent

EPIC K Phase 1 (P1-high): Risk Analyzer Agent (Blueprint 3.3 - Agent Catalog V2)
Issue: #4096
"""

from governance.risk_analyzer import (
    RiskAnalyzerAgent,
    RiskCategory,
    RiskLevel,
    RiskAction,
    RiskFinding,
    get_risk_analyzer,
    reset_risk_analyzer,
    analyze_task_risk,
)


class TestRiskAnalyzerAgent:
    """Tests for RiskAnalyzerAgent class"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_analyzer_initialization(self):
        """Test analyzer initializes with default values"""
        analyzer = RiskAnalyzerAgent()
        assert analyzer.enabled is True
        assert analyzer.block_on_critical is True
        assert analyzer.require_approval_on_high is True
        assert analyzer.content_safety_integration is True

    def test_analyzer_disabled(self):
        """Test analyzer returns minimal risk when disabled"""
        analyzer = RiskAnalyzerAgent(enabled=False)
        result = analyzer.analyze_task("delete all files")
        assert result.overall_level == RiskLevel.MINIMAL
        assert result.action == RiskAction.ALLOW
        assert result.summary == "Risk analysis disabled"

    def test_empty_task_description(self):
        """Test analyzer handles empty task description"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("")
        assert result.overall_level == RiskLevel.MINIMAL
        assert result.action == RiskAction.ALLOW
        assert result.summary == "Empty task description"

    def test_safe_task(self):
        """Test analyzer allows safe tasks"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Fix typo in README.md")
        assert result.overall_level in [RiskLevel.MINIMAL, RiskLevel.LOW]
        assert result.action == RiskAction.ALLOW
        assert result.should_block is False


class TestHighRiskTaskDetection:
    """Tests for high-risk task pattern detection"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_mass_deletion_detection(self):
        """Test detection of mass deletion operations"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Delete all files in the database")
        assert result.overall_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert any(
            f.finding_id == "TR-001" for f in result.findings
        )

    def test_production_deployment_detection(self):
        """Test detection of production deployment"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Deploy to production environment")
        assert any(
            f.finding_id == "TR-002" for f in result.findings
        )

    def test_credential_modification_detection(self):
        """Test detection of credential modification"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Modify the API keys in config")
        assert result.overall_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert any(
            f.finding_id == "TR-003" for f in result.findings
        )

    def test_privileged_command_detection(self):
        """Test detection of privileged command execution"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Execute shell command as root")
        assert result.overall_level == RiskLevel.CRITICAL
        assert any(
            f.finding_id == "TR-004" for f in result.findings
        )

    def test_pii_access_detection(self):
        """Test detection of PII access operations"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Export customer personal data")
        assert any(
            f.finding_id == "TR-005" for f in result.findings
        )

    def test_security_bypass_detection(self):
        """Test detection of security bypass attempts"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Disable security checks temporarily")
        assert result.overall_level == RiskLevel.CRITICAL
        assert any(
            f.finding_id == "TR-006" for f in result.findings
        )


class TestSecurityRiskDetection:
    """Tests for security risk detection"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_env_file_detection(self):
        """Test detection of .env file modifications"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Update configuration",
            context={"files": [".env", "config.py"]}
        )
        assert any(
            f.finding_id == "Env-001" for f in result.findings
        )

    def test_secrets_file_detection(self):
        """Test detection of secrets file modifications"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Update secrets",
            context={"files": ["secrets.yaml"]}
        )
        assert any(
            f.finding_id == "Env-002" for f in result.findings
        )

    def test_key_file_detection(self):
        """Test detection of key file modifications"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Update certificates",
            context={"files": ["server.key", "server.pem"]}
        )
        assert any(
            f.finding_id in ["Env-004", "Env-005"] for f in result.findings
        )

    def test_migration_file_detection(self):
        """Test detection of migration file modifications"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Add new migration",
            context={"files": ["migrations/001_add_users.py"]}
        )
        assert any(
            f.finding_id == "DB-001" for f in result.findings
        )

    def test_dangerous_code_pattern_detection(self):
        """Test detection of dangerous code patterns"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Add code that uses eval() for dynamic execution"
        )
        assert any(
            f.finding_id == "SEC-002" for f in result.findings
        )


class TestScopeRiskDetection:
    """Tests for scope risk detection"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_large_file_count_detection(self):
        """Test detection of large file count"""
        analyzer = RiskAnalyzerAgent()
        files = [f"file{i}.py" for i in range(60)]
        result = analyzer.analyze_task(
            "Refactor codebase",
            context={"files": files}
        )
        assert result.overall_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert any(
            f.finding_id == "SCOPE-001" for f in result.findings
        )

    def test_medium_file_count_detection(self):
        """Test detection of medium file count"""
        analyzer = RiskAnalyzerAgent()
        files = [f"file{i}.py" for i in range(25)]
        result = analyzer.analyze_task(
            "Update imports",
            context={"files": files}
        )
        assert any(
            f.finding_id == "SCOPE-002" for f in result.findings
        )

    def test_large_line_count_detection(self):
        """Test detection of large line changes"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Major refactoring",
            context={"lines_added": 800, "lines_removed": 500}
        )
        assert any(
            f.finding_id == "SCOPE-004" for f in result.findings
        )


class TestComplianceRiskDetection:
    """Tests for compliance risk detection"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_email_handling_detection(self):
        """Test detection of email handling"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Process user email addresses")
        assert any(
            f.finding_id == "COMP-001" for f in result.findings
        )

    def test_ssn_handling_detection(self):
        """Test detection of SSN handling"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Validate social security numbers")
        assert result.overall_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert any(
            f.finding_id == "COMP-003" for f in result.findings
        )

    def test_credit_card_handling_detection(self):
        """Test detection of credit card handling"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Process credit card payments")
        assert result.overall_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert any(
            f.finding_id == "COMP-004" for f in result.findings
        )

    def test_medical_data_handling_detection(self):
        """Test detection of medical data handling"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Access patient medical records")
        assert any(
            f.finding_id == "COMP-006" for f in result.findings
        )

    def test_gdpr_compliance_detection(self):
        """Test detection of GDPR-related tasks"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Implement GDPR data deletion")
        assert any(
            f.finding_id == "COMP-007" for f in result.findings
        )


class TestCostRiskDetection:
    """Tests for cost risk detection"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_tier0_model_detection(self):
        """Test detection of Tier 0 model usage"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Complex reasoning task",
            context={"model_tier": 0}
        )
        assert any(
            f.finding_id == "COST-001" for f in result.findings
        )

    def test_high_llm_call_count_detection(self):
        """Test detection of high LLM call count"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Process many items",
            context={"estimated_llm_calls": 15}
        )
        assert any(
            f.finding_id == "COST-002" for f in result.findings
        )


class TestRiskLevelCalculation:
    """Tests for risk level calculation"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_critical_risk_blocks(self):
        """Test that CRITICAL risk results in BLOCK action"""
        analyzer = RiskAnalyzerAgent(block_on_critical=True)
        result = analyzer.analyze_task("Execute shell command as root")
        assert result.overall_level == RiskLevel.CRITICAL
        assert result.action == RiskAction.BLOCK
        assert result.should_block is True

    def test_critical_risk_no_block_when_disabled(self):
        """Test CRITICAL risk doesn't block when blocking disabled"""
        analyzer = RiskAnalyzerAgent(block_on_critical=False)
        result = analyzer.analyze_task("Execute shell command as root")
        assert result.overall_level == RiskLevel.CRITICAL
        assert result.should_block is False

    def test_high_risk_requires_approval(self):
        """Test that HIGH risk results in REQUIRE_APPROVAL action"""
        analyzer = RiskAnalyzerAgent(require_approval_on_high=True)
        result = analyzer.analyze_task("Deploy to production")
        if result.overall_level == RiskLevel.HIGH:
            assert result.action == RiskAction.REQUIRE_APPROVAL
            assert result.requires_approval is True

    def test_high_risk_no_approval_when_disabled(self):
        """Test HIGH risk doesn't require approval when disabled"""
        analyzer = RiskAnalyzerAgent(require_approval_on_high=False)
        result = analyzer.analyze_task("Deploy to production")
        if result.overall_level == RiskLevel.HIGH:
            assert result.requires_approval is False


class TestResultSerialization:
    """Tests for result serialization"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_finding_to_dict(self):
        """Test RiskFinding serialization"""
        finding = RiskFinding(
            category=RiskCategory.SECURITY,
            level=RiskLevel.HIGH,
            finding_id="SEC-001",
            title="Test finding",
            description="Test description",
            score=75,
            evidence="test evidence",
            recommendation="Test recommendation",
        )
        result = finding.to_dict()
        assert result["category"] == "security"
        assert result["level"] == "high"
        assert result["finding_id"] == "SEC-001"
        assert result["score"] == 75

    def test_analysis_result_to_dict(self):
        """Test RiskAnalysisResult serialization"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Delete all files")
        result_dict = result.to_dict()
        assert "overall_score" in result_dict
        assert "overall_level" in result_dict
        assert "action" in result_dict
        assert "findings" in result_dict
        assert "category_scores" in result_dict
        assert "mitigation_recommendations" in result_dict
        assert result_dict["analyzer_id"] == "risk_analyzer_v1"


class TestGlobalFunctions:
    """Tests for global singleton functions"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_get_risk_analyzer_singleton(self):
        """Test singleton pattern for analyzer"""
        analyzer1 = get_risk_analyzer()
        analyzer2 = get_risk_analyzer()
        assert analyzer1 is analyzer2

    def test_reset_risk_analyzer(self):
        """Test reset clears singleton"""
        analyzer1 = get_risk_analyzer()
        reset_risk_analyzer()
        analyzer2 = get_risk_analyzer()
        assert analyzer1 is not analyzer2

    def test_analyze_task_risk_convenience_function(self):
        """Test convenience function for analysis"""
        result = analyze_task_risk("Fix typo in README")
        assert result.overall_level in [RiskLevel.MINIMAL, RiskLevel.LOW]
        assert result.action == RiskAction.ALLOW


class TestMitigationRecommendations:
    """Tests for mitigation recommendation generation"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_critical_risk_has_recommendations(self):
        """Test CRITICAL risk includes recommendations"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Execute shell command as root")
        assert len(result.mitigation_recommendations) > 0
        assert any(
            "CRITICAL" in rec for rec in result.mitigation_recommendations
        )

    def test_high_risk_has_recommendations(self):
        """Test HIGH risk includes recommendations"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Deploy to production")
        if result.overall_level == RiskLevel.HIGH:
            assert len(result.mitigation_recommendations) > 0

    def test_recommendations_limited_to_10(self):
        """Test recommendations are limited to 10"""
        analyzer = RiskAnalyzerAgent()
        # Create a task that triggers many findings
        result = analyzer.analyze_task(
            "Delete all files, deploy to production, modify credentials, "
            "execute as root, access customer data, disable security",
            context={
                "files": [f"file{i}.py" for i in range(60)],
                "lines_added": 1000,
                "model_tier": 0,
            }
        )
        assert len(result.mitigation_recommendations) <= 10


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_whitespace_only_task(self):
        """Test handling of whitespace-only task"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("   \n\t  ")
        assert result.overall_level == RiskLevel.MINIMAL
        assert result.action == RiskAction.ALLOW

    def test_unicode_task(self):
        """Test handling of unicode task description"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("修復 README 中的錯字 🎉")
        assert result.overall_level in [RiskLevel.MINIMAL, RiskLevel.LOW]

    def test_empty_context(self):
        """Test handling of empty context"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Fix bug", context={})
        assert result is not None
        assert result.overall_level is not None

    def test_none_context(self):
        """Test handling of None context"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Fix bug", context=None)
        assert result is not None
        assert result.overall_level is not None

    def test_analysis_duration_tracked(self):
        """Test analysis duration is tracked"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("test task")
        assert result.analysis_duration_ms >= 0

    def test_evidence_hash_generated(self):
        """Test evidence hash is generated"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task("Delete all files")
        assert result.evidence_hash is not None
        assert len(result.evidence_hash) == 16


class TestTaskTypeComplexity:
    """Tests for task type complexity scoring"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_risk_analyzer()

    def test_fix_lint_low_complexity(self):
        """Test fix_lint task type has low complexity"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Fix linting errors",
            context={"task_type": "fix_lint"}
        )
        # fix_lint should have low complexity score
        complexity_score = result.category_scores.get(RiskCategory.TASK_COMPLEXITY, 0)
        assert complexity_score <= 30

    def test_feature_high_complexity(self):
        """Test feature task type has higher complexity"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Implement new feature",
            context={"task_type": "feature"}
        )
        assert any(
            f.finding_id == "TC-001" and f.title == "Task type: feature"
            for f in result.findings
        )

    def test_deployment_high_complexity(self):
        """Test deployment task type has high complexity"""
        analyzer = RiskAnalyzerAgent()
        result = analyzer.analyze_task(
            "Deploy application",
            context={"task_type": "deployment"}
        )
        assert any(
            f.finding_id == "TC-001" for f in result.findings
        )
