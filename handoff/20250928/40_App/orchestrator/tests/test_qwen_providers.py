"""
Unit tests for Qwen LLM Providers (AliCloud and SiliconFlow)

Tests:
- AliCloudProvider functionality
- SiliconFlowProvider functionality
- Provider initialization and configuration
- API call mocking and response handling

Reference:
- EPIC #2594: Qwen3 Provider Integration
- Ticket 1: Provider Adapters
"""
import pytest
from unittest.mock import patch, MagicMock

from llm.providers.alicloud_provider import AliCloudProvider
from llm.providers.siliconflow_provider import SiliconFlowProvider
from common.config.settings import settings

DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"


class TestAliCloudProvider:
    """Tests for AliCloudProvider"""

    def test_provider_name(self):
        """Test provider name is correct"""
        provider = AliCloudProvider()
        assert provider.provider_name == "alicloud"
        assert provider.get_provider_name() == "alicloud"

    def test_default_model(self):
        """Test default model is qwen-max"""
        provider = AliCloudProvider()
        assert provider.model == "qwen-max"

    def test_custom_model(self):
        """Test custom model initialization"""
        provider = AliCloudProvider(model="qwen-plus")
        assert provider.model == "qwen-plus"

    def test_supported_models(self):
        """Test supported models list"""
        assert "qwen-max" in AliCloudProvider.SUPPORTED_MODELS
        assert "qwen-plus" in AliCloudProvider.SUPPORTED_MODELS
        assert "qwen-turbo" in AliCloudProvider.SUPPORTED_MODELS

    def test_base_url(self):
        """Test DashScope base URL default is correct"""
        assert settings.dashscope_base_url == DASHSCOPE_BASE_URL

    @patch('llm.providers.alicloud_provider.settings')
    def test_is_available_with_key(self, mock_settings):
        """Test is_available returns True when API key is set"""
        mock_settings.dashscope_api_key = "test-key"
        provider = AliCloudProvider()
        assert provider.is_available() is True

    @patch('llm.providers.alicloud_provider.settings')
    def test_is_available_without_key(self, mock_settings):
        """Test is_available returns False when API key is not set"""
        mock_settings.dashscope_api_key = None
        provider = AliCloudProvider()
        assert provider.is_available() is False

    @patch('llm.providers.alicloud_provider.settings')
    def test_generate_raises_without_key(self, mock_settings):
        """Test generate raises ValueError when API key is not set"""
        mock_settings.dashscope_api_key = None
        provider = AliCloudProvider()
        with pytest.raises(ValueError, match="DashScope API key not configured"):
            provider.generate("Test prompt")

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_success(self, mock_openai_class, mock_settings):
        """Test successful generation"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = DASHSCOPE_BASE_URL

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        response = provider.generate("Test prompt")

        assert response.content == "Generated content"
        assert response.provider == "alicloud"
        assert response.model == "qwen-max"
        assert response.usage["total_tokens"] == 30

        mock_openai_class.assert_called_once_with(
            api_key="test-key",
            base_url=DASHSCOPE_BASE_URL
        )

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_system_prompt(self, mock_openai_class, mock_settings):
        """Test generation with system prompt"""
        mock_settings.dashscope_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        provider.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant"
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_json_mode(self, mock_openai_class, mock_settings):
        """Test generation with JSON mode"""
        mock_settings.dashscope_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        provider.generate("Test prompt", json_mode=True)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["response_format"] == {"type": "json_object"}

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_custom_model(self, mock_openai_class, mock_settings):
        """Test generation with custom model override"""
        mock_settings.dashscope_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        response = provider.generate("Test prompt", model="qwen-turbo")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "qwen-turbo"
        assert response.model == "qwen-turbo"

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_api_error(self, mock_openai_class, mock_settings):
        """Test API error handling"""
        mock_settings.dashscope_api_key = "test-key"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        with pytest.raises(Exception, match="API Error"):
            provider.generate("Test prompt")


class TestSiliconFlowProvider:
    """Tests for SiliconFlowProvider"""

    def test_provider_name(self):
        """Test provider name is correct"""
        provider = SiliconFlowProvider()
        assert provider.provider_name == "siliconflow"
        assert provider.get_provider_name() == "siliconflow"

    def test_default_model(self):
        """Test default model is Qwen/Qwen2.5-72B-Instruct"""
        provider = SiliconFlowProvider()
        assert provider.model == "Qwen/Qwen2.5-72B-Instruct"

    def test_custom_model(self):
        """Test custom model initialization"""
        provider = SiliconFlowProvider(model="Qwen/Qwen2.5-32B-Instruct")
        assert provider.model == "Qwen/Qwen2.5-32B-Instruct"

    def test_supported_models(self):
        """Test supported models list"""
        assert "Qwen/Qwen2.5-72B-Instruct" in SiliconFlowProvider.SUPPORTED_MODELS
        assert "Qwen/Qwen2.5-32B-Instruct" in SiliconFlowProvider.SUPPORTED_MODELS
        assert "Qwen/Qwen2.5-14B-Instruct" in SiliconFlowProvider.SUPPORTED_MODELS
        assert "Qwen/Qwen2.5-7B-Instruct" in SiliconFlowProvider.SUPPORTED_MODELS

    def test_base_url(self):
        """Test SiliconFlow base URL default is correct"""
        assert settings.siliconflow_base_url == SILICONFLOW_BASE_URL

    @patch('llm.providers.siliconflow_provider.settings')
    def test_is_available_with_key(self, mock_settings):
        """Test is_available returns True when API key is set"""
        mock_settings.siliconflow_api_key = "test-key"
        provider = SiliconFlowProvider()
        assert provider.is_available() is True

    @patch('llm.providers.siliconflow_provider.settings')
    def test_is_available_without_key(self, mock_settings):
        """Test is_available returns False when API key is not set"""
        mock_settings.siliconflow_api_key = None
        provider = SiliconFlowProvider()
        assert provider.is_available() is False

    @patch('llm.providers.siliconflow_provider.settings')
    def test_generate_raises_without_key(self, mock_settings):
        """Test generate raises ValueError when API key is not set"""
        mock_settings.siliconflow_api_key = None
        provider = SiliconFlowProvider()
        with pytest.raises(ValueError, match="SiliconFlow API key not configured"):
            provider.generate("Test prompt")

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_success(self, mock_openai_class, mock_settings):
        """Test successful generation"""
        mock_settings.siliconflow_api_key = "test-key"
        mock_settings.siliconflow_base_url = SILICONFLOW_BASE_URL

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        response = provider.generate("Test prompt")

        assert response.content == "Generated content"
        assert response.provider == "siliconflow"
        assert response.model == "Qwen/Qwen2.5-72B-Instruct"
        assert response.usage["total_tokens"] == 30

        mock_openai_class.assert_called_once_with(
            api_key="test-key",
            base_url=SILICONFLOW_BASE_URL
        )

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_system_prompt(self, mock_openai_class, mock_settings):
        """Test generation with system prompt"""
        mock_settings.siliconflow_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        provider.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant"
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_json_mode(self, mock_openai_class, mock_settings):
        """Test generation with JSON mode"""
        mock_settings.siliconflow_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        provider.generate("Test prompt", json_mode=True)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["response_format"] == {"type": "json_object"}

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_custom_model(self, mock_openai_class, mock_settings):
        """Test generation with custom model override"""
        mock_settings.siliconflow_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        response = provider.generate("Test prompt", model="Qwen/Qwen2.5-7B-Instruct")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "Qwen/Qwen2.5-7B-Instruct"
        assert response.model == "Qwen/Qwen2.5-7B-Instruct"

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_api_error(self, mock_openai_class, mock_settings):
        """Test API error handling"""
        mock_settings.siliconflow_api_key = "test-key"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        with pytest.raises(Exception, match="API Error"):
            provider.generate("Test prompt")


class TestProviderImports:
    """Tests for provider imports from __init__.py"""

    def test_alicloud_provider_import(self):
        """Test AliCloudProvider can be imported from providers package"""
        from llm.providers import AliCloudProvider
        assert AliCloudProvider is not None
        assert AliCloudProvider.provider_name == "alicloud"

    def test_siliconflow_provider_import(self):
        """Test SiliconFlowProvider can be imported from providers package"""
        from llm.providers import SiliconFlowProvider
        assert SiliconFlowProvider is not None
        assert SiliconFlowProvider.provider_name == "siliconflow"

    def test_all_exports(self):
        """Test __all__ includes new providers"""
        from llm.providers import __all__
        assert "AliCloudProvider" in __all__
        assert "SiliconFlowProvider" in __all__


class TestAliCloudProviderErrorHandling:
    """Tests for AliCloudProvider error handling scenarios

    Note: These tests use custom exception classes instead of openai exceptions
    to avoid issues with test isolation when openai module is globally mocked
    by other tests (e.g., test_observer_node.py uses sys.modules['openai']).
    """

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_timeout_error(self, mock_openai_class, mock_settings):
        """Test timeout error handling - provider should propagate exceptions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = DASHSCOPE_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = TimeoutError(
            "Request timed out"
        )
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        with pytest.raises(TimeoutError):
            provider.generate("Test prompt")

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_rate_limit_error(self, mock_openai_class, mock_settings):
        """Test rate limit error handling - provider should propagate exceptions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = DASHSCOPE_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Rate limit exceeded"
        )
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        with pytest.raises(Exception, match="Rate limit exceeded"):
            provider.generate("Test prompt")

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_authentication_error(self, mock_openai_class, mock_settings):
        """Test authentication error handling - provider should propagate exceptions"""
        mock_settings.dashscope_api_key = "invalid-key"
        mock_settings.dashscope_base_url = DASHSCOPE_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = PermissionError(
            "Invalid API key"
        )
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        with pytest.raises(PermissionError):
            provider.generate("Test prompt")

    @patch('llm.providers.alicloud_provider.settings')
    @patch('openai.OpenAI')
    def test_api_connection_error(self, mock_openai_class, mock_settings):
        """Test API connection error handling - provider should propagate exceptions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = DASHSCOPE_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ConnectionError(
            "Failed to connect to API"
        )
        mock_openai_class.return_value = mock_client

        provider = AliCloudProvider()
        with pytest.raises(ConnectionError):
            provider.generate("Test prompt")

    def test_error_message_includes_env_var_hint(self):
        """Test that error message includes environment variable hint"""
        provider = AliCloudProvider()
        with pytest.raises(ValueError) as exc_info:
            provider.generate("Test prompt")
        assert "DASHSCOPE_API_KEY" in str(exc_info.value)


