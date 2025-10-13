# Agent MVP 閉環驗證報告 (Issue #54)

**日期**: 2025-10-13  
**驗證範圍**: FAQ → PR → CI → Auto-merge → Deploy  
**狀態**: ⚠️ 部分功能異常

---

## 執行摘要

Agent MVP 閉環流程中發現 **Auto-merge 階段未正常運作**，導致 FAQ PR 需要手動合併。

### 驗證結果

| 階段 | 狀態 | 說明 |
|------|------|------|
| **Phase 1: FAQ → PR** | ✅ 正常 | Orchestrator 成功建立 PR，trace-id 正確傳播 |
| **Phase 2: PR → CI** | ✅ 正常 | CI workflows 觸發並通過（12 checks passed） |
| **Phase 3: CI → Auto-merge** | ❌ **異常** | auto-merge-faq workflow 被跳過 (skipped) |
| **Phase 4: Auto-merge → Deploy** | ⚠️ 無法驗證 | Phase 3 失敗導致無法驗證 |

---

## 問題分析

### 1. Auto-merge Workflow 狀態

**工作流檔案**: `.github/workflows/auto-merge-faq.yml`

**最近 10 次執行記錄**:
```json
{
  "conclusion": "skipped",
  "event": "check_suite",
  "headBranch": "main",
  "status": "completed"
}
```

**問題**: 所有執行都是 `check_suite` 事件觸發，發生在 PR 合併到 main **之後**，此時已經太遲。

### 2. 觸發條件分析

```yaml
on:
  workflow_dispatch:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'docs/FAQ.md'
  check_suite:
    types: [completed]

jobs:
  auto-merge:
    if: github.event.pull_request.user.login == 'github-actions[bot]' || contains(github.event.pull_request.title, 'trace-id')
```

**根本原因**:
- Workflow 有 `pull_request` 觸發器，但實際上只看到 `check_suite` 事件
- 當由 `check_suite` 觸發時，`github.event.pull_request` 為 `null`
- 導致 if 條件評估失敗，workflow 被跳過

### 3. 實際 FAQ PR 案例

**PR #240**: "docs: Update FAQ (trace-id: 76b42fd4)"
- **建立者**: RC918 (非 github-actions[bot])
- **標題**: 包含 "trace-id" ✅
- **檔案變更**: docs/FAQ.md ✅
- **CI 狀態**: 12 checks passed ✅
- **Auto-merge**: ❌ Workflow 被跳過

**Git 提交記錄**:
```bash
c0a9ae0d docs: add FAQ.md (trace-id: 76b42fd4-f620-4f82-bfaa-e641fc0df083) (#240)
```

### 4. graph.py 自動合併嘗試

**檔案**: `handoff/20250928/40_App/orchestrator/graph.py:57-64`

```python
try:
    import subprocess
    subprocess.run([
        "gh", "pr", "merge", str(pr_num),
        "--auto", "--squash",
        "--repo", repo_full
    ], check=False)
except Exception as e:
    print(f"[GitHub] Could not enable auto-merge: {e}")
```

**發現**: Orchestrator 確實嘗試啟用 auto-merge，但：
1. 使用的是 `gh pr merge --auto`（GitHub CLI auto-merge 功能）
2. 這與 GitHub Actions workflow 的 auto-merge 是不同機制
3. 可能因權限問題未成功啟用

---

## 可能的原因

### A. pull_request 事件未觸發

**假設**: Workflow 的 `paths: ['docs/FAQ.md']` 過濾器阻止了觸發

**驗證需要**:
- 檢查 PR #240 是否實際修改了 docs/FAQ.md
- 查看 GitHub Actions 日誌確認是否有 pull_request 事件

### B. 權限問題

**假設**: `GITHUB_TOKEN` 權限不足以觸發 pull_request 事件的 workflows

**當前權限**:
```yaml
permissions:
  pull-requests: write
  contents: write
```

