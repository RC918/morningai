# Owner Console 具體完整 Phase 規劃

**文檔版本：** 1.0.0  
**創建日期：** 2025-11-15  
**負責人：** Ryan Chen (@RC918)  
**Repository：** RC918/morningai  
**Production Domain：** admin.gm365.me

---

## 📋 執行摘要

### 🎉 驗證狀態更新（2025-11-15）

經過深度代碼調查和測試驗證，實際完成狀態如下：

| Phase | 原計劃狀態 | 實際驗證狀態 | 完成度 |
|-------|-----------|-------------|--------|
| **Week 1 (P0)** | 待實施 | ✅ **已完成** | 100% |
| **Week 2 (P1)** | 待實施 | ✅ **已完成並超標** | 100% (Coverage 59.89% vs 目標 30%) |
| **Week 3 (P1)** | 待實施 | 🟡 **部分完成** | 60% |
| **Week 4 (P2)** | 待實施 | 🔴 **未開始** | 0% |

**關鍵發現：**
- ✅ Token 安全：完整實現（credentials + CSRF + 401 retry）
- ✅ 2FA 系統：10 組件 + 11 測試 + 強制執行
- ✅ 測試覆蓋率：59.89% lines（超標 2 倍）
- ✅ TenantManagement：真實 API 整合
- 🟡 Agent Logs：核心功能完成，缺細節（Trace 連結、抽屜、skeleton）
- 🟡 SystemMonitoring：基本完成，缺優化（skeleton、空狀態、圖表）
- 🔴 Billing/Subscription/Alerting：完全未開始

**詳細調查報告：** 見 `docs/WEEK_3_4_INVESTIGATION_REPORT.md`

### 當前狀態評估

經過深度調查，Owner Console 的實際進度遠超原路線圖估計：

- **原估計進度：** 15-20%
- **實際進度：** 40-50%
- **主要原因：** 最近兩週（PR #1289-1294）完成大量 UI/UX 整合、測試框架建立、真實 API 整合

### Phase 劃分策略

本規劃採用**週為單位的 Phase 劃分**，對應 P0→P1→P2 優先級：

- **Phase 1 (Week 1):** 安全性與部署驗證（P0）- ✅ **已完成**
- **Phase 2 (Week 2):** 完整性與基線品質（P1）- ✅ **已完成**
- **Phase 3 (Week 3):** UX 強化與數據運營（P1 尾段）- 🟡 **60% 完成**
- **Phase 4 (Week 4):** P2 功能原型與穩定化 - 🔴 **未開始**

每週五進行 Demo，確保可交付成果。

---

## 🎯 Phase 1: 安全性與部署驗證（Week 1）

**時間範圍：** 2025-11-18 至 2025-11-22（5 個工作日）  
**優先級：** P0 - 阻塞性任務  
**目標：** 完成核心安全機制驗證，確保生產環境可部署  
**實際狀態：** ✅ **已完成（2025-11-15 驗證）**

### 任務清單

#### 任務 1.1: Token 安全流程驗證與完成

**負責人：** Backend + Frontend  
**預估時間：** 2-3 天  
**狀態：** ✅ **已完成並驗證**

**驗證證據（2025-11-15）：**
- ✅ `api-client.ts:63` - 所有請求使用 `credentials: 'include'`
- ✅ `api-client.ts:49-54` - CSRF token 自動注入到 POST/PUT/PATCH/DELETE
- ✅ `auth.ts:484-521` - 401 自動刷新重試機制
- ✅ `auth.ts:402-428` - 403 CSRF 失敗自動重試機制
- ✅ `main.jsx:26` - 應用啟動時調用 `bootstrapCsrf()`
- ✅ `AuthProvider.tsx:65` - 組件掛載時調用 `initAuth()`
- ✅ Generated clients (`tenant.ts:15`, `admin.ts:19`) 正確導入 `apiClient`
- ✅ Fetch 使用審計：只有 3 個文件使用 `fetch()`（api-client.ts, auth.ts, UXMetrics.jsx - 全部合理）
- ✅ 相關 PR：#1282 "Fix Frontend Dashboard auth crash - CSRF token and routing"

**背景：**
- 後端 HttpOnly Cookie + CSRF 機制已完成（`auth_enhanced.py:270-272`）
- 前端 `auth.ts:12` 註釋確認「No token storage in localStorage」
- 需要驗證實際運行時是否完全使用 Cookie 流程

**子任務：**

1. **前端 ApiClient Cookie 化驗證**（0.5 天）
   - [ ] 檢查 `src/lib/api.ts` 的 `ApiClient` 類別
   - [ ] 確認所有請求使用 `credentials: 'include'`
   - [ ] 驗證無任何 `localStorage.setItem('token', ...)` 或 `sessionStorage` 使用
   - [ ] 檢查跨子域 Cookie 屬性：
     - `Domain=.gm365.me`（允許 admin.gm365.me 和 api.gm365.me 共享）
     - `Secure=true`（僅 HTTPS）
     - `SameSite=Lax`（防 CSRF，允許頂層導航）
   - [ ] 驗證 CSRF token 流程：`bootstrapCsrf()` → `X-CSRF-Token` header

2. **401 自動 Refresh 與重試邏輯**（1 天）
   - [ ] 實作 `ApiClient` 的 401 攔截器
   - [ ] 調用 `/api/auth/v2/refresh` 端點（使用 Cookie 中的 refresh token）
   - [ ] 成功後重試原始請求（最多 1 次）
   - [ ] 失敗後清除狀態並重定向到 `/login`
   - [ ] 單元測試：模擬 401 → refresh 成功 → 重試成功
   - [ ] 單元測試：模擬 401 → refresh 失敗 → 登出

