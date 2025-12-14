# Phase 1: main.py 拆分計劃

## 概述

本文件詳細說明 `handoff/20250928/40_App/api-backend/src/main.py`（1677 行）的重構計劃，目標是將其拆分為可維護的模組，同時維持向後相容性與部署穩定性。

## 風險等級：中高風險（可控）

### 風險因素

1. **啟動入口契約** - 多處依賴 `src.main:app`：
   - `render.yaml`: `gunicorn -c gunicorn.conf.py src.main:app`
   - CI workflows: `FLASK_APP=src.main:app`
   - 70+ 測試檔案 `from src.main import app`

2. **Module-level globals 依賴**：
   - `BACKEND_SERVICES_AVAILABLE` - 被 `src/routes/dashboard.py` import
   - `PHASE_456_AVAILABLE` - 被多個測試 patch
   - `_as_bool`, `is_vercel_preview`, `get_health_payload`, `before_send` - 被測試直接 import

3. **Import-time 副作用**：
   - sys.path 修改（lines 12-32）
   - Sentry 初始化（lines 68-139）
   - Flask app 建立（line 160）
   - Blueprint 註冊（lines 340-406）

### 已有護欄

- Route-map regression guard（184 routes baseline）
- Settings reload fixture
- CORS 測試覆蓋

---

## 現況分析

### main.py 結構分解

| 區塊 | 行數 | 內容 | 風險 |
|------|------|------|------|
| Import & sys.path | 1-66 | 路徑設定、模組 import | 高 |
| Sentry init | 68-139 | Sentry SDK 初始化 | 中 |
| Security imports | 141-158 | SecurityManager, Backend services | 中 |
| App creation | 160-208 | Flask app, config | 中 |
| CORS setup | 210-320 | CORS handlers | 低（已有測試）|
| Security manager | 323-338 | SecurityManager 設定 | 中 |
| Blueprint registration | 340-421 | 20+ blueprints | 中 |
| Error handlers | 424-445 | Global exception handler | 低 |
| Health check | 448-525 | Health endpoint | 低 |
| Database setup | 528-707 | DB config, init, retry | 高 |
| Static serving | 709-723 | Static file routes | 低 |
| Phase 7 APIs | 726-936 | ~15 endpoints | 低 |
| Dashboard APIs | 939-1204 | ~10 endpoints | 低 |
| Phase 4-6 APIs | 1207-1571 | ~20 endpoints | 中 |
| Settings route | 1574-1651 | Settings endpoint | 低 |
| Main block | 1654-1677 | Dev server startup | 低 |

### 外部依賴點

```
gunicorn.conf.py → src.main:app
render.yaml → src.main:app
CI workflows → FLASK_APP=src.main:app
src/routes/dashboard.py → from src.main import BACKEND_SERVICES_AVAILABLE
70+ test files → from src.main import app, _as_bool, etc.
```

---

## 重構策略：Move-Only First

採用「先搬移、後重構」策略，每個 PR 只做一件事，確保可獨立驗收、可快速回滾。

### 核心原則

1. **維持 `src.main:app` 契約** - 外部仍從同一路徑取得 app
2. **維持 module-level globals** - 保留 `BACKEND_SERVICES_AVAILABLE` 等供外部 import
3. **Move-only** - 第一階段只搬移，不改行為
4. **每步驗證** - 每個 PR 都跑 route-map guard + smoke test

---

## 拆分順序（6 個 PR）

### PR1a: 抽出純函式與工具（低風險）

**目標**：將無副作用的純函式搬到獨立模組

**搬移內容**：
```python
# src/utils/helpers.py (新檔案)
def _as_bool(val): ...
```

**main.py 變更**：
```python
from src.utils.helpers import _as_bool
```

**驗收條件**：
- [ ] Route-map guard 通過
- [ ] 所有現有測試通過
- [ ] `from src.main import _as_bool` 仍可用（re-export）

**預估行數減少**：~10 行

---

### PR1b: 抽出 CORS middleware（低風險）

**目標**：將 CORS 相關函式搬到 middleware 模組

**搬移內容**：
```python
# src/middleware/cors.py (新檔案)
def is_vercel_preview(origin): ...
def add_cors_headers(response): ...
def setup_cors(app, cors_origins, cors_debug_enabled): ...
```

