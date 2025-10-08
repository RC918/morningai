# RFC: Agent MVP 閉環流程設計（FAQ → PR → CI → Auto-merge → Deploy）

**狀態**: Draft  
**作者**: Devin AI  
**日期**: 2025-10-08  
**相關 Issue**: #54  

## 摘要

本 RFC 提出 MorningAI Agent MVP 的全自動閉環流程設計，實現從 FAQ 任務觸發到自動部署的端到端流程，目標在 1 分鐘內完成（TTE ≤ 1 min），並達到 99% 以上的成功率。

## 動機

當前 FAQ 生成流程雖然已具備基本功能，但存在以下問題：

1. **執行時間過長**：E2E 測試允許最多 10 分鐘（120 次輪詢 × 5 秒），實際執行時間不可預測
2. **缺乏自動化監控**：無法追蹤端到端執行時間和成功率
3. **錯誤恢復機制不完善**：部署失敗後無自動回滾機制
4. **追蹤能力有限**：trace_id 雖然存在但未系統性整合到監控體系

本 RFC 旨在建立一個可靠、快速、可監控的全自動閉環流程。

---

## 1. 系統流程圖

### 1.1 整體流程

```
┌─────────────┐
│  API 請求    │  POST /api/agent/faq
│  (公開端點)  │  {"question": "..."}
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (api-backend)                                  │
│  • 驗證請求                                              │
│  • 生成 task_id (UUID, 作為 trace_id)                    │
│  • 檢查 Redis 重複性 (1 小時 TTL)                         │
│  • 入隊到 Redis Queue                                    │
│  • 返回 202 + task_id                                    │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  Redis Queue (Upstash)                                  │
│  • Queue: "orchestrator"                                │
│  • Job: run_orchestrator_task(task_id, question, repo) │
│  • TTL: 600s, Result TTL: 24h                           │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  Worker (orchestrator/redis_queue/worker.py)            │
│  • 監聽 "orchestrator" 隊列                              │
│  • 更新 Redis: status=running                            │
│  • 執行 graph.execute()                                  │
│  • Sentry breadcrumb 記錄每步                            │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  Orchestrator (graph.py)                                │
│  1. 建立 Git 分支: orchestrator/faq-{timestamp}          │
│  2. 生成 FAQ 內容 (OpenAI API)                           │
│  3. Commit + Push 到分支                                 │
│  4. 開啟 PR (含 trace_id 在描述中)                        │
│  5. 返回 pr_url, state, trace_id                        │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  GitHub PR 建立                                          │
│  • Title: "Update FAQ - {question}"                     │
│  • Body: 包含 trace_id, Devin run 連結                   │
│  • Files changed: docs/FAQ.md                           │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  CI Workflows 觸發                                       │
│  • backend-ci/test                                      │
│  • frontend-ci/build                                    │
│  • orchestrator-e2e/run                                 │
│  • openapi-verify/lint                                  │
│  • agent-mvp-smoke/smoke                                │
│  • vercel-deploy/deploy                                 │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼ (所有檢查通過)
┌─────────────────────────────────────────────────────────┐
│  Auto-merge Workflow                                    │
│  • 條件: FAQ.md only + github-actions[bot] or trace-id  │
│  • 執行: gh pr merge --auto --squash                     │
│  • 權限: pull-requests: write, contents: write           │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  部署到生產環境                                           │
│  • Vercel: 前端自動部署                                   │
│  • Render: 後端 auto-deploy on push                      │
│  • Worker: 自動重啟並拉取最新代碼                         │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  Post-deploy 驗證                                        │
│  • Health check: /healthz                               │
│  • Sentry 監控: 無新錯誤                                  │
│  • Worker heartbeat: 正常運行                            │
└─────────────────────────────────────────────────────────┘
```

### 1.2 資料流時序圖

```
User/API  Backend  Redis   Worker  Orchestrator  GitHub  CI  Auto-merge  Deploy
   │         │       │       │          │          │      │       │         │
   │─POST───>│       │       │          │          │      │       │         │
   │         │──入隊─>│       │          │          │      │       │         │
   │<──202──│       │       │          │          │      │       │         │
   │  task_id       │       │          │          │      │       │         │
   │                │       │          │          │      │       │         │
   │                │<──拉取─│          │          │      │       │         │
   │                │       │──執行────>│          │      │       │         │
   │                │       │          │──生成 FAQ─>│      │       │         │
   │                │       │          │<──PR URL──│      │       │         │
   │                │       │<──完成───│          │      │       │         │
   │                │       │          │          │──觸發─>│       │         │
   │                │       │          │          │      │       │         │
   │                │       │          │          │      │<─通過─│         │
   │                │       │          │          │      │       │──合併──>│
   │                │       │          │          │      │       │         │─部署→
   │                │       │          │          │      │       │         │
   [───── 輪詢 task status ─────────────────────────────────────────────────]
   │<──200──│       │       │          │          │      │       │         │
   │  done         │       │          │          │      │       │         │
```

