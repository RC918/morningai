# MorningAI Environment Architecture

**Last Updated**: 2025-11-26  
**Document Version**: 2.3  
**Related Documents**: 
- [PROJECT_STRUCTURE_REPORT.md](PROJECT_STRUCTURE_REPORT.md) - 專案結構報告
- [PROJECT_DEEP_ANALYSIS.md](../PROJECT_DEEP_ANALYSIS.md) - 深度解析報告
- [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md) - 新人上手指南

---

⚠️ **SECURITY NOTICE**: This document contains references to sensitive environment variables.
- 🔒 Variables marked with lock icon are **SECRETS** - never log, commit, or share
- All example values are placeholders - generate unique secrets for each environment
- Rotate secrets immediately if exposed
- Use `python -c "import secrets; print(secrets.token_urlsafe(64))"` to generate secure secrets

---

## Overview

MorningAI uses a multi-environment deployment architecture to ensure safe development, testing, and production workflows. This document provides a comprehensive overview of all environments, their configurations, and deployment processes.

**近期重要更新** (2025-11-25 至 2025-11-26):
- **PR #1548**: Frontend Dashboard 代碼分割優化 - 20% bundle 減少 + Lighthouse CI color-contrast 修復
  - Path: `handoff/20250928/40_App/frontend-dashboard/`
  - 影響：提升性能和無障礙合規性
- **PR #1562**: RQ Job Timeout 配置 - 新增 `RQ_JOB_TIMEOUT` 環境變數
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
  - 影響：可配置的任務超時時間（預設：3600 秒）
- **PR #1547**: AppleButton 遷移到 shared-ui - Adapter pattern 實作
  - Path: `packages/shared-ui/`
  - 影響：統一組件庫跨 frontend-dashboard 和 owner-console
- **PR #1546**: Phase 2 UI 完成 - 情感顏色、AppleButton 對齊、Spring 動畫
  - Path: `handoff/20250928/40_App/frontend-dashboard/src/`
- **PR #1545**: P1 情感顏色 + AgentExecutionLogs Apple 設計
  - Path: `handoff/20250928/40_App/owner-console/src/components/AgentExecutionLogs.tsx`
- **PR #1544**: Apple 設計系統全局應用
  - Path: `handoff/20250928/40_App/frontend-dashboard/`, `handoff/20250928/40_App/owner-console/`
- **UUID 正規化修復**: 處理外部工具的前綴 task ID
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
- **LoginPage UX 改進**: 使用 Apple 設計系統全面重構
  - Path: `handoff/20250928/40_App/frontend-dashboard/src/components/LoginPage.tsx`

**先前重要更新** (2025-11-18 至 2025-11-23):
- **PR #1350**: E2E 測試基礎設施完成 - 32 Playwright 測試通過，route handler 隔離，完整 API mocking
  - Path: `handoff/20250928/40_App/owner-console/e2e/`
  - 測試改善: 11 passed → 32 passed (修復 21 個失敗測試)
- **PR #1398**: 生產環境路徑發現機制 - 新增 `MORNINGAI_REPO_PATH` 環境變數
  - Path: `handoff/20250928/40_App/orchestrator/context_manager.py`
  - 4 層 fallback: env var → git detection → marker-based discovery
- **PR #1399**: Backend 測試環境統一 - Python 3.12, Redis service, PyJWT 衝突解決
  - Path: `.github/workflows/test-apps.yml`
  - 統一 backend.yml 和 test-apps.yml 配置
- **PR #1480**: Pydantic 別名系統 - 新增 23 個關鍵環境變數別名 (2025-11-23)
  - Path: `common/config/settings.py`
  - 修復：`FLASK_SECRET_KEY`, `ENCRYPTION_MASTER_KEY`, `STRIPE_WEBHOOK_SECRET_KEY` 別名
  - 影響：向後相容性改進，標準化配置命名
- **PR #1452**: Redis 映射清理 - 防止 NoneType DataError (2025-11-23)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - 新增：`sanitize_redis_mapping()` 函數過濾 None 值
  - 影響：提升 Worker 心跳和任務狀態更新的穩定性

---

## Environment Summary

| Environment | Status | Purpose | Branch | Auto-Deploy |
|-------------|--------|---------|--------|-------------|
| **Production** | ✅ Active | Live user-facing services | `main` | Yes |
| **Staging** | ✅ Active | Pre-production testing | `develop` | Yes |
| **Local Development** | ✅ Active | Developer workstations | Any | No |

---

## 🚀 Production Environment

### Services

#### Backend API
- **URL**: https://morningai-backend-v2.onrender.com
- **Service Name**: `morningai-backend-v2`
- **Platform**: Render
- **Runtime**: Python 3
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /healthz`

#### Orchestrator API
- **URL**: https://morningai-orchestrator-api.onrender.com
- **Service Name**: `morningai-orchestrator-api`
- **Platform**: Render
- **Runtime**: Docker
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /health`

⚠️ **Orchestrator Architecture (Dual-Mode System with Shared Core)**

MorningAI uses a **dual-mode orchestrator architecture** with a shared core executor and canary routing:

```
API Backend → Redis Queue → Worker (Routing) → [Simple Mode | LangGraph Mode]
                                                       ↓              ↓
                                                  graph.execute (Shared Core)
```

**Key Insight**: `graph.py` is NOT just "legacy code" - it's the **shared execution engine** used by both modes.

| Component | Role | Traffic | Status | Path |
|-----------|------|---------|--------|------|
| **Simple Mode** | Direct execution | ~95% | Feature-frozen | `handoff/20250928/40_App/orchestrator/graph.py` |
| **LangGraph Mode** | Stateful workflows | ~5% | Active development | `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py` |
| **Shared Core** | Execution engine | 100% | Both modes | `handoff/20250928/40_App/orchestrator/graph.py:30-155` |
| **Routing Logic** | Mode selection | 100% | Canary deployment | `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-400` |

### Execution Modes

**Simple Mode** (~95% traffic):
- ✅ Fast: Direct execution, no state machine overhead
- ✅ Stable: Battle-tested, production-proven
- ✅ Stateless: No retry logic, no CI monitoring
- ❌ Feature-frozen: Only bug fixes accepted
- Entry: `worker.py:399` → `graph.execute()`

