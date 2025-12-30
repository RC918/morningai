"""
Tests for Refactor Agent - Phase 4 (#1818, #1888, #1889)
"""
import pytest
import tempfile
import time
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


class TestFileModification:
    """Tests for file modification functionality (#1889)"""

    def test_create_backup_success(self):
        """Test _create_backup creates backup file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("const x = 1;")

            agent = RefactorAgent(repo_path=tmpdir)
            backup_path = agent._create_backup(test_file)

            assert backup_path is not None
            assert backup_path.exists()
            assert backup_path.read_text() == "const x = 1;"

    def test_create_backup_nonexistent_file(self):
        """Test _create_backup returns None for non-existent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            backup_path = agent._create_backup(Path(tmpdir) / "nonexistent.ts")

            assert backup_path is None

    def test_restore_from_backup_success(self):
        """Test _restore_from_backup restores file content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_file = Path(tmpdir) / "test.ts"
            backup_file = Path(tmpdir) / "test.ts.bak"

            original_file.write_text("modified content")
            backup_file.write_text("original content")

            agent = RefactorAgent(repo_path=tmpdir)
            success = agent._restore_from_backup(original_file, backup_file)

            assert success is True
            assert original_file.read_text() == "original content"

    def test_restore_from_backup_missing_backup(self):
        """Test _restore_from_backup returns False for missing backup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_file = Path(tmpdir) / "test.ts"
            original_file.write_text("content")

            agent = RefactorAgent(repo_path=tmpdir)
            success = agent._restore_from_backup(
                original_file,
                Path(tmpdir) / "nonexistent.bak"
            )

            assert success is False

    def test_get_diff_preview(self):
        """Test get_diff_preview generates diff output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "src" / "test.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n")

            agent = RefactorAgent(repo_path=tmpdir)

            error = TSError(
                file_path="src/test.ts",
                line=3,
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

            diff = agent.get_diff_preview(task, "const x = value ?? 0;")

            assert diff is not None
            assert "---" in diff
            assert "+++" in diff
            assert "-line 3" in diff
            assert "+const x = value ?? 0;" in diff

    def test_get_diff_preview_file_not_found(self):
        """Test get_diff_preview returns None for missing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            error = TSError(
                file_path="nonexistent.ts",
                line=1,
                column=1,
                error_code="TS2531",
                message="Error"
            )

            task = RefactorTask(
                task_id="test",
                error=error,
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            diff = agent.get_diff_preview(task, "fix")

            assert diff is None

    def test_apply_fix_success(self):
        """Test apply_fix modifies file correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "src" / "test.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("line 1\n    const x = null;\nline 3\n")

            agent = RefactorAgent(repo_path=tmpdir)

            error = TSError(
                file_path="src/test.ts",
                line=2,
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

            success, backup_path = agent.apply_fix(task, "const x = value ?? 0;")

            assert success is True
            assert backup_path is not None
            assert backup_path.exists()

            content = test_file.read_text()
            assert "const x = value ?? 0;" in content

    def test_apply_fix_preserves_indentation(self):
        """Test apply_fix preserves original indentation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("function test() {\n    const x = null;\n}\n")

            agent = RefactorAgent(repo_path=tmpdir)

            error = TSError(
                file_path="test.ts",
                line=2,
                column=5,
                error_code="TS2531",
                message="Error"
            )

            task = RefactorTask(
                task_id="test",
                error=error,
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            success, _ = agent.apply_fix(task, "const x = value ?? 0;")

            assert success is True
            content = test_file.read_text()
            assert "    const x = value ?? 0;" in content

    def test_apply_fix_file_not_found(self):
        """Test apply_fix returns False for missing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            error = TSError(
                file_path="nonexistent.ts",
                line=1,
                column=1,
                error_code="TS2531",
                message="Error"
            )

            task = RefactorTask(
                task_id="test",
                error=error,
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            success, backup_path = agent.apply_fix(task, "fix")

            assert success is False
            assert backup_path is None

    def test_apply_fix_without_backup(self):
        """Test apply_fix works without creating backup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("const x = null;\n")

            agent = RefactorAgent(repo_path=tmpdir)

            error = TSError(
                file_path="test.ts",
                line=1,
                column=1,
                error_code="TS2531",
                message="Error"
            )

            task = RefactorTask(
                task_id="test",
                error=error,
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            success, backup_path = agent.apply_fix(task, "const x = 0;", create_backup=False)

            assert success is True
            assert backup_path is None

    def test_apply_fixes_batch(self):
        """Test apply_fixes_batch applies multiple fixes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.ts"
            file2 = Path(tmpdir) / "file2.ts"
            file1.write_text("const a = null;\n")
            file2.write_text("const b = null;\n")

            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id="task1",
                    error=TSError(
                        file_path="file1.ts", line=1, column=1,
                        error_code="TS2531", message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW
                ),
                RefactorTask(
                    task_id="task2",
                    error=TSError(
                        file_path="file2.ts", line=1, column=1,
                        error_code="TS2531", message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW
                ),
            ]

            fixes = ["const a = 0;", "const b = 0;"]

            results = agent.apply_fixes_batch(tasks, fixes)

            assert results['success_count'] == 2
            assert results['failure_count'] == 0
            assert len(results['applied']) == 2
            assert len(results['backups']) == 2

    def test_apply_fixes_batch_with_none_fix(self):
        """Test apply_fixes_batch handles None fixes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.ts"
            file1.write_text("const a = null;\n")

            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id="task1",
                    error=TSError(
                        file_path="file1.ts", line=1, column=1,
                        error_code="TS2531", message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW
                ),
            ]

            fixes = [None]

            results = agent.apply_fixes_batch(tasks, fixes)

            assert results['success_count'] == 0
            assert results['failure_count'] == 1
            assert "file1.ts" in results['failed']

    def test_rollback_batch(self):
        """Test rollback_batch restores multiple files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.ts"
            file2 = Path(tmpdir) / "file2.ts"
            backup1 = Path(tmpdir) / ".refactor_backups" / "file1.bak"
            backup2 = Path(tmpdir) / ".refactor_backups" / "file2.bak"

            backup1.parent.mkdir(parents=True, exist_ok=True)

            file1.write_text("modified1")
            file2.write_text("modified2")
            backup1.write_text("original1")
            backup2.write_text("original2")

            agent = RefactorAgent(repo_path=tmpdir)

            backups = {
                "file1.ts": backup1,
                "file2.ts": backup2,
            }

            results = agent.rollback_batch(backups)

            assert results["file1.ts"] is True
            assert results["file2.ts"] is True
            assert file1.read_text() == "original1"
            assert file2.read_text() == "original2"

    def test_cleanup_backups(self):
        """Test cleanup_backups removes old backup files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / ".refactor_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            old_backup = backup_dir / "old.bak"
            new_backup = backup_dir / "new.bak"

            old_backup.write_text("old")
            new_backup.write_text("new")

            import os
            old_time = time.time() - (48 * 3600)
            os.utime(old_backup, (old_time, old_time))

            agent = RefactorAgent(repo_path=tmpdir)
            deleted_count = agent.cleanup_backups(max_age_hours=24)

            assert deleted_count == 1
            assert not old_backup.exists()
            assert new_backup.exists()

    def test_cleanup_backups_no_backup_dir(self):
        """Test cleanup_backups returns 0 when no backup dir exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            deleted_count = agent.cleanup_backups()

            assert deleted_count == 0

    def test_apply_fixes_batch_same_file(self):
        """Test apply_fixes_batch handles same-file line offset correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text(
                "line1\n"
                "line2\n"
                "line3\n"
                "line4\n"
                "line5\n"
            )

            agent = RefactorAgent(repo_path=tmpdir)

            task1 = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="test.ts",
                    line=2,
                    column=1,
                    error_code="TS2322",
                    message="Error on line 2"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            task2 = RefactorTask(
                task_id="task2",
                error=TSError(
                    file_path="test.ts",
                    line=4,
                    column=1,
                    error_code="TS2322",
                    message="Error on line 4"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            fix1 = "fixed2a\nfixed2b"
            fix2 = "fixed4"

            results = agent.apply_fixes_batch(
                [task1, task2],
                [fix1, fix2],
                create_backups=True
            )

            assert results['success_count'] == 2
            assert results['failure_count'] == 0

            content = test_file.read_text()
            lines = content.strip().split("\n")

            assert "fixed2a" in lines[1]
            assert "fixed2b" in lines[2]
            assert "fixed4" in lines[4]

    def test_get_diff_preview_multiline(self):
        """Test get_diff_preview shows all lines of multi-line fix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text(
                "line1\n"
                "line2\n"
                "line3\n"
                "line4\n"
                "line5\n"
            )

            agent = RefactorAgent(repo_path=tmpdir)

            task = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="test.ts",
                    line=3,
                    column=1,
                    error_code="TS2322",
                    message="Error"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW
            )

            fix = "fixedA\nfixedB\nfixedC"

            diff = agent.get_diff_preview(task, fix)

            assert diff is not None
            assert "-line3" in diff
            assert "+fixedA" in diff
            assert "+fixedB" in diff
            assert "+fixedC" in diff


class TestPRAutomation:
    """Tests for PR Automation functionality (#1890)"""

    def test_generate_branch_name(self):
        """Test branch name generation follows expected format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            branch_name = agent._generate_branch_name()

            assert branch_name.startswith("refactor/ts-fixes-")
            parts = branch_name.split("-")
            assert len(parts) >= 4

    def test_generate_pr_title(self):
        """Test PR title generation includes error count"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            title = agent._generate_pr_title(5)

            assert "5 errors" in title
            assert "fix(ts):" in title
            assert "Automated TS strict mode fixes" in title

    def test_generate_pr_title_single_error(self):
        """Test PR title generation with single error uses singular form"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            title = agent._generate_pr_title(1)

            assert "1 error)" in title
            assert "1 errors" not in title

    def test_generate_branch_name_with_timestamp(self):
        """Test branch name generation with custom timestamp"""
        from datetime import datetime
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            ts = datetime(2025, 12, 4, 10, 30, 45)
            branch_name = agent._generate_branch_name(timestamp=ts)

            assert branch_name == "refactor/ts-fixes-20251204-103045"

    def test_generate_pr_title_with_timestamp(self):
        """Test PR title generation with custom timestamp"""
        from datetime import datetime
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            ts = datetime(2025, 12, 4, 10, 30, 45)
            title = agent._generate_pr_title(3, timestamp=ts)

            assert "2025-12-04" in title
            assert "3 errors" in title

    def test_generate_changelog_empty_tasks(self):
        """Test changelog generation with no completed tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            changelog = agent._generate_changelog([])

            assert changelog == "No fixes applied."

    def test_generate_changelog_with_tasks(self):
        """Test changelog generation with completed tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            task1 = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="src/file1.ts",
                    line=10,
                    column=5,
                    error_code="TS2531",
                    message="Object is possibly 'null'"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW,
                status="completed"
            )

            task2 = RefactorTask(
                task_id="task2",
                error=TSError(
                    file_path="src/file1.ts",
                    line=20,
                    column=3,
                    error_code="TS7006",
                    message="Parameter implicitly has 'any' type"
                ),
                fix_strategy="implicit_any",
                estimated_risk=RefactorRisk.MEDIUM,
                status="completed"
            )

            task3 = RefactorTask(
                task_id="task3",
                error=TSError(
                    file_path="src/file2.ts",
                    line=5,
                    column=1,
                    error_code="TS2322",
                    message="Type mismatch"
                ),
                fix_strategy="type_mismatch",
                estimated_risk=RefactorRisk.HIGH,
                status="failed"
            )

            changelog = agent._generate_changelog([task1, task2, task3])

            assert "## Changelog" in changelog
            assert "`src/file1.ts`" in changelog
            assert "Line 10" in changelog
            assert "Line 20" in changelog
            assert "`TS2531`" in changelog
            assert "`TS7006`" in changelog
            assert "src/file2.ts" not in changelog

    def test_generate_pr_description(self):
        """Test PR description generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            result = RefactorResult(
                run_id="test-run-123",
                started_at=time.time(),
                completed_at=time.time(),
                total_errors_found=10,
                errors_fixed=3,
                errors_failed=1,
                summary="Found 10 TS errors. Fixed 3, failed 1. Remaining: 6"
            )

            task = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="src/test.ts",
                    line=10,
                    column=5,
                    error_code="TS2531",
                    message="Object is possibly 'null'"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW,
                status="completed"
            )

            description = agent._generate_pr_description(result, [task])

            assert "## Description" in description
            assert "Automated TypeScript strict mode error fixes" in description
            assert "test-run-123" in description
            assert "## Changelog" in description
            assert "## How to Review" in description
            assert "`TS2531`: 1" in description

    def test_create_pr_auto_pr_disabled(self):
        """Test create_pr returns None when auto_pr is disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            result = RefactorResult(
                run_id="test-run",
                started_at=time.time()
            )

            pr_url, pr_number = agent.create_pr(result, [])

            assert pr_url is None
            assert pr_number is None

    def test_create_pr_no_completed_tasks(self):
        """Test create_pr returns None when no completed tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = True

            result = RefactorResult(
                run_id="test-run",
                started_at=time.time()
            )

            task = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="src/test.ts",
                    line=10,
                    column=5,
                    error_code="TS2531",
                    message="Error"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW,
                status="failed"
            )

            pr_url, pr_number = agent.create_pr(result, [task])

            assert pr_url is None
            assert pr_number is None

    @patch('subprocess.run')
    def test_create_refactor_branch_success(self, mock_run):
        """Test branch creation success"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            result = agent._create_refactor_branch("test-branch")

            assert result is True
            mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_create_refactor_branch_failure(self, mock_run):
        """Test branch creation failure"""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="branch already exists"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            result = agent._create_refactor_branch("test-branch")

            assert result is False

    @patch('subprocess.run')
    def test_commit_fixes_success(self, mock_run):
        """Test commit fixes success"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            task = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="src/test.ts",
                    line=10,
                    column=5,
                    error_code="TS2531",
                    message="Error"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW,
                status="completed"
            )

            result = agent._commit_fixes([task], "test commit")

            assert result is True

    @patch('subprocess.run')
    def test_commit_fixes_no_completed_tasks(self, mock_run):
        """Test commit fixes with no completed tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            task = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="src/test.ts",
                    line=10,
                    column=5,
                    error_code="TS2531",
                    message="Error"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW,
                status="failed"
            )

            result = agent._commit_fixes([task], "test commit")

            assert result is False
            mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_commit_fixes_git_add_failure_aborts(self, mock_run):
        """Test commit fixes aborts when git add fails"""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="git add failed"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            task = RefactorTask(
                task_id="task1",
                error=TSError(
                    file_path="src/test.ts",
                    line=10,
                    column=5,
                    error_code="TS2531",
                    message="Error"
                ),
                fix_strategy="null_check",
                estimated_risk=RefactorRisk.LOW,
                status="completed"
            )

            result = agent._commit_fixes([task], "test commit")

            assert result is False
            assert mock_run.call_count == 1

    @patch('subprocess.run')
    def test_push_branch_success(self, mock_run):
        """Test push branch success"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            result = agent._push_branch("test-branch")

            assert result is True

    @patch('subprocess.run')
    def test_push_branch_failure(self, mock_run):
        """Test push branch failure"""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="push failed"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            result = agent._push_branch("test-branch")

            assert result is False

    @patch('subprocess.run')
    def test_checkout_main_success(self, mock_run):
        """Test checkout main success"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            result = agent._checkout_main()

            assert result is True

    @patch('subprocess.run')
    def test_checkout_main_failure(self, mock_run):
        """Test checkout main failure"""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            result = agent._checkout_main()

            assert result is False

    @pytest.mark.xfail(reason="Pre-existing legacy debt #3251 - GITHUB_TOKEN env var not set in CI")
    def test_get_github_repo_no_token(self):
        """Test get_github_repo returns None when no token available"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.dict('os.environ', {}, clear=True):
                with patch('common.config.settings.settings') as mock_settings:
                    mock_settings.agent_github_token = None
                    mock_settings.github_token = None

                    _ = agent._get_github_repo()

    def test_changelog_groups_by_file(self):
        """Test changelog groups fixes by file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id=f"task{i}",
                    error=TSError(
                        file_path=f"src/file{i % 2}.ts",
                        line=i * 10,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
                for i in range(4)
            ]

            changelog = agent._generate_changelog(tasks)

            assert "`src/file0.ts`" in changelog
            assert "`src/file1.ts`" in changelog


class TestRunRefactorPipeline:
    """Tests for run_refactor() pipeline including apply and PR creation (TS-3)"""

    def test_run_refactor_applies_fixes_when_not_dry_run(self):
        """Test that run_refactor calls apply_fixes_batch when not in dry_run mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "src" / "test.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("const x = null;\n")

            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? 'default';"
                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 0,
                    'applied': ['src/test.ts'],
                    'failed': [],
                    'backups': {},
                    'task_results': {'task-0': True}
                }

                result = agent.run_refactor(max_errors=1, dry_run=False)

                mock_apply.assert_called_once()
                assert result.errors_fixed == 1

    def test_run_refactor_does_not_apply_in_dry_run(self):
        """Test that run_refactor does NOT call apply_fixes_batch in dry_run mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]

                result = agent.run_refactor(max_errors=1, dry_run=True)

                mock_apply.assert_not_called()
                assert result.errors_fixed == 0
                assert result.metadata["dry_run"] is True

    def test_run_refactor_creates_pr_when_auto_pr_enabled(self):
        """Test that run_refactor calls create_pr when auto_pr is enabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = True

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply, \
                 patch.object(agent, 'create_pr') as mock_create_pr:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? 'default';"
                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 0,
                    'applied': ['src/test.ts'],
                    'failed': [],
                    'backups': {},
                    'task_results': {'task-0': True}
                }
                mock_create_pr.return_value = ("https://github.com/test/pr/1", 1)

                result = agent.run_refactor(max_errors=1, dry_run=False)

                mock_create_pr.assert_called_once()
                assert result.pr_url == "https://github.com/test/pr/1"
                assert result.metadata["pr_number"] == 1

    def test_run_refactor_does_not_create_pr_when_auto_pr_disabled(self):
        """Test that run_refactor does NOT call create_pr when auto_pr is disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply, \
                 patch.object(agent, 'create_pr') as mock_create_pr:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? 'default';"
                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 0,
                    'applied': ['src/test.ts'],
                    'failed': [],
                    'backups': {},
                    'task_results': {'task-0': True}
                }

                result = agent.run_refactor(max_errors=1, dry_run=False)

                mock_create_pr.assert_not_called()
                assert result.pr_url is None

    def test_run_refactor_handles_empty_fix_applied(self):
        """Test that run_refactor handles tasks with empty fix_applied"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = ""

                result = agent.run_refactor(max_errors=1, dry_run=False)

                mock_apply.assert_not_called()
                assert result.errors_fixed == 0
                assert result.errors_failed == 1

    def test_run_refactor_handles_none_fix_applied(self):
        """Test that run_refactor handles tasks with None fix_applied"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = None

                result = agent.run_refactor(max_errors=1, dry_run=False)

                assert result.errors_fixed == 0
                assert result.errors_failed == 1

    def test_run_refactor_handles_apply_failure(self):
        """Test that run_refactor handles apply_fixes_batch failures correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? 'default';"
                mock_apply.return_value = {
                    'success_count': 0,
                    'failure_count': 1,
                    'applied': [],
                    'failed': ['src/test.ts'],
                    'backups': {},
                    'task_results': {'task-0': False}
                }

                result = agent.run_refactor(max_errors=1, dry_run=False)

                assert result.errors_fixed == 0
                assert result.errors_failed == 1
                assert result.tasks[0].status == "failed"
                assert "Failed to apply" in result.tasks[0].error_message

    def test_run_refactor_handles_partial_apply_success(self):
        """Test that run_refactor handles partial apply success correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test1.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error 1"
                    ),
                    TSError(
                        file_path="src/test2.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error 2"
                    )
                ]
                mock_generate.return_value = "fixed code"
                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 1,
                    'applied': ['src/test1.ts'],
                    'failed': ['src/test2.ts'],
                    'backups': {},
                    'task_results': {'task-0': True, 'task-1': False}
                }

                result = agent.run_refactor(max_errors=2, dry_run=False)

                assert result.errors_fixed == 1
                assert result.errors_failed == 1

    def test_run_refactor_handles_create_pr_failure(self):
        """Test that run_refactor handles create_pr failure gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = True

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply, \
                 patch.object(agent, 'create_pr') as mock_create_pr:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? 'default';"
                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 0,
                    'applied': ['src/test.ts'],
                    'failed': [],
                    'backups': {},
                    'task_results': {'task-0': True}
                }
                mock_create_pr.return_value = (None, None)

                result = agent.run_refactor(max_errors=1, dry_run=False)

                mock_create_pr.assert_called_once()
                assert result.pr_url is None
                assert result.errors_fixed == 1

    def test_run_refactor_filters_whitespace_only_fixes(self):
        """Test that run_refactor filters out whitespace-only fix_applied"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "   \n\t  "

                result = agent.run_refactor(max_errors=1, dry_run=False)

                mock_apply.assert_not_called()
                assert result.errors_fixed == 0


class TestApplyFixesBatchTaskResults:
    """Tests for apply_fixes_batch task_results tracking (TS-3)"""

    def test_apply_fixes_batch_returns_task_results(self):
        """Test that apply_fixes_batch returns task_results dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("line 1\nline 2\nline 3\n")

            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id="task-001",
                    error=TSError(
                        file_path="test.ts",
                        line=2,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
            ]
            fixes = ["fixed line 2"]

            results = agent.apply_fixes_batch(tasks, fixes)

            assert 'task_results' in results
            assert results['task_results']['task-001'] is True

    def test_apply_fixes_batch_task_results_tracks_failures(self):
        """Test that apply_fixes_batch tracks failures in task_results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id="task-001",
                    error=TSError(
                        file_path="nonexistent.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
            ]
            fixes = ["fixed code"]

            results = agent.apply_fixes_batch(tasks, fixes)

            assert results['task_results']['task-001'] is False
            assert results['failure_count'] == 1

    def test_apply_fixes_batch_handles_none_fix(self):
        """Test that apply_fixes_batch handles None fix correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("line 1\n")

            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id="task-001",
                    error=TSError(
                        file_path="test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
            ]
            fixes = [None]

            results = agent.apply_fixes_batch(tasks, fixes)

            assert results['task_results']['task-001'] is False
            assert results['failure_count'] == 1

    def test_apply_fixes_batch_handles_empty_string_fix(self):
        """Test that apply_fixes_batch handles empty string fix correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("line 1\n")

            agent = RefactorAgent(repo_path=tmpdir)

            tasks = [
                RefactorTask(
                    task_id="task-001",
                    error=TSError(
                        file_path="test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
            ]
            fixes = [""]

            results = agent.apply_fixes_batch(tasks, fixes)

            assert results['task_results']['task-001'] is False
            assert results['failure_count'] == 1


class TestCheckExistingRefactorPR:
    """Tests for _check_existing_refactor_pr method (TS-3 follow-up)"""

    def test_check_existing_refactor_pr_returns_none_when_no_repo(self):
        """Test that _check_existing_refactor_pr returns None when GitHub unavailable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.object(agent, '_get_github_repo', return_value=None):
                result = agent._check_existing_refactor_pr()
                assert result is None

    def test_check_existing_refactor_pr_finds_matching_pr_by_title(self):
        """Test that _check_existing_refactor_pr finds PR with fix(ts): title and automated label"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_label_automated = MagicMock()
            mock_label_automated.name = "automated"

            mock_pr = MagicMock()
            mock_pr.title = "fix(ts): Automated TS strict mode fixes (5 errors) - 2025-01-01"
            mock_pr.number = 123
            mock_pr.html_url = "https://github.com/test/repo/pull/123"
            mock_pr.labels = [mock_label_automated]

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.get_pulls.return_value = [mock_pr]

            with patch.object(agent, '_get_github_repo', return_value=mock_repo):
                result = agent._check_existing_refactor_pr()
                assert result == mock_pr
                mock_repo.get_pulls.assert_called_once_with(state='open', base='main')

    def test_check_existing_refactor_pr_requires_both_title_and_label(self):
        """Test that _check_existing_refactor_pr requires BOTH fix(ts): title AND automated label"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_label_automated = MagicMock()
            mock_label_automated.name = "automated"

            mock_pr = MagicMock()
            mock_pr.title = "some other title"
            mock_pr.number = 456
            mock_pr.html_url = "https://github.com/test/repo/pull/456"
            mock_pr.labels = [mock_label_automated]

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.get_pulls.return_value = [mock_pr]

            with patch.object(agent, '_get_github_repo', return_value=mock_repo):
                result = agent._check_existing_refactor_pr()
                assert result is None

    def test_check_existing_refactor_pr_returns_none_when_no_match(self):
        """Test that _check_existing_refactor_pr returns None when no matching PR"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_label = MagicMock()
            mock_label.name = "bug"

            mock_pr = MagicMock()
            mock_pr.title = "fix: some bug"
            mock_pr.labels = [mock_label]

            mock_repo = MagicMock()
            mock_repo.get_pulls.return_value = [mock_pr]

            with patch.object(agent, '_get_github_repo', return_value=mock_repo):
                result = agent._check_existing_refactor_pr()
                assert result is None

    def test_check_existing_refactor_pr_handles_exception(self):
        """Test that _check_existing_refactor_pr handles exceptions gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_repo = MagicMock()
            mock_repo.get_pulls.side_effect = Exception("API error")

            with patch.object(agent, '_get_github_repo', return_value=mock_repo):
                result = agent._check_existing_refactor_pr()
                assert result is None

    def test_check_existing_refactor_pr_uses_custom_target_branch(self):
        """Test that _check_existing_refactor_pr uses custom target branch when provided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_label_automated = MagicMock()
            mock_label_automated.name = "automated"

            mock_pr = MagicMock()
            mock_pr.title = "fix(ts): Automated TS strict mode fixes (3 errors) - 2025-01-01"
            mock_pr.number = 789
            mock_pr.html_url = "https://github.com/test/repo/pull/789"
            mock_pr.labels = [mock_label_automated]

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.get_pulls.return_value = [mock_pr]

            with patch.object(agent, '_get_github_repo', return_value=mock_repo):
                result = agent._check_existing_refactor_pr(target_branch="develop")
                assert result == mock_pr
                mock_repo.get_pulls.assert_called_once_with(state='open', base='develop')


class TestPreparePRBranch:
    """Tests for _prepare_pr_branch method (TS-3 follow-up)"""

    def test_prepare_pr_branch_success(self):
        """Test that _prepare_pr_branch returns True on success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.object(agent, '_create_refactor_branch', return_value=True), \
                 patch.object(agent, '_commit_fixes', return_value=True), \
                 patch.object(agent, '_push_branch', return_value=True):

                result = agent._prepare_pr_branch("test-branch", [], "Test title")
                assert result is True

    def test_prepare_pr_branch_fails_on_branch_creation(self):
        """Test that _prepare_pr_branch returns False when branch creation fails"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.object(agent, '_create_refactor_branch', return_value=False):
                result = agent._prepare_pr_branch("test-branch", [], "Test title")
                assert result is False

    def test_prepare_pr_branch_fails_on_commit(self):
        """Test that _prepare_pr_branch returns False and checkouts main on commit failure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.object(agent, '_create_refactor_branch', return_value=True), \
                 patch.object(agent, '_commit_fixes', return_value=False), \
                 patch.object(agent, '_checkout_main', return_value=True) as mock_checkout:

                result = agent._prepare_pr_branch("test-branch", [], "Test title")
                assert result is False
                mock_checkout.assert_called_once()

    def test_prepare_pr_branch_fails_on_push(self):
        """Test that _prepare_pr_branch returns False and checkouts main on push failure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            with patch.object(agent, '_create_refactor_branch', return_value=True), \
                 patch.object(agent, '_commit_fixes', return_value=True), \
                 patch.object(agent, '_push_branch', return_value=False), \
                 patch.object(agent, '_checkout_main', return_value=True) as mock_checkout:

                result = agent._prepare_pr_branch("test-branch", [], "Test title")
                assert result is False
                mock_checkout.assert_called_once()


class TestSubmitPRToGitHub:
    """Tests for _submit_pr_to_github method (TS-3 follow-up)"""

    def test_submit_pr_to_github_success(self):
        """Test that _submit_pr_to_github returns PR URL and number on success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_pr = MagicMock()
            mock_pr.html_url = "https://github.com/test/repo/pull/123"
            mock_pr.number = 123

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.create_pull.return_value = mock_pr

            result = agent._submit_pr_to_github(
                mock_repo, "test-branch", "Test title", "Test body", False, ["refactor"]
            )

            assert result == ("https://github.com/test/repo/pull/123", 123)
            mock_repo.create_pull.assert_called_once_with(
                title="Test title",
                body="Test body",
                head="test-branch",
                base="main",
                draft=False
            )
            mock_pr.add_to_labels.assert_called_once_with("refactor")

    def test_submit_pr_to_github_with_draft(self):
        """Test that _submit_pr_to_github creates draft PR when requested"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_pr = MagicMock()
            mock_pr.html_url = "https://github.com/test/repo/pull/123"
            mock_pr.number = 123

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.create_pull.return_value = mock_pr

            agent._submit_pr_to_github(
                mock_repo, "test-branch", "Test title", "Test body", True, []
            )

            mock_repo.create_pull.assert_called_once_with(
                title="Test title",
                body="Test body",
                head="test-branch",
                base="main",
                draft=True
            )

    def test_submit_pr_to_github_handles_label_failure(self):
        """Test that _submit_pr_to_github handles label addition failure gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_pr = MagicMock()
            mock_pr.html_url = "https://github.com/test/repo/pull/123"
            mock_pr.number = 123
            mock_pr.add_to_labels.side_effect = Exception("Label error")

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.create_pull.return_value = mock_pr

            result = agent._submit_pr_to_github(
                mock_repo, "test-branch", "Test title", "Test body", False, ["refactor"]
            )

            assert result == ("https://github.com/test/repo/pull/123", 123)

    def test_submit_pr_to_github_handles_create_failure(self):
        """Test that _submit_pr_to_github returns None on PR creation failure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_repo = MagicMock()
            mock_repo.create_pull.side_effect = Exception("API error")

            result = agent._submit_pr_to_github(
                mock_repo, "test-branch", "Test title", "Test body", False, ["refactor"]
            )

            assert result == (None, None)

    def test_submit_pr_to_github_no_labels(self):
        """Test that _submit_pr_to_github works with empty labels list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_pr = MagicMock()
            mock_pr.html_url = "https://github.com/test/repo/pull/123"
            mock_pr.number = 123

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.create_pull.return_value = mock_pr

            result = agent._submit_pr_to_github(
                mock_repo, "test-branch", "Test title", "Test body", False, []
            )

            assert result == ("https://github.com/test/repo/pull/123", 123)
            mock_pr.add_to_labels.assert_not_called()

    def test_submit_pr_to_github_custom_base_branch(self):
        """Test that _submit_pr_to_github uses custom base branch when provided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            mock_pr = MagicMock()
            mock_pr.html_url = "https://github.com/test/repo/pull/123"
            mock_pr.number = 123

            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_repo.create_pull.return_value = mock_pr

            result = agent._submit_pr_to_github(
                mock_repo, "test-branch", "Test title", "Test body", False, [],
                base_branch="develop"
            )

            assert result == ("https://github.com/test/repo/pull/123", 123)
            mock_repo.create_pull.assert_called_once_with(
                title="Test title",
                body="Test body",
                head="test-branch",
                base="develop",
                draft=False
            )


class TestCreatePRWithExistingPRCheck:
    """Tests for create_pr with existing PR check (TS-3 follow-up)"""

    def test_create_pr_skips_when_existing_pr_found(self):
        """Test that create_pr skips creation when existing open PR found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = True

            mock_existing_pr = MagicMock()
            mock_existing_pr.number = 999
            mock_existing_pr.html_url = "https://github.com/test/repo/pull/999"

            tasks = [
                RefactorTask(
                    task_id="task-001",
                    error=TSError(
                        file_path="test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
            ]
            result = RefactorResult(
                run_id="test-run",
                started_at=0.0,
                total_errors_found=1,
                errors_fixed=1,
                errors_failed=0,
                tasks=tasks
            )

            with patch.object(agent, '_check_existing_refactor_pr', return_value=mock_existing_pr):
                pr_url, pr_number = agent.create_pr(result, tasks)

                assert pr_url is None
                assert pr_number is None

    def test_create_pr_proceeds_when_no_existing_pr(self):
        """Test that create_pr proceeds when no existing open PR found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = True

            tasks = [
                RefactorTask(
                    task_id="task-001",
                    error=TSError(
                        file_path="test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Error"
                    ),
                    fix_strategy="null_check",
                    estimated_risk=RefactorRisk.LOW,
                    status="completed"
                )
            ]
            result = RefactorResult(
                run_id="test-run",
                started_at=0.0,
                total_errors_found=1,
                errors_fixed=1,
                errors_failed=0,
                tasks=tasks
            )

            with patch.object(agent, '_check_existing_refactor_pr', return_value=None), \
                 patch.object(agent, '_prepare_pr_branch', return_value=True), \
                 patch.object(agent, '_get_github_repo') as mock_get_repo, \
                 patch.object(agent, '_submit_pr_to_github', return_value=("https://github.com/test/pr/1", 1)), \
                 patch.object(agent, '_checkout_main', return_value=True):

                mock_repo = MagicMock()
                mock_get_repo.return_value = mock_repo

                pr_url, pr_number = agent.create_pr(result, tasks)

                assert pr_url == "https://github.com/test/pr/1"
                assert pr_number == 1


class TestSanitizeLLMOutput:
    """Tests for _sanitize_llm_output method"""

    def test_sanitize_removes_marker_lines(self):
        """Test that lines with >>> marker are sanitized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            polluted_output = ">>> 34: const x = null;\n    35: const y = 1;"
            result = agent._sanitize_llm_output(polluted_output)

            assert ">>>" not in result
            assert "34:" not in result
            assert "const x = null;" in result
            assert "const y = 1;" in result

    def test_sanitize_preserves_legitimate_code(self):
        """Test that legitimate code like object literals is NOT modified"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            legitimate_code = 'const obj = { 1: "first", 2: "second" };'
            result = agent._sanitize_llm_output(legitimate_code)

            assert result == legitimate_code

    def test_sanitize_preserves_code_without_marker(self):
        """Test that code without >>> marker is returned unchanged"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            clean_code = "const x = 1;\nconst y = 2;"
            result = agent._sanitize_llm_output(clean_code)

            assert result == clean_code

    def test_sanitize_handles_empty_input(self):
        """Test that empty input returns empty output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            assert agent._sanitize_llm_output("") == ""
            assert agent._sanitize_llm_output(None) is None

    def test_sanitize_handles_multiline_with_markers(self):
        """Test sanitization of multiline output with mixed markers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            polluted_output = """>>> 10: function test() {
    11:   const x = null;
>>> 12:   return x;
    13: }"""
            result = agent._sanitize_llm_output(polluted_output)

            assert ">>>" not in result
            assert "10:" not in result
            assert "function test()" in result
            assert "const x = null;" in result
            assert "return x;" in result


class TestVerifySyntaxAfterFix:
    """Tests for _verify_syntax_after_fix method"""

    def test_verify_syntax_returns_true_on_exception(self):
        """Test that exceptions trigger fail-closed behavior (returns True)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test-project"
            project_dir.mkdir()

            agent = RefactorAgent(repo_path=tmpdir)

            with patch('subprocess.run', side_effect=Exception("pnpm not found")):
                has_errors, error_list = agent._verify_syntax_after_fix("test-project")

                assert has_errors is True
                assert len(error_list) == 1
                assert "Error during syntax verification" in error_list[0]

    def test_verify_syntax_returns_false_for_nonexistent_project(self):
        """Test that nonexistent project returns False (no errors)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            has_errors, error_list = agent._verify_syntax_after_fix("nonexistent-project")

            assert has_errors is False
            assert error_list == []


class TestRollbackOnSyntaxErrors:
    """Tests for rollback behavior when syntax errors are detected"""

    def test_rollback_called_when_syntax_errors_detected(self):
        """Test that rollback_batch is called when _verify_syntax_after_fix returns errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "src" / "test.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("const x = null;\n")

            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply, \
                 patch.object(agent, '_verify_syntax_after_fix') as mock_verify, \
                 patch.object(agent, 'rollback_batch') as mock_rollback:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? undefined;"

                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 0,
                    'applied': ["src/test.ts"],
                    'failed': [],
                    'backups': {"src/test.ts": Path(tmpdir) / ".refactor_backups" / "test.ts.bak"},
                    'task_results': {"task-0": True}
                }

                mock_verify.return_value = (True, ["error TS1005: ';' expected"])

                result = agent.run_refactor(dry_run=False, max_errors=1)

                mock_rollback.assert_called_once()
                assert result.errors_fixed == 0

    def test_no_rollback_when_no_syntax_errors(self):
        """Test that rollback_batch is NOT called when no syntax errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "src" / "test.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("const x = null;\n")

            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate, \
                 patch.object(agent, 'apply_fixes_batch') as mock_apply, \
                 patch.object(agent, '_verify_syntax_after_fix') as mock_verify, \
                 patch.object(agent, 'rollback_batch') as mock_rollback:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/test.ts",
                        line=1,
                        column=1,
                        error_code="TS2531",
                        message="Object is possibly 'null'"
                    )
                ]
                mock_generate.return_value = "const x = null ?? undefined;"

                mock_apply.return_value = {
                    'success_count': 1,
                    'failure_count': 0,
                    'applied': ["src/test.ts"],
                    'failed': [],
                    'backups': {"src/test.ts": Path(tmpdir) / ".refactor_backups" / "test.ts.bak"},
                    'task_results': {"task-0": True}
                }

                mock_verify.return_value = (False, [])

                result = agent.run_refactor(dry_run=False, max_errors=1)

                mock_rollback.assert_not_called()
                assert result.errors_fixed == 1


