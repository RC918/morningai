# Contributing to MorningAI

感謝您對 MorningAI 專案的貢獻！本文檔提供了貢獻指南和最佳實踐。

## 目錄

- [分工規則](#分工規則)
- [設計系統與 Shared UI](#設計系統與-shared-ui)
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

## 設計系統與 Shared UI

### 使用 @morningai/shared-ui

MorningAI 使用統一的設計系統，所有 UI 元件集中在 `packages/shared-ui/`。

#### 基本原則

1. **優先使用 shared-ui** - 開發新功能前，先檢查 shared-ui 是否有可用元件
2. **不要重複造輪子** - 避免在應用層重新實作已存在的元件
3. **新元件放 shared-ui** - 如果元件會被多個應用使用，應加入 shared-ui
4. **使用 Design Tokens** - 使用 CSS 變數而非硬編碼顏色/間距

#### 檢查可用元件

```bash
# 查看所有可用元件
cat packages/shared-ui/src/index.ts

# 或啟動 Storybook 瀏覽
pnpm --filter frontend-dashboard storybook
```

#### 使用範例

```tsx
// ✅ 好的做法 - 使用 shared-ui
import { Button, Card, Input } from '@morningai/shared-ui'

function MyComponent() {
  return (
    <Card>
      <Input placeholder="輸入..." />
      <Button>提交</Button>
    </Card>
  )
}

// ❌ 不好的做法 - 在應用層重新實作
// src/components/my-button.tsx
export function MyButton() {
  return <button className="...">按鈕</button>
}
```

#### 加入新元件到 Shared UI

如果元件會被多個應用使用：

1. 在 `packages/shared-ui/src/components/` 建立元件
2. 在 `packages/shared-ui/src/index.ts` 匯出
3. 加入 Storybook story 到 `packages/shared-ui/src/stories/`
4. 執行 `pnpm --filter @morningai/shared-ui build`
5. 更新 `packages/shared-ui/README.md`

#### 相關文件

- 📚 [Shared UI 使用指南](docs/shared-ui-guide.md) - 完整使用指南
- 📦 [Shared UI README](packages/shared-ui/README.md) - 套件文件
- 🎨 Storybook: `pnpm --filter frontend-dashboard storybook`

### 廢棄目錄

以下目錄已廢棄，**請勿使用**：

- ⛔ `tools/frontend-lab/` - 已遷移到 `handoff/20250928/40_App/frontend-dashboard/`

如誤用廢棄目錄，CI 會自動阻止 PR 合併。

### Phase 2 PR 要求（Epic #2304）

Phase 2 設計系統遷移 PR 必須遵循以下流程：

#### 必要步驟

1. **執行 Audit 腳本**：
   ```bash
   ./scripts/phase2_audit.sh
   # 或針對特定檔案
   ./scripts/phase2_audit.sh --file <target_file>
   ```

2. **執行 Bundle Size 量測**：
   ```bash
   ./scripts/measure-bundle-size.sh
   ```

3. **填寫 PR Template**：使用 `PR_PHASE2_TEMPLATE.md` 或 PR template 中的 Phase 2 Audit Checklist

#### 相關文件

- 📋 [PR_PHASE2_TEMPLATE.md](PR_PHASE2_TEMPLATE.md) - Phase 2 PR 範本（含範例填寫）
- 📚 [DESIGN_SYSTEM_GUIDELINES.md](DESIGN_SYSTEM_GUIDELINES.md) - 設計系統指南
  - 「Phase 2 Audit Scripts 技術文檔」章節：Namespace JSX 解析規則、Bundle Size Fallback 計算方式
- 🎯 [Epic #2304](https://github.com/RC918/morningai/issues/2304) - Phase 2 拆分計畫

#### 腳本依賴

- **Bash 4+**：macOS 預設 Bash 3.2，需使用 `brew install bash`
- **bc**：可選，若無則使用 awk fallback
- **gzip**：系統 CLI

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

## Python Lint 規則 (Ruff)

MorningAI 使用 [Ruff](https://docs.astral.sh/ruff/) 作為 Python linter，配置於 `pyproject.toml`。

### 基本配置

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W"]  # pycodestyle errors/warnings, pyflakes
ignore = []  # 所有規則都啟用

[tool.ruff.lint.per-file-ignores]
"*/migrations/*" = ["E501"]  # 允許 migrations 超長行
"*/tests/*" = ["E501"]       # 允許測試檔案超長行
"**/main.py" = ["E402"]      # 允許 main.py 延遲 import
"**/governance.py" = ["E402"] # 允許 governance.py 延遲 import
```

### 常見規則說明

| 規則 | 說明 | 修復方式 |
|------|------|---------|
| E501 | Line too long (>120 chars) | 拆分長行、使用括號換行 |
| E402 | Module import not at top | 重新排列 imports 或加入 per-file-ignores |
| F401 | Unused import | 移除未使用的 import |
| F841 | Unused variable | 移除未使用的變數或使用 `_` 前綴 |
| W291 | Trailing whitespace | 移除行尾空白 |

### 本地執行 Lint

**重要**：請使用與 CI 相同的 Ruff 版本以確保一致性。

```bash
# 安裝指定版本的 Ruff（與 CI 一致）
pip install ruff==0.8.6

# 檢查所有錯誤
ruff check handoff/20250928/40_App/api-backend/src

# 自動修復可修復的錯誤
ruff check handoff/20250928/40_App/api-backend/src --fix

# 顯示統計資訊
ruff check handoff/20250928/40_App/api-backend/src --statistics
```

### CI 整合

Lint 檢查在 `backend-ci` workflow 中執行，目前為 **blocking** 模式（lint 失敗會阻擋 CI）。

CI 使用 [astral-sh/ruff-action](https://github.com/astral-sh/ruff-action) 官方 action，版本透過 `env.RUFF_VERSION` 集中管理。

```yaml
# .github/workflows/backend.yml
env:
  RUFF_VERSION: "0.8.6"  # 集中管理版本

jobs:
  lint:
    runs-on: ubuntu-latest
    continue-on-error: false  # blocking mode
    steps:
      - uses: actions/checkout@v4
      - name: Run Ruff linter
        uses: astral-sh/ruff-action@v2
        with:
          version: ${{ env.RUFF_VERSION }}
          args: "check handoff/20250928/40_App/api-backend/src --output-format=github"
```

**版本升級**：Ruff 版本由 Dependabot 自動監控，每月檢查更新並建立 PR。

### 修復長行的技巧

```python
# ❌ 超過 120 字元
result = some_function(very_long_argument_name, another_long_argument, yet_another_argument)

# ✅ 使用括號換行
result = some_function(
    very_long_argument_name,
    another_long_argument,
    yet_another_argument
)

# ❌ 超長字串
message = "This is a very long error message that exceeds the line length limit"

# ✅ 使用隱式字串連接
message = (
    "This is a very long error message "
    "that exceeds the line length limit"
)

# ❌ 超長條件式
if condition1 and condition2 and condition3 and condition4:
    pass

# ✅ 提取變數
is_valid = condition1 and condition2
is_ready = condition3 and condition4
if is_valid and is_ready:
    pass
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

## i18n 國際化規範

### i18n Violation Baseline 機制

MorningAI 使用 **violation baseline** 機制來防止新的 i18n 違規，同時允許團隊逐步修復現有違規。

#### 工作原理

1. **Baseline 檔案**: `scripts/i18n-baseline.json` 記錄當前的違規數量
2. **Pre-commit Hook**: 在 commit 時自動修復可修復的 i18n 問題（使用 `eslint --fix --quiet`）
3. **CI Baseline Check**: 在 CI 中檢查違規數量，如果超過 baseline 則失敗

#### 使用 i18n

**✅ 正確做法** - 使用 `t()` 函數：
```tsx
import { useTranslation } from 'react-i18next'

function MyComponent() {
  const { t } = useTranslation()
  
  return (
    <div>
      <h1>{t('welcome.title')}</h1>
      <p>{t('welcome.description')}</p>
      <Button>{t('common.submit')}</Button>
    </div>
  )
}
```

**❌ 錯誤做法** - 硬編碼字串：
```tsx
// ❌ 會被 ESLint 阻擋
function MyComponent() {
  return (
    <div>
      <h1>Welcome</h1>
      <p>This is a description</p>
      <Button>Submit</Button>
    </div>
  )
}
```

#### 添加翻譯 Key

1. 在 `src/i18n/locales/en-US.json` 添加英文翻譯
2. 在 `src/i18n/locales/zh-TW.json` 添加中文翻譯

```json
// en-US.json
{
  "welcome": {
    "title": "Welcome",
    "description": "This is a description"
  },
  "common": {
    "submit": "Submit"
  }
}

// zh-TW.json
{
  "welcome": {
    "title": "歡迎",
    "description": "這是描述"
  },
  "common": {
    "submit": "提交"
  }
}
```

#### 檢查違規數量

```bash
# 檢查當前違規數量
cd handoff/20250928/40_App/frontend-dashboard
pnpm lint | grep "i18next/no-literal-string" | wc -l

cd handoff/20250928/40_App/owner-console
pnpm lint | grep "i18next/no-literal-string" | wc -l

# 或使用 baseline check script
node scripts/check-i18n-baseline.js
```

#### 更新 Baseline

當你修復了一些違規後，更新 baseline：

1. 運行 `node scripts/check-i18n-baseline.js` 確認改進
2. 如果違規數量減少，手動更新 `scripts/i18n-baseline.json`
3. Commit 更新後的 baseline 檔案

#### Pre-commit Hook

Pre-commit hook 會自動：
- 對 staged 的 `.js/.jsx/.ts/.tsx` 檔案運行 `eslint --fix --quiet`
- 自動修復可修復的問題
- 只在有 i18n 違規（error）時阻擋 commit

如果 commit 被阻擋：
1. 查看 ESLint 錯誤訊息
2. 將硬編碼字串替換為 `t()` 調用
3. 添加對應的翻譯 key
4. 重新 commit

#### CI Baseline Check

CI 會在每次 PR 時檢查：
- 如果違規數量 **增加**：❌ CI 失敗
- 如果違規數量 **減少**：✅ CI 通過並顯示改進
- 如果違規數量 **不變**：✅ CI 通過

#### 30/60/90 天違規清理計劃

參見 `docs/i18n-cleanup-plan.md` 了解詳細的違規清理計劃和進度追蹤。

## TypeScript 類型檢查規範

### 標準 TypeCheck 命令

**前端專案** (frontend-dashboard, owner-console):
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run typecheck
```

**重要說明**:
- 錯誤數量可能因環境而異（Storybook 檔案包含/排除）
- **標準**: PR 不得引入新的 TypeScript 錯誤
- **驗證方式**: 比較 main 分支和 PR 分支的錯誤差異

### 驗證流程

1. **記錄 main 分支錯誤數**:
```bash
git checkout main
cd handoff/20250928/40_App/frontend-dashboard
pnpm run typecheck 2>&1 | grep "error TS" > /tmp/main_errors.txt
wc -l /tmp/main_errors.txt
```

2. **記錄 PR 分支錯誤數**:
```bash
git checkout your-pr-branch
cd handoff/20250928/40_App/frontend-dashboard
pnpm run typecheck 2>&1 | grep "error TS" > /tmp/pr_errors.txt
wc -l /tmp/pr_errors.txt
```

3. **比較差異**:
```bash
# 查看新增的錯誤
diff /tmp/main_errors.txt /tmp/pr_errors.txt | grep "^>"

# 查看修復的錯誤
diff /tmp/main_errors.txt /tmp/pr_errors.txt | grep "^<"
```

### 類型標註最佳實踐

1. **完整的介面定義**
   - 避免使用 `Record<string, unknown>` 作為主要類型
   - 為所有已知屬性定義明確的類型
   - 使用 `unknown` 而非 `any` 處理未知類型

2. **避免 `as any` 轉型**
   - 優先擴展介面定義
   - 使用可選屬性 (`name?: string`)
   - 使用類型守衛 (`if ('property' in object)`)

3. **函式類型標註**
   - 所有函式參數加上類型
   - 所有函式加上回傳類型
   - React 元件使用 `React.ReactElement` 或 `React.FC`

**範例**:
```typescript
// ✅ 好的類型定義
interface MetricsReport {
  generated_at: string
  web_vitals?: Record<string, WebVitalData>  // 使用具體的 value 類型
  recommendations?: Recommendation[]
}

interface WebVitalData {
  status: 'good' | 'excellent' | 'needs_improvement' | 'poor'
  current: number
  average: number
  p90: number
  count: number
}

// ❌ 不好的類型定義
interface MetricsReport {
  generated_at: string
  web_vitals?: Record<string, unknown>  // 過於泛型
  recommendations?: unknown[]
}
```

## i18n 政策（強制執行）

**所有用戶可見的字串都必須使用 i18n。** 這由 ESLint 強制執行，違反將導致 CI 失敗。

### ✅ 正確用法

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      {/* ✅ 使用 t() 處理簡單字串 */}
      <h1>{t('settings.2fa.title')}</h1>
      <p>{t('settings.2fa.subtitle')}</p>
      
      {/* ✅ 使用 t() 處理插值 */}
      <p>{t('dashboard.welcome', { name: userName })}</p>
      
      {/* ✅ 使用 Trans 組件處理包含 HTML 的字串 */}
      <Trans i18nKey="settings.2fa.description">
        使用<strong>雙重驗證</strong>保護您的帳戶
      </Trans>
      
      {/* ✅ 使用 t() 處理無障礙屬性 */}
      <button aria-label={t('common.close')}>×</button>
      <img alt={t('dashboard.chart.alt')} src="chart.png" />
    </div>
  );
}
```

### ❌ 錯誤用法（會導致 ESLint 錯誤）

```tsx
function MyComponent() {
  return (
    <div>
      {/* ❌ 硬編碼字串 - ESLint 會報錯 */}
      <h1>雙重驗證</h1>
      <p>保護您的帳戶</p>
      
      {/* ❌ 硬編碼無障礙屬性 - ESLint 會報錯 */}
      <button aria-label="關閉">×</button>
      <img alt="儀表板圖表" src="chart.png" />
    </div>
  );
}
```

### Translation Key 命名規範

使用階層式命名空間結構：`{page}.{section}.{element}`

範例：
- `settings.2fa.title` - Settings 頁面，2FA 區塊，標題元素
- `dashboard.metrics.cpuUsage` - Dashboard 頁面，metrics 區塊，CPU 使用率標籤
- `common.actions.save` - 通用字串，actions 區塊，儲存按鈕

### 新增 Translation Keys

1. **同時加入兩個語系檔案：**
   - `src/i18n/locales/en-US.json`（英文）
   - `src/i18n/locales/zh-TW.json`（繁體中文）

2. **使用適當的巢狀結構**

3. **測試兩種語言** - 在應用中切換語言並確認所有字串正確顯示

詳細說明請參閱 `TOLGEE_POC_SETUP.md`。

## 資料庫遷移規範 (Database Migrations)

MorningAI 使用 **Alembic 1.13.1** 進行資料庫 schema 版本管理。

### 創建新 Migration

```bash
cd handoff/20250928/40_App/api-backend

# 設置 DATABASE_URL
export DATABASE_URL="sqlite:////absolute/path/to/dev.db"

# 自動生成 migration
alembic revision --autogenerate -m "add user email verification"
```

### Migration 命名規範

```bash
# ✅ 好的命名 - 清楚描述變更
alembic revision --autogenerate -m "add user email verification"
alembic revision --autogenerate -m "add agent reputation score index"
alembic revision --autogenerate -m "create billing_plans table"

# ❌ 不好的命名 - 太模糊
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "fix"
alembic revision --autogenerate -m "changes"
```

### 必須手動檢查的項目

創建 migration 後，**必須手動檢查**以下項目：

1. **Upgrade 邏輯正確**
   ```python
   def upgrade():
       # 檢查所有 CREATE TABLE, ALTER TABLE 語句
       op.create_table('new_table', ...)
   ```

2. **Downgrade 邏輯正確**（可回滾）
   ```python
   def downgrade():
       # 必須能夠完全回滾 upgrade 的變更
       op.drop_table('new_table')
   ```

3. **Enum 值使用小寫**（關鍵！）
   ```python
   # ✅ 正確 - 使用小寫 enum 值
   sa.Enum('dev_agent', 'ops_agent', 'pm_agent', name='agenttypedb')
   
   # ❌ 錯誤 - 使用大寫會導致 PostgreSQL 拒絕插入
   sa.Enum('DEV_AGENT', 'OPS_AGENT', 'PM_AGENT', name='agenttypedb')
   ```

4. **外鍵約束正確**
   ```python
   op.create_foreign_key(
       'fk_tasks_agent_id',
       'tasks', 'agents',
       ['agent_id'], ['agent_id'],
       ondelete='CASCADE'  # 明確指定刪除行為
   )
   ```

5. **索引定義合理**
   ```python
   op.create_index('idx_tasks_status', 'tasks', ['status'])
   ```

### Enum 值政策（重要！）

**問題**: SQLAlchemy 預設會將 enum **名稱**（大寫）而非 enum **值**（小寫）寫入資料庫。

**解決方案**: 在模型中使用 `values_callable` 參數

```python
# src/models/agent_registry_db.py

class AgentTypeDB(str, Enum):
    DEV_AGENT = "dev_agent"        # ✅ 值為小寫
    OPS_AGENT = "ops_agent"

class AgentDB(db.Model):
    agent_type = db.Column(
        db.Enum(
            AgentTypeDB,
            values_callable=lambda e: [i.value for i in e],  # ✅ 關鍵參數
            name='agenttypedb'
        ),
        nullable=False
    )
```

### 本地測試 Migration

```bash
# 1. Upgrade
alembic upgrade head

# 2. 測試 downgrade
alembic downgrade -1

# 3. 重新 upgrade
alembic upgrade head

# 4. 測試資料插入
python scripts/test_migration_data_insertion.py
```

### 提交前檢查清單

- [ ] Migration 檔案已手動檢查
- [ ] Upgrade 和 downgrade 都已本地測試
- [ ] Enum 值使用小寫
- [ ] 外鍵約束有明確的 ondelete 行為
- [ ] 已執行 `python scripts/test_migration_data_insertion.py`
- [ ] DATABASE_URL 使用絕對路徑（SQLite）

### 禁止的操作

1. **不要編輯已部署的 migration**
   - 一旦 migration 已部署到生產環境，不要編輯它
   - 創建新的 migration 來修正問題

2. **不要編輯 `alembic/versions/` 之外的生成文件**
   - `alembic/env.py` 和 `alembic.ini` 是手動維護的配置文件

3. **不要跳過 downgrade 測試**
   - 所有 migration 必須可以回滾

### 相關文檔

- **[Database Migrations Guide](docs/database/MIGRATIONS.md)** - 完整的 Alembic 工作流程和故障排除
- **[Onboarding Guide](docs/ONBOARDING_GUIDE.md)** - 包含 Alembic 設置說明
- **PR #1107**: https://github.com/RC918/morningai/pull/1107 - Alembic 實作參考

## Database Module 使用指南

### 模組概覽

MorningAI 使用 SQLAlchemy 2.0 + Alembic 進行資料庫操作。主要模組位於：

```
handoff/20250928/40_App/api-backend/src/
├── models/                    # SQLAlchemy 模型定義
│   ├── base.py               # Base 類別和共用 mixin
│   ├── agent_registry_db.py  # Agent 相關模型
│   └── ...
├── database/                  # 資料庫連線和 session 管理
│   ├── connection.py         # 連線池配置
│   └── session.py            # Session 工廠
└── repositories/              # 資料存取層
    └── ...
```

### 連線配置

```python
# 使用環境變數配置
from src.database.connection import get_engine, get_session

# 取得 engine（連線池）
engine = get_engine()

# 取得 session（建議使用 context manager）
with get_session() as session:
    result = session.query(AgentDB).filter_by(status='active').all()
```

### Session 管理最佳實踐

```python
# ✅ 正確做法 - 使用 context manager
from src.database.session import get_session

def get_active_agents():
    with get_session() as session:
        return session.query(AgentDB).filter_by(status='active').all()

# ❌ 錯誤做法 - 手動管理 session
def get_active_agents():
    session = Session()
    try:
        return session.query(AgentDB).filter_by(status='active').all()
    finally:
        session.close()  # 容易忘記
```

### 交易管理

```python
# 自動 commit/rollback
with get_session() as session:
    agent = AgentDB(name='new_agent', type=AgentTypeDB.DEV_AGENT)
    session.add(agent)
    # 離開 context 時自動 commit
    # 如果發生例外，自動 rollback
```

## Retry/Backoff 配置指南

### 概覽

MorningAI 使用 `tenacity` 庫進行重試邏輯，配置位於 `src/utils/retry_config.py`。

### 預設配置

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 標準重試配置
STANDARD_RETRY = {
    'stop': stop_after_attempt(3),           # 最多重試 3 次
    'wait': wait_exponential(
        multiplier=1,                         # 基礎等待時間 1 秒
        min=1,                                # 最小等待 1 秒
        max=10                                # 最大等待 10 秒
    ),
    'retry': retry_if_exception_type((
        ConnectionError,
        TimeoutError,
    )),
}

# 資料庫操作重試配置
DB_RETRY = {
    'stop': stop_after_attempt(5),           # 最多重試 5 次
    'wait': wait_exponential(
        multiplier=0.5,
        min=0.5,
        max=30
    ),
    'retry': retry_if_exception_type((
        OperationalError,
        InterfaceError,
    )),
}
```

### 使用範例

```python
from tenacity import retry
from src.utils.retry_config import STANDARD_RETRY, DB_RETRY

@retry(**STANDARD_RETRY)
def call_external_api():
    response = requests.get('https://api.example.com/data')
    response.raise_for_status()
    return response.json()

@retry(**DB_RETRY)
def save_to_database(data):
    with get_session() as session:
        session.add(data)
```

### 自訂重試配置

```python
from tenacity import retry, stop_after_attempt, wait_fixed

# 固定等待時間
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2)  # 每次等待 2 秒
)
def my_function():
    pass

# 帶回調的重試
@retry(
    stop=stop_after_attempt(3),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number}"
    )
)
def my_function_with_logging():
    pass
