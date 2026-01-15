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
from typing import Optional, Literal, Tuple
from pydantic import Field, field_validator, model_validator, ConfigDict, SecretStr
from pydantic_settings import BaseSettings


# =============================================================================
# Provider Configuration - Single Source of Truth
# =============================================================================
# This is the authoritative list of valid LLM providers in MorningAI.
# All provider validation should reference this constant.
#
# To add a new provider:
# 1. Add to VALID_PROVIDERS tuple below
# 2. Add corresponding API key field in Settings class
# 3. Update env.schema.yaml LLM_PROVIDER choices
# 4. Update ROUTING_ALLOWED_PROVIDERS documentation
# =============================================================================

VALID_PROVIDERS: Tuple[str, ...] = ("openai", "gemini", "alicloud", "siliconflow")
"""
Tuple of valid LLM provider names.

Used for:
- LLM_PROVIDER validation (with 'auto' option)
- ROUTING_ALLOWED_PROVIDERS parsing
- Provider health endpoint validation
- Routing engine provider filtering
"""


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

    llm_test_generator_model: str = Field(
        default="qwen-max",
        alias="LLM_TEST_GENERATOR_MODEL",
        description="Model for LLM test generator (defaults to qwen-max for Alicloud)"
    )

    dev_agent_endpoint: Optional[str] = Field(
        None,
        alias="DEV_AGENT_ENDPOINT",
        description="Dev agent API endpoint"
    )

    llm_provider: Literal["openai", "gemini", "alicloud", "siliconflow", "auto"] = Field(
        default="auto",
        alias="LLM_PROVIDER",
        description="LLM provider for text generation (openai, gemini, alicloud, siliconflow, auto). Auto selects Qwen-first."
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

    dashscope_api_key_secret: Optional[SecretStr] = Field(
        None,
        alias="DASHSCOPE_API_KEY",
        description="AliCloud DashScope API key for Qwen models (EPIC #2594)",
        repr=False
    )

    @property
    def dashscope_api_key(self) -> Optional[str]:
        """DashScope API key (unwrapped from SecretStr)"""
        return self.dashscope_api_key_secret.get_secret_value() if self.dashscope_api_key_secret else None

    siliconflow_api_key_secret: Optional[SecretStr] = Field(
        None,
        alias="SILICONFLOW_API_KEY",
        description="SiliconFlow API key for Qwen models (EPIC #2594)",
        repr=False
    )

    @property
    def siliconflow_api_key(self) -> Optional[str]:
        """SiliconFlow API key (unwrapped from SecretStr)"""
        return self.siliconflow_api_key_secret.get_secret_value() if self.siliconflow_api_key_secret else None

    dashscope_base_url: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL",
        description="AliCloud DashScope API base URL - international endpoint (EPIC #2594)"
    )

    siliconflow_base_url: str = Field(
        default="https://api.siliconflow.cn/v1",
        alias="SILICONFLOW_BASE_URL",
        description="SiliconFlow API base URL (EPIC #2594)"
    )

    routing_allowed_providers: str = Field(
        default="",
        alias="ROUTING_ALLOWED_PROVIDERS",
        description="Comma-separated allowlist of providers for LLM routing (governance control)"
    )

    # Issue #3377: Configurable workflow patterns for CI log fetching
    ci_workflow_patterns: str = Field(
        default="test,ci",
        alias="CI_WORKFLOW_PATTERNS",
        description="Comma-separated patterns to match CI workflow names for log fetching (Issue #3377)"
    )

    # Issue #3378: Configurable job patterns for CI log fetching
    ci_job_patterns: str = Field(
        default="orchestrator&test,test",
        alias="CI_JOB_PATTERNS",
        description="Comma-separated patterns to match CI job names for log fetching. Use & for AND (Issue #3378)"
    )

    # EPIC I-1: Runtime Drift Detection(Blueprint 4.3 - Model Governance Framework v2)
    drift_detection_enabled: bool = Field(
        default=False,
        alias="DRIFT_DETECTION_ENABLED",
        description="Enable runtime drift detection for LLM responses (EPIC I-1)"
    )

    drift_detection_block_on_fail: bool = Field(
        default=False,
        alias="DRIFT_DETECTION_BLOCK_ON_FAIL",
        description="Block LLM requests when drift detection fails (EPIC I-1)"
    )

    drift_detection_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        alias="DRIFT_DETECTION_SAMPLE_RATE",
        description="Sample rate for drift detection (0.0-1.0) (EPIC I-1)"
    )

    # EPIC I-2b: Drift-Triggered Retry (Blueprint 4.3 - Model Governance Framework v2)
    drift_retry_enabled: bool = Field(
        default=False,
        alias="DRIFT_RETRY_ENABLED",
        description="Enable drift-triggered retry with higher-tier model (EPIC I-2b)"
    )

    drift_retry_max_retries: int = Field(
        default=1,
        ge=0,
        le=2,
        alias="DRIFT_RETRY_MAX_RETRIES",
        description="Maximum retry attempts per request (EPIC I-2b)"
    )

    drift_retry_eligible_drift_types: str = Field(
        default="json_parse_error,schema_violation,empty_response",
        alias="DRIFT_RETRY_ELIGIBLE_DRIFT_TYPES",
        description="Comma-separated drift types eligible for retry (EPIC I-2b)"
    )

    drift_retry_model_tier: str = Field(
        default="higher",
        alias="DRIFT_RETRY_MODEL_TIER",
        description="Model tier for retry: same, higher, highest (EPIC I-2b)"
    )

    drift_retry_cost_cap_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        alias="DRIFT_RETRY_COST_CAP_MULTIPLIER",
        description="Maximum cost increase allowed for retry (EPIC I-2b)"
    )

    drift_retry_eligible_task_types: str = Field(
        default="code_generation,code_review",
        alias="DRIFT_RETRY_ELIGIBLE_TASK_TYPES",
        description="Comma-separated task types eligible for retry (EPIC I-2b)"
    )

    # EPIC I-2: Provider Health Scoring (Blueprint 4.3 - Model Governance Framework v2)
    provider_health_enabled: bool = Field(
        default=True,
        alias="PROVIDER_HEALTH_ENABLED",
        description="Enable provider health scoring metrics collection (EPIC I-2)"
    )

    provider_health_window_minutes: int = Field(
        default=15,
        ge=1,
        le=60,
        alias="PROVIDER_HEALTH_WINDOW_MINUTES",
        description="Time window in minutes for health score calculation (EPIC I-2)"
    )

    provider_health_latency_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        alias="PROVIDER_HEALTH_LATENCY_WEIGHT",
        description="Weight for latency in health score calculation (EPIC I-2)"
    )

    provider_health_error_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        alias="PROVIDER_HEALTH_ERROR_WEIGHT",
        description="Weight for error rate in health score calculation (EPIC I-2)"
    )

    provider_health_drift_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        alias="PROVIDER_HEALTH_DRIFT_WEIGHT",
        description="Weight for drift rate in health score calculation (EPIC I-2)"
    )

    # EPIC I-3a: Health Alerting (Blueprint 4.3 - Model Governance Framework v2)
    health_alerting_enabled: bool = Field(
        default=False,
        alias="HEALTH_ALERTING_ENABLED",
        description="Enable provider health alerting (EPIC I-3a)"
    )

    health_alert_threshold: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        alias="HEALTH_ALERT_THRESHOLD",
        description="Health score threshold below which alerts are triggered (EPIC I-3a)"
    )

    health_alert_cooldown_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        alias="HEALTH_ALERT_COOLDOWN_MINUTES",
        description="Cooldown period between alerts for the same provider (EPIC I-3a)"
    )

    health_alert_min_requests: int = Field(
        default=10,
        ge=1,
        le=1000,
        alias="HEALTH_ALERT_MIN_REQUESTS",
        description="Minimum requests in window before alerting (prevents noise) (EPIC I-3a)"
    )

    health_alert_error_rate_threshold: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        alias="HEALTH_ALERT_ERROR_RATE_THRESHOLD",
        description="Error rate threshold (%) that triggers immediate alert (EPIC I-3a)"
    )

    # EPIC I-4: Auto-Degradation Advisory (Blueprint 4.3 - Model Governance Framework v2)
    degradation_advisory_enabled: bool = Field(
        default=False,
        alias="DEGRADATION_ADVISORY_ENABLED",
        description="Enable degradation advisory system (EPIC I-4 Phase A, observe-only)"
    )

    # EPIC I-4 Phase B: Degradation Enforcement (Hard Gating)
    degradation_enforcement_enabled: bool = Field(
        default=False,
        alias="DEGRADATION_ENFORCEMENT_ENABLED",
        description="Enable degradation enforcement (EPIC I-4 Phase B). When enabled, AVOID providers are filtered from available providers. Requires DEGRADATION_ADVISORY_ENABLED=true."
    )

    degradation_healthy_threshold: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
        alias="DEGRADATION_HEALTHY_THRESHOLD",
        description="Health score threshold for HEALTHY status (EPIC I-4)"
    )

    degradation_degraded_threshold: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        alias="DEGRADATION_DEGRADED_THRESHOLD",
        description="Health score threshold for DEGRADED status (EPIC I-4)"
    )

    degradation_critical_threshold: float = Field(
        default=25.0,
        ge=0.0,
        le=100.0,
        alias="DEGRADATION_CRITICAL_THRESHOLD",
        description="Health score threshold for CRITICAL status (EPIC I-4)"
    )

    degradation_recovery_buffer: float = Field(
        default=10.0,
        ge=0.0,
        le=50.0,
        alias="DEGRADATION_RECOVERY_BUFFER",
        description="Additional score required for recovery (hysteresis) (EPIC I-4)"
    )

    degradation_cooldown_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        alias="DEGRADATION_COOLDOWN_MINUTES",
        description="Cooldown period between advisories for the same provider (EPIC I-4)"
    )

    degradation_min_requests: int = Field(
        default=10,
        ge=1,
        le=1000,
        alias="DEGRADATION_MIN_REQUESTS",
        description="Minimum requests in window before advisory (EPIC I-4)"
    )

    degradation_floor_provider_count: int = Field(
        default=1,
        ge=0,
        le=10,
        alias="DEGRADATION_FLOOR_PROVIDER_COUNT",
        description="Minimum providers to keep at non-AVOID status (floor protection) (EPIC I-4)"
    )

    degradation_floor_strategy: str = Field(
        default="hybrid",
        alias="DEGRADATION_FLOOR_STRATEGY",
        description="Floor provider selection strategy: 'fixed' (always use fixed provider), 'dynamic' (select healthiest), 'hybrid' (dynamic with stickiness and fallback) (EPIC I-4)"
    )

    degradation_fixed_floor_provider: str = Field(
        default="openai",
        alias="DEGRADATION_FIXED_FLOOR_PROVIDER",
        description="Fixed floor provider for 'fixed' strategy or fallback for 'hybrid' strategy (EPIC I-4)"
    )

    degradation_floor_switch_margin: float = Field(
        default=10.0,
        ge=0.0,
        le=50.0,
        alias="DEGRADATION_FLOOR_SWITCH_MARGIN",
        description="Score margin required to switch floor provider in 'hybrid' strategy (stickiness) (EPIC I-4)"
    )

    degradation_floor_min_requests: int = Field(
        default=10,
        ge=1,
        le=1000,
        alias="DEGRADATION_FLOOR_MIN_REQUESTS",
        description="Minimum requests required for a provider to be considered as floor candidate (EPIC I-4)"
    )

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

    orchestrator_recursion_limit: int = Field(
        default=100,
        ge=5,
        le=200,
        alias="ORCHESTRATOR_RECURSION_LIMIT",
        description="Maximum number of LangGraph workflow steps before forced termination. "
                    "Prevents runaway workflows from infinite loops or excessive checkpoint writes. "
                    "Default: 100 (sufficient for SeniorCoder three-stage supervisor pattern). "
                    "Issue #3366: Increased from 30 to 100 for D-2b SeniorCoder integration. "
                    "Blueprint: Flow Controller v3 Fail-Fast Recovery."
    )

    worker_drain_mode: bool = Field(
        default=False,
        alias="WORKER_DRAIN_MODE",
        description="When True, NEW worker instances exit immediately without consuming jobs. "
                    "Note: This does NOT stop in-progress jobs on already-running workers. "
                    "See runbook for full DB maintenance procedure. "
                    "Blueprint: Flow Controller v3 Operational Control."
    )

    # Value Gate Settings (Publisher Node Governance)
    # Blueprint: Flow Controller v3 + Safety Governor v2
    enable_value_gate: bool = Field(
        default=True,
        alias="ENABLE_VALUE_GATE",
        description="Enable Value Gate to prevent low-significance PRs. Part of Publisher Node governance."
    )

    value_gate_min_score: int = Field(
        default=30,
        ge=0,
        le=100,
        alias="VALUE_GATE_MIN_SCORE",
        description="Minimum significance score (0-100) required to create a PR. Changes below this threshold are logged only."
    )

    value_gate_dry_run: bool = Field(
        default=False,
        alias="VALUE_GATE_DRY_RUN",
        description="Log-only mode for Value Gate. When True, logs what would be blocked but allows PR creation. Default changed from True to False (Dec 2025) for Secure by Default. Set VALUE_GATE_DRY_RUN=true to restore old behavior."
    )

    # PR Deduplication Settings (Memory v2 Short-term)
    # Blueprint: Memory v2 Layer 1 (Short-term Memory)
    enable_pr_deduplication: bool = Field(
        default=True,
        alias="ENABLE_PR_DEDUPLICATION",
        description="Enable PR deduplication to prevent duplicate/similar PRs. Part of Memory v2 short-term layer."
    )

    pr_dedup_window_seconds: int = Field(
        default=3600,
        ge=60,
        alias="PR_DEDUP_WINDOW_SECONDS",
        description="Time window in seconds for PR deduplication check (default: 3600 = 1 hour)."
    )

    pr_dedup_similarity_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        alias="PR_DEDUP_SIMILARITY_THRESHOLD",
        description="Similarity threshold (0.0-1.0) for semantic/path deduplication. Higher = stricter matching."
    )

    pr_dedup_dry_run: bool = Field(
        default=True,
        alias="PR_DEDUP_DRY_RUN",
        description="Log-only mode for PR deduplication. When True, logs duplicates but allows PR creation."
    )

    pr_dedup_lease_ttl_seconds: int = Field(
        default=300,
        ge=60,
        alias="PR_DEDUP_LEASE_TTL_SECONDS",
        description="TTL in seconds for atomic PR creation lease. Prevents race condition duplicates. (default: 300 = 5 min)"
    )

    # Issue #2872: Add LIMIT to zrangebyscore for performance
    pr_dedup_max_records: int = Field(
        default=100,
        ge=10,
        le=1000,
        alias="PR_DEDUP_MAX_RECORDS",
        description="Maximum number of PR records to fetch during deduplication check (default: 100). Limits memory usage for high-volume repos."
    )

    # Issue #2933: Make fail-open alert thresholds configurable
    fail_open_alert_threshold: int = Field(
        default=5,
        ge=1,
        le=100,
        alias="FAIL_OPEN_ALERT_THRESHOLD",
        description="Number of fail-open events that trigger an alert (default: 5). Adjust based on Redis stability and traffic."
    )

    fail_open_alert_window_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        alias="FAIL_OPEN_ALERT_WINDOW_MINUTES",
        description="Time window in minutes for counting fail-open events (default: 5). Longer windows smooth out transient spikes."
    )

    # Issue #2873: Make security keywords configurable
    security_keywords: str = Field(
        default="auth,permission,secret,credential,token,password,api_key",
        alias="SECURITY_KEYWORDS",
        description="Comma-separated list of security-related keywords for risk detection in PM Agent and changeset analysis."
    )

    # Docs Digest Strategy Settings (Layer 2 Value Gate)
    # Blueprint: Flow Controller v3 + Safety Governor v2
    # Issue #3087: Implement Docs Digest Strategy
    docs_digest_enabled: bool = Field(
        default=False,
        alias="DOCS_DIGEST_ENABLED",
        description="Enable Docs Digest Strategy to accumulate blocked changes and create periodic summary PRs. Default is False (disabled)."
    )

    docs_digest_count_threshold: int = Field(
        default=5,
        ge=1,
        le=50,
        alias="DOCS_DIGEST_COUNT_THRESHOLD",
        description="Number of blocked changes needed to trigger a digest PR (default: 5)."
    )

    docs_digest_flush_hour_utc: int = Field(
        default=0,
        ge=0,
        le=23,
        alias="DOCS_DIGEST_FLUSH_HOUR_UTC",
        description="Hour (0-23 UTC) for daily digest flush. Uses opportunistic triggering (default: 0 = midnight UTC)."
    )

    docs_digest_lock_ttl_seconds: int = Field(
        default=600,
        ge=60,
        le=1800,
        alias="DOCS_DIGEST_LOCK_TTL_SECONDS",
        description="TTL in seconds for distributed lock during digest flush (default: 600 = 10 min)."
    )

    docs_digest_max_items: int = Field(
        default=50,
        ge=10,
        le=200,
        alias="DOCS_DIGEST_MAX_ITEMS",
        description="Maximum number of blocked changes to accumulate before rejecting new ones (default: 50)."
    )

    # Issue #2874: Routing engine candidate selection weights
    routing_cost_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        alias="ROUTING_COST_WEIGHT",
        description="Weight for cost factor in model selection (0-1). Higher values prefer cheaper providers."
    )

    routing_preference_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        alias="ROUTING_PREFERENCE_WEIGHT",
        description="Weight for provider preference in model selection (0-1). Higher values prefer configured provider order."
    )

    # Cost Optimization: Escalation Ladder Hard Cap
    # Prevents runaway costs from unlimited tier escalation
    routing_max_escalations: int = Field(
        default=1,
        ge=0,
        le=3,
        alias="ROUTING_MAX_ESCALATIONS",
        description="Maximum number of tier escalations allowed per task (0-3). Default: 1. Set to 0 to disable escalation entirely."
    )

    routing_max_retries: int = Field(
        default=2,
        ge=1,
        le=5,
        alias="ROUTING_MAX_RETRIES",
        description="Maximum number of retries allowed per task (1-5). Default: 2. When exceeded, RoutingEngine returns the lowest-cost available model (starting from Tier 3, falling back upward if unavailable) instead of failing. This ensures graceful degradation during cost control."
    )

    routing_default_tier: int = Field(
        default=2,
        ge=0,
        le=3,
        alias="ROUTING_DEFAULT_TIER",
        description="Default tier for tasks without explicit routing config (0-3). Default: 2 (Tier 2 = qwen-turbo). Lower tiers are more expensive."
    )

    routing_force_tier_floor: bool = Field(
        default=True,
        alias="ROUTING_FORCE_TIER_FLOOR",
        description="If true, tasks cannot escalate below the minimum tier (Tier 2) unless explicitly marked as high-risk. This forces 90%+ traffic to Tier 2-3."
    )

    routing_tier_floor: int = Field(
        default=2,
        ge=0,
        le=3,
        alias="ROUTING_TIER_FLOOR",
        description="Minimum tier floor (0-3). Tasks cannot escalate below this tier unless high-risk. Default: 2."
    )

    # Issue #3234: Configurable auto-fix confidence threshold (EPIC D)
    autofix_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        alias="AUTOFIX_CONFIDENCE_THRESHOLD",
        description="Minimum confidence score (0.0-1.0) for auto-fix eligibility. Suggestions with confidence >= this threshold are considered 'high confidence' and eligible for auto-fix. Default: 0.8"
    )

    use_redis_checkpointer: bool = Field(
        default=False,
        alias="USE_REDIS_CHECKPOINTER",
        description="Use Redis-based checkpointer for LangGraph state persistence instead of in-memory MemorySaver. Enables cross-process state recovery."
    )

    use_postgres_checkpointer: bool = Field(
        default=False,
        alias="USE_POSTGRES_CHECKPOINTER",
        description="Use PostgreSQL-based checkpointer for LangGraph state persistence. Recommended over Redis for Upstash (which doesn't support RediSearch). Requires DATABASE_URL."
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

    enable_checkpoint_failover: bool = Field(
        default=True,
        alias="ENABLE_CHECKPOINT_FAILOVER",
        description="Enable automatic failover to MemorySaver when PostgreSQL checkpointer fails at runtime. "
                    "Implements 'soft landing' resilience: workflow continues with degraded persistence instead of failing. "
                    "Set to False to fail-fast on checkpoint errors. (Blueprint: Fail-Fast Recovery)"
    )

    checkpoint_retry_log_sample_rate: int = Field(
        default=1,
        ge=1,
        le=1000,
        alias="CHECKPOINT_RETRY_LOG_SAMPLE_RATE",
        description="Sample rate for retry warning logs during transient errors. "
                    "1 = log every retry (default), 10 = log every 10th retry. "
                    "First and last retries are always logged regardless of this setting. "
                    "Higher values reduce log noise during prolonged outages. (Issue #3109)"
    )

    # Issue #3027: MemorySaver OOM Protection Settings
    max_degraded_workflows_per_worker: int = Field(
        default=100,
        ge=1,
        le=10000,
        alias="MAX_DEGRADED_WORKFLOWS_PER_WORKER",
        description="Maximum number of concurrent degraded workflows per worker. "
                    "When PostgreSQL fails and workflows degrade to MemorySaver, this limit "
                    "prevents OOM by rejecting new workflows when capacity is reached. "
                    "Set based on worker memory and average checkpoint size. (Issue #3027)"
    )

    degraded_checkpoint_memory_warning_mb: int = Field(
        default=512,
        ge=64,
        le=8192,
        alias="DEGRADED_CHECKPOINT_MEMORY_WARNING_MB",
        description="Memory usage threshold in MB for degraded checkpointer warnings. "
                    "When MemorySaver memory usage exceeds this threshold, a warning is logged. "
                    "This is an early warning signal before OOM occurs. (Issue #3027)"
    )

    # Issue #3027: Hard Memory Limit for OOM Protection (Dec 2025)
    degraded_checkpoint_memory_hard_limit_mb: int = Field(
        default=1024,
        ge=128,
        le=16384,
        alias="DEGRADED_CHECKPOINT_MEMORY_HARD_LIMIT_MB",
        description="Hard memory limit in MB for degraded checkpointer. "
                    "When MemorySaver memory usage exceeds this threshold, the task is terminated "
                    "with DegradedCheckpointerMemoryExceeded exception to protect the worker. "
                    "This is the 'safety airbag' that prevents OOM kills. (Issue #3027)"
    )

    # Issue #3027: Checkpoint Eviction (LRU) for OOM Protection (Dec 2025)
    degraded_checkpoint_max_per_thread: int = Field(
        default=10,
        ge=1,
        le=100,
        alias="DEGRADED_CHECKPOINT_MAX_PER_THREAD",
        description="Maximum number of checkpoints to retain per thread in degraded mode. "
                    "When exceeded, oldest checkpoints are evicted (LRU policy). "
                    "Prevents unbounded checkpoint growth in MemorySaver. (Issue #3027)"
    )

    # Issue #3027: Message Window Size for OOM Protection (Dec 2025)
    message_window_size: int = Field(
        default=30,
        ge=5,
        le=200,
        alias="MESSAGE_WINDOW_SIZE",
        description="Maximum number of non-system messages to retain in AgentState. "
                    "When exceeded, oldest messages are pruned (keeping SystemMessage + last K). "
                    "This is a global limit that applies to both Postgres and MemorySaver modes. "
                    "Prevents unbounded message accumulation and reduces checkpoint size. (Issue #3027)"
    )

    # Issue #2259: Review Follow-up Task Storage Settings
    review_follow_up_store_backend: str = Field(
        default="in_memory",
        alias="REVIEW_FOLLOW_UP_STORE_BACKEND",
        description="Backend for review follow-up task storage: 'in_memory' (default) or 'redis'. Use 'redis' for multi-worker consistency and restart durability."
    )

    review_follow_up_task_ttl: int = Field(
        default=30 * 24 * 60 * 60,  # 30 days in seconds
        alias="REVIEW_FOLLOW_UP_TASK_TTL",
        description="TTL in seconds for review follow-up tasks in Redis (default: 2592000 = 30 days). Only applies when using Redis backend."
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

    # Issue #3581: Longer timeout for CI failure auto-fix tasks
    # CI failure auto-fix involves multiple LLM calls (classification, code generation, review)
    # and can take longer than regular tasks. Default: 1800 seconds = 30 minutes.
    rq_ci_autofix_timeout: int = Field(
        default=1800,
        alias="RQ_CI_AUTOFIX_TIMEOUT",
        description="Job timeout for CI failure auto-fix tasks in seconds (default: 1800 = 30 minutes). These tasks involve multiple LLM calls and need longer timeout."
    )

    # Issue #3581: Timeout for individual LLM calls during code generation
    # The OpenAI v1 SDK uses httpx with a default timeout of 600 seconds, which was
    # causing code generation to appear to hang for 10+ minutes before the RQ worker
    # was killed. Default: 120 seconds = 2 minutes per LLM call.
    codegen_llm_timeout_seconds: int = Field(
        default=120,
        alias="CODEGEN_LLM_TIMEOUT_SECONDS",
        description="Timeout in seconds for individual LLM calls during code generation (default: 120 = 2 minutes). Prevents SimpleLLM from hanging on slow OpenAI responses."
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

    redis_readonly_sleep_seconds: int = Field(
        default=15,
        alias="REDIS_READONLY_SLEEP_SECONDS",
        description="Sleep duration in seconds when Redis is in read-only mode during maintenance."
    )

    redis_readonly_max_retries: int = Field(
        default=20,
        alias="REDIS_READONLY_MAX_RETRIES",
        description="Maximum consecutive retries when Redis is in read-only mode. After this, worker exits to trigger restart."
    )

    # Issue #3229: commit_file() Retry Policy Configuration
    commit_file_max_retries: int = Field(
        default=3,
        alias="COMMIT_FILE_MAX_RETRIES",
        description="Maximum retry attempts for transient GitHub API errors in commit_file() (default: 3)."
    )

    commit_file_initial_delay: float = Field(
        default=2.0,
        alias="COMMIT_FILE_INITIAL_DELAY",
        description="Initial delay in seconds before first retry in commit_file() (default: 2.0)."
    )

    commit_file_backoff_factor: float = Field(
        default=2.0,
        alias="COMMIT_FILE_BACKOFF_FACTOR",
        description="Exponential backoff multiplier for commit_file() retries (default: 2.0). Delay doubles each retry."
    )

    commit_file_max_total_time: float = Field(
        default=30.0,
        alias="COMMIT_FILE_MAX_TOTAL_TIME",
        description="Maximum total time budget in seconds for all commit_file() retries (default: 30.0). Prevents unbounded retry loops."
    )

    commit_file_jitter_factor: float = Field(
        default=0.25,
        alias="COMMIT_FILE_JITTER_FACTOR",
        description="Jitter factor for commit_file() retry delays (default: 0.25). Adds random ±25% to delay to avoid thundering herd."
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

    cors_debug: bool = Field(
        default=False,
        alias="CORS_DEBUG",
        description="Enable CORS debug logging (only effective in non-production environments)"
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

    # USE_LANGGRAPH, USE_LANGGRAPH_PERCENT, USE_LANGGRAPH_FOR_FAQ removed in Issue #2651
    # LangGraph is now the only orchestrator mode (Simple Mode removed 2025-12-18)

    rollout_tracker_enabled: bool = Field(
        default=True,
        alias="ROLLOUT_TRACKER_ENABLED",
        description="Enable RolloutTracker for LangGraph rollout monitoring (Issue #2285)"
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

    # EPIC B Phase 7-8: Enhanced Reviewer Capabilities
    # Blueprint Section 3.3: Agent Separation Principle - Reviewer can FLAG but NOT fix
    use_multi_specialist_review: bool = Field(
        default=False,
        alias="USE_MULTI_SPECIALIST_REVIEW",
        description="Enable B-9 Multi-Specialist Review: parallel security/performance/architecture analysis. Requires USE_LLM_REVIEWER=True."
    )

    use_test_coverage_flagging: bool = Field(
        default=False,
        alias="USE_TEST_COVERAGE_FLAGGING",
        description="Enable B-11 Test Coverage Flagging: identify missing test coverage in PRs. READ-ONLY - flags issues but does NOT generate tests (that's Test Agent v2's job)."
    )

    use_dependency_analysis: bool = Field(
        default=False,
        alias="USE_DEPENDENCY_ANALYSIS",
        description="Enable B-12 Dependency Analysis: identify outdated/vulnerable dependencies in PRs. READ-ONLY - flags issues but does NOT fix them (that's Fixer Agent's job)."
    )

    # EPIC D Stage 3: Test Agent v2 Capabilities
    # Blueprint Section 3.3: Test Agent v2 generates tests from Reviewer flags
    use_test_generation: bool = Field(
        default=False,
        alias="USE_TEST_GENERATION",
        description="Enable D-7 Test Generation: automatically generate tests for coverage gaps identified by B-11. Requires USE_TEST_COVERAGE_FLAGGING=True. Test Agent v2 implementation."
    )

    test_generation_max_files: int = Field(
        default=5,
        alias="TEST_GENERATION_MAX_FILES",
        description="Maximum number of test files to generate per run (D-7). Limits LLM costs and prevents overwhelming PRs."
    )

    test_generation_enable_llm: bool = Field(
        default=True,
        alias="TEST_GENERATION_ENABLE_LLM",
        description="Enable LLM-powered test generation (D-7). When False, uses template-based fallback."
    )

    # EPIC D Stage 3: Diagnostic Agent Capabilities
    # Blueprint Section 3.5: Diagnostic Agent for error diagnosis and MRE generation
    use_diagnostic_agent: bool = Field(
        default=False,
        alias="USE_DIAGNOSTIC_AGENT",
        description="Enable D-8 Diagnostic Agent: provides root cause analysis, MRE generation, and blast radius assessment for errors. Integrates with D-7 Test Generation for regression test creation."
    )

    diagnostic_agent_enable_llm: bool = Field(
        default=True,
        alias="DIAGNOSTIC_AGENT_ENABLE_LLM",
        description="Enable LLM-powered diagnosis (D-8). When False, uses pattern-based analysis fallback."
    )

    diagnostic_agent_max_mre_lines: int = Field(
        default=50,
        alias="DIAGNOSTIC_AGENT_MAX_MRE_LINES",
        description="Maximum lines in generated MRE (D-8). Limits output size for readability."
    )

    # EPIC F Stage 3: Debate Engine for Adversarial Collaboration
    # Blueprint Section 7: Left Agent vs Right Agent → Judge Agent decision
    use_debate_engine: bool = Field(
        default=False,
        alias="USE_DEBATE_ENGINE",
        description="Enable F-5 Debate Engine: adversarial collaboration for high-risk decisions. Left Agent proposes conventional approach, Right Agent proposes alternative, Judge Agent decides."
    )

    debate_engine_enable_llm: bool = Field(
        default=True,
        alias="DEBATE_ENGINE_ENABLE_LLM",
        description="Enable LLM-powered debate arguments (F-5). When False, uses template-based fallback."
    )

    debate_engine_max_rounds: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="DEBATE_ENGINE_MAX_ROUNDS",
        description="Maximum debate rounds before Judge makes final decision (F-5). Higher values allow deeper exploration but increase latency and cost. Valid range: 1-10."
    )

    # EPIC F Stage 3: Self-refinement Loop for plan → execute → feedback → replan
    # Blueprint Section F-5: Closed loop execution with failure recovery
    use_self_refinement: bool = Field(
        default=False,
        alias="USE_SELF_REFINEMENT",
        description="Enable F-5 Self-refinement Loop: plan → execute → feedback → replan closed loop. Automatically replans on task failures with failure learning context."
    )

    self_refinement_max_task_replans: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="SELF_REFINEMENT_MAX_TASK_REPLANS",
        description="Maximum replans per failed task (F-5). After this limit, escalates to HITL. Valid range: 1-10."
    )

    self_refinement_max_full_replans: int = Field(
        default=2,
        ge=1,
        le=5,
        alias="SELF_REFINEMENT_MAX_FULL_REPLANS",
        description="Maximum full plan replans (F-5). After this limit, escalates to HITL. Valid range: 1-5."
    )

    # EPIC F Stage 3: Review Consolidation - Judge Agent Arbitration
    # Blueprint Section F-5.5: Conflict detection and arbitration for MultiSpecialistReviewer
    use_review_consolidation: bool = Field(
        default=False,
        alias="USE_REVIEW_CONSOLIDATION",
        description="Enable F-5.5 Review Consolidation: conflict detection and Judge Agent arbitration for MultiSpecialistReviewer findings. When enabled, ReviewConsolidator resolves conflicting specialist opinions."
    )

    # EPIC F Stage 3: Agent Assignment + Flow Template Selection
    # Blueprint Section F-4: Rule-based agent assignment and flow template selection
    use_agent_assignment: bool = Field(
        default=False,
        alias="USE_AGENT_ASSIGNMENT",
        description="Enable F-4 Agent Assignment: rule-based agent assignment based on task type and risk level. When enabled, AgentAssigner applies assignments to all tasks in a plan."
    )

    # EPIC F Stage 3: Model Tier Selection + Decision Hooks
    # Blueprint Section F-6: Rule-based model tier selection and planner hooks
    use_model_tier_selection: bool = Field(
        default=False,
        alias="USE_MODEL_TIER_SELECTION",
        description="Enable F-6 Model Tier Selection: rule-based model tier selection based on task characteristics. When enabled, ModelTierSelector assigns tiers (tier_0 to tier_3) to all tasks in a plan."
    )

    use_debate_hook: bool = Field(
        default=False,
        alias="USE_DEBATE_HOOK",
        description="Enable F-6 Debate Hook: triggers Debate Engine v2 for high-risk plans. When enabled, DebateHook invokes adversarial collaboration for critical decisions."
    )

    # EPIC G: Memory v2 - 4-Layer Memory System
    # Blueprint Section 5.1: Short-Term, Agent Interaction, Knowledge Base, Governance Memory
    enable_memory_v2: bool = Field(
        default=False,
        alias="ENABLE_MEMORY_V2",
        description="Enable G-1 Memory v2: 4-layer memory system for orchestrator. When enabled, integrates Short-Term, Agent Interaction, Knowledge Base, and Governance Memory layers."
    )

    enable_memory_v2_flow_state: bool = Field(
        default=False,
        alias="ENABLE_MEMORY_V2_FLOW_STATE",
        description="Enable G-1 Flow State persistence: saves FlowController state to Short-Term Memory for recovery. Requires ENABLE_MEMORY_V2=true."
    )

    enable_memory_v2_debate: bool = Field(
        default=False,
        alias="ENABLE_MEMORY_V2_DEBATE",
        description="Enable G-1 Debate context persistence: saves debate results to Agent Interaction Memory. Requires ENABLE_MEMORY_V2=true."
    )

    enable_memory_v2_governance: bool = Field(
        default=False,
        alias="ENABLE_MEMORY_V2_GOVERNANCE",
        description="Enable G-1 Governance memory: saves safety patterns, drift analysis, and routing decisions. Requires ENABLE_MEMORY_V2=true."
    )

    memory_v2_short_term_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        alias="MEMORY_V2_SHORT_TERM_TTL",
        description="TTL in seconds for Short-Term Memory entries (G-1). Default: 1 hour. Valid range: 60-86400."
    )

    memory_v2_agent_interaction_ttl: int = Field(
        default=86400,
        ge=3600,
        le=604800,
        alias="MEMORY_V2_AGENT_INTERACTION_TTL",
        description="TTL in seconds for Agent Interaction Memory entries (G-1). Default: 24 hours. Valid range: 1 hour - 7 days."
    )

    # EPIC G Phase G-2: Memory Consolidation Agent
    # Blueprint Section 5.1, 9, 10: Memory consolidation for accumulated experience
    enable_memory_consolidation: bool = Field(
        default=False,
        alias="ENABLE_MEMORY_CONSOLIDATION",
        description="Enable G-2 Memory Consolidation: periodically transfers important short-term memories to Knowledge Base. Requires ENABLE_MEMORY_V2=true."
    )

    memory_consolidation_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        alias="MEMORY_CONSOLIDATION_THRESHOLD",
        description="Importance threshold for memory consolidation (G-2). Memories with score >= threshold are consolidated. Default: 0.5."
    )

    memory_consolidation_batch_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        alias="MEMORY_CONSOLIDATION_BATCH_SIZE",
        description="Maximum memories to process per consolidation run (G-2). Default: 100."
    )

    memory_consolidation_interval_hours: float = Field(
        default=6.0,
        ge=1.0,
        le=24.0,
        alias="MEMORY_CONSOLIDATION_INTERVAL_HOURS",
        description="Hours between consolidation runs (G-2). Default: 6 hours. Valid range: 1-24 hours."
    )

    memory_consolidation_dry_run: bool = Field(
        default=True,
        alias="MEMORY_CONSOLIDATION_DRY_RUN",
        description="Enable dry-run mode for memory consolidation (G-2). When True, logs consolidation actions without persisting. Default: True for safe rollout."
    )

    senior_coder_strict_schema_validation: bool = Field(
        default=False,
        alias="SENIOR_CODER_STRICT_SCHEMA_VALIDATION",
        description="Enable strict schema validation for SeniorCoder output (Issue #3748). When True, abort/reject on schema validation failure. When False, observe-only mode (log warnings, continue)."
    )

    max_ci_error_file_paths: int = Field(
        default=20,
        alias="MAX_CI_ERROR_FILE_PATHS",
        description="Maximum number of CI error file paths to pass to GeneralCoder (Issue #3738). Increased from 5 to 20 to support HITL 6+ files escalation."
    )

    enable_llm_json_repair: bool = Field(
        default=False,
        alias="ENABLE_LLM_JSON_REPAIR",
        description="Enable LLM-based JSON repair for truncated responses (EPIC B Phase 3 P3). Disabled by default for safer rollout."
    )

    llm_json_repair_max_tokens: int = Field(
        default=1000,
        alias="LLM_JSON_REPAIR_MAX_TOKENS",
        description="Max tokens for LLM JSON repair output (EPIC B Phase 3). Tune based on model limits or cost."
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

    llm_review_max_diff_chars: int = Field(
        default=80000,
        alias="LLM_REVIEW_MAX_DIFF_CHARS",
        description="Maximum characters for annotated diff in LLM reviewer prompt. Diffs exceeding this limit will be truncated (preserving + lines over context lines). Default 80k chars (~20k tokens) leaves room for system prompt and response."
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

    # Issue #3578: SSOT Telemetry Schema v3 Migration
    enable_ssot_telemetry: bool = Field(
        default=False,
        alias="ENABLE_SSOT_TELEMETRY",
        description="Enable SSOT Telemetry Schema v3 spans in node_metrics decorator (Issue #3578 Spine First)"
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

    # Phase B-B: Internal Repo Dogfooding (Staging Only)
    # Allows MorningAI to review its own code in Staging environment
    allow_internal_repos_in_staging: bool = Field(
        default=False,
        alias="ALLOW_INTERNAL_REPOS_IN_STAGING",
        description="Allow AI review workflow to process internal repos (RC918/morningai) in Staging. Enables dogfooding - MorningAI reviewing its own code."
    )

    internal_repos_whitelist: str = Field(
        default="RC918/morningai",
        alias="INTERNAL_REPOS_WHITELIST",
        description="Comma-separated list of internal repos allowed for AI review in Staging (e.g., 'RC918/morningai,RC918/other-repo')"
    )

    # Phase B-B: PR_UPDATED Event Support with Debounce/Throttle
    # Enables AI review on PR updates (push events) with debounce to prevent cost explosion
    enable_pr_updated_review: bool = Field(
        default=False,
        alias="ENABLE_PR_UPDATED_REVIEW",
        description="Enable AI review workflow for PR_UPDATED events (synchronize/edited). Requires debounce to prevent cost explosion from rapid pushes."
    )

    pr_updated_debounce_seconds: int = Field(
        default=30,
        alias="PR_UPDATED_DEBOUNCE_SECONDS",
        ge=5,
        le=300,
        description="Debounce window in seconds for PR_UPDATED events. Only the last event within this window will trigger a review. Default: 30 seconds."
    )

    pr_updated_throttle_seconds: int = Field(
        default=600,
        alias="PR_UPDATED_THROTTLE_SECONDS",
        ge=60,
        le=3600,
        description="Minimum time between PR_UPDATED reviews for the same PR. Prevents excessive reviews on active PRs. Default: 10 minutes (600 seconds)."
    )

    pr_updated_repos_whitelist: str = Field(
        default="",
        alias="PR_UPDATED_REPOS_WHITELIST",
        description="Comma-separated list of repos where PR_UPDATED review is enabled. Empty string means all repos (if enable_pr_updated_review=True). Use for gradual rollout."
    )

    # Phase B-B: Fault Injection for 422 Fallback Verification (Staging Only)
    # Enables controlled testing of the 422 fallback mechanism
    enable_fault_injection: bool = Field(
        default=False,
        alias="ENABLE_FAULT_INJECTION",
        description="Enable fault injection for testing fallback mechanisms. Only works when is_staging=True. Use with caution."
    )

    fault_injection_422_rate: float = Field(
        default=1.0,
        alias="FAULT_INJECTION_422_RATE",
        ge=0.0,
        le=1.0,
        description="Rate at which to inject 422 errors (0.0-1.0). Only applies when enable_fault_injection=True and is_staging=True."
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

    # VSCode IDE Resource monitoring (#2353)
    vscode_session_idle_timeout: int = Field(
        default=1800,
        alias="VSCODE_SESSION_IDLE_TIMEOUT",
        description="IDE session idle timeout in seconds. Sessions inactive for this duration will be marked for cleanup. Default is 30 minutes (1800 seconds)."
    )

    vscode_session_cpu_limit_percent: int = Field(
        default=80,
        alias="VSCODE_SESSION_CPU_LIMIT_PERCENT",
        description="CPU usage threshold percentage for IDE session overload protection. When exceeded, new sessions may be rejected."
    )

    vscode_session_memory_limit_percent: int = Field(
        default=85,
        alias="VSCODE_SESSION_MEMORY_LIMIT_PERCENT",
        description="Memory usage threshold percentage for IDE session overload protection. When exceeded, new sessions may be rejected."
    )

    vscode_max_sessions: int = Field(
        default=10,
        alias="VSCODE_MAX_SESSIONS",
        description="Maximum number of concurrent IDE sessions allowed. Set to 0 for unlimited."
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

    # EPIC B Phase B-3: GitHub Review Posting Feature Flags
    enable_github_review_posting: bool = Field(
        default=False,
        alias="ENABLE_GITHUB_REVIEW_POSTING",
        description="Enable posting review comments to GitHub PR inline reviews (EPIC B Phase B-3)"
    )

    github_review_posting_dry_run: bool = Field(
        default=True,
        alias="GITHUB_REVIEW_POSTING_DRY_RUN",
        description="Dry-run mode for GitHub review posting - logs what would be posted without actually posting"
    )

    github_review_posting_max_comments: int = Field(
        default=10,
        ge=1,
        le=50,
        alias="GITHUB_REVIEW_POSTING_MAX_COMMENTS",
        description="Maximum number of inline comments to post per review (prevents notification spam)"
    )

    # EPIC B Optimization: Filter non-diff file comments
    # When enabled, review comments for files NOT in the PR diff are filtered out
    # This reduces noise from pre-existing issues in unchanged files
    reviewer_filter_non_diff_files: bool = Field(
        default=True,
        alias="REVIEWER_FILTER_NON_DIFF_FILES",
        description="Filter out review comments for files not in the PR diff (reduces noise from pre-existing issues)"
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

    # =========================================================================
    # Flow Controller v3 (EPIC C) - Dynamic Routing Feature Flags
    # Issue #2746: Feature Flag configuration for LLM-driven routing
    # =========================================================================

    enable_dynamic_routing: bool = Field(
        default=False,
        alias="ENABLE_DYNAMIC_ROUTING",
        description=(
            "Enable LLM-driven dynamic routing (Flow Controller v3). "
            "Default False = 100% old behavior (conditional_edges). "
            "When True, enables Router v3 with fail-safe fallback to deterministic routing. "
            "Note: This flag is only used when DYNAMIC_ROUTING_SAMPLE_RATE=0. "
            "When sample_rate > 0, per-workflow hash-based bucketing takes precedence."
        )
    )

    dynamic_routing_sample_rate: int = Field(
        default=0,
        ge=0,
        le=100,
        alias="DYNAMIC_ROUTING_SAMPLE_RATE",
        description=(
            "Percentage of workflows to route through Flow Controller v3 (0-100). "
            "Uses deterministic hash-based bucketing for sticky assignment. "
            "0 = disabled (uses ENABLE_DYNAMIC_ROUTING flag), "
            "5 = 5% canary, 25 = 25%, 100 = full rollout. "
            "Same workflow always routes to same path (deterministic)."
        )
    )

    router_model_tier: Literal["tier1", "tier2"] = Field(
        default="tier1",
        alias="ROUTER_MODEL_TIER",
        description=(
            "Model tier for router decisions. "
            "tier1 = 235B parameter model (highest quality), "
            "tier2 = 80B parameter model (faster, lower cost)"
        )
    )

    router_timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        alias="ROUTER_TIMEOUT_SECONDS",
        description="Timeout for router LLM calls in seconds (1-60)"
    )

    router_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        alias="ROUTER_MAX_RETRIES",
        description="Maximum retries for router LLM calls (0-5)"
    )

    router_fallback_rate_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        alias="ROUTER_FALLBACK_RATE_THRESHOLD",
        description=(
            "Fallback rate threshold for automatic rollback (0.0-1.0). "
            "If fallback rate exceeds this threshold, consider disabling dynamic routing."
        )
    )

    # =========================================================================
    # EPIC D - SimpleCoder Feature Flags (D-1 Phase 1)
    # Issue #2760: SimpleCoder wiring into LangGraph workflow
    # =========================================================================

    enable_simple_coder: bool = Field(
        default=False,
        alias="ENABLE_SIMPLE_CODER",
        description=(
            "Enable SimpleCoder auto-fix in fixer_node (EPIC D Phase 1). "
            "Default False = SimpleCoder disabled, only AutoFixer runs. "
            "When True, SimpleCoder attempts fix first with Three Don'ts guardrails, "
            "falling back to AutoFixer if SimpleCoder skips or fails."
        )
    )

    enable_general_coder: bool = Field(
        default=False,
        alias="ENABLE_GENERAL_CODER",
        description=(
            "Enable GeneralCoder multi-file auto-fix in fixer_node (EPIC D Phase 1b). "
            "Default False = GeneralCoder disabled, only SimpleCoder/AutoFixer runs. "
            "When True, GeneralCoder attempts multi-file fix with atomic commits, "
            "falling back to SimpleCoder if GeneralCoder skips or fails. "
            "Requires ENABLE_SIMPLE_CODER=True for fallback chain."
        )
    )

    general_coder_max_files: int = Field(
        default=5,
        alias="GENERAL_CODER_MAX_FILES",
        ge=1,
        le=20,
        description=(
            "Maximum number of files GeneralCoder can process in a single multi-file fix. "
            "Default 5 (D-1b design limit). Higher values may increase LLM token usage "
            "and processing time. Recommended range: 3-10 for most projects."
        )
    )

    enable_senior_coder: bool = Field(
        default=False,
        alias="ENABLE_SENIOR_CODER",
        description=(
            "Enable SeniorCoder reasoning-first architecture (EPIC D Phase 2). "
            "Default False = SeniorCoder disabled, direct GeneralCoder/SimpleCoder execution. "
            "When True, SeniorCoder analyzes task complexity and creates architecture spec "
            "before delegating to GeneralCoder/SimpleCoder for implementation. "
            "Requires ENABLE_GENERAL_CODER=True for full pipeline."
        )
    )

    enable_self_correction: bool = Field(
        default=False,
        alias="ENABLE_SELF_CORRECTION",
        description=(
            "Enable D-4 Self-Correction Loop for autonomous test failure recovery (Issue #2764). "
            "Default False = Self-correction disabled, test failures escalate to Reviewer. "
            "When True, the system attempts to automatically fix test failures by: "
            "1. Parsing test output (pytest/npm test) to identify failure types "
            "2. Analyzing errors (syntax, assertion, import, type, runtime) "
            "3. Generating fixes using GeneralCoder/SimpleCoder "
            "4. Retrying up to 3 times before escalating to Reviewer. "
            "Requires ENABLE_GENERAL_CODER=True or ENABLE_SIMPLE_CODER=True for fix generation."
        )
    )

    self_correction_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="SELF_CORRECTION_MAX_ATTEMPTS",
        description=(
            "Maximum retry attempts for D-4 Self-Correction Loop before escalating to Reviewer. "
            "Default 3 = Try to fix test failures up to 3 times before giving up. "
            "Lower values = faster escalation (more conservative). "
            "Higher values = more retry attempts (more aggressive). "
            "Recommended range: 2-5 for most projects."
        )
    )

    enable_multi_file_hitl_escalation: bool = Field(
        default=True,
        alias="ENABLE_MULTI_FILE_HITL_ESCALATION",
        description=(
            "Enable HITL escalation when GeneralCoder skips due to 6+ files (P1 feature). "
            "Default True = When GeneralCoder cannot handle 6+ files, trigger HITL escalation "
            "to request human review instead of silently falling back to SimpleCoder/AutoFixer. "
            "This improves user experience by surfacing complex multi-file issues that require "
            "human oversight. Depends on Context Manager Telemetry for file selection data."
        )
    )

    require_design_doc_gate: bool = Field(
        default=True,
        alias="REQUIRE_DESIGN_DOC_GATE",
        description=(
            "Enforce mandatory architecture review before GeneralCoder execution (P2 feature). "
            "Blueprint Section 4.1 Safety Governor v2 alignment - 強制架構審查. "
            "Default True = When SeniorCoder is enabled, GeneralCoder MUST have a valid "
            "ArchitectureSpec before proceeding. If SeniorCoder planning fails or is disabled, "
            "trigger HITL escalation instead of proceeding without design review. "
            "This ensures all code changes have proper architecture planning and review. "
            "Only effective when ENABLE_SENIOR_CODER=True."
        )
    )

    # ==========================================================================
    # Configurable HITL Thresholds (P3 Feature)
    # ==========================================================================
    # These settings allow operators to tune HITL escalation behavior based on
    # their team's capacity and risk tolerance. Blueprint Section 4.1 alignment.
    # ==========================================================================

    hitl_multi_file_threshold: int = Field(
        default=6,
        ge=2,
        le=50,
        alias="HITL_MULTI_FILE_THRESHOLD",
        description=(
            "File count threshold for HITL escalation (P3 feature). "
            "When GeneralCoder encounters more files than this threshold, "
            "trigger HITL escalation instead of proceeding. "
            "Default 6 = Tasks affecting 6+ files require human review. "
            "Lower values = more conservative (more HITL escalations). "
            "Higher values = more permissive (fewer HITL escalations). "
            "Recommended range: 5-10 for most teams."
        )
    )

    hitl_complexity_escalation_enabled: bool = Field(
        default=True,
        alias="HITL_COMPLEXITY_ESCALATION_ENABLED",
        description=(
            "Enable HITL escalation for complex tasks (P3 feature). "
            "Default True = When SeniorCoder classifies a task as 'complex', "
            "trigger HITL escalation for human review before proceeding. "
            "When False, complex tasks proceed without human review. "
            "Blueprint Section 4.1 Safety Governor v2 alignment."
        )
    )

    hitl_design_doc_gate_enabled: bool = Field(
        default=True,
        alias="HITL_DESIGN_DOC_GATE_ENABLED",
        description=(
            "Enable HITL escalation when Design Doc Gate fails (P3 feature). "
            "Default True = When ArchitectureSpec is missing or invalid, "
            "trigger HITL escalation instead of proceeding without design review. "
            "When False, missing/invalid specs log a warning but don't block. "
            "Blueprint Section 4.1 Safety Governor v2 alignment."
        )
    )

    # ==========================================================================
    # EPIC F - Planner v3 Feature Flags (Phase F-3c)
    # Issue #3864: FlowController integration into LangGraph orchestrator
    # ==========================================================================

    enable_flow_controller_v3: bool = Field(
        default=False,
        alias="ENABLE_FLOW_CONTROLLER_V3",
        description=(
            "Enable FlowController v3 for unified plan execution (EPIC F Phase F-3c). "
            "Default False = FlowController disabled, uses existing executor_node. "
            "When True, plans are executed via FlowController with AgentTaskExecutor, "
            "providing unified task execution, dependency management, and state mapping. "
            "This is the foundation for Planner v3 architecture."
        )
    )

    flow_controller_sample_rate: int = Field(
        default=0,
        ge=0,
        le=100,
        alias="FLOW_CONTROLLER_SAMPLE_RATE",
        description=(
            "Percentage of workflows to route through FlowController v3 (canary gating). "
            "Default 0 = No canary traffic, use ENABLE_FLOW_CONTROLLER_V3 flag only. "
            "When > 0, uses hash-based bucketing of trace_id for deterministic assignment. "
            "Example: 10 = 10% of workflows use FlowController, 90% use legacy executor. "
            "Recommended: Start with 5-10% in staging, gradually increase to 100%."
        )
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

    @model_validator(mode="after")
    def validate_provider_health_weights(self) -> "Settings":
        """Validate and normalize provider health scoring weights (EPIC I-2).

        Soft validation: If weights don't sum to 1.0, log a warning and normalize
        them to preserve relative preferences. This follows the observe-only safety
        contract - we never block service startup on misconfiguration.

        Fixes #3352
        """
        weights = {
            "latency": self.provider_health_latency_weight,
            "error": self.provider_health_error_weight,
            "drift": self.provider_health_drift_weight,
        }
        weights_sum = sum(weights.values())

        if abs(weights_sum - 1.0) > 0.001:
            if weights_sum > 0:
                normalized = {k: v / weights_sum for k, v in weights.items()}
                warnings.warn(
                    f"Provider health weights sum to {weights_sum:.3f} instead of 1.0. "
                    f"Weights will be normalized to preserve relative preferences. "
                    f"Current: latency={weights['latency']}, error={weights['error']}, "
                    f"drift={weights['drift']}. "
                    f"Normalized: latency={normalized['latency']:.3f}, "
                    f"error={normalized['error']:.3f}, drift={normalized['drift']:.3f}",
                    UserWarning
                )
                object.__setattr__(
                    self, "provider_health_latency_weight", normalized["latency"]
                )
                object.__setattr__(
                    self, "provider_health_error_weight", normalized["error"]
                )
                object.__setattr__(
                    self, "provider_health_drift_weight", normalized["drift"]
                )
            else:
                warnings.warn(
                    f"Provider health weights sum to {weights_sum:.3f} instead of 1.0. "
                    f"All weights are zero - normalization skipped to avoid division by zero. "
                    f"Health scoring will be ineffective until weights are configured.",
                    UserWarning
                )

        return self

    def log_deprecation_warnings(self):
        """Log warnings for deprecated variable usage.

        This method checks for deprecated environment variables and emits
        warnings when they are used. Each deprecated variable has:
        - old_field: The deprecated field name in Settings
        - new_field: The replacement field name in Settings
        - old_env: The deprecated environment variable name
        - new_env: The replacement environment variable name
        - removal_date: The date after which support will be removed
        """
        # SECRET_KEY and MASTER_KEY removed - deadline 2025-11-30 passed
        # Deprecated variables with their replacements and removal dates
        deprecated_vars = [
            # (old_field, new_field, old_env, new_env, removal_date)
            ("stripe_webhook_secret", "stripe_webhook_secret_key", "STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET_KEY", "2025-12-31"),
            ("owner_password", "admin_password", "OWNER_PASSWORD", "ADMIN_PASSWORD", "2025-12-31"),
        ]

        for old_field, new_field, old_env, new_env, removal_date in deprecated_vars:
            old_value = getattr(self, old_field, None)
            new_value = getattr(self, new_field, None)

            if old_value and not new_value:
                warnings.warn(
                    f"{old_env} is deprecated. Please use {new_env} instead. "
                    f"Support for {old_env} will be removed after {removal_date}.",
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