3. **E2E 測試 Token 流程**（1 天）
   - [ ] Playwright 測試：登入 → 調用 API → 模擬 token 過期 → 自動 refresh → 繼續使用
   - [ ] 測試場景：
     - 正常登入 → 訪問 `/dashboard` → 檢查 API 請求成功
     - 手動清除 access token Cookie → 觸發 API → 驗證自動 refresh
     - 手動清除 refresh token Cookie → 觸發 API → 驗證重定向到登入頁
   - [ ] 錄製 Playwright trace 並附加到 PR

4. **安全審查**（0.5 天）
   - [ ] 檢查瀏覽器開發者工具：
     - Set-Cookie header 包含 `HttpOnly; Secure; SameSite=Lax`
     - 無 token 儲存在 localStorage/sessionStorage
   - [ ] XSS 風險檢查：確認無 `dangerouslySetInnerHTML` 使用 token
   - [ ] 跨子域測試：在 staging 環境驗證 Cookie 共享

**依賴關係：**
- 後端 `/api/auth/v2/refresh` 端點已存在 ✅
- 前端需要 `ApiClient` 類別重構

**驗收標準：**
- [ ] 代碼內無 token 儲存在 Web Storage
- [ ] E2E 測試通過（Playwright trace 附加到 PR）
- [ ] 安全審閱通過（Set-Cookie 標頭檢查，XSS 風險檢查）
- [ ] Staging 環境驗證成功

**風險與緩解：**
- **風險：** 跨子域 Cookie 在某些瀏覽器（Safari）可能被阻擋
  - **緩解：** 使用 `SameSite=Lax`（而非 `None`），測試 Safari 行為
- **風險：** CSRF token 與 Cookie 不同步導致 403
  - **緩解：** 確保 `bootstrapCsrf()` 在每次頁面載入時執行

---

#### 任務 1.2: 2FA 強制流程啟動

**負責人：** Backend + Frontend  
**預估時間：** 3-4 天（Week 1 啟動，Week 2 完成）  
**狀態：** 🔴 P0 阻塞

**背景：**
- 後端 2FA 端點已完成（`auth_2fa.py`, `totp.py`）
- 前端有測試覆蓋（`auth-2fa.test.tsx` 11 tests, `2fa-api.test.ts` 7 tests）
- 需要完整的 UI 流程與路由守衛

**Week 1 子任務（最小可演示片段）：**

1. **2FA Enroll UI 初版**（1.5 天）
   - [ ] 創建 `TwoFactorEnroll.tsx` 對話框元件
   - [ ] 顯示 QR code（使用 `qrcode.react` 或類似庫）
   - [ ] 輸入框驗證初次 TOTP（6 位數字）
   - [ ] 調用 `/api/auth/2fa/enroll` 端點
   - [ ] 成功後顯示 8 個 backup codes
   - [ ] 提供「下載 backup codes」按鈕（純文字檔案）
   - [ ] 單元測試：QR code 渲染、TOTP 驗證、backup codes 顯示

2. **2FA Challenge UI 初版**（1.5 天）
   - [ ] 創建 `TwoFactorChallenge.tsx` 對話框元件
   - [ ] 輸入框：TOTP 或 backup code
   - [ ] 「記住此裝置 30 天」勾選框
   - [ ] 調用 `/api/auth/2fa/verify` 端點
   - [ ] 錯誤處理：顯示「代碼無效」訊息，允許重試
   - [ ] 成功後關閉對話框，繼續登入流程
   - [ ] 單元測試：TOTP 驗證、backup code 驗證、trusted device 選項

3. **路由守衛初版**（0.5 天）
   - [ ] 在 `LoginPage.tsx` 中檢查 2FA 狀態
   - [ ] 如果 Owner 角色且未完成 2FA，顯示 `TwoFactorEnroll` 對話框
   - [ ] 如果 Owner 角色且已註冊 2FA，顯示 `TwoFactorChallenge` 對話框
   - [ ] 非 Owner 角色跳過 2FA（可選功能）

4. **Demo 準備**（0.5 天）
   - [ ] 錄製演示影片：Owner 登入 → 強制 2FA enroll → 掃描 QR → 驗證 TOTP → 顯示 backup codes
   - [ ] 錄製演示影片：Owner 登入 → 2FA challenge → 輸入 TOTP → 成功進入

**Week 2 子任務（完整功能）：** 見 Phase 2

**依賴關係：**
- 後端 2FA 端點存在 ✅
- 需要前端 UI/邏輯實作

**驗收標準（Week 1）：**
- [ ] Demo 流程可演示：強制挑戰彈窗與 happy-path 通過
- [ ] 單元/整合測試覆蓋核心分支
- [ ] PR 包含演示影片或 Playwright trace

**風險與緩解：**
- **風險：** QR code 生成失敗或無法掃描
  - **緩解：** 提供手動輸入 secret 的選項（顯示 Base32 字串）
- **風險：** Backup codes 下載被瀏覽器阻擋
  - **緩解：** 使用 `Blob` + `URL.createObjectURL` 方式下載

---

#### 任務 1.3: Vercel 預覽部署驗證

**負責人：** DevOps  
**預估時間：** 1 天  
**狀態：** 🟡 P1 驗證任務（從 P0 降級）

**背景：**
- `vercel-ignore.sh` 邏輯正確：允許 `develop/feature/fix/devin/*` 分支預覽部署
- PR 檢查顯示兩個 Vercel 專案都存在（morningai, owner-console）
- 最近的文檔 PR 因「純文檔變更」被正確跳過

**子任務：**

