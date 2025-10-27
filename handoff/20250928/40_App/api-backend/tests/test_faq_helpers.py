"""Tests for FAQ helper functions and models"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError
from src.routes.faq import (
    FAQSearchRequest,
    FAQCreateRequest,
    FAQUpdateRequest,
    generate_cache_key,
    get_cached_result,
    set_cached_result,
    invalidate_cache_pattern,
    async_route
)


class TestFAQSearchRequest:
    """Test FAQSearchRequest validation"""
    
    def test_valid_search_request(self):
        """Test valid search request"""
        req = FAQSearchRequest(
            q="test query",
            page=1,
            page_size=10,
            category="general",
            sort_by="created_at",
            sort_order="desc"
        )
        assert req.q == "test query"
        assert req.page == 1
        assert req.page_size == 10
        assert req.category == "general"
        assert req.sort_by == "created_at"
        assert req.sort_order == "desc"
    
    def test_query_strip_whitespace(self):
        """Test query whitespace stripping"""
        req = FAQSearchRequest(q="  test query  ")
        assert req.q == "test query"
    
    def test_empty_query_raises_error(self):
        """Test empty query raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            FAQSearchRequest(q="")
        errors = exc_info.value.errors()
        assert any('query cannot be empty' in str(e['msg']) for e in errors)
    
    def test_whitespace_only_query_raises_error(self):
        """Test whitespace-only query raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            FAQSearchRequest(q="   ")
        errors = exc_info.value.errors()
        assert any('query cannot be empty' in str(e['msg']) for e in errors)
    
    def test_page_minimum_value(self):
        """Test page must be >= 1"""
        with pytest.raises(ValidationError):
            FAQSearchRequest(q="test", page=0)
    
    def test_page_size_minimum_value(self):
        """Test page_size must be >= 1"""
        with pytest.raises(ValidationError):
            FAQSearchRequest(q="test", page_size=0)
    
    def test_page_size_maximum_value(self):
        """Test page_size must be <= 100"""
        with pytest.raises(ValidationError):
            FAQSearchRequest(q="test", page_size=101)
    
    def test_sort_order_validation(self):
        """Test sort_order must be asc or desc"""
        with pytest.raises(ValidationError) as exc_info:
            FAQSearchRequest(q="test", sort_order="invalid")
        errors = exc_info.value.errors()
        assert any('sort_order must be asc or desc' in str(e['msg']) for e in errors)
    
    def test_sort_order_case_insensitive(self):
        """Test sort_order is case insensitive"""
        req = FAQSearchRequest(q="test", sort_order="ASC")
        assert req.sort_order == "asc"
        
        req = FAQSearchRequest(q="test", sort_order="DESC")
        assert req.sort_order == "desc"
    
    def test_default_values(self):
        """Test default values"""
        req = FAQSearchRequest(q="test")
        assert req.page == 1
        assert req.page_size == 10
        assert req.category is None
        assert req.sort_by is None
        assert req.sort_order == "desc"


class TestFAQCreateRequest:
    """Test FAQCreateRequest validation"""
    
    def test_valid_create_request(self):
        """Test valid create request"""
        req = FAQCreateRequest(
            question="What is this?",
            answer="This is an answer",
            category="general",
            tags=["tag1", "tag2"]
        )
        assert req.question == "What is this?"
        assert req.answer == "This is an answer"
        assert req.category == "general"
        assert req.tags == ["tag1", "tag2"]
    
    def test_question_strip_whitespace(self):
        """Test question whitespace stripping"""
        req = FAQCreateRequest(
            question="  What is this?  ",
            answer="Answer"
        )
        assert req.question == "What is this?"
    
    def test_answer_strip_whitespace(self):
        """Test answer whitespace stripping"""
        req = FAQCreateRequest(
            question="Question",
            answer="  Answer  "
        )
        assert req.answer == "Answer"
    
    def test_empty_question_raises_error(self):
        """Test empty question raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            FAQCreateRequest(question="", answer="Answer")
        errors = exc_info.value.errors()
        assert any('field cannot be empty' in str(e['msg']) for e in errors)
    
    def test_empty_answer_raises_error(self):
        """Test empty answer raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            FAQCreateRequest(question="Question", answer="")
        errors = exc_info.value.errors()
        assert any('field cannot be empty' in str(e['msg']) for e in errors)
    
    def test_default_values(self):
        """Test default values"""
        req = FAQCreateRequest(question="Q", answer="A")
        assert req.category is None
        assert req.tags == []


class TestFAQUpdateRequest:
    """Test FAQUpdateRequest validation"""
    
    def test_valid_update_request(self):
        """Test valid update request"""
        req = FAQUpdateRequest(
            question="Updated question",
            answer="Updated answer",
            category="updated",
            tags=["new_tag"]
        )
        assert req.question == "Updated question"
        assert req.answer == "Updated answer"
        assert req.category == "updated"
        assert req.tags == ["new_tag"]
    
    def test_partial_update(self):
        """Test partial update with only some fields"""
        req = FAQUpdateRequest(question="Updated question")
        assert req.question == "Updated question"
        assert req.answer is None
        assert req.category is None
        assert req.tags is None
    
    def test_all_fields_optional(self):
        """Test all fields are optional"""
        req = FAQUpdateRequest()
        assert req.question is None
        assert req.answer is None
        assert req.category is None
        assert req.tags is None


class TestGenerateCacheKey:
    """Test generate_cache_key function"""
    
    def test_basic_cache_key(self):
        """Test basic cache key generation"""
        key = generate_cache_key("search", q="test")
        assert key.startswith("faq:search:")
        assert len(key) > len("faq:search:")
    
    def test_same_params_same_key(self):
        """Test same parameters generate same key"""
        key1 = generate_cache_key("search", q="test", page=1)
        key2 = generate_cache_key("search", q="test", page=1)
        assert key1 == key2
    
    def test_different_params_different_key(self):
        """Test different parameters generate different keys"""
        key1 = generate_cache_key("search", q="test1")
        key2 = generate_cache_key("search", q="test2")
        assert key1 != key2
    
    def test_param_order_doesnt_matter(self):
        """Test parameter order doesn't affect key"""
        key1 = generate_cache_key("search", q="test", page=1, limit=10)
        key2 = generate_cache_key("search", limit=10, page=1, q="test")
        assert key1 == key2
    
    def test_different_prefixes(self):
        """Test different prefixes generate different keys"""
        key1 = generate_cache_key("search", q="test")
        key2 = generate_cache_key("item", q="test")
        assert key1 != key2
        assert key1.startswith("faq:search:")
        assert key2.startswith("faq:item:")


