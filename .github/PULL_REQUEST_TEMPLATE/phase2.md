## Phase 2 PR - Design System Card Migration

<!-- 
此模板專用於 Phase 2 設計系統遷移 PR。
如果您的 PR 不是 Phase 2 遷移的一部分，請使用預設模板。

選擇此模板的方式：
- 建立 PR 時在 URL 加上 ?template=phase2.md
- 或從 GitHub 的模板選擇器中選擇
-->

**Phase**: 2-X (e.g., 2-1a, 2-2b)
**Target Page/Component**: [Page or component name]
**Epic**: #2304

---

## 描述 (Description)

<!-- 簡要說明此 PR 遷移的內容 -->

### Changes Summary

- [ ] Migrated `[LegacyCard]` to `[SharedUICard]`
- [ ] Updated imports to use `@morningai/shared-ui`
- [ ] Removed legacy card component (if applicable)

## PR 類型與優先級 (PR Type & Priority)

- [ ] **P0 - 主線功能 / 緊急修復 (Blocking)**
- [x] **P1 - 修正既有問題 / 改善體驗 (Non-blocking)** - Phase 2 遷移
- [ ] **P2 - 優化 / 重構 / 技術債 (Nice-to-have)**

## 本 PR 不處理 (Out of Scope)

<!-- 明確列出此 PR 不會處理的項目 -->

- [此處列出不處理的項目，若無則刪除此行]

---

## Audit Delta Report

### Before

```bash
# 執行 audit 腳本取得 baseline
./scripts/phase2_audit.sh --file [target_file]
# 或執行整體 audit
./scripts/phase2_audit.sh
```

| Metric | Value |
|--------|-------|
| Shared-UI Cards | X |
| Legacy Cards | X |
| Unknown Cards | X |
| Adoption | X% |
| Raw Hex | X |
| Inline Styles | X |

### After

| Metric | Value |
|--------|-------|
| Shared-UI Cards | X |
| Legacy Cards | X |
| Unknown Cards | X |
| Adoption | X% |
| Raw Hex | X |
| Inline Styles | X |

### Delta Summary

| Metric | Before | After | Delta | Status |
|--------|--------|-------|-------|--------|
| Shared-UI Cards | X | X | +X | PASS |
| Legacy Cards | X | X | -X | PASS |
| Raw Hex | X | X | 0 | PASS |
| Inline Styles | X | X | 0 | PASS |

<details>
<summary>範例填寫（可刪除）</summary>

**Before**:
```
=== File: src/components/2fa/TwoFAStatusCard.jsx ===
Shared-UI Cards: 0
Legacy Cards: 1 (TwoFAStatusCard)
Unknown Cards: 0
Adoption: 0%
Raw Hex: 2
Inline Styles: 1
```

**After**:
```
=== File: src/components/2fa/TwoFAStatusCard.jsx ===
Shared-UI Cards: 4 (SettingsCard)
Legacy Cards: 0
Unknown Cards: 0
Adoption: 100%
Raw Hex: 0
Inline Styles: 0
```

**Delta Summary**:
| Metric | Before | After | Delta | Status |
|--------|--------|-------|-------|--------|
| Shared-UI Cards | 0 | 4 | +4 | PASS |
| Legacy Cards | 1 | 0 | -1 | PASS |
| Raw Hex | 2 | 0 | -2 | PASS |
| Inline Styles | 1 | 0 | -1 | PASS |

</details>

---

## Bundle Size Report

### Before (from baseline or main branch)

```bash
./scripts/measure-bundle-size.sh
```

| App | Total JS (gzip) | Total CSS (gzip) | Largest Chunk |
|-----|-----------------|------------------|---------------|
| owner-console | X kB | X kB | X kB |
| frontend-dashboard | X kB | X kB | X kB |

### After

| App | Total JS (gzip) | Total CSS (gzip) | Largest Chunk |
|-----|-----------------|------------------|---------------|
| owner-console | X kB | X kB | X kB |
| frontend-dashboard | X kB | X kB | X kB |

### Delta

| Metric | Delta | Threshold | Status |
|--------|-------|-----------|--------|
| Total JS | +X kB | +50 kB | PASS/FAIL |
| Total CSS | +X kB | +10 kB | PASS/FAIL |
| Largest Chunk | +X kB | +30 kB | PASS/FAIL |

---

## 如何測試 (How to Test)

### 測試類型 (Test Types)

- [ ] 單元測試 (Unit Tests) - `pnpm test`
- [ ] 整合測試 (Integration Tests)
- [ ] E2E 測試 (End-to-End Tests) - Playwright
- [ ] 視覺回歸測試 (Visual Regression Tests) - VRT
- [ ] 手動測試 (Manual Testing)
- [ ] 無障礙測試 (Accessibility Testing)

### 測試步驟 (Test Steps)

1. 
2. 
3. 

### 測試環境 (Test Environment)

- [ ] 本地開發環境 (Local Development)
- [ ] CI/CD Pipeline
- [ ] Vercel Preview

---

## Manual Verification Checklist

### Functional Verification

