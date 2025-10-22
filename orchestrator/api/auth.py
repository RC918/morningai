#!/usr/bin/env python3
"""
Authentication and Authorization for Orchestrator API
Supports both JWT and API Key authentication
"""
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
import jwt

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer()
security_api_key = APIKeyHeader(name="X-API-Key", auto_error=False)


class Role(Enum):
    """User roles"""
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"


class AuthConfig:
    """Authentication configuration"""
    JWT_SECRET_KEY = os.getenv("ORCHESTRATOR_JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    API_KEYS: Dict[str, str] = {}
    
    @classmethod
    def validate_config(cls):
        """Validate authentication configuration on startup"""
        if not cls.JWT_SECRET_KEY:
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: ORCHESTRATOR_JWT_SECRET environment variable is not set. "
                "JWT authentication cannot function without a secret key. "
                "Please set ORCHESTRATOR_JWT_SECRET to a strong random string (minimum 32 characters). "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        if len(cls.JWT_SECRET_KEY) < 32:
            logger.warning(
                "SECURITY WARNING: ORCHESTRATOR_JWT_SECRET is too short (< 32 characters). "
                "This weakens JWT security. Generate a stronger secret with: "
                "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
    
    @classmethod
    def load_api_keys(cls):
        """Load API keys from environment variables"""
        cls.API_KEYS = {}
        for key, value in os.environ.items():
            if key.startswith("ORCHESTRATOR_API_KEY_"):
                try:
                    api_key, role = value.split(":")
                    cls.API_KEYS[api_key] = role
                    logger.info(f"Loaded API key: {key} with role {role}")
                except ValueError:
                    logger.warning(f"Invalid API key format for {key}, expected 'key:role'")


AuthConfig.load_api_keys()
AuthConfig.validate_config()


class AuthUser:
    """Authenticated user"""
    def __init__(self, user_id: str, role: Role, auth_method: str):
        self.user_id = user_id
        self.role = role
        self.auth_method = auth_method
    
    def has_role(self, required_role: Role) -> bool:
        """Check if user has required role"""
        role_hierarchy = {
            Role.ADMIN: 3,
            Role.AGENT: 2,
            Role.USER: 1
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)


def create_jwt_token(user_id: str, role: Role) -> str:
    """
    Create a JWT token
    
    Args:
        user_id: User identifier
        role: User role
    
    Returns:
        str: JWT token
    """
    payload = {
        "sub": user_id,
        "role": role.value,
        "exp": datetime.now(timezone.utc) + timedelta(hours=AuthConfig.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, AuthConfig.JWT_SECRET_KEY, algorithm=AuthConfig.JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Optional[Dict]: Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            AuthConfig.JWT_SECRET_KEY,
            algorithms=[AuthConfig.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def verify_api_key(api_key: str) -> Optional[str]:
    """
    Verify API key and return role
    
    Args:
        api_key: API key string
    
    Returns:
        Optional[str]: Role if valid, None otherwise
    """
    role = AuthConfig.API_KEYS.get(api_key)
    if role:
        logger.debug(f"Valid API key with role: {role}")
    return role


async def get_current_user(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(security_api_key)
) -> AuthUser:
    """
    Get current authenticated user from JWT or API Key
    
    Supports two authentication methods:
    1. Bearer token (JWT): Authorization: Bearer <token>
    2. API Key: X-API-Key: <key>
    
    Args:
        bearer_credentials: Bearer token credentials
        api_key: API key from header
    
    Returns:
        AuthUser: Authenticated user
    
    Raises:
        HTTPException: If authentication fails
    """
    if bearer_credentials:
        token = bearer_credentials.credentials
        payload = verify_jwt_token(token)
        
        if payload:
            try:
                role = Role(payload.get("role"))
                return AuthUser(
                    user_id=payload.get("sub"),
                    role=role,
                    auth_method="jwt"
                )
            except ValueError:
                logger.warning(f"Invalid role in JWT: {payload.get('role')}")
    
    if api_key:
        role_str = verify_api_key(api_key)
        if role_str:
            try:
                role = Role(role_str)
                return AuthUser(
                    user_id=f"api_key_{api_key[:8]}",
                    role=role,
                    auth_method="api_key"
                )
            except ValueError:
                logger.warning(f"Invalid role for API key: {role_str}")
    
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def require_role(required_role: Role):
    """
    Dependency to require specific role
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: AuthUser = Depends(require_role(Role.ADMIN))):
            ...
    """
    async def role_checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return user
    
    return role_checker


async def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require admin role"""
    if not user.has_role(Role.ADMIN):
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


async def require_agent(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require agent role or higher"""
    if not user.has_role(Role.AGENT):
        raise HTTPException(status_code=403, detail="Agent role required")
    return user
