# Contributing to MorningAI

感謝您對 MorningAI 專案的貢獻！本文檔提供了貢獻指南和最佳實踐。

## 目錄

- [分工規則](#分工規則)
- [API 變更流程](#api-變更流程)
- [測試策略](#測試策略)
- [GitHub Actions 最佳實踐](#github-actions-最佳實踐)
- [驗收標準](#驗收標準)

## 分工規則

### Design PR
**允許改動**：
- `docs/UX/**`
- `docs/UX/tokens.json`
- `docs/**.md`
- `frontend/樣式與文案`

**禁止改動**：
- `handoff/**/30_API/openapi/**`
- `**/api/**`
- `**/src/**` 的後端與 API 相關檔

### Backend/Engineering PR
**允許改動**：
- `**/api/**`
- `**/src/**`
- `handoff/**/30_API/openapi/**`

**禁止改動**：
- `docs/UX/**` 與設計稿資源

## API 變更流程

變更 API 或資料欄位（OpenAPI/DB）時：

1. **建立 RFC Issue**
   - 添加 label: `rfc`
   - 說明：動機、影響、相容策略、逐步 rollout
   
2. **等待核准**
   - 經 Owner 核准後才可提交工程 PR
   
3. **提交 PR**
   - 遵循測試策略
   - 通過所有 CI 檢查

## 測試策略

### 測試類型

MorningAI 專案使用三層測試策略：

#### 1. 單元測試 (Unit Tests)

**目錄**: `tests/unit/`

**特性**:
- 使用 mock 隔離所有外部依賴
- 測試單一函式/類別的邏輯
- 快速執行（< 1 秒/測試）
- 覆蓋率目標: **80%+**

**範例**:
```python
# tests/unit/services/test_monitoring_unit.py
import pytest
from unittest.mock import Mock, patch

def test_collect_metrics_success(mock_state_manager):
    """測試 metrics 收集成功情境"""
    with patch('src.services.monitoring.resilience_manager') as mock_rm:
        mock_rm.get_stats.return_value = {'success': 10}
        
        dashboard = MonitoringDashboard()
        metrics = dashboard.collect_metrics()
        
        assert metrics['success'] == 10
```

**何時使用**:
- 測試業務邏輯
- 測試資料轉換
- 測試錯誤處理
- 測試邊界條件

#### 2. 整合測試 (Integration Tests)

**目錄**: `tests/integration/`

**特性**:
- 使用真實 Flask app 和 JWT token
- 測試多個模組的協作
- 中等執行速度（1-5 秒/測試）
- 覆蓋率目標: **60%+**

**範例**:
```python
# tests/integration/routes/test_vectors_integration.py
import pytest
from src.main import app
from src.middleware.auth_middleware import create_admin_token

@pytest.fixture
def client():
    """建立測試 client"""
    app.config['TESTING'] = True
    return app.test_client()

@pytest.fixture
def auth_headers():
    """建立認證 headers"""
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}

def test_vector_search_with_auth(client, auth_headers):
    """測試 vector 搜尋需要認證"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=auth_headers)
    assert response.status_code == 200
```

**何時使用**:
- 測試 API 路由
- 測試認證流程
- 測試多個服務的協作
- 測試資料庫操作

#### 3. E2E 測試 (End-to-End Tests)

**目錄**: `tests/integration/e2e/`

**特性**:
- 測試完整使用者流程
- 使用真實資料庫和服務
- 較慢執行速度（5-30 秒/測試）
- 覆蓋率目標: **關鍵路徑 100%**

**範例**:
```python
# tests/integration/e2e/test_full_workflow.py
def test_complete_user_journey(client, auth_headers):
    """測試完整使用者流程：註冊 -> 登入 -> 搜尋 -> 查看結果"""
    # 1. 註冊
    response = client.post('/api/auth/register', json={...})
    assert response.status_code == 201
    
    # 2. 登入
    response = client.post('/api/auth/login', json={...})
    token = response.json['token']
    
    # 3. 搜尋
    response = client.post('/api/vectors/search', 
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
```

**何時使用**:
- 測試關鍵使用者流程
- 測試跨模組整合
- 部署前驗證

### 測試目錄結構

```
tests/
  unit/                    # 單元測試 (使用 mock)
    routes/
      test_vectors_unit.py
      test_faq_unit.py
    services/
      test_monitoring_unit.py
  integration/             # 整合測試 (使用真實依賴)
    routes/
      test_vectors_integration.py
      test_faq_integration.py
    e2e/
      test_full_workflow.py
  fixtures/                # 共用 fixtures
    auth.py
    database.py
```

### JWT Token 使用規範

#### 測試環境 JWT Secret

**要求**: 測試環境必須使用獨立的 JWT secret

```python
# tests/fixtures/auth.py
import os
import pytest

@pytest.fixture(autouse=True)
def test_jwt_secret():
    """確保測試環境使用獨立的 JWT secret"""
    os.environ['JWT_SECRET'] = 'test-secret-do-not-use-in-production'
    yield
    # 清理
    if 'JWT_SECRET' in os.environ:
        del os.environ['JWT_SECRET']
```

#### JWT Token 建立

**單元測試**: 使用 mock JWT
```python
@pytest.fixture
def mock_jwt():
    with patch('src.middleware.auth_middleware.jwt_required', lambda f: f):
        yield
```

**整合測試**: 使用真實 JWT token
```python
@pytest.fixture
def auth_headers():
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}
```

### CI 配置

```yaml
# 快速反饋 (每次 commit)
- pytest tests/unit/ --maxfail=1

# 完整驗證 (PR merge)
- pytest tests/unit/ tests/integration/ --cov=src --cov-fail-under=60
```

### 測試覆蓋率目標

| 測試類型 | 覆蓋率目標 | 執行頻率 |
|---------|-----------|---------|
| 單元測試 | 80%+ | 每次 commit |
| 整合測試 | 60%+ | 每次 PR |
| E2E 測試 | 關鍵路徑 100% | 每日/部署前 |

### 測試命名規範

```python
# ✅ 好的測試名稱
def test_collect_metrics_returns_dashboard_metrics():
    """測試 collect_metrics 返回 DashboardMetrics 物件"""
    pass

def test_vector_search_requires_authentication():
    """測試 vector 搜尋需要認證"""
    pass

# ❌ 不好的測試名稱
def test_1():
    pass

def test_monitoring():
    pass
```

### Fixture 使用規範

**共用 fixtures**: 放在 `tests/fixtures/`

```python
# tests/fixtures/auth.py
import pytest
from src.middleware.auth_middleware import create_admin_token

@pytest.fixture
def auth_headers():
    """建立認證 headers"""
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}
```

**使用方式**:
```python
# tests/integration/routes/test_vectors_integration.py
from tests.fixtures.auth import auth_headers

def test_vector_search(client, auth_headers):
    response = client.post('/api/vectors/search', headers=auth_headers)
    assert response.status_code == 200
```

## GitHub Actions 最佳實踐

### 🚨 防止無限循環

**強制規則**：所有 workflows 必須使用 `branches` 或 `branches-ignore` filter。

#### ✅ 推薦配置

**標準 CI workflows**（測試、構建、驗證）：
```yaml
on:
  workflow_dispatch:  # 允許手動觸發
  push:
    branches: [main]  # 只在 main 分支觸發
  pull_request:
    branches: [main]  # 只對合併到 main 的 PRs 觸發
```

**部署 workflows**：
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
  workflow_dispatch:
```

**自動化系統 workflows**（會創建 PRs/推送代碼）：
```yaml
on:
  workflow_dispatch:
  push:
    branches-ignore:
      - 'orchestrator/**'  # 排除自動化分支
      - 'bot/**'
      - 'automated/**'
  pull_request:
    branches-ignore:
      - 'orchestrator/**'
```

#### ❌ 禁止的模式

**完全沒有 filter**（會導致無限循環）：
```yaml
# ❌ FORBIDDEN - 任何 push 都會觸發
on:
  push:
  pull_request:
```

**只有 paths filter**（不足夠）：
```yaml
# ⚠️ RISKY - 沒有 branches filter
on:
  pull_request:
    paths:
      - 'docs/**'
```

### 📋 自動合併 Workflows 特別規則

如果 workflow 會自動 merge PRs，**必須**：

1. **限制 branches**：
   ```yaml
   pull_request:
     branches: [main]  # 只允許合併到 main 的 PRs
   ```

2. **驗證提交者**：
   ```yaml
   if: |
     github.event.pull_request.user.login == 'devin-ai-integration[bot]'
   ```

3. **檢查檔案範圍**：
   ```yaml
   # 只有特定檔案變更才 auto-merge
   paths:
     - 'docs/FAQ.md'
   ```

### 🛡️ Rate Limiting 和監控

**所有會創建 PRs 或推送代碼的 workflows 應該**：

1. **添加 concurrency 控制**：
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

2. **設置 timeout**：
   ```yaml
   jobs:
     auto-create-pr:
       runs-on: ubuntu-latest
       timeout-minutes: 10  # 防止卡住
   ```

3. **添加條件檢查**：
   ```yaml
   if: |
     github.event_name == 'workflow_dispatch' ||
     github.ref == 'refs/heads/main'
   ```

### 📝 Workflow 變更檢查清單

創建或修改 workflows 時，確認：

- [ ] 所有 `push:` 和 `pull_request:` 觸發器都有 `branches` 或 `branches-ignore`
- [ ] Auto-merge workflows 有嚴格的 branches filter
- [ ] 會創建 PRs/推送的 workflows 不會觸發自己
- [ ] 使用 `workflow_dispatch` 允許手動觸發（方便調試）
- [ ] 設置適當的 `timeout-minutes`
- [ ] 有 `concurrency` 控制（如果適用）

## 驗收標準

所有 PR 需通過：

1. **OpenAPI 驗證**
   - API schema 符合 OpenAPI 3.0 規範
   - 所有 endpoints 都有文檔

2. **測試覆蓋率**
   - 單元測試覆蓋率 ≥ 80%
   - 整合測試覆蓋率 ≥ 60%
   - 所有測試通過

3. **CI 檢查**
   - Lint 檢查通過
   - Type 檢查通過
   - Build 成功

4. **Post-deploy Health 斷言**
   - 部署後健康檢查通過
   - 關鍵 API endpoints 可訪問

違規改動將被 CI 自動阻擋（見 `.github/workflows/pr-guard.yml`）。

## 相關文檔

- [測試最佳實踐](docs/TESTING.md)
- [API 文檔](orchestrator/API_USAGE.md)
- [部署指南](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [監控設置](docs/MONITORING_SETUP.md)

## 問題回報

如有問題，請：
1. 搜尋現有 Issues
2. 建立新 Issue，包含：
   - 問題描述
   - 重現步驟
   - 預期行為
   - 實際行為
   - 環境資訊

## 授權

貢獻代碼即表示您同意將代碼授權給專案使用。