---

## 2. 權限設計

### 2.1 GitHub Token Scope 要求

當前使用的 `GITHUB_TOKEN` 權限需求：

```yaml
permissions:
  contents: write        # 建立分支、提交文件
  pull-requests: write   # 建立和合併 PR
  actions: read          # 讀取 workflow 狀態
  checks: read           # 讀取 CI 檢查結果
```

#### Backend API (enqueue 任務)
- 不需要 GitHub 權限
- 僅需 Redis 連接權限

#### Worker (執行 orchestrator)
```bash
GITHUB_TOKEN=<token>           # 必須：repo scope
GITHUB_REPO=RC918/morningai    # 必須：目標倉庫
REDIS_URL=<redis_url>          # 必須：任務佇列
SENTRY_DSN=<dsn>               # 可選：錯誤追蹤
```

**Token scope (PyGithub)**:
- `repo` - 完整倉庫存取權限
  - `repo:status` - 提交狀態
  - `repo_deployment` - 部署狀態
  - `public_repo` - 公開倉庫存取

#### Auto-merge Workflow
```yaml
permissions:
  pull-requests: write   # 執行 gh pr merge
  contents: write        # 合併到 main 分支
```

### 2.2 CI Trigger 條件

#### 觸發條件矩陣

| Workflow | 觸發事件 | 路徑過濾 | 分支限制 |
|----------|----------|---------|---------|
| backend-ci | push, pull_request | `api-backend/**` | 全部 |
| frontend-ci | push, pull_request | `frontend-dashboard/**` | 全部 |
| orchestrator-e2e | push, pull_request | `orchestrator/**` | 全部 |
| openapi-verify | pull_request | `**/openapi.yaml` | 全部 |
| agent-mvp-smoke | pull_request, cron | - | main |
| auto-merge-faq | pull_request, check_suite | `docs/FAQ.md` | 全部 |
| vercel-deploy | push | `frontend-dashboard/**` | main |

#### Auto-merge 觸發條件

```yaml
if: |
  github.event.pull_request.user.login == 'github-actions[bot]' ||
  contains(github.event.pull_request.title, 'trace-id')
```

**條件詳解**:
1. PR 由 `github-actions[bot]` 建立（orchestrator 使用的 bot）
2. **OR** PR 標題包含 `trace-id`（手動觸發的追蹤任務）

**安全檢查**:
- 僅當 `docs/FAQ.md` 是唯一變更的檔案
- 所有 CI 檢查必須通過（check_suite.conclusion == 'success'）

---

## 3. trace_id 與 pr_url 資料流設計

### 3.1 trace_id 生成與傳播

#### 生成時機
```python
# api-backend/src/routes/agent.py
task_id = str(uuid.uuid4())  # 作為 trace_id
```

#### 資料流追蹤

```
生成點              儲存位置                     用途
─────────────────────────────────────────────────────────
Backend API      → task_id (返回給 client)      • Client 輪詢狀態使用
                 → Redis: agent:task:{task_id}  • Worker 讀取任務參數
                 → RQ Job arguments             • Worker 執行時的 trace_id

Worker          → Sentry breadcrumb.data        • 錯誤追蹤關聯
                → structured logs               • 日誌關聯查詢
                → Redis: trace_id 欄位          • 任務狀態查詢

Orchestrator    → PR description                • GitHub PR 追蹤
                → Git commit message            • Git 歷史追蹤
                → execute() return value        • Worker 結果回傳

Redis (final)   → agent:task:{task_id}:
                  - trace_id: {task_id}
                  - pr_url: https://...
                  - status: done/error
                  - job_id: {rq_job_id}
```

### 3.2 Redis 資料結構

