# MorningAI 工程優化實施計劃

## 概述

本計劃旨在提升 MorningAI 平台的底層工程實作與開發流程，聚焦於可維護性、安全性和開發體驗改進。這些優化與高階功能規劃並不衝突，而是為平台的長期穩定性和可擴展性奠定基礎。

**目標**：
- 提高代碼可維護性和安全性
- 改善開發者體驗和工作流程
- 降低技術債務和運維風險
- 為未來功能擴展做好準備

**原則**：
- 每個優化項目獨立 PR（降低風險，便於回滾）
- 優先實施安全性和穩定性改進
- 添加 CI 防護規則防止新增問題
- 分階段推進，保持向後兼容

---

## 優先級分級

### P1：安全性/穩定性優先（立即實施）
1. 統一環境變量管理
2. 補強 faq_agent 遷移腳本

### P2：開發體驗/可見性（P1 完成後）
3. 為 shared-ui 建立專屬 Storybook
4. LangGraph 編排器啟用準備

### P3：架構優化（P1/P2 穩定後）
5. 根級模組重構為命名空間包

---

## 優化項目詳細計劃

### 1. 統一環境變量管理（P1）

#### 現狀問題
- **Schema 漂移**：56 個變量在 `config/env.schema.yaml` 中定義，但實際使用 83 個（27 個缺失）
- **分散訪問**：314 處 `os.getenv` 調用分散在 105 個文件中
- **缺少驗證**：關鍵變量如 `TOTP_ENCRYPTION_KEY` 未在 schema 中定義
- **無類型安全**：字符串轉換邏輯分散（如 "true"/"false" 轉 bool）
- **安全風險**：無統一的秘密管理和輪換策略

#### 技術方案
使用 **Pydantic BaseSettings** 實現類型化、驗證化的配置管理。

#### 實施階段

**PR 1a：添加防護機制（不改變運行時行為）**
- 範圍：
  - 創建 `common/config/settings.py` 模塊（Pydantic BaseSettings）
  - 映射 `config/env.schema.yaml` 中的所有變量
  - 添加 `Field(alias=...)` 支持舊變量名（寬限期）
  - 補全缺失的 27 個變量到 schema（包括 `TOTP_ENCRYPTION_KEY`）
  - 添加薄包裝函數 `getenv(name, default=None)` 記錄棄用警告
  - 添加 `.flake8` 配置排除 `.venv`
  - 添加 CI 規則：禁止新增直接 `os.getenv` 調用（允許在 `settings.py` 內部）
  - 生成 `.env.example` 從 settings 類
- 驗收標準：
  - CI 通過，無運行時行為變化
  - `.env.example` 自動生成且完整
  - 新 PR 中直接使用 `os.getenv` 會被 CI 阻止
- 風險：低（僅添加新模塊，不修改現有代碼）

**PR 1b：關鍵路徑遷移（保留別名回退）**
- 範圍：
  - 替換關鍵路徑中的 `os.getenv`：
    - 認證/TOTP（`totp.py`, `auth_enhanced.py`）
    - 數據庫連接（`main.py`, `worker.py`）
    - Redis 配置（`redis_config.py`, `redis_client.py`）
    - 外部 API 密鑰（`github_api.py`, OpenAI 調用）
  - 保留別名映射避免破壞（如 `SECRET_KEY` → `FLASK_SECRET_KEY`）
  - 添加運行時驗證：進程啟動時檢查必需變量
- 驗收標準：
  - 所有測試通過（包括 E2E）
  - 本地開發環境正常運行
  - 生產環境部署無問題
- 風險：中（修改關鍵路徑，需充分測試）

**PR 1c：批量遷移剩餘模塊**
- 範圍：
  - 使用 `rg` + `sed` 批量替換剩餘 `os.getenv` 調用
  - 按模塊分批進行（每個 PR 10-20 個文件）
  - 移除包裝函數回退
  - 強制 CI 規則：任何 `os.getenv` 使用（除 `settings.py` 內部）都失敗
- 驗收標準：
  - 代碼庫中無直接 `os.getenv` 調用（除 `settings.py`）
  - 所有測試通過
  - CI 強制執行新規則
- 風險：低（分批進行，每批獨立驗證）

#### 時間估算
- PR 1a：2-3 天
- PR 1b：3-4 天
- PR 1c：4-5 天（分 3-4 個 PR）
- **總計**：9-12 天

