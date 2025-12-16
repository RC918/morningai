<!--
================================================================================
HOTFIX PR TEMPLATE - 緊急修復專用模板
================================================================================

適用時機 (When to Use):
- 生產環境緊急修復（P0 優先級）
- 需要快速修復並部署的問題
- 影響用戶的關鍵 bug 修復

如何選擇此模板 (How to Select):
- 方法 1: 在 PR URL 後加上 ?template=hotfix.md
  例如: https://github.com/RC918/morningai/compare/main...your-branch?template=hotfix.md
- 方法 2: 從 GitHub 的模板選擇器中選擇 "hotfix"

注意事項 (Important Notes):
- 此模板簡化了檢查清單，專注於快速修復
- 必須填寫問題描述、修復方案和 Rollback Plan
- 建議建立 follow-up issue 進行完整修復（如這是臨時修復）
- 如果不是緊急修復，請使用預設模板

其他模板:
- 一般 PR: 預設模板（不加參數）
- Phase 2 遷移: ?template=phase2.md

文檔參考: CONTRIBUTING.md#pr-template-選擇
================================================================================
-->

## Hotfix PR

**Priority**: P0 - 緊急修復
**Affected Environment**: Production / Staging / Both
**Incident Link**: [Link to incident report if applicable]

---

## 問題描述 (Problem Description)

<!-- 簡要說明需要緊急修復的問題 -->

### 影響範圍 (Impact)

- **受影響用戶數**: 
- **業務影響**: 
- **發現時間**: 

## 修復方案 (Fix Description)

<!-- 說明修復的方式和原因 -->

## 根本原因 (Root Cause)

<!-- 簡要說明問題的根本原因（如已知） -->

---

## 測試驗證 (Testing)

### 快速驗證步驟

1. [ ] 
2. [ ] 
3. [ ] 

### 驗證環境

- [ ] 本地環境已驗證
- [ ] Staging 環境已驗證（如適用）

---

## Rollback Plan

<!-- 如果修復失敗，如何回滾？ -->

- [ ] 回滾步驟已記錄
- [ ] 回滾已測試（如適用）

---

## Checklist

- [ ] 修復已在本地測試
- [ ] 不會引入新的 breaking changes
- [ ] 已通知相關團隊成員
- [ ] 已建立 follow-up issue 進行完整修復（如這是臨時修復）

## Follow-up

<!-- 列出需要後續處理的事項 -->

- [ ] Follow-up Issue: #XXXX

---

## 審核者注意事項 (Reviewer Notes)

<!-- 任何審核者需要知道的額外資訊 -->
