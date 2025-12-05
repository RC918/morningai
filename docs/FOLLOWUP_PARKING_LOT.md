# Follow-up Parking Lot 流程

本文件說明如何管理 PR review 過程中產生的 follow-up 項目，避免 PR scope creep 和 follow-up 爆炸問題。

## 背景

在 code review 過程中，reviewer 經常會發現額外的改進機會或相關問題。如果這些項目都加入當前 PR，會導致：

1. PR scope 無限擴大，難以 review
2. 合併時間延長，阻擋其他工作
3. 風險增加，因為變更範圍過大

## Follow-up Parking Lot 機制

### 什麼是 Parking Lot？

Parking Lot 是一個暫存區，用於記錄 review 過程中發現但不應在當前 PR 處理的項目。這些項目會被追蹤為獨立的 issues 或 PRs，在當前 PR 合併後處理。

### 何時使用 Parking Lot？

當 reviewer 提出的建議符合以下條件時，應該放入 Parking Lot：

| 條件 | 放入 Parking Lot | 在當前 PR 處理 |
|------|-----------------|---------------|
| 與 PR 核心目標無關 | O | |
| 需要大量額外變更 | O | |
| 涉及其他模組/檔案 | O | |
| 是「nice to have」優化 | O | |
| 是阻擋性 bug 或安全問題 | | O |
| 是簡單的 typo 或格式修正 | | O |
| 會導致 PR 無法正常運作 | | O |

### 流程

#### 1. 識別 Follow-up 項目

在 review 過程中，當發現不應在當前 PR 處理的項目時：

```markdown
<!-- 在 PR comment 中標記 -->
[PARKING LOT] 這個建議很好，但超出當前 PR scope。建議建立 follow-up issue。
```

#### 2. 記錄到 PR Description

在 PR 的「本 PR 不處理 (Out of Scope)」區塊中記錄：

```markdown
## 本 PR 不處理 (Out of Scope)

- 重構 `UserService` 以支援批次操作（建議 follow-up: #1234）
- 新增 unit tests 覆蓋 edge cases
- 更新相關文件
```

#### 3. 建立 Follow-up Issues

對於重要的 Parking Lot 項目，應建立獨立的 GitHub issue：

```markdown
## 標題
[Follow-up] 從 PR #1234 - 重構 UserService 支援批次操作

## 描述
此 issue 源自 PR #1234 的 review 討論。

### 背景
在 review PR #1234 時，@reviewer 建議...

### 建議改進
- [ ] 項目 1
- [ ] 項目 2

### 優先級
P2 - 非阻擋性改進

### 相關連結
- 原始 PR: #1234
- Review comment: [連結]
```

#### 4. 追蹤和處理

建立 follow-up issue 後：

1. 加上適當的 label（`P1`, `P2`, `P3`）
2. 指派給適當的人員（通常是原 PR 作者）
3. 在每週技術債 review 中追蹤進度

## 優先級定義

| 優先級 | 定義 | 處理時間 |
|-------|------|---------|
| P0-urgent | 阻擋性問題，必須在當前 PR 處理 | 立即 |
| P1 | 重要但非阻擋，下一個 sprint 處理 | 1-2 週 |
| P2 | 改進項目，排入 backlog | 2-4 週 |
| P3 | Nice to have，有空再處理 | 視情況 |

## 範例

### 好的 Parking Lot 使用

```markdown
## 本 PR 不處理 (Out of Scope)

- 將 `handleError` 函數提取為共用 utility（已建立 #1235）
- 新增 retry 機制處理 network failures（已建立 #1236）
- 更新 API 文件反映新的 error codes
```

### 不好的做法

```markdown
## 本 PR 不處理 (Out of Scope)

- 修復會導致 production crash 的 bug  <!-- 這應該在當前 PR 處理！ -->
- 所有相關的 unit tests  <!-- 測試應該跟著功能一起提交 -->
```

## 相關文件

- [PR Template](../.github/pull_request_template.md) - PR 模板包含 Out of Scope 區塊
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 貢獻指南