1. **創建驗證 PR**（0.5 天）
   - [ ] 在 `owner-console` 中做一個極小的 UI 改動（例如：修改 `OwnerDashboard.jsx` 的標題文字）
   - [ ] 創建 `devin/verify-vercel-preview` 分支
   - [ ] 推送並創建 PR
   - [ ] 等待 CI 完成，檢查 Vercel 部署狀態

2. **驗證預覽 URL**（0.25 天）
   - [ ] 在 PR 中找到兩個預覽 URL：
     - `morningai` 專案的預覽 URL
     - `owner-console` 專案的預覽 URL
   - [ ] 訪問兩個 URL，確認可正常載入
   - [ ] 測試基本功能：登入、導航、API 請求

3. **文檔更新**（0.25 天）
   - [ ] 更新 `docs/ONBOARDING_GUIDE.md` 的「部署流程」章節
   - [ ] 說明 Vercel 預覽部署的觸發條件
   - [ ] 說明如何在 PR 中找到預覽 URL
   - [ ] 如果 `owner-console` 需要獨立 `vercel.json`，補上並文件化

**依賴關係：**
- 無

**驗收標準：**
- [ ] PR 內貼兩個預覽 URL，能正常訪問
- [ ] `ONBOARDING_GUIDE.md` 更新完成
- [ ] 如需要，`owner-console/vercel.json` 已創建

**風險與緩解：**
- **風險：** `owner-console` 專案配置在 Vercel 後台而非 repo
  - **緩解：** 檢查 Vercel 後台設置，如需要創建 `vercel.json`

---

### Phase 1 交付成果

**PRs：**
1. Token 安全驗證與完成
2. 2FA 強制流程初版（enroll + challenge UI）
3. Vercel 預覽部署驗證

**文檔：**
- `OWNER_CONSOLE_PHASE_PLAN.md`（本文檔）
- `ONBOARDING_GUIDE.md`（部署/安全段落更新）

**Demo（週五）：**
- Token 安全流程演示（登入 → API 調用 → 自動 refresh）
- 2FA enroll 流程演示（QR code → TOTP 驗證 → backup codes）
- Vercel 預覽 URL 展示

---

## 🎯 Phase 2: 完整性與基線品質（Week 2）

**時間範圍：** 2025-11-25 至 2025-11-29（5 個工作日）  
**優先級：** P1 - 功能完善  
**目標：** 完成 2FA 完整流程，提升測試覆蓋率到 30%，完成 TenantManagement 真實 API 整合

### 任務清單

#### 任務 2.1: 2FA 強制流程完成

**負責人：** Backend + Frontend  
**預估時間：** 2 天（延續 Week 1）  
**狀態：** 🔴 P0 阻塞

**子任務：**

1. **完整 Enroll 流程**（0.5 天）
   - [ ] 添加「跳過」按鈕（僅限非 Owner 角色）
   - [ ] 添加「稍後設定」選項（Owner 角色下次登入仍會提示）
   - [ ] 優化 UI：loading 狀態、錯誤提示、成功動畫
   - [ ] 添加「重新生成 QR code」選項（如果掃描失敗）

2. **完整 Challenge 流程**（0.5 天）
   - [ ] 添加「使用 backup code」切換選項
   - [ ] 添加「忘記裝置？」連結（重新 enroll）
   - [ ] 優化錯誤處理：剩餘嘗試次數、鎖定機制
   - [ ] 添加「信任此裝置」的說明文字

3. **路由守衛完整實作**（0.5 天）
   - [ ] 在 `App.jsx` 中添加 `ProtectedRoute` 元件
   - [ ] 檢查 JWT 中的 `2fa_verified` claim
   - [ ] 未驗證的 Owner 角色重定向到 2FA 流程
   - [ ] 已驗證的用戶正常訪問
   - [ ] 非 Owner 角色跳過檢查

4. **E2E 測試完整流程**（0.5 天）
   - [ ] Playwright 測試：Owner 登入 → 強制 2FA enroll → 掃描 QR → 驗證 TOTP → 顯示 backup codes → 成功進入
   - [ ] Playwright 測試：Owner 登入 → 2FA challenge → 輸入 TOTP → 成功進入
   - [ ] Playwright 測試：Owner 登入 → 2FA challenge → 使用 backup code → 成功進入
   - [ ] Playwright 測試：Owner 登入 → 2FA challenge → 勾選「記住此裝置」→ 30 天內免 2FA
   - [ ] 錄製 Playwright trace 並附加到 PR

**驗收標準：**
- [ ] Owner 角色無法繞過 2FA
- [ ] 所有 2FA 流程 UI 完整且易用
- [ ] E2E 測試通過（Playwright trace 附加到 PR）
- [ ] 安全審計通過（TOTP secrets Fernet 加密儲存）

---

#### 任務 2.2: 測試覆蓋率提升到 30%

**負責人：** Frontend  
**預估時間：** 3-4 天  
**狀態：** 🟡 P1 品質提升

**背景：**
- 測試框架已完整（Vitest + Playwright）
- 218 個測試通過
- 當前覆蓋率未知，需要基線報告

**子任務：**

1. **運行完整 Coverage 報告**（0.5 天）
   - [ ] 在 `owner-console` 中運行 `pnpm test:coverage`
   - [ ] 生成 HTML 報告並檢查當前基線
   - [ ] 識別覆蓋率最低的模組（<20%）
   - [ ] 將報告截圖附加到 PR

2. **設定 CI Coverage 門檻**（0.5 天）
   - [ ] 在 `.github/workflows/frontend.yml` 中添加 coverage 檢查
   - [ ] 設定門檻：30%（先警告不阻塞）
   - [ ] 在 PR 中顯示 coverage 報告連結
   - [ ] 設定 coverage 趨勢追蹤（類似 TypeScript strict mode）

