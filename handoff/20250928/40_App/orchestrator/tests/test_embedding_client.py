"""
Unit tests for EmbeddingClient abstraction layer

Tests:
- EmbeddingClient initialization with different providers
- Provider auto-selection (alicloud > openai)
- AliCloud embedding dimensions (1536 for DB compatibility)
- Cache behavior with resolved providers
- get_embedding_client factory function
"""
from unittest.mock import patch, MagicMock

from llm.embedding_client import (
    EmbeddingClient,
    get_embedding_client,
    _resolve_provider,
    _get_default_model,
    _get_cached_client,
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_DIMENSIONS_OPENAI,
    DEFAULT_EMBEDDING_DIMENSIONS_ALICLOUD,
)


class TestResolveProvider:
    """Tests for _resolve_provider function"""

    @patch('llm.embedding_client.settings')
    def test_resolve_alicloud_when_dashscope_key_present(self, mock_settings):
        """Test auto-selection chooses alicloud when DASHSCOPE_API_KEY is set"""
        mock_settings.dashscope_api_key = "test-dashscope-key"
        mock_settings.openai_api_key = "test-openai-key"

        result = _resolve_provider("auto")
        assert result == "alicloud"

    @patch('llm.embedding_client.settings')
    def test_resolve_openai_when_only_openai_key_present(self, mock_settings):
        """Test auto-selection chooses openai when only OPENAI_API_KEY is set"""
        mock_settings.dashscope_api_key = None
        mock_settings.openai_api_key = "test-openai-key"

        result = _resolve_provider("auto")
        assert result == "openai"

    @patch('llm.embedding_client.settings')
    def test_resolve_defaults_to_openai_when_no_keys(self, mock_settings):
        """Test auto-selection defaults to openai when no API keys are set"""
        mock_settings.dashscope_api_key = None
        mock_settings.openai_api_key = None

        result = _resolve_provider("auto")
        assert result == "openai"

    def test_resolve_explicit_alicloud(self):
        """Test explicit alicloud provider selection"""
        result = _resolve_provider("alicloud")
        assert result == "alicloud"

    def test_resolve_explicit_openai(self):
        """Test explicit openai provider selection"""
        result = _resolve_provider("openai")
        assert result == "openai"


class TestGetDefaultModel:
    """Tests for _get_default_model function"""

    def test_alicloud_default_model(self):
        """Test default model for alicloud is text-embedding-v3"""
        result = _get_default_model("alicloud")
        assert result == "text-embedding-v3"

    def test_openai_default_model(self):
        """Test default model for openai is text-embedding-3-small"""
        result = _get_default_model("openai")
        assert result == "text-embedding-3-small"


class TestEmbeddingClient:
    """Tests for EmbeddingClient class"""

    @patch('llm.embedding_client.settings')
    def test_init_with_explicit_alicloud_provider(self, mock_settings):
        """Test initialization with explicit alicloud provider auto-selects 1024 dimensions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client = EmbeddingClient(provider="alicloud")
        assert client.provider_name == "alicloud"
        assert client.model == "text-embedding-v3"
        assert client.dimensions == DEFAULT_EMBEDDING_DIMENSIONS_ALICLOUD  # 1024

    @patch('llm.embedding_client.settings')
    def test_init_with_explicit_openai_provider(self, mock_settings):
        """Test initialization with explicit openai provider auto-selects 1536 dimensions"""
        mock_settings.openai_api_key = "test-key"

        client = EmbeddingClient(provider="openai")
        assert client.provider_name == "openai"
        assert client.model == "text-embedding-3-small"
        assert client.dimensions == DEFAULT_EMBEDDING_DIMENSIONS_OPENAI  # 1536

    @patch('llm.embedding_client.settings')
    def test_init_with_auto_selects_alicloud(self, mock_settings):
        """Test auto provider selection chooses alicloud when available"""
        mock_settings.dashscope_api_key = "test-dashscope-key"
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client = EmbeddingClient(provider="auto")
        assert client.provider_name == "alicloud"

    @patch('llm.embedding_client.settings')
    def test_init_with_custom_dimensions(self, mock_settings):
        """Test initialization with custom dimensions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client = EmbeddingClient(provider="alicloud", dimensions=512)
        assert client.dimensions == 512

    @patch('llm.embedding_client.settings')
    def test_provider_specific_default_dimensions(self, mock_settings):
        """Test provider-specific default dimensions are auto-selected"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        mock_settings.openai_api_key = "test-key"

        # AliCloud defaults to 1024
        alicloud_client = EmbeddingClient(provider="alicloud")
        assert alicloud_client.dimensions == DEFAULT_EMBEDDING_DIMENSIONS_ALICLOUD  # 1024

        # OpenAI defaults to 1536
        openai_client = EmbeddingClient(provider="openai")
        assert openai_client.dimensions == DEFAULT_EMBEDDING_DIMENSIONS_OPENAI  # 1536

        # Legacy constant still exists for backward compatibility
        assert DEFAULT_EMBEDDING_DIMENSIONS == 1536

    @patch('llm.embedding_client.settings')
    def test_is_available_alicloud_with_key(self, mock_settings):
        """Test is_available returns True for alicloud when key is set"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client = EmbeddingClient(provider="alicloud")
        assert client.is_available() is True

    @patch('llm.embedding_client.settings')
    def test_is_available_alicloud_without_key(self, mock_settings):
        """Test is_available returns False for alicloud when key is not set"""
        mock_settings.dashscope_api_key = None
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client = EmbeddingClient(provider="alicloud")
        assert client.is_available() is False

    @patch('llm.embedding_client.settings')
    def test_is_available_openai_with_key(self, mock_settings):
        """Test is_available returns True for openai when key is set"""
        mock_settings.openai_api_key = "test-key"

        client = EmbeddingClient(provider="openai")
        assert client.is_available() is True

    @patch('llm.embedding_client.settings')
    def test_is_available_openai_without_key(self, mock_settings):
        """Test is_available returns False for openai when key is not set"""
        mock_settings.openai_api_key = None

        client = EmbeddingClient(provider="openai")
        assert client.is_available() is False