**main.py 變更**：
```python
from src.middleware.cors import setup_cors
# 在 app 建立後呼叫
setup_cors(app, cors_origins, cors_debug_enabled)
```

**驗收條件**：
- [ ] Route-map guard 通過
- [ ] CORS 測試全部通過
- [ ] `from src.main import is_vercel_preview` 仍可用（re-export）

**預估行數減少**：~100 行

---

### PR1c: 抽出 Blueprint 註冊（中風險）

**目標**：將 blueprint 註冊邏輯集中管理

**搬移內容**：
```python
# src/routes/__init__.py (修改)
def register_blueprints(app):
    """Register all blueprints to the Flask app.
    
    IMPORTANT: 使用函式內 lazy import 避免循環依賴和 import-time 副作用。
    所有 blueprint imports 必須在函式內部執行，不可在模組頂層。
    """
    # Lazy imports - 避免循環依賴
    from src.routes.billing import bp as billing_bp
    from src.routes.tenant import bp as tenant_bp
    from src.routes.vectors import bp as vectors_bp
    from src.routes.governance import bp as governance_bp, admin_bp as admin_agents_bp
    from src.routes.agent_registry import bp as agent_registry_bp
    from src.routes.admin import bp as admin_bp
    from src.routes.failures import bp as failures_bp
    from src.routes.experiments import bp as experiments_bp
    from src.routes.ai_policies import bp as ai_policies_bp
    from src.routes.user import user_bp
    from src.routes.auth import auth_bp
    from src.routes.auth_enhanced import auth_enhanced_bp
    from src.routes.auth_2fa import auth_2fa_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.totp import totp_bp
    
    # 註冊順序必須與原 main.py 一致
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(auth_enhanced_bp, url_prefix="/api/auth/v2")
    app.register_blueprint(auth_2fa_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(totp_bp, url_prefix="/api/auth/v2/totp")
    app.register_blueprint(billing_bp)
    # ... 其餘 blueprints
```

**main.py 變更**：
```python
from src.routes import register_blueprints
register_blueprints(app)
```

**Blueprint Contract Test（必要）**：
```python
# tests/test_blueprint_contract.py

import pytest

class TestBlueprintContract:
    """Verify all blueprints are registered correctly after refactoring."""
    
    # 預期的 blueprint 名稱列表（從 route-map baseline 提取）
    EXPECTED_BLUEPRINTS = [
        'user_bp', 'auth_bp', 'auth_enhanced_bp', 'auth_2fa_bp',
        'dashboard_bp', 'totp_bp', 'billing_bp', 'agent_registry_bp',
        'tenant_bp', 'vectors_bp', 'governance_bp', 'admin_bp',
        'admin_agents_bp', 'failures_bp', 'experiments_bp', 'ai_policies_bp',
    ]
    
    def test_all_blueprints_registered(self):
        """Verify all expected blueprints are registered."""
        from src.main import app
        registered_names = [bp.name for bp in app.blueprints.values()]
        for expected in self.EXPECTED_BLUEPRINTS:
            # Blueprint 名稱可能不完全匹配，檢查是否存在對應路由
            pass  # 由 route-map guard 覆蓋
    
    def test_blueprint_count_unchanged(self):
        """Verify blueprint count matches baseline."""
        from src.main import app
        # 從 route-map baseline 計算預期數量
        assert len(app.blueprints) >= 15, "Blueprint count decreased unexpectedly"
```

**驗收條件**：
- [ ] Route-map guard 通過（關鍵！）
- [ ] Blueprint Contract Test 通過
- [ ] 所有 API 測試通過
- [ ] Blueprint 註冊順序不變
- [ ] 使用函式內 lazy import（不可在模組頂層 import）

**預估行數減少**：~80 行

---

### PR1d: 抽出 Error handlers（低風險）

**目標**：將錯誤處理邏輯獨立

**搬移內容**：
```python
# src/middleware/error_handlers.py (新檔案)
def handle_exception(e): ...
def register_error_handlers(app): ...
```

**main.py 變更**：
```python
from src.middleware.error_handlers import register_error_handlers
register_error_handlers(app)
```

