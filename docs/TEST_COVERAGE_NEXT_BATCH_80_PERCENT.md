# Test Coverage Next Batch: 80% Target

## 概述
規劃下一批測試覆蓋率改進，目標從當前 75.65% 提升至 80%+。

**當前狀態**: 75.65% (654 tests)  
**目標**: 80%+ (預估需要 ~50-70 個新測試)  
**預計時程**: 2-3 個工作日  
**前置 PR**: #723 (已合併), #731 (coverage gate)

## 當前覆蓋率分析

### 低覆蓋率檔案（優先處理）

#### 1. governance.py - **35% 覆蓋率** 🔴
**當前狀態**:
- 總行數: 136 lines
- 已覆蓋: 48 lines
- 未覆蓋: 88 lines

**未覆蓋的關鍵功能**:
- 風險路由決策邏輯（high/medium/low risk routing）
- 多租戶策略衝突處理
- Policy 繼承和覆寫機制
- 動態策略重載
- 錯誤降級路徑（policy 失敗時的 fallback）

**測試計畫** (預估 20-25 個測試):
1. **風險路由測試** (8 tests):
   - High risk → human review 路由
   - Medium risk → enhanced monitoring 路由
   - Low risk → auto-approve 路由
   - 邊界條件（risk score 臨界值）
   - 多重風險因子組合
   - 風險評分計算正確性
   - 風險等級升降級
   - 自定義風險閾值

2. **多租戶策略測試** (6 tests):
   - 租戶 A 策略不影響租戶 B
   - 租戶策略繼承 global policy
   - 租戶策略覆寫 global policy
   - 租戶策略衝突解決
   - 跨租戶權限隔離
   - 租戶策略動態切換

3. **Policy 加載和重載測試** (4 tests):
   - 動態重載 policy（無需重啟）
   - Policy 版本控制
   - Policy 回滾機制
   - Policy 熱更新通知

4. **錯誤處理和降級測試** (4 tests):
   - Policy 解析失敗 → 使用 default policy
   - Policy 執行超時 → fail-safe mode
   - 無效 policy → 記錄錯誤並使用 fallback
   - Policy service 不可用 → 本地 cache

5. **工具權限矩陣測試** (3 tests):
   - 複雜權限組合（多個工具、多個角色）
   - 權限繼承鏈
   - 權限撤銷和恢復

**預期覆蓋率提升**: 35% → 70%+ (增加 35%)

#### 2. main.py - **65% 覆蓋率** 🟡
**當前狀態**:
- 總行數: 603 lines
- 已覆蓋: 389 lines
- 未覆蓋: 214 lines

**未覆蓋的關鍵功能**:
- 外部依賴失敗重試邏輯
- 降級路徑（graceful degradation）
- 複雜錯誤處理鏈
- 中間件組合和順序
- 請求/響應轉換

**測試計畫** (預估 15-20 個測試):
1. **外部依賴重試測試** (5 tests):
   - Supabase 連接失敗 → 重試 3 次
   - LLM API 超時 → exponential backoff
   - Redis 暫時不可用 → 跳過 cache
   - 第三方 API rate limit → 等待並重試
   - 所有重試失敗 → 返回降級響應

2. **降級路徑測試** (4 tests):
   - FAQ 搜尋失敗 → 返回 cached results
   - Agent 不可用 → 返回靜態回應
   - 向量搜尋失敗 → fallback 到關鍵字搜尋
   - 完全降級模式（所有外部依賴失敗）

3. **中間件測試** (4 tests):
   - 中間件執行順序正確性
   - 中間件異常不影響其他中間件
   - 中間件修改 request/response
   - 中間件短路（early return）

4. **複雜錯誤處理測試** (4 tests):
   - 嵌套錯誤處理（error in error handler）
   - 錯誤上下文保留
   - 錯誤聚合和報告
   - 自定義錯誤類型處理

5. **請求/響應轉換測試** (3 tests):
   - 請求參數驗證和轉換
   - 響應格式標準化
   - 國際化（i18n）響應

**預期覆蓋率提升**: 65% → 78%+ (增加 13%)