3. **補齊關鍵模組測試**（2-2.5 天）
   - [ ] **SystemMonitoring 頁面測試**（0.5 天）
     - 測試：載入時顯示 loading 狀態
     - 測試：API 成功後顯示數據
     - 測試：API 失敗後顯示錯誤訊息
     - 測試：重試按鈕功能
   - [ ] **AgentGovernance 頁面測試**（0.5 天）
     - 測試：4 個 tabs 切換
     - 測試：統計卡片顯示
     - 測試：表格排序/篩選
   - [ ] **TenantManagement 頁面測試**（0.5 天）
     - 測試：表格載入與顯示
     - 測試：分頁功能
     - 測試：搜尋功能
   - [ ] **ApiClient 完整測試**（0.5 天）
     - 測試：CSRF token 自動附加
     - 測試：401 自動 refresh
     - 測試：重試邏輯
   - [ ] **Auth 流程完整測試**（0.5 天）
     - 測試：登入成功流程
     - 測試：登入失敗處理
     - 測試：登出流程
     - 測試：token 過期處理

4. **新增 Playwright Smoke 測試**（0.5 天）
   - [ ] 測試：登入 → 導航到 Dashboard → 檢查頁面載入
   - [ ] 測試：登入 → 導航到 Governance → 檢查 tabs 顯示
   - [ ] 測試：登入 → 登出 → 檢查重定向到登入頁

**驗收標準：**
- [ ] 測試覆蓋率 ≥ 30%
- [ ] CI 彙報覆蓋率（在 PR 中顯示）
- [ ] 至少 3 條 Playwright smoke 測試通過
- [ ] Coverage 報告附加到 PR

**風險與緩解：**
- **風險：** 覆蓋率補測的工作量超預期
  - **緩解：** 先鎖定 30%，不要同週衝 40%
- **風險：** Playwright 測試在 CI 上 flake
  - **緩解：** 加重試、trace、視頻

---

#### 任務 2.3: TenantManagement 真實 API 整合

**負責人：** Frontend + Backend  
**預估時間：** 2-3 天  
**狀態：** 🟡 P1 功能完善

**背景：**
- 需要檢查 `TenantManagement.jsx` 當前狀態
- 如果使用 mock data，替換為真實 API

**子任務：**

1. **盤點當前狀態**（0.5 天）
   - [ ] 檢查 `TenantManagement.jsx` 是否使用 mock data
   - [ ] 檢查後端是否有 `/api/admin/tenants` 端點
   - [ ] 如果端點不存在，與後端團隊對齊 API 契約

2. **真實 API 整合**（1 天）
   - [ ] 替換 mock data 為 `ApiClient.get('/api/admin/tenants')`
   - [ ] 實作表格：排序、篩選、分頁
   - [ ] 實作搜尋功能（按 tenant name 或 ID）
   - [ ] 實作空狀態：「目前沒有租戶」
   - [ ] 實作錯誤處理：顯示錯誤訊息與重試按鈕

3. **單元/整合測試**（0.5 天）
   - [ ] 測試：API 成功後顯示租戶列表
   - [ ] 測試：API 失敗後顯示錯誤訊息
   - [ ] 測試：表格排序功能
   - [ ] 測試：表格篩選功能
   - [ ] 測試：分頁功能

4. **Playwright Smoke 測試**（0.5 天）
   - [ ] 測試：登入 → 導航到 Tenants → 檢查表格載入
   - [ ] 測試：點擊排序按鈕 → 檢查表格重新排序
   - [ ] 測試：輸入搜尋關鍵字 → 檢查表格篩選

**依賴關係：**
- 後端 `/api/admin/tenants` 端點（如不存在需補充）

**驗收標準：**
- [ ] TenantManagement 使用真實 API
- [ ] 表格功能完整（排序、篩選、分頁）
- [ ] 測試通過
- [ ] PR 內貼截圖/短錄屏

**風險與緩解：**
- **風險：** 後端 API 契約不明確
  - **緩解：** 先草擬 OpenAPI 草圖，快速對齊最小欄位

---

### Phase 2 交付成果

**PRs：**
1. 2FA 完整流程（enroll + challenge + 路由守衛 + E2E 測試）
2. 測試覆蓋率提升到 30%（Coverage 報告 + CI 門檻）
3. TenantManagement 真實 API 整合

**文檔：**
- `TESTING.md`（測試框架使用指南、覆蓋率目標）
- `ENVIRONMENTS.md`（如需更新）

**Demo（週五）：**
- 2FA 完整流程演示（enroll + challenge + trusted device）
- Coverage 報告展示（30% 達成）
- TenantManagement 真實 API 演示（表格排序/篩選/分頁）

---

## 🎯 Phase 3: UX 強化與數據運營（Week 3）

**時間範圍：** 2025-12-02 至 2025-12-06（5 個工作日）  
**優先級：** P1 尾段 - UX 優化  
**目標：** 清理 Mock Data，強化 Agent Execution Logs，完成 SystemMonitoring 收尾

### 任務清單

#### 任務 3.1: 清理 Mock Data 與死路徑

**負責人：** Frontend  
**預估時間：** 1-2 天  
**狀態：** 🟢 P2 清理任務

**子任務：**

1. **全庫 Mock Data 掃描**（0.5 天）
   - [ ] 運行 `grep -r "mock_api" handoff/20250928/40_App/owner-console/`
   - [ ] 運行 `grep -r "demo.*data" handoff/20250928/40_App/owner-console/`
   - [ ] 運行 `grep -r "DEMO_PATTERNS" handoff/20250928/40_App/owner-console/`
   - [ ] 列出所有 mock data 引用位置

