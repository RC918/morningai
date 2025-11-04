# PR #562 關鍵修復指南

**目標**: 修復 2 個 P0 關鍵安全問題，使 PR #562 可以安全合併

**預計時間**: 1.5 小時

---

## 🔴 Critical Issue #1: JWT Secret 預設值不安全

### 問題描述

**檔案**: `orchestrator/api/auth.py:31`

**當前代碼**:
```python
JWT_SECRET_KEY = os.getenv("ORCHESTRATOR_JWT_SECRET", "change-me-in-production")
```

**問題**:
- 如果生產環境忘記設定 `ORCHESTRATOR_JWT_SECRET`，將使用預設值 `"change-me-in-production"`
- 攻擊者可以使用此預設 secret 偽造任何 JWT token
- 可以提升權限至 admin 角色，完全繞過身份驗證

**影響**: 🔴 **CRITICAL** - 完全繞過身份驗證系統

### 修復方案

**步驟 1**: 修改 `orchestrator/api/auth.py`

找到第 29-33 行:
```python
class AuthConfig:
    """Authentication configuration"""
    JWT_SECRET_KEY = os.getenv("ORCHESTRATOR_JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
```

替換為:
```python
class AuthConfig:
    """Authentication configuration"""
    JWT_SECRET_KEY = os.getenv("ORCHESTRATOR_JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    @classmethod
    def validate_config(cls):
        """Validate authentication configuration on startup"""
        if not cls.JWT_SECRET_KEY:
            raise RuntimeError(
                "ORCHESTRATOR_JWT_SECRET environment variable is required. "
                "Generate a secure secret with: openssl rand -hex 32"
            )
        if cls.JWT_SECRET_KEY == "change-me-in-production":
            raise RuntimeError(
                "Default JWT secret detected. This is a critical security issue! "
                "Set a secure ORCHESTRATOR_JWT_SECRET environment variable."
            )
        if len(cls.JWT_SECRET_KEY) < 32:
            logger.warning(
                f"JWT secret is only {len(cls.JWT_SECRET_KEY)} characters. "
                "Recommended minimum: 32 characters for HS256."
            )
```

**步驟 2**: 在應用啟動時調用驗證

修改 `orchestrator/api/main.py`，在 `lifespan` 函數中新增驗證:

找到第 32-51 行:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global redis_queue, orchestrator_router, hitl_gate
    
    logger.info("Starting Orchestrator API")
    
    redis_queue = await create_redis_queue()
    
    orchestrator_router = OrchestratorRouter(redis_queue)
    
    hitl_gate = HITLGate(redis_queue)
    
    logger.info("Orchestrator API started successfully")
    
    yield
    
    logger.info("Shutting down Orchestrator API")
    if redis_queue:
        await redis_queue.disconnect()
```

在 `logger.info("Starting Orchestrator API")` 之後新增:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global redis_queue, orchestrator_router, hitl_gate
    
    logger.info("Starting Orchestrator API")
    
    # Validate authentication configuration
    from orchestrator.api.auth import AuthConfig
    AuthConfig.validate_config()
    logger.info("Authentication configuration validated")
    
    redis_queue = await create_redis_queue()
    
    orchestrator_router = OrchestratorRouter(redis_queue)
    
    hitl_gate = HITLGate(redis_queue)
    
    logger.info("Orchestrator API started successfully")
    
    yield
    
    logger.info("Shutting down Orchestrator API")
    if redis_queue:
        await redis_queue.disconnect()
```

**步驟 3**: 更新 README 文件

在 `orchestrator/README.md` 的環境變數部分新增警告:

```markdown
### 🔴 CRITICAL: JWT Secret

**必須設定** `ORCHESTRATOR_JWT_SECRET` 環境變數:

```bash
# 生成安全的 secret (推薦)
export ORCHESTRATOR_JWT_SECRET=$(openssl rand -hex 32)

# 或手動設定 (至少 32 字元)
export ORCHESTRATOR_JWT_SECRET="your-very-long-and-random-secret-key-here"
```

⚠️ **警告**: 
- 不設定此變數，應用將無法啟動
- 使用弱 secret 會導致嚴重安全漏洞
- 生產環境必須使用強隨機 secret
```

### 驗證修復

**測試 1**: 啟動時未設定 secret
```bash
cd orchestrator
unset ORCHESTRATOR_JWT_SECRET
python -m orchestrator.api.main
```

**預期結果**: 應該拋出 `RuntimeError` 並顯示錯誤訊息

**測試 2**: 使用預設 secret
```bash
export ORCHESTRATOR_JWT_SECRET="change-me-in-production"
python -m orchestrator.api.main
```