---

### 2. 補強 faq_agent 遷移腳本（P1）

#### 現狀問題
- **執行方式簡單**：`deploy.sh` + `psql` 直接執行 SQL
- **缺少預檢查**：無數據庫狀態驗證
- **無回滾支持**：失敗時無自動回滾
- **無詳細驗證**：不檢查表結構、索引等
- **與 dev_agent 不一致**：dev_agent 有完善的 Python 運行器（295 行）

#### 技術方案
提取通用遷移工具，創建共享的 Python 運行器。

#### 實施階段

**PR 2a：提取通用遷移工具**
- 範圍：
  - 分析 `agents/dev_agent/migrations/run_migration.py`（295 行）
  - 提取通用邏輯到 `tools/db_migrations/runner.py`：
    - 數據庫連接管理
    - 事務性執行（每個文件一個事務）
    - 遷移狀態追蹤表（`applied_migrations`）
    - 冪等性檢查
    - Dry-run 模式
    - Schema 前置條件驗證
    - 錯誤回滾
    - 結構化日誌
  - 設置 `statement_timeout` 和 `lock_timeout` 安全值
  - 創建 `agents/faq_agent/migrations/run_migration.py` 使用共享工具
  - 保留 `deploy.sh` 作為薄包裝調用 Python
- 驗收標準：
  - Python 運行器可獨立執行 faq_agent 遷移
  - Dry-run 模式正常工作
  - 錯誤時自動回滾
  - 日誌清晰詳細
- 風險：低（新增工具，不修改現有流程）

**PR 2b：添加 CI 測試**
- 範圍：
  - 添加 CI job 使用臨時 PostgreSQL 容器
  - 從乾淨數據庫應用 faq_agent 遷移
  - 測試回滾邏輯（故意引入錯誤）
  - 驗證冪等性（重複執行）
- 驗收標準：
  - CI 中遷移測試通過
  - 回滾測試正常工作
  - 冪等性測試通過
- 風險：低（僅添加測試）

**PR 2c（可選）：重構 dev_agent 使用共享工具**
- 範圍：
  - 將 `agents/dev_agent/migrations/run_migration.py` 重構為使用 `tools/db_migrations/runner.py`
  - 保留 dev_agent 特定的檢查（pgvector、特定表名）
- 驗收標準：
  - dev_agent 遷移功能不變
  - 代碼重複減少
- 風險：低（重構現有功能）

#### 時間估算
- PR 2a：3-4 天
- PR 2b：1-2 天
- PR 2c（可選）：2-3 天
- **總計**：4-6 天（不含可選）

---

### 3. 為 shared-ui 建立專屬 Storybook（P2）

#### 現狀問題
- **組件無可視化**：47 個組件文件，0 個 stories
- **測試覆蓋不足**：無組件級視覺測試
- **文檔缺失**：開發者難以了解組件用法
- **責任不清**：應用層 Storybook（26 stories）記錄業務組件和設計系統

#### 技術方案
在 `packages/shared-ui` 中添加獨立 Storybook，與應用層 Storybook 共存。

#### 實施階段

**PR 3：添加 shared-ui Storybook**
- 範圍：
  - 在 `packages/shared-ui` 添加 `.storybook/` 目錄
  - 配置使用 `@storybook/react-vite` 8.6.14（對齊 root overrides）
  - 添加 addons：`a11y`, `interactions`, `essentials`, `links`
  - 啟用 autodocs 和 CSF 3.0
  - 組織結構：
    - **Foundations**：tokens, colors, spacing, typography, shadows
    - **Primitives**：Button, Input, Dialog, Modal, Sheet 等
    - **Patterns**：Forms, Navigation, Feedback
    - **Utilities**：Toasts, Loaders, Skeletons
  - 為每個組件創建 `.stories.tsx` 文件（共存於組件目錄）
  - 添加 `package.json` scripts：
    - `storybook`: 開發服務器
    - `build-storybook`: 靜態構建
  - 添加 CI job：
    - Storybook 構建測試
    - a11y 檢查（axe-core）
    - 可選：Playwright VRT（如不使用 Chromatic）
  - 更新 `packages/shared-ui/README.md` 添加 Storybook 使用說明
- 驗收標準：
  - Storybook 本地運行正常（`pnpm --filter @morningai/shared-ui storybook`）
  - 至少 20 個組件有 stories（優先核心組件）
  - a11y 檢查通過
  - CI 構建成功
  - 文檔清晰完整
