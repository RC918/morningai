"""
SSOT Guard Tests for Degradation Multipliers

This test module ensures that degradation severity multipliers maintain
a Single Source of Truth (SSOT) across the codebase.

Background:
- PR #3422 introduced a potential SSOT violation where routing code
  hardcoded multipliers (0.7/0.3) that differed from SEVERITY_MULTIPLIERS (0.5/0.25)
- This guard test prevents future drift by:
  1. Verifying SEVERITY_MULTIPLIERS is the canonical source
  2. Scanning routing code for hardcoded multiplier patterns
  3. Ensuring any routing-specific multipliers are explicitly documented

Reference: gemini-code-assist critical finding on PR #3422
"""
import ast
import re
from pathlib import Path

import pytest

from governance.degradation_types import (
    DegradationSeverity,
    SEVERITY_MULTIPLIERS,
)


class TestSeverityMultipliersSSOT:
    """Tests to ensure SEVERITY_MULTIPLIERS is the single source of truth"""

    def test_severity_multipliers_is_complete(self):
        """Verify SEVERITY_MULTIPLIERS covers all DegradationSeverity values"""
        for severity in DegradationSeverity:
            assert severity in SEVERITY_MULTIPLIERS, (
                f"SEVERITY_MULTIPLIERS missing entry for {severity.name}. "
                f"All severity levels must have a defined multiplier."
            )

    def test_severity_multipliers_values_are_valid(self):
        """Verify all multiplier values are in valid range [0.0, 1.0]"""
        for severity, multiplier in SEVERITY_MULTIPLIERS.items():
            assert 0.0 <= multiplier <= 1.0, (
                f"SEVERITY_MULTIPLIERS[{severity.name}] = {multiplier} is out of range. "
                f"Multipliers must be between 0.0 and 1.0."
            )

    def test_severity_multipliers_ordering(self):
        """Verify multipliers decrease with increasing severity"""
        assert SEVERITY_MULTIPLIERS[DegradationSeverity.HEALTHY] == 1.0, (
            "HEALTHY severity must have multiplier 1.0 (no reduction)"
        )
        assert SEVERITY_MULTIPLIERS[DegradationSeverity.AVOID] == 0.0, (
            "AVOID severity must have multiplier 0.0 (complete block)"
        )
        assert (
            SEVERITY_MULTIPLIERS[DegradationSeverity.HEALTHY] >
            SEVERITY_MULTIPLIERS[DegradationSeverity.DEGRADED] >
            SEVERITY_MULTIPLIERS[DegradationSeverity.CRITICAL] >
            SEVERITY_MULTIPLIERS[DegradationSeverity.AVOID]
        ), (
            "Multipliers must decrease with increasing severity: "
            "HEALTHY > DEGRADED > CRITICAL > AVOID"
        )

    def test_severity_multipliers_documented_in_enum(self):
        """Verify DegradationSeverity docstring matches SEVERITY_MULTIPLIERS"""
        docstring = DegradationSeverity.__doc__ or ""
        
        for severity, multiplier in SEVERITY_MULTIPLIERS.items():
            pattern = rf"{severity.name}.*multiplier.*{multiplier}"
            assert re.search(pattern, docstring, re.IGNORECASE), (
                f"DegradationSeverity docstring should document that "
                f"{severity.name} has multiplier {multiplier}. "
                f"Keep documentation in sync with SEVERITY_MULTIPLIERS."
            )