**預期結果**: 應該拋出 `RuntimeError` 並顯示錯誤訊息

**測試 3**: 使用安全 secret
```bash
export ORCHESTRATOR_JWT_SECRET=$(openssl rand -hex 32)
python -m orchestrator.api.main
```

**預期結果**: 應用正常啟動

---

## 🔴 Critical Issue #2: Rate Limiter 未正確初始化

### 問題描述

**檔案**: `orchestrator/api/main.py:70`

**當前代碼**:
```python
app.add_middleware(RateLimitMiddleware, redis_client=None)
```

**問題**:
- `redis_client=None` 導致 Rate Limiter 使用本地記憶體 fallback
- 失去分散式限流能力
- 多個 API 實例無法共享限流狀態
- 攻擊者可以繞過限流 (向不同實例發送請求)

**影響**: 🔴 **HIGH** - 限流失效 (多實例環境)

### 修復方案

**問題**: Middleware 在 `lifespan` 之前初始化，此時 `redis_queue` 尚未創建

**解決方案**: 使用 `app.state` 延遲初始化

**步驟 1**: 修改 `orchestrator/api/main.py`

找到第 54-70 行:
```python
app = FastAPI(
    title="MorningAI Orchestrator",
    description="Multi-Agent Task Orchestration and Event Bus",
    version="1.0.0",
    lifespan=lifespan
)

allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

app.add_middleware(RateLimitMiddleware, redis_client=None)
```

修改為:
```python
app = FastAPI(
    title="MorningAI Orchestrator",
    description="Multi-Agent Task Orchestration and Event Bus",
    version="1.0.0",
    lifespan=lifespan
)

allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Rate limiting will be initialized in lifespan with Redis client
# Middleware is added after lifespan initialization
```

**步驟 2**: 修改 `lifespan` 函數以儲存 Redis client

找到 `lifespan` 函數，修改為:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global redis_queue, orchestrator_router, hitl_gate
    
    logger.info("Starting Orchestrator API")
    
    # Validate authentication configuration
    from orchestrator.api.auth import AuthConfig
    AuthConfig.validate_config()
    logger.info("Authentication configuration validated")
    
    redis_queue = await create_redis_queue()
    
    # Store Redis client in app state for middleware
    app.state.redis_client = redis_queue.redis_client
    
    orchestrator_router = OrchestratorRouter(redis_queue)
    
    hitl_gate = HITLGate(redis_queue)
    
    # Add rate limiting middleware with Redis client
    from orchestrator.api.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, redis_client=redis_queue.redis_client)
    logger.info("Rate limiting enabled with Redis backend")
    
    logger.info("Orchestrator API started successfully")
    
    yield
    
    logger.info("Shutting down Orchestrator API")
    if redis_queue:
        await redis_queue.disconnect()
```

**步驟 3**: 修改 `RateLimitMiddleware` 以支援延遲初始化

修改 `orchestrator/api/rate_limiter.py`，找到第 130-139 行:
```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, redis_client: Optional[Redis] = None):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            redis_client: Redis client for distributed rate limiting
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_client)
```

修改為:
```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, redis_client: Optional[Redis] = None):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            redis_client: Redis client for distributed rate limiting
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_client)
        
        if redis_client:
            logger.info("Rate limiter initialized with Redis (distributed mode)")
        else:
            logger.warning(
                "Rate limiter initialized without Redis (local memory fallback). "
                "This is NOT suitable for production with multiple instances."
            )
```

### 驗證修復

**測試 1**: 檢查啟動日誌
```bash
cd orchestrator
export ORCHESTRATOR_JWT_SECRET=$(openssl rand -hex 32)
export REDIS_URL="redis://localhost:6379"
python -m orchestrator.api.main
```

**預期日誌**:
```
INFO:     Starting Orchestrator API
INFO:     Authentication configuration validated
INFO:     Rate limiting enabled with Redis backend
INFO:     Rate limiter initialized with Redis (distributed mode)
INFO:     Orchestrator API started successfully
```

**測試 2**: 驗證 Redis 連接
```bash
# 在另一個終端
redis-cli
> KEYS rate_limit:*
```

發送幾個請求後，應該看到 rate limit keys

**測試 3**: 測試限流功能
```bash
# 快速發送多個請求
for i in {1..10}; do
  curl -X POST http://localhost:8000/tasks \
    -H "Content-Type: application/json" \
    -H "X-API-Key: your-api-key" \
    -d '{"type":"faq","payload":{}}'