- 風險：低（新增功能，不影響現有代碼）

**未來增強（不在本計劃範圍）**：
- Storybook Composition：應用層 Storybook 可組合 shared-ui Storybook
- Chromatic 集成：如需外部 SaaS 進行視覺回歸測試
- 交互測試：使用 `@storybook/test` 添加組件交互測試

#### 時間估算
- PR 3：5-7 天（包含為 20+ 組件創建 stories）
- **總計**：5-7 天

---

### 4. LangGraph 編排器啟用準備（P2）

#### 現狀問題
- **全局開關風險**：`USE_LANGGRAPH=false` 是全局標誌，切換影響所有任務
- **無漸進式推出**：無法小範圍測試 LangGraph 模式
- **缺少監控**：無法比較兩種模式的性能和可靠性
- **回滾困難**：出問題時只能全局回滾

#### 技術方案
添加金絲雀推出機制，支持按百分比或按任務啟用 LangGraph。

#### 實施階段

**PR 4：添加金絲雀機制**
- 範圍：
  - 添加環境變量 `USE_LANGGRAPH_PERCENT`（0-100，默認 0）
  - 或添加任務級標誌（payload 中 `use_langgraph: bool`）
  - 在 `worker.py:303-307` 添加選擇邏輯：
    ```python
    # 按百分比
    use_langgraph = (
        os.getenv("USE_LANGGRAPH", "false").lower() == "true" or
        (random.randint(1, 100) <= int(os.getenv("USE_LANGGRAPH_PERCENT", "0")))
    )
    
    # 或按任務
    use_langgraph = task_payload.get("use_langgraph", False)
    ```
  - 添加結構化日誌記錄選擇決策：
    ```python
    logger.info(
        "Orchestrator mode selected",
        extra={
            "task_id": task_id,
            "mode": "langgraph" if use_langgraph else "simple",
            "reason": "percent_rollout" or "task_flag" or "global_flag"
        }
    )
    ```
  - 添加指標追蹤（可選，如有 Sentry/DataDog）：
    - 執行時長
    - 重試次數
    - 失敗率
    - 決策邊緣路徑
  - 創建運維手冊 `docs/deployment/LANGGRAPH_ROLLOUT.md`：
    - 啟用步驟
    - 監控指標
    - 回滾流程（設置 `USE_LANGGRAPH_PERCENT=0`）
    - 故障排查
- 驗收標準：
  - 金絲雀機制正常工作
  - 日誌清晰記錄模式選擇
  - 運維手冊完整
  - 測試覆蓋兩種模式
- 風險：低（添加選擇邏輯，不改變現有行為）

**生產推出計劃（不在本 PR 範圍）**：
1. 在 staging 環境設置 `USE_LANGGRAPH_PERCENT=100` 測試 1 周
2. 在 production 設置 `USE_LANGGRAPH_PERCENT=5` 金絲雀測試
3. 逐步提升：5% → 25% → 50% → 100%
4. 每個階段監控 1-3 天，無問題再提升
5. 出問題立即回滾到 0%

#### 時間估算
- PR 4：2-3 天
- **總計**：2-3 天

---

### 5. 根級模組重構為命名空間包（P3）

#### 現狀問題
- **18 個根級 Python 文件**：`phase4-7_*.py`, `*_manager.py` 等
- **導入路徑不清晰**：直接從根目錄導入
- **潛在命名衝突**：根級命名空間污染

#### 技術方案
創建 `morningai_core` 命名空間包，逐步遷移根級模塊。

#### 實施階段

**PR 5a：創建命名空間包並遷移核心管理器**
- 範圍：
  - 創建 `morningai_core/` 包（使用 `src/` 佈局）
  - 遷移核心管理器（小批量）：
    - `persistent_state_manager.py` → `morningai_core/managers/state.py`
    - `security_manager.py` → `morningai_core/managers/security.py`
    - `knowledge_graph_manager.py` → `morningai_core/managers/knowledge_graph.py`
  - 在舊位置添加 shim 文件（重新導出 + 棄用警告）：
    ```python
    # persistent_state_manager.py (shim)
    import warnings
    from morningai_core.managers.state import *
    
    warnings.warn(
        "Importing from root-level persistent_state_manager.py is deprecated. "
        "Use 'from morningai_core.managers import state' instead.",
        DeprecationWarning,
        stacklevel=2
    )
    ```
  - 更新 `PYTHONPATH` 配置：
    - `render.yaml`
    - 本地開發腳本
    - CI 工作流
  - 添加 `flake8-import-order` 或 `isort` 檢查循環導入
