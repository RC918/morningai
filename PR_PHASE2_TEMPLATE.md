# Phase 2 PR Template - Design System Card Migration

> ⚠️ **DEPRECATED / 已棄用**
>
> 此檔案已被 `.github/PULL_REQUEST_TEMPLATE/phase2.md` 取代。
> 請使用新的多模板機制建立 Phase 2 PR：
>
> **如何使用新模板：**
> - 在 PR URL 後加上 `?template=phase2.md`
> - 例如：`https://github.com/RC918/morningai/compare/main...your-branch?template=phase2.md`
>
> **新模板位置：** [.github/PULL_REQUEST_TEMPLATE/phase2.md](.github/PULL_REQUEST_TEMPLATE/phase2.md)
>
> 此檔案將在 Issue #2564 中移除。保留此檔案僅供參考歷史記錄。

---

## PR Information

**Phase**: 2-X (e.g., 2-1a, 2-2b)
**Target Page/Component**: [Page or component name]
**Epic**: #2304

---

## Description

[Brief description of what this PR migrates]

### Changes Summary

- [ ] Migrated `[LegacyCard]` to `[SharedUICard]`
- [ ] Updated imports to use `@morningai/shared-ui`
- [ ] Removed legacy card component (if applicable)

---

## Audit Delta

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
<summary>📋 範例填寫（可刪除）</summary>

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

| App | Total JS (gzip) | Total CSS (gzip) | Largest Chunk |
|-----|-----------------|------------------|---------------|
| owner-console | X kB | X kB | X kB |

### After

| App | Total JS (gzip) | Total CSS (gzip) | Largest Chunk |
|-----|-----------------|------------------|---------------|
| owner-console | X kB | X kB | X kB |

### Delta

| Metric | Delta | Threshold | Status |
|--------|-------|-----------|--------|
| Total JS | +X kB | +50 kB | PASS/FAIL |
| Total CSS | +X kB | +10 kB | PASS/FAIL |
| Largest Chunk | +X kB | +30 kB | PASS/FAIL |

---

## Manual Verification Checklist

### Functional Verification

- [ ] **No console errors**: Browser console shows no new errors
- [ ] **No network errors**: Network tab shows no failed requests
- [ ] **User flow works**: Completed the following steps:
  1. [ ] Step 1: [Describe action and expected result]
  2. [ ] Step 2: [Describe action and expected result]
  3. [ ] Step 3: [Describe action and expected result]
  4. [ ] Step 4: [Describe action and expected result] (optional)
  5. [ ] Step 5: [Describe action and expected result] (optional)
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
| Active | [screenshot] | [screenshot] |
| Loading | [screenshot] | [screenshot] |
| Error | [screenshot] | [screenshot] |
| Empty | [screenshot] | [screenshot] |

---

## Interim QA Exit Criteria (for Phase 2-1d completion)

> This section is only required for the final PR of Phase 2-1 (PR 2-1d)

- [ ] All Phase 2-1 pages pass keyboard navigation test
- [ ] All Phase 2-1 pages pass focus ring visibility test
- [ ] All Phase 2-1 pages pass main interaction flow test
- [ ] Vercel preview visual comparison passes for all Phase 2-1 pages
- [ ] No new raw hex colors introduced (delta = 0 or negative)
- [ ] No new inline styles introduced (delta = 0 or negative)
- [ ] Shared-UI adoption >= 80% for all Phase 2-1 pages
- [ ] Bundle size within thresholds
- [ ] No console errors on any Phase 2-1 page
- [ ] No network errors on any Phase 2-1 page
- [ ] Permission-based views verified (admin vs non-admin)

---

## Reviewer Notes

[Any additional context for reviewers]

---

## Related Issues

- Epic: #2304
- Phase 2-X Issue: #XXXX (if applicable)

---

**Link to Devin run**: [URL]
**Requested by**: [Name] / @[GitHub username]
