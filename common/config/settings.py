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
from pydantic import Field, field_validator, ConfigDict, SecretStr
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
    
    
    jwt_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="JWT_SECRET_KEY",
        description="JWT token signing key for authentication",
        repr=False
    )
    
    @property
    def jwt_secret_key(self) -> Optional[str]:
        """JWT secret key (unwrapped from SecretStr)"""
        return self.jwt_secret_key_secret.get_secret_value() if self.jwt_secret_key_secret else None
    
    admin_password_secret: Optional[SecretStr] = Field(
        None,
        alias="ADMIN_PASSWORD",
        description="Admin user password for system access",
        repr=False
    )
    
    @property
    def admin_password(self) -> Optional[str]:
        """Admin password (unwrapped from SecretStr)"""
        return self.admin_password_secret.get_secret_value() if self.admin_password_secret else None
    
    flask_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="SECRET_KEY",
        description="Flask application secret key for sessions",
        repr=False
    )
    
    @property
    def flask_secret_key(self) -> Optional[str]:
        """Flask secret key (unwrapped from SecretStr)"""
        return self.flask_secret_key_secret.get_secret_value() if self.flask_secret_key_secret else None
    
    secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="SECRET_KEY",
        description="DEPRECATED: Use flask_secret_key instead",
        repr=False
    )
    
    @property
    def secret_key(self) -> Optional[str]:
        """Secret key (unwrapped from SecretStr) - DEPRECATED"""
        return self.secret_key_secret.get_secret_value() if self.secret_key_secret else None
    
    encryption_master_key_secret: Optional[SecretStr] = Field(
        None,
        alias="MASTER_KEY",
        description="Master encryption key for sensitive data",
        repr=False
    )
    
    @property
    def encryption_master_key(self) -> Optional[str]:
        """Encryption master key (unwrapped from SecretStr)"""
        return self.encryption_master_key_secret.get_secret_value() if self.encryption_master_key_secret else None
    
    master_key_secret: Optional[SecretStr] = Field(
        None,
        alias="MASTER_KEY",
        description="DEPRECATED: Use encryption_master_key instead",
        repr=False
    )
    
    @property
    def master_key(self) -> Optional[str]:
        """Master key (unwrapped from SecretStr) - DEPRECATED"""
        return self.master_key_secret.get_secret_value() if self.master_key_secret else None
    
    totp_encryption_key_secret: Optional[SecretStr] = Field(
        default=None,
        alias="TOTP_ENCRYPTION_KEY",
        description="Fernet encryption key for TOTP secrets",
        repr=False
    )
    
    @property
    def totp_encryption_key(self) -> Optional[str]:
        """TOTP encryption key (unwrapped from SecretStr)"""
        return self.totp_encryption_key_secret.get_secret_value() if self.totp_encryption_key_secret else None
    
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
    
    supabase_db_password_secret: Optional[SecretStr] = Field(
        None,
        alias="SUPABASE_DB_PASSWORD",
        description="Supabase PostgreSQL database password",
        repr=False
    )
    
    @property
    def supabase_db_password(self) -> Optional[str]:
        """Supabase DB password (unwrapped from SecretStr)"""
        return self.supabase_db_password_secret.get_secret_value() if self.supabase_db_password_secret else None
    
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
    
    supabase_anon_key_secret: Optional[SecretStr] = Field(
        None,
        alias="SUPABASE_ANON_KEY",
        description="Supabase anonymous/public key",
        repr=False
    )
    
    @property
    def supabase_anon_key(self) -> Optional[str]:
        """Supabase anon key (unwrapped from SecretStr)"""
        return self.supabase_anon_key_secret.get_secret_value() if self.supabase_anon_key_secret else None
    
    supabase_service_role_key_secret: Optional[SecretStr] = Field(
        None,
        alias="SUPABASE_SERVICE_ROLE_KEY",
        description="Supabase service role key (admin access)",
        repr=False
    )
    
    @property
    def supabase_service_role_key(self) -> Optional[str]:
        """Supabase service role key (unwrapped from SecretStr)"""
        return self.supabase_service_role_key_secret.get_secret_value() if self.supabase_service_role_key_secret else None
    
    cloudflare_api_token_secret: Optional[SecretStr] = Field(
        None,
        alias="CLOUDFLARE_API_TOKEN",
        description="Cloudflare API token for DNS/CDN management",
        repr=False
    )
    
    @property
    def cloudflare_api_token(self) -> Optional[str]:
        """Cloudflare API token (unwrapped from SecretStr)"""
        return self.cloudflare_api_token_secret.get_secret_value() if self.cloudflare_api_token_secret else None
    
    cloudflare_zone_id: Optional[str] = Field(
        None,
        description="Cloudflare zone ID for domain"
    )
    
    vercel_token_secret: Optional[SecretStr] = Field(
        None,
        alias="VERCEL_TOKEN",
        description="Vercel deployment token",
        repr=False
    )
    
    @property
    def vercel_token(self) -> Optional[str]:
        """Vercel token (unwrapped from SecretStr)"""
        return self.vercel_token_secret.get_secret_value() if self.vercel_token_secret else None
    
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
    
    vercel_token_new_secret: Optional[SecretStr] = Field(
        None,
        alias="VERCEL_TOKEN_NEW",
        description="New Vercel token for migration",
        repr=False
    )
    
    @property
    def vercel_token_new(self) -> Optional[str]:
        """New Vercel token (unwrapped from SecretStr)"""
        return self.vercel_token_new_secret.get_secret_value() if self.vercel_token_new_secret else None
    
    vercel_token_2_secret: Optional[SecretStr] = Field(
        None,
        alias="VERCEL_TOKEN_2",
        description="Secondary Vercel token for testing",
        repr=False
    )
    
    @property
    def vercel_token_2(self) -> Optional[str]:
        """Secondary Vercel token (unwrapped from SecretStr)"""
        return self.vercel_token_2_secret.get_secret_value() if self.vercel_token_2_secret else None
    
    render_api_key_secret: Optional[SecretStr] = Field(
        None,
        alias="RENDER_API_KEY",
        description="Render API key for deployments",
        repr=False
    )
    
    @property
    def render_api_key(self) -> Optional[str]:
        """Render API key (unwrapped from SecretStr)"""
        return self.render_api_key_secret.get_secret_value() if self.render_api_key_secret else None
    
    render_instance_id: Optional[str] = Field(
        None,
        description="Render instance ID (auto-set by Render platform)"
    )
    
    upstash_redis_rest_url: Optional[str] = Field(
        None,
        alias="UPSTASH_REDIS_REST_URL",
        description="Upstash Redis REST API URL"
    )
    
    upstash_redis_rest_token_secret: Optional[SecretStr] = Field(
        None,
        alias="UPSTASH_REDIS_REST_TOKEN",
        description="Upstash Redis REST API token",
        repr=False
    )
    
    @property
    def upstash_redis_rest_token(self) -> Optional[str]:
        """Upstash Redis REST token (unwrapped from SecretStr)"""
        return self.upstash_redis_rest_token_secret.get_secret_value() if self.upstash_redis_rest_token_secret else None
    
    fly_api_token_secret: Optional[SecretStr] = Field(
        None,
        alias="FLY_API_TOKEN",
        description="Fly.io API token for sandbox deployments",
        repr=False
    )
    
    @property
    def fly_api_token(self) -> Optional[str]:
        """Fly.io API token (unwrapped from SecretStr)"""
        return self.fly_api_token_secret.get_secret_value() if self.fly_api_token_secret else None
    
    
    sentry_dsn: Optional[str] = Field(
        None,
        description="Sentry DSN for error tracking"
    )
    
    sentry_auth_token_secret: Optional[SecretStr] = Field(
        None,
        alias="SENTRY_AUTH_TOKEN",
        description="Sentry authentication token for API access",
        repr=False
    )
    
    @property
    def sentry_auth_token(self) -> Optional[str]:
        """Sentry auth token (unwrapped from SecretStr)"""
        return self.sentry_auth_token_secret.get_secret_value() if self.sentry_auth_token_secret else None
    
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
    
    monitor_auth_token_secret: Optional[SecretStr] = Field(
        None,
        alias="MONITOR_AUTH_TOKEN",
        description="Monitoring system authentication token",
        repr=False
    )
    
    @property
    def monitor_auth_token(self) -> Optional[str]:
        """Monitor auth token (unwrapped from SecretStr)"""
        return self.monitor_auth_token_secret.get_secret_value() if self.monitor_auth_token_secret else None
    
    cost_alert_threshold: float = Field(
        default=50.0,
        description="Cost alert threshold in USD"
    )
    
    latency_alert_threshold: float = Field(
        default=5000.0,
        description="Latency alert threshold in milliseconds"
    )
    
    
    github_token_secret: Optional[SecretStr] = Field(
        None,
        alias="GITHUB_TOKEN",
        description="GitHub API token for repository operations",
        repr=False
    )
    
    @property
    def github_token(self) -> Optional[str]:
        """GitHub token (unwrapped from SecretStr)"""
        return self.github_token_secret.get_secret_value() if self.github_token_secret else None
    
    github_repo: str = Field(
        default="RC918/morningai",
        description="GitHub repository in owner/repo format"
    )
    
    agent_github_token_secret: Optional[SecretStr] = Field(
        None,
        alias="AGENT_GITHUB_TOKEN",
        description="GitHub token for agent operations",
        repr=False
    )
    
    @property
    def agent_github_token(self) -> Optional[str]:
        """Agent GitHub token (unwrapped from SecretStr)"""
        return self.agent_github_token_secret.get_secret_value() if self.agent_github_token_secret else None
    
    openai_api_key_secret: Optional[SecretStr] = Field(
        None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key for embeddings and LLM operations",
        repr=False
    )
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API key (unwrapped from SecretStr)"""
        return self.openai_api_key_secret.get_secret_value() if self.openai_api_key_secret else None
    
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
    
    telegram_bot_token_secret: Optional[SecretStr] = Field(
        None,
        alias="TELEGRAM_BOT_TOKEN",
        description="Telegram bot token for HITL approvals",
        repr=False
    )
    
    @property
    def telegram_bot_token(self) -> Optional[str]:
        """Telegram bot token (unwrapped from SecretStr)"""
        return self.telegram_bot_token_secret.get_secret_value() if self.telegram_bot_token_secret else None
    
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
    
    mailtrap_api_token_secret: Optional[SecretStr] = Field(
        None,
        alias="Mailtrap_API_TOKEN",
        description="Mailtrap API token for email testing",
        repr=False
    )
    
    @property
    def mailtrap_api_token(self) -> Optional[str]:
        """Mailtrap API token (unwrapped from SecretStr)"""
        return self.mailtrap_api_token_secret.get_secret_value() if self.mailtrap_api_token_secret else None
    
    
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
    
    orchestrator_jwt_secret_secret: Optional[SecretStr] = Field(
        None,
        alias="ORCHESTRATOR_JWT_SECRET",
        description="JWT secret for orchestrator API authentication",
        repr=False
    )
    
    @property
    def orchestrator_jwt_secret(self) -> Optional[str]:
        """Orchestrator JWT secret (unwrapped from SecretStr)"""
        return self.orchestrator_jwt_secret_secret.get_secret_value() if self.orchestrator_jwt_secret_secret else None
    
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
    
    
    stripe_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="STRIPE_SECRET_KEY",
        description="Stripe secret key (planned for Phase 10)",
        repr=False
    )
    
    @property
    def stripe_secret_key(self) -> Optional[str]:
        """Stripe secret key (unwrapped from SecretStr)"""
        return self.stripe_secret_key_secret.get_secret_value() if self.stripe_secret_key_secret else None
    
    stripe_webhook_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="STRIPE_WEBHOOK_SECRET",
        description="Stripe webhook secret key",
        repr=False
    )
    
    @property
    def stripe_webhook_secret_key(self) -> Optional[str]:
        """Stripe webhook secret key (unwrapped from SecretStr)"""
        return self.stripe_webhook_secret_key_secret.get_secret_value() if self.stripe_webhook_secret_key_secret else None
    
    stripe_webhook_secret_secret: Optional[SecretStr] = Field(
        None,
        alias="STRIPE_WEBHOOK_SECRET",
        description="DEPRECATED: Use stripe_webhook_secret_key instead",
        repr=False
    )
    
    @property
    def stripe_webhook_secret(self) -> Optional[str]:
        """Stripe webhook secret (unwrapped from SecretStr) - DEPRECATED"""
        return self.stripe_webhook_secret_secret.get_secret_value() if self.stripe_webhook_secret_secret else None
    
    
    test_admin_jwt_secret: Optional[SecretStr] = Field(
        None,
        alias="TEST_ADMIN_JWT",
        description="JWT token for E2E tests",
        repr=False
    )
    
    @property
    def test_admin_jwt(self) -> Optional[str]:
        """Test admin JWT (unwrapped from SecretStr)"""
        return self.test_admin_jwt_secret.get_secret_value() if self.test_admin_jwt_secret else None
    
    testing: bool = Field(
        default=False,
        description="Enable testing mode"
    )
    
    run_py_browser_e2e: bool = Field(
        default=False,
        alias="RUN_PY_BROWSER_E2E",
        description="Enable Playwright browser E2E tests (requires staging credentials)"
    )
    
    staging_api_url: Optional[str] = Field(
        None,
        description="Staging environment API URL"
    )
    
    staging_test_email: Optional[str] = Field(
        None,
        description="Test user email for staging environment"
    )
    
    staging_test_password_secret: Optional[SecretStr] = Field(
        None,
        alias="STAGING_TEST_PASSWORD",
        description="Test user password for staging environment",
        repr=False
    )
    
    @property
    def staging_test_password(self) -> Optional[str]:
        """Staging test password (unwrapped from SecretStr)"""
        return self.staging_test_password_secret.get_secret_value() if self.staging_test_password_secret else None
    
    
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
    
    dashboard_api_key_secret: Optional[SecretStr] = Field(
        None,
        alias="DASHBOARD_API_KEY",
        description="Ops agent dashboard API key",
        repr=False
    )
    
    @property
    def dashboard_api_key(self) -> Optional[str]:
        """Dashboard API key (unwrapped from SecretStr)"""
        return self.dashboard_api_key_secret.get_secret_value() if self.dashboard_api_key_secret else None
    
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
    
    @field_validator("totp_encryption_key_secret", mode="after")
    @classmethod
    def validate_totp_key(cls, v: Optional[SecretStr]) -> Optional[SecretStr]:
        """Validate TOTP encryption key format"""
        if v:
            raw = v.get_secret_value()
            if raw and len(raw) < 32:
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
