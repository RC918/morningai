import pytest
import os
import json
from unittest.mock import Mock, patch, mock_open
from flask import Flask
from src.utils.i18n import I18n, translate, get_locale, localized_response, i18n


@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    
    @app.route('/test')
    def test_route():
        return {"message": "test"}
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def i18n_instance():
    """Create fresh I18n instance"""
    return I18n()


def test_i18n_initialization():
    """Test I18n initializes with default locale"""
    i18n_obj = I18n()
    assert i18n_obj.default_locale == "zh-TW"
    assert "zh-TW" in i18n_obj.supported_locales
    assert "en-US" in i18n_obj.supported_locales


def test_i18n_custom_default_locale():
    """Test I18n with custom default locale"""
    i18n_obj = I18n(default_locale="en-US")
    assert i18n_obj.default_locale == "en-US"


def test_initialize_default_translations(i18n_instance):
    """Test default translations are initialized"""
    assert "zh-TW" in i18n_instance.translations
    assert "en-US" in i18n_instance.translations
    assert "query.success" in i18n_instance.translations["zh-TW"]
    assert "query.success" in i18n_instance.translations["en-US"]


def test_translate_zh_tw(i18n_instance):
    """Test translation to zh-TW"""
    result = i18n_instance.t("query.success", locale="zh-TW")
    assert result == "查詢成功"


def test_translate_en_us(i18n_instance):
    """Test translation to en-US"""
    result = i18n_instance.t("query.success", locale="en-US")
    assert result == "Query successful"


def test_translate_missing_key(i18n_instance):
    """Test translation with missing key returns key"""
    result = i18n_instance.t("missing.key", locale="zh-TW")
    assert result == "missing.key"


def test_translate_with_interpolation(i18n_instance):
    """Test translation with variable interpolation"""
    result = i18n_instance.t("error.rate_limit", locale="zh-TW", seconds=60)
    assert "60" in result


def test_translate_with_missing_interpolation_variable(i18n_instance):
    """Test translation with missing interpolation variable"""
    result = i18n_instance.t("error.rate_limit", locale="zh-TW")
    assert "error.rate_limit" in result or "{seconds}" in result


def test_translate_invalid_locale_fallback(i18n_instance):
    """Test translation falls back to default locale for invalid locale"""
    result = i18n_instance.t("query.success", locale="fr-FR")
    assert result == "查詢成功"


def test_get_locale_from_accept_language_zh_tw(app, i18n_instance):
    """Test get_locale extracts zh-TW from Accept-Language"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW,zh;q=0.9'}):
        locale = i18n_instance.get_locale()
        assert locale == "zh-TW"


def test_get_locale_from_accept_language_zh(app, i18n_instance):
    """Test get_locale extracts zh-TW from zh"""
    with app.test_request_context(headers={'Accept-Language': 'zh;q=0.9'}):
        locale = i18n_instance.get_locale()
        assert locale == "zh-TW"


def test_get_locale_from_accept_language_en(app, i18n_instance):
    """Test get_locale extracts en-US from en"""
    with app.test_request_context(headers={'Accept-Language': 'en-US,en;q=0.9'}):
        locale = i18n_instance.get_locale()
        assert locale == "en-US"


def test_get_locale_default(app, i18n_instance):
    """Test get_locale returns default when no Accept-Language"""
    with app.test_request_context():
        locale = i18n_instance.get_locale()
        assert locale == "zh-TW"


def test_get_locale_exception_handling(i18n_instance):
    """Test get_locale handles exceptions gracefully"""
    locale = i18n_instance.get_locale()
    assert locale == "zh-TW"


def test_translate_response_with_message(app, i18n_instance):
    """Test translate_response translates message field"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"message": "_query.success"}
        result = i18n_instance.translate_response(data)
        assert result["message"] == "查詢成功"


def test_translate_response_without_underscore(app, i18n_instance):
    """Test translate_response leaves message without underscore unchanged"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"message": "custom message"}
        result = i18n_instance.translate_response(data)
        assert result["message"] == "custom message"


def test_translate_response_with_error(app, i18n_instance):
    """Test translate_response translates error message"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"error": {"message": "_error.unauthorized"}}
        result = i18n_instance.translate_response(data)
        assert "認證失敗" in result["error"]["message"]


def test_translate_response_error_without_underscore(app, i18n_instance):
    """Test translate_response leaves error message without underscore unchanged"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"error": {"message": "custom error"}}
        result = i18n_instance.translate_response(data)
        assert result["error"]["message"] == "custom error"


def test_translate_response_with_locale_parameter(i18n_instance):
    """Test translate_response with explicit locale parameter"""
    data = {"message": "_query.success"}
    result = i18n_instance.translate_response(data, locale="en-US")
    assert result["message"] == "Query successful"


def test_error_response_zh_tw(app, i18n_instance):
    """Test error_response generates zh-TW error"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        response, status_code = i18n_instance.error_response("unauthorized", 401)
        assert status_code == 401
        assert response["error"]["code"] == "unauthorized"
        assert "認證失敗" in response["error"]["message"]


def test_error_response_en_us(app, i18n_instance):
    """Test error_response generates en-US error"""
    with app.test_request_context(headers={'Accept-Language': 'en-US'}):
        response, status_code = i18n_instance.error_response("unauthorized", 401)
        assert status_code == 401
        assert "Authentication failed" in response["error"]["message"]