2. **移除或 FeatureFlag 包裝**（0.5 天）
   - [ ] 可以直接刪除的 mock data：立即刪除
   - [ ] 無法立即刪除的：用 `FEATURE_MOCK_DATA` FeatureFlag 包裝
   - [ ] 更新 `feature-flags.ts` 添加 `FEATURE_MOCK_DATA` 定義

3. **補齊空狀態與錯誤處理**（0.5 天）
   - [ ] 所有頁面添加空狀態：「目前沒有數據」
   - [ ] 所有頁面添加錯誤處理：顯示錯誤訊息與重試按鈕
   - [ ] 所有頁面添加 loading 狀態：skeleton 或 spinner

4. **文檔更新**（0.5 天）
   - [ ] 更新 `ONBOARDING_GUIDE.md` 移除 mock data 相關說明
   - [ ] 更新 `PROJECT_STRUCTURE_REPORT.md` 反映真實狀態

**驗收標準：**
- [ ] 無殘留 `mock_api` 引用（或已用 FeatureFlag 控制）
- [ ] 所有頁面有適當的空狀態與錯誤處理
- [ ] 文檔更新完成

---

#### 任務 3.2: 強化 Agent Execution Logs

**負責人：** Frontend  
**預估時間：** 2-3 天  
**狀態：** 🟡 P1 功能強化

**背景：**
- `AgentExecutionLogs.tsx` 已完成 TypeScript 遷移（70% 完成）
- 需要添加篩選、分頁、Trace 連結、詳情抽屜

**子任務：**

1. **多維篩選功能**（1 天）
   - [ ] 添加篩選器 UI：
     - Agent Type 下拉選單（dev_agent, ops_agent, pm_agent, etc.）
     - Status 下拉選單（success, failed, pending, running）
     - Time Range 日期選擇器（last 24h, last 7d, last 30d, custom）
   - [ ] 實作篩選邏輯：更新 API 請求參數
   - [ ] 實作「清除篩選」按鈕
   - [ ] 單元測試：篩選器狀態管理

2. **分頁功能**（0.5 天）
   - [ ] 添加分頁 UI：使用 `shared-ui` 的 Pagination 元件
   - [ ] 實作分頁邏輯：更新 API 請求參數（`page`, `limit`）
   - [ ] 顯示總數：「顯示 1-20 / 共 150 筆」
   - [ ] 單元測試：分頁狀態管理

3. **Trace ID 連結驗證**（0.5 天）
   - [ ] 檢查後端是否有 trace 詳情查詢 API
   - [ ] 如果有：實作點擊 Trace ID → 跳轉到詳情頁
   - [ ] 如果沒有：實作點擊 Trace ID → 複製到剪貼簿（顯示 toast 提示）
   - [ ] 添加 tooltip：「點擊複製 Trace ID」

4. **詳細資訊抽屜**（0.5 天）
   - [ ] 創建 `ExecutionLogDrawer.tsx` 元件
   - [ ] 顯示完整 execution log：
     - Task ID, Agent Type, Status, Created At, Updated At
     - PR URL（如果有）
     - Error Message（如果失敗）
     - Trace ID（可複製）
   - [ ] 添加「關閉」按鈕
   - [ ] 單元測試：抽屜開關邏輯

5. **Skeleton 與 Loading 優化**（0.5 天）
   - [ ] 添加 skeleton loading：表格載入時顯示
   - [ ] 優化 loading 狀態：使用 `shared-ui` 的 Spinner 元件
   - [ ] 添加「載入中...」文字提示

**驗收標準：**
- [ ] 篩選功能完整且易用
- [ ] 分頁正常運作
- [ ] Trace ID 可點擊並跳轉（或複製）
- [ ] UI 流暢無卡頓
- [ ] 測試通過
- [ ] PR 貼截圖/短錄屏

---

#### 任務 3.3: SystemMonitoring 收尾

**負責人：** Frontend  
**預估時間：** 0.5-1 天  
**狀態：** 🟢 P2 收尾任務

**背景：**
- SystemMonitoring 已 80% 完成
- 需要添加 skeleton、空狀態、可選指標圖

**子任務：**

1. **Skeleton Loading**（0.25 天）
   - [ ] 添加 skeleton loading：統計卡片載入時顯示
   - [ ] 使用 `shared-ui` 的 Skeleton 元件

2. **空狀態優化**（0.25 天）
   - [ ] 添加空狀態：「目前沒有監控數據」
   - [ ] 添加「重新載入」按鈕

3. **可選指標圖表**（0.5 天，可選）
   - [ ] 添加輕量 sparkline 圖表（使用 `recharts` 或類似庫）
   - [ ] 顯示最近 24 小時的趨勢
   - [ ] 如果時間不足，可以跳過此項

**驗收標準：**
- [ ] Skeleton、空狀態、可選指標圖可見
- [ ] PR 截圖

---

### Phase 3 交付成果

**PRs：**
1. Mock Data 清理
2. Agent Execution Logs 強化（篩選/分頁/Trace 連結/詳情抽屜）
3. SystemMonitoring 收尾

**文檔：**
- `PROJECT_STRUCTURE_REPORT.md`（反映真實狀態）
- `ONBOARDING_GUIDE.md`（移除 mock data 說明）

**Demo（週五）：**
- Agent Execution Logs 完整功能演示（篩選/分頁/詳情抽屜）
- SystemMonitoring 收尾演示（skeleton/空狀態）
- Mock Data 清理報告

---

## 🎯 Phase 4: P2 功能原型與穩定化（Week 4）

**時間範圍：** 2025-12-09 至 2025-12-13（5 個工作日）  
**優先級：** P2 - 進階功能  
**目標：** 完成 Billing、Subscription、Alerting 原型，準備 Phase Exit Review

### 任務清單

#### 任務 4.1: Billing & Revenue Dashboard 原型