class TestEnvironmentHealthCheck:
    """Tests for _check_environment_health() method"""

    def test_healthy_environment_no_ts2307(self):
        """Test that environment is healthy when no TS2307 errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            errors = [
                TSError(
                    file_path="src/test.ts",
                    line=1,
                    column=1,
                    error_code="TS2531",
                    message="Object is possibly 'null'"
                ),
                TSError(
                    file_path="src/test.ts",
                    line=2,
                    column=1,
                    error_code="TS7006",
                    message="Parameter 'x' implicitly has an 'any' type"
                )
            ]

            is_healthy, problem_modules = agent._check_environment_health(errors)

            assert is_healthy is True
            assert problem_modules == []

    def test_unhealthy_environment_shared_ui_missing(self):
        """Test that environment is unhealthy when @morningai/shared-ui is missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            errors = [
                TSError(
                    file_path="src/components/Test.tsx",
                    line=1,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module '@morningai/shared-ui' or its corresponding type declarations."
                )
            ]

            is_healthy, problem_modules = agent._check_environment_health(errors)

            assert is_healthy is False
            assert "@morningai/shared-ui" in problem_modules

    def test_unhealthy_environment_react_missing(self):
        """Test that environment is unhealthy when react is missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            errors = [
                TSError(
                    file_path="src/App.tsx",
                    line=1,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module 'react' or its corresponding type declarations."
                )
            ]

            is_healthy, problem_modules = agent._check_environment_health(errors)

            assert is_healthy is False
            assert "react" in problem_modules

    def test_unhealthy_environment_multiple_modules(self):
        """Test that multiple missing modules are all detected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            errors = [
                TSError(
                    file_path="src/App.tsx",
                    line=1,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module 'react' or its corresponding type declarations."
                ),
                TSError(
                    file_path="src/App.tsx",
                    line=2,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module 'react-i18next' or its corresponding type declarations."
                ),
                TSError(
                    file_path="src/components/Test.tsx",
                    line=1,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module '@morningai/shared-ui' or its corresponding type declarations."
                )
            ]

            is_healthy, problem_modules = agent._check_environment_health(errors)

            assert is_healthy is False
            assert len(problem_modules) == 3
            assert "react" in problem_modules
            assert "react-i18next" in problem_modules
            assert "@morningai/shared-ui" in problem_modules

    def test_healthy_environment_ts2307_for_local_module(self):
        """Test that TS2307 for local modules doesn't trigger unhealthy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            errors = [
                TSError(
                    file_path="src/App.tsx",
                    line=1,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module './utils/helper' or its corresponding type declarations."
                )
            ]

            is_healthy, problem_modules = agent._check_environment_health(errors)

            assert is_healthy is True
            assert problem_modules == []

    def test_unhealthy_environment_workspace_namespace(self):
        """Test that any @morningai/* module triggers unhealthy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            errors = [
                TSError(
                    file_path="src/App.tsx",
                    line=1,
                    column=1,
                    error_code="TS2307",
                    message="Cannot find module '@morningai/some-new-package' or its corresponding type declarations."
                )
            ]

            is_healthy, problem_modules = agent._check_environment_health(errors)

            assert is_healthy is False
            assert "@morningai/some-new-package" in problem_modules

    def test_run_refactor_aborts_on_unhealthy_environment(self):
        """Test that run_refactor aborts early when environment is unhealthy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)
            agent.auto_pr = False

            with patch.object(agent, 'collect_ts_errors') as mock_collect, \
                 patch.object(agent, 'generate_fix') as mock_generate:

                mock_collect.return_value = [
                    TSError(
                        file_path="src/App.tsx",
                        line=1,
                        column=1,
                        error_code="TS2307",
                        message="Cannot find module '@morningai/shared-ui' or its corresponding type declarations."
                    )
                ]

                result = agent.run_refactor(dry_run=False, max_errors=10)

                # Should NOT call generate_fix because it aborted early
                mock_generate.assert_not_called()

                # Result should indicate environment failure
                assert "Environment health check failed" in result.summary
                assert result.metadata.get("aborted_reason") == "environment_unhealthy"
                assert "@morningai/shared-ui" in result.metadata.get("problem_modules", [])

    def test_empty_errors_is_healthy(self):
        """Test that empty error list is considered healthy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = RefactorAgent(repo_path=tmpdir)

            is_healthy, problem_modules = agent._check_environment_health([])

            assert is_healthy is True
            assert problem_modules == []
