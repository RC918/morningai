# Emergency Override Runbook

> **警告**：此流程僅用於真正的緊急情況。濫用將削弱設計系統的完整性。

## 前提條件

在使用此緊急繞過流程之前，必須滿足以下條件：

1. **合法的業務緊急需求**
   - 生產環境重大 bug 需要立即修復
   - 時間敏感的業務需求（如客戶演示、重要發布）
   - 阻擋其他關鍵工作的依賴問題

2. **必須由 @RC918 批准**
   - 在 PR 中明確說明緊急原因
   - 獲得 @RC918 的明確書面批准（PR 評論）

3. **承諾後續修復**
   - 同意在 7 天內修復違規
   - 指派負責人追蹤修復

## 緊急繞過流程

### Step 1: 申請批准

在 PR 中標記 @RC918 並說明：
```markdown
@RC918 緊急繞過申請

**緊急原因**：[詳細說明為什麼需要立即合併]

**業務影響**：[說明如果不立即合併會有什麼影響]

**違規內容**：[列出具體的設計系統違規]

**修復計劃**：[說明何時以及如何修復違規]

**承諾期限**：7 天內修復
```

等待 @RC918 的明確批准評論。

### Step 2: 臨時移除檢查

**僅在獲得批准後執行**：

1. 前往 Branch Protection 設定：
   ```
   https://github.com/RC918/morningai/settings/branches
   ```

2. 找到 `main` 分支保護規則，點擊 "Edit"

3. 在 "Require status checks to pass before merging" 區域：
   - 找到 "Audit UI Library Imports" 檢查
   - **暫時取消勾選**
   - 記錄當前時間和操作者

4. 點擊 "Save changes"

5. **立即截圖保存**當前設定狀態（用於審計）

### Step 3: 合併 PR

1. 立即合併緊急 PR

2. 在 PR 中留言記錄：
   ```markdown
   ✅ 緊急合併完成
   
   - 合併時間：[時間]
   - 操作者：[姓名]
   - 批准者：@RC918
   - Branch protection 臨時移除：Audit UI Library Imports
   ```

### Step 4: 立即復原 Branch Protection

**關鍵**：合併後**立即**復原設定，不要延遲！

1. 返回 Branch Protection 設定：
   ```
   https://github.com/RC918/morningai/settings/branches
   ```

2. 編輯 `main` 分支保護規則

3. **重新勾選** "Audit UI Library Imports"

4. 點擊 "Save changes"

5. 驗證設定已復原（截圖保存）

### Step 5: 建立 Follow-up Issue

立即建立追蹤 issue：

**標題**：
```
[Tech Debt] Fix design system violation in PR #XXXX
```

**內容**：
```markdown
## 背景

PR #XXXX 因緊急業務需求使用了緊急繞過流程合併，包含以下設計系統違規：

[列出具體違規]

## 違規詳情

- **檔案**：[違規檔案路徑]
- **違規類型**：[直接 import @radix-ui / @mui / 等]
- **原 PR**：#XXXX
- **緊急合併時間**：[時間]
- **批准者**：@RC918

## 修復要求

必須在 **7 天內**（截止日期：[日期]）完成以下修復：

1. 將違規的 UI 元件遷移到 `@morningai/shared-ui`
2. 如果 shared-ui 缺少對應元件，先在 shared-ui 中實作
3. 更新所有 import 語句
4. 確保通過 `./scripts/audit-shared-ui-imports.sh` 檢查
5. 確保通過所有 CI 檢查

## 驗收標準

- [ ] 所有違規檔案已修復
- [ ] `./scripts/audit-shared-ui-imports.sh` 返回 0 違規
- [ ] CI "Audit UI Library Imports" 檢查通過
- [ ] PR 已合併到 main

## 指派

- **負責人**：[原 PR 作者]
- **審核者**：@RC918
- **截止日期**：[7 天後的日期]

## 參考資料

- 快速修復指南：`docs/DESIGN_SYSTEM_QUICKSTART.md`
- 完整文檔：`docs/DESIGN_SYSTEM_ENFORCEMENT.md`
- Shared-UI README：`packages/shared-ui/README.md`
```