#### Task 狀態追蹤
```redis
# Key: agent:task:{task_id}
# Type: Hash
# TTL: 3600 seconds (1 hour)

HGETALL agent:task:550e8400-e29b-41d4-a716-446655440000
{
  "status": "done",                    # queued|running|done|error
  "question": "What is Phase 10?",
  "trace_id": "550e8400-...",          # 與 task_id 相同
  "job_id": "550e8400-...",            # RQ job ID
  "pr_url": "https://github.com/RC918/morningai/pull/123",
  "state": "open",                     # PR 狀態
  "created_at": "2025-10-08T16:00:00Z",
  "updated_at": "2025-10-08T16:00:45Z"
}
```

#### 重複性檢查（Idempotency）
```redis
# Key: agent:faq:hash:{question_hash}
# Type: String (存 task_id)
# TTL: 3600 seconds (1 hour)

GET agent:faq:hash:a3f2e1d9c8b7
-> "550e8400-e29b-41d4-a716-446655440000"

# 相同問題 1 小時內只處理一次
```

### 3.3 Sentry Breadcrumb 整合

當前實作位置: `orchestrator/redis_queue/worker.py`

```python
# 任務啟動
sentry_sdk.add_breadcrumb(
    category='task',
    message='Starting orchestrator task',
    level='info',
    data={
        'task_id': task_id,
        'trace_id': task_id,
        'question': question,
        'repo': repo
    }
)

# Redis 狀態更新
sentry_sdk.add_breadcrumb(
    category='redis',
    message='Updating task status to running',
    level='info',
    data={
        'redis_key': f"agent:task:{task_id}",
        'task_id': task_id
    }
)

# Orchestrator 執行
sentry_sdk.add_breadcrumb(
    category='orchestrator',
    message='Executing orchestrator',
    level='info',
    data={
        'task_id': task_id,
        'trace_id': task_id
    }
)

# 任務完成
sentry_sdk.add_breadcrumb(
    category='redis',
    message='Updating task status to done',
    level='info',
    data={
        'redis_key': redis_key,
        'task_id': task_id,
        'pr_url': pr_url
    }
)
```

### 3.4 pr_url 回寫流程

```python
# orchestrator/graph.py:execute()
pr_url, pr_number = open_pr(
    repo=repo,
    branch=branch,
    title=f"Update FAQ - {question}",
    body=f"trace-id: {trace_id}\n\n[Devin run](https://app.devin.ai/...)",
    base="main"
)

# orchestrator/redis_queue/worker.py:run_orchestrator_task()
pr_url, state, trace_id = execute(question, repo, trace_id=task_id)

redis.hset(
    f"agent:task:{task_id}",
    mapping={
        "status": "done",
        "pr_url": pr_url,
        "state": state,
        "trace_id": trace_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
)
```

### 3.5 端到端追蹤查詢

#### 通過 trace_id 查詢完整生命週期

```bash
# 1. Redis 查詢任務狀態
redis-cli HGETALL agent:task:{trace_id}

# 2. Sentry 查詢錯誤事件
# Search: trace_id:{trace_id}

# 3. GitHub 查詢 PR
# Search in PR body: "trace-id: {trace_id}"

# 4. Worker 日誌查詢（structured logs）
# grep "trace_id.*{trace_id}" worker.log
```

---

## 4. 錯誤復原策略（Auto-rollback）

### 4.1 當前狀況

**問題**: 系統目前**沒有**自動回滾機制。

**風險**:
- 如果 FAQ 更新引入錯誤（語法錯誤、不當內容），部署後會影響生產環境
- CI 檢查通過但 Post-deploy health check 失敗時，錯誤代碼已經部署
- 手動回滾需要人工介入，違背全自動閉環目標

### 4.2 提議的 Auto-rollback 策略