#### 3. agent.py - **70% 覆蓋率** 🟡
**當前狀態**:
- 總行數: 163 lines
- 已覆蓋: 114 lines
- 未覆蓋: 49 lines

**未覆蓋的關鍵功能**:
- 複雜任務編排
- 並發任務處理
- 任務優先級和排程
- 長時間運行任務監控

**測試計畫** (預估 10-12 個測試):
1. **任務編排測試** (4 tests):
   - 多步驟任務執行順序
   - 任務依賴關係處理
   - 任務失敗回滾
   - 條件分支任務

2. **並發處理測試** (3 tests):
   - 多個並發任務不互相干擾
   - 並發限制（max concurrent tasks）
   - 任務佇列滿時的處理

3. **任務監控測試** (3 tests):
   - 長時間運行任務進度追蹤
   - 任務超時檢測和終止
   - 任務資源使用監控

4. **任務優先級測試** (2 tests):
   - 高優先級任務優先執行
   - 優先級動態調整

**預期覆蓋率提升**: 70% → 82%+ (增加 12%)

### 中等覆蓋率檔案（次要優先）

#### 4. faq.py - **79% 覆蓋率** ✅
**當前狀態**: 已經相當好，可以暫緩

#### 5. auth_middleware.py - **68% 覆蓋率** 🟡
**測試計畫** (預估 5-8 個測試):
- Token 刷新機制
- 多種認證方式（JWT, API Key, OAuth）
- 認證失敗後的重試
- 認證 cache 機制

**預期覆蓋率提升**: 68% → 80%+ (增加 12%)

## FAQ E2E 測試整合

### 目標
將 FAQ 功能納入 fast-pass 測試矩陣，確保端到端流程正常。

### 測試場景 (預估 8-10 個 E2E 測試):

1. **完整 FAQ 生命週期** (1 test):
   - 創建 FAQ → 搜尋 FAQ → 更新 FAQ → 刪除 FAQ
   - 驗證每一步的響應和副作用

2. **FAQ 搜尋流程** (3 tests):
   - 關鍵字搜尋 → 向量搜尋 → 結果排序 → 分頁
   - 空搜尋結果處理
   - 搜尋結果 cache 驗證

3. **FAQ 權限流程** (2 tests):
   - User 角色：只能搜尋
   - Admin 角色：完整 CRUD 權限

4. **FAQ 與 Agent 整合** (2 tests):
   - Agent 查詢 FAQ 並回答用戶
   - Agent 建議新 FAQ（基於常見問題）

5. **FAQ 性能測試** (2 tests):
   - 大量 FAQ 搜尋性能
   - 並發搜尋請求處理

### Fast-Pass 矩陣配置
```yaml
# .github/workflows/e2e-fast-pass.yml
on:
  pull_request:
    paths:
      - 'handoff/**/api-backend/src/routes/faq.py'
      - 'handoff/**/api-backend/src/routes/agent.py'
      - 'handoff/**/api-backend/tests/test_faq_*.py'
      - 'handoff/**/api-backend/tests/test_agent_*.py'

jobs:
  faq-e2e:
    runs-on: ubuntu-latest
    steps:
      - name: Run FAQ E2E tests
        run: |
          pytest tests/e2e/test_faq_lifecycle.py -v
```

## 實施計畫

### Phase 1: Governance 深度覆蓋（Day 1-2）
**目標**: governance.py 從 35% → 70%+

**步驟**:
1. 創建 `test_governance_risk_routing.py` (8 tests)
2. 創建 `test_governance_multi_tenant.py` (6 tests)
3. 創建 `test_governance_policy_reload.py` (4 tests)
4. 擴展 `test_governance_authz.py` (7 tests → 11 tests)
5. 運行測試並驗證覆蓋率

**驗收標準**:
- governance.py 覆蓋率 ≥ 70%
- 所有新測試通過
- 無 flaky tests

### Phase 2: Main & Agent 錯誤處理（Day 2-3）
**目標**: main.py 65% → 78%, agent.py 70% → 82%