done
```

**預期結果**: 
- 前 30 個請求成功 (假設 `/tasks` 限制為 30/min)
- 第 31 個請求返回 429 Too Many Requests
- Response headers 包含 `X-RateLimit-*`

---

## 📋 完整修復檢查清單

### 修復前準備

- [ ] 切換到 PR #562 分支
  ```bash
  cd /home/ubuntu/repos/morningai
  git checkout devin/1761047019-api-auth-security
  git pull origin devin/1761047019-api-auth-security
  ```

- [ ] 備份當前代碼
  ```bash
  git stash
  ```

### Issue #1: JWT Secret

- [ ] 修改 `orchestrator/api/auth.py` - 新增 `validate_config()` 方法
- [ ] 修改 `orchestrator/api/main.py` - 在 `lifespan` 中調用驗證
- [ ] 更新 `orchestrator/README.md` - 新增 JWT secret 文件
- [ ] 測試: 未設定 secret 時應用無法啟動
- [ ] 測試: 使用預設 secret 時應用無法啟動
- [ ] 測試: 使用安全 secret 時應用正常啟動

### Issue #2: Rate Limiter

- [ ] 修改 `orchestrator/api/main.py` - 移除 `app.add_middleware(RateLimitMiddleware, redis_client=None)`
- [ ] 修改 `orchestrator/api/main.py` - 在 `lifespan` 中新增 middleware
- [ ] 修改 `orchestrator/api/rate_limiter.py` - 新增初始化日誌
- [ ] 測試: 啟動日誌顯示 "Rate limiting enabled with Redis backend"
- [ ] 測試: Redis 中可以看到 rate limit keys
- [ ] 測試: 限流功能正常工作

### 提交與推送

- [ ] 提交修復
  ```bash
  git add orchestrator/api/auth.py
  git add orchestrator/api/main.py
  git add orchestrator/api/rate_limiter.py
  git add orchestrator/README.md
  git commit -m "fix: Critical security fixes for PR #562

  - Add JWT secret validation on startup (Issue #1)
  - Fix rate limiter Redis initialization (Issue #2)
  - Add comprehensive error messages and logging
  - Update README with security warnings
  
  Addresses CTO review feedback from CTO_REVIEW_PR562_SPRINT1_SECURITY.md"
  ```

- [ ] 推送到遠端
  ```bash
  git push origin devin/1761047019-api-auth-security
  ```

### 驗證 CI

- [ ] 等待 CI 完成
- [ ] 確認所有 13 項檢查通過
- [ ] 檢查 Vercel 部署成功

### 更新 PR 描述

- [ ] 在 PR #562 描述中新增:
  ```markdown
  ## 🔄 Updates (2025-10-21)
  
  ### Critical Fixes Applied
  
  Based on CTO review feedback, the following critical issues have been fixed:
  
  1. **🔴 JWT Secret Validation** (Issue #1)
     - Added startup validation for `ORCHESTRATOR_JWT_SECRET`
     - Application will fail to start if secret is missing or insecure
     - Added comprehensive error messages and documentation
  
  2. **🔴 Rate Limiter Initialization** (Issue #2)
     - Fixed Redis client initialization in middleware
     - Rate limiter now properly uses Redis for distributed rate limiting
     - Added logging to confirm Redis backend is active
  
  ### Testing
  
  - ✅ JWT secret validation tested (missing, default, secure)
  - ✅ Rate limiter Redis integration tested
  - ✅ All CI checks passing
  
  ### Documentation
  
  - Updated README with JWT secret requirements
  - Added security warnings and setup instructions
  
  **Review Report**: See `CTO_REVIEW_PR562_SPRINT1_SECURITY.md` for full details
  ```

---

## 🎯 完成後

修復完成後，PR #562 可以安全合併。

### 下一步行動

1. **立即**: 合併 PR #562
2. **本週**: 開始 Issue #560 (API 整合測試)
3. **下週**: 完成 Issue #561 (生產部署配置)

### 生產部署前檢查

在部署到生產環境前，確保:

- [ ] Issue #560 完成 (API 整合測試)
- [ ] Issue #561 完成 (生產部署配置)
- [ ] 設定生產環境變數:
  ```bash
  ORCHESTRATOR_JWT_SECRET=<使用 openssl rand -hex 32 生成>
  CORS_ORIGINS=https://yourdomain.com
  ORCHESTRATOR_API_KEY_PROD=<強隨機 key>:agent
  REDIS_URL=redis://production-redis:6379
  ```
- [ ] 執行完整的安全審計
- [ ] 進行負載測試

---

**預計總時間**: 1.5 小時

**問題?** 參考完整審查報告: `CTO_REVIEW_PR562_SPRINT1_SECURITY.md`