#### 4.2.1 三層防護機制

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Pre-merge 驗證 (阻止錯誤合併)                    │
├──────────────────────────────────────────────────────────┤
│  • CI 檢查全部通過 (必須)                                  │
│  • OpenAPI schema 驗證 (如有 API 變更)                     │
│  • Lint + Format 檢查                                     │
│  • Unit tests 通過                                        │
│  • Orchestrator E2E 測試                                  │
│  ↓ 僅當全部通過才允許 auto-merge                           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Layer 2: Post-deploy 健康檢查 (偵測部署問題)              │
├──────────────────────────────────────────────────────────┤
│  • 部署後 2 分鐘內執行 smoke test                          │
│  • 檢查項目:                                              │
│    - GET /healthz 返回 200                                │
│    - GET /api/agent/tasks/{test_task_id} 正常              │
│    - Frontend 首頁載入成功                                 │
│    - Worker heartbeat 正常 (Redis 有心跳)                  │
│  ↓ 如果失敗 → 觸發 Layer 3 自動回滾                        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Layer 3: Auto-rollback 執行 (恢復上一個穩定版本)          │
├──────────────────────────────────────────────────────────┤
│  • Git revert 合併 commit                                 │
│  • 自動建立 hotfix PR: "Rollback: {reason}"               │
│  • 快速合併 (bypass normal CI, 僅運行 smoke test)          │
│  • 通知 Slack #oncall                                     │
│  • 建立 GitHub Issue (label: P0, auto-rollback)           │
└──────────────────────────────────────────────────────────┘
```

#### 4.2.2 實作設計

##### Workflow: `post-deploy-rollback.yml`

```yaml
name: Post-deploy Rollback

on:
  workflow_dispatch:
    inputs:
      commit_sha:
        description: 'Commit SHA to rollback'
        required: true
      reason:
        description: 'Rollback reason'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Create rollback branch
        run: |
          git checkout main
          git pull origin main
          ROLLBACK_BRANCH="hotfix/rollback-$(date +%s)"
          git checkout -b $ROLLBACK_BRANCH
          echo "ROLLBACK_BRANCH=$ROLLBACK_BRANCH" >> $GITHUB_ENV
      
      - name: Revert commit
        run: |
          git revert --no-edit ${{ inputs.commit_sha }}
          git push origin $ROLLBACK_BRANCH
      
      - name: Create rollback PR
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh pr create \
            --title "🚨 Auto-rollback: ${{ inputs.reason }}" \
            --body "**Reason**: ${{ inputs.reason }}
            
            **Reverted commit**: ${{ inputs.commit_sha }}
            **Timestamp**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
            
            This is an automated rollback triggered by post-deploy health check failure.
            
            cc @RC918" \
            --base main \
            --head $ROLLBACK_BRANCH \
            --label "P0,auto-rollback,hotfix"
      
      - name: Auto-merge rollback PR
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          PR_NUMBER=$(gh pr list --head $ROLLBACK_BRANCH --json number -q '.[0].number')
          # 快速合併，僅等待 smoke test
          gh pr merge $PR_NUMBER --auto --squash
      
      - name: Create incident issue
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh issue create \
            --title "🚨 Production Rollback: ${{ inputs.reason }}" \
            --body "**Auto-rollback executed**
            
            **Reverted commit**: ${{ inputs.commit_sha }}
            **Reason**: ${{ inputs.reason }}
            **Rollback PR**: #$PR_NUMBER
            **Time**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
            
            **Action Required**:
            - [ ] Investigate root cause
            - [ ] Fix underlying issue
            - [ ] Submit proper fix with full CI validation
            
            cc @RC918" \
            --label "P0,incident,auto-rollback"