- [ ] **No console errors**: Browser console shows no new errors
- [ ] **No network errors**: Network tab shows no failed requests
- [ ] **User flow works**: Completed the following steps:
  1. [ ] Step 1: [Describe action and expected result]
  2. [ ] Step 2: [Describe action and expected result]
  3. [ ] Step 3: [Describe action and expected result]
- [ ] **Permission check**: Verified behavior for:
  - [ ] Admin user
  - [ ] Non-admin user (if applicable)
- [ ] **No security issues**: No `dangerousSetInnerHTML` or unescaped user input
- [ ] **API contract unchanged**: No changes to API request/response format

### Performance Verification

- [ ] **Bundle size within threshold**: See Bundle Size Report above
- [ ] **List virtualization preserved**: Long lists still use virtualization/pagination
- [ ] **No unnecessary re-renders**: React DevTools shows expected render count

### Accessibility (a11y) Verification

- [ ] **Keyboard navigation**: Tab order is logical and complete
- [ ] **Focus ring visible**: Focus indicator is clearly visible on all interactive elements
- [ ] **aria-label/role correct**: Screen reader announces elements correctly
- [ ] **Modal focus trap**: Modal/dialog traps focus correctly (if applicable)
- [ ] **Color contrast**: Text meets WCAG AA contrast requirements

### Visual Verification

- [ ] **Vercel Preview URL**: [Insert URL]
- [ ] **Visual comparison**: Before/after screenshots attached below
- [ ] **Responsive check**: Verified on:
  - [ ] Desktop (1920x1080)
  - [ ] Tablet (1024x768) (if applicable)
  - [ ] Mobile (375x812) (if applicable)

---

## Visual Evidence

### Before

![Before - Default State](path/to/before-default.png)
<!-- Screenshot naming: {phase}-{pr}-{page}-before-{viewport}.png -->
<!-- Example: 2-1a-settings2fa-before-desktop.png -->

### After

![After - Default State](path/to/after-default.png)
<!-- Screenshot naming: {phase}-{pr}-{page}-after-{viewport}.png -->
<!-- Example: 2-1a-settings2fa-after-desktop.png -->

### State Screenshots (if applicable)

| State | Before | After |
|-------|--------|-------|
| Default | [screenshot] | [screenshot] |
| Hover | [screenshot] | [screenshot] |
| Focus | [screenshot] | [screenshot] |
| Loading | [screenshot] | [screenshot] |
| Error | [screenshot] | [screenshot] |

---

## i18n 檢查清單（強制）

- [ ] 所有用戶可見字串使用 `t()` 或 `<Trans>`（無硬編碼字串）
- [ ] 新 translation keys 已加入 `en-US.json` 和 `zh-TW.json`
- [ ] Translation keys 使用適當的命名空間
- [ ] 無障礙屬性已翻譯
- [ ] ESLint i18n 規則通過
- [ ] 不適用 - 此 PR 無用戶可見變更

## 設計系統檢查 (Design System Checklist)

- [ ] 我已檢查 `@morningai/shared-ui` 是否有可用的元件
- [ ] 如果需要新元件，我已將其加入 `packages/shared-ui/` 而非應用層
- [ ] 新元件已加入 Storybook story
- [ ] 我沒有在應用層重複實作已存在於 shared-ui 的元件
- [ ] 如使用設計 tokens，我已從 `@morningai/shared-ui` 匯入而非硬編碼

## Shared-UI Import 合規性（強制）

- [ ] 我已使用 `@morningai/shared-ui` 元件，而非直接 import UI 元件庫
- [ ] ESLint `no-restricted-imports` 規則通過
- [ ] CI 的 "Audit UI Library Imports" 檢查通過

---

## Interim QA Exit Criteria (for Phase 2-1d completion)

> This section is only required for the final PR of each Phase 2 sub-phase

- [ ] All Phase 2-X pages pass keyboard navigation test
- [ ] All Phase 2-X pages pass focus ring visibility test
- [ ] All Phase 2-X pages pass main interaction flow test
- [ ] Vercel preview visual comparison passes for all Phase 2-X pages
- [ ] No new raw hex colors introduced (delta = 0 or negative)
- [ ] No new inline styles introduced (delta = 0 or negative)
- [ ] Shared-UI adoption >= 80% for all Phase 2-X pages
- [ ] Bundle size within thresholds
- [ ] No console errors on any Phase 2-X page
- [ ] No network errors on any Phase 2-X page
- [ ] Permission-based views verified (admin vs non-admin)

---

## 程式碼品質檢查

- [ ] ESLint 通過（0 warnings）：`pnpm lint`
- [ ] TypeScript 類型檢查通過：`pnpm typecheck`
- [ ] 無 `any` 類型（使用適當的類型定義）
- [ ] 所有測試通過：`pnpm test`

## 文檔更新檢查清單

- [ ] **新增/修改 GitHub Actions workflow** → 更新 `docs/ci_matrix.md`
- [ ] **架構變更** → 更新 `PROJECT_STRUCTURE_REPORT.md`
- [ ] 不適用 - 此 PR 不需要文檔更新

---

## Related Issues

- Epic: #2304
- Phase 2-X Issue: #XXXX (if applicable)

---

## Reviewer Notes

<!-- Any additional context for reviewers -->