**負責人：** Backend + Frontend  
**預估時間：** 4-5 天  
**狀態：** 🟢 P2 新功能

**子任務：**

1. **後端契約定義**（1 天）
   - [ ] 設計 API 契約：`GET /api/admin/billing/revenue`
   - [ ] 定義資料結構：
     - 總營收（Total Revenue）
     - 月經常性收入（MRR）
     - 按 tenant 分組的營收
     - 按時間分組的營收（日/週/月）
   - [ ] 草擬 OpenAPI 規格

2. **後端最小統計彙總**（1.5 天）
   - [ ] 實作 `/api/admin/billing/revenue` 端點
   - [ ] 從 `billing_transactions` 表彙總數據
   - [ ] 實作快取機制（Redis，1 小時 TTL）
   - [ ] 單元測試：彙總邏輯

3. **前端圖表/表格初版**（1.5 天）
   - [ ] 創建 `BillingDashboard.jsx` 頁面
   - [ ] 添加統計卡片：總營收、MRR、本月營收
   - [ ] 添加圖表：營收趨勢（使用 `recharts`）
   - [ ] 添加表格：按 tenant 分組的營收
   - [ ] 單元測試：圖表渲染、表格顯示

4. **假資料與真資料路徑隔離**（0.5 天）
   - [ ] 使用 `FEATURE_BILLING_ENABLED` FeatureFlag
   - [ ] 如果 flag 關閉，顯示「功能開發中」提示
   - [ ] 如果 flag 開啟，顯示真實數據

**驗收標準：**
- [ ] 主要 KPI 可視化
- [ ] 文檔記錄資料來源與延遲特性
- [ ] FeatureFlag 控制功能開關

---

#### 任務 4.2: Tenant Subscription Management 原型

**負責人：** Backend + Frontend  
**預估時間：** 4-5 天  
**狀態：** 🟢 P2 新功能

**子任務：**

1. **訂閱模型設計**（1 天）
   - [ ] 設計訂閱模型：
     - 方案（Plan）：Free, Pro, Enterprise
     - 訂閱狀態（Status）：active, canceled, expired
     - 計費週期（Billing Cycle）：monthly, yearly
   - [ ] 設計資料庫 schema：`tenant_subscriptions` 表
   - [ ] 草擬 OpenAPI 規格

2. **後端訂閱管理 API**（1.5 天）
   - [ ] 實作 CRUD 端點：
     - `GET /api/admin/subscriptions` - 列出所有訂閱
     - `POST /api/admin/subscriptions` - 創建訂閱
     - `PUT /api/admin/subscriptions/{id}` - 更新訂閱
     - `DELETE /api/admin/subscriptions/{id}` - 取消訂閱
   - [ ] 實作訂閱邏輯：升級/降級/取消
   - [ ] 單元測試：CRUD 操作

3. **前端訂閱管理 UI**（1.5 天）
   - [ ] 創建 `SubscriptionManagement.jsx` 頁面
   - [ ] 添加表格：顯示所有訂閱
   - [ ] 添加「創建訂閱」對話框
   - [ ] 添加「編輯訂閱」對話框
   - [ ] 添加「取消訂閱」確認對話框
   - [ ] 單元測試：CRUD 操作

4. **支付閘道整合（可選）**（1 天，可選）
   - [ ] 如果需要整合第三方支付（Stripe, PayPal），先 mock 接口
   - [ ] 抽象清楚支付接口，便於日後替換
   - [ ] 如果時間不足，可以跳過此項

**驗收標準：**
- [ ] 基本 CRUD 流程打通
- [ ] 測試覆蓋核心流程
- [ ] FeatureFlag 控制功能開關

---

#### 任務 4.3: Automated Alerting System 原型

**負責人：** Backend + Frontend  
**預估時間：** 3-4 天  
**狀態：** 🟢 P2 新功能

**子任務：**

1. **規則模型設計**（0.5 天）
   - [ ] 設計警報規則模型：
     - 規則名稱（Rule Name）
     - 觸發條件（Condition）：例如「Queue depth > 100」
     - 通知渠道（Channel）：Email, Webhook, Slack
     - 觸發頻率（Frequency）：每 5 分鐘檢查一次
   - [ ] 設計資料庫 schema：`alert_rules` 表

2. **後端最小引擎**（1.5 天）
   - [ ] 實作 Cron job：每 5 分鐘檢查一次規則
   - [ ] 實作規則評估邏輯：檢查條件是否滿足
   - [ ] 實作通知發送：Email（使用 SendGrid）、Webhook（HTTP POST）
   - [ ] 單元測試：規則評估、通知發送

3. **前端規則配置 UI**（1 天）
   - [ ] 創建 `AlertingRules.jsx` 頁面
   - [ ] 添加表格：顯示所有規則
   - [ ] 添加「創建規則」對話框
   - [ ] 添加「編輯規則」對話框
   - [ ] 添加「刪除規則」確認對話框
   - [ ] 單元測試：CRUD 操作

4. **通知渠道整合**（1 天）
   - [ ] 先實作 Webhook（最簡單）
   - [ ] 再實作 Email（使用 SendGrid）
   - [ ] Slack 整合可以日後擴展

**驗收標準：**
- [ ] 能建立一條規則並觸發一次通知
- [ ] PR 有動作證明與演示
- [ ] FeatureFlag 控制功能開關

---

### Phase 4 交付成果

**PRs：**
1. Billing & Revenue Dashboard 原型
2. Tenant Subscription Management 原型
3. Automated Alerting System 原型

**文檔：**
- API 契約文檔（OpenAPI 規格）
- 配置指南（如何設定警報規則）
- 故障排除指南