class TestCacheFunctions:
    """Test cache helper functions"""
    
    @patch('src.routes.faq.redis_client')
    def test_get_cached_result_hit(self, mock_redis):
        """Test cache hit"""
        test_data = {"result": "test"}
        mock_redis.get.return_value = json.dumps(test_data)
        
        result = get_cached_result("test_key")
        
        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")
    
    @patch('src.routes.faq.redis_client')
    def test_get_cached_result_miss(self, mock_redis):
        """Test cache miss"""
        mock_redis.get.return_value = None
        
        result = get_cached_result("test_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("test_key")
    
    @patch('src.routes.faq.redis_client')
    def test_get_cached_result_redis_error(self, mock_redis):
        """Test Redis connection error"""
        from redis import ConnectionError as RedisConnectionError
        mock_redis.get.side_effect = RedisConnectionError("Connection failed")
        
        result = get_cached_result("test_key")
        
        assert result is None
    
    @patch('src.routes.faq.redis_client')
    def test_get_cached_result_json_error(self, mock_redis):
        """Test invalid JSON in cache"""
        mock_redis.get.return_value = "invalid json"
        
        result = get_cached_result("test_key")
        
        assert result is None
    
    @patch('src.routes.faq.redis_client')
    def test_set_cached_result(self, mock_redis):
        """Test setting cache"""
        test_data = {"result": "test"}
        
        set_cached_result("test_key", test_data, ttl=300)
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0] == "test_key"
        assert call_args[1] == 300
        assert json.loads(call_args[2]) == test_data
    
    @patch('src.routes.faq.redis_client')
    def test_set_cached_result_redis_error(self, mock_redis):
        """Test Redis error when setting cache"""
        from redis import ConnectionError as RedisConnectionError
        mock_redis.setex.side_effect = RedisConnectionError("Connection failed")
        
        set_cached_result("test_key", {"data": "test"})
    
    @patch('src.routes.faq.redis_client')
    def test_invalidate_cache_pattern(self, mock_redis):
        """Test cache invalidation"""
        mock_redis.scan_iter.return_value = iter([
            "faq:search:key1",
            "faq:search:key2",
            "faq:search:key3"
        ])
        
        invalidate_cache_pattern("search")
        
        mock_redis.scan_iter.assert_called_once_with("faq:search*")
        mock_redis.delete.assert_called_once()
        deleted_keys = mock_redis.delete.call_args[0]
        assert len(deleted_keys) == 3
    
    @patch('src.routes.faq.redis_client')
    def test_invalidate_cache_pattern_no_keys(self, mock_redis):
        """Test cache invalidation with no matching keys"""
        mock_redis.scan_iter.return_value = iter([])
        
        invalidate_cache_pattern("search")
        
        mock_redis.scan_iter.assert_called_once_with("faq:search*")
        mock_redis.delete.assert_not_called()
    
    @patch('src.routes.faq.redis_client')
    def test_invalidate_cache_pattern_error(self, mock_redis):
        """Test cache invalidation error"""
        mock_redis.scan_iter.side_effect = Exception("Redis error")
        
        invalidate_cache_pattern("search")


class TestAsyncRoute:
    """Test async_route decorator"""
    
    def test_async_route_decorator(self):
        """Test async_route decorator executes async function"""
        @async_route
        async def test_func(value):
            return value * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_async_route_with_exception(self):
        """Test async_route decorator handles exceptions"""
        @async_route
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_func()
    
    def test_async_route_preserves_function_name(self):
        """Test async_route preserves function metadata"""
        @async_route
        async def test_func():
            """Test docstring"""
            pass
        
        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test docstring"
