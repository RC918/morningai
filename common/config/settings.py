"""
Centralized Configuration Management using Pydantic BaseSettings

This module provides type-safe, validated access to all environment variables
used across the MorningAI platform. It replaces scattered os.getenv() calls
with a single source of truth.

Usage:
    from common.config.settings import settings
    
    api_key = settings.openai_api_key
    db_url = settings.database_url
    is_production = settings.is_production

Features:
- Type validation and coercion
- Default values from env.schema.yaml
- Alias support for deprecated variable names
- Automatic .env file loading
- Startup validation for required variables
"""

import os
import sys
import warnings
from typing import Optional, Literal
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All variables are mapped from config/env.schema.yaml.
    Supports both new and deprecated variable names via Field(alias=...).
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars not defined here
        populate_by_name=True,  # Allow both field name and alias
    )
    
    
    jwt_secret_key: Optional[str] = Field(
        None,
        alias="JWT_SECRET_KEY",
        min_length=32,
        description="JWT token signing key for authentication"
    )
    
    admin_password: Optional[str] = Field(
        None,
        description="Admin user password for system access"
    )
    
    flask_secret_key: Optional[str] = Field(
        None,
        alias="SECRET_KEY",  # Support deprecated SECRET_KEY
        min_length=32,
        description="Flask application secret key for sessions"
    )
    
    secret_key: Optional[str] = Field(
        None,
        min_length=32,
        description="DEPRECATED: Use flask_secret_key instead"
    )
    
    encryption_master_key: Optional[str] = Field(
        None,
        alias="MASTER_KEY",  # Support deprecated MASTER_KEY
        min_length=32,
        description="Master encryption key for sensitive data"
    )
    
    master_key: Optional[str] = Field(
        None,
        description="DEPRECATED: Use encryption_master_key instead"
    )
    
    totp_encryption_key: Optional[str] = Field(
        default=None,
        min_length=32,
        description="Fernet encryption key for TOTP secrets"
    )
    
    cookie_secure: bool = Field(
        default=True,
        description="Enable Secure flag on authentication cookies (HTTPS-only)"
    )
    
    cookie_samesite: Literal["Strict", "Lax", "None"] = Field(
        default="Lax",
        description="SameSite attribute for authentication cookies"
    )
    
    
    database_url: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL",
        description="PostgreSQL database connection URL"
    )
    
    redis_url: Optional[str] = Field(
        default=None,
        alias="REDIS_URL",
        description="Redis connection URL for queue and caching"
    )
    
    memory_table: str = Field(
        default="memory",
        description="Supabase memory table name for vector storage"
    )
    
    supabase_db_password: Optional[str] = Field(
        None,
        description="Supabase PostgreSQL database password"
    )
    
    redis_key_prefix: str = Field(
        default="morningai",
        description="Redis key prefix for namespacing"
    )
    
    db_pool_max: int = Field(
        default=10,
        description="Maximum database connection pool size"
    )
    
    
    supabase_url: Optional[str] = Field(
        None,
        alias="SUPABASE_URL",
        description="Supabase project URL"
    )
    
    supabase_anon_key: Optional[str] = Field(
        None,
        alias="SUPABASE_ANON_KEY",
        description="Supabase anonymous/public key"
    )
    
    supabase_service_role_key: Optional[str] = Field(
        None,
        alias="SUPABASE_SERVICE_ROLE_KEY",
        description="Supabase service role key (admin access)"
    )
    
    cloudflare_api_token: Optional[str] = Field(
        None,
        description="Cloudflare API token for DNS/CDN management"
    )
    
    cloudflare_zone_id: Optional[str] = Field(
        None,
        description="Cloudflare zone ID for domain"
    )
    
    vercel_token: Optional[str] = Field(
        None,
        description="Vercel deployment token"
    )
    
    vercel_org_id: Optional[str] = Field(
        None,
        description="Vercel organization ID"
    )
    
    vercel_project_id: Optional[str] = Field(
        None,
        description="Vercel project ID"
    )
    
    vercel_team_id: Optional[str] = Field(
        None,
        description="Vercel team ID (alternative to vercel_org_id)"
    )
    
    vercel_token_new: Optional[str] = Field(
        None,
        description="New Vercel token for migration"
    )
    
    vercel_token_2: Optional[str] = Field(
        None,
        description="Secondary Vercel token for testing"
    )
    
    render_api_key: Optional[str] = Field(
        None,
        description="Render API key for deployments"
    )
    
    render_instance_id: Optional[str] = Field(
        None,
        description="Render instance ID (auto-set by Render platform)"
    )
    
    upstash_redis_rest_url: Optional[str] = Field(
        None,
        alias="UPSTASH_REDIS_REST_URL",
        description="Upstash Redis REST API URL"
    )
    
    upstash_redis_rest_token: Optional[str] = Field(
        None,
        alias="UPSTASH_REDIS_REST_TOKEN",
        description="Upstash Redis REST API token"
    )
    
    fly_api_token: Optional[str] = Field(
        None,
        description="Fly.io API token for sandbox deployments"
    )
    
    
    sentry_dsn: Optional[str] = Field(
        None,
        description="Sentry DSN for error tracking"
    )
    
    sentry_auth_token: Optional[str] = Field(
        None,
        description="Sentry authentication token for API access"
    )
    
    sentry_environment: str = Field(
        default="production",
        description="Sentry environment name"
    )
    
    sentry_enabled: bool = Field(
        default=True,
        description="Enable Sentry error tracking"
    )
    
    sentry_org: Optional[str] = Field(
        None,
        description="Sentry organization slug"
    )
    
    alert_email: Optional[str] = Field(
        None,
        description="Email address for system alerts"
    )
    
    alert_slack_channel: Optional[str] = Field(
        None,
        description="Slack channel for alerts"
    )
    
    monitor_base_url: Optional[str] = Field(
        None,
        description="Monitoring system base URL"
    )
    
    monitor_auth_token: Optional[str] = Field(
        None,
        description="Monitoring system authentication token"
    )
    
    cost_alert_threshold: float = Field(
        default=50.0,
        description="Cost alert threshold in USD"
    )
    
    latency_alert_threshold: float = Field(
        default=5000.0,
        description="Latency alert threshold in milliseconds"
    )
    
    
    github_token: Optional[str] = Field(
        None,
        alias="GITHUB_TOKEN",
        description="GitHub API token for repository operations"
    )
    
    github_repo: str = Field(
        default="RC918/morningai",
        description="GitHub repository in owner/repo format"
    )
    
    agent_github_token: Optional[str] = Field(
        None,
        description="GitHub token for agent operations"
    )
    
    openai_api_key: Optional[str] = Field(
        None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key for embeddings and LLM operations"
    )
    
    openai_max_daily_cost: float = Field(
        default=100.0,
        description="Maximum daily OpenAI API cost in USD"
    )
    
    dev_agent_model: str = Field(
        default="gpt-4",
        description="OpenAI model for dev agent"
    )
    
    dev_agent_endpoint: Optional[str] = Field(
        None,
        description="Dev agent API endpoint"
    )
    
    slack_webhook_url: Optional[str] = Field(
        None,
        description="Slack webhook URL for notifications"
    )
    
    telegram_bot_token: Optional[str] = Field(
        None,
        description="Telegram bot token for HITL approvals"
    )
    
    telegram_admin_chat_id: Optional[str] = Field(
        None,
        description="Telegram admin chat ID for notifications"
    )
    
    mcp_server_url: Optional[str] = Field(
        None,
        description="MCP (Model Context Protocol) server endpoint"
    )
    
    agent_id: Optional[str] = Field(
        None,
        description="Agent identifier for MCP operations"
    )
    
    mailtrap_api_token: Optional[str] = Field(
        None,
        alias="Mailtrap_API_TOKEN",  # Support legacy naming
        description="Mailtrap API token for email testing"
    )
    
    
    rq_queue_name: str = Field(
        default="orchestrator",
        description="Redis Queue name for task processing"
    )
    
    rq_serializer: Literal["json", "pickle"] = Field(
        default="json",
        description="RQ serializer type"
    )
    
    
    flask_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Flask environment mode"
    )
    
    environment: Literal["development", "staging", "production"] = Field(
        default="production",
        description="Deployment environment"
    )
    
    port: int = Field(
        default=5000,
        description="Application server port"
    )
    
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174",
        description="CORS allowed origins (comma-separated)"
    )
    
    app_version: str = Field(
        default="8.0.0",
        description="Application version for tracking"
    )
    
    app_phase: str = Field(
        default="Phase 8",
        description="Current application phase"
    )
    
    hostname: Optional[str] = Field(
        None,
        description="System hostname (auto-detected)"
    )
    
    orchestrator_path: str = Field(
        default="handoff/20250928/40_App/orchestrator",
        description="Path to orchestrator module"
    )
    
    orchestrator_jwt_secret: Optional[str] = Field(
        None,
        min_length=32,
        description="JWT secret for orchestrator API authentication"
    )
    
    orchestrator_cors_origins: str = Field(
        default="http://localhost:5173",
        description="CORS allowed origins for orchestrator API"
    )
    
    orchestrator_shutdown_timeout: int = Field(
        default=30,
        description="Graceful shutdown timeout in seconds"
    )
    
    orchestrator_test_mode: bool = Field(
        default=False,
        description="Enable orchestrator test mode"
    )
    
    policies_path: str = Field(
        default="policies",
        description="Path to governance policy files"
    )
    
    faq_cache_ttl: int = Field(
        default=3600,
        description="FAQ cache TTL in seconds"
    )
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application logging level"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging)"
    )
    
    
    rate_limit_requests: int = Field(
        default=100,
        description="Maximum requests per window"
    )
    
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )
    
    rate_limit_by_user: bool = Field(
        default=True,
        description="Apply rate limits per user (vs global)"
    )
    
    rate_limit_fail_fast: bool = Field(
        default=False,
        description="Fail fast on rate limit errors"
    )
    
    rate_limit_redis_max_retries: int = Field(
        default=3,
        description="Maximum Redis connection retries for rate limiting"
    )
    
    rate_limit_redis_retry_delay: int = Field(
        default=1,
        description="Delay between Redis retries in seconds"
    )
    
    
    phase7_enabled: bool = Field(
        default=True,
        description="Enable Phase 7 components"
    )
    
    ops_agent_enabled: bool = Field(
        default=True,
        description="Enable Ops Agent functionality"
    )
    
    growth_strategist_enabled: bool = Field(
        default=True,
        description="Enable Growth Strategist agent"
    )
    
    pm_agent_enabled: bool = Field(
        default=True,
        description="Enable PM Agent functionality"
    )
    
    hitl_approval_enabled: bool = Field(
        default=True,
        description="Enable HITL (Human-in-the-Loop) approval system"
    )
    
    demo_mode: bool = Field(
        default=False,
        description="Enable demo mode (limited functionality)"
    )
    
    sandbox_enabled: bool = Field(
        default=False,
        description="Enable Docker sandbox containers for agents"
    )
    
    feature_2fa_enabled: bool = Field(
        default=True,
        description="Enable Two-Factor Authentication (2FA/TOTP) feature"
    )
    
    feature_2fa_preauth: bool = Field(
        default=False,
        description="Enable Pre-Auth Token for 2FA (Week 1 - reduces password transmission)"
    )
    
    preauth_token_ttl: int = Field(
        default=300,
        description="Pre-Auth Token TTL in seconds (5 minutes default)"
    )
    
    enable_mock_users: bool = Field(
        default=False,
        description="Enable mock users for development/testing"
    )
    
    use_langgraph: bool = Field(
        default=False,
        description="Enable LangGraph orchestrator mode"
    )
    
    use_langgraph_percent: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Percentage of tasks to use LangGraph mode (0-100)"
    )
    
    allow_governance_mock: bool = Field(
        default=False,
        description="Allow mock governance for testing"
    )
    
    
    vite_api_base_url: str = Field(
        default="http://localhost:5001",
        description="Frontend API base URL"
    )
    
    vite_features: str = Field(
        default="dashboard,checkout,settings",
        description="Enabled frontend features (comma-separated)"
    )
    
    vite_sentry_dsn: Optional[str] = Field(
        None,
        description="Frontend Sentry DSN for error tracking"
    )
    
    vite_use_mock: bool = Field(
        default=False,
        description="Use mock API in frontend for development"
    )
    
    
    stripe_secret_key: Optional[str] = Field(
        None,
        description="Stripe secret key (planned for Phase 10)"
    )
    
    stripe_webhook_secret_key: Optional[str] = Field(
        None,
        alias="STRIPE_WEBHOOK_SECRET",  # Support deprecated name
        description="Stripe webhook secret key"
    )
    
    stripe_webhook_secret: Optional[str] = Field(
        None,
        description="DEPRECATED: Use stripe_webhook_secret_key instead"
    )
    
    
    test_admin_jwt: Optional[str] = Field(
        None,
        description="JWT token for E2E tests"
    )
    
    testing: bool = Field(
        default=False,
        description="Enable testing mode"
    )
    
    staging_api_url: Optional[str] = Field(
        None,
        description="Staging environment API URL"
    )
    
    staging_test_email: Optional[str] = Field(
        None,
        description="Test user email for staging environment"
    )
    
    staging_test_password: Optional[str] = Field(
        None,
        description="Test user password for staging environment"
    )
    
    
    gunicorn_workers: int = Field(
        default=4,
        description="Number of Gunicorn worker processes"
    )
    
    gunicorn_log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info",
        description="Gunicorn logging level"
    )
    
    gunicorn_reload: bool = Field(
        default=False,
        description="Enable Gunicorn auto-reload on code changes"
    )
    
    dashboard_port: int = Field(
        default=8050,
        description="Ops agent dashboard port"
    )
    
    dashboard_api_key: Optional[str] = Field(
        None,
        description="Ops agent dashboard API key"
    )
    
    allowed_origins: str = Field(
        default="http://localhost:8050",
        description="Allowed origins for ops agent dashboard"
    )
    
    workspace_path: Optional[str] = Field(
        None,
        description="Agent workspace directory path"
    )
    
    setuptools_ext_suffix: Optional[str] = Field(
        None,
        description="Setuptools extension suffix (auto-detected)"
    )
    
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.environment == "staging"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    
    @field_validator("enable_mock_users")
    @classmethod
    def validate_mock_users_production(cls, v: bool, info) -> bool:
        """Ensure mock users are disabled in production"""
        environment = info.data.get("environment", "development")
        if v and environment in ["production", "staging"]:
            raise ValueError(
                f"ENABLE_MOCK_USERS must be false in {environment} environment. "
                "Mock users are only allowed in development."
            )
        return v
    
    @field_validator("totp_encryption_key")
    @classmethod
    def validate_totp_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate TOTP encryption key format"""
        if v and len(v) < 32:
            warnings.warn(
                "TOTP_ENCRYPTION_KEY should be at least 32 characters. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'",
                UserWarning
            )
        return v
    
    @field_validator("redis_url")
    @classmethod
    def warn_non_tls_redis(cls, v: str) -> str:
        """Warn about non-TLS Redis connections"""
        if v and not v.startswith("rediss://"):
            warnings.warn(
                f"Redis URL does not use TLS (rediss://): {v}. "
                "For production, consider using UPSTASH_REDIS_REST_URL which has HTTPS/TLS by default.",
                UserWarning
            )
        return v
    
    def log_deprecation_warnings(self):
        """Log warnings for deprecated variable usage"""
        deprecated_vars = [
            ("secret_key", "flask_secret_key", "SECRET_KEY", "FLASK_SECRET_KEY"),
            ("master_key", "encryption_master_key", "MASTER_KEY", "ENCRYPTION_MASTER_KEY"),
            ("stripe_webhook_secret", "stripe_webhook_secret_key", "STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET_KEY"),
        ]
        
        for old_field, new_field, old_env, new_env in deprecated_vars:
            old_value = getattr(self, old_field, None)
            new_value = getattr(self, new_field, None)
            
            if old_value and not new_value:
                warnings.warn(
                    f"{old_env} is deprecated. Please use {new_env} instead. "
                    f"Support for {old_env} will be removed after 2025-11-30.",
                    DeprecationWarning,
                    stacklevel=2
                )


_settings_instance = None

def get_settings() -> Settings:
    """
    Get or create the global settings instance.
    
    In test mode, always creates a fresh instance to pick up environment
    variables set by tests at runtime. Test mode is detected via pytest
    in sys.modules or TESTING environment variable.
    """
    global _settings_instance
    
    is_pytest = 'pytest' in sys.modules
    is_testing_env = os.getenv('TESTING', '').lower() in ('1', 'true', 'yes')
    is_testing = is_pytest or is_testing_env
    
    if is_testing or _settings_instance is None:
        _settings_instance = Settings()
        if not is_testing:
            _settings_instance.log_deprecation_warnings()
    
    return _settings_instance

def reload_settings() -> Settings:
    """
    Reload settings from environment variables.
    
    This is primarily useful for tests that modify os.environ at runtime.
    After changing environment variables, call this function to force
    the settings instance to reload.
    
    Example:
        import os
        from common.config.settings import reload_settings
        
        os.environ['JWT_SECRET_KEY'] = 'new-test-key'
        reload_settings()  # Settings will now use the new value
    
    Returns:
        The newly created Settings instance
    """
    global _settings_instance
    _settings_instance = None
    return get_settings()

class _SettingsProxy:
    """Proxy object that lazily instantiates Settings on first access"""
    def __getattr__(self, name):
        return getattr(get_settings(), name)

settings = _SettingsProxy()


def getenv(name: str, default: str = None) -> str:
    """
    Backward compatibility wrapper for os.getenv().
    
    DEPRECATED: This function is provided for gradual migration only.
    New code should use `settings.variable_name` directly.
    
    This function will be removed in a future version.
    """
    warnings.warn(
        f"Using getenv('{name}') is deprecated. "
        f"Please use 'from common.config.settings import settings' and access settings.{name.lower()} instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return os.getenv(name, default)