class TestSiliconFlowProviderErrorHandling:
    """Tests for SiliconFlowProvider error handling scenarios

    Note: These tests use custom exception classes instead of openai exceptions
    to avoid issues with test isolation when openai module is globally mocked
    by other tests (e.g., test_observer_node.py uses sys.modules['openai']).
    """

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_timeout_error(self, mock_openai_class, mock_settings):
        """Test timeout error handling - provider should propagate exceptions"""
        mock_settings.siliconflow_api_key = "test-key"
        mock_settings.siliconflow_base_url = SILICONFLOW_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = TimeoutError(
            "Request timed out"
        )
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        with pytest.raises(TimeoutError):
            provider.generate("Test prompt")

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_rate_limit_error(self, mock_openai_class, mock_settings):
        """Test rate limit error handling - provider should propagate exceptions"""
        mock_settings.siliconflow_api_key = "test-key"
        mock_settings.siliconflow_base_url = SILICONFLOW_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Rate limit exceeded"
        )
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        with pytest.raises(Exception, match="Rate limit exceeded"):
            provider.generate("Test prompt")

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_authentication_error(self, mock_openai_class, mock_settings):
        """Test authentication error handling - provider should propagate exceptions"""
        mock_settings.siliconflow_api_key = "invalid-key"
        mock_settings.siliconflow_base_url = SILICONFLOW_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = PermissionError(
            "Invalid API key"
        )
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        with pytest.raises(PermissionError):
            provider.generate("Test prompt")

    @patch('llm.providers.siliconflow_provider.settings')
    @patch('openai.OpenAI')
    def test_api_connection_error(self, mock_openai_class, mock_settings):
        """Test API connection error handling - provider should propagate exceptions"""
        mock_settings.siliconflow_api_key = "test-key"
        mock_settings.siliconflow_base_url = SILICONFLOW_BASE_URL

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ConnectionError(
            "Failed to connect to API"
        )
        mock_openai_class.return_value = mock_client

        provider = SiliconFlowProvider()
        with pytest.raises(ConnectionError):
            provider.generate("Test prompt")

    def test_error_message_includes_env_var_hint(self):
        """Test that error message includes environment variable hint"""
        provider = SiliconFlowProvider()
        with pytest.raises(ValueError) as exc_info:
            provider.generate("Test prompt")
        assert "SILICONFLOW_API_KEY" in str(exc_info.value)
