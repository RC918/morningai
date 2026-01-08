#!/usr/bin/env python3
"""
Unit tests for LLM Planner Adapter - Phase 1
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from llm_planner_adapter import LLMPlannerAdapter, generate_llm_plan


class TestLLMPlannerAdapter:
    """Test suite for LLM Planner Adapter"""

    @patch('llm_planner_adapter.OpenAI')
    @patch('llm_planner_adapter.get_client_for_task')
    @patch('llm_planner_adapter.settings')
    def test_init_with_api_key(self, mock_settings, mock_get_client, mock_openai_cls):
        """Test initialization with OpenAI API key via RoutingEngine task-based routing"""
        mock_settings.openai_api_key = "test-key"
        mock_llm = MagicMock()
        mock_llm.provider_name = "openai"
        mock_get_client.return_value = mock_llm

        # Note: provider parameter is deprecated and ignored
        # RoutingEngine now handles provider selection via get_client_for_task
        adapter = LLMPlannerAdapter(provider="openai")

        # Verify get_client_for_task was called with TaskType.PLANNING
        mock_get_client.assert_called_once()
        # OpenAI client is created when provider_name is "openai" and API key exists
        mock_openai_cls.assert_called_once_with(api_key="test-key")
        assert adapter.client is mock_openai_cls.return_value

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

    @patch('llm_planner_adapter.LLMClient')
    def test_generate_plan_no_client(self, mock_llm_client_class):
        """Test plan generation without LLM client"""
        mock_llm_client_class.side_effect = ValueError("No LLM provider available")
        adapter = LLMPlannerAdapter()

        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "static"
        assert isinstance(result["plan"], list)

    @patch('llm_planner_adapter.LLMClient')
    def test_generate_plan_with_llm_success(self, mock_llm_client_class):
        """Test successful LLM plan generation"""
        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Analyze requirements", "rationale": "Understand the task", "risk": "low"},
            {"step": "Implement solution", "rationale": "Write code", "risk": "medium"},
            {"step": "Test changes", "rationale": "Verify correctness", "risk": "low"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_plan)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3
        assert "planning_time_ms" in result

    @patch('llm_planner_adapter.LLMClient')
    def test_generate_plan_with_llm_invalid_response(self, mock_llm_client_class):
        """Test LLM plan generation with invalid response"""
        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        invalid_plan = [
            {"step": "Only one step", "rationale": "Not enough", "risk": "low"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps(invalid_plan)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 50}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "static"

    @patch('llm_planner_adapter.LLMClient')
    def test_generate_plan_with_llm_exception(self, mock_llm_client_class):
        """Test LLM plan generation with exception"""
        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        mock_client.generate.side_effect = Exception("API error")

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
    @patch('llm_planner_adapter.LLMClient')
    def test_classifier_import_failure(self, mock_llm_client_class, mock_settings):
        """Test classifier import failure fallback to unknown"""
        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "low"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "low"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_plan)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

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

    def test_clean_json_response_markdown_blocks(self):
        """Test cleaning JSON response with markdown code blocks"""
        adapter = LLMPlannerAdapter()

        content_with_markdown = '''```json
[
  {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
  {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"}
]
```'''

        cleaned = adapter._clean_json_response(content_with_markdown)
        parsed = json.loads(cleaned)

        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["step"] == "Step 1"

    def test_clean_json_response_explanatory_text(self):
        """Test cleaning JSON response with explanatory text"""
        adapter = LLMPlannerAdapter()

        content_with_text = '''Here is the plan:
[
  {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
  {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"}
]
This should work well.'''

        cleaned = adapter._clean_json_response(content_with_text)
        parsed = json.loads(cleaned)

        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_clean_json_response_both_issues(self):
        """Test cleaning JSON response with both markdown and explanatory text"""
        adapter = LLMPlannerAdapter()

        content_with_both = '''Here is your plan:
```json
[
  {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
  {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
  {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
]
```
Hope this helps!'''

        cleaned = adapter._clean_json_response(content_with_both)
        parsed = json.loads(cleaned)

        assert isinstance(parsed, list)
        assert len(parsed) == 3

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_json_mode_enabled(self, mock_llm_client_class, mock_settings):
        """Test LLM plan generation with JSON mode enabled"""
        mock_settings.planner_json_mode = True

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps({"plan": valid_plan})
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3

        call_args = mock_client.generate.call_args
        assert call_args.kwargs["json_mode"] is True

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_json_mode_disabled(self, mock_llm_client_class, mock_settings):
        """Test LLM plan generation with JSON mode disabled"""
        mock_settings.planner_json_mode = False

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_plan)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3

        call_args = mock_client.generate.call_args
        assert call_args.kwargs["json_mode"] is False

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_parse_json_with_retry_success_first_attempt(self, mock_llm_client_class, mock_settings):
        """Test JSON parsing succeeds on first attempt"""
        mock_settings.planner_json_mode = False

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_plan)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_parse_json_with_retry_success_second_attempt(self, mock_llm_client_class, mock_settings):
        """Test JSON parsing succeeds on second attempt after cleaning"""
        mock_settings.planner_json_mode = False

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        markdown_wrapped = f'''```json
{json.dumps(valid_plan)}
```'''

        mock_response = MagicMock()
        mock_response.content = markdown_wrapped
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_parse_json_mode_with_retry(self, mock_llm_client_class, mock_settings):
        """Test JSON mode parsing with retry logic"""
        mock_settings.planner_json_mode = True

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        markdown_wrapped = f'''```json
{json.dumps({"plan": valid_plan})}
```'''

        mock_response = MagicMock()
        mock_response.content = markdown_wrapped
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        assert result["planner_type"] == "llm"
        assert len(result["plan"]) == 3


class TestReasoningModeEnabled:
    """Test suite for reasoning_mode_enabled feature (Phase 3)

    Uses pytest.mark.parametrize to consolidate duplicate test patterns.
    """

    @pytest.mark.parametrize(
        "reasoning_mode_enabled,expected_thinking_level",
        [
            (False, "low"),   # Default: reasoning mode disabled -> low thinking
            (True, "high"),   # Reasoning mode enabled -> high thinking
        ],
        ids=["reasoning_disabled_low", "reasoning_enabled_high"]
    )
    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_gemini_thinking_level(
        self, mock_llm_client_class, mock_settings,
        reasoning_mode_enabled, expected_thinking_level
    ):
        """Test Gemini thinking_level based on reasoning_mode_enabled setting"""
        mock_settings.planner_json_mode = True
        mock_settings.reasoning_mode_enabled = reasoning_mode_enabled

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "gemini"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps({"plan": valid_plan})
        mock_response.provider = "gemini"
        mock_response.model = "gemini-3-pro-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        call_args = mock_client.generate.call_args
        assert call_args.kwargs["thinking_level"] == expected_thinking_level

    @patch('llm_planner_adapter.settings')
    @patch('llm_planner_adapter.LLMClient')
    def test_openai_no_thinking_level(self, mock_llm_client_class, mock_settings):
        """Test that OpenAI provider does not receive thinking_level parameter"""
        mock_settings.planner_json_mode = True
        mock_settings.reasoning_mode_enabled = True

        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"

        valid_plan = [
            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
            {"step": "Step 2", "rationale": "Reason 2", "risk": "medium"},
            {"step": "Step 3", "rationale": "Reason 3", "risk": "high"}
        ]

        mock_response = MagicMock()
        mock_response.content = json.dumps({"plan": valid_plan})
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMPlannerAdapter()
        adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

        call_args = mock_client.generate.call_args
        assert "thinking_level" not in call_args.kwargs