```

## Redis 驗證指南

### 連線驗證

```python
import redis
import os

def validate_redis_connection():
    """驗證 Redis 連線是否正常"""
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        raise ValueError("REDIS_URL environment variable not set")
    
    try:
        client = redis.from_url(redis_url)
        # PING 測試
        response = client.ping()
        if not response:
            raise ConnectionError("Redis PING failed")
        
        # 寫入/讀取測試
        test_key = '_health_check_'
        client.set(test_key, 'ok', ex=10)
        value = client.get(test_key)
        if value != b'ok':
            raise ValueError("Redis read/write test failed")
        
        client.delete(test_key)
        return True
    except redis.ConnectionError as e:
        raise ConnectionError(f"Cannot connect to Redis: {e}")
```

### 常見問題排查

| 問題 | 可能原因 | 解決方案 |
|------|---------|---------|
| `ConnectionRefusedError` | Redis 服務未啟動 | 啟動 Redis: `redis-server` |
| `AuthenticationError` | 密碼錯誤 | 檢查 REDIS_URL 中的密碼 |
| `TimeoutError` | 網路問題或 Redis 過載 | 檢查網路連線，增加 timeout |
| `ResponseError: NOAUTH` | 需要認證但未提供 | 在 REDIS_URL 中加入密碼 |

### 環境變數格式

```bash
# 本地開發（無密碼）
REDIS_URL=redis://localhost:6379/0