**標籤**：
- `tech-debt`
- `design-system`
- `priority:high`

**指派**：原 PR 作者

**Milestone**：設定 7 天後的截止日期

## 審計與追蹤

### 記錄要求

每次使用緊急繞過流程，必須記錄：

1. **PR 評論**：完整的批准和執行記錄
2. **Branch Protection 截圖**：移除前、移除後、復原後
3. **Follow-up Issue**：追蹤修復進度
4. **時間記錄**：每個步驟的執行時間

### 月度審查

每月審查緊急繞過使用情況：

1. 統計使用次數
2. 分析緊急原因
3. 評估是否有濫用
4. 檢查修復完成率
5. 識別流程改進機會

### 警告指標

如果出現以下情況，需要重新評估流程：

- 🚨 單月使用超過 3 次
- 🚨 同一團隊/個人重複使用
- 🚨 修復超過 7 天期限
- 🚨 緊急原因不充分
- 🚨 Branch protection 未及時復原

## 常見問題

### Q: 什麼情況下可以使用緊急繞過？

**A**: 僅限真正的緊急情況：
- ✅ 生產環境重大 bug 需要立即修復
- ✅ 時間敏感的客戶演示或發布
- ❌ 開發者方便（不是緊急情況）
- ❌ 不想修復違規（不是緊急情況）
- ❌ 趕截止日期（應該提前規劃）

### Q: 如果 @RC918 不在線怎麼辦？

**A**: 等待批准。如果真的是緊急情況，通過其他渠道聯繫（Slack、電話）。不要在沒有批准的情況下使用此流程。

### Q: 可以延長 7 天修復期限嗎？

**A**: 特殊情況下可以，但必須：
1. 在 follow-up issue 中說明原因
2. 獲得 @RC918 批准
3. 設定新的明確截止日期
4. 不應該成為常態

### Q: 如果忘記復原 branch protection 怎麼辦？

**A**: 立即復原！這是嚴重的安全問題。如果發現 branch protection 未復原：
1. 立即復原設定
2. 在 Slack 通知團隊
3. 檢查期間是否有其他 PR 合併
4. 記錄事件並改進流程

### Q: 可以為多個 PR 同時使用緊急繞過嗎？

**A**: 不建議。每個 PR 應該單獨評估和批准。如果有多個緊急 PR，考慮：
1. 是否可以合併為一個 PR
2. 是否真的都是緊急情況
3. 是否需要重新評估優先級

## 替代方案

在使用緊急繞過之前，考慮這些替代方案：

### 方案 1: 快速修復違規（推薦）

通常修復設計系統違規只需要 5-15 分鐘：
```bash
# 1. 檢查 shared-ui 是否有對應元件
ls packages/shared-ui/src/components/ui/

# 2. 更新 import
# 從：import { Button } from '@radix-ui/react-button'
# 到：import { Button } from '@morningai/shared-ui'

# 3. 驗證
./scripts/audit-shared-ui-imports.sh
```

參考：`docs/DESIGN_SYSTEM_QUICKSTART.md`

### 方案 2: 拆分 PR

將違規部分拆分到單獨的 PR：
1. PR A：不含違規的緊急修復（立即合併）
2. PR B：含違規的部分（修復後合併）

### 方案 3: 快速添加到 shared-ui

如果 shared-ui 缺少元件，快速添加：
```bash
# 1. 在 shared-ui 中實作元件（10-20 分鐘）
# 2. 更新應用中的 import
# 3. 一起合併
```

## 聯絡資訊

- **批准者**：@RC918 (Ryan Chen)
- **Slack 頻道**：#design-system
- **緊急聯絡**：[緊急情況下的聯絡方式]

---

**最後更新**：2025-11-22  
**維護者**：@RC918 (Ryan Chen)  
**版本**：1.0.0

**記住**：緊急繞過是最後手段。優先考慮快速修復違規或拆分 PR。