- 驗收標準：
  - 所有測試通過
  - 新導入路徑正常工作
  - Shim 文件正常工作（向後兼容）
  - CI 通過
- 風險：高（影響導入路徑，需充分測試）

**PR 5b+：批量遷移剩餘模塊**
- 範圍：
  - 按領域分批遷移：
    - Phase API 模塊 → `morningai_core/phases/`
    - 其他工具模塊 → `morningai_core/utils/`
  - 每批 3-5 個文件
  - 更新所有導入引用
  - 保留 shim 文件
- 驗收標準：
  - 每批獨立測試通過
  - 無破壞性變更
- 風險：中（分批進行降低風險）

**PR 5c：移除 Shim 文件（棄用期後）**
- 範圍：
  - 在 1-2 個版本後移除 shim 文件
  - 更新所有剩餘的舊導入路徑
  - 強制使用新導入路徑
- 驗收標準：
  - 無舊導入路徑殘留
  - 所有測試通過
- 風險：低（有棄用期緩衝）

#### 時間估算
- PR 5a：4-5 天
- PR 5b+：6-8 天（分 2-3 個 PR）
- PR 5c：2-3 天
- **總計**：12-16 天

**注意**：此項目風險最高，建議在 P1/P2 項目穩定後再進行。

---

## 總體時間線

### 第一階段：P1 項目（安全性/穩定性）
- **Week 1-2**：統一環境變量管理（PR 1a, 1b）
- **Week 3**：補強 faq_agent 遷移腳本（PR 2a, 2b）
- **Week 4**：統一環境變量管理完成（PR 1c）
- **總計**：3-4 週

### 第二階段：P2 項目（開發體驗）
- **Week 5-6**：為 shared-ui 建立專屬 Storybook（PR 3）
- **Week 6**：LangGraph 編排器啟用準備（PR 4）
- **總計**：2 週

### 第三階段：P3 項目（架構優化，可選）
- **Week 7-9**：根級模組重構為命名空間包（PR 5a, 5b+, 5c）
- **總計**：3 週

**總體時間估算**：8-9 週（不含 P3）或 11-12 週（含 P3）

---

## CI/CD 變更

### 新增 CI 規則
1. **環境變量檢查**：
   - 禁止新增直接 `os.getenv` 調用（除 `settings.py` 內部）
   - 檢查 schema 與代碼使用的一致性

2. **Flake8 配置**：
   - 添加 `.flake8` 排除 `.venv`, `.git`, `dist`, `build`

3. **Storybook 構建**：
   - 添加 shared-ui Storybook 構建 job
   - a11y 檢查（axe-core）

4. **遷移測試**：
   - faq_agent 遷移在臨時 PostgreSQL 中測試

5. **導入檢查**：
   - 使用 `flake8-import-order` 或 `isort` 檢查循環導入

---

## 風險評估與緩解

### 高風險項目
1. **統一環境變量管理（PR 1b）**
   - 風險：修改關鍵路徑可能破壞認證/數據庫連接
   - 緩解：
     - 充分的單元測試和 E2E 測試
     - 在 staging 環境完整測試
     - 保留別名回退機制
     - 分階段推進，先添加防護再遷移

2. **根級模組重構（PR 5a）**
   - 風險：影響所有導入路徑，可能破壞測試和部署
   - 緩解：
     - 使用 shim 文件保持向後兼容
     - 小批量遷移（每批 3-5 個文件）
     - 充分的測試覆蓋
     - 更新所有 PYTHONPATH 配置
     - 在 P1/P2 穩定後再進行

### 中風險項目
1. **faq_agent 遷移腳本（PR 2a）**
   - 風險：遷移邏輯錯誤可能導致數據損壞
   - 緩解：
     - 在臨時數據庫中充分測試
     - 添加 dry-run 模式
     - 事務性執行，錯誤自動回滾
     - 在 staging 環境先測試

### 低風險項目
1. **shared-ui Storybook（PR 3）**
   - 風險：低，僅添加新功能
   - 緩解：獨立於現有代碼，不影響運行時

