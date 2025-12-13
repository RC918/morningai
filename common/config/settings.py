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
from pydantic import Field, field_validator, model_validator, ConfigDict, SecretStr
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

    access_token_expiry_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRY_MINUTES",
        description="JWT access token expiry time in minutes (CI/E2E can override to 60)"
    )

    log_token_expiry_on_startup: bool = Field(
        default=False,
        alias="LOG_TOKEN_EXPIRY_ON_STARTUP",
        description="Enable debug logging of JWT token expiry configuration on startup"
    )

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

    owner_password_secret: Optional[SecretStr] = Field(
        None,
        alias="OWNER_PASSWORD",
        description="Owner user password for system access",
        repr=False
    )

    @property
    def owner_password(self) -> Optional[str]:
        """Owner password (unwrapped from SecretStr)"""
        return self.owner_password_secret.get_secret_value() if self.owner_password_secret else None

    flask_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="FLASK_SECRET_KEY",
        description="Flask application secret key for sessions",
        repr=False
    )

    @property
    def flask_secret_key(self) -> Optional[str]:
        """Flask secret key (unwrapped from SecretStr)"""
        return self.flask_secret_key_secret.get_secret_value() if self.flask_secret_key_secret else None

    # SECRET_KEY removed - deadline 2025-11-30 passed
    # Use FLASK_SECRET_KEY instead

    encryption_master_key_secret: Optional[SecretStr] = Field(
        None,
        alias="ENCRYPTION_MASTER_KEY",
        description="Master encryption key for sensitive data",
        repr=False
    )

    @property
    def encryption_master_key(self) -> Optional[str]:
        """Encryption master key (unwrapped from SecretStr)"""
        return self.encryption_master_key_secret.get_secret_value() if self.encryption_master_key_secret else None

    # MASTER_KEY removed - deadline 2025-11-30 passed
    # Use ENCRYPTION_MASTER_KEY instead

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
        alias="COOKIE_SECURE",
        description="Enable Secure flag on authentication cookies (HTTPS-only)"
    )

    cookie_samesite: Literal["Strict", "Lax", "None"] = Field(
        default="Lax",
        alias="COOKIE_SAMESITE",
        description="SameSite attribute for authentication cookies"
    )

    cookie_domain: Optional[str] = Field(
        default=None,
        alias="COOKIE_DOMAIN",
        description="Optional domain restriction for authentication cookies"
    )

    cookie_path: str = Field(
        default="/",
        alias="COOKIE_PATH",
        description="Path restriction for authentication cookies"
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

    redis_host: str = Field(
        default="localhost",
        alias="REDIS_HOST",
        description="Redis host for fallback connection when REDIS_URL is not set"
    )

    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        alias="REDIS_PORT",
        description="Redis port for fallback connection when REDIS_URL is not set"
    )

    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        alias="REDIS_DB",
        description="Redis database number for fallback connection when REDIS_URL is not set"
    )

    memory_table: str = Field(
        default="memory",
        alias="MEMORY_TABLE",
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
        alias="REDIS_KEY_PREFIX",
        description="Redis key prefix for namespacing"
    )

    db_pool_max: int = Field(
        default=10,
        alias="DB_POOL_MAX",
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
        alias="CLOUDFLARE_ZONE_ID",
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
        alias="VERCEL_ORG_ID",
        description="Vercel organization ID"
    )

    vercel_project_id: Optional[str] = Field(
        None,
        alias="VERCEL_PROJECT_ID",
        description="Vercel project ID"
    )

    vercel_team_id: Optional[str] = Field(
        None,
        alias="VERCEL_TEAM_ID",
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
        alias="RENDER_INSTANCE_ID",
        description="Render instance ID (auto-set by Render platform)"
    )

    git_commit: Optional[str] = Field(
        None,
        alias="GIT_COMMIT",
        description="Git commit SHA for version tracking (auto-set by CI)"
    )

    render_git_commit: Optional[str] = Field(
        None,
        alias="RENDER_GIT_COMMIT",
        description="Git commit SHA from Render platform (auto-set by Render)"
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
        alias="SENTRY_DSN",
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
        alias="SENTRY_ENVIRONMENT",
        description="Sentry environment name"
    )

    sentry_enabled: bool = Field(
        default=True,
        alias="SENTRY_ENABLED",
        description="Enable Sentry error tracking"
    )

    sentry_org: Optional[str] = Field(
        None,
        alias="SENTRY_ORG",
        description="Sentry organization slug"
    )

    sentry_project: Optional[str] = Field(
        None,
        alias="SENTRY_PROJECT",
        description="Sentry project slug"
    )

    alert_email: Optional[str] = Field(
        None,
        alias="ALERT_EMAIL",
        description="Email address for system alerts"
    )

    alert_slack_channel: Optional[str] = Field(
        None,
        alias="ALERT_SLACK_CHANNEL",
        description="Slack channel for alerts"
    )

    ops_alert_webhook_url: Optional[str] = Field(
        None,
        alias="OPS_ALERT_WEBHOOK_URL",
        description="Optional webhook URL for operational alerts (Slack/email/custom)"
    )

    monitor_base_url: Optional[str] = Field(
        None,
        alias="MONITOR_BASE_URL",
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
        alias="COST_ALERT_THRESHOLD",
        description="Cost alert threshold in USD"
    )

    latency_alert_threshold: float = Field(
        default=5000.0,
        alias="LATENCY_ALERT_THRESHOLD",
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
        alias="GITHUB_REPO",
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
        alias="OPENAI_MAX_DAILY_COST",
        description="Maximum daily OpenAI API cost in USD"
    )

    dev_agent_model: str = Field(
        default="gpt-4",
        alias="DEV_AGENT_MODEL",
        description="OpenAI model for dev agent"
    )

    dev_agent_endpoint: Optional[str] = Field(
        None,
        alias="DEV_AGENT_ENDPOINT",
        description="Dev agent API endpoint"
    )

    llm_provider: Literal["openai", "gemini", "auto"] = Field(
        default="openai",
        alias="LLM_PROVIDER",
        description="LLM provider for text generation (openai, gemini, auto)"
    )

    gemini_api_key_secret: Optional[SecretStr] = Field(
        None,
        alias="GEMINI_API_KEY",
        description="Google Gemini API key for LLM operations (Phase 2 Extra)",
        repr=False
    )

    @property
    def gemini_api_key(self) -> Optional[str]:
        """Gemini API key (unwrapped from SecretStr)"""
        return self.gemini_api_key_secret.get_secret_value() if self.gemini_api_key_secret else None

    slack_webhook_url: Optional[str] = Field(
        None,
        alias="SLACK_WEBHOOK_URL",
        description="Slack webhook URL for notifications",
        repr=False
    )

    # Webhook secrets for external service integration (#1822)
    github_webhook_secret_secret: Optional[SecretStr] = Field(
        None,
        alias="GITHUB_WEBHOOK_SECRET",
        description="GitHub webhook secret for signature validation",
        repr=False
    )

    @property
    def github_webhook_secret(self) -> Optional[str]:
        """GitHub webhook secret (unwrapped from SecretStr)"""
        return self.github_webhook_secret_secret.get_secret_value() if self.github_webhook_secret_secret else None

    jira_webhook_secret_secret: Optional[SecretStr] = Field(
        None,
        alias="JIRA_WEBHOOK_SECRET",
        description="Jira webhook secret for signature validation",
        repr=False
    )

    @property
    def jira_webhook_secret(self) -> Optional[str]:
        """Jira webhook secret (unwrapped from SecretStr)"""
        return self.jira_webhook_secret_secret.get_secret_value() if self.jira_webhook_secret_secret else None

    slack_signing_secret_secret: Optional[SecretStr] = Field(
        None,
        alias="SLACK_SIGNING_SECRET",
        description="Slack signing secret for request signature validation",
        repr=False
    )

    @property
    def slack_signing_secret(self) -> Optional[str]:
        """Slack signing secret (unwrapped from SecretStr)"""
        return self.slack_signing_secret_secret.get_secret_value() if self.slack_signing_secret_secret else None

    webhook_verify_signature: bool = Field(
        default=True,
        alias="WEBHOOK_VERIFY_SIGNATURE",
        description="Enable webhook signature verification (disable for testing)"
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
        alias="TELEGRAM_ADMIN_CHAT_ID",
        description="Telegram admin chat ID for notifications"
    )

    mcp_server_url: Optional[str] = Field(
        None,
        alias="MCP_SERVER_URL",
        description="MCP (Model Context Protocol) server endpoint"
    )

    agent_id: Optional[str] = Field(
        None,
        alias="AGENT_ID",
        description="Agent identifier for MCP operations"
    )

    mailtrap_api_token_secret: Optional[SecretStr] = Field(
        None,
        alias="MAILTRAP_API_TOKEN",
        description="Mailtrap API token for email testing",
        repr=False
    )

    @property
    def mailtrap_api_token(self) -> Optional[str]:
        """Mailtrap API token (unwrapped from SecretStr)"""
        return self.mailtrap_api_token_secret.get_secret_value() if self.mailtrap_api_token_secret else None

    rq_queue_name: str = Field(
        default="orchestrator",
        alias="RQ_QUEUE_NAME",
        description="Redis Queue name for task processing"
    )

    rq_serializer: Literal["json", "pickle"] = Field(
        default="json",
        alias="RQ_SERIALIZER",
        description="RQ serializer type"
    )

    flask_env: Literal["development", "staging", "production", "testing"] = Field(
        default="development",
        alias="FLASK_ENV",
        description="Flask environment mode"
    )

    environment: Literal["development", "staging", "production"] = Field(
        default="production",
        alias="ENVIRONMENT",
        description="Deployment environment"
    )

    port: int = Field(
        default=5000,
        alias="PORT",
        description="Application server port"
    )

    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174",
        alias="CORS_ORIGINS",
        description="CORS allowed origins (comma-separated)"
    )

    app_version: str = Field(
        default="8.0.0",
        alias="APP_VERSION",
        description="Application version for tracking"
    )

    app_phase: str = Field(
        default="Phase 8",
        alias="APP_PHASE",
        description="Current application phase"
    )

    hostname: Optional[str] = Field(
        None,
        alias="HOSTNAME",
        description="System hostname (auto-detected)"
    )

    orchestrator_path: str = Field(
        default="handoff/20250928/40_App/orchestrator",
        alias="ORCHESTRATOR_PATH",
        description="Path to orchestrator module"
    )

    orchestrator_api_url: Optional[str] = Field(
        None,
        alias="ORCHESTRATOR_API_URL",
        description="Orchestrator API URL for health monitoring"
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
        alias="ORCHESTRATOR_CORS_ORIGINS",
        description="CORS allowed origins for orchestrator API"
    )

    orchestrator_shutdown_timeout: int = Field(
        default=30,
        alias="ORCHESTRATOR_SHUTDOWN_TIMEOUT",
        description="Graceful shutdown timeout in seconds"
    )

    orchestrator_test_mode: bool = Field(
        default=True,
        alias="ORCHESTRATOR_TEST_MODE",
        description="Enable orchestrator test mode (default: True for safety, set to False for production PRs)"
    )

    orchestrator_docs_max_prs_per_hour: int = Field(
        default=3,
        alias="ORCHESTRATOR_DOCS_MAX_PRS_PER_HOUR",
        description="Maximum documentation PRs allowed per hour (default: 3 to prevent PR bombing)"
    )

    orchestrator_dry_run: bool = Field(
        default=False,
        alias="ORCHESTRATOR_DRY_RUN",
        description="Skip PR creation in orchestrator, return synthetic results. Use in staging to avoid PR bombing."
    )

    use_redis_checkpointer: bool = Field(
        default=False,
        alias="USE_REDIS_CHECKPOINTER",
        description="Use Redis-based checkpointer for LangGraph state persistence instead of in-memory MemorySaver. Enables cross-process state recovery."
    )

    use_distributed_vm_locking: bool = Field(
        default=False,
        alias="USE_DISTRIBUTED_VM_LOCKING",
        description="Use Redis-backed distributed locking for VM provisioning. Enables cross-process coordination for duplicate prevention and concurrency limits. (#2104)"
    )

    vm_lock_ttl_seconds: int = Field(
        default=300,
        alias="VM_LOCK_TTL_SECONDS",
        description="TTL in seconds for VM task locks (default: 300 = 5 minutes). Locks auto-expire to handle process crashes."
    )

    vm_registry_ttl_buffer: int = Field(
        default=300,
        alias="VM_REGISTRY_TTL_BUFFER",
        description="Additional TTL buffer in seconds for VM registry entries beyond VM timeout (default: 300 = 5 minutes)."
    )

    vm_cleanup_interval_seconds: int = Field(
        default=300,
        alias="VM_CLEANUP_INTERVAL_SECONDS",
        description="Interval in seconds for running stale VM cleanup job (default: 300 = 5 minutes). Set to 0 to disable."
    )

    redis_checkpointer_ttl: int = Field(
        default=86400,
        alias="REDIS_CHECKPOINTER_TTL",
        description="TTL in seconds for Redis checkpointer entries (default: 24 hours). Set to 0 for no expiration."
    )

    rq_max_jobs: int = Field(
        default=0,
        alias="RQ_MAX_JOBS",
        description="Max jobs before worker restart for memory management (default: 0 = unlimited). Recommended: 10-20 for LangGraph workloads to prevent OOM."
    )

    rq_job_timeout: int = Field(
        default=600,
        alias="RQ_JOB_TIMEOUT",
        description="Job timeout in seconds (default: 600 = 10 minutes). Jobs exceeding this timeout will be terminated."
    )

    rq_task_ttl: int = Field(
        default=600,
        alias="RQ_TASK_TTL",
        description="Task enqueue TTL in seconds (default: 600 = 10 minutes). Tasks not started within this time are discarded."
    )

    rq_result_ttl: int = Field(
        default=86400,
        alias="RQ_RESULT_TTL",
        description="Result retention TTL in seconds (default: 86400 = 24 hours). Successful job results are kept for this duration."
    )

    rq_failure_ttl: int = Field(
        default=3600,
        alias="RQ_FAILURE_TTL",
        description="Failure retention TTL in seconds (default: 3600 = 1 hour). Failed job records are kept for this duration."
    )

    worker_heartbeat_interval: int = Field(
        default=60,
        alias="WORKER_HEARTBEAT_INTERVAL",
        description="Worker heartbeat interval in seconds. Optimized to reduce Redis command volume."
    )

    worker_heartbeat_ttl: int = Field(
        default=180,
        alias="WORKER_HEARTBEAT_TTL",
        description="Worker heartbeat key TTL in seconds. Should be at least 3x the interval for safety margin."
    )

    policies_path: str = Field(
        default="policies",
        alias="POLICIES_PATH",
        description="Path to governance policy files"
    )

    faq_cache_ttl: int = Field(
        default=3600,
        alias="FAQ_CACHE_TTL",
        description="FAQ cache TTL in seconds"
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Application logging level"
    )

    @field_validator('log_level', mode='before')
    @classmethod
    def normalize_log_level(cls, v):
        """Normalize log level to uppercase for case-insensitive validation."""
        if isinstance(v, str):
            return v.strip().upper()
        return v

    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="Enable debug mode (verbose logging)"
    )

    rate_limit_requests: int = Field(
        default=60,
        alias="RATE_LIMIT_REQUESTS",
        description="Maximum requests per window"
    )

    rate_limit_window: int = Field(
        default=60,
        alias="RATE_LIMIT_WINDOW",
        description="Rate limit window in seconds"
    )

    rate_limit_by_user: bool = Field(
        default=True,
        alias="RATE_LIMIT_BY_USER",
        description="Apply rate limits per user (vs global)"
    )

    rate_limit_fail_fast: bool = Field(
        default=False,
        alias="RATE_LIMIT_FAIL_FAST",
        description="Fail fast on rate limit errors"
    )

    rate_limit_redis_max_retries: int = Field(
        default=3,
        alias="RATE_LIMIT_REDIS_MAX_RETRIES",
        description="Maximum Redis connection retries for rate limiting"
    )

    rate_limit_redis_retry_delay: int = Field(
        default=1,
        alias="RATE_LIMIT_REDIS_RETRY_DELAY",
        description="Delay between Redis retries in seconds"
    )

    phase7_enabled: bool = Field(
        default=True,
        alias="PHASE7_ENABLED",
        description="Enable Phase 7 components"
    )

    ops_agent_enabled: bool = Field(
        default=True,
        alias="OPS_AGENT_ENABLED",
        description="Enable Ops Agent functionality"
    )

    growth_strategist_enabled: bool = Field(
        default=True,
        alias="GROWTH_STRATEGIST_ENABLED",
        description="Enable Growth Strategist agent"
    )

    pm_agent_enabled: bool = Field(
        default=True,
        alias="PM_AGENT_ENABLED",
        description="Enable PM Agent functionality"
    )

    refactor_agent_enabled: bool = Field(
        default=True,
        alias="REFACTOR_AGENT_ENABLED",
        description="Enable Refactor Agent for automated TS strict mode fixes"
    )

    refactor_agent_errors_per_run: int = Field(
        default=10,
        alias="REFACTOR_AGENT_ERRORS_PER_RUN",
        description="Number of TS errors to fix per nightly run"
    )

    refactor_agent_auto_pr: bool = Field(
        default=False,
        alias="REFACTOR_AGENT_AUTO_PR",
        description="Automatically create PRs for refactor fixes (disabled by default, enable after staging validation)"
    )

    hitl_approval_enabled: bool = Field(
        default=True,
        alias="HITL_APPROVAL_ENABLED",
        description="Enable HITL (Human-in-the-Loop) approval system"
    )

    demo_mode: bool = Field(
        default=False,
        alias="DEMO_MODE",
        description="Enable demo mode (limited functionality)"
    )

    sandbox_enabled: bool = Field(
        default=False,
        alias="SANDBOX_ENABLED",
        description="Enable Docker sandbox containers for agents"
    )

    canary_metrics_enabled: bool = Field(
        default=True,
        alias="CANARY_METRICS_ENABLED",
        description="Enable canary deployment metrics collection"
    )

    canary_alerting_enabled: bool = Field(
        default=True,
        alias="CANARY_ALERTING_ENABLED",
        description="Enable canary SLO alerting"
    )

    canary_window_minutes: int = Field(
        default=15,
        alias="CANARY_WINDOW_MINUTES",
        description="Time window for canary SLO evaluation in minutes"
    )

    canary_p95_ms_threshold: int = Field(
        default=2500,
        alias="CANARY_P95_MS_THRESHOLD",
        description="Canary p95 latency threshold in milliseconds"
    )

    canary_5xx_rate_threshold: float = Field(
        default=1.0,
        alias="CANARY_5XX_RATE_THRESHOLD",
        description="Canary 5xx error rate threshold percentage"
    )

    canary_failure_rate_threshold: float = Field(
        default=5.0,
        alias="CANARY_FAILURE_RATE_THRESHOLD",
        description="Canary planner failure rate threshold percentage"
    )

    canary_buckets_ms: str = Field(
        default="50,100,200,400,800,1600,3200",
        alias="CANARY_BUCKETS_MS",
        description="Canary latency histogram buckets in milliseconds (comma-separated)"
    )

    feature_2fa_enabled: bool = Field(
        default=True,
        alias="FEATURE_2FA_ENABLED",
        description="Enable Two-Factor Authentication (2FA/TOTP) feature"
    )

    force_enable_2fa_in_tests: bool = Field(
        default=False,
        alias="FORCE_ENABLE_2FA_IN_TESTS",
        description="Force enable 2FA in test mode (overrides TESTING=True check)"
    )

    feature_2fa_preauth: bool = Field(
        default=False,
        alias="FEATURE_2FA_PREAUTH",
        description="Enable Pre-Auth Token for 2FA (Week 1 - reduces password transmission)"
    )

    preauth_token_ttl: int = Field(
        default=300,
        alias="PREAUTH_TOKEN_TTL",
        description="Pre-Auth Token TTL in seconds (5 minutes default)"
    )

    enable_mock_users: bool = Field(
        default=False,
        alias="ENABLE_MOCK_USERS",
        description="Enable mock users for development/testing"
    )

    use_tiktoken_estimator: bool = Field(
        default=False,
        alias="USE_TIKTOKEN_ESTIMATOR",
        description="Use tiktoken for accurate token estimation instead of heuristic"
    )

    enable_rate_limit_in_tests: bool = Field(
        default=False,
        alias="ENABLE_RATE_LIMIT_IN_TESTS",
        description="Enable rate limiting in test environment"
    )

    idempotency_tests_allowed: bool = Field(
        default=False,
        alias="IDEMPOTENCY_TESTS_ALLOWED",
        description="Allow idempotency tests to run"
    )

    enable_orchestrator: bool = Field(
        default=True,
        alias="ENABLE_ORCHESTRATOR",
        description="Enable orchestrator/agent routes (set to false in CI/E2E to bypass Redis/TLS dependencies)"
    )

    feature_cookie_auth: bool = Field(
        default=False,
        alias="FEATURE_COOKIE_AUTH",
        description="Enable cookie-based authentication (token in cookie instead of JSON body)"
    )

    use_langgraph: bool = Field(
        default=False,
        alias="USE_LANGGRAPH",
        description="Enable LangGraph orchestrator mode"
    )

    use_langgraph_percent: int = Field(
        default=0,
        ge=0,
        le=100,
        alias="USE_LANGGRAPH_PERCENT",
        description="Percentage of tasks to use LangGraph mode (0-100)"
    )

    @field_validator('use_langgraph_percent', mode='before')
    @classmethod
    def normalize_langgraph_percent(cls, v):
        if v is None:
            return 0
        if isinstance(v, str):
            v = v.strip().rstrip('%')
            try:
                v = int(float(v))
            except ValueError:
                return 0
        return max(0, min(100, int(v)))

    use_langgraph_for_faq: bool = Field(
        default=False,
        alias="USE_LANGGRAPH_FOR_FAQ",
        description="Enable LangGraph mode for FAQ tasks (default false to preserve low latency)"
    )

    use_llm_planner: bool = Field(
        default=False,
        alias="USE_LLM_PLANNER",
        description="Enable LLM-powered planner in LangGraph orchestrator (Phase 1)"
    )

    use_llm_reviewer: bool = Field(
        default=False,
        alias="USE_LLM_REVIEWER",
        description="Enable LLM-powered reviewer in LangGraph orchestrator (Phase 6 PR-3)"
    )

    # Phase 3: Reasoning mode for Gemini 3 deep thinking
    reasoning_mode_enabled: bool = Field(
        default=False,
        alias="REASONING_MODE_ENABLED",
        description="Enable reasoning mode (thinking_level=high) for Gemini 3 models in planner and reviewer. When disabled, uses thinking_level=low for faster responses."
    )

    # Phase 4: Gemini 3 kill switch for emergency rollback
    disable_gemini3: bool = Field(
        default=False,
        alias="DISABLE_GEMINI3",
        description="Emergency kill switch to disable all Gemini 3 experiments. When enabled, all traffic goes to control group (OpenAI). Use for immediate rollback if Gemini 3 causes issues."
    )

    security_enforcement_mode: Literal["advisory", "block_critical", "block_high", "block_all"] = Field(
        default="advisory",
        alias="SECURITY_ENFORCEMENT_MODE",
        description="Security policy enforcement mode for advisory nodes in LangGraph orchestrator"
    )

    reviewer_json_mode: bool = Field(
        default=True,
        alias="REVIEWER_JSON_MODE",
        description="Enable JSON mode for LLM reviewer (ensures valid JSON responses)"
    )

    planner_json_mode: bool = Field(
        default=True,
        alias="PLANNER_JSON_MODE",
        description="Enable OpenAI JSON mode for LLM planner (ensures valid JSON responses)"
    )

    planner_events_storage: Literal["db", "jsonl"] = Field(
        default="db",
        alias="PLANNER_EVENTS_STORAGE",
        description="Storage backend for planner events (db or jsonl)"
    )

    use_code_generation: bool = Field(
        default=False,
        alias="USE_CODE_GENERATION",
        description="Enable AI-powered code generation workflow (Phase 2)"
    )

    use_codegen_workflow_percent: int = Field(
        default=0,
        ge=0,
        le=100,
        alias="USE_CODEGEN_WORKFLOW_PERCENT",
        description="Percentage of tasks to use code generation workflow (0-100, for canary rollout)"
    )

    enable_project_engineer_codegen: bool = Field(
        default=False,
        alias="ENABLE_PROJECT_ENGINEER_CODEGEN",
        description="Enable ProjectEngineerAgent code generation execution mode (Phase 2 Step C)"
    )

    enable_project_engineer_fixer: bool = Field(
        default=False,
        alias="ENABLE_PROJECT_ENGINEER_FIXER",
        description="Enable ProjectEngineerAgent auto-fix mode in fixer_node (Phase 2 Step C Fixer Node)"
    )

    auto_fix_enabled: bool = Field(
        default=False,
        alias="AUTO_FIX_ENABLED",
        description="Master switch for auto-fix execution from AI reviewer comments (Issue #2251)"
    )

    auto_fix_categories: str = Field(
        default="style,documentation",
        alias="AUTO_FIX_CATEGORIES",
        description="Comma-separated list of categories allowed for auto-fix (style,documentation,bug_fix,refactor)"
    )

    auto_fix_repos_allowlist: str = Field(
        default="",
        alias="AUTO_FIX_REPOS_ALLOWLIST",
        description="Comma-separated list of repos allowed for auto-fix (empty = all repos)"
    )

    auto_fix_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="AUTO_FIX_MAX_RETRIES",
        description="Maximum auto-fix attempts per PR (1-10, default 3)"
    )

    auto_fix_per_repo_per_hour: int = Field(
        default=10,
        ge=1,
        le=100,
        alias="AUTO_FIX_PER_REPO_PER_HOUR",
        description="Maximum auto-fix attempts per repo per hour (1-100, default 10)"
    )

    auto_fix_per_pr_per_hour: int = Field(
        default=3,
        ge=1,
        le=20,
        alias="AUTO_FIX_PER_PR_PER_HOUR",
        description="Maximum auto-fix attempts per PR per hour (1-20, default 3)"
    )

    auto_fix_global_per_hour: int = Field(
        default=100,
        ge=1,
        le=1000,
        alias="AUTO_FIX_GLOBAL_PER_HOUR",
        description="Maximum global auto-fix attempts per hour (1-1000, default 100)"
    )

    auto_fix_canary_percent: int = Field(
        default=10,
        ge=0,
        le=100,
        alias="AUTO_FIX_CANARY_PERCENT",
        description="Percentage of eligible auto-fix tasks to execute (0-100, for canary rollout, Issue #2252)"
    )

    auto_fix_actor_names: str = Field(
        default="morningai-bot,auto-fix-bot,github-actions[bot]",
        alias="AUTO_FIX_ACTOR_NAMES",
        description="Comma-separated list of bot actor names for auto-fix loop protection"
    )

    auto_fix_estimated_tokens: int = Field(
        default=2000,
        ge=100,
        le=50000,
        alias="AUTO_FIX_ESTIMATED_TOKENS",
        description="Estimated tokens for auto-fix tasks (Epic #2311 runtime policy enforcement)"
    )

    meta_agent_estimated_tokens: int = Field(
        default=5000,
        ge=100,
        le=100000,
        alias="META_AGENT_ESTIMATED_TOKENS",
        description="Estimated tokens for meta-agent tasks (Epic #2311 runtime policy enforcement)"
    )

    enable_failure_learning_context: bool = Field(
        default=True,
        alias="ENABLE_FAILURE_LEARNING_CONTEXT",
        description="Enable querying past failures for learning context in Planner (Phase 2 Observer Node)"
    )

    enable_knowledge_graph_learning: bool = Field(
        default=False,
        alias="ENABLE_KNOWLEDGE_GRAPH_LEARNING",
        description="Enable querying Knowledge Graph for code patterns in Planner learning context (Tier 3 Knowledge Graph Integration)"
    )

    knowledge_graph_max_patterns: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="KNOWLEDGE_GRAPH_MAX_PATTERNS",
        description="Maximum number of Knowledge Graph patterns to include in learning context (1-10, default 3)"
    )

    # Issue #1824: DeepWiki Knowledge Base
    enable_deepwiki: bool = Field(
        default=False,
        alias="ENABLE_DEEPWIKI",
        description="Enable DeepWiki knowledge base service for code query and session insights (#1824 DeepWiki 知識庫)"
    )

    deepwiki_max_sources: int = Field(
        default=5,
        ge=1,
        le=20,
        alias="DEEPWIKI_MAX_SOURCES",
        description="Maximum number of knowledge sources to include in DeepWiki query results (1-20, default 5)"
    )

    # Phase 2 PR-1813: Agent Evaluation Integration
    enable_agent_eval: bool = Field(
        default=True,
        alias="ENABLE_AGENT_EVAL",
        description="Enable agent evaluation metrics collection and capability regression detection (Phase 2 #1813)"
    )

    agent_eval_success_rate_threshold: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        alias="AGENT_EVAL_SUCCESS_RATE_THRESHOLD",
        description="Minimum success rate threshold for capability regression detection (0-100, default 70%)"
    )

    agent_eval_ci_pass_rate_threshold: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        alias="AGENT_EVAL_CI_PASS_RATE_THRESHOLD",
        description="Minimum CI pass rate threshold for capability regression detection (0-100, default 80%)"
    )

    agent_eval_fixer_success_threshold: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        alias="AGENT_EVAL_FIXER_SUCCESS_THRESHOLD",
        description="Minimum fixer success rate threshold for self-healing detection (0-100, default 50%)"
    )

    agent_eval_baseline_sample_size: int = Field(
        default=50,
        ge=10,
        le=1000,
        alias="AGENT_EVAL_BASELINE_SAMPLE_SIZE",
        description="Number of recent metrics to use for baseline comparison (10-1000, default 50)"
    )

    agent_eval_regression_alert_enabled: bool = Field(
        default=True,
        alias="AGENT_EVAL_REGRESSION_ALERT_ENABLED",
        description="Enable alerts when capability regression is detected"
    )

    project_engineer_fixer_percent: int = Field(
        default=0,
        ge=0,
        le=100,
        alias="PROJECT_ENGINEER_FIXER_PERCENT",
        description="Percentage of tasks to use auto-fix in fixer_node (0-100, for canary rollout)"
    )

    # Phase 3 PR-4: Agent-level timeout and semantic task rules
    project_engineer_task_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=1800,
        alias="PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS",
        description="Maximum execution time for ProjectEngineerAgent.run_task() in seconds (30-1800, default 300)"
    )

    project_engineer_allowed_repos: str = Field(
        default="RC918/morningai",
        alias="PROJECT_ENGINEER_ALLOWED_REPOS",
        description="Comma-separated list of allowed repositories for ProjectEngineerAgent (e.g., 'RC918/morningai,RC918/other-repo')"
    )

    project_engineer_allowed_directories: str = Field(
        default="docs/,tests/,handoff/",
        alias="PROJECT_ENGINEER_ALLOWED_DIRECTORIES",
        description="Comma-separated list of allowed directory prefixes for code generation (e.g., 'docs/,tests/')"
    )

    # Phase 4 PR-1: Task type restrictions
    project_engineer_allowed_task_types: str = Field(
        default="",
        alias="PROJECT_ENGINEER_ALLOWED_TASK_TYPES",
        description="Comma-separated list of allowed task types for code generation (empty = all safe task types allowed)"
    )

    # Phase 1 Security Foundation: Action whitelist, sensitive file blocking, HITL
    project_engineer_allowed_actions: str = Field(
        default="read_file,write_file,create_file,list_directory,search_code,run_tests,run_lint,create_pr,add_comment,update_documentation",
        alias="PROJECT_ENGINEER_ALLOWED_ACTIONS",
        description="Comma-separated list of allowed actions for ProjectEngineerAgent (Phase 1 Security Foundation)"
    )

    # NOTE: Default value must stay in sync with SENSITIVE_FILE_PATTERNS in
    # handoff/20250928/40_App/orchestrator/project_engineer/semantic_rules.py
    # Use SENSITIVE_FILE_PATTERNS_CSV from semantic_rules.py as the source of truth
    # PR #1943 revision: Minimal blocklist - only files that should NEVER be modified
    project_engineer_blocked_files: str = Field(
        default=".key,.npmrc,.p12,.pem,.pfx,.pypirc,id_ed25519,id_rsa,private_key,secrets.yaml,secrets.yml",
        alias="PROJECT_ENGINEER_BLOCKED_FILE_PATTERNS",
        description="Comma-separated list of sensitive file patterns to block (Phase 1 Security Foundation - Minimal Blocklist)"
    )

    project_engineer_require_hitl_high_risk: bool = Field(
        default=True,
        alias="PROJECT_ENGINEER_REQUIRE_HITL_FOR_HIGH_RISK",
        description="Require Human-in-the-Loop approval for high-risk operations (Phase 1 Security Foundation)"
    )

    allow_governance_mock: bool = Field(
        default=False,
        alias="ALLOW_GOVERNANCE_MOCK",
        description="Allow mock governance for testing"
    )

    # Phase 3 #1822: Meta Agent Integration (Integrated Development Tools)
    enable_meta_agent: bool = Field(
        default=False,
        alias="ENABLE_META_AGENT",
        description="Enable Meta Agent autonomous execution path via webhooks (#1822 Integrated Development Tools)"
    )

    enable_meta_agent_vm: bool = Field(
        default=False,
        alias="ENABLE_META_AGENT_VM",
        description="Enable VM provisioning for Meta Agent isolated execution (requires ENABLE_META_AGENT=true)"
    )

    meta_agent_vm_provider: str = Field(
        default="local",
        alias="META_AGENT_VM_PROVIDER",
        description="VM provider for Meta Agent: 'local', 'docker', or 'fly' (requires ENABLE_META_AGENT_VM=true)"
    )

    # VSCode IDE CORS / iframe support (#2353)
    vscode_iframe_allowed_origins: str = Field(
        default="",
        alias="VSCODE_IFRAME_ALLOWED_ORIGINS",
        description="Comma-separated list of origins allowed to embed VSCode IDE in iframe (e.g., 'https://app.morningai.com,https://staging.morningai.com'). Empty means iframe embedding is disabled."
    )

    vscode_public_base_url: Optional[str] = Field(
        default=None,
        alias="VSCODE_PUBLIC_BASE_URL",
        description="Public base URL for VSCode IDE access (e.g., 'https://ide.morningai.com'). If not set, uses internal localhost URL."
    )

    # VSCode IDE Extension auto-install (#2353)
    vscode_default_extensions: str = Field(
        default="",
        alias="VSCODE_DEFAULT_EXTENSIONS",
        description="Comma-separated list of VS Code extension IDs to auto-install for all VSCode IDE sessions (e.g., 'ms-python.python,esbenp.prettier-vscode'). Empty string disables auto-install."
    )

    enable_visual_verification: bool = Field(
        default=False,
        alias="ENABLE_VISUAL_VERIFICATION",
        description="Enable visual verification for Meta Agent task execution using headless browser (requires ENABLE_META_AGENT=true)"
    )

    # Tier 5: Outbound Notifier Feature Flags (per-service)
    enable_github_notifications: bool = Field(
        default=False,
        alias="ENABLE_GITHUB_NOTIFICATIONS",
        description="Enable outbound notifications to GitHub (comments on issues/PRs) for Meta Agent task status"
    )

    enable_jira_notifications: bool = Field(
        default=False,
        alias="ENABLE_JIRA_NOTIFICATIONS",
        description="Enable outbound notifications to Jira (comments on issues) for Meta Agent task status"
    )

    enable_slack_notifications: bool = Field(
        default=False,
        alias="ENABLE_SLACK_NOTIFICATIONS",
        description="Enable outbound notifications to Slack (messages) for Meta Agent task status"
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
        alias="STRIPE_WEBHOOK_SECRET_KEY",
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
        alias="TESTING",
        description="Enable testing mode"
    )

    rls_tests_allowed: bool = Field(
        default=False,
        alias="RLS_TESTS_ALLOWED",
        description="Enable RLS (Row Level Security) tests with real user JWTs (MUST be true to run RLS tests)"
    )

    test_supabase_url: Optional[str] = Field(
        None,
        alias="TEST_SUPABASE_URL",
        description="Supabase URL for testing environment validation"
    )

    run_py_browser_e2e: bool = Field(
        default=False,
        alias="RUN_PY_BROWSER_E2E",
        description="Enable Playwright browser E2E tests (requires staging credentials)"
    )

    staging_api_url: Optional[str] = Field(
        None,
        alias="STAGING_API_URL",
        description="Staging environment API URL"
    )

    staging_test_email: Optional[str] = Field(
        None,
        alias="STAGING_TEST_EMAIL",
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
        alias="GUNICORN_WORKERS",
        description="Number of Gunicorn worker processes"
    )

    gunicorn_log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info",
        alias="GUNICORN_LOG_LEVEL",
        description="Gunicorn logging level"
    )

    @field_validator('gunicorn_log_level', mode='before')
    @classmethod
    def normalize_gunicorn_log_level(cls, v):
        """Normalize gunicorn log level to lowercase for case-insensitive validation."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    gunicorn_reload: bool = Field(
        default=False,
        alias="GUNICORN_RELOAD",
        description="Enable Gunicorn auto-reload on code changes"
    )

    dashboard_port: int = Field(
        default=8050,
        alias="DASHBOARD_PORT",
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
        alias="ALLOWED_ORIGINS",
        description="Allowed origins for ops agent dashboard"
    )

    workspace_path: Optional[str] = Field(
        None,
        alias="WORKSPACE_PATH",
        description="Agent workspace directory path"
    )

    repo_root_path: Optional[str] = Field(
        None,
        alias="REPO_ROOT_PATH",
        description="Repository root path"
    )

    morningai_repo_path: Optional[str] = Field(
        None,
        alias="MORNINGAI_REPO_PATH",
        description="MorningAI repository path"
    )

    setuptools_ext_suffix: Optional[str] = Field(
        None,
        alias="SETUPTOOLS_EXT_SUFFIX",
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

    @model_validator(mode="after")
    def validate_heartbeat_ttl(self) -> "Settings":
        """Ensure heartbeat TTL is at least 3x the interval for safety margin."""
        if self.worker_heartbeat_ttl < self.worker_heartbeat_interval * 3:
            warnings.warn(
                f"WORKER_HEARTBEAT_TTL ({self.worker_heartbeat_ttl}) should be at least 3x "
                f"WORKER_HEARTBEAT_INTERVAL ({self.worker_heartbeat_interval}) for safety margin. "
                f"Recommended: {self.worker_heartbeat_interval * 3}",
                UserWarning
            )
        return self

    @model_validator(mode="after")
    def validate_job_timeout_hierarchy(self) -> "Settings":
        """Ensure RQ job timeout is greater than agent-level task timeout.

        The job timeout must be greater than the agent-level timeout to allow
        for graceful cleanup and error handling. This validation warns if the
        hierarchy is violated (Phase 3 P4 #1817).
        """
        if self.rq_job_timeout <= self.project_engineer_task_timeout_seconds:
            warnings.warn(
                f"RQ_JOB_TIMEOUT ({self.rq_job_timeout}s) should be greater than "
                f"PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS ({self.project_engineer_task_timeout_seconds}s) "
                f"to allow for graceful cleanup. Recommended: {self.project_engineer_task_timeout_seconds + 60}s",
                UserWarning
            )
        return self

    def log_deprecation_warnings(self):
        """Log warnings for deprecated variable usage"""
        # SECRET_KEY and MASTER_KEY removed - deadline 2025-11-30 passed
        # Only STRIPE_WEBHOOK_SECRET remains as deprecated
        deprecated_vars = [
            ("stripe_webhook_secret", "stripe_webhook_secret_key", "STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET_KEY"),
        ]

        for old_field, new_field, old_env, new_env in deprecated_vars:
            old_value = getattr(self, old_field, None)
            new_value = getattr(self, new_field, None)

            if old_value and not new_value:
                warnings.warn(
                    f"{old_env} is deprecated. Please use {new_env} instead. "
                    f"Support for {old_env} will be removed after 2025-12-31.",
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