class TestEmbeddingClientEmbed:
    """Tests for EmbeddingClient.embed method"""

    @patch('openai.OpenAI')
    @patch('llm.embedding_client.settings')
    def test_embed_alicloud_with_dimensions(self, mock_settings, mock_openai_class):
        """Test embed with alicloud includes dimensions parameter (default 1024)"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 1024
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]

        mock_openai_client = MagicMock()
        mock_openai_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai_client

        client = EmbeddingClient(provider="alicloud")
        result = client.embed("test text")

        assert result is not None
        assert len(result) == 1024
        mock_openai_client.embeddings.create.assert_called_once()
        call_kwargs = mock_openai_client.embeddings.create.call_args.kwargs
        assert call_kwargs["dimensions"] == DEFAULT_EMBEDDING_DIMENSIONS_ALICLOUD  # 1024

    @patch('openai.OpenAI')
    @patch('llm.embedding_client.settings')
    def test_embed_openai_with_dimensions(self, mock_settings, mock_openai_class):
        """Test embed with openai includes dimensions parameter (default 1536)"""
        mock_settings.openai_api_key = "test-key"

        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]

        mock_openai_client = MagicMock()
        mock_openai_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai_client

        client = EmbeddingClient(provider="openai")
        result = client.embed("test text")

        assert result is not None
        assert len(result) == 1536
        mock_openai_client.embeddings.create.assert_called_once()
        call_kwargs = mock_openai_client.embeddings.create.call_args.kwargs
        assert call_kwargs["dimensions"] == DEFAULT_EMBEDDING_DIMENSIONS_OPENAI  # 1536

    @patch('llm.embedding_client.settings')
    def test_embed_returns_none_when_not_available(self, mock_settings):
        """Test embed returns None when API key not available"""
        mock_settings.dashscope_api_key = None
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client = EmbeddingClient(provider="alicloud")
        result = client.embed("test text")

        assert result is None


class TestGetEmbeddingClient:
    """Tests for get_embedding_client factory function"""

    @patch('llm.embedding_client._get_cached_client')
    @patch('llm.embedding_client._resolve_provider')
    @patch('llm.embedding_client._get_default_model')
    @patch('llm.embedding_client._get_default_dimensions')
    def test_resolves_provider_before_caching(
        self, mock_get_dimensions, mock_get_model, mock_resolve, mock_cached
    ):
        """Test that provider is resolved before calling cached client factory"""
        mock_resolve.return_value = "alicloud"
        mock_get_model.return_value = "text-embedding-v3"
        mock_get_dimensions.return_value = 1024
        mock_cached.return_value = MagicMock()

        get_embedding_client(provider="auto")

        mock_resolve.assert_called_once_with("auto")
        mock_get_dimensions.assert_called_once_with("alicloud")
        mock_cached.assert_called_once_with("alicloud", "text-embedding-v3", 1024)

    @patch('llm.embedding_client._get_cached_client')
    @patch('llm.embedding_client._resolve_provider')
    @patch('llm.embedding_client._get_default_model')
    def test_passes_custom_dimensions_to_cache(
        self, mock_get_model, mock_resolve, mock_cached
    ):
        """Test that custom dimensions are passed to cached client factory"""
        mock_resolve.return_value = "alicloud"
        mock_get_model.return_value = "text-embedding-v3"
        mock_cached.return_value = MagicMock()

        get_embedding_client(provider="auto", dimensions=512)

        mock_cached.assert_called_once_with("alicloud", "text-embedding-v3", 512)

    @patch('llm.embedding_client._get_cached_client')
    @patch('llm.embedding_client._resolve_provider')
    @patch('llm.embedding_client._get_default_dimensions')
    def test_uses_provided_model(self, mock_get_dimensions, mock_resolve, mock_cached):
        """Test that provided model is used instead of default"""
        mock_resolve.return_value = "alicloud"
        mock_get_dimensions.return_value = 1024
        mock_cached.return_value = MagicMock()

        get_embedding_client(model="custom-model", provider="auto")

        mock_cached.assert_called_once_with("alicloud", "custom-model", 1024)


class TestCacheCorrectness:
    """Tests for cache correctness with dynamic provider changes"""

    @patch('llm.embedding_client.settings')
    def test_cache_keyed_on_resolved_provider(self, mock_settings):
        """Test that cache is keyed on resolved provider, not 'auto'"""
        _get_cached_client.cache_clear()

        mock_settings.dashscope_api_key = "test-dashscope-key"
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client1 = get_embedding_client(provider="auto")
        assert client1.provider_name == "alicloud"

        mock_settings.dashscope_api_key = None

        client2 = get_embedding_client(provider="auto")
        assert client2.provider_name == "openai"

        assert client1 is not client2

        _get_cached_client.cache_clear()

    @patch('llm.embedding_client.settings')
    def test_same_resolved_provider_returns_cached_instance(self, mock_settings):
        """Test that same resolved provider returns cached instance"""
        _get_cached_client.cache_clear()

        mock_settings.dashscope_api_key = "test-dashscope-key"
        mock_settings.openai_api_key = None
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client1 = get_embedding_client(provider="auto")
        client2 = get_embedding_client(provider="auto")

        assert client1 is client2

        _get_cached_client.cache_clear()

    @patch('llm.embedding_client.settings')
    def test_different_dimensions_creates_new_instance(self, mock_settings):
        """Test that different dimensions creates new cached instance"""
        _get_cached_client.cache_clear()

        mock_settings.dashscope_api_key = "test-dashscope-key"
        mock_settings.openai_api_key = None
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        client1 = get_embedding_client(provider="auto", dimensions=1536)
        client2 = get_embedding_client(provider="auto", dimensions=512)

        assert client1 is not client2
        assert client1.dimensions == 1536
        assert client2.dimensions == 512

        _get_cached_client.cache_clear()


class TestAliCloudEmbeddingDimensions:
    """Tests for AliCloud embedding dimensions compatibility with DB schema"""

    def test_default_dimensions_matches_db_schema(self):
        """Test default dimensions (1536) matches DB schema vector(1536)"""
        assert DEFAULT_EMBEDDING_DIMENSIONS == 1536

    @patch('openai.OpenAI')
    @patch('llm.embedding_client.settings')
    def test_alicloud_embedding_returns_1536_dimensions(
        self, mock_settings, mock_openai_class
    ):
        """Test AliCloud embedding returns vector with 1536 dimensions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        expected_embedding = [0.1] * 1536
        mock_embedding = MagicMock()
        mock_embedding.embedding = expected_embedding
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]

        mock_openai_client = MagicMock()
        mock_openai_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai_client

        client = EmbeddingClient(provider="alicloud")
        result = client.embed("test text")

        assert result is not None
        assert len(result) == 1536

    @patch('openai.OpenAI')
    @patch('llm.embedding_client.settings')
    def test_alicloud_embed_batch_returns_1536_dimensions(
        self, mock_settings, mock_openai_class
    ):
        """Test AliCloud embed_batch returns vectors with 1536 dimensions"""
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        expected_embeddings = [[0.1] * 1536, [0.2] * 1536]
        mock_data = []
        for emb in expected_embeddings:
            mock_embedding = MagicMock()
            mock_embedding.embedding = emb
            mock_data.append(mock_embedding)

        mock_response = MagicMock()
        mock_response.data = mock_data

        mock_openai_client = MagicMock()
        mock_openai_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai_client

        client = EmbeddingClient(provider="alicloud")
        results = client.embed_batch(["text1", "text2"])

        assert results is not None
        assert len(results) == 2
        assert all(len(emb) == 1536 for emb in results)