**步驟**:
1. 創建 `test_main_retry_degradation.py` (15 tests)
2. 創建 `test_agent_orchestration.py` (10 tests)
3. 擴展 `test_agent_error_paths.py` (17 tests → 25 tests)
4. 運行測試並驗證覆蓋率

**驗收標準**:
- main.py 覆蓋率 ≥ 78%
- agent.py 覆蓋率 ≥ 82%
- 所有新測試通過

### Phase 3: FAQ E2E 整合（Day 3）
**目標**: 建立 E2E 測試框架

**步驟**:
1. 創建 `tests/e2e/` 目錄結構
2. 創建 `test_faq_lifecycle.py` (10 tests)
3. 配置 fast-pass workflow
4. 運行 E2E 測試並驗證

**驗收標準**:
- 所有 E2E 測試通過
- Fast-pass 配置正確
- E2E 測試時間 < 2 分鐘

### Phase 4: 最終驗證和 PR（Day 3）
**步驟**:
1. 運行完整測試套件
2. 驗證總覆蓋率 ≥ 80%
3. 檢查 CI 通過
4. 創建 PR 並等待審查

**驗收標準**:
- 總覆蓋率 ≥ 80%
- 所有測試通過（預估 700+ tests）
- CI coverage gate 通過（≥ 75%）
- 無 flaky tests

## 預期成果

### 覆蓋率提升
- **governance.py**: 35% → 70% (+35%)
- **main.py**: 65% → 78% (+13%)
- **agent.py**: 70% → 82% (+12%)
- **auth_middleware.py**: 68% → 80% (+12%)
- **總覆蓋率**: 75.65% → 80%+ (+4.35%)

### 測試數量
- **當前**: 654 tests
- **新增**: ~60 tests
- **總計**: ~714 tests

### 測試執行時間
- **當前**: ~30 秒（unit tests）
- **新增**: ~10 秒（unit tests）+ ~2 分鐘（E2E tests）
- **總計**: ~2.5 分鐘

## 風險和緩解

### 風險 1: 測試過於複雜
**緩解**: 
- 使用 fixtures 和 helper functions 簡化測試
- 遵循 AAA 模式（Arrange, Act, Assert）
- 每個測試只驗證一個行為

### 風險 2: Flaky tests
**緩解**:
- 避免依賴外部服務（使用 mocks）
- 避免時間依賴（使用 freezegun）
- 使用 pytest-xdist 並行運行檢測競態條件

### 風險 3: 測試維護成本高
**緩解**:
- 使用 parametrize 減少重複代碼
- 建立共享 fixtures 庫
- 文檔化測試意圖和場景

### 風險 4: CI 時間過長
**緩解**:
- 使用 pytest-xdist 並行運行
- 分離 unit tests 和 E2E tests
- 只在相關檔案變更時運行 E2E tests（fast-pass）

## 成功指標

### 量化指標
- ✅ 總覆蓋率 ≥ 80%
- ✅ governance.py ≥ 70%
- ✅ main.py ≥ 78%
- ✅ agent.py ≥ 82%
- ✅ 所有測試通過率 100%
- ✅ CI 執行時間 < 5 分鐘

### 質化指標
- ✅ 測試可讀性高（清晰的測試名稱和結構）
- ✅ 測試穩定性高（無 flaky tests）
- ✅ 測試維護性好（易於修改和擴展）
- ✅ 測試覆蓋關鍵業務邏輯

## 參考資料
- [PR #723: Test Coverage Batch A/B/C](https://github.com/RC918/morningai/pull/723)
- [PR #731: Coverage Gate 75%](https://github.com/RC918/morningai/pull/731)
- [TEST_COVERAGE_IMPROVEMENT_REPORT.md](./TEST_COVERAGE_IMPROVEMENT_REPORT.md)
- [POST_DEPLOYMENT_MONITORING_24H.md](./POST_DEPLOYMENT_MONITORING_24H.md)

## 聯絡人
- **技術負責人**: Ryan Chen (@RC918)
- **Devin Session**: https://app.devin.ai/sessions/438417371dcc4d1f95886422404511ea