2. **LangGraph 金絲雀機制（PR 4）**
   - 風險：低，僅添加選擇邏輯
   - 緩解：默認行為不變，充分測試

---

## 驗收標準

### 全局標準（所有 PR）
- ✅ 所有 CI 檢查通過
- ✅ 測試覆蓋率不降低（保持 74%+）
- ✅ 無新增 lint 錯誤
- ✅ 文檔更新完整
- ✅ 在 staging 環境測試通過
- ✅ Code review 通過

### 項目特定標準
見各項目的「驗收標準」部分。

---

## 回滾計劃

### PR 級回滾
- 每個 PR 獨立，可單獨回滾
- 使用 `git revert` 而非 `git reset`
- 保留 commit 歷史

### 功能級回滾
1. **環境變量管理**：
   - PR 1a：直接回滾（無運行時影響）
   - PR 1b：回滾並恢復舊環境變量名
   - PR 1c：回滾單個批次

2. **faq_agent 遷移**：
   - 保留舊 `deploy.sh` 作為備份
   - 新運行器出問題可切回舊方式

3. **LangGraph 金絲雀**：
   - 設置 `USE_LANGGRAPH_PERCENT=0` 立即禁用

4. **根級模組重構**：
   - Shim 文件提供向後兼容
   - 可延長棄用期

---

## 運維影響

### 部署變更
1. **環境變量**：
   - 需要在 Render/Vercel 更新環境變量配置
   - 添加新的必需變量（如 `TOTP_ENCRYPTION_KEY` 到 schema）
   - 更新 `.env.example`

2. **PYTHONPATH**：
   - 更新 `render.yaml` 中的 PYTHONPATH
   - 更新本地開發腳本

3. **數據庫遷移**：
   - faq_agent 遷移方式變更（從 shell 到 Python）
   - 需要更新部署文檔

### 監控需求
1. **LangGraph 金絲雀**：
   - 監控兩種模式的執行時長、失敗率
   - 設置告警閾值

2. **環境變量**：
   - 監控啟動時的配置驗證錯誤
   - 記錄棄用警告

---

## 待確認問題

### 技術決策
1. **Storybook VRT**：
   - 使用 Chromatic（外部 SaaS）還是 Playwright VRT？
   - 公司是否有外部 SaaS 使用政策？

2. **秘密管理**：
   - 本地開發使用 `.env.local` 還是 SOPS/1Password？
   - 生產環境僅使用 Render/Vercel 秘密存儲？

3. **LangGraph 監控**：
   - 使用 Sentry/DataDog 還是僅 stdout 日誌？
   - 需要哪些 SLO 指標？

### 實施順序
1. **P1/P2 並行**：
   - 是否允許 P1 和 P2 項目並行進行？
   - 還是必須 P1 完成後再開始 P2？

2. **P3 執行**：
   - 是否執行 P3（根級模組重構）？
   - 還是暫時擱置，等待更合適的時機？

### 資源分配
1. **時間預算**：
   - 是否接受 8-12 週的時間線？
   - 是否需要壓縮時間？

2. **優先級調整**：
   - 是否需要調整項目優先級？
   - 是否有其他緊急項目需要插入？

---

## 下一步行動

1. **審核本計劃**：
   - 確認優先級和範圍
   - 確認技術方案
   - 確認時間線

2. **回答待確認問題**：
   - 技術決策
   - 實施順序
   - 資源分配

3. **開始實施**：
   - 創建 tracking issue
   - 開始 PR 1a（環境變量防護機制）

---

## 附錄

### 參考文件
- `config/env.schema.yaml`：環境變量 schema
- `agents/dev_agent/migrations/run_migration.py`：遷移運行器參考
- `packages/shared-ui/package.json`：shared-ui 配置
- `handoff/20250928/40_App/frontend-dashboard/.storybook/main.ts`：Storybook 配置參考
- `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:303-307`：LangGraph 選擇邏輯

### 相關文檔
- `docs/ENVIRONMENTS.md`：環境架構文檔
- `docs/PROJECT_STRUCTURE_REPORT.md`：項目結構報告
- `docs/ONBOARDING_GUIDE.md`：入職指南

### 工具和庫
- **Pydantic**：類型化配置管理
- **Storybook 8.6.14**：組件文檔
- **pytest**：測試框架
- **flake8**：代碼檢查
- **rg (ripgrep)**：代碼搜索
