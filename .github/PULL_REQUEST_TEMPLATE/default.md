<!--
================================================================================
DEFAULT PR TEMPLATE - 預設 PR 模板
================================================================================

適用時機 (When to Use):
- 一般功能開發、bug 修復、重構
- 文檔更新、CI/CD 變更
- 任何非 Phase 2 遷移或緊急修復的 PR

注意事項 (Important Notes):
- 此模板不包含 Phase 2 Audit Checklist
- 如果您的 PR 是 Phase 2 設計系統遷移，請使用 phase2.md 模板
  選擇方式：在 PR URL 後加上 ?template=phase2.md
- 如果是緊急修復，請使用 hotfix.md 模板

其他模板:
- Phase 2 遷移: ?template=phase2.md
- 緊急修復: ?template=hotfix.md

文檔參考: CONTRIBUTING.md#pr-template-選擇
================================================================================
-->

## PR Title 格式（必須）

<!-- PR title 必須符合以下格式，否則 CI 會失敗 -->

**格式：** `<type>: <description>` 或 `<type>(<scope>): <description>`

**常用類型：** `feat:`, `fix:`, `docs:`, `ci:`, `refactor:`, `chore:`, `deps:`, `test:`, `perf:`, `style:`

**完整規範：** [docs/development/commit_hygiene.md](../../docs/development/commit_hygiene.md)

## 描述 (Description)

<!-- 簡要說明此 PR 的目的和變更內容 -->

## PR 類型與優先級 (PR Type & Priority)

<!-- 請勾選此 PR 的類型，並在合併前確保已加上對應的 GitHub label -->

- [ ] **P0 - 主線功能 / 緊急修復 (Blocking)** - 必須立即處理，阻擋主線進度
- [ ] **P1 - 修正既有問題 / 改善體驗 (Non-blocking)** - 重要但不阻擋主線
- [ ] **P2 - 優化 / 重構 / 技術債 (Nice-to-have)** - 可排期處理

**對應 GitHub Labels**: `P0-urgent`, `P1`, `P2`

## 本 PR 不處理 (Out of Scope)

<!-- 
明確列出此 PR 不會處理的項目，避免 scope creep。
這些項目應該建立為 follow-up issues 或 PRs。
-->

- [此處列出不處理的項目，若無則刪除此行]

## 如何測試 (How to Test)

<!-- 請詳細說明如何測試此 PR 的變更 -->

### 測試類型 (Test Types)

請勾選已執行的測試類型：

- [ ] 單元測試 (Unit Tests) - `pnpm test`
- [ ] 整合測試 (Integration Tests)
- [ ] E2E 測試 (End-to-End Tests) - Playwright
- [ ] 視覺回歸測試 (Visual Regression Tests) - VRT
- [ ] 手動測試 (Manual Testing)
- [ ] 無障礙測試 (Accessibility Testing)

### 測試步驟 (Test Steps)

<!-- 請描述手動測試的具體步驟 -->

1. 
2. 
3. 

### 預期結果 (Expected Results)

<!-- 描述預期的行為和結果 -->

### 實際結果 (Actual Results)

<!-- 描述實際觀察到的行為和結果 -->

### 測試環境 (Test Environment)

- [ ] 本地開發環境 (Local Development)
- [ ] CI/CD Pipeline
- [ ] Staging 環境
- [ ] 不同瀏覽器測試（如適用）：Chrome / Firefox / Safari / Edge

### 受影響的區域 (Affected Areas)

<!-- 列出此變更可能影響的其他功能或區域 -->

- 

### 截圖/影片 (Screenshots/Videos)

<!-- 如有 UI 變更，請附上截圖或影片 -->

### 新增的自動化測試 (New Automated Tests)

<!-- 列出為此 PR 新增的測試文件和測試案例 -->

- 

## i18n 檢查清單（強制）

<!-- 所有用戶可見的變更都必須符合 i18n 要求 -->

- [ ] 所有用戶可見字串使用 `t()` 或 `<Trans>`（無硬編碼字串）
- [ ] 新 translation keys 已加入 `en-US.json` 和 `zh-TW.json`
- [ ] Translation keys 使用適當的命名空間（例如：`settings.2fa.title`）
- [ ] 無障礙屬性（`alt`、`aria-label`、`title`、`placeholder`）已翻譯
- [ ] ESLint i18n 規則通過（無 `i18next/no-literal-string` 錯誤）
- [ ] 已測試語言切換（如有 UI 變更）
- [ ] 不適用 - 此 PR 無用戶可見變更

## 設計系統檢查 (Design System Checklist)

如果此 PR 包含 UI 元件變更，請確認：