**Demo（週五）：**
- Billing Dashboard 演示（營收趨勢圖表）
- Subscription Management 演示（CRUD 操作）
- Alerting System 演示（創建規則 → 觸發通知）

---

## 📊 並行執行與依賴關係

### 可並行執行的任務

**Week 1:**
- Token 安全驗證 ∥ 2FA Enroll UI 初版
- Vercel 預覽部署驗證（獨立任務）

**Week 2:**
- 2FA 完整流程 ∥ Coverage 提升（部分重疊）
- TenantManagement 整合（獨立任務）

**Week 3:**
- Mock Data 清理 ∥ Agent Execution Logs 強化
- SystemMonitoring 收尾（獨立任務）

**Week 4:**
- Billing Dashboard ∥ Subscription Management ∥ Alerting System（三者獨立）

### 依賴關係

**必須先後執行：**
1. Token 安全完整 → 2FA E2E 測試（Week 1 → Week 2）
2. 2FA 完整流程 → 路由守衛完整實作（Week 1 → Week 2）
3. TenantManagement 整合 → Mock Data 清理（Week 2 → Week 3）
4. Agent Execution Logs 強化 → Trace 連結（需確認後端支持）

---

## ✅ 驗收標準總覽（DoD Gates）

### 每週 DoD（Definition of Done）

**Week 1:**
- [ ] Token 安全 E2E 測試通過
- [ ] 2FA Enroll/Challenge UI 可演示
- [ ] Vercel 預覽 URL 可訪問
- [ ] 所有 PR 有演示影片或 Playwright trace

**Week 2:**
- [ ] 2FA 完整流程 E2E 測試通過
- [ ] Coverage 報告顯示 ≥30%
- [ ] TenantManagement 使用真實 API
- [ ] 所有 PR 有測試覆蓋

**Week 3:**
- [ ] 無殘留 mock_api 引用
- [ ] Agent Execution Logs 篩選/分頁/詳情可用
- [ ] SystemMonitoring 收尾完成
- [ ] 所有 PR 有截圖/錄屏

**Week 4:**
- [ ] Billing/Subscription/Alerting 原型可演示
- [ ] 所有功能有 FeatureFlag 控制
- [ ] API 契約文檔完成

### 安全任務驗收標準

**Token 安全：**
- [ ] 代碼內無 token 儲存在 Web Storage
- [ ] E2E 測試驗證自動 refresh
- [ ] Set-Cookie header 檢查通過
- [ ] XSS 風險檢查通過

**2FA 強制：**
- [ ] Owner 角色無法繞過 2FA
- [ ] 所有 2FA 流程 UI 完整
- [ ] E2E 測試覆蓋所有分支
- [ ] TOTP secrets Fernet 加密儲存

### 功能任務驗收標準

**測試覆蓋率：**
- [ ] CI 報告顯示 ≥30%
- [ ] 關鍵模組有測試覆蓋
- [ ] Playwright smoke 測試通過

**TenantManagement：**
- [ ] 使用真實 API
- [ ] 表格功能完整
- [ ] 測試通過

**Agent Execution Logs：**
- [ ] 篩選/分頁/詳情可用
- [ ] UI 流暢無卡頓
- [ ] 測試通過

---

## ⚠️ 風險評估與緩解策略

### 高風險項目

#### 1. 跨子域 Cookie/CSRF 兼容性

**風險等級：** 🔴 高  
**影響範圍：** Token 安全流程  
**緩解策略：**
- 在 staging 環境先驗證 Cookie 行為
- 打開瀏覽器開發者工具檢查 Set-Cookie、SameSite、Secure、Domain
- 測試 Safari 瀏覽器（對 Cookie 限制最嚴格）
- 如果跨子域 Cookie 失敗，考慮使用單一域名（api.gm365.me 作為 API 域）

#### 2. Playwright 測試 Flakiness

**風險等級：** 🟡 中  
**影響範圍：** E2E 測試  
**緩解策略：**
- CI 設定 retry（最多 3 次）
- 啟用 trace 和視頻錄製
- 本地先穩定再推送到 CI
- 使用 `waitForSelector` 而非固定延遲

#### 3. 後端 API 契約不明確

**風險等級：** 🟡 中  
**影響範圍：** TenantManagement, Billing, Subscription  
**緩解策略：**
- 先草擬 OpenAPI 草圖
- 快速對齊最小欄位
- 使用 mock server 進行前端開發（如 MSW）

#### 4. 測試覆蓋率補測工作量超預期

**風險等級：** 🟡 中  
**影響範圍：** Week 2 進度  
**緩解策略：**
- 先鎖定 30%，不要同週衝 40%
- 聚焦關鍵模組（ApiClient, Auth, 主要頁面）
- 避免長尾測試（邊緣 case）

### 中風險項目

#### 5. Agent Execution Logs 的 Trace 連結後端支持度不明確

**風險等級：** 🟢 低  
**影響範圍：** Week 3 功能  
**緩解策略：**
- 先確認後端是否有 trace 查詢 API
- 如果沒有，實作「複製 Trace ID」功能
- 添加 TODO 註釋，日後擴展

#### 6. Billing/Subscription 的後端資料來源與第三方支付閘道未定

**風險等級：** 🟢 低  
**影響範圍：** Week 4 功能  
**緩解策略：**
- Week 4 以原型為目標
- FeatureFlag 保護，避免影響現網
- 先出 OpenAPI 草案與資料字典

---

## 📈 成功指標與 KPI

### Phase 1 成功指標

- [ ] Token 安全 E2E 測試通過率 100%
- [ ] 2FA Enroll/Challenge UI 可演示
- [ ] Vercel 預覽 URL 可訪問率 100%
- [ ] 週五 Demo 完成

### Phase 2 成功指標