```

##### Workflow: `post-deploy-health.yml` (增強版)

```yaml
name: Post-deploy Health Check

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Wait for deployment
        run: sleep 120  # 等待 Vercel + Render 部署完成
      
      - name: Backend health check
        id: backend
        run: |
          response=$(curl -f -s https://morningai-backend-v2.onrender.com/healthz || echo "FAIL")
          if [ "$response" = "FAIL" ]; then
            echo "status=failed" >> $GITHUB_OUTPUT
            exit 1
          fi
      
      - name: Frontend health check
        id: frontend
        run: |
          response=$(curl -f -s -o /dev/null -w "%{http_code}" https://morningai.vercel.app || echo "000")
          if [ "$response" != "200" ]; then
            echo "status=failed" >> $GITHUB_OUTPUT
            exit 1
          fi
      
      - name: Worker heartbeat check
        id: worker
        env:
          REDIS_URL: ${{ secrets.REDIS_URL }}
        run: |
          pip install redis
          python - <<'PY'
          import os, sys, time, redis
          r = redis.from_url(os.getenv("REDIS_URL"))
          now = time.time()
          found = False
          for k in r.scan_iter(b"worker:heartbeat:*"):
              found = True
              m = r.hgetall(k)
              ts = float((m.get(b'last_heartbeat') or b'0').decode())
              if now - ts > 300:  # 5 分鐘內有心跳
                  sys.exit(1)
          if not found:
              sys.exit(1)
          PY
      
      - name: Trigger rollback on failure
        if: failure()
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh workflow run post-deploy-rollback.yml \
            -f commit_sha=${{ github.sha }} \
            -f reason="Post-deploy health check failed"
      
      - name: Notify on failure
        if: failure()
        run: |
          # 發送 Slack/Email 通知（需配置）
          echo "Health check failed, rollback triggered"
```

#### 4.2.3 回滾決策邏輯

```
部署成功 (git push to main)
    ↓
等待 2 分鐘（deployment window）
    ↓
執行 Post-deploy Health Check
    ↓
┌───────────────────┐
│  Health OK?       │
└────┬──────────┬───┘
     YES        NO
     │          │
     │          ↓
     │    ┌─────────────────┐
     │    │ 觸發 Auto-rollback│
     │    └─────────────────┘
     │          │
     │          ↓
     │    • Revert commit
     │    • Create hotfix PR
     │    • Auto-merge (fast-track)
     │    • Create P0 issue
     │    • Notify #oncall
     │          │
     ↓          ↓
   正常運行    回滾完成
```

### 4.3 回滾性能目標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 偵測時間 | ≤ 3 分鐘 | 部署後 2 分鐘 + health check 1 分鐘 |
| 回滾決策 | ≤ 30 秒 | 自動觸發，無需人工判斷 |
| 回滾執行 | ≤ 5 分鐘 | Revert + PR + Merge + Deploy |
| **總回滾時間 (TRB)** | **≤ 8 分鐘** | 從偵測到問題恢復 |

### 4.4 手動回滾流程（備用）

如果自動回滾失敗，提供手動流程：

```bash
# 1. 找到需要回滾的 commit
git log --oneline -10

# 2. 建立 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/manual-rollback-$(date +%s)

# 3. Revert commit
git revert <commit_sha> --no-edit

# 4. 推送並建立 PR
git push origin HEAD
gh pr create --title "Manual Rollback: <reason>" --body "..." --base main

# 5. 快速合併
gh pr merge <PR_NUMBER> --squash --delete-branch
```

---

## 5. 成功指標：TTE ≤ 1 min、成功率 ≥ 99%

### 5.1 Time-to-Execute (TTE) 分解

#### 當前時間分配（估計）

| 階段 | 當前時間 | 目標時間 | 優化策略 |
|------|----------|----------|----------|
| API 入隊 | ~0.5s | 0.5s | ✓ 已優化（Redis 快速入隊） |
| Worker 拉取任務 | ~1-5s | 1s | ✓ RQ polling interval 已優化 |
| Graph.execute() | ~20-40s | 15s | **需優化** |
| ├─ OpenAI API call | ~10-20s | 8s | 使用更快的模型、減少 token |
| ├─ Git 操作 | ~5-10s | 3s | 使用淺複製、批次操作 |
| └─ GitHub API (create PR) | ~5-10s | 4s | 已優化（PyGithub） |
| CI 觸發 | ~5-10s | 5s | ✓ GitHub Actions 觸發延遲 |
| CI 執行 | **60-120s** | **25s** | **Critical path** |
| ├─ backend-ci/test | ~40s | 15s | 並行測試、快取優化 |
| ├─ frontend-ci/build | ~27s | 10s | ✓ 已接近最優 |
| ├─ orchestrator-e2e | ~25s | 15s | Mock 外部 API、精簡測試 |
| └─ openapi-verify | ~8s | 5s | ✓ 已優化 |
| Auto-merge 執行 | ~2-5s | 2s | ✓ 已優化 |
| **總計** | **90-180s** | **≤60s** | **需優化 CI** |

#### 關鍵瓶頸

1. **CI 執行時間過長**（60-120s）- 占總時間 60-70%
2. **OpenAI API 延遲**（10-20s）- 不可控，但可優化 prompt 減少 token
3. **Worker 輪詢間隔**（1-5s）- RQ 預設輪詢，可優化為事件驅動

### 5.2 TTE 優化方案

#### 5.2.1 CI 並行化（Phase 1 - 可立即實作）

```yaml
# .github/workflows/agent-mvp-ci-fast.yml
name: Agent MVP Fast CI

on:
  pull_request:
    paths:
      - 'docs/FAQ.md'

jobs:
  fast-track-faq:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        check: [lint, smoke, openapi]
      fail-fast: false  # 並行執行，不因單一失敗而中斷
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run ${{ matrix.check }}
        run: |
          case "${{ matrix.check }}" in
            lint)
              # 僅檢查 Markdown 語法
              npm install -g markdownlint-cli
              markdownlint docs/FAQ.md
              ;;
            smoke)
              # 快速 smoke test（不部署）
              echo "FAQ.md syntax OK"
              ;;
            openapi)
              # 僅在有 API 變更時執行
              if git diff --name-only origin/main | grep -q openapi.yaml; then
                npm run openapi:verify
              fi
              ;;
          esac
    
    timeout-minutes: 3  # 每個檢查最多 3 分鐘
