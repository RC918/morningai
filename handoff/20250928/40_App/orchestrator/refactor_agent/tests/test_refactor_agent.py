"""
Tests for Refactor Agent - Phase 4 (#1818, #1888)
"""
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from refactor_agent.agent import (
    RefactorAgent,
    RefactorTask,
    RefactorResult,
    RefactorRisk,
    TSError,
    TS_FIX_STRATEGIES,
    TS_FIX_PROMPT_TEMPLATES,
    STRATEGY_TO_TEMPLATE,
    MIN_LLM_FIX_LENGTH,
    get_refactor_agent,
    run_nightly_refactor,
)


class TestTSError:
    """Tests for TSError dataclass"""

    def test_ts_error_creation(self):
        """Test TSError creation with all fields"""
        error = TSError(
            file_path="src/components/Button.tsx",
            line=42,
            column=10,
            error_code="TS2322",
            message="Type 'string' is not assignable to type 'number'",
            severity="error"
        )

        assert error.file_path == "src/components/Button.tsx"
        assert error.line == 42
        assert error.column == 10
        assert error.error_code == "TS2322"
        assert error.severity == "error"

    def test_ts_error_to_dict(self):
        """Test TSError serialization"""
        error = TSError(
            file_path="src/App.tsx",
            line=10,
            column=5,
            error_code="TS7006",
            message="Parameter 'x' implicitly has an 'any' type"
        )

        result = error.to_dict()

        assert result["file_path"] == "src/App.tsx"
        assert result["line"] == 10
        assert result["error_code"] == "TS7006"