- [ ] 我已檢查 `@morningai/shared-ui` 是否有可用的元件
- [ ] 如果需要新元件，我已將其加入 `packages/shared-ui/` 而非應用層
- [ ] 新元件已加入 Storybook story（位於 `packages/shared-ui/src/components/**/*.stories.tsx`）
- [ ] 我沒有在應用層重複實作已存在於 shared-ui 的元件
- [ ] 如使用設計 tokens，我已從 `@morningai/shared-ui` 匯入而非硬編碼
- [ ] 不適用 - 此 PR 不包含 UI 元件變更

### Apple 組件檢查（如適用）

如果此 PR 包含 Apple 風格組件變更，請確認：

- [ ] 組件消費 `tokens.json` 的 CSS 變數（不使用平行色彩系統）
- [ ] 若為視覺原語（純視覺、無業務邏輯），已放在 `@morningai/shared-ui`
- [ ] 若為應用層 adapter，已正確包裝 shared-ui 組件
- [ ] 已加入完整的 stories + tests + a11y tests
- [ ] 已支援 `prefers-reduced-motion`（動畫組件）
- [ ] 不適用 - 此 PR 不包含 Apple 組件變更

**相關文件**: [設計系統治理規則](../../CONTRIBUTING_DESIGN_SYSTEM.md#apple-組件規則)

## Shared-UI Import 合規性（強制 - Stage 3: 完全強制執行）

<!-- 此檢查會阻擋 PR 合併。違規的 PR 無法合併，直到問題解決。 -->

**必須符合的要求**：

- [ ] 我已使用 `@morningai/shared-ui` 元件，而非直接 import `@radix-ui/react-*`、`@mui/*` 等 UI 元件庫
- [ ] 我沒有直接 import `@headlessui/*` 或 `@chakra-ui/*`
- [ ] 如果使用第三方庫，僅限於允許的例外：
  - lucide-react（圖示）
  - recharts（圖表）
  - date-fns（日期處理）
- [ ] ESLint `no-restricted-imports` 規則通過（無 UI 元件庫 import 警告）
- [ ] CI 的 "Audit UI Library Imports" 檢查通過（必須通過才能合併）
- [ ] 不適用 - 此 PR 不包含 UI import 變更

**緊急情況處理**：
如果您有合法的緊急情況需要繞過此檢查，請參考 [Emergency Override Runbook](../../docs/EMERGENCY_OVERRIDE_RUNBOOK.md)。

**注意**：沒有自動繞過機制。所有例外都需要明確的管理員批准和記錄。

**相關文件**:
- [快速修復指南（2 分鐘）](../../docs/DESIGN_SYSTEM_QUICKSTART.md)
- [設計系統強制執行指南](../../docs/DESIGN_SYSTEM_ENFORCEMENT.md)
- [i18n 政策](../../CONTRIBUTING.md#i18n-政策強制執行)
- Storybook: `pnpm --filter frontend-dashboard storybook`

## 程式碼品質檢查

- [ ] ESLint 通過（0 warnings）：`pnpm lint`
- [ ] TypeScript 類型檢查通過：`pnpm typecheck`
- [ ] 無 `any` 類型（使用適當的類型定義）
- [ ] 所有測試通過：`pnpm test`
- [ ] 程式碼遵循現有模式和慣例

## 文檔更新檢查清單 (Documentation Updates)

如果此 PR 包含以下類型的變更，請確認相關文檔已更新：

- [ ] **新增基礎設施/工具** (Storybook, VRT, CI jobs 等) → 更新 `ONBOARDING_GUIDE.md` 和 `PROJECT_STRUCTURE_REPORT.md`
- [ ] **新增/修改環境變數** → 更新 `config/env.schema.yaml` 和 `docs/ENVIRONMENTS.md`
- [ ] **新增功能/API 端點** → 更新 `ONBOARDING_GUIDE.md` 或相關 API 文檔
- [ ] **修改部署流程** → 更新 `docs/deployment/` 相關文件
- [ ] **架構變更** → 更新 `PROJECT_STRUCTURE_REPORT.md` 和相關 ADR
- [ ] **新增/修改 GitHub Actions workflow** → 更新 `docs/ci_matrix.md` 相關章節，並在 workflow 文件頂部添加文檔引用註釋
- [ ] 不適用 - 此 PR 不需要文檔更新

**重要**: 文檔是單一真實來源。請確保：
- `config/env.schema.yaml` 是所有環境變數的 SSOT
- `ENVIRONMENTS.md` 反映所有環境變數變更
- `ONBOARDING_GUIDE.md` 包含新開發者需要的所有設置步驟

## 提醒
- [ ] 不修改 OpenAPI/資料欄位（若要改，先提 RFC）
- [ ] 設計 PR 僅含 UI/文案/樣式；工程 PR 僅含 API/邏輯
- [ ] 避免使用已廢棄的目錄（如 `tools/frontend-lab`）
- [ ] 不在 src/** 中導入已廢棄的模組（如 `utils.preauth_token`，請使用 `utils.pre_auth_token`）
- [ ] 所有環境變數已在 `config/env.schema.yaml` 中定義