- [ ] 2FA 完整流程 E2E 測試通過率 100%
- [ ] 測試覆蓋率 ≥30%
- [ ] TenantManagement 使用真實 API
- [ ] 週五 Demo 完成

### Phase 3 成功指標

- [ ] Mock Data 清理完成率 100%
- [ ] Agent Execution Logs 功能完整度 100%
- [ ] SystemMonitoring 收尾完成
- [ ] 週五 Demo 完成

### Phase 4 成功指標

- [ ] Billing/Subscription/Alerting 原型可演示
- [ ] 所有功能有 FeatureFlag 控制
- [ ] API 契約文檔完成
- [ ] 週五 Demo 完成

---

## 🔗 GitHub Milestones/Issues 同步建議

### Milestones 更新

**建議創建/更新以下 Milestones：**

1. **Owner Console Phase 1 (Week 1)** - 安全性與部署驗證
   - Due Date: 2025-11-22
   - Issues: Token 安全、2FA 初版、Vercel 驗證

2. **Owner Console Phase 2 (Week 2)** - 完整性與基線品質
   - Due Date: 2025-11-29
   - Issues: 2FA 完整、Coverage 30%、TenantManagement

3. **Owner Console Phase 3 (Week 3)** - UX 強化與數據運營
   - Due Date: 2025-12-06
   - Issues: Mock 清理、Agent Logs 強化、SystemMonitoring 收尾

4. **Owner Console Phase 4 (Week 4)** - P2 功能原型
   - Due Date: 2025-12-13
   - Issues: Billing、Subscription、Alerting

### Issues 更新建議

**建議更新以下 Issues 狀態：**

1. **Issue #767** - Enhanced Token Security
   - 更新狀態：⏳ 80% → 🔴 P0 進行中
   - 添加 Week 1 子任務清單

2. **Issue #767** - 2FA Implementation
   - 更新狀態：⏳ 70% → 🔴 P0 進行中
   - 添加 Week 1-2 子任務清單

3. **Issue #768** - Basic System Monitoring
   - 更新狀態：⏳ 80% → 🟢 P2 收尾中
   - 添加 Week 3 子任務清單

4. **Issue #769** - Agent Execution Logs
   - 更新狀態：⏳ 70% → 🟡 P1 進行中
   - 添加 Week 3 子任務清單

5. **Issue #774** - PWA Implementation
   - 狀態：✅ 已完成
   - 建議關閉

---

## 📝 立即可執行的第一步行動清單

### Week 1 Day 1（2025-11-18）

**上午：**
1. [ ] 創建 `devin/week1-token-security` 分支
2. [ ] 檢查 `src/lib/api.ts` 的 `ApiClient` 類別
3. [ ] 確認所有請求使用 `credentials: 'include'`
4. [ ] 開始實作 401 攔截器

**下午：**
1. [ ] 創建 `devin/week1-2fa-enroll` 分支
2. [ ] 創建 `TwoFactorEnroll.tsx` 元件骨架
3. [ ] 安裝 `qrcode.react` 依賴
4. [ ] 開始實作 QR code 顯示

**晚上（可選）：**
1. [ ] 創建 `devin/verify-vercel-preview` 分支
2. [ ] 在 `owner-console` 中做極小 UI 改動
3. [ ] 推送並創建 PR

### Week 1 Day 2-5

按照 Phase 1 任務清單逐步執行，每天結束前更新進度到 GitHub Issues。

---

## 📚 參考文檔

### 內部文檔

- `docs/ONBOARDING_GUIDE.md` - 開發者入職指南
- `docs/PROJECT_STRUCTURE_REPORT.md` - 專案結構報告
- `docs/ENVIRONMENTS.md` - 環境變數文檔
- `docs/TESTING.md` - 測試框架使用指南（待創建）
- `config/env.schema.yaml` - 環境變數 schema

### 外部資源

- [Playwright 文檔](https://playwright.dev/)
- [Vitest 文檔](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)
- [HttpOnly Cookies](https://owasp.org/www-community/HttpOnly)

---

## 📞 聯絡資訊

**專案負責人：** Ryan Chen (@RC918)  
**Email：** ryan2939z@gmail.com  
**GitHub：** https://github.com/RC918/morningai  
**Production：** https://admin.gm365.me

---

**文檔狀態：** ✅ 完整且可執行  
**最後更新：** 2025-11-15  
**下次審查：** 每週五 Demo 後更新進度

---

## 附錄 A: 進度追蹤模板

### 週報模板

```markdown
# Owner Console Week X 進度報告

**日期：** YYYY-MM-DD  
**Phase：** Phase X  
**整體進度：** X%

## 本週完成

- [ ] 任務 1
- [ ] 任務 2
- [ ] 任務 3

## 本週阻塞

- 阻塞 1：描述與解決方案
- 阻塞 2：描述與解決方案

## 下週計劃

- [ ] 任務 1
- [ ] 任務 2
- [ ] 任務 3

## Demo 連結

- PR: #XXXX
- 演示影片: [連結]
- Playwright Trace: [連結]
```

---

## 附錄 B: PR 檢查清單

### 安全任務 PR 檢查清單

- [ ] E2E 測試通過
- [ ] 安全審查通過
- [ ] Set-Cookie header 檢查
- [ ] XSS 風險檢查
- [ ] 演示影片或 Playwright trace 附加

### 功能任務 PR 檢查清單

- [ ] 單元測試通過
- [ ] 整合測試通過
- [ ] Playwright smoke 測試通過
- [ ] 截圖或錄屏附加
- [ ] 文檔更新完成

---

**準備完成！** 🚀  
**Created by:** Devin AI  
**Date:** 2025-11-15  
**Requested by:** Ryan Chen (@RC918)