```

**預期效果**: CI 時間從 60s → 15s

#### 5.2.2 OpenAI API 優化（Phase 2）

```python
# orchestrator/graph.py
def generate_faq_content(question: str) -> str:
    """使用更快的模型和優化的 prompt"""
    
    # 從 gpt-4 改為 gpt-3.5-turbo（快 3-5 倍）
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 更快
        messages=[
            {"role": "system", "content": "You are a concise FAQ writer."},
            {"role": "user", "content": f"Write a brief FAQ answer (max 100 words): {question}"}
        ],
        max_tokens=150,  # 限制 token 數量
        temperature=0.7,
        timeout=10  # 10 秒超時
    )
    
    return response.choices[0].message.content.strip()
```

**預期效果**: OpenAI API 時間從 15s → 5s

#### 5.2.3 Git 操作優化（Phase 2）

```python
# orchestrator/tools/github_api.py
def create_branch_fast(repo, base="main", new_branch="orchestrator/demo"):
    """使用淺複製加速分支建立"""
    
    # 不使用 PyGithub 的 API（需要多次 HTTP 請求）
    # 改用 Git CLI（本地操作，更快）
    
    try:
        # 淺複製，只拉取最新 1 個 commit
        subprocess.run([
            "git", "clone", "--depth", "1", 
            "--branch", base,
            f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git",
            "/tmp/morningai-clone"
        ], check=True, timeout=5)
        
        # 建立並推送新分支
        subprocess.run([
            "git", "-C", "/tmp/morningai-clone",
            "checkout", "-b", new_branch
        ], check=True)
        
        # ... commit and push
        
    finally:
        shutil.rmtree("/tmp/morningai-clone", ignore_errors=True)
```

**預期效果**: Git 操作時間從 10s → 3s

### 5.3 成功率監控

#### 5.3.1 成功率定義

```
成功率 = (成功完成的任務數 / 總任務數) × 100%

成功 = 滿足以下所有條件：
  • Task status = "done"
  • PR 成功建立（pr_url 非空）
  • CI 全部通過
  • Auto-merge 成功（PR state = "merged"）
  • Post-deploy health check 通過
```

#### 5.3.2 失敗分類

| 失敗類型 | 計入成功率 | 應對策略 |
|----------|------------|----------|
| 重複任務（idempotency 拒絕） | **否** | 返回現有 task_id，不計入失敗 |
| OpenAI API 超時/失敗 | 是 | Retry 3 次，計入失敗 |
| GitHub API 失敗（rate limit） | 是 | Exponential backoff retry |
| CI 失敗（code issue） | 是 | 計入失敗，需人工修復 |
| Auto-merge 失敗（權限） | 是 | 環境問題，需修復 |
| Worker crash | 是 | 自動重啟，但該任務計入失敗 |

#### 5.3.3 監控指標收集

##### Redis 指標（即時）

```redis
# 成功任務計數器
INCR agent:metrics:success:$(date +%Y%m%d)

# 失敗任務計數器
INCR agent:metrics:failure:$(date +%Y%m%d)

# TTE 分佈（使用 sorted set 記錄）
ZADD agent:metrics:tte:$(date +%Y%m%d) {timestamp} {tte_ms}
```

##### Structured Logging（歷史查詢）

```python
# orchestrator/redis_queue/logger_util.py
log_structured(
    level="info",
    message="Task completed",
    operation="complete",
    trace_id=task_id,
    task_id=task_id,
    elapsed_ms=(end_time - start_time) * 1000,
    pr_url=pr_url,
    success=True
)
```

##### Sentry 指標（錯誤追蹤）

```python
# Worker 任務完成時記錄指標
if SENTRY_DSN:
    sentry_sdk.capture_message(
        f"Task completed: {task_id}",
        level="info",
        tags={
            "task_status": "done",
            "tte_ms": elapsed_ms,
            "success": True
        }
    )
```

#### 5.3.4 指標查詢 API

```python
# api-backend/src/routes/metrics.py (新增)

