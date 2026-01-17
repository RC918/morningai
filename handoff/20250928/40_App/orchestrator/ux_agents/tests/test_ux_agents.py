#!/usr/bin/env python3
"""
Unit Tests for UX/UI Agents - EPIC K Phase 2 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - UX/UI Agents
Issue: #4097 (EPIC K P2: 4 UI/UX Agents Implementation)

This module contains comprehensive unit tests for all 4 UI/UX Agents:
1. UI Consistency Agent
2. UX Heuristic Agent
3. Visual Regression Agent
4. Design Token Governance Agent
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest  # noqa: E402

from ux_agents.ui_consistency_agent import (  # noqa: E402
    UIConsistencyAgent,
    UIConsistencyFinding,
    UIConsistencyResult,
    ConsistencyCategory,
    ConsistencyLevel,
    ConsistencyAction,
    get_ui_consistency_agent,
    reset_ui_consistency_agent,
    analyze_ui_consistency,
)

from ux_agents.ux_heuristic_agent import (  # noqa: E402
    UXHeuristicAgent,
    HeuristicFinding,
    HeuristicResult,
    NielsenHeuristic,
    HeuristicSeverity,
    HeuristicAction,
    get_ux_heuristic_agent,
    reset_ux_heuristic_agent,
    analyze_ux_heuristics,
)

from ux_agents.visual_regression_agent import (  # noqa: E402
    VisualRegressionAgent,
    VisualRegressionFinding,
    VisualRegressionResult,
    RegressionType,
    RegressionSeverity,
    RegressionAction,
    get_visual_regression_agent,
    reset_visual_regression_agent,
    analyze_visual_regression,
)

from ux_agents.design_token_agent import (  # noqa: E402
    DesignTokenGovernanceAgent,
    TokenViolation,
    TokenGovernanceResult,
    ViolationType,
    ViolationSeverity,
    GovernanceAction,
    get_design_token_agent,
    reset_design_token_agent,
    analyze_design_tokens,
)


class TestUIConsistencyAgent:
    """Tests for UI Consistency Agent."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_ui_consistency_agent()

    def test_agent_initialization(self):
        """Test agent initializes with correct defaults."""
        agent = UIConsistencyAgent()
        assert agent.enabled is True
        assert agent.strict_mode is False
        assert agent.design_token_validation is True

    def test_agent_disabled(self):
        """Test agent returns pass when disabled."""
        agent = UIConsistencyAgent(enabled=False)
        result = agent.analyze_code("const color = '#ff0000';")
        assert result.overall_score == 100
        assert result.action == ConsistencyAction.PASS
        assert "disabled" in result.summary.lower()

    def test_empty_code_content(self):
        """Test agent handles empty content."""
        agent = UIConsistencyAgent()
        result = agent.analyze_code("")
        assert result.overall_score == 100
        assert result.action == ConsistencyAction.PASS

    def test_detect_hardcoded_hex_color(self):
        """Test detection of hardcoded hex colors."""
        agent = UIConsistencyAgent()
        code = """
        const Button = () => {
            return <button style={{ color: '#ff0000' }}>Click</button>;
        };
        """
        result = agent.analyze_code(code, "Button.tsx")
        assert len(result.findings) > 0
        color_findings = [
            f for f in result.findings
            if f.category == ConsistencyCategory.COLOR_USAGE
        ]
        assert len(color_findings) > 0
        assert "#ff0000" in color_findings[0].actual_value

    def test_detect_hardcoded_rgb_color(self):
        """Test detection of hardcoded RGB colors."""
        agent = UIConsistencyAgent()
        code = "background: rgb(255, 0, 0);"
        result = agent.analyze_code(code)
        color_findings = [
            f for f in result.findings
            if f.category == ConsistencyCategory.COLOR_USAGE
        ]
        assert len(color_findings) > 0

    def test_detect_hardcoded_spacing(self):
        """Test detection of hardcoded spacing values."""
        agent = UIConsistencyAgent()
        code = "padding: 24px; margin: 16px;"
        result = agent.analyze_code(code)
        spacing_findings = [
            f for f in result.findings
            if f.category == ConsistencyCategory.SPACING
        ]
        assert len(spacing_findings) > 0

    def test_detect_accessibility_issues(self):
        """Test detection of accessibility issues."""
        agent = UIConsistencyAgent()
        code = '<img src="logo.png">'
        result = agent.analyze_code(code)
        a11y_findings = [
            f for f in result.findings
            if f.category == ConsistencyCategory.ACCESSIBILITY
        ]
        assert len(a11y_findings) > 0
        assert "alt" in a11y_findings[0].title.lower() or "alt" in a11y_findings[0].description.lower()

    def test_result_serialization(self):
        """Test result can be serialized to dict."""
        agent = UIConsistencyAgent()
        result = agent.analyze_code("const x = '#fff';")
        result_dict = result.to_dict()
        assert "overall_score" in result_dict
        assert "findings" in result_dict
        assert "category_scores" in result_dict

    def test_finding_serialization(self):
        """Test finding can be serialized to dict."""
        finding = UIConsistencyFinding(
            category=ConsistencyCategory.COLOR_USAGE,
            level=ConsistencyLevel.MEDIUM,
            finding_id="TEST-001",
            title="Test Finding",
            description="Test description",
        )
        finding_dict = finding.to_dict()
        assert finding_dict["category"] == "color_usage"
        assert finding_dict["level"] == "medium"

    def test_singleton_pattern(self):
        """Test singleton pattern works correctly."""
        agent1 = get_ui_consistency_agent()
        agent2 = get_ui_consistency_agent()
        assert agent1 is agent2

    def test_convenience_function(self):
        """Test analyze_ui_consistency convenience function."""
        result = analyze_ui_consistency("const color = '#000';")
        assert isinstance(result, UIConsistencyResult)

    def test_strict_mode(self):
        """Test strict mode is properly configured."""
        agent = UIConsistencyAgent(strict_mode=True)
        assert agent.strict_mode is True
        code = """
        #ff0000 #00ff00 #0000ff
        rgb(255,0,0) rgba(0,0,0,0.5)
        padding: 100px; margin: 50px;
        """
        result = agent.analyze_code(code)
        assert len(result.findings) > 0
        assert result.overall_score < 100