**LangGraph Mode** (~5% traffic, Phase 1):
- ✅ Stateful: Full state machine with LangGraph
- ✅ Intelligent: LLM-powered planning (when `USE_LLM_PLANNER=true`)
- ✅ Resilient: Retry logic, error handling, CI monitoring
- ✅ Active Development: New features go here
- Entry: `worker.py:396` → `langgraph_orchestrator.run_orchestrator()` → `executor_node` → `graph.execute()`

### Routing Logic (Canary Deployment)

**Algorithm** (`worker.py:366-400`):
```python
use_langgraph = settings.use_langgraph or False
use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)

if not use_langgraph and use_langgraph_percent > 0:
    # Canary logic: MD5 hash for deterministic routing
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100  # 0-99 bucket
    use_langgraph = task_percent < use_langgraph_percent
```

**Properties**:
- **Deterministic**: Same task_id always routes to same mode
- **Uniform**: MD5 ensures even distribution across 0-99 buckets
- **Controllable**: Adjust `USE_LANGGRAPH_PERCENT` to change traffic split
- **Observable**: Logs routing decision with structured logging

**Monitoring Keywords** (search in Render Dashboard logs):
- `"Canary deployment"` - Routing decision
- `"Using LangGraph orchestrator"` - LangGraph execution
- `"Using simple orchestrator"` - Simple execution
- `"Using LLM planner"` - LLM planner selection

### Environment Variable Configuration

⚠️ **注意**：本文檔描述架構設計和政策。實際環境變數配置可能因運維需求調整。請以 Render Dashboard 的實際配置為準。

**Phase 1 參考配置**（實際配置請查看 Render Dashboard）:

| 服務 | USE_LANGGRAPH | USE_LANGGRAPH_PERCENT | USE_LLM_PLANNER | 位置 |
|------|---------------|----------------------|-----------------|------|
| `morningai-agent-worker` (Production) | `false` | `5` | `true` | Render Dashboard → Production Worker → Environment |

**Note**: For staging worker configuration, refer to [STAGING_SETUP_GUIDE.md](./ops/STAGING_SETUP_GUIDE.md). Staging worker service names are environment-specific and defined in the staging setup documentation.

**配置範例**:
```bash
USE_LANGGRAPH=false              # Allow canary routing (not 100%)
USE_LANGGRAPH_PERCENT=5          # 5% traffic to LangGraph
USE_LLM_PLANNER=true             # LangGraph uses LLM planner
```

**Kill Switch** (Emergency - 100% Simple):
```bash
USE_LANGGRAPH=false
USE_LANGGRAPH_PERCENT=0          # 0% to LangGraph (100% Simple)
```

**Full LangGraph** (Future - Phase 2+):
```bash
USE_LANGGRAPH=true               # 100% to LangGraph (overrides percent)
```

### Development Guidelines

**✅ DO**: Add new orchestrator features to LangGraph mode only
**❌ DON'T**: Add features to Simple mode (feature-frozen)
**⚠️ CRITICAL**: Changes to `graph.execute()` affect BOTH modes - test both!