# 生產環境（有密碼）
REDIS_URL=redis://:password@redis-host:6379/0

# 帶 SSL
REDIS_URL=rediss://:password@redis-host:6379/0
```

## 並行安全測試指南

### 多進程同時初始化測試

當多個進程同時啟動並嘗試初始化共享資源時，可能發生 race condition。以下是測試方法：

```python
# tests/integration/test_concurrent_init.py
import pytest
import multiprocessing
import time
from src.database.connection import get_engine

def init_database_connection(result_queue, process_id):
    """模擬進程初始化資料庫連線"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        result_queue.put((process_id, 'success', None))
    except Exception as e:
        result_queue.put((process_id, 'error', str(e)))

def test_concurrent_database_init():
    """測試多進程同時初始化資料庫連線"""
    num_processes = 10
    result_queue = multiprocessing.Queue()
    processes = []
    
    # 同時啟動多個進程
    for i in range(num_processes):
        p = multiprocessing.Process(
            target=init_database_connection,
            args=(result_queue, i)
        )
        processes.append(p)
    
    # 同時啟動所有進程
    for p in processes:
        p.start()
    
    # 等待所有進程完成
    for p in processes:
        p.join(timeout=30)
    
    # 收集結果
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    # 驗證所有進程都成功
    errors = [r for r in results if r[1] == 'error']
    assert len(errors) == 0, f"Concurrent init errors: {errors}"
    assert len(results) == num_processes
```

### Redis 並行寫入測試

```python
def test_concurrent_redis_writes():
    """測試多進程同時寫入 Redis"""
    import redis
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    client = redis.from_url(os.environ['REDIS_URL'])
    num_writes = 100
    
    def write_to_redis(key_suffix):
        key = f"test_concurrent_{key_suffix}"
        client.set(key, f"value_{key_suffix}", ex=60)
        return client.get(key) == f"value_{key_suffix}".encode()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(write_to_redis, i) for i in range(num_writes)]
        results = [f.result() for f in as_completed(futures)]
    
    assert all(results), "Some concurrent writes failed"
```

## 測試環境 Cleanup 指南

### Test DB Teardown Safety Net

確保測試資料庫在測試後正確清理，防止測試污染：

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine, text
from src.database.connection import get_engine

@pytest.fixture(scope='session', autouse=True)
def setup_test_database():
    """Session-level fixture 確保測試資料庫設置和清理"""
    # Setup: 創建測試資料庫
    engine = get_engine()
    
    yield engine
    
    # Teardown: 清理所有測試資料
    with engine.connect() as conn:
        # 取得所有表格
        tables = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )).fetchall()
        
        # 清空所有表格（保留 schema）
        for (table,) in tables:
            if not table.startswith('alembic'):
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
        conn.commit()

@pytest.fixture(autouse=True)
def cleanup_after_each_test(request):
    """每個測試後清理"""
    yield
    
    # 測試後清理特定資料
    from src.database.session import get_session
    with get_session() as session:
        # 清理測試創建的資料
        session.execute(text("DELETE FROM agents WHERE name LIKE 'test_%'"))
        session.commit()
```

### 隔離測試資料

```python
# tests/fixtures/database.py
import pytest
from src.database.session import get_session

@pytest.fixture
def isolated_db_session():
    """提供隔離的資料庫 session，測試後自動 rollback"""
    with get_session() as session:
        # 開始 savepoint
        session.begin_nested()
        
        yield session
        
        # 測試後 rollback 到 savepoint
        session.rollback()

# 使用範例
def test_create_agent(isolated_db_session):
    agent = AgentDB(name='test_agent', type=AgentTypeDB.DEV_AGENT)
    isolated_db_session.add(agent)
    isolated_db_session.flush()
    
    assert agent.id is not None
    # 測試結束後，這個 agent 會被自動 rollback
```

### 清理檢查清單

測試環境清理時，確保：

- [ ] 所有測試表格已清空（除了 alembic_version）
- [ ] Redis 測試 keys 已刪除（使用 `test_*` prefix）
- [ ] 臨時檔案已刪除
- [ ] Mock 已還原
- [ ] 環境變數已還原

### 故障安全機制

```python
# tests/conftest.py
import atexit

def emergency_cleanup():
    """程式異常終止時的緊急清理"""
    try:
        from src.database.connection import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM agents WHERE name LIKE 'test_%'"))
            conn.commit()
    except Exception:
        pass  # 忽略清理錯誤

# 註冊緊急清理
atexit.register(emergency_cleanup)
```

---

## 驗收標準

所有 PR 需通過：

1. **i18n 要求（強制）**
   - 所有用戶可見字串使用 `t()` 或 `<Trans>`（無硬編碼字串）
   - 新 translation keys 已加入 `en-US.json` 和 `zh-TW.json`
   - Translation keys 使用適當的命名空間
   - 無障礙屬性已翻譯
   - ESLint i18n 規則通過（無 `i18next/no-literal-string` 錯誤）

2. **OpenAPI 驗證**
   - API schema 符合 OpenAPI 3.0 規範
   - 所有 endpoints 都有文檔

3. **測試覆蓋率**
   - 單元測試覆蓋率 ≥ 80%
   - 整合測試覆蓋率 ≥ 60%
   - 所有測試通過

4. **CI 檢查**
   - Lint 檢查通過（**包含 i18n 規則**）
   - Type 檢查通過（**不得引入新錯誤**）
   - Build 成功

5. **Post-deploy Health 斷言**
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