def test_error_response_with_kwargs(app, i18n_instance):
    """Test error_response includes kwargs in details"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        response, status_code = i18n_instance.error_response(
            "invalid_parameter",
            400,
            field="email",
            message="invalid format"
        )
        assert status_code == 400
        assert "details" in response["error"]
        assert response["error"]["details"]["field"] == "email"


def test_error_response_default_status_code(app, i18n_instance):
    """Test error_response uses default status code"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        response, status_code = i18n_instance.error_response("bad_request")
        assert status_code == 400


def test_translate_convenience_function(app):
    """Test translate convenience function"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        result = translate("query.success")
        assert result == "查詢成功"


def test_get_locale_convenience_function(app):
    """Test get_locale convenience function"""
    with app.test_request_context(headers={'Accept-Language': 'en-US'}):
        locale = get_locale()
        assert locale == "en-US"


def test_localized_response_convenience_function(app):
    """Test localized_response convenience function"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"message": "_query.success"}
        result = localized_response(data)
        assert result["message"] == "查詢成功"


def test_all_error_types_zh_tw(i18n_instance):
    """Test all error types have zh-TW translations"""
    error_types = [
        "unauthorized",
        "forbidden",
        "not_found",
        "bad_request",
        "internal_server",
        "rate_limit",
        "invalid_parameter"
    ]
    
    for error_type in error_types:
        key = f"error.{error_type}"
        result = i18n_instance.t(key, locale="zh-TW")
        assert result != key
        assert len(result) > 0


def test_all_error_types_en_us(i18n_instance):
    """Test all error types have en-US translations"""
    error_types = [
        "unauthorized",
        "forbidden",
        "not_found",
        "bad_request",
        "internal_server",
        "rate_limit",
        "invalid_parameter"
    ]
    
    for error_type in error_types:
        key = f"error.{error_type}"
        result = i18n_instance.t(key, locale="en-US")
        assert result != key
        assert len(result) > 0


def test_vector_translations_zh_tw(i18n_instance):
    """Test vector-related translations in zh-TW"""
    keys = [
        "vector.visualization.success",
        "vector.no_vectors",
        "vector.insufficient"
    ]
    
    for key in keys:
        result = i18n_instance.t(key, locale="zh-TW")
        assert result != key
        assert len(result) > 0


def test_vector_translations_en_us(i18n_instance):
    """Test vector-related translations in en-US"""
    keys = [
        "vector.visualization.success",
        "vector.no_vectors",
        "vector.insufficient"
    ]
    
    for key in keys:
        result = i18n_instance.t(key, locale="en-US")
        assert result != key
        assert len(result) > 0


def test_alert_translations_zh_tw(i18n_instance):
    """Test alert translations in zh-TW"""
    result = i18n_instance.t("cost.alert.high", locale="zh-TW", amount="100")
    assert "100" in result
    
    result = i18n_instance.t("latency.alert.high", locale="zh-TW", ms="500")
    assert "500" in result


def test_alert_translations_en_us(i18n_instance):
    """Test alert translations in en-US"""
    result = i18n_instance.t("cost.alert.high", locale="en-US", amount="100")
    assert "100" in result
    
    result = i18n_instance.t("latency.alert.high", locale="en-US", ms="500")
    assert "500" in result


def test_crud_translations_zh_tw(i18n_instance):
    """Test CRUD operation translations in zh-TW"""
    operations = ["query", "create", "update", "delete"]
    statuses = ["success", "failed"]
    
    for op in operations:
        for status in statuses:
            key = f"{op}.{status}"
            result = i18n_instance.t(key, locale="zh-TW")
            assert result != key
            assert len(result) > 0


def test_crud_translations_en_us(i18n_instance):
    """Test CRUD operation translations in en-US"""
    operations = ["query", "create", "update", "delete"]
    statuses = ["success", "failed"]
    
    for op in operations:
        for status in statuses:
            key = f"{op}.{status}"
            result = i18n_instance.t(key, locale="en-US")
            assert result != key
            assert len(result) > 0


def test_lru_cache_on_translate():
    """Test that translate method uses lru_cache"""
    i18n_obj = I18n()
    assert hasattr(i18n_obj.t, '__wrapped__')


def test_translate_response_non_dict_message(app, i18n_instance):
    """Test translate_response handles non-string message"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"message": 123}
        result = i18n_instance.translate_response(data)
        assert result["message"] == 123


def test_translate_response_non_dict_error(app, i18n_instance):
    """Test translate_response handles non-dict error"""
    with app.test_request_context(headers={'Accept-Language': 'zh-TW'}):
        data = {"error": "string error"}
        result = i18n_instance.translate_response(data)
        assert result["error"] == "string error"


def test_error_response_with_explicit_locale(i18n_instance):
    """Test error_response with explicit locale parameter"""
    response, status_code = i18n_instance.error_response(
        "unauthorized",
        401,
        locale="en-US"
    )
    assert "Authentication failed" in response["error"]["message"]


def test_global_i18n_instance():
    """Test global i18n instance is created"""
    assert i18n is not None
    assert isinstance(i18n, I18n)


def test_supported_locales(i18n_instance):
    """Test supported locales are defined"""
    assert len(i18n_instance.supported_locales) == 2
    assert "zh-TW" in i18n_instance.supported_locales
    assert "en-US" in i18n_instance.supported_locales