**Documentation**: 
- [ONBOARDING_GUIDE.md - Orchestrator Architecture](./ONBOARDING_GUIDE.md#orchestrator-architecture) - Comprehensive developer guide
- [PROJECT_STRUCTURE_REPORT.md - Orchestrator System](./PROJECT_STRUCTURE_REPORT.md#3-orchestrator-system) - Technical details
- [ADR-005: Dual Orchestrator Architecture](adr/005-dual-orchestrator-architecture.md) - Historical context
- [ADR-002: Producer-Consumer Architecture](adr/002-producer-consumer-architecture.md) - Technical architecture
- [ADR-004: Shared Core Executor Pattern](adr/004-shared-core-executor-pattern.md) - Design decision for shared execution engine

**Migration Roadmap**:
- **Phase 1** (Current): 5% LangGraph canary validation
- **Phase 2** (Q1 2026): Gradually increase to 100% LangGraph
- **Phase 3** (Q2 2026): Refactor `graph.py` to `core_executor.py`

#### Frontend Dashboard
- **URL**: https://morningai.vercel.app
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)

### Infrastructure

#### Database
- **Provider**: Supabase PostgreSQL
- **Project Name**: `morningai` (production)
- **Project ID**: `qevmlbsunnwgrsdibdoi`
- **URL**: https://qevmlbsunnwgrsdibdoi.supabase.co
- **Type**: Production instance
- **Connection**: Pooler (port 6543)
- **Backups**: Automatic daily backups
- **Schema**: Full production schema with all tables

#### Redis
- **Provider**: Upstash
- **Type**: Production instance
- **Protocol**: `rediss://` (TLS enabled)
- **Key Prefix**: None (production)

#### Monitoring
- **Error Tracking**: Sentry
- **Environment Tag**: `production`
- **Uptime Target**: 99.9%

### Environment Variables

**Schema Definition**: `config/env.schema.yaml` (Single Source of Truth)
- **Total Defined**: 122 variables (20 required, 102 optional)
- **Schema Version**: 1.3 (Phase 1-2 + Feature Flags + Deployment)
- **Auto-Generated**: `.env.example` is generated from schema via `scripts/generate-env-examples.py`
- **CI Validation**: `tests/lint/test_env_vars_defined.py` validates all `os.getenv()` calls against schema
- **Deprecation**: Root `env_schema.yaml` is deprecated; use `config/env.schema.yaml` only
- **Path**: `/home/ubuntu/repos/morningai/config/env.schema.yaml`

**Recent Additions (PR #1398)**:
- **Deployment Category**: New category for deployment-specific variables
  - `MORNINGAI_REPO_PATH`: Repository root path for production/staging
    - Required in Render.com: `/opt/render/project/src`
    - Falls back to git detection or marker-based discovery
    - Replaces hardcoded `~/repos/morningai` path

**Phase 1-2 New Variables** (Added 2025-11):
- **2FA/Authentication**: 
  - `FEATURE_2FA_PREAUTH` (boolean, safe to log)
  - `PREAUTH_TOKEN_TTL` (integer seconds, safe to log)
  - 🔒 `TOTP_ENCRYPTION_KEY` (**SECRET** - DO NOT LOG/COMMIT - 32 bytes base64 encoded)
- **AI Orchestration** (Phase 1-2):
  - `USE_LLM_PLANNER` (boolean) - Enable LLM-based task planning (Phase 1)
  - `USE_CODEGEN_WORKFLOW_PERCENT` (integer 0-100) - Percentage rollout for code generation workflow (Phase 2)
  - `USE_LANGGRAPH` (boolean) - Enable LangGraph orchestrator mode
  - `USE_LANGGRAPH_PERCENT` (integer 0-100) - Percentage rollout for LangGraph
- **Rate Limiting**: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`, `RATE_LIMIT_BY_USER`, `RATE_LIMIT_FAIL_FAST`, `RATE_LIMIT_REDIS_MAX_RETRIES`, `RATE_LIMIT_REDIS_RETRY_DELAY`
- **Testing** (⚠️ **TEST ENVIRONMENTS ONLY** - NEVER SET IN PRODUCTION):
  - `TESTING` (boolean) - Enables test mode behaviors
  - 🚫 `FORCE_ENABLE_2FA_IN_TESTS` (boolean) - **DANGEROUS** - Can bypass security controls
    - ⚠️ **CRITICAL**: This flag MUST ONLY be set in test environments
    - ⚠️ Setting in production/staging can disable 2FA enforcement
    - ⚠️ CI should fail if this is set in production/staging environments
- **Database**: `DB_POOL_MAX`, `DB_POOL_SIZE`, `DB_POOL_RECYCLE`, `DB_POOL_PRE_PING`
- **Redis**: `REDIS_KEY_PREFIX`, `RQ_QUEUE_NAME`
- **Security**: `COOKIE_DOMAIN`, `COOKIE_PATH`, `FEATURE_COOKIE_AUTH`
- **Operations**: `DEBUG`, `FAQ_CACHE_TTL`, `ORCHESTRATOR_PATH`, `OPENAI_MAX_DAILY_COST`
- **Deployment**: `GIT_COMMIT`, `RENDER_GIT_COMMIT`, `SENTRY_ENVIRONMENT`
- **Governance**: `ALLOW_GOVERNANCE_MOCK`, `ENABLE_MOCK_USERS`

**Redis Requirements**:
- **Minimum Version**: Redis 2.6+ (required for Lua EVAL support used in atomic pre-auth token consumption)
- **Recommended**: Upstash Redis or self-hosted Redis 8.2.2+ with TLS (`rediss://`)
- **Security**: CVE-2025-49844 protection requires TLS-enabled connections

**Critical Variables**:
```bash
# ⚠️ EXAMPLE CONFIGURATION - NEVER USE THESE PLACEHOLDER VALUES IN PRODUCTION
# Generate secure secrets: python -c "import secrets; print(secrets.token_urlsafe(64))"

ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...

# 🔒 SECRETS - Minimum 64 characters, cryptographically random
JWT_SECRET_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING           # 🔒 SECRET - DO NOT LOG
SECRET_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING               # 🔒 SECRET - DO NOT LOG
MASTER_ENCRYPTION_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING    # 🔒 SECRET - DO NOT LOG
ENCRYPTION_MASTER_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING    # 🔒 SECRET - Alias for MASTER_ENCRYPTION_KEY
TOTP_ENCRYPTION_KEY=CHANGEME_GENERATE_RANDOM_32_BYTES_BASE64     # 🔒 SECRET - 32 bytes base64 - Required for 2FA
ORCHESTRATOR_JWT_SECRET=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING  # 🔒 SECRET - DO NOT LOG
```

**Monitoring**:
```bash
SENTRY_DSN=<production-dsn>
SENTRY_ENVIRONMENT=production
```

**Orchestrator Configuration** (Phase 1-2):

⚠️ **注意**：以下為參考配置。實際環境變數請查看 Render Dashboard。

```bash
# Dual-Mode Orchestrator with Canary Routing
USE_LANGGRAPH=false                     # Allow canary routing (false = use percent, true = 100%)
USE_LANGGRAPH_PERCENT=5                 # 5% traffic to LangGraph mode (0-100)

# Phase 1-2 Feature Flags
USE_LLM_PLANNER=true                    # Enable LLM-based task planning (Phase 1)
USE_CODEGEN_WORKFLOW_PERCENT=0          # Percentage rollout for code generation (Phase 2, 0-100)

# Configuration Examples:
# - Kill Switch (100% Simple):    USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=0
# - 5% Canary (Phase 1 Reference): USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=5
# - 50% Split Testing:            USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=50
# - 100% LangGraph (Future):      USE_LANGGRAPH=true (overrides percent)
```

**Rate Limiting**:
```bash
# Rate limiting configuration (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=true               # Fail on startup if Redis unavailable (production only)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Logging Configuration**:
```bash
# Application logging level (case-insensitive, normalized to uppercase)
# Used by: Python logging configuration (common/config/settings.py)
LOG_LEVEL=INFO                          # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
                                        # Supports any case: info/INFO/Info all work

# Gunicorn logging level (case-insensitive, normalized to lowercase)
# Used by: Gunicorn configuration (gunicorn.conf.py)
GUNICORN_LOG_LEVEL=info                 # Options: debug, info, warning, error, critical
                                        # Supports any case: INFO/info/Info all work

# Note: As of PR #1499, both LOG_LEVEL and GUNICORN_LOG_LEVEL support case-insensitive
# input. The validators automatically normalize to the correct case before validation.
# This prevents ValidationError when environment variables use different casing.
# See config/env.schema.yaml for default values and allowed choices.
```

**Troubleshooting**:
- If you provide an invalid value (not in the list above), the application will fail to start with a Pydantic `ValidationError` on the `log_level` or `gunicorn_log_level` field.
- Check startup logs for details and update the environment variable to one of the supported values.
- Example error: `ValidationError: 1 validation error for Settings log_level Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'`

---

## 環境變數別名系統（Pydantic Aliases）

**Added**: 2025-11-23 (PR #1480)  
**Path**: `common/config/settings.py:47-722`

從 2025-11-23 起，配置系統通過 Pydantic BaseSettings 支援環境變數別名，確保向後相容性並標準化命名規範。這允許使用舊的環境變數名稱，同時逐步遷移到標準化的命名約定。

### 別名系統概述

MorningAI 使用 Pydantic 的 `Field(alias=...)` 功能來支援多個環境變數名稱映射到同一個配置屬性。這確保了：

1. **向後相容性**：現有部署可以繼續使用舊的環境變數名稱
2. **標準化命名**：新部署應使用正式的標準化名稱
3. **逐步遷移**：團隊可以按自己的節奏遷移到新名稱
4. **CI 驗證**：別名覆蓋率由 CI 自動檢查（`scripts/ci/check_settings_aliases.py`）

### 關鍵別名映射

以下是已修復和標準化的關鍵環境變數別名：

| 正式名稱（推薦） | 舊名稱（別名） | 狀態 | 安全等級 | 說明 |
|-----------------|---------------|------|----------|------|
| `FLASK_SECRET_KEY` | `SECRET_KEY` | ⚠️ 已棄用 | 🔒 CRITICAL | Flask 應用程式會話密鑰 |
| `ENCRYPTION_MASTER_KEY` | `MASTER_KEY` | ⚠️ 已棄用 | 🔒 CRITICAL | 主加密密鑰 |
| `STRIPE_WEBHOOK_SECRET_KEY` | `STRIPE_WEBHOOK_SECRET` | ⚠️ 已棄用 | 🔒 SECRET | Stripe Webhook 驗證密鑰 |

**重要提示**：
- 🔒 標記為 CRITICAL 的變數必須至少 64 字符，使用加密隨機生成
- ⚠️ 已棄用的名稱仍然有效，但建議遷移到正式名稱
- 在生產環境中，優先使用正式名稱以避免混淆

### 新增別名（2025-11-23）

以下 23 個環境變數現在支援通過 Pydantic 別名加載：

#### 認證與安全
- `ACCESS_TOKEN_EXPIRY_MINUTES` - JWT 訪問令牌過期時間（分鐘）
- `LOG_TOKEN_EXPIRY_ON_STARTUP` - 啟動時記錄令牌過期配置
- `FEATURE_2FA_ENABLED` - 啟用 2FA/TOTP 功能
- `FEATURE_2FA_PREAUTH` - 啟用預認證令牌流程
- `PREAUTH_TOKEN_TTL` - 預認證令牌 TTL（秒）

#### 測試與開發
- `RLS_TESTS_ALLOWED` - 允許 RLS 測試（僅測試環境）
- `TEST_SUPABASE_URL` - 測試環境 Supabase URL
- `ENABLE_MOCK_USERS` - 啟用模擬用戶（⚠️ 生產環境必須為 false）
- `STAGING_API_URL` - Staging 環境 API URL
- `STAGING_TEST_EMAIL` - Staging 測試用戶郵箱

#### 基礎設施與監控
- `REDIS_KEY_PREFIX` - Redis 鍵前綴（例如：`stg:` 用於 staging）
- `RQ_QUEUE_NAME` - Redis Queue 隊列名稱（默認：`orchestrator`）
- `RQ_JOB_TIMEOUT` - RQ worker job timeout 秒數（默認：`600`）- 控制 LLM Planner 等長時間運行任務的超時時間
- `DB_POOL_MAX` - 數據庫連接池最大連接數
- `SENTRY_DSN` - Sentry 錯誤追蹤 DSN
- `SENTRY_ENVIRONMENT` - Sentry 環境標識（production/staging/development）
- `PORT` - 應用程式監聽端口
- `LOG_LEVEL` - 日誌級別（DEBUG/INFO/WARNING/ERROR）
- `DEBUG` - 調試模式開關

#### Cookie 與會話
- `COOKIE_SECURE` - Cookie Secure 標誌（生產環境應為 true）
- `COOKIE_SAMESITE` - Cookie SameSite 屬性（Strict/Lax/None）
- `COOKIE_DOMAIN` - Cookie 域名
- `COOKIE_PATH` - Cookie 路徑

#### 其他
- `MEMORY_TABLE` - 記憶體表名稱（用於 pgvector 存儲）

### 別名驗證與 CI

**驗證腳本**：`scripts/ci/check_settings_aliases.py`

此腳本檢查 `config/env.schema.yaml` 中定義的所有環境變數是否在 `common/config/settings.py` 中有對應的 Pydantic 別名。

**CI 工作流**：[`.github/workflows/settings-alias-audit.yml`](../.github/workflows/settings-alias-audit.yml)

自動運行別名覆蓋率檢查（warn-only 模式，不阻擋合併），確保配置系統的一致性。

**目前別名狀態（快照）***：

- 總變數數量：148（來自 `config/env.schema.yaml`）
- 排除項目：11 個（前端專用 / 已棄用等）
- 必要變數：137
- 已有別名：約 109 個（約 80% 覆蓋率）
- 缺少別名：28 個

\* 根據 2025-11-23 執行的 `scripts/ci/check_settings_aliases.py` 稽核結果。可透過運行 `python scripts/ci/check_settings_aliases.py` 重新計算。

**目標**：100% 覆蓋率（所有 `env.schema.yaml` 中的必要變數都應在 `settings.py` 中有別名）

### 使用建議

1. **新部署**：使用正式名稱（表格中的"正式名稱"列）
2. **現有部署**：可以繼續使用舊名稱，但建議逐步遷移
3. **遷移策略**：
   ```bash
   # 步驟 1: 在 .env 中同時設置新舊名稱
   FLASK_SECRET_KEY=your_secret_key
   SECRET_KEY=your_secret_key  # 保留以確保相容性
   
   # 步驟 2: 驗證應用程式正常運行
   # 步驟 3: 移除舊名稱
   FLASK_SECRET_KEY=your_secret_key
   ```
4. **安全考慮**：
   - 🚫 **絕對不要**在生產環境中設置 `ENABLE_MOCK_USERS=true`
   - 🚫 **絕對不要**在生產/staging 環境中設置 `RLS_TESTS_ALLOWED=true`
   - ✅ 在生產環境中始終使用 `COOKIE_SECURE=true`

### 技術實現

別名通過 Pydantic 的 `Field` 定義實現：

```python
# common/config/settings.py 示例
class Settings(BaseSettings):
    flask_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="FLASK_SECRET_KEY",  # 正式名稱
        description="Flask application secret key for sessions",
        repr=False
    )
    
    # 舊名稱通過 Pydantic 的環境變數加載自動支援
    # 如果同時設置了新舊名稱，新名稱（alias）優先
```

**加載優先級**：
1. 環境變數（使用 alias 名稱）
2. .env 文件（使用 alias 名稱）
3. 默認值

### 相關文檔

- **配置 Schema**：`config/env.schema.yaml` - 所有環境變數的單一真實來源
- **Pydantic 設置**：`common/config/settings.py` - 類型安全的配置類
- **別名檢查腳本**：`scripts/ci/check_settings_aliases.py` - CI 驗證工具
- **環境變數生成**：`scripts/generate-env-examples.py` - 生成 .env.example 文件

---

## 🧪 Staging Environment

### Services

#### Backend API Staging
- **URL**: https://morningai-backend-v2-stg.onrender.com
- **Service Name**: `morningai-backend-v2-stg`
- **Platform**: Render
- **Runtime**: Python 3
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Health Check**: `GET /healthz`
- **Status**: ✅ Healthy

**Health Check Response**:
```json
{
  "database": "connected",
  "phase": "Phase 8: Self-service Dashboard & Reporting Center",
  "redis": {
    "protocol": "rediss",
    "status": "connected",
    "tls_enabled": true,
    "type": "redis",
    "url": "main-gull-14059.upstash.io:6379"
  },
  "services": {
    "backend_services": "available",
    "phase4_apis": "available",
    "phase5_apis": "available",
    "phase6_apis": "available",
    "security_manager": "available"
  },
  "status": "healthy",
  "timestamp": "2025-10-28T08:18:16.548126",
  "version": "8.0.0"
}
```

#### Orchestrator API Staging
- **URL**: https://morningai-orchestrator-api-stg.onrender.com
- **Service Name**: `morningai-orchestrator-api-stg`
- **Platform**: Render
- **Runtime**: Docker
- **Dockerfile**: `orchestrator/Dockerfile`
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Health Check**: `GET /health`
- **Status**: ✅ Healthy

**Health Check Response**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 292,
    "processing_tasks": 62,
    "total_tasks": 354
  }
}
```

#### Frontend Dashboard Staging
- **URL**: https://staging.morningai.me
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Status**: ✅ Healthy

#### Owner Console Staging
- **URL**: https://staging-owner.morningai.me
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `develop`
- **Auto-Deploy**: Yes (on push to `develop`)
- **Status**: ✅ Healthy

**Deployment Strategy**:
- **Branch Policy**: `develop` → staging, `main` → production, `feature/*|fix/*|devin/*` → preview
- **Ignore Script**: `scripts/vercel-ignore.sh` (skips docs-only changes)
- **Documentation**: See [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](deployment/VERCEL_DEPLOYMENT_STRATEGY.md) for complete setup and troubleshooting

### Infrastructure

#### Database
- **Provider**: Supabase PostgreSQL
- **Project Name**: `morningai-staging`
- **Project ID**: `dckisglnlemvpvmyvnut`
- **URL**: https://dckisglnlemvpvmyvnut.supabase.co
- **Connection**: Pooler (port 6543)
- **Data**: Separate from production
- **Schema**: Minimal test schema (tenants, user_profiles, agent_tasks)
- **Purpose**: RLS testing and security validation

⚠️ **Important**: Staging database has a minimal schema for security testing. Not all production tables exist in staging. This is intentional to keep the staging environment lightweight and focused on P0 security testing.

#### Redis
- **Provider**: Upstash (shared with production)
- **Protocol**: `rediss://` (TLS enabled)
- **Key Prefix**: `stg:` (isolates staging data)
- **Queue Name**: `orchestrator-staging`

#### Monitoring
- **Error Tracking**: Sentry
- **Environment Tag**: `staging`
- **Cost**: ~$14/month (Render Starter plans)

### Environment Variables

**Backend Staging**:
```bash
# Environment
ENVIRONMENT=staging

# Database (Staging Supabase)
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>

# Redis (Shared with production, isolated by prefix)
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
RQ_JOB_TIMEOUT=600                      # Job timeout in seconds (default: 600 = 10 minutes)

# Database Connection Pool
DB_POOL_SIZE=5
DB_POOL_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Security (Different from production)
JWT_SECRET_KEY=<staging-secret>
SECRET_KEY=<staging-secret>
MASTER_ENCRYPTION_KEY=<staging-secret>

# Monitoring
SENTRY_DSN=<same-as-production>
SENTRY_ENVIRONMENT=staging

# Rate Limiting (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=false              # Allow startup without Redis (staging)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Orchestrator Staging**:
```bash
# Environment
ENVIRONMENT=staging
PORT=8000

# Security (REQUIRED)
ORCHESTRATOR_JWT_SECRET=<staging-orchestrator-secret-48-chars>

# Redis (REQUIRED)
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
RQ_JOB_TIMEOUT=600                      # Job timeout in seconds (default: 600 = 10 minutes)

# Optional
ORCHESTRATOR_CORS_ORIGINS=https://morningai-staging.vercel.app,http://localhost:5173
SENTRY_ENVIRONMENT=staging
LOG_LEVEL=INFO
```

### Setup Documentation

For complete staging environment setup instructions, see:
- **[Staging Setup Guide](ops/STAGING_SETUP_GUIDE.md)** - Comprehensive setup guide with step-by-step instructions

---

## 💻 Local Development Environment

### Services

#### Backend API
- **URL**: http://localhost:8000
- **Runtime**: Python 3.12+
- **Framework**: Flask
- **Start Command**: 
  ```bash
  # Option 1: Flask CLI (recommended for development)
  export FLASK_APP=src.main
  flask run --port 8000
  
  # Option 2: Gunicorn (production-like)
  gunicorn "src.main:app" --bind 0.0.0.0:8000 --reload
  
  # Quick one-liner (equivalent to Option 1)
  export FLASK_APP=src.main && flask run --port 8000
  ```
- **Working Directory**: `handoff/20250928/40_App/api-backend`

#### Orchestrator API
- **URL**: http://localhost:8001
- **Runtime**: Python 3.12+
- **Framework**: FastAPI
- **Start Command**: `uvicorn orchestrator.api.main:app --port 8001 --reload`
- **Working Directory**: Repository root

#### Frontend Dashboard
- **URL**: http://localhost:5173
- **Runtime**: Node.js 20+
- **Start Command**: `npm run dev`
- **Working Directory**: `handoff/20250928/40_App/frontend-dashboard`

### Infrastructure

#### Database
- **Option 1**: Local PostgreSQL
- **Option 2**: Staging Supabase (recommended for testing)
- **Option 3**: Production Supabase (read-only, for debugging)

#### Redis
- **Option 1**: Local Redis (`redis://localhost:6379/0`)
- **Option 2**: Staging Redis (recommended for testing)

### Environment Variables

Create `.env` file in each service directory:

**Backend `.env`**:
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0
TESTING=false

# Or use staging infrastructure
DATABASE_URL=<staging-database-url>
REDIS_URL=<staging-redis-url>
REDIS_KEY_PREFIX=dev:

# Rate Limiting (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=false              # Allow startup without Redis (development)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Testing Flags** (⚠️ **DEVELOPMENT/TEST ONLY** - Added Nov 2025):
```bash
# Enable rate limiting in test environment (default: false)
ENABLE_RATE_LIMIT_IN_TESTS=false

# Enable Playwright browser E2E tests (requires staging credentials)
RUN_PY_BROWSER_E2E=false

# Flask environment mode (now accepts 'testing' for test environments)
FLASK_ENV=testing  # Options: development, staging, production, testing (default: development)
```

**⚠️ CRITICAL:** These flags MUST ONLY be set in test/development environments. Never set in production/staging.

**Schema:** See `config/env.schema.yaml` for complete definitions and constraints.

**Frontend `.env.local`**:
```bash
VITE_API_URL=http://localhost:8000
VITE_ORCHESTRATOR_URL=http://localhost:8001
VITE_ENVIRONMENT=development

# Or point to staging backend
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
VITE_ORCHESTRATOR_URL=https://morningai-orchestrator-api-stg.onrender.com
```

**VITE_API_BASE_URL** (Frontend - Added/Updated Nov 2025):
```bash
# For Vercel preview/production deployments (uses Vercel proxy)
VITE_API_BASE_URL=/api

# For local development or direct backend access
VITE_API_BASE_URL=http://localhost:8000/api
# or
VITE_API_BASE_URL=https://morningai-backend-v2-stg.onrender.com/api
```

**Important:** The value must include the `/api` suffix. For Vercel deployments, use `/api` (relative path) to leverage Vercel's proxy. For direct backend access, use the full URL with `/api` suffix.

**Schema:** See `config/env.schema.yaml` for complete definition.

**VITE_TRACE_VIEWER_URL** (Frontend - Added Nov 2025):
```bash
# Optional: URL for observability platform trace viewer
# Used to link trace IDs in Agent Execution Logs to detailed trace views
# Leave empty or unset to disable trace links

# Jaeger
VITE_TRACE_VIEWER_URL=https://jaeger.gm365.me

# Tempo (Grafana)
VITE_TRACE_VIEWER_URL=https://tempo.gm365.me

# Grafana Explore
VITE_TRACE_VIEWER_URL=https://grafana.gm365.me/explore

# For testing (any URL)
VITE_TRACE_VIEWER_URL=https://example.com
```

**Behavior:**
- When set: External link icon appears next to trace IDs in Agent Execution Logs
- When unset or empty: Only copy button appears (no external link)
- Link format: `{VITE_TRACE_VIEWER_URL}/trace/{encoded_trace_id}`
- Security: Trace IDs are automatically URL-encoded using `encodeURIComponent()`

**Usage Locations:**
- Owner Console → Agent Governance → Agent Execution Logs (desktop table view)
- Owner Console → Agent Governance → Agent Execution Logs (mobile card view)
- Owner Console → Agent Governance → Agent Execution Logs (execution details drawer)

**Testing:**
1. Set `VITE_TRACE_VIEWER_URL` in `.env.local` or Vercel environment variables
2. Navigate to Agent Governance page in Owner Console
3. Verify external link icon appears next to trace IDs
4. Click link to verify it opens in new tab with correct URL format

**Schema:** See `config/env.schema.yaml` for complete definition.

### Setup Documentation

For complete local development setup instructions, see:
- **[Local Development Setup](setup_local.md)** - Quick start guide and troubleshooting

---

## 🔔 Monitor Orchestrator Behavior

The monitor orchestrator (`scripts/monitor_orchestrator.py`) performs health checks and queue monitoring for the Orchestrator API.

### Slack Notifications

**Graceful Degradation** (Default Behavior):
- **Optional**: If `SLACK_WEBHOOK_URL` is not configured, the monitor will continue to run
- **Console Fallback**: Alerts are printed to console instead of sent to Slack
- **Use Case**: Allows CI/CD workflows (GitHub Actions) to succeed even without Slack integration
- **Exit Code**: Monitor exit code reflects health/queue check results, not Slack notification status

**Production Recommendations**:
- ✅ **Recommended**: Configure `SLACK_WEBHOOK_URL` in GitHub Secrets for real-time alerts
- ✅ Monitor GitHub Actions logs for console output when Slack is not configured
- ⚠️ **Warning**: If Slack webhook is accidentally removed, alerts will only appear in logs

**Configuration**:
```bash
# Optional - enables Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional - override default Orchestrator API URL
ORCHESTRATOR_API_URL=https://morningai-orchestrator-api.onrender.com
```

**Behavior Examples**:

*With Slack configured*:
```bash
$ python scripts/monitor_orchestrator.py
Checking health: https://morningai-orchestrator-api.onrender.com/health
✓ Health check passed (response time: 0.23s)
✓ Queue stats: pending=5, processing=2, total=7
✓ All checks passed
# Slack alert sent to channel
```

*Without Slack configured*:
```bash
$ python scripts/monitor_orchestrator.py
[WARNING] SLACK_WEBHOOK_URL not configured - Slack alerts disabled
[INFO] Continuing with health checks only (no Slack notifications)
Checking health: https://morningai-orchestrator-api.onrender.com/health
✓ Health check passed (response time: 0.23s)
✓ Queue stats: pending=5, processing=2, total=7
✓ All checks passed
# No Slack alert sent - alerts printed to console only
```

*When critical issues detected (without Slack)*:
```bash
$ python scripts/monitor_orchestrator.py
[WARNING] SLACK_WEBHOOK_URL not configured - Slack alerts disabled
[INFO] Continuing with health checks only (no Slack notifications)
Checking health: https://morningai-orchestrator-api.onrender.com/health
[CRITICAL] Health Check Failed - Connection Error
Unable to connect to the API.
URL: https://morningai-orchestrator-api.onrender.com/health
Possible causes: Service is down, network issue, or DNS problem
✗ Some checks failed
# Exit code: 1 (failure)
```

**GitHub Actions Integration**:

The monitor runs every 5 minutes via GitHub Actions workflow (`.github/workflows/monitor-orchestrator.yml`). The workflow will:
- ✅ **Succeed** if health checks pass (even without Slack configured)
- ❌ **Fail** if health checks fail (alerts visible in workflow logs)
- 📊 Alerts are visible in GitHub Actions logs regardless of Slack configuration

---

## 🔧 Import Path Configuration

Services that import the `common` module use a multi-tier fallback mechanism to ensure imports work across all environments.

### Priority Order

| Priority | Mechanism | Use Case | Example |
|----------|-----------|----------|---------|
| 1 | REPO_ROOT | Explicit control | `REPO_ROOT=/app` |
| 2 | PYTHONPATH | Standard Python | `PYTHONPATH=/app:/other` |
| 3 | Marker files | Auto-discovery | `.git`, `pyproject.toml`, `env.schema.yaml` or `env_schema.yaml` |

### Configuration by Environment

**Docker Containers**:
```dockerfile
ENV REPO_ROOT=/app
ENV PYTHONPATH=/app
```

**Render Services**:
```yaml
envVars:
  - key: REPO_ROOT
    value: /app
  - key: PYTHONPATH
    value: /app
  - key: DEBUG_IMPORTS
    value: "false"  # Set to "true" for troubleshooting
```

**Local Development**:
```bash
export REPO_ROOT=/path/to/morningai
export DEBUG_IMPORTS=true
```

### Debugging Import Issues

**Enable import debugging**:
```bash
DEBUG_IMPORTS=true python monitoring/braintrust_processor.py
```

**Expected output**:
```
✅ sys.path bootstrap: REPO_ROOT=/app
Final sys.path (first 3): ['', '/app', '/usr/local/lib/python311.zip']
```

**Verify configuration in Docker**:
```bash
# Check environment variables
docker exec <container> env | grep -E 'REPO_ROOT|PYTHONPATH'

# Check sys.path
docker exec <container> python -c "import sys; print(sys.path[:5])"

# Test import
docker exec <container> python -c "from common.config.settings import settings; print('✅ Import successful')"
```

### Affected Services

- **Braintrust Processor** (`monitoring/braintrust_processor.py`)
- **API Backend** (`handoff/20250928/40_App/api-backend/gunicorn.conf.py`)

### Troubleshooting

See [monitoring/DEPLOYMENT.md](../monitoring/DEPLOYMENT.md#troubleshooting) for detailed troubleshooting steps.

---

## 🔄 Deployment Workflow

### Development Flow

```mermaid
graph LR
    A[Feature Branch] -->|PR| B[develop]
    B -->|Auto-deploy| C[Staging Environment]
    C -->|Manual Test| D{Tests Pass?}
    D -->|Yes| E[PR to main]
    E -->|Manual Approval| F[Production]
    D -->|No| A
```

### Step-by-Step Process

#### 1. Feature Development
```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Develop and commit
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

#### 2. Staging Deployment
```bash
# Create PR to develop
# GitHub Actions will:
# - Run staging CI checks
# - Auto-deploy to Render staging services

# Test on staging
curl https://morningai-backend-v2-stg.onrender.com/healthz
```

#### 3. Production Deployment
```bash
# After staging tests pass, create PR to main
# Requires manual approval
# Auto-deploys to production services
```

### CI/CD Workflows

#### Staging CI (`.github/workflows/staging-deploy.yml`)
- **Trigger**: Push/PR to `develop` branch
- **Tests**: Backend (pytest + coverage), Frontend (build), Smoke tests
- **Deploy**: Auto-deploy to Render staging services
- **Environment**: `ENVIRONMENT=staging`

#### Production CI (`.github/workflows/backend.yml`, etc.)
- **Trigger**: Push to `main` branch
- **Tests**: Full test suite, E2E tests
- **Deploy**: Auto-deploy to production services
- **Validation**: Post-deploy health checks (90% SLA)

---

## 🧪 Testing Environments

### Health Check Commands

**Production**:
```bash
# Backend
curl https://morningai-backend-v2.onrender.com/healthz

# Orchestrator
curl https://morningai-orchestrator-api.onrender.com/health

# Monitoring Dashboard
curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard
```

**Staging**:
```bash
# Backend
curl https://morningai-backend-v2-stg.onrender.com/healthz

# Orchestrator
curl https://morningai-orchestrator-api-stg.onrender.com/health

# Monitoring Dashboard
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard
```

**Local**:
```bash
# Backend
curl http://localhost:8000/healthz

# Orchestrator
curl http://localhost:8001/health

# Monitoring Dashboard
curl http://localhost:8000/api/phase7/monitoring/dashboard
```

### Monitoring Dashboard Endpoints

**Primary Endpoint** (Recommended):
- **Path**: `/api/phase7/monitoring/dashboard`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ✅ Production Ready

**Legacy Endpoint** (Deprecated):
- **Path**: `/api/dashboard/data`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ⚠️ **DEPRECATED** - Use `/api/phase7/monitoring/dashboard` instead
- **Deprecation Timeline**: TBD (tracked in future release notes)

**Degradation Behavior**:

| Scenario | HTTP Status | Response Behavior |
|----------|-------------|-------------------|
| All services healthy | 200 OK | Full metrics with real data |
| Redis unavailable | 200 OK | Fallback metrics with `available: false`, `source: 'fallback'`, `error: 'Redis unavailable'` |
| Database unavailable | 200 OK | `overall_status: 'degraded'` with critical alert |
| Both Redis + DB unavailable | 503 Service Unavailable | `ServiceUnavailableError` response |

**Environment Variables**:
- `REDIS_URL`: Required for queue metrics
- `DATABASE_URL`: Required for health checks
- `BACKEND_SERVICES_AVAILABLE`: Gate flag (auto-set by backend)

**Documentation**: See [Monitoring Troubleshooting Guide](deployment/troubleshooting-monitoring.md) for 503 error diagnosis

### Expected Responses

**Backend `/healthz`**:
```json
{
  "status": "healthy",
  "phase": "Phase 8",
  "version": "8.0.0",
  "database": "connected",
  "redis": {
    "status": "connected",
    "protocol": "rediss",
    "tls_enabled": true
  },
  "services": {
    "backend_services": "available",
    "phase4_apis": "available",
    "phase5_apis": "available",
    "phase6_apis": "available",
    "security_manager": "available"
  }
}
```

**Orchestrator `/health`**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 0,
    "processing_tasks": 0,
    "total_tasks": 0
  }
}
```

---

## 🔐 Security & Secrets

### Secret Management

**Production Secrets**:
- Stored in Render dashboard (encrypted)
- Different from staging secrets
- Minimum 32 characters for JWT/encryption keys
- Rotated quarterly

**Staging Secrets**:
- Stored in Render dashboard (encrypted)
- Different from production secrets
- Can use weaker secrets (but still 32+ chars)
- Rotated as needed

**Local Secrets**:
- Stored in `.env` files (gitignored)
- Can use test/dummy values
- Never commit to repository

### Secret Generation

```bash
# Generate JWT secret (48 characters recommended)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Generate encryption key (32 characters minimum)
openssl rand -hex 32

# Generate API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 Monitoring & Observability

### Sentry Error Tracking

**Production**:
- Environment: `production`
- Dashboard: https://sentry.io/organizations/morningai/issues/?environment=production
- Alerts: Enabled for critical errors

**Staging**:
- Environment: `staging`
- Dashboard: https://sentry.io/organizations/morningai/issues/?environment=staging
- Alerts: Disabled (testing environment)

### Render Monitoring

**Production Services**:
- Dashboard: https://dashboard.render.com/
- Metrics: CPU, Memory, Request count
- Logs: Real-time log streaming
- Alerts: Enabled for downtime

**Staging Services**:
- Dashboard: https://dashboard.render.com/
- Auto-suspend: Enabled (15 minutes inactivity)
- Cost optimization: ~50% savings

### Supabase Monitoring

**Production Database**:
- Dashboard: https://supabase.com/dashboard/project/[production-id]
- Metrics: Connection pool, Query performance
- Backups: Daily automatic backups

**Staging Database**:
- Dashboard: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- Metrics: Connection pool, Query performance
- Data cleanup: Monthly manual cleanup

---

## 💰 Cost Breakdown

### Production
- **Render Backend**: $7/month (Starter)
- **Render Orchestrator**: $7/month (Starter)
- **Vercel Frontend**: $0/month (Free tier)
- **Supabase Database**: $0/month (Free tier) or $25/month (Pro)
- **Upstash Redis**: $0/month (Free tier) or $10/month (Pay-as-you-go)
- **Total**: ~$14-49/month

### Staging
- **Render Backend**: $7/month (Starter, auto-suspend enabled)
- **Render Orchestrator**: $7/month (Starter, auto-suspend enabled)
- **Supabase Database**: $0/month (Free tier)
- **Upstash Redis**: $0/month (Shared with production)
- **Total**: ~$14/month (effective ~$7/month with auto-suspend)

### Local Development
- **Cost**: $0/month
- **Infrastructure**: Developer workstation only

---

## 🚨 Troubleshooting

### Common Issues

#### Issue: Service won't start
**Check**:
1. Build logs in Render dashboard
2. All required environment variables are set
3. `DATABASE_URL` format is correct
4. `REDIS_URL` is accessible

**Fix**:
```bash
# Test DATABASE_URL locally
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Test REDIS_URL locally
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

#### Issue: Database connection fails
**Check**:
1. Supabase project is running (not paused)
2. `DATABASE_URL` includes correct password
3. Connection pooler is enabled (port 6543)
4. IP allowlist includes Render IPs (if configured)

**Fix**:
- Get fresh `DATABASE_URL` from Supabase dashboard → Settings → Database → Connection string (Pooler)

#### Issue: Redis connection fails
**Check**:
1. `REDIS_URL` uses `rediss://` (double s) for TLS
2. Upstash Redis is accessible
3. Password is correct

**Fix**:
- Get fresh `REDIS_URL` from Upstash dashboard
- Ensure `rediss://` scheme (not `redis://`)

#### Issue: ORCHESTRATOR_JWT_SECRET error
**Error**: `CRITICAL SECURITY ERROR: ORCHESTRATOR_JWT_SECRET environment variable is not set`

**Fix**:
```bash
# Generate new secret (48 characters)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Add to Render environment variables
# Key: ORCHESTRATOR_JWT_SECRET
# Value: <generated-secret>
```

#### Issue: Staging auto-suspend too aggressive
**Fix**:
- Disable auto-suspend in Render dashboard
- Or: Set up cron job to ping `/healthz` every 10 minutes

---

## 📝 Best Practices

### Development
1. **Always test on staging first** before merging to `main`
2. **Use feature branches** for all development
3. **Run tests locally** before pushing
4. **Keep staging data separate** from production

### Deployment
1. **Review staging deployment** before production
2. **Monitor health checks** after deployment
3. **Check Sentry** for errors after deployment
4. **Have rollback plan** ready

### Security
1. **Never commit secrets** to repository
2. **Use different secrets** for each environment
3. **Rotate secrets** quarterly (production) or as needed (staging)
4. **Use TLS** for all external connections (`rediss://`, `https://`)

### Cost Optimization
1. **Enable auto-suspend** for staging services
2. **Clean up staging data** monthly
3. **Monitor usage** in Render/Supabase dashboards
4. **Use free tiers** where possible

---

## 🔗 Quick Links

### Production
- **Backend**: https://morningai-backend-v2.onrender.com
- **Orchestrator**: https://morningai-orchestrator-api.onrender.com
- **Tenant Dashboard**: https://app.gm365.me
- **Owner Console**: https://admin.gm365.me
- **Render Dashboard**: https://dashboard.render.com/

### Staging
- **Backend**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator**: https://morningai-orchestrator-api-stg.onrender.com
- **Supabase**: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- **Setup Guide**: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)

### Documentation
- **Local Setup**: [docs/setup_local.md](setup_local.md)
- **Contributing**: [docs/CONTRIBUTING.md](CONTRIBUTING.md)
- **CI/CD**: [docs/ci_matrix.md](ci_matrix.md)
- **Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Authentication API**: [docs/openapi.auth.yaml](openapi.auth.yaml) - 2FA/TOTP endpoints (OpenAPI 3.0.3)

---

**Last Updated**: 2025-10-28  
**Maintained By**: CTO / DevOps Team  
**Status**: ✅ All environments operational