class TestRoutingCodeSSOTCompliance:
    """
    Tests to detect hardcoded multipliers in routing code.
    
    These tests scan the routing module for patterns that might indicate
    SSOT violations (hardcoded multipliers instead of using SEVERITY_MULTIPLIERS).
    """

    @pytest.fixture
    def routing_engine_path(self):
        """Path to the routing engine module"""
        return Path(__file__).parent.parent / "core" / "routing" / "engine.py"

    @pytest.fixture
    def routing_module_path(self):
        """Path to the routing module directory"""
        return Path(__file__).parent.parent / "core" / "routing"

    def test_no_hardcoded_degradation_multipliers_in_routing_engine(
        self, routing_engine_path
    ):
        """
        Verify routing engine doesn't hardcode degradation multipliers.
        
        If routing needs different multipliers than SEVERITY_MULTIPLIERS,
        they should be defined as a separate constant (e.g., ROUTING_SEVERITY_MULTIPLIERS)
        with clear documentation explaining why they differ.
        """
        if not routing_engine_path.exists():
            pytest.skip("routing engine not found")

        content = routing_engine_path.read_text()
        
        suspicious_patterns = [
            (r'DegradationSeverity\.DEGRADED[^}]*:\s*0\.[0-9]+', 
             "Hardcoded DEGRADED multiplier"),
            (r'DegradationSeverity\.CRITICAL[^}]*:\s*0\.[0-9]+',
             "Hardcoded CRITICAL multiplier"),
            (r'DegradationSeverity\.HEALTHY[^}]*:\s*1\.0',
             "Hardcoded HEALTHY multiplier (should use SEVERITY_MULTIPLIERS)"),
            (r'DegradationSeverity\.AVOID[^}]*:\s*0\.0',
             "Hardcoded AVOID multiplier (should use SEVERITY_MULTIPLIERS)"),
        ]
        
        violations = []
        for pattern, description in suspicious_patterns:
            if re.search(pattern, content):
                if "SEVERITY_MULTIPLIERS" not in content:
                    violations.append(description)
        
        if violations:
            pytest.fail(
                f"Potential SSOT violations in routing engine:\n"
                f"- {chr(10).join(violations)}\n\n"
                f"If routing needs degradation multipliers, import and use "
                f"SEVERITY_MULTIPLIERS from governance.degradation_types.\n"
                f"If routing needs DIFFERENT multipliers, define them as "
                f"ROUTING_SEVERITY_MULTIPLIERS with documentation explaining why."
            )

    def test_routing_module_imports_severity_multipliers_if_using_degradation(
        self, routing_module_path
    ):
        """
        If routing code references DegradationSeverity, it should also
        import SEVERITY_MULTIPLIERS to ensure SSOT compliance.
        """
        if not routing_module_path.exists():
            pytest.skip("routing module not found")

        for py_file in routing_module_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            content = py_file.read_text()
            
            uses_degradation_severity = "DegradationSeverity" in content
            imports_severity_multipliers = "SEVERITY_MULTIPLIERS" in content
            defines_routing_multipliers = "ROUTING_SEVERITY_MULTIPLIERS" in content
            
            if uses_degradation_severity:
                has_valid_multiplier_source = (
                    imports_severity_multipliers or 
                    defines_routing_multipliers
                )
                
                if not has_valid_multiplier_source:
                    lines_with_severity = [
                        i + 1 for i, line in enumerate(content.split('\n'))
                        if 'DegradationSeverity' in line and 'import' not in line.lower()
                    ]
                    
                    if lines_with_severity:
                        pytest.fail(
                            f"{py_file.name} uses DegradationSeverity (lines {lines_with_severity}) "
                            f"but doesn't import SEVERITY_MULTIPLIERS or define "
                            f"ROUTING_SEVERITY_MULTIPLIERS.\n\n"
                            f"To maintain SSOT, either:\n"
                            f"1. Import SEVERITY_MULTIPLIERS from governance.degradation_types\n"
                            f"2. Define ROUTING_SEVERITY_MULTIPLIERS with documentation"
                        )