class TestUXHeuristicAgent:
    """Tests for UX Heuristic Agent."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_ux_heuristic_agent()

    def test_agent_initialization(self):
        """Test agent initializes with correct defaults."""
        agent = UXHeuristicAgent()
        assert agent.enabled is True
        assert agent.strict_mode is False

    def test_agent_disabled(self):
        """Test agent returns pass when disabled."""
        agent = UXHeuristicAgent(enabled=False)
        result = agent.analyze_code("const x = 1;")
        assert result.overall_score == 100
        assert result.action == HeuristicAction.PASS

    def test_empty_code_content(self):
        """Test agent handles empty content."""
        agent = UXHeuristicAgent()
        result = agent.analyze_code("")
        assert result.overall_score == 100

    def test_detect_loading_state(self):
        """Test detection of loading state handling."""
        agent = UXHeuristicAgent()
        code = """
        const Component = () => {
            const [isLoading, setIsLoading] = useState(false);
            if (isLoading) return <Spinner />;
            return <div>Content</div>;
        };
        """
        result = agent.analyze_code(code)
        vis_score = result.heuristic_scores.get(
            NielsenHeuristic.VISIBILITY_OF_SYSTEM_STATUS, 0
        )
        assert vis_score >= 50

    def test_detect_error_handling(self):
        """Test detection of error handling patterns."""
        agent = UXHeuristicAgent()
        code = """
        try {
            await fetchData();
        } catch (error) {
            handleError(error);
        }
        """
        result = agent.analyze_code(code)
        err_score = result.heuristic_scores.get(
            NielsenHeuristic.ERROR_RECOVERY, 0
        )
        assert err_score >= 50

    def test_detect_user_control(self):
        """Test detection of user control patterns."""
        agent = UXHeuristicAgent()
        code = """
        const Modal = ({ onClose, onCancel }) => {
            return (
                <div>
                    <button onClick={onCancel}>Cancel</button>
                    <button onClick={onClose}>Close</button>
                </div>
            );
        };
        """
        result = agent.analyze_code(code)
        ctrl_score = result.heuristic_scores.get(
            NielsenHeuristic.USER_CONTROL_FREEDOM, 0
        )
        assert ctrl_score >= 50

    def test_detect_anti_patterns(self):
        """Test detection of UX anti-patterns."""
        agent = UXHeuristicAgent()
        code = "alert('Error occurred!');"
        result = agent.analyze_code(code)
        anti_findings = [
            f for f in result.findings
            if "alert" in f.title.lower() or "anti" in f.finding_id.lower()
        ]
        assert len(anti_findings) > 0

    def test_result_serialization(self):
        """Test result can be serialized to dict."""
        agent = UXHeuristicAgent()
        result = agent.analyze_code("const x = 1;")
        result_dict = result.to_dict()
        assert "overall_score" in result_dict
        assert "heuristic_scores" in result_dict

    def test_finding_serialization(self):
        """Test finding can be serialized to dict."""
        finding = HeuristicFinding(
            heuristic=NielsenHeuristic.ERROR_PREVENTION,
            severity=HeuristicSeverity.MAJOR,
            finding_id="TEST-001",
            title="Test Finding",
            description="Test description",
            user_impact="Test impact",
        )
        finding_dict = finding.to_dict()
        assert finding_dict["heuristic"] == "error_prevention"
        assert finding_dict["severity"] == "major"

    def test_singleton_pattern(self):
        """Test singleton pattern works correctly."""
        agent1 = get_ux_heuristic_agent()
        agent2 = get_ux_heuristic_agent()
        assert agent1 is agent2

    def test_convenience_function(self):
        """Test analyze_ux_heuristics convenience function."""
        result = analyze_ux_heuristics("const x = 1;")
        assert isinstance(result, HeuristicResult)

    def test_nielsen_heuristics_enum(self):
        """Test all 10 Nielsen heuristics are defined."""
        assert len(NielsenHeuristic) == 10
        assert NielsenHeuristic.VISIBILITY_OF_SYSTEM_STATUS
        assert NielsenHeuristic.ERROR_PREVENTION
        assert NielsenHeuristic.ERROR_RECOVERY


class TestVisualRegressionAgent:
    """Tests for Visual Regression Agent."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_visual_regression_agent()

    def test_agent_initialization(self):
        """Test agent initializes with correct defaults."""
        agent = VisualRegressionAgent()
        assert agent.enabled is True
        assert agent.strict_mode is False
        assert agent.track_all_changes is True

    def test_agent_disabled(self):
        """Test agent returns pass when disabled."""
        agent = VisualRegressionAgent(enabled=False)
        result = agent.analyze_changes("color: red;", "color: blue;")
        assert result.overall_score == 100
        assert result.action == RegressionAction.PASS

    def test_detect_color_change(self):
        """Test detection of color changes."""
        agent = VisualRegressionAgent()
        old_css = "color: red;"
        new_css = "color: blue;"
        result = agent.analyze_changes(old_css, new_css)
        color_findings = [
            f for f in result.findings
            if f.regression_type == RegressionType.COLOR_CHANGE
        ]
        assert len(color_findings) > 0

    def test_detect_layout_shift(self):
        """Test detection of layout shifts."""
        agent = VisualRegressionAgent()
        old_css = "position: relative;"
        new_css = "position: absolute;"
        result = agent.analyze_changes(old_css, new_css)
        layout_findings = [
            f for f in result.findings
            if f.regression_type == RegressionType.LAYOUT_SHIFT
        ]
        assert len(layout_findings) > 0

    def test_detect_visibility_change(self):
        """Test detection of visibility changes."""
        agent = VisualRegressionAgent()
        code = "display: none;"
        result = agent.analyze_code(code)
        vis_findings = [
            f for f in result.findings
            if f.regression_type == RegressionType.VISIBILITY_CHANGE
        ]
        assert len(vis_findings) > 0

    def test_detect_size_change(self):
        """Test detection of size changes."""
        agent = VisualRegressionAgent()
        old_css = "width: 100px;"
        new_css = "width: 200px;"
        result = agent.analyze_changes(old_css, new_css)
        size_findings = [
            f for f in result.findings
            if f.regression_type == RegressionType.SIZE_CHANGE
        ]
        assert len(size_findings) > 0

    def test_result_serialization(self):
        """Test result can be serialized to dict."""
        agent = VisualRegressionAgent()
        result = agent.analyze_code("display: none;")
        result_dict = result.to_dict()
        assert "overall_score" in result_dict
        assert "type_counts" in result_dict

    def test_finding_serialization(self):
        """Test finding can be serialized to dict."""
        finding = VisualRegressionFinding(
            regression_type=RegressionType.COLOR_CHANGE,
            severity=RegressionSeverity.MEDIUM,
            finding_id="TEST-001",
            title="Test Finding",
            description="Test description",
        )
        finding_dict = finding.to_dict()
        assert finding_dict["regression_type"] == "color_change"
        assert finding_dict["severity"] == "medium"

    def test_singleton_pattern(self):
        """Test singleton pattern works correctly."""
        agent1 = get_visual_regression_agent()
        agent2 = get_visual_regression_agent()
        assert agent1 is agent2

    def test_convenience_function(self):
        """Test analyze_visual_regression convenience function."""
        result = analyze_visual_regression("color: red;", "color: blue;")
        assert isinstance(result, VisualRegressionResult)

    def test_single_file_analysis(self):
        """Test single file analysis (no diff)."""
        agent = VisualRegressionAgent()
        result = agent.analyze_code("opacity: 0;")
        assert isinstance(result, VisualRegressionResult)
        assert result.evidence_hash is not None