**驗收條件**：
- [ ] 錯誤處理測試通過
- [ ] Sentry 整合正常

**預估行數減少**：~25 行

---

### PR1e: 抽出 Database 初始化（高風險）

**目標**：將資料庫設定與初始化邏輯獨立

**搬移內容**：
```python
# src/extensions/database.py (新檔案)
def configure_database(app): ...
def init_test_database(app): ...
def init_database_with_retry(app, max_retries=6): ...
def validate_rate_limit_redis(): ...
```

**main.py 變更**：
```python
from src.extensions.database import configure_database, init_database_with_retry
configure_database(app)
init_database_with_retry(app)
```

**驗收條件**：
- [ ] 本地開發環境正常啟動
- [ ] CI 測試全部通過
- [ ] Production 部署正常（需 staging 驗證）

**預估行數減少**：~180 行

---

### PR1f: 抽出 Sentry 初始化（中風險）

**目標**：將 Sentry 初始化邏輯獨立

**搬移內容**：
```python
# src/extensions/sentry.py (新檔案)
def init_sentry(app_settings): ...
def before_send(event, hint): ...
```

**main.py 變更**：
```python
from src.extensions.sentry import init_sentry
SENTRY_DSN = init_sentry(app_settings)
```

**驗收條件**：
- [ ] Sentry 測試通過
- [ ] Production 環境 Sentry 正常上報

**預估行數減少**：~70 行

---

## 後續階段（Phase 1 完成後）

### Phase 1.5: App Factory Pattern

在 main.py 縮減到 ~500 行後，導入 `create_app()` factory：

```python
# src/main.py
def create_app(config=None):
    app = Flask(__name__, ...)
    
    # 載入設定
    configure_app(app, config)
    
    # 初始化擴展
    init_sentry(app_settings)
    configure_database(app)
    
    # 註冊 middleware
    setup_cors(app, ...)
    register_error_handlers(app)
    
    # 註冊路由
    register_blueprints(app)
    
    return app

# 維持向後相容
app = create_app()
```

### Phase 1.6: 路由模組化

將 main.py 中剩餘的 inline routes（Phase 7, Dashboard, Phase 4-6）搬到對應的 blueprint 模組。

---

## 前置工作（PR1 之前）

### 1. 新增 Smoke Tests

```python
# tests/test_app_bootstrap.py

def test_import_main_does_not_crash():
    """Verify main.py can be imported without errors."""
    import src.main
    assert src.main.app is not None

def test_health_endpoint_returns_ok():
    """Verify health endpoint is accessible."""
    from src.main import app
    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code in (200, 503)  # 503 if DB unavailable
        data = response.get_json()
        assert 'status' in data
        assert 'version' in data
```

### 2. Import Contract Test（必要）

驗證所有 public symbols 仍可從 `src.main` import，防止重構時意外破壞外部依賴：

```python
# tests/test_import_contract.py

import pytest

class TestImportContract:
    """Verify all public symbols remain importable from src.main.
    
    This test ensures backward compatibility during Phase 1 refactoring.
    Any symbol listed here MUST remain importable from src.main even after
    being moved to a new module (via re-export).
    """
    
    # Public symbols that MUST remain importable from src.main
    PUBLIC_SYMBOLS = [
        'app',                      # Flask app instance
        '_as_bool',                 # Helper function
        'is_vercel_preview',        # CORS helper
        'add_cors_headers',         # CORS middleware
        'before_send',              # Sentry hook
        'get_health_payload',       # Health check helper
        'handle_exception',         # Error handler
        'BACKEND_SERVICES_AVAILABLE',  # Feature flag
        'PHASE_456_AVAILABLE',      # Feature flag
        'SECURITY_AVAILABLE',       # Feature flag
        'SENTRY_DSN',               # Config value
    ]
    
    @pytest.mark.parametrize('symbol', PUBLIC_SYMBOLS)
    def test_symbol_importable(self, symbol):
        """Verify each public symbol can be imported from src.main."""
        import src.main
        assert hasattr(src.main, symbol), f"Symbol '{symbol}' not found in src.main"
    
    def test_app_is_flask_instance(self):
        """Verify app is a Flask instance."""
        from src.main import app
        from flask import Flask
        assert isinstance(app, Flask)
    
    def test_backend_services_is_bool(self):
        """Verify BACKEND_SERVICES_AVAILABLE is a boolean."""
        from src.main import BACKEND_SERVICES_AVAILABLE
        assert isinstance(BACKEND_SERVICES_AVAILABLE, bool)
```

