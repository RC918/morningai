"""
Token Service for centralized JWT operations.

Issue #4220: Implement centralized TokenService abstraction for JWT operations.

This service encapsulates all JWT token encode/decode operations in a single place,
following the Single Responsibility Principle and Blueprint 2025 Final architecture:
- Section 4.3: Model Governance Framework v2 - Clean architecture patterns
- Section 5.1: Memory v2 - Centralized abstractions

Benefits:
1. Single Responsibility: All JWT operations in one place
2. Easier Testing: Mock TokenService instead of individual functions
3. Cleaner Dependency Injection: Pass TokenService instance to services
4. Reduced Coupling: Services don't need to know about settings retrieval
"""

import jwt
import logging
from typing import Optional, Dict, Any

from common.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)

# Default fallback secret for testing (DO NOT USE IN PRODUCTION)
_TEST_SECRET_FALLBACK = 'test-secret-key-for-testing'


class TokenService:
    """Centralized service for JWT token operations.

    This class provides a unified interface for encoding and decoding JWT tokens,
    ensuring consistent algorithm and secret key usage across the application.

    Usage:
        # Using singleton (recommended for most cases)
        from src.services.token_service import get_token_service
        token_service = get_token_service()
        token = token_service.encode(payload)
        decoded = token_service.decode(token)

        # Using dependency injection (recommended for testing)
        token_service = TokenService(settings=custom_settings)
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize TokenService with optional settings injection.

        Args:
            settings: Optional Settings instance for dependency injection.
                     If not provided, uses get_settings() singleton.
        """
        self._settings = settings

    @property
    def _resolved_settings(self) -> Settings:
        """Get settings, either injected or from singleton."""
        if self._settings is not None:
            return self._settings
        return get_settings()

    @property
    def algorithm(self) -> str:
        """Get JWT algorithm from settings.

        Returns:
            JWT algorithm string (e.g., 'HS256', 'RS256')
        """
        return self._resolved_settings.jwt_algorithm

    @property
    def secret(self) -> str:
        """Get JWT secret key from settings.

        Returns:
            JWT secret key string. Falls back to test secret if not configured
            (only in non-production environments).

        Raises:
            ValueError: If JWT_SECRET_KEY is not configured in production.
        """
        secret = self._resolved_settings.jwt_secret_key
        if not secret:
            # Fail fast in production - never use fallback secret
            if self._resolved_settings.is_production:
                logger.critical(
                    "CRITICAL: JWT_SECRET_KEY is not configured in production. "
                    "This is a security risk. Aborting."
                )
                raise ValueError(
                    "JWT_SECRET_KEY must be configured in production environment."
                )
            # Non-production: use fallback with warning
            logger.warning(
                "JWT_SECRET_KEY not configured, using test fallback. "
                "DO NOT USE IN PRODUCTION."
            )
            return _TEST_SECRET_FALLBACK
        return secret

    def encode(self, payload: Dict[str, Any]) -> str:
        """Encode a payload into a JWT token.

        Args:
            payload: Dictionary containing the JWT claims.
                    Should include standard claims like 'exp', 'iat', etc.

        Returns:
            Encoded JWT token string.

        Example:
            payload = {
                'user_id': '123',
                'email': 'user@example.com',
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            token = token_service.encode(payload)
        """
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(
        self,
        token: str,
        verify: bool = True,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Decode a JWT token and return the payload.

        Args:
            token: JWT token string to decode.
            verify: Whether to verify the token signature (default: True).
            options: Optional dict of decode options passed to jwt.decode().

        Returns:
            Decoded payload dictionary.

        Raises:
            jwt.ExpiredSignatureError: If the token has expired.
            jwt.InvalidTokenError: If the token is invalid or malformed.

        Example:
            try:
                payload = token_service.decode(token)
                user_id = payload.get('user_id')
            except jwt.ExpiredSignatureError:
                # Handle expired token
            except jwt.InvalidTokenError:
                # Handle invalid token
        """
        # Copy options to avoid mutating caller's dict
        decode_options = options.copy() if options else {}
        if not verify:
            decode_options['verify_signature'] = False

        return jwt.decode(
            token,
            self.secret,
            algorithms=[self.algorithm],
            options=decode_options if decode_options else None
        )

    def decode_safe(self, token: str) -> Optional[Dict[str, Any]]:
        """Safely decode a JWT token, returning None on any error.

        This is a convenience method that catches all JWT exceptions
        and returns None instead of raising.

        Args:
            token: JWT token string to decode.

        Returns:
            Decoded payload dictionary, or None if decoding fails.

        Example:
            payload = token_service.decode_safe(token)
            if payload is None:
                # Token is invalid or expired
                return unauthorized_response()
        """
        try:
            return self.decode(token)
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None


# Singleton instance
_token_service_instance: Optional[TokenService] = None


def get_token_service() -> TokenService:
    """Get the singleton TokenService instance.

    This function provides a singleton TokenService for use throughout
    the application. For testing, you can create a new TokenService
    instance with custom settings.

    Returns:
        TokenService singleton instance.

    Example:
        token_service = get_token_service()
        token = token_service.encode({'user_id': '123'})
    """
    global _token_service_instance
    if _token_service_instance is None:
        _token_service_instance = TokenService()
    return _token_service_instance


def reset_token_service() -> None:
    """Reset the singleton TokenService instance.

    This is primarily useful for testing to ensure a fresh instance
    is created with updated settings.
    """
    global _token_service_instance
    _token_service_instance = None