class TestDesignTokenGovernanceAgent:
    """Tests for Design Token Governance Agent."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_design_token_agent()

    def test_agent_initialization(self):
        """Test agent initializes with correct defaults."""
        agent = DesignTokenGovernanceAgent()
        assert agent.enabled is True
        assert agent.strict_mode is False
        assert agent.auto_suggest is True

    def test_agent_disabled(self):
        """Test agent returns pass when disabled."""
        agent = DesignTokenGovernanceAgent(enabled=False)
        result = agent.analyze_code("color: #ff0000;")
        assert result.overall_score == 100
        assert result.action == GovernanceAction.PASS

    def test_empty_code_content(self):
        """Test agent handles empty content."""
        agent = DesignTokenGovernanceAgent()
        result = agent.analyze_code("")
        assert result.overall_score == 100

    def test_detect_hardcoded_hex_color(self):
        """Test detection of hardcoded hex colors."""
        agent = DesignTokenGovernanceAgent()
        code = "color: #ff0000;"
        result = agent.analyze_code(code)
        color_violations = [
            v for v in result.violations
            if v.violation_type == ViolationType.HARDCODED_COLOR
        ]
        assert len(color_violations) > 0

    def test_detect_hardcoded_rgb_color(self):
        """Test detection of hardcoded RGB colors."""
        agent = DesignTokenGovernanceAgent()
        code = "background: rgb(255, 0, 0);"
        result = agent.analyze_code(code)
        color_violations = [
            v for v in result.violations
            if v.violation_type == ViolationType.HARDCODED_COLOR
        ]
        assert len(color_violations) > 0

    def test_detect_hardcoded_spacing(self):
        """Test detection of hardcoded spacing values."""
        agent = DesignTokenGovernanceAgent()
        code = "padding: 24px; margin: 48px;"
        result = agent.analyze_code(code)
        spacing_violations = [
            v for v in result.violations
            if v.violation_type == ViolationType.HARDCODED_SPACING
        ]
        assert len(spacing_violations) > 0

    def test_detect_hardcoded_typography(self):
        """Test detection of hardcoded typography values."""
        agent = DesignTokenGovernanceAgent()
        code = "font-size: 14px; font-weight: 700;"
        result = agent.analyze_code(code)
        typography_violations = [
            v for v in result.violations
            if v.violation_type == ViolationType.HARDCODED_TYPOGRAPHY
        ]
        assert len(typography_violations) > 0

    def test_detect_deprecated_tokens(self):
        """Test detection of deprecated token usage."""
        agent = DesignTokenGovernanceAgent()
        code = "const color = colors.gray;"
        result = agent.analyze_code(code)
        deprecated_violations = [
            v for v in result.violations
            if v.violation_type == ViolationType.DEPRECATED_TOKEN
        ]
        assert len(deprecated_violations) > 0

    def test_suggest_replacement_token(self):
        """Test suggestion of replacement tokens."""
        agent = DesignTokenGovernanceAgent()
        code = "color: #4D7CFE;"
        result = agent.analyze_code(code)
        violations_with_suggestions = [
            v for v in result.violations
            if v.suggested_token is not None
        ]
        assert len(violations_with_suggestions) > 0

    def test_count_valid_token_usage(self):
        """Test counting of valid token usage."""
        agent = DesignTokenGovernanceAgent()
        code = """
        const style = {
            color: colors.primary['500'],
            padding: spacing.md,
            borderRadius: radius.lg,
        };
        """
        result = agent.analyze_code(code)
        assert result.token_usage_count > 0

    def test_compliance_rate_calculation(self):
        """Test compliance rate is calculated correctly."""
        agent = DesignTokenGovernanceAgent()
        code = """
        color: #ff0000;
        background: colors.primary['500'];
        """
        result = agent.analyze_code(code)
        assert 0 <= result.compliance_rate <= 100

    def test_result_serialization(self):
        """Test result can be serialized to dict."""
        agent = DesignTokenGovernanceAgent()
        result = agent.analyze_code("color: #fff;")
        result_dict = result.to_dict()
        assert "overall_score" in result_dict
        assert "violations" in result_dict
        assert "compliance_rate" in result_dict

    def test_violation_serialization(self):
        """Test violation can be serialized to dict."""
        violation = TokenViolation(
            violation_type=ViolationType.HARDCODED_COLOR,
            severity=ViolationSeverity.HIGH,
            finding_id="TEST-001",
            title="Test Violation",
            description="Test description",
        )
        violation_dict = violation.to_dict()
        assert violation_dict["violation_type"] == "hardcoded_color"
        assert violation_dict["severity"] == "high"

    def test_singleton_pattern(self):
        """Test singleton pattern works correctly."""
        agent1 = get_design_token_agent()
        agent2 = get_design_token_agent()
        assert agent1 is agent2

    def test_convenience_function(self):
        """Test analyze_design_tokens convenience function."""
        result = analyze_design_tokens("color: #000;")
        assert isinstance(result, TokenGovernanceResult)

    def test_strict_mode(self):
        """Test strict mode affects action determination."""
        agent = DesignTokenGovernanceAgent(strict_mode=True)
        code = """
        #ff0000 #00ff00 #0000ff
        rgb(255,0,0) rgba(0,0,0,0.5)
        font-size: 14px; font-weight: 700;
        padding: 100px; margin: 50px;
        """
        result = agent.analyze_code(code)
        assert result.action in [GovernanceAction.BLOCK, GovernanceAction.REQUIRE_REVIEW]


class TestIntegration:
    """Integration tests for all UX/UI Agents."""

    def setup_method(self):
        """Reset all singletons before each test."""
        reset_ui_consistency_agent()
        reset_ux_heuristic_agent()
        reset_visual_regression_agent()
        reset_design_token_agent()

    def test_all_agents_analyze_same_code(self):
        """Test all agents can analyze the same code."""
        code = """
        const Button = ({ onClick, isLoading }) => {
            if (isLoading) return <Spinner />;
            return (
                <button
                    onClick={onClick}
                    style={{
                        color: '#4D7CFE',
                        padding: '16px',
                        borderRadius: '8px',
                    }}
                >
                    Click me
                </button>
            );
        };
        """

        ui_result = analyze_ui_consistency(code, "Button.tsx")
        ux_result = analyze_ux_heuristics(code, "Button.tsx")
        vr_result = get_visual_regression_agent().analyze_code(code, "Button.tsx")
        dt_result = analyze_design_tokens(code, "Button.tsx")

        assert isinstance(ui_result, UIConsistencyResult)
        assert isinstance(ux_result, HeuristicResult)
        assert isinstance(vr_result, VisualRegressionResult)
        assert isinstance(dt_result, TokenGovernanceResult)

        assert ui_result.evidence_hash is not None
        assert ux_result.evidence_hash is not None
        assert vr_result.evidence_hash is not None
        assert dt_result.evidence_hash is not None

    def test_all_agents_have_consistent_interface(self):
        """Test all agents have consistent interface."""
        agents = [
            UIConsistencyAgent(),
            UXHeuristicAgent(),
            VisualRegressionAgent(),
            DesignTokenGovernanceAgent(),
        ]

        for agent in agents:
            assert hasattr(agent, 'enabled')
            assert hasattr(agent, 'strict_mode')
            assert hasattr(agent, 'analyze_code')
            assert hasattr(agent, '_load_settings')
            assert hasattr(agent, '_compile_patterns')

    def test_all_results_have_consistent_interface(self):
        """Test all results have consistent interface."""
        code = "const x = '#fff';"

        results = [
            analyze_ui_consistency(code),
            analyze_ux_heuristics(code),
            get_visual_regression_agent().analyze_code(code),
            analyze_design_tokens(code),
        ]

        for result in results:
            assert hasattr(result, 'overall_score')
            assert hasattr(result, 'summary')
            assert hasattr(result, 'analyzer_id')
            assert hasattr(result, 'analysis_duration_ms')
            assert hasattr(result, 'evidence_hash')
            assert hasattr(result, 'to_dict')

            result_dict = result.to_dict()
            assert 'overall_score' in result_dict
            assert 'summary' in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