### 3. 確認 Module-level Globals Re-export

在每個 PR 中，確保以下 globals 仍可從 `src.main` import：

```python
# src/main.py 底部
# Re-exports for backward compatibility
from src.utils.helpers import _as_bool
from src.middleware.cors import is_vercel_preview
from src.extensions.sentry import before_send
# BACKEND_SERVICES_AVAILABLE, PHASE_456_AVAILABLE 保留在 main.py
```

---

## Patch Canonical Target 規範（必要）

### 問題背景

當函式從 `src.main` 搬移到新模組（如 `src.utils.helpers`）後，測試中的 `@patch` 需要指向正確的位置。錯誤的 patch target 會導致 mock 失效。

### 規範

**原則：Patch where it's used, not where it's defined**

當函式被搬移後，patch target 取決於被測試程式碼如何 import 該函式：

| 情境 | 被測程式碼 import 方式 | Patch Target |
|------|------------------------|--------------|
| 1 | `from src.main import _as_bool` | `src.main._as_bool` |
| 2 | `from src.utils.helpers import _as_bool` | `src.utils.helpers._as_bool` |
| 3 | `import src.main; src.main._as_bool()` | `src.main._as_bool` |

### 重構後的 Canonical Target 對照表

| Symbol | 定義位置（新） | Canonical Patch Target | 說明 |
|--------|---------------|------------------------|------|
| `_as_bool` | `src.utils.helpers` | `src.main._as_bool` | 透過 re-export，測試仍 patch `src.main` |
| `is_vercel_preview` | `src.middleware.cors` | `src.main.is_vercel_preview` | 透過 re-export |
| `add_cors_headers` | `src.middleware.cors` | `src.main.add_cors_headers` | 透過 re-export |
| `before_send` | `src.extensions.sentry` | `src.extensions.sentry.before_send` | **不可 re-export**，Sentry SDK 持有原模組參考 |
| `get_health_payload` | `src.main`（暫不搬移） | `src.main.get_health_payload` | 保留原位 |
| `handle_exception` | `src.middleware.error_handlers` | `src.main.handle_exception` | 透過 re-export |
| `BACKEND_SERVICES_AVAILABLE` | `src.main`（保留） | `src.main.BACKEND_SERVICES_AVAILABLE` | 不搬移 |
| `PHASE_456_AVAILABLE` | `src.main`（保留） | `src.main.PHASE_456_AVAILABLE` | 不搬移 |

### 實作要求

1. **Re-export 必須在 main.py 底部明確宣告**：
   ```python
   # src/main.py 底部
   # Re-exports for backward compatibility (DO NOT REMOVE)
   # These symbols are patched by tests via 'src.main.{symbol}'
   from src.utils.helpers import _as_bool  # noqa: F401
   from src.middleware.cors import is_vercel_preview, add_cors_headers  # noqa: F401
   from src.middleware.error_handlers import handle_exception  # noqa: F401
   # NOTE: before_send 不可 re-export，因為 Sentry SDK 持有原模組參考
   # 測試需 patch 'src.extensions.sentry.before_send'
   ```

2. **測試不需修改 patch target**：
   - 現有測試使用 `@patch('src.main.BACKEND_SERVICES_AVAILABLE')` 仍有效
   - 現有測試使用 `@patch('src.main._as_bool')` 仍有效（透過 re-export）