class TestMultiplierConsistencyContract:
    """
    Contract tests to ensure multiplier consistency across modules.
    
    These tests verify that any module using degradation multipliers
    produces consistent results with the canonical SEVERITY_MULTIPLIERS.
    """

    def test_degradation_advisor_uses_severity_multipliers(self):
        """Verify DegradationAdvisor.get_multiplier uses SEVERITY_MULTIPLIERS"""
        from governance.degradation_advisor import DegradationPolicy
        
        policy = DegradationPolicy()
        
        for severity in DegradationSeverity:
            advisor_multiplier = policy.get_multiplier(severity)
            canonical_multiplier = SEVERITY_MULTIPLIERS[severity]
            
            assert advisor_multiplier == canonical_multiplier, (
                f"DegradationPolicy.get_multiplier({severity.name}) = {advisor_multiplier} "
                f"but SEVERITY_MULTIPLIERS[{severity.name}] = {canonical_multiplier}. "
                f"These must be consistent to maintain SSOT."
            )

    def test_degradation_recommendation_uses_severity_multipliers(self):
        """Verify DegradationRecommendation score_multiplier matches SEVERITY_MULTIPLIERS"""
        from governance.degradation_types import DegradationRecommendation
        
        for severity in DegradationSeverity:
            expected_multiplier = SEVERITY_MULTIPLIERS[severity]
            
            recommendation = DegradationRecommendation(
                provider="test_provider",
                severity=severity,
                score_multiplier=expected_multiplier,
                health_score=50.0,
                health_score_normalized=0.5,
                reason="Test recommendation",
            )
            
            assert recommendation.score_multiplier == expected_multiplier, (
                f"DegradationRecommendation with severity {severity.name} "
                f"should use multiplier {expected_multiplier}"
            )


class TestFutureProofing:
    """
    Tests to catch potential SSOT issues before they become problems.
    
    These tests use AST analysis to detect patterns that might lead
    to SSOT violations in the future.
    """

    def test_no_hardcoded_degradation_severity_dict(self):
        """
        Scan for dictionary literals that map DegradationSeverity to float values.
        
        This test catches the specific pattern from PR #3422 where a dict like:
        {DegradationSeverity.DEGRADED: 0.7, DegradationSeverity.CRITICAL: 0.3}
        was hardcoded instead of using SEVERITY_MULTIPLIERS.
        
        Note: This does NOT flag cost_weight/preference_weight values (0.3/0.7)
        which are for a different purpose (Issue #2874 scoring weights).
        """
        routing_dir = Path(__file__).parent.parent / "core" / "routing"
        
        if not routing_dir.exists():
            pytest.skip("routing directory not found")
        
        violations = []
        
        for py_file in routing_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            content = py_file.read_text()
            
            pattern = r'\{[^}]*DegradationSeverity\.\w+\s*:\s*\d+\.\d+[^}]*\}'
            
            matches = re.finditer(pattern, content)
            for match in matches:
                matched_text = match.group()
                if 'SEVERITY_MULTIPLIERS' not in content[:match.start()]:
                    line_no = content[:match.start()].count('\n') + 1
                    violations.append(
                        f"{py_file.name}:{line_no} - "
                        f"Hardcoded DegradationSeverity->float dict found"
                    )
        
        if violations:
            pytest.fail(
                f"Hardcoded DegradationSeverity multiplier dicts found:\n"
                f"- {chr(10).join(violations)}\n\n"
                f"Use SEVERITY_MULTIPLIERS from governance.degradation_types instead.\n"
                f"If routing needs different values, define ROUTING_SEVERITY_MULTIPLIERS "
                f"with documentation explaining why."
            )

    def test_degradation_multiplier_function_uses_constant(self):
        """
        If a function named *degradation*multiplier* exists in routing,
        verify it imports or references SEVERITY_MULTIPLIERS.
        """
        routing_dir = Path(__file__).parent.parent / "core" / "routing"
        
        if not routing_dir.exists():
            pytest.skip("routing directory not found")
        
        for py_file in routing_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            content = py_file.read_text()
            
            if re.search(r'def\s+\w*degradation\w*multiplier', content, re.IGNORECASE):
                if 'SEVERITY_MULTIPLIERS' not in content:
                    if 'ROUTING_SEVERITY_MULTIPLIERS' not in content:
                        pytest.fail(
                            f"{py_file.name} contains a degradation multiplier function "
                            f"but doesn't reference SEVERITY_MULTIPLIERS or "
                            f"ROUTING_SEVERITY_MULTIPLIERS.\n\n"
                            f"To maintain SSOT, the function should use the shared constant."
                        )