**RFC 要求**:
```yaml
permissions:
  contents: write        # 建立分支、提交文件
  pull-requests: write   # 建立和合併 PR
  actions: read          # 讀取 workflow 狀態
  checks: read           # 讀取 CI 檢查結果
```

**缺少**: `actions: read`, `checks: read`

### C. 建立者身份問題

**當前**: PR 由 RC918 建立（使用 GITHUB_TOKEN）  
**RFC 設計**: 預期由 github-actions[bot] 建立

**Impact**: 第一個 if 條件失敗，但第二個條件（trace-id）應該成功

---

## 建議修復方案

### 選項 1: 修復 pull_request 事件觸發（推薦）

**問題**: 為什麼 pull_request 事件沒有觸發 workflow？

**行動**:
1. 手動建立測試 FAQ PR 驗證觸發條件
2. 檢查 GitHub Actions 設定是否啟用 pull_request workflows
3. 驗證 paths 過濾器是否正確

### 選項 2: 調整 check_suite 觸發邏輯

```yaml
jobs:
  auto-merge:
    if: |
      (github.event_name == 'pull_request' && 
       (github.event.pull_request.user.login == 'github-actions[bot]' || 
        contains(github.event.pull_request.title, 'trace-id'))) ||
      (github.event_name == 'check_suite' &&
       github.event.check_suite.conclusion == 'success' &&
       github.event.check_suite.pull_requests[0].title contains 'trace-id')
```

**缺點**: 更複雜，可能不可靠

### 選項 3: 依賴 graph.py 的 `gh pr merge --auto`

**當前狀態**: 已實作但未驗證是否成功

**行動**:
1. 檢查 GITHUB_TOKEN 是否有足夠權限啟用 auto-merge
2. 在 Worker 日誌中查看是否有錯誤訊息
3. 手動測試 `gh pr merge --auto` 命令

---

## 下一步驗證計畫

### 1. 手動觸發測試
```bash
# 觸發 workflow
gh workflow run auto-merge-faq.yml

# 查看執行結果
gh run list --workflow=auto-merge-faq.yml --limit 1
gh run view <run_id>
```

### 2. 建立測試 FAQ PR
```bash
# 透過 API 建立測試 FAQ 任務
curl -X POST http://localhost:5000/api/agent/faq \
  -H "Content-Type: application/json" \
  -d '{"question": "Test auto-merge workflow verification"}'

# 監控 PR 建立和 auto-merge workflow 觸發
```

### 3. 檢查既有 PR 的 Actions 日誌
```bash
# 查看 PR #240 的 workflow runs
gh pr view 240 --json url
# 在 GitHub UI 查看 "Checks" tab
```

---

## RFC 合規性檢查

**RFC 目標**: TTE ≤ 60 秒, 成功率 ≥ 99%

| RFC 需求 | 實作狀態 | 備註 |
|---------|---------|------|
| API 請求返回 202 + task_id | ✅ | agent.py 已實作 |
| Redis 入隊與追蹤 | ✅ | RQ worker 正常運作 |
| trace_id 傳播 | ✅ | 在 commit、PR、Redis 都有 |
| PR 自動建立 | ✅ | graph.py execute() 成功 |
| PR 包含 trace_id | ✅ | 在 title 和 body |
| CI 自動觸發 | ✅ | 12 workflows 正常執行 |
| **Auto-merge 執行** | ❌ | **Workflow 被跳過** |
| Post-deploy 驗證 | ⚠️ | 無法驗證（需 auto-merge） |

**成功率**: 目前 0%（需手動合併）  
**TTE**: 無法達成目標（需人工介入）

---

## 結論

Agent MVP 閉環流程在 **Auto-merge 階段** 中斷，需要修復 auto-merge-faq workflow 的觸發機制。推薦採用「選項 1」進行深入調查，確認為何 pull_request 事件未觸發 workflow。

**優先級**: P0（阻擋 Issue #54 完成）  
**影響範圍**: 所有 FAQ 任務需要手動合併  
**預估修復時間**: 1-2 小時（調查 + 測試 + 驗證）