@app.route('/api/metrics/agent', methods=['GET'])
def get_agent_metrics():
    """獲取 Agent 任務執行指標"""
    
    today = datetime.now(timezone.utc).strftime('%Y%m%d')
    
    success_count = redis.get(f"agent:metrics:success:{today}") or 0
    failure_count = redis.get(f"agent:metrics:failure:{today}") or 0
    total_count = int(success_count) + int(failure_count)
    
    success_rate = (int(success_count) / total_count * 100) if total_count > 0 else 0
    
    # 計算 TTE p50, p95, p99
    tte_values = redis.zrange(f"agent:metrics:tte:{today}", 0, -1, withscores=True)
    tte_sorted = sorted([score for _, score in tte_values])
    
    p50 = tte_sorted[len(tte_sorted)//2] if tte_sorted else 0
    p95 = tte_sorted[int(len(tte_sorted)*0.95)] if tte_sorted else 0
    p99 = tte_sorted[int(len(tte_sorted)*0.99)] if tte_sorted else 0
    
    return jsonify({
        "date": today,
        "total_tasks": total_count,
        "success_count": int(success_count),
        "failure_count": int(failure_count),
        "success_rate_percent": round(success_rate, 2),
        "tte_ms": {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2)
        },
        "slo_met": {
            "tte_under_60s": p95 < 60000,
            "success_rate_above_99": success_rate >= 99.0
        }
    })
```

### 5.4 SLO（Service Level Objective）

| 指標 | SLO | 測量週期 | 告警閾值 |
|------|-----|----------|----------|
| **TTE P95** | ≤ 60 秒 | 每日 | P95 > 90s |
| **TTE P99** | ≤ 120 秒 | 每日 | P99 > 180s |
| **成功率** | ≥ 99% | 每日 | < 98% |
| **CI 通過率** | ≥ 95% | 每週 | < 90% |
| **Auto-merge 成功率** | ≥ 99% | 每日 | < 95% |
| **Worker 可用性** | ≥ 99.5% | 每月 | < 99% |

### 5.5 Dashboard 展示（建議）

```javascript
// frontend-dashboard/src/components/AgentMetrics.jsx

export function AgentMetricsDashboard() {
  const [metrics, setMetrics] = useState(null);
  
  useEffect(() => {
    fetch('/api/metrics/agent')
      .then(res => res.json())
      .then(setMetrics);
  }, []);
  
  if (!metrics) return <Loading />;
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Success Rate Card */}
      <Card>
        <CardHeader>
          <CardTitle>Success Rate (Today)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-4xl font-bold ${
            metrics.success_rate_percent >= 99 ? 'text-green-600' : 'text-red-600'
          }`}>
            {metrics.success_rate_percent}%
          </div>
          <p className="text-sm text-gray-500">
            {metrics.success_count} / {metrics.total_tasks} tasks
          </p>
          {metrics.slo_met.success_rate_above_99 ? (
            <Badge variant="success">✓ SLO Met</Badge>
          ) : (
            <Badge variant="destructive">✗ Below SLO</Badge>
          )}
        </CardContent>
      </Card>
      
      {/* TTE Card */}
      <Card>
        <CardHeader>
          <CardTitle>Time-to-Execute (P95)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-4xl font-bold ${
            metrics.tte_ms.p95 <= 60000 ? 'text-green-600' : 'text-orange-600'
          }`}>
            {(metrics.tte_ms.p95 / 1000).toFixed(1)}s
          </div>
          <p className="text-sm text-gray-500">
            P50: {(metrics.tte_ms.p50 / 1000).toFixed(1)}s | 
            P99: {(metrics.tte_ms.p99 / 1000).toFixed(1)}s
          </p>
          {metrics.slo_met.tte_under_60s ? (
            <Badge variant="success">✓ SLO Met (&lt;60s)</Badge>
          ) : (
            <Badge variant="destructive">✗ Above SLO</Badge>
          )}
        </CardContent>
      </Card>
      
      {/* Worker Health Card */}
      <Card>
        <CardHeader>
          <CardTitle>Worker Health</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Worker heartbeat status */}
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 6. 實作路徑（Roadmap）

### Phase 1: 基礎監控與快速 CI（1-2 週）
- [ ] 實作 TTE 和成功率指標收集
- [ ] 建立 `/api/metrics/agent` 端點
- [ ] 優化 FAQ 專用 CI workflow（並行化）
- [ ] 新增 Metrics Dashboard 頁面
- **目標**: TTE P95 < 90s, 成功率 > 95%

