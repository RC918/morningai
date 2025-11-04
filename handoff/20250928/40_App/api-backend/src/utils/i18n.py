"""
Internationalization (i18n) Utility

Provides multi-language support for API responses and error messages.
"""
import os
import json
import logging
from typing import Dict, Optional, Any
from functools import lru_cache
from flask import request

logger = logging.getLogger(__name__)


class I18n:
    """Internationalization handler"""
    
    def __init__(self, default_locale: str = "zh-TW"):
        self.default_locale = default_locale
        self.translations: Dict[str, Dict[str, str]] = {}
        self.supported_locales = ["zh-TW", "en-US"]
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files"""
        translations_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "translations"
        )
        
        if not os.path.exists(translations_dir):
            logger.warning(f"Translations directory not found: {translations_dir}")
            self._initialize_default_translations()
            return
        
        for locale in self.supported_locales:
            translation_file = os.path.join(translations_dir, f"{locale}.json")
            
            if os.path.exists(translation_file):
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[locale] = json.load(f)
                    logger.info(f"Loaded translations for {locale}")
                except Exception as e:
                    logger.error(f"Failed to load translations for {locale}: {e}")
                    self.translations[locale] = {}
            else:
                logger.warning(f"Translation file not found: {translation_file}")
                self.translations[locale] = {}
    
    def _initialize_default_translations(self):
        """Initialize default translations in memory"""
        self.translations = {
            "zh-TW": {
                "query.success": "查詢成功",
                "query.failed": "查詢失敗",
                "create.success": "創建成功",
                "create.failed": "創建失敗",
                "update.success": "更新成功",
                "update.failed": "更新失敗",
                "delete.success": "刪除成功",
                "delete.failed": "刪除失敗",
                "error.unauthorized": "認證失敗。請檢查您的 API 金鑰。",
                "error.forbidden": "禁止存取。您沒有權限執行此操作。",
                "error.not_found": "找不到資源。請確認 ID 是否正確。",
                "error.bad_request": "請求錯誤。請檢查參數格式。",
                "error.internal_server": "伺服器發生錯誤，我們正在處理。請稍後再試。",
                "error.rate_limit": "請求過於頻繁。請等待 {seconds} 秒後再試。",
                "error.invalid_parameter": "參數 '{field}' 無效: {message}",
                "vector.visualization.success": "向量視覺化已生成",
                "vector.no_vectors": "沒有找到向量",
                "vector.insufficient": "需要至少 {count} 個向量才能進行視覺化",
                "drift.detected": "檢測到記憶遷移",
                "cost.alert.high": "LLM 成本過高: ${amount}",
                "latency.alert.high": "延遲過高: {ms}ms"
            },
            "en-US": {
                "query.success": "Query successful",
                "query.failed": "Query failed",
                "create.success": "Created successfully",
                "create.failed": "Creation failed",
                "update.success": "Updated successfully",
                "update.failed": "Update failed",
                "delete.success": "Deleted successfully",
                "delete.failed": "Deletion failed",
                "error.unauthorized": "Authentication failed. Please check your API key.",
                "error.forbidden": "Access forbidden. You don't have permission for this operation.",
                "error.not_found": "Resource not found. Please check the ID.",
                "error.bad_request": "Bad request. Please check your parameters.",
                "error.internal_server": "Server error occurred. We're working on it. Please try again later.",
                "error.rate_limit": "Too many requests. Please wait {seconds} seconds before retrying.",
                "error.invalid_parameter": "Invalid parameter '{field}': {message}",
                "vector.visualization.success": "Vector visualization generated",
                "vector.no_vectors": "No vectors found",
                "vector.insufficient": "Need at least {count} vectors for visualization",
                "drift.detected": "Memory drift detected",
                "cost.alert.high": "High LLM cost: ${amount}",
                "latency.alert.high": "High latency: {ms}ms"
            }
        }
    
    def get_locale(self) -> str:
        """Get current locale from request or default"""
        try:
            accept_language = request.headers.get('Accept-Language', '')
            
            if 'zh-TW' in accept_language or 'zh-tw' in accept_language:
                return 'zh-TW'
            elif 'zh' in accept_language:
                return 'zh-TW'
            elif 'en' in accept_language:
                return 'en-US'
            
            return self.default_locale
        except:
            return self.default_locale
    
    @lru_cache(maxsize=1000)
    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the specified locale
        
        Args:
            key: Translation key (e.g., "query.success")
            locale: Target locale (defaults to request locale)
            **kwargs: Variables for interpolation
        
        Returns:
            Translated string
        """
        if locale is None:
            locale = self.get_locale()
        
        if locale not in self.translations:
            locale = self.default_locale
        
        translation = self.translations.get(locale, {}).get(key, key)
        
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing interpolation variable {e} for key {key}")
        
        return translation
    
    def translate_response(self, data: Dict[str, Any], locale: Optional[str] = None) -> Dict[str, Any]:
        """
        Translate response message fields
        
        Args:
            data: Response data dictionary
            locale: Target locale
        
        Returns:
            Translated response
        """
        if locale is None:
            locale = self.get_locale()
        
        if "message" in data and isinstance(data["message"], str):
            if data["message"].startswith("_"):
                key = data["message"][1:]
                data["message"] = self.t(key, locale)
        
        if "error" in data and isinstance(data["error"], dict):
            if "message" in data["error"] and data["error"]["message"].startswith("_"):
                key = data["error"]["message"][1:]
                data["error"]["message"] = self.t(key, locale)
        
        return data
    
    def error_response(
        self,
        error_type: str,
        status_code: int = 400,
        locale: Optional[str] = None,
        **kwargs
    ) -> tuple[Dict[str, Any], int]:
        """
        Generate standardized error response
        
        Args:
            error_type: Error type key (e.g., "unauthorized", "not_found")
            status_code: HTTP status code
            locale: Target locale
            **kwargs: Additional error context
        
        Returns:
            (response_dict, status_code) tuple
        """
        if locale is None:
            locale = self.get_locale()
        
        error_key = f"error.{error_type}"
        message = self.t(error_key, locale, **kwargs)
        
        response = {
            "error": {
                "code": error_type,
                "message": message
            }
        }
        
        if kwargs:
            response["error"]["details"] = kwargs
        
        return response, status_code


i18n = I18n()


def translate(key: str, **kwargs) -> str:
    """
    Convenience function for translation
    
    Args:
        key: Translation key
        **kwargs: Interpolation variables
    
    Returns:
        Translated string
    """
    return i18n.t(key, **kwargs)


def get_locale() -> str:
    """Get current request locale"""
    return i18n.get_locale()


def localized_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply localization to response data
    
    Args:
        data: Response dictionary
    
    Returns:
        Localized response
    """
    return i18n.translate_response(data)
