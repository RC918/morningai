"""
Unit tests for LLMClient abstraction layer

Tests:
- LLMClient initialization with different providers
- Provider auto-selection
- OpenAIProvider functionality
- GeminiProvider functionality (stub)
- LLMResponse dataclass
- Provider governance allowlist (ROUTING_ALLOWED_PROVIDERS)
"""
import pytest
from unittest.mock import patch, MagicMock

from llm.client import LLMClient, _get_available_providers
from llm.providers.base import LLMResponse
from llm.providers.openai_provider import OpenAIProvider
from llm.providers.gemini_provider import GeminiProvider


class TestLLMResponse:
    """Tests for LLMResponse dataclass"""

    def test_llm_response_creation(self):
        """Test basic LLMResponse creation"""
        response = LLMResponse(
            content="Test content",
            model="gpt-4",
            provider="openai"
        )
        assert response.content == "Test content"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.usage == {}
        assert response.raw_response is None

    def test_llm_response_with_usage(self):
        """Test LLMResponse with usage statistics"""
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
        response = LLMResponse(
            content="Test content",
            model="gpt-4",
            provider="openai",
            usage=usage
        )
        assert response.usage == usage
        assert response.usage["total_tokens"] == 150


class TestOpenAIProvider:
    """Tests for OpenAIProvider"""

    def test_provider_name(self):
        """Test provider name is correct"""
        provider = OpenAIProvider()
        assert provider.provider_name == "openai"
        assert provider.get_provider_name() == "openai"

    def test_default_model(self):
        """Test default model is gpt-4-turbo-preview"""
        provider = OpenAIProvider()
        assert provider.model == "gpt-4-turbo-preview"

    def test_custom_model(self):
        """Test custom model initialization"""
        provider = OpenAIProvider(model="gpt-4")
        assert provider.model == "gpt-4"

    @patch('llm.providers.openai_provider.settings')
    def test_is_available_with_key(self, mock_settings):
        """Test is_available returns True when API key is set"""
        mock_settings.openai_api_key = "test-key"
        provider = OpenAIProvider()
        assert provider.is_available() is True

    @patch('llm.providers.openai_provider.settings')
    def test_is_available_without_key(self, mock_settings):
        """Test is_available returns False when API key is not set"""
        mock_settings.openai_api_key = None
        provider = OpenAIProvider()
        assert provider.is_available() is False

    @patch('llm.providers.openai_provider.settings')
    def test_generate_raises_without_key(self, mock_settings):
        """Test generate raises ValueError when API key is not set"""
        mock_settings.openai_api_key = None
        provider = OpenAIProvider()
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            provider.generate("Test prompt")

    @patch('llm.providers.openai_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_success(self, mock_openai_class, mock_settings):
        """Test successful generation"""
        mock_settings.openai_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider()
        response = provider.generate("Test prompt")

        assert response.content == "Generated content"
        assert response.provider == "openai"
        assert response.usage["total_tokens"] == 30

    @patch('llm.providers.openai_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_system_prompt(self, mock_openai_class, mock_settings):
        """Test generation with system prompt"""
        mock_settings.openai_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider()
        provider.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant"
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch('llm.providers.openai_provider.settings')
    @patch('openai.OpenAI')
    def test_generate_with_json_mode(self, mock_openai_class, mock_settings):
        """Test generation with JSON mode"""
        mock_settings.openai_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider()
        provider.generate("Test prompt", json_mode=True)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["response_format"] == {"type": "json_object"}


class TestGeminiProvider:
    """Tests for GeminiProvider"""

    def test_provider_name(self):
        """Test provider name is correct"""
        provider = GeminiProvider()
        assert provider.provider_name == "gemini"
        assert provider.get_provider_name() == "gemini"

    def test_default_model(self):
        """Test default model is gemini-2.0-flash"""
        provider = GeminiProvider()
        assert provider.model == "gemini-2.0-flash"

    def test_custom_model(self):
        """Test custom model initialization"""
        provider = GeminiProvider(model="gemini-pro-vision")
        assert provider.model == "gemini-pro-vision"

    @patch('llm.providers.gemini_provider.settings')
    def test_is_available_without_key(self, mock_settings):
        """Test is_available returns False when API key is not set"""
        mock_settings.gemini_api_key = None
        provider = GeminiProvider()
        assert provider.is_available() is False

    @patch('llm.providers.gemini_provider.settings')
    def test_generate_raises_without_key(self, mock_settings):
        """Test generate raises ValueError when API key is not set"""
        mock_settings.gemini_api_key = None
        provider = GeminiProvider()
        with pytest.raises((ValueError, NotImplementedError)):
            provider.generate("Test prompt")


class TestLLMClient:
    """Tests for LLMClient"""

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_default_provider_is_openai(self, mock_openai_provider, mock_settings):
        """Test default provider is OpenAI"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient()
        assert client.provider_name == "openai"

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_explicit_openai_provider(self, mock_openai_provider, mock_settings):
        """Test explicit OpenAI provider selection"""
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient(provider="openai")
        assert client.provider_name == "openai"

    @patch('llm.client.settings')
    @patch('llm.client.GeminiProvider')
    def test_explicit_gemini_provider(self, mock_gemini_provider, mock_settings):
        """Test explicit Gemini provider selection"""
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gemini-pro"
        mock_gemini_provider.return_value = mock_provider_instance

        client = LLMClient(provider="gemini")
        assert client.provider_name == "gemini"

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_env_provider_setting(self, mock_openai_provider, mock_settings):
        """Test provider from environment variable"""
        mock_settings.llm_provider = "openai"
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient()
        assert client.provider_name == "openai"

    @patch('llm.client._get_available_providers')
    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_auto_select_openai(
        self, mock_openai_provider, mock_settings, mock_get_available
    ):
        """Test auto provider selection chooses OpenAI when available"""
        mock_settings.llm_provider = None
        mock_get_available.return_value = ["openai"]
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient(provider="auto")
        assert client.provider_name == "openai"

    @patch('llm.client._get_available_providers')
    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    @patch('llm.client.GeminiProvider')
    def test_auto_select_gemini_fallback(
        self, mock_gemini_provider, mock_openai_provider, mock_settings,
        mock_get_available
    ):
        """Test auto provider selection falls back to Gemini"""
        mock_settings.llm_provider = None
        mock_get_available.return_value = ["gemini"]

        mock_openai_instance = MagicMock()
        mock_openai_instance.is_available.return_value = False
        mock_openai_provider.return_value = mock_openai_instance

        mock_gemini_instance = MagicMock()
        mock_gemini_instance.is_available.return_value = True
        mock_gemini_instance.model = "gemini-pro"
        mock_gemini_provider.return_value = mock_gemini_instance

        client = LLMClient(provider="auto")
        assert client.provider_name == "gemini"

    @patch('llm.client._get_available_providers')
    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    @patch('llm.client.GeminiProvider')
    def test_auto_select_raises_when_none_available(
        self, mock_gemini_provider, mock_openai_provider, mock_settings,
        mock_get_available
    ):
        """Test auto provider selection raises when no provider available"""
        mock_settings.llm_provider = None
        mock_get_available.return_value = []

        mock_openai_instance = MagicMock()
        mock_openai_instance.is_available.return_value = False
        mock_openai_provider.return_value = mock_openai_instance

        mock_gemini_instance = MagicMock()
        mock_gemini_instance.is_available.return_value = False
        mock_gemini_provider.return_value = mock_gemini_instance

        with pytest.raises(ValueError, match="No LLM provider available"):
            LLMClient(provider="auto")

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_generate_delegates_to_provider(self, mock_openai_provider, mock_settings):
        """Test generate method delegates to provider"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_provider_instance.generate.return_value = LLMResponse(
            content="Generated",
            model="gpt-4-turbo-preview",
            provider="openai"
        )
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient()
        response = client.generate("Test prompt")

        mock_provider_instance.generate.assert_called_once()
        assert response.content == "Generated"

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_is_available(self, mock_openai_provider, mock_settings):
        """Test is_available method"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient()
        assert client.is_available() is True

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_model_property(self, mock_openai_provider, mock_settings):
        """Test model property"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        client = LLMClient()
        assert client.model == "gpt-4-turbo-preview"

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_custom_model(self, mock_openai_provider, mock_settings):
        """Test custom model initialization"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4"
        mock_openai_provider.return_value = mock_provider_instance

        _client = LLMClient(model="gpt-4")
        mock_openai_provider.assert_called_with(model="gpt-4")
        assert _client is not None

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_get_default_client(self, mock_openai_provider, mock_settings):
        """Test get_default_client singleton"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        LLMClient.reset_default_client()

        client1 = LLMClient.get_default_client()
        client2 = LLMClient.get_default_client()
        assert client1 is client2

        LLMClient.reset_default_client()

    @patch('llm.client.settings')
    @patch('llm.client.OpenAIProvider')
    def test_reset_default_client(self, mock_openai_provider, mock_settings):
        """Test reset_default_client"""
        mock_settings.llm_provider = None
        mock_provider_instance = MagicMock()
        mock_provider_instance.is_available.return_value = True
        mock_provider_instance.model = "gpt-4-turbo-preview"
        mock_openai_provider.return_value = mock_provider_instance

        LLMClient.reset_default_client()

        client1 = LLMClient.get_default_client()
        LLMClient.reset_default_client()
        client2 = LLMClient.get_default_client()
        assert client1 is not client2

        LLMClient.reset_default_client()


class TestProviderGovernanceAllowlist:
    """Tests for ROUTING_ALLOWED_PROVIDERS governance control.

    Blueprint Alignment: Model Governance Framework v2 - policy-driven routing
    """

    def _create_mock_provider(self, is_available: bool):
        """Helper to create a mock provider class"""
        mock_class = MagicMock()
        mock_class.return_value.is_available.return_value = is_available
        return mock_class

    def test_no_allowlist_returns_all_available(self):
        """Test that empty allowlist returns all providers with valid API keys"""
        mock_registry = [
            ("openai", self._create_mock_provider(True)),
            ("gemini", self._create_mock_provider(True)),
            ("alicloud", self._create_mock_provider(False)),
            ("siliconflow", self._create_mock_provider(False)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = ""
                available = _get_available_providers()
                assert "openai" in available
                assert "gemini" in available
                assert "alicloud" not in available
                assert "siliconflow" not in available

    def test_allowlist_filters_to_allowed_only(self):
        """Test that allowlist filters providers to only allowed ones"""
        mock_registry = [
            ("openai", self._create_mock_provider(True)),
            ("gemini", self._create_mock_provider(True)),
            ("alicloud", self._create_mock_provider(True)),
            ("siliconflow", self._create_mock_provider(True)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = "alicloud"
                available = _get_available_providers()
                assert available == ["alicloud"]

    def test_allowlist_multiple_providers(self):
        """Test allowlist with multiple providers"""
        mock_registry = [
            ("openai", self._create_mock_provider(True)),
            ("gemini", self._create_mock_provider(True)),
            ("alicloud", self._create_mock_provider(True)),
            ("siliconflow", self._create_mock_provider(False)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = "alicloud,openai"
                available = _get_available_providers()
                assert "alicloud" in available
                assert "openai" in available
                assert "gemini" not in available
                assert "siliconflow" not in available

    def test_allowlist_requires_api_key(self):
        """Test that allowlist still requires valid API key"""
        mock_registry = [
            ("openai", self._create_mock_provider(True)),
            ("gemini", self._create_mock_provider(False)),
            ("alicloud", self._create_mock_provider(False)),
            ("siliconflow", self._create_mock_provider(False)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = "alicloud,gemini"
                available = _get_available_providers()
                assert available == []

    def test_allowlist_case_insensitive(self):
        """Test that allowlist matching is case-insensitive"""
        mock_registry = [
            ("openai", self._create_mock_provider(True)),
            ("gemini", self._create_mock_provider(False)),
            ("alicloud", self._create_mock_provider(True)),
            ("siliconflow", self._create_mock_provider(False)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = "AliCloud,OPENAI"
                available = _get_available_providers()
                assert "alicloud" in available
                assert "openai" in available

    def test_allowlist_with_whitespace(self):
        """Test that allowlist handles whitespace correctly"""
        mock_registry = [
            ("openai", self._create_mock_provider(True)),
            ("gemini", self._create_mock_provider(False)),
            ("alicloud", self._create_mock_provider(True)),
            ("siliconflow", self._create_mock_provider(False)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = " alicloud , openai "
                available = _get_available_providers()
                assert "alicloud" in available
                assert "openai" in available

    def test_allowlist_blocks_siliconflow_when_only_alicloud_allowed(self):
        """Test governance: SiliconFlow blocked even with API key when only AliCloud allowed.

        This is the key governance scenario: user wants to lock down to AliCloud only,
        even if SiliconFlow API key is accidentally configured.
        """
        mock_registry = [
            ("openai", self._create_mock_provider(False)),
            ("gemini", self._create_mock_provider(False)),
            ("alicloud", self._create_mock_provider(True)),
            ("siliconflow", self._create_mock_provider(True)),
        ]

        with patch('llm.client._PROVIDER_REGISTRY', mock_registry):
            with patch('llm.client.settings') as mock_settings:
                mock_settings.routing_allowed_providers = "alicloud"
                available = _get_available_providers()
                assert available == ["alicloud"]
                assert "siliconflow" not in available