### Phase 2: TTE 優化（2-3 週）
- [ ] OpenAI API 優化（使用 gpt-3.5-turbo）
- [ ] Git 操作優化（淺複製）
- [ ] Worker 事件驅動（減少輪詢延遲）
- [ ] CI 快取優化（dependencies、test fixtures）
- **目標**: TTE P95 < 60s

### Phase 3: Auto-rollback 實作（2-3 週）
- [ ] 實作 `post-deploy-health.yml` workflow
- [ ] 實作 `post-deploy-rollback.yml` workflow
- [ ] 整合 Slack/Email 通知
- [ ] Runbook 與演練（Chaos Engineering）
- **目標**: TRB (Time-to-Rollback) < 8 min

### Phase 4: 達成 99% SLO（持續優化）
- [ ] 持續監控與調整
- [ ] A/B testing 不同優化方案
- [ ] 容錯機制增強（Retry with backoff）
- [ ] 定期 SLO review
- **目標**: 成功率 ≥ 99%, TTE P95 ≤ 60s

---

## 7. 風險與緩解措施

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| OpenAI API 不穩定 | TTE 增加、失敗率上升 | • Timeout 設定<br>• Retry 機制<br>• 降級方案（使用範本） |
| GitHub API Rate Limit | 任務失敗 | • Token rotation<br>• Backoff retry<br>• 監控 rate limit header |
| CI 執行時間波動 | TTE 不穩定 | • 監控 CI 執行時間<br>• 優化 slow tests<br>• 快取機制 |
| Worker 單點故障 | 任務積壓 | • 多 worker 實例<br>• Heartbeat 監控<br>• 自動重啟 |
| Auto-rollback 誤觸發 | 不必要的回滾 | • 多重健康檢查<br>• 人工確認選項（可選）<br>• Rollback log 分析 |
| Redis 連接中斷 | 任務狀態丟失 | • Redis 持久化（RDB + AOF）<br>• 連接 retry<br>• 降級模式（demo mode） |

---

## 8. 未來擴展

### 8.1 多 Agent 支援
- 支援多種類型的 Agent 任務（不僅限於 FAQ）
- 統一的 trace_id 系統
- 跨 Agent 的指標聚合

### 8.2 進階監控
- Distributed tracing（OpenTelemetry）
- Real-time dashboard（WebSocket 更新）
- 告警規則自動調整（基於歷史數據）

### 8.3 智能優化
- AI 預測任務執行時間
- 動態調整資源分配
- 自動化 A/B testing

---

## 9. 總結

本 RFC 提出了一個完整的 Agent MVP 閉環流程設計，涵蓋：

✅ **系統流程圖**: 清晰定義從 API 到部署的 10 個階段  
✅ **權限設計**: 明確 GitHub token scope 和 CI trigger 條件  
✅ **trace_id 追蹤**: 端到端的資料流設計（Redis + Sentry）  
✅ **Auto-rollback**: 三層防護機制，TRB < 8 分鐘  
✅ **成功指標**: TTE ≤ 60s (P95), 成功率 ≥ 99%  

**關鍵成功因素**:
1. CI 並行化與優化（60s → 15s）
2. OpenAI API 優化（15s → 5s）
3. 完善的監控與指標收集
4. 可靠的 Auto-rollback 機制

**下一步**: RFC 審核通過後，按 Phase 1-4 逐步實作。

---

## 附錄 A: 相關文件

- [Phase 9 Final Report](../phase9-final-report.md)
- [Worker Shutdown Report](../ops/worker-shutdown-report.md)
- [Sentry Alerts](../sentry-alerts.md)
- [Agent MVP E2E Workflow](../../.github/workflows/agent-mvp-e2e.yml)
- [Auto-merge FAQ Workflow](../../.github/workflows/auto-merge-faq.yml)

## 附錄 B: 詞彙表

- **TTE (Time-to-Execute)**: 從 API 請求到 PR 合併的總時間
- **TRB (Time-to-Rollback)**: 從偵測問題到回滾完成的總時間
- **SLO (Service Level Objective)**: 服務水平目標
- **P95/P99**: 第 95/99 百分位數
- **trace_id**: 唯一任務追蹤識別碼（與 task_id 相同）
- **Idempotency**: 重複執行相同操作不會產生副作用
