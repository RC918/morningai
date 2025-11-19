"""
Tests for i18n (internationalization) utilities.

Tests cover:
- I18n class: translation loading, getting translations, locale detection
- Helper functions: translate, get_locale, localized_response
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import json


class TestI18n:
    """Test I18n class"""
    
    def test_init_default_locale(self):
        """Should initialize with default locale"""
        from utils.i18n import I18n
        
        i18n = I18n()
        
        assert i18n.default_locale == "zh-TW"
        assert "zh-TW" in i18n.supported_locales
        assert "en-US" in i18n.supported_locales
    
    def test_init_custom_locale(self):
        """Should initialize with custom default locale"""
        from utils.i18n import I18n
        
        i18n = I18n(default_locale="en-US")
        
        assert i18n.default_locale == "en-US"
    
    def test_initialize_default_translations(self):
        """Should initialize default translations when directory not found"""
        from utils.i18n import I18n
        
        with patch('os.path.exists', return_value=False):
            i18n = I18n()
        
        assert "zh-TW" in i18n.translations
        assert "en-US" in i18n.translations
        assert "query.success" in i18n.translations["zh-TW"]
        assert "query.success" in i18n.translations["en-US"]
    
    def test_get_locale_from_accept_language_zh_tw(self):
        """Should detect zh-TW from Accept-Language header"""
        from utils.i18n import I18n
        
        i18n = I18n()
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "zh-TW,zh;q=0.9"}
        
        with patch('utils.i18n.request', mock_request):
            result = i18n.get_locale()
        
        assert result == "zh-TW"
    
    def test_get_locale_from_accept_language_zh(self):
        """Should detect zh-TW from zh in Accept-Language header"""
        from utils.i18n import I18n
        
        i18n = I18n()
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "zh;q=0.9"}
        
        with patch('utils.i18n.request', mock_request):
            result = i18n.get_locale()
        
        assert result == "zh-TW"
    
    def test_get_locale_from_accept_language_en(self):
        """Should detect en-US from en in Accept-Language header"""
        from utils.i18n import I18n
        
        i18n = I18n()
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "en-US,en;q=0.9"}
        
        with patch('utils.i18n.request', mock_request):
            result = i18n.get_locale()
        
        assert result == "en-US"
    
    def test_get_locale_default_fallback(self):
        """Should return default locale when no Accept-Language header"""
        from utils.i18n import I18n
        
        i18n = I18n()
        mock_request = MagicMock()
        mock_request.headers = {}
        
        with patch('utils.i18n.request', mock_request):
            result = i18n.get_locale()
        
        assert result == "zh-TW"
    
    def test_get_locale_exception_fallback(self):
        """Should return default locale on exception"""
        from utils.i18n import I18n
        
        i18n = I18n()
        
        with patch('utils.i18n.request', side_effect=RuntimeError("No request context")):
            result = i18n.get_locale()
        
        assert result == "zh-TW"
    
    def test_translate_existing_key(self):
        """Should translate existing key"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "en-US": {"query.success": "Query successful"}
        }
        
        result = i18n.t("query.success", locale="en-US")
        
        assert result == "Query successful"
    
    def test_translate_missing_key_returns_key(self):
        """Should return key when translation missing"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {"en-US": {}}
        
        result = i18n.t("missing.key", locale="en-US")
        
        assert result == "missing.key"
    
    def test_translate_with_interpolation(self):
        """Should interpolate variables in translation"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "en-US": {"error.rate_limit": "Wait {seconds} seconds"}
        }
        
        result = i18n.t("error.rate_limit", locale="en-US", seconds=30)
        
        assert result == "Wait 30 seconds"
    
    def test_translate_missing_locale_uses_default(self):
        """Should use default locale when specified locale missing"""
        from utils.i18n import I18n
        
        i18n = I18n(default_locale="en-US")
        i18n.translations = {
            "en-US": {"hello": "Hello"}
        }
        
        result = i18n.t("hello", locale="fr-FR")
        
        assert result == "Hello"
    
    def test_translate_no_locale_uses_request_locale(self):
        """Should use request locale when not specified"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "zh-TW": {"hello": "你好"}
        }
        
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "zh-TW"}
        
        with patch('utils.i18n.request', mock_request):
            result = i18n.t("hello")
        
        assert result == "你好"
    
    def test_translate_response_with_message(self):
        """Should translate message field starting with underscore"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "en-US": {"query.success": "Query successful"}
        }
        
        data = {"message": "_query.success"}
        result = i18n.translate_response(data, locale="en-US")
        
        assert result["message"] == "Query successful"
    
    def test_translate_response_without_underscore(self):
        """Should not translate message without underscore prefix"""
        from utils.i18n import I18n
        
        i18n = I18n()
        
        data = {"message": "Direct message"}
        result = i18n.translate_response(data, locale="en-US")
        
        assert result["message"] == "Direct message"
    
    def test_translate_response_with_error(self):
        """Should translate error message starting with underscore"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "en-US": {"error.not_found": "Not found"}
        }
        
        data = {"error": {"message": "_error.not_found"}}
        result = i18n.translate_response(data, locale="en-US")
        
        assert result["error"]["message"] == "Not found"
    
    def test_error_response(self):
        """Should generate error response with translation"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "en-US": {"error.unauthorized": "Authentication failed"}
        }
        
        response, status_code = i18n.error_response("unauthorized", status_code=401, locale="en-US")
        
        assert status_code == 401
        assert response["error"]["code"] == "unauthorized"
        assert response["error"]["message"] == "Authentication failed"
    
    def test_error_response_with_details(self):
        """Should include details in error response"""
        from utils.i18n import I18n
        
        i18n = I18n()
        i18n.translations = {
            "en-US": {"error.invalid_parameter": "Invalid {field}"}
        }
        
        response, status_code = i18n.error_response(
            "invalid_parameter",
            status_code=400,
            locale="en-US",
            field="email"
        )
        
        assert response["error"]["message"] == "Invalid email"
        assert response["error"]["details"]["field"] == "email"


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_translate_function(self):
        """Should translate using global i18n instance"""
        from utils.i18n import translate, i18n
        
        i18n.translations = {
            "en-US": {"hello": "Hello"}
        }
        
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "en-US"}
        
        with patch('utils.i18n.request', mock_request):
            result = translate("hello")
        
        assert result == "Hello"
    
    def test_get_locale_function(self):
        """Should get locale using global i18n instance"""
        from utils.i18n import get_locale
        
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "zh-TW"}
        
        with patch('utils.i18n.request', mock_request):
            result = get_locale()
        
        assert result == "zh-TW"
    
    def test_localized_response_function(self):
        """Should localize response using global i18n instance"""
        from utils.i18n import localized_response, i18n
        
        i18n.translations = {
            "en-US": {"success": "Success"}
        }
        
        mock_request = MagicMock()
        mock_request.headers = {"Accept-Language": "en-US"}
        
        data = {"message": "_success"}
        
        with patch('utils.i18n.request', mock_request):
            result = localized_response(data)
        
        assert result["message"] == "Success"


class TestDefaultTranslations:
    """Test default translations are loaded correctly"""
    
    def test_has_zh_tw_translations(self):
        """Should have zh-TW translations"""
        from utils.i18n import I18n
        
        with patch('os.path.exists', return_value=False):
            i18n = I18n()
        
        assert "query.success" in i18n.translations["zh-TW"]
        assert i18n.translations["zh-TW"]["query.success"] == "查詢成功"
    
    def test_has_en_us_translations(self):
        """Should have en-US translations"""
        from utils.i18n import I18n
        
        with patch('os.path.exists', return_value=False):
            i18n = I18n()
        
        assert "query.success" in i18n.translations["en-US"]
        assert i18n.translations["en-US"]["query.success"] == "Query successful"
    
    def test_has_error_translations(self):
        """Should have error translations"""
        from utils.i18n import I18n
        
        with patch('os.path.exists', return_value=False):
            i18n = I18n()
        
        assert "error.unauthorized" in i18n.translations["en-US"]
        assert "error.not_found" in i18n.translations["en-US"]
        assert "error.rate_limit" in i18n.translations["en-US"]