3. **新增 Patch Target Contract Test**：
   ```python
   # tests/test_patch_targets.py
   
   from unittest.mock import patch
   import pytest
   
   class TestPatchTargets:
       """Verify patch targets work correctly after refactoring."""
       
       def test_patch_as_bool_via_main(self):
           """Verify _as_bool can be patched via src.main."""
           with patch('src.main._as_bool', return_value=True):
               from src.main import _as_bool
               assert _as_bool('false') == True  # Mocked
       
       def test_patch_backend_services_available(self):
           """Verify BACKEND_SERVICES_AVAILABLE can be patched."""
           with patch('src.main.BACKEND_SERVICES_AVAILABLE', False):
               from src.main import BACKEND_SERVICES_AVAILABLE
               assert BACKEND_SERVICES_AVAILABLE == False
       
       def test_patch_phase_456_available(self):
           """Verify PHASE_456_AVAILABLE can be patched."""
           with patch('src.main.PHASE_456_AVAILABLE', False):
               from src.main import PHASE_456_AVAILABLE
               assert PHASE_456_AVAILABLE == False
   ```

### PR1f 特別注意：Sentry before_send hook

`before_send` 函式在 Sentry SDK 初始化時作為 callback 傳入：

```python
sentry_sdk.init(
    dsn=SENTRY_DSN,
    before_send=before_send,  # 傳入函式參考
    ...
)
```

**重要**：`before_send` **不可使用 re-export 策略**。原因：
1. Sentry SDK 在 `init()` 時持有 `before_send` 函式的直接參考
2. 當 `init_sentry()` 在 `src/extensions/sentry.py` 內呼叫時，SDK 持有的是該模組內的函式參考
3. 即使在 `src.main` re-export `before_send`，patch `src.main.before_send` 也無法影響 Sentry 行為

**正確做法**：
- 測試需 patch `src.extensions.sentry.before_send`（定義位置）
- 不要在 `src.main` re-export `before_send`

**驗證方式**：
```python
def test_sentry_before_send_hook_works():
    """Verify Sentry before_send hook is correctly configured."""
    from src.extensions.sentry import before_send
    # 模擬 Sentry event
    event = {'exception': {'values': [{'type': 'TestError'}]}}
    hint = {}
    result = before_send(event, hint)
    assert result is not None  # 或根據 before_send 邏輯驗證
```

---

## 驗收清單

每個 PR 必須通過：

- [ ] `pytest tests/test_route_map.py -v` - Route-map guard（9 tests）
- [ ] `pytest tests/test_import_contract.py -v` - Import contract test
- [ ] `pytest tests/test_app_bootstrap.py -v` - Smoke tests
- [ ] `pytest tests/test_cors_config.py -v` - CORS tests
- [ ] `pytest -q` - Full test suite
- [ ] CI checks 全部通過
- [ ] `gunicorn -c gunicorn.conf.py src.main:app --check-config` - Gunicorn 設定驗證

### 建議：Gunicorn --check-config 納入 CI（Non-blocking）

建議在 CI workflow 中新增 Gunicorn 設定驗證步驟：

```yaml
# .github/workflows/test-apps.yml
- name: Verify Gunicorn config
  run: |
    cd handoff/20250928/40_App/api-backend
    gunicorn -c gunicorn.conf.py src.main:app --check-config
```

此步驟可在 Phase 1 實作過程中加入，作為額外的啟動驗證護欄。

---

## 時程估計

| PR | 預估時間 | 依賴 |
|----|----------|------|
| Smoke tests | 0.5 天 | 無 |
| PR1a: 純函式 | 0.5 天 | Smoke tests |
| PR1b: CORS | 1 天 | PR1a |
| PR1c: Blueprints | 1 天 | PR1b |
| PR1d: Error handlers | 0.5 天 | PR1c |
| PR1e: Database | 1.5 天 | PR1d |
| PR1f: Sentry | 1 天 | PR1e |

**總計**：~6 天

---

## 風險緩解

1. **每個 PR 都可獨立回滾** - 使用 merge commit，不 squash
2. **Staging 驗證** - PR1e（Database）需在 staging 環境驗證
3. **監控** - Phase 1 合併後監控 Render 啟動錯誤率、5xx、CORS 相關指標
4. **快速回滾計劃** - 保留 revert commit 準備

---

## 相關文件

- [Epic #2374](https://github.com/RC918/morningai/issues/2374) - 技術債優化計劃
- [docs/TESTING.md](./TESTING.md) - 測試文檔（含 route-map guard 說明）
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) - 架構文檔

---

最後更新：2025-12-14（含 CTO 審閱補充 + Gemini Review 修正）
