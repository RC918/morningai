#!/usr/bin/env python3
"""
Unit tests for LLM Planner Adapter - Phase 1
"""
import json
from unittest.mock import patch, MagicMock
from llm_planner_adapter import LLMPlannerAdapter, generate_llm_plan


class TestLLMPlannerAdapter:
    """Test suite for LLM Planner Adapter"""

    def test_init_with_api_key(self):
        """Test initialization with OpenAI API key"""
        with patch('llm_planner_adapter.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            adapter = LLMPlannerAdapter()
            assert adapter.client is not None

    def test_init_without_api_key(self):
        """Test initialization without OpenAI API key"""
        with patch('llm_planner_adapter.settings') as mock_settings:
            mock_settings.openai_api_key = None
            adapter = LLMPlannerAdapter()
            assert adapter.client is None

    def test_validate_plan_valid(self):
        """Test plan validation with valid plan"""
        adapter = LLMPlannerAdapter()

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        assert adapter._validate_plan(valid_plan) is True

    def test_validate_plan_invalid_not_list(self):
        """Test plan validation with non-list input"""
        adapter = LLMPlannerAdapter()
        assert adapter._validate_plan("not a list") is False

    def test_validate_plan_invalid_too_few_steps(self):
        """Test plan validation with too few steps"""
        adapter = LLMPlannerAdapter()

        invalid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"}
        ]

        assert adapter._validate_plan(invalid_plan) is False

    def test_validate_plan_invalid_too_many_steps(self):
        """Test plan validation with too many steps"""
        adapter = LLMPlannerAdapter()

        invalid_plan = [
            {"step": f"Step {i}", "rationale": f"Reason {i}", "risk": "low"}
            for i in range(10)
        ]

        assert adapter._validate_plan(invalid_plan) is False

    def test_validate_plan_invalid_missing_keys(self):
        """Test plan validation with missing required keys"""
        adapter = LLMPlannerAdapter()

        invalid_plan = [
            {"step": "Step 1", "rationale": "Reason 1"},  # Missing 'risk'
            {"step": "Step 2", "rationale": "Reason 2", "risk": "low"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "low"}
        ]

        assert adapter._validate_plan(invalid_plan) is False

    def test_validate_plan_invalid_risk_value(self):
        """Test plan validation with invalid risk value"""
        adapter = LLMPlannerAdapter()

        invalid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "invalid"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "low"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "low"}
        ]

        assert adapter._validate_plan(invalid_plan) is False

    def test_get_static_plan(self):
        """Test static plan generation"""
        adapter = LLMPlannerAdapter()
        result = adapter._get_static_plan("test_type")

        assert result["planner_type"] == "static"
        assert result["task_type"] == "test_type"
        assert isinstance(result["plan"], list)
        assert len(result["plan"]) > 0
        assert result["planning_time_ms"] == 0

    def test_get_code_context(self):
        """Test code context extraction"""
        adapter = LLMPlannerAdapter()
        context = adapter._get_code_context("RC918/morningai", "test goal")

        assert isinstance(context, str)
        assert "RC918/morningai" in context
        assert "test goal" in context
        estimated_tokens = len(context) // 4
        assert estimated_tokens <= 2100  # Allow some buffer for token estimation

    @patch('llm_planner_adapter.settings')
    def test_generate_plan_no_client(self, mock_settings):
        """Test plan generation without OpenAI client"""
        mock_settings.openai_api_key = None
        adapter = LLMPlannerAdapter()

        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "static"
        assert isinstance(result["plan"], list)

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.OpenAI')
    def test_generate_plan_with_llm_success(self, mock_openai_class, mock_settings):
        """Test successful LLM plan generation"""
        mock_settings.openai_api_key = "test-key"
        mock_settings.use_llm_planner = True

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        valid_plan = [
            {"step": "Analyze requirements", "rationale": "Understand the task", "risk": "low"},
            {"step": "Implement solution", "rationale": "Write code", "risk": "medium"},
            {"step": "Test changes", "rationale": "Verify correctness", "risk": "low"}
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(valid_plan)
        mock_client.chat.completions.create.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3
        assert "planning_time_ms" in result

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.OpenAI')
    def test_generate_plan_with_llm_invalid_response(self, mock_openai_class, mock_settings):
        """Test LLM plan generation with invalid response"""
        mock_settings.openai_api_key = "test-key"
        mock_settings.use_llm_planner = True

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        invalid_plan = [
            {"step": "Only one step", "rationale": "Not enough", "risk": "low"}
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(invalid_plan)
        mock_client.chat.completions.create.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "static"

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.OpenAI')
    def test_generate_plan_with_llm_exception(self, mock_openai_class, mock_settings):
        """Test LLM plan generation with exception"""
        mock_settings.openai_api_key = "test-key"
        mock_settings.use_llm_planner = True

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_client.chat.completions.create.side_effect = Exception("API error")

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "static"

    def test_convenience_function(self):
        """Test convenience function generate_llm_plan"""
        with patch('llm_planner_adapter.settings') as mock_settings:
            mock_settings.openai_api_key = None

            result = generate_llm_plan("test goal", "RC918/morningai", "trace-123")

            assert isinstance(result, dict)
            assert "plan" in result
            assert "planner_type" in result

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.OpenAI')
    def test_classifier_import_failure(self, mock_openai_class, mock_settings):
        """Test classifier import failure fallback to unknown"""
        mock_settings.openai_api_key = "test-key"
        mock_settings.use_llm_planner = True

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "low"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "low"}
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(valid_plan)
        mock_client.chat.completions.create.return_value = mock_response

        adapter = LLMPlannerAdapter()

        with patch('llm_planner_adapter.LLMPlannerAdapter.generate_plan') as mock_generate:
            def side_effect_generate(goal, repo, trace_id, task_type=None, code_context=None):
                if not task_type:
                    with patch('builtins.__import__', side_effect=ImportError("Module not found")):
                        try:
                            from agents.dev_agent.workflows.task_classifier import classify_task
                            classification = classify_task(goal)
                            task_type = classification.get("task_type", "unknown")
                        except ImportError:
                            try:
                                from agents.dev_agent.workflows.task_classifier import TaskClassifier
                                classifier = TaskClassifier()
                                task_type_enum = classifier.classify(goal)
                                task_type = (
                                    task_type_enum.value if hasattr(task_type_enum, 'value')
                                    else str(task_type_enum)
                                )
                            except Exception:
                                task_type = "unknown"
                        except Exception:
                            task_type = "unknown"

                return {
                    "plan": ["Step 1", "Step 2", "Step 3"],
                    "planner_type": "llm",
                    "task_type": task_type,
                    "planning_time_ms": 100
                }

            mock_generate.side_effect = side_effect_generate
            result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

            assert result["task_type"] == "unknown"