class TestRefactorTask:
    """Tests for RefactorTask dataclass"""

    def test_refactor_task_creation(self):
        """Test RefactorTask creation"""
        error = TSError(
            file_path="src/utils.ts",
            line=20,
            column=1,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="task-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        assert task.task_id == "task-001"
        assert task.fix_strategy == "null_check"
        assert task.estimated_risk == RefactorRisk.LOW
        assert task.status == "pending"

    def test_refactor_task_to_dict(self):
        """Test RefactorTask serialization"""
        error = TSError(
            file_path="src/index.ts",
            line=1,
            column=1,
            error_code="TS2532",
            message="Object is possibly 'undefined'"
        )

        task = RefactorTask(
            task_id="task-002",
            error=error,
            fix_strategy="undefined_check",
            estimated_risk=RefactorRisk.MEDIUM,
            status="completed",
            fix_applied="// Added undefined check"
        )

        result = task.to_dict()

        assert result["task_id"] == "task-002"
        assert result["fix_strategy"] == "undefined_check"
        assert result["estimated_risk"] == "medium"
        assert result["status"] == "completed"


class TestRefactorResult:
    """Tests for RefactorResult dataclass"""

    def test_refactor_result_creation(self):
        """Test RefactorResult creation"""
        result = RefactorResult(
            run_id="run-001",
            started_at=1000.0,
            completed_at=1010.0,
            total_errors_found=100,
            errors_fixed=10,
            errors_failed=0
        )

        assert result.run_id == "run-001"
        assert result.total_errors_found == 100
        assert result.errors_fixed == 10

    def test_refactor_result_to_dict(self):
        """Test RefactorResult serialization"""
        result = RefactorResult(
            run_id="run-002",
            started_at=2000.0,
            total_errors_found=50,
            errors_fixed=5,
            summary="Fixed 5 errors"
        )

        data = result.to_dict()

        assert data["run_id"] == "run-002"
        assert data["total_errors_found"] == 50
        assert data["summary"] == "Fixed 5 errors"


class TestTSFixStrategies:
    """Tests for TS fix strategy mappings"""

    def test_common_error_codes_have_strategies(self):
        """Test that common error codes have fix strategies"""
        common_codes = ["TS2322", "TS2531", "TS7006", "TS2339"]

        for code in common_codes:
            assert code in TS_FIX_STRATEGIES

    def test_null_check_strategy(self):
        """Test null check strategy mapping"""
        assert TS_FIX_STRATEGIES["TS2531"] == "null_check"

    def test_implicit_any_strategy(self):
        """Test implicit any strategy mapping"""
        assert TS_FIX_STRATEGIES["TS7006"] == "implicit_any"


class TestRefactorAgent:
    """Tests for RefactorAgent class"""

    def test_agent_initialization(self):
        """Test RefactorAgent initialization"""
        with patch.object(RefactorAgent, '_find_repo_path') as mock_find:
            mock_find.return_value = Path("/tmp/test-repo")

            agent = RefactorAgent(repo_path="/tmp/test-repo")

            assert agent.repo_path == Path("/tmp/test-repo")
            assert agent.enabled is True
            assert agent.errors_per_run == RefactorAgent.DEFAULT_ERRORS_PER_RUN

    def test_agent_with_custom_settings(self):
        """Test RefactorAgent with custom settings"""
        with patch('refactor_agent.agent.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="/tmp/repo",
                returncode=0
            )

            agent = RefactorAgent(repo_path="/tmp/custom-repo")

            assert agent.repo_path == Path("/tmp/custom-repo")

    def test_parse_tsc_error_valid(self):
        """Test parsing valid tsc error line"""
        agent = RefactorAgent(repo_path="/tmp/test")

        line = "src/App.tsx(10,5): error TS2322: Type 'string' is not assignable"
        error = agent._parse_tsc_error(line, "frontend-dashboard")

        assert error is not None
        assert error.line == 10
        assert error.column == 5
        assert error.error_code == "TS2322"

    def test_parse_tsc_error_invalid(self):
        """Test parsing invalid tsc error line"""
        agent = RefactorAgent(repo_path="/tmp/test")

        line = "This is not a valid error line"
        error = agent._parse_tsc_error(line, "frontend-dashboard")

        assert error is None

    def test_analyze_error_low_risk(self):
        """Test error analysis for low risk errors"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/utils.ts",
            line=10,
            column=1,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = agent.analyze_error(error)

        assert task.fix_strategy == "null_check"
        assert task.estimated_risk == RefactorRisk.LOW

    def test_analyze_error_medium_risk(self):
        """Test error analysis for medium risk errors"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/types.ts",
            line=20,
            column=1,
            error_code="TS2322",
            message="Type mismatch"
        )

        task = agent.analyze_error(error)

        assert task.fix_strategy == "type_mismatch"
        assert task.estimated_risk == RefactorRisk.MEDIUM

    def test_analyze_error_high_risk(self):
        """Test error analysis for unknown error codes"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/complex.ts",
            line=30,
            column=1,
            error_code="TS9999",
            message="Unknown error"
        )

        task = agent.analyze_error(error)

        assert task.fix_strategy == "manual_review"
        assert task.estimated_risk == RefactorRisk.HIGH

    def test_generate_fix_null_check(self):
        """Test fix generation for null check"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=15,
            column=1,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        fix = agent.generate_fix(task)

        assert fix is not None
        assert "null check" in fix.lower()

    def test_generate_fix_manual_review(self):
        """Test fix generation returns None for manual review"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/complex.ts",
            line=100,
            column=1,
            error_code="TS9999",
            message="Complex error"
        )

        task = RefactorTask(
            task_id="test-002",
            error=error,
            fix_strategy="manual_review",
            estimated_risk=RefactorRisk.HIGH
        )

        fix = agent.generate_fix(task)

        assert fix is None

    def test_generate_summary(self):
        """Test summary generation"""
        agent = RefactorAgent(repo_path="/tmp/test")

        summary = agent._generate_summary(
            total_errors=100,
            errors_fixed=10,
            errors_failed=2
        )

        assert "100" in summary
        assert "10" in summary
        assert "90" in summary  # remaining = total - fixed

    def test_run_refactor_disabled(self):
        """Test run_refactor when agent is disabled"""
        agent = RefactorAgent(repo_path="/tmp/test")
        agent.enabled = False

        result = agent.run_refactor()

        assert "disabled" in result.summary.lower()

    def test_run_refactor_dry_run(self):
        """Test run_refactor in dry run mode"""
        agent = RefactorAgent(repo_path="/tmp/test")

        with patch.object(agent, 'collect_ts_errors') as mock_collect:
            mock_collect.return_value = [
                TSError(
                    file_path="src/test.ts",
                    line=1,
                    column=1,
                    error_code="TS2531",
                    message="Test error"
                )
            ]

            result = agent.run_refactor(max_errors=1, dry_run=True)

            assert result.total_errors_found == 1
            assert result.errors_fixed == 0  # dry run doesn't fix
            assert result.metadata["dry_run"] is True

    def test_get_progress_report(self):
        """Test get_progress_report returns correct metrics"""
        agent = RefactorAgent(repo_path="/tmp/test")

        with patch.object(agent, 'collect_ts_errors') as mock_collect:
            mock_collect.return_value = [
                TSError(
                    file_path="frontend-dashboard/src/App.tsx",
                    line=10,
                    column=1,
                    error_code="TS2531",
                    message="Object is possibly 'null'"
                ),
                TSError(
                    file_path="frontend-dashboard/src/utils.ts",
                    line=20,
                    column=1,
                    error_code="TS2531",
                    message="Object is possibly 'null'"
                ),
                TSError(
                    file_path="owner-console/src/index.tsx",
                    line=5,
                    column=1,
                    error_code="TS7006",
                    message="Parameter 'x' implicitly has an 'any' type"
                ),
            ]

            report = agent.get_progress_report()

            assert report["total_errors"] == 3
            assert report["target_errors"] == 0
            assert report["progress_percent"] == 0.0
            assert report["errors_by_code"]["TS2531"] == 2
            assert report["errors_by_code"]["TS7006"] == 1
            assert report["errors_by_project"]["frontend-dashboard"] == 2
            assert report["errors_by_project"]["owner-console"] == 1
            assert len(report["top_error_codes"]) <= 5

    def test_get_progress_report_no_errors(self):
        """Test get_progress_report with no errors returns 100% progress"""
        agent = RefactorAgent(repo_path="/tmp/test")

        with patch.object(agent, 'collect_ts_errors') as mock_collect:
            mock_collect.return_value = []

            report = agent.get_progress_report()

            assert report["total_errors"] == 0
            assert report["progress_percent"] == 100.0
            assert report["errors_by_code"] == {}
            assert report["errors_by_project"] == {}


class TestGetRefactorAgent:
    """Tests for get_refactor_agent singleton"""

    def test_get_refactor_agent_singleton(self):
        """Test that get_refactor_agent returns singleton"""
        import refactor_agent.agent as module

        module._refactor_agent = None

        agent1 = get_refactor_agent()
        agent2 = get_refactor_agent()

        assert agent1 is agent2

        module._refactor_agent = None


class TestRunNightlyRefactor:
    """Tests for run_nightly_refactor convenience function"""

    def test_run_nightly_refactor(self):
        """Test run_nightly_refactor function"""
        with patch('refactor_agent.agent.get_refactor_agent') as mock_get:
            mock_agent = MagicMock()
            mock_agent.run_refactor.return_value = RefactorResult(
                run_id="test-run",
                started_at=1000.0,
                total_errors_found=50,
                errors_fixed=5
            )
            mock_get.return_value = mock_agent

            result = run_nightly_refactor(max_errors=5, dry_run=True)

            mock_agent.run_refactor.assert_called_once_with(
                max_errors=5, dry_run=True
            )
            assert result.run_id == "test-run"


class TestRefactorRisk:
    """Tests for RefactorRisk enum"""

    def test_risk_levels(self):
        """Test all risk levels exist"""
        assert RefactorRisk.HIGH.value == "high"
        assert RefactorRisk.MEDIUM.value == "medium"
        assert RefactorRisk.LOW.value == "low"
        assert RefactorRisk.INFO.value == "info"


class TestPromptTemplates:
    """Tests for LLM prompt templates (#1888)"""

    def test_min_llm_fix_length_constant(self):
        """Test MIN_LLM_FIX_LENGTH constant is defined"""
        assert MIN_LLM_FIX_LENGTH == 5

    def test_all_strategies_have_templates(self):
        """Test that all fix strategies have corresponding templates"""
        for strategy in STRATEGY_TO_TEMPLATE:
            template_key = STRATEGY_TO_TEMPLATE[strategy]
            assert template_key in TS_FIX_PROMPT_TEMPLATES

    def test_null_check_template_has_placeholders(self):
        """Test null_check template has required placeholders"""
        template = TS_FIX_PROMPT_TEMPLATES["null_check"]
        assert "{error_message}" in template
        assert "{file_path}" in template
        assert "{line}" in template
        assert "{column}" in template
        assert "{code_context}" in template

    def test_generic_template_has_error_code(self):
        """Test generic template includes error_code placeholder"""
        template = TS_FIX_PROMPT_TEMPLATES["generic"]
        assert "{error_code}" in template

    def test_template_count(self):
        """Test we have at least 10 prompt templates"""
        assert len(TS_FIX_PROMPT_TEMPLATES) >= 10


class TestLLMIntegration:
    """Tests for LLM integration in RefactorAgent (#1888)"""

    def test_get_llm_client_not_available(self):
        """Test _get_llm_client returns None when LLM import fails"""
        agent = RefactorAgent(repo_path="/tmp/test")

        if hasattr(agent, '_llm_client'):
            delattr(agent, '_llm_client')

        with patch.dict('sys.modules', {'llm': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'llm'")):
                client = agent._get_llm_client()
                assert client is None
                assert agent._llm_client is None

    def test_get_llm_client_available(self):
        """Test _get_llm_client returns client when LLMClient is available"""
        agent = RefactorAgent(repo_path="/tmp/test")

        if hasattr(agent, '_llm_client'):
            delattr(agent, '_llm_client')

        mock_llm_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_llm_client_class.return_value = mock_client_instance

        mock_llm_module = MagicMock()
        mock_llm_module.LLMClient = mock_llm_client_class

        with patch.dict('sys.modules', {'llm': mock_llm_module}):
            client = agent._get_llm_client()
            assert client is mock_client_instance
            assert agent._llm_client is mock_client_instance

    def test_get_llm_client_caches_result(self):
        """Test _get_llm_client caches the client instance"""
        agent = RefactorAgent(repo_path="/tmp/test")

        mock_client = MagicMock()
        agent._llm_client = mock_client

        client = agent._get_llm_client()
        assert client is mock_client

    def test_get_code_context_file_not_found(self):
        """Test _get_code_context handles missing files"""
        agent = RefactorAgent(repo_path="/tmp/nonexistent")

        context = agent._get_code_context("missing/file.ts", 10)

        assert "File not found" in context

    def test_get_code_context_success(self):
        """Test _get_code_context returns correct context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text(
                "line 1\nline 2\nline 3\nline 4\nline 5\n"
                "line 6\nline 7\nline 8\nline 9\nline 10\n"
            )

            agent = RefactorAgent(repo_path=tmpdir)
            context = agent._get_code_context("test.ts", 5, context_lines=2)

            assert "line 5" in context
            assert ">>>" in context

    def test_build_fix_prompt_uses_correct_template(self):
        """Test _build_fix_prompt selects correct template"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        with patch.object(agent, '_get_code_context', return_value="// mock context"):
            prompt = agent._build_fix_prompt(task)

        assert "null" in prompt.lower()
        assert "src/test.ts" in prompt
        assert "10" in prompt

    def test_generate_fix_with_llm_success(self):
        """Test _generate_fix_with_llm returns fix on success"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        mock_response = MagicMock()
        mock_response.content = "const value = obj?.property ?? defaultValue;"

        mock_client = MagicMock()
        mock_client.generate.return_value = mock_response

        with patch.object(agent, '_get_llm_client', return_value=mock_client):
            with patch.object(agent, '_get_code_context', return_value="// context"):
                fix = agent._generate_fix_with_llm(task)

        assert fix is not None
        assert "obj?.property" in fix

    def test_generate_fix_with_llm_strips_code_blocks(self):
        """Test _generate_fix_with_llm strips markdown code blocks"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        mock_response = MagicMock()
        mock_response.content = "```typescript\nconst x = value ?? 0;\n```"

        mock_client = MagicMock()
        mock_client.generate.return_value = mock_response

        with patch.object(agent, '_get_llm_client', return_value=mock_client):
            with patch.object(agent, '_get_code_context', return_value="// context"):
                fix = agent._generate_fix_with_llm(task)

        assert fix is not None
        assert "```" not in fix
        assert "const x = value ?? 0;" in fix

    def test_generate_fix_with_llm_retries_on_failure(self):
        """Test _generate_fix_with_llm retries on API failure"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        mock_response = MagicMock()
        mock_response.content = "const fixed = value!;"

        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            Exception("API error"),
            mock_response
        ]

        with patch.object(agent, '_get_llm_client', return_value=mock_client):
            with patch.object(agent, '_get_code_context', return_value="// context"):
                with patch('time.sleep'):
                    fix = agent._generate_fix_with_llm(task, max_retries=2)

        assert fix is not None
        assert mock_client.generate.call_count == 2

    def test_generate_fix_with_llm_returns_none_after_max_retries(self):
        """Test _generate_fix_with_llm returns None after max retries"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("API error")

        with patch.object(agent, '_get_llm_client', return_value=mock_client):
            with patch.object(agent, '_get_code_context', return_value="// context"):
                with patch('time.sleep'):
                    fix = agent._generate_fix_with_llm(task, max_retries=1)

        assert fix is None
        assert mock_client.generate.call_count == 2

    def test_generate_fix_falls_back_to_placeholder(self):
        """Test generate_fix falls back to placeholder when LLM unavailable"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=15,
            column=1,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        with patch.object(agent, '_generate_fix_with_llm', return_value=None):
            fix = agent.generate_fix(task)

        assert fix is not None
        assert "null check" in fix.lower()
        assert "15" in fix

    def test_generate_fix_uses_llm_when_available(self):
        """Test generate_fix uses LLM fix when available"""
        agent = RefactorAgent(repo_path="/tmp/test")

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = RefactorTask(
            task_id="test-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        llm_fix = "const safeValue = value ?? defaultValue;"

        with patch.object(agent, '_generate_fix_with_llm', return_value=llm_fix):
            fix = agent.generate_fix(task)

        assert fix == llm_fix

    def test_all_fallback_strategies_have_messages(self):
        """Test all common strategies have fallback messages"""
        agent = RefactorAgent(repo_path="/tmp/test")

        strategies = [
            "null_check", "undefined_check", "implicit_any",
            "possibly_null", "possibly_undefined", "type_mismatch",
            "property_missing", "argument_type", "unknown_type",
            "binding_any", "argument_count"
        ]

        for strategy in strategies:
            error = TSError(
                file_path="src/test.ts",
                line=10,
                column=1,
                error_code="TS0000",
                message="Test error"
            )

            task = RefactorTask(
                task_id="test",
                error=error,
                fix_strategy=strategy,
                estimated_risk=RefactorRisk.LOW
            )

            with patch.object(agent, '_generate_fix_with_llm', return_value=None):
                fix = agent.generate_fix(task)

            assert fix is not None, f"No fallback for strategy: {strategy}"
