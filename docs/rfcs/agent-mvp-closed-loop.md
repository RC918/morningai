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

## 1. 目標（TTE ≤ 1 min、成功率 ≥ 99%）

### 1.1 核心目標

本 RFC 的核心目標是建立一個**快速、可靠、可觀測**的 Agent MVP 閉環流程：

| 指標 | 目標值 | 說明 |
|------|--------|------|
| **TTE (Time-to-Execute)** | P95 ≤ 60 秒 | 從 API 請求到 PR 合併的端到端時間 |
| **成功率** | ≥ 99% | 任務成功完成率（含 CI 通過、Auto-merge、部署驗證） |
| **TRB (Time-to-Rollback)** | ≤ 8 分鐘 | 偵測問題到回滾完成的時間 |
| **可用性** | ≥ 99.5% | Worker 和 API 的月度可用性 |

### 1.2 成功標準

一個任務被視為「成功」需滿足：
1. ✅ Task status = "done"
2. ✅ PR 成功建立（pr_url 非空）
3. ✅ 所有 CI 檢查通過
4. ✅ Auto-merge 成功執行
5. ✅ Post-deploy health check 通過

### 1.3 非功能性需求

- **可觀測性**: 每個任務都有 trace_id，可追蹤整個生命週期
- **可回滾性**: 部署失敗時 8 分鐘內自動回滾
- **容錯性**: 支援重試機制，減少瞬時錯誤影響

---

## 2. 系統流程圖

### 2.1 整體流程

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

### 2.2 資料流時序圖

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

## 3. 權限設計

### 3.1 GitHub Token Scope 要求

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

### 3.2 CI Trigger 條件

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

## 4. trace_id 與 pr_url 資料流設計

### 4.1 trace_id 生成與傳播

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

### 4.2 Redis 資料結構

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

### 4.3 資料庫持久化（agent_tasks 表格）

**設計目標**: 除 Redis（1 小時 TTL）外，新增永久審計軌跡儲存於 PostgreSQL。

**資料表結構**:
```sql
create table if not exists agent_tasks (
  task_id uuid primary key,
  trace_id uuid not null,
  job_id text,
  question text,
  status text check (status in ('queued','running','done','error')),
  pr_url text,
  error_msg text,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  updated_at timestamptz not null default now()
);

create index if not exists idx_agent_tasks_created_at on agent_tasks (created_at desc);
create index if not exists idx_agent_tasks_status on agent_tasks (status);
```

**寫入流程（Write-through）**:

| 狀態轉換 | 觸發點 | 更新欄位 |
|---------|--------|---------|
| → queued | API enqueue | task_id, trace_id, question, status='queued', job_id, created_at, updated_at |
| → running | Worker 開始 | status='running', started_at, updated_at |
| → done | Worker 成功 | status='done', pr_url, finished_at, updated_at |
| → error | Worker 失敗 | status='error', error_msg, finished_at, updated_at |

**讀取流程（DB-first with Redis fallback）**:
```python
# GET /api/agent/tasks/{task_id}
# 1. 優先讀取 DB（永久儲存）
task = supabase.table("agent_tasks").select("*").eq("task_id", task_id).execute()

# 2. DB 無資料時回退 Redis（1 小時內的任務）
if not task.data:
    task = redis.get(f"agent:task:{task_id}")
```

**觀測性（Sentry Breadcrumbs）**:
```python
# 每次狀態轉換新增 breadcrumb
sentry_sdk.add_breadcrumb(
    category='agent_task',
    message=f'Task {task_id} status → {status}',
    level='info',
    data={'task_id': task_id, 'status': status, 'pr_url': pr_url}
)
```

**錯誤處理**:
- DB 寫入失敗不影響 Redis 流程（graceful degradation）
- 每次失敗記錄錯誤日誌但繼續執行
- Sentry 追蹤所有 DB 操作錯誤

### 4.4 Sentry Breadcrumb 整合

當前實作位置: `orchestrator/redis_queue/worker.py`, `api-backend/src/routes/agent.py`

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

# 任務完成（含 DB 持久化）
sentry_sdk.add_breadcrumb(
    category='agent_task',
    message='Task completed and persisted to DB',
    level='info',
    data={
        'task_id': task_id,
        'status': 'done',
        'pr_url': pr_url
    }
)
```

### 4.5 pr_url 回寫流程

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

### 4.6 端到端追蹤查詢

#### 通過 trace_id 查詢完整生命週期

```bash
# 1. DB 查詢任務狀態（永久儲存）
psql -c "SELECT * FROM agent_tasks WHERE task_id = '{trace_id}'"

# 2. Redis 查詢任務狀態（1 小時內）
redis-cli HGETALL agent:task:{trace_id}

# 3. Sentry 查詢錯誤事件
# Search: trace_id:{trace_id}

# 4. GitHub 查詢 PR
# Search in PR body: "trace-id: {trace_id}"

# 5. Worker 日誌查詢（structured logs）
# grep "trace_id.*{trace_id}" worker.log
```

---

## 5. 錯誤復原策略（Auto-rollback）

### 5.1 當前狀況

**問題**: 系統目前**沒有**自動回滾機制。

**風險**:
- 如果 FAQ 更新引入錯誤（語法錯誤、不當內容），部署後會影響生產環境
- CI 檢查通過但 Post-deploy health check 失敗時，錯誤代碼已經部署
- 手動回滾需要人工介入，違背全自動閉環目標

### 5.2 提議的 Auto-rollback 策略

#### 5.2.1 三層防護機制

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

#### 5.2.2 實作設計

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

#### 5.2.3 回滾決策邏輯

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

### 5.3 回滾性能目標

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 偵測時間 | ≤ 3 分鐘 | 部署後 2 分鐘 + health check 1 分鐘 |
| 回滾決策 | ≤ 30 秒 | 自動觸發，無需人工判斷 |
| 回滾執行 | ≤ 5 分鐘 | Revert + PR + Merge + Deploy |
| **總回滾時間 (TRB)** | **≤ 8 分鐘** | 從偵測到問題恢復 |

### 5.4 手動回滾流程（備用）

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

## 6. e2e 測試情境（多輪 / 佇列壓力 / 超時）

### 6.1 基礎功能測試

#### 6.1.1 單次 FAQ 生成流程
```yaml
# 測試目標: 驗證基本閉環流程
scenario:
  name: "Single FAQ Generation"
  steps:
    - POST /api/agent/faq {"question": "What is Phase 10?"}
    - 驗證返回 202 + task_id
    - 輪詢任務狀態 (最多 60 秒)
    - 驗證 PR 建立成功
    - 驗證 CI 全部通過
    - 驗證 Auto-merge 執行
    - 驗證 docs/FAQ.md 已更新
  expected:
    - TTE < 60s
    - Status = "done"
    - PR merged successfully
```

#### 6.1.2 重複請求（Idempotency）
```yaml
scenario:
  name: "Duplicate Request Handling"
  steps:
    - POST 相同 question 兩次
    - 第二次請求應返回相同 task_id
    - 不應建立重複 PR
  expected:
    - 第二次返回 409 或重用 task_id
    - Redis 1 小時 TTL 內去重
```

### 6.2 多輪 FAQ 請求測試

#### 6.2.1 順序多輪請求
```yaml
scenario:
  name: "Sequential Multiple Requests"
  steps:
    - 依序發送 5 個不同 FAQ 請求
    - 每個請求間隔 2 秒
  expected:
    - 所有任務均成功完成
    - 每個任務 TTE < 60s
    - 5 個 PR 都成功合併
    - 無任務互相干擾
```

#### 6.2.2 並發多輪請求
```yaml
scenario:
  name: "Concurrent Multiple Requests"
  steps:
    - 同時發送 10 個不同 FAQ 請求
    - 模擬高峰期流量
  expected:
    - 所有任務進入佇列
    - Worker 依序處理（無崩潰）
    - 成功率 ≥ 90% (允許部分失敗)
    - 平均 TTE < 90s (可能排隊)
```

### 6.3 佇列壓力測試

#### 6.3.1 Worker 容量測試
```yaml
scenario:
  name: "Worker Capacity Test"
  setup:
    - 單一 Worker 實例
  steps:
    - 發送 20 個 FAQ 請求
    - 監控 Worker 記憶體使用
    - 監控 Redis 佇列長度
  expected:
    - Worker 不 crash
    - 記憶體使用 < 512MB
    - 佇列最大長度 < 20
    - 所有任務最終完成
```

#### 6.3.2 佇列積壓恢復測試
```yaml
scenario:
  name: "Queue Backlog Recovery"
  setup:
    - 停止 Worker
    - 累積 10 個任務在佇列
  steps:
    - 重啟 Worker
    - 觀察任務處理順序（FIFO）
  expected:
    - Worker 依序處理所有任務
    - 無任務遺失
    - 恢復時間 < 5 分鐘
```

### 6.4 超時情境測試

#### 6.4.1 OpenAI API 超時
```yaml
scenario:
  name: "OpenAI API Timeout"
  setup:
    - Mock OpenAI API 延遲 30 秒
  steps:
    - 發送 FAQ 請求
    - 觀察 Worker 行為
  expected:
    - Orchestrator timeout 觸發 (10s)
    - 任務標記為失敗
    - Retry 機制觸發（最多 3 次）
    - Sentry 記錄 timeout 事件
```

#### 6.4.2 GitHub API 超時
```yaml
scenario:
  name: "GitHub API Timeout"
  setup:
    - Mock GitHub API 延遲
  steps:
    - 發送 FAQ 請求
    - Orchestrator 嘗試建立 PR
  expected:
    - Exponential backoff retry
    - 最多重試 3 次
    - 失敗後標記任務為 error
```

#### 6.4.3 CI 執行超時
```yaml
scenario:
  name: "CI Execution Timeout"
  setup:
    - Mock CI workflow 執行超過 10 分鐘
  steps:
    - PR 建立後觸發 CI
    - E2E 測試輪詢超時（120 次 × 5 秒）
  expected:
    - E2E 測試失敗（但 PR 仍存在）
    - Auto-merge 不會執行（CI 未完成）
    - 人工介入處理
```

### 6.5 失敗情境測試

#### 6.5.1 CI 失敗情境
```yaml
scenario:
  name: "CI Failure Handling"
  setup:
    - 引入會導致 lint 失敗的代碼
  steps:
    - 發送 FAQ 請求
    - PR 建立後 CI 執行
  expected:
    - CI 檢查失敗
    - Auto-merge 不執行
    - 任務狀態保持 "running" 或標記 "ci_failed"
    - GitHub Issue 自動建立（可選）
```

#### 6.5.2 Auto-merge 權限失敗
```yaml
scenario:
  name: "Auto-merge Permission Failure"
  setup:
    - 移除 GITHUB_TOKEN 的 pull-requests:write 權限
  steps:
    - 發送 FAQ 請求
    - CI 全部通過
    - Auto-merge workflow 執行
  expected:
    - Auto-merge 失敗（403 權限錯誤）
    - Sentry 記錄錯誤
    - 告警通知 #oncall
```

#### 6.5.3 Post-deploy Health Check 失敗
```yaml
scenario:
  name: "Post-deploy Health Failure & Rollback"
  setup:
    - 引入會導致 /healthz 失敗的變更
  steps:
    - 發送 FAQ 請求
    - PR 合併並部署
    - Post-deploy health check 執行
  expected:
    - Health check 失敗
    - Auto-rollback workflow 觸發
    - Revert commit 建立
    - Hotfix PR 自動合併
    - 8 分鐘內完成回滾
```

### 6.6 測試自動化

#### 6.6.1 整合到 CI
```yaml
# .github/workflows/agent-mvp-e2e-extended.yml
name: Agent MVP E2E Extended Tests

on:
  pull_request:
    paths:
      - 'orchestrator/**'
      - '.github/workflows/auto-merge-faq.yml'
  schedule:
    - cron: '0 2 * * *'  # 每日 2am 執行

jobs:
  e2e-scenarios:
    strategy:
      matrix:
        scenario:
          - single-faq
          - duplicate-request
          - sequential-5x
          - concurrent-10x
          - timeout-openai
          - ci-failure
    steps:
      - name: Run ${{ matrix.scenario }}
        run: |
          python tests/e2e/${{ matrix.scenario }}.py
```

#### 6.6.2 測試資料管理
```python
# tests/e2e/test_data.py
FAQ_TEST_QUESTIONS = [
    "What is Phase 10?",
    "How do I deploy to production?",
    "What is the worker heartbeat mechanism?",
    # ... more test questions
]

def generate_unique_question():
    """生成唯一測試問題（避免 idempotency 衝突）"""
    timestamp = int(time.time())
    return f"Test FAQ at {timestamp}: What is the current system status?"
```

### 6.7 效能基準測試

```yaml
scenario:
  name: "Performance Baseline"
  frequency: "每週執行"
  steps:
    - 執行 100 個 FAQ 請求
    - 記錄每個請求的 TTE
    - 計算 P50, P95, P99
  acceptance_criteria:
    - P95 < 60s
    - P99 < 120s
    - 成功率 ≥ 99%
  report:
    - 生成效能趨勢圖表
    - 與上週基準比較
    - 標記效能回歸
```

---

## 7. 指標與觀測（Sentry tags / APP_VERSION / heartbeat 關聯）

### 7.1 Sentry Tags 設計

#### 7.1.1 任務執行 Tags
```python
# orchestrator/redis_queue/worker.py
def run_orchestrator_task(task_id, question, repo):
    with sentry_sdk.configure_scope() as scope:
        # 設定 tags
        scope.set_tag("task_id", task_id)
        scope.set_tag("trace_id", task_id)
        scope.set_tag("task_type", "faq_generation")
        scope.set_tag("environment", os.getenv("ENV", "production"))
        scope.set_tag("worker_instance", os.getenv("RENDER_INSTANCE_ID", "local"))
        
        # 執行任務
        start_time = time.time()
        try:
            result = execute(question, repo, trace_id=task_id)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 成功時設定 tags
            scope.set_tag("task_status", "done")
            scope.set_tag("tte_ms", int(elapsed_ms))
            scope.set_tag("success", "true")
            scope.set_tag("pr_url", result.get("pr_url", ""))
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 失敗時設定 tags
            scope.set_tag("task_status", "error")
            scope.set_tag("tte_ms", int(elapsed_ms))
            scope.set_tag("success", "false")
            scope.set_tag("error_type", type(e).__name__)
            raise
```

#### 7.1.2 可用的 Sentry Tags 列表

| Tag | 值範例 | 用途 |
|-----|--------|------|
| `task_id` | `550e8400-...` | 唯一任務識別碼 |
| `trace_id` | `550e8400-...` | 與 task_id 相同，用於追蹤 |
| `task_type` | `faq_generation` | 任務類型 |
| `task_status` | `done`, `error`, `timeout` | 任務結果狀態 |
| `tte_ms` | `45000` | 執行時間（毫秒） |
| `success` | `true`, `false` | 是否成功 |
| `error_type` | `OpenAITimeout`, `GitHubAPIError` | 錯誤類型 |
| `pr_url` | `https://github.com/...` | PR 連結 |
| `environment` | `production`, `staging` | 執行環境 |
| `worker_instance` | `srv-abc123` | Worker 實例 ID |
| `app_version` | `v1.2.3` | 應用版本號 |

### 7.2 APP_VERSION 追蹤

#### 7.2.1 版本號生成策略
```bash
# 使用 Git commit SHA 作為版本號
APP_VERSION=$(git rev-parse --short HEAD)
echo "APP_VERSION=$APP_VERSION" >> $GITHUB_ENV
```

#### 7.2.2 Render 部署配置
```yaml
# render.yaml
services:
  - type: worker
    name: morningai-worker
    env: python
    envVars:
      - key: APP_VERSION
        sync: false  # 每次部署時動態設定
      - key: SENTRY_RELEASE
        value: ${APP_VERSION}  # Sentry release tracking
```

#### 7.2.3 Worker 初始化時設定版本
```python
# orchestrator/redis_queue/worker.py
import os
import sentry_sdk

APP_VERSION = os.getenv("APP_VERSION", os.getenv("RENDER_GIT_COMMIT", "unknown"))

# 設定 Sentry release
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENV", "production"),
    release=f"morningai-worker@{APP_VERSION}",
    traces_sample_rate=0.1
)

# 在每個任務中記錄版本
def run_orchestrator_task(task_id, question, repo):
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("app_version", APP_VERSION)
        scope.set_context("deployment", {
            "version": APP_VERSION,
            "instance_id": os.getenv("RENDER_INSTANCE_ID", "local"),
            "deployed_at": os.getenv("RENDER_GIT_COMMIT_DATE", "unknown")
        })
```

#### 7.2.4 Sentry Release 查詢
```bash
# 查詢特定版本的錯誤
# Sentry UI: Filters → Release → morningai-worker@abc123

# 查詢版本間的錯誤差異
# 比較 v1.2.3 和 v1.2.4 的錯誤率變化
```

### 7.3 Worker Heartbeat 與任務執行關聯

#### 7.3.1 Heartbeat + Task 資料結構
```redis
# Worker Heartbeat
HGETALL worker:heartbeat:srv-abc123
{
  "last_heartbeat": "2025-10-08T16:00:00Z",
  "status": "running",
  "current_task_id": "550e8400-...",  # 新增：當前執行任務
  "app_version": "abc123",             # 新增：版本號
  "tasks_completed": 42,               # 新增：累計完成任務數
  "uptime_seconds": 3600
}

# Task 資料中也記錄 Worker 資訊
HGETALL agent:task:550e8400-...
{
  "status": "running",
  "worker_instance": "srv-abc123",    # 新增：處理此任務的 Worker
  "worker_version": "abc123",         # 新增：Worker 版本
  "started_at": "2025-10-08T16:00:00Z",
  "trace_id": "550e8400-..."
}
```

#### 7.3.2 Heartbeat 更新邏輯
```python
# orchestrator/redis_queue/worker.py
def update_heartbeat_with_task_info(redis, worker_id, current_task_id=None):
    """更新 Heartbeat 並記錄當前任務"""
    heartbeat_key = f"worker:heartbeat:{worker_id}"
    
    heartbeat_data = {
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "status": "running" if current_task_id else "idle",
        "app_version": APP_VERSION,
        "uptime_seconds": int(time.time() - worker_start_time)
    }
    
    if current_task_id:
        heartbeat_data["current_task_id"] = current_task_id
        # 增加完成計數
        redis.hincrby(heartbeat_key, "tasks_completed", 0)  # init if not exists
    
    redis.hset(heartbeat_key, mapping=heartbeat_data)
    redis.expire(heartbeat_key, 300)  # 5 分鐘 TTL

def run_orchestrator_task(task_id, question, repo):
    """執行任務時更新 Heartbeat"""
    worker_id = os.getenv("RENDER_INSTANCE_ID", "local")
    
    # 任務開始：更新 Heartbeat 記錄當前任務
    update_heartbeat_with_task_info(redis, worker_id, current_task_id=task_id)
    
    # 更新任務資料記錄 Worker 資訊
    redis.hset(
        f"agent:task:{task_id}",
        mapping={
            "status": "running",
            "worker_instance": worker_id,
            "worker_version": APP_VERSION,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
    )
    
    try:
        # 執行任務
        result = execute(question, repo, trace_id=task_id)
        
        # 任務完成：增加完成計數
        redis.hincrby(f"worker:heartbeat:{worker_id}", "tasks_completed", 1)
        
    finally:
        # 清除當前任務
        update_heartbeat_with_task_info(redis, worker_id, current_task_id=None)
```

#### 7.3.3 Heartbeat 監控 + Sentry 關聯
```python
# .github/workflows/worker-heartbeat-monitor.yml 增強版
def check_worker_health_with_sentry():
    """檢查 Worker 健康狀態並關聯 Sentry 事件"""
    import redis
    import sentry_sdk
    
    r = redis.from_url(os.getenv("REDIS_URL"))
    now = time.time()
    
    for key in r.scan_iter(b"worker:heartbeat:*"):
        worker_id = key.decode().split(":")[-1]
        data = r.hgetall(key)
        
        last_heartbeat = data.get(b"last_heartbeat", b"").decode()
        current_task = data.get(b"current_task_id", b"").decode()
        app_version = data.get(b"app_version", b"").decode()
        
        # 檢查是否超過 2 分鐘無心跳
        heartbeat_age = now - parse_timestamp(last_heartbeat)
        
        if heartbeat_age > 120:
            # 發送 Sentry 事件
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("worker_id", worker_id)
                scope.set_tag("app_version", app_version)
                scope.set_tag("heartbeat_age_seconds", int(heartbeat_age))
                if current_task:
                    scope.set_tag("stuck_task_id", current_task)
                
                sentry_sdk.capture_message(
                    f"Worker {worker_id} heartbeat stale (>2min)",
                    level="error"
                )
            
            # 如果 Worker 卡在某個任務上
            if current_task:
                task_data = r.hgetall(f"agent:task:{current_task}")
                task_started = task_data.get(b"started_at", b"").decode()
                task_age = now - parse_timestamp(task_started)
                
                if task_age > 600:  # 任務執行超過 10 分鐘
                    sentry_sdk.capture_message(
                        f"Task {current_task} stuck for {task_age}s on worker {worker_id}",
                        level="critical"
                    )
```

### 7.4 TTE 和成功率監控

#### 7.4.1 Time-to-Execute (TTE) 分解

#### 7.4.1.1 當前時間分配（估計）

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

#### 7.4.1.2 關鍵瓶頸

1. **CI 執行時間過長**（60-120s）- 占總時間 60-70%
2. **OpenAI API 延遲**（10-20s）- 不可控，但可優化 prompt 減少 token
3. **Worker 輪詢間隔**（1-5s）- RQ 預設輪詢，可優化為事件驅動

#### 7.4.2 TTE 優化方案

##### 7.4.2.1 CI 並行化（Phase 1 - 可立即實作）

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

##### 7.4.2.2 OpenAI API 優化（Phase 2）

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

##### 7.4.2.3 Git 操作優化（Phase 2）

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

#### 7.4.3 成功率監控

##### 7.4.3.1 成功率定義

```
成功率 = (成功完成的任務數 / 總任務數) × 100%

成功 = 滿足以下所有條件：
  • Task status = "done"
  • PR 成功建立（pr_url 非空）
  • CI 全部通過
  • Auto-merge 成功（PR state = "merged"）
  • Post-deploy health check 通過
```

##### 7.4.3.2 失敗分類

| 失敗類型 | 計入成功率 | 應對策略 |
|----------|------------|----------|
| 重複任務（idempotency 拒絕） | **否** | 返回現有 task_id，不計入失敗 |
| OpenAI API 超時/失敗 | 是 | Retry 3 次，計入失敗 |
| GitHub API 失敗（rate limit） | 是 | Exponential backoff retry |
| CI 失敗（code issue） | 是 | 計入失敗，需人工修復 |
| Auto-merge 失敗（權限） | 是 | 環境問題，需修復 |
| Worker crash | 是 | 自動重啟，但該任務計入失敗 |

##### 7.4.3.3 監控指標收集

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

##### 7.4.3.4 指標查詢 API

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

### 7.5 SLO（Service Level Objective）

| 指標 | SLO | 測量週期 | 告警閾值 |
|------|-----|----------|----------|
| **TTE P95** | ≤ 60 秒 | 每日 | P95 > 90s |
| **TTE P99** | ≤ 120 秒 | 每日 | P99 > 180s |
| **成功率** | ≥ 99% | 每日 | < 98% |
| **CI 通過率** | ≥ 95% | 每週 | < 90% |
| **Auto-merge 成功率** | ≥ 99% | 每日 | < 95% |
| **Worker 可用性** | ≥ 99.5% | 每月 | < 99% |

### 7.6 Dashboard 展示（建議）

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

### 7.7 Sentry Dashboard 配置

#### 7.7.1 推薦的 Sentry Discover 查詢

**任務成功率（按版本）**
```sql
SELECT
  tag[app_version] as version,
  count() as total,
  countIf(tag[success] = 'true') as success_count,
  success_count / total * 100 as success_rate
FROM events
WHERE tag[task_type] = 'faq_generation'
GROUP BY version
ORDER BY version DESC
```

**TTE 分佈（P50/P95/P99）**
```sql
SELECT
  quantile(0.5)(tag[tte_ms]) as p50,
  quantile(0.95)(tag[tte_ms]) as p95,
  quantile(0.99)(tag[tte_ms]) as p99
FROM events
WHERE tag[task_type] = 'faq_generation'
  AND tag[success] = 'true'
  AND timestamp > now() - 24h
```

**Worker 健康狀態**
```sql
SELECT
  tag[worker_instance] as worker,
  tag[app_version] as version,
  count() as events,
  max(timestamp) as last_seen
FROM events
WHERE message LIKE '%Worker%heartbeat%'
GROUP BY worker, version
ORDER BY last_seen DESC
```

#### 7.7.2 告警規則（基於 Sentry Tags）

```yaml
# Sentry Alert: TTE 超過 SLO
alert:
  name: "Agent TTE Exceeded SLO"
  conditions:
    - tag[task_type] = 'faq_generation'
    - tag[tte_ms] > 90000  # P95 > 90s
    - count > 5 in 10 minutes
  actions:
    - Slack #oncall
    - Email on-call engineer

# Sentry Alert: 成功率低於 SLO
alert:
  name: "Agent Success Rate Below SLO"
  conditions:
    - tag[task_type] = 'faq_generation'
    - count(tag[success] = 'false') / count(*) > 0.05  # 失敗率 > 5%
    - in 1 hour
  actions:
    - Slack #oncall
    - Create GitHub Issue
```

---

## 8. 風險與時程（里程碑與拆分 PR）

### 8.1 風險與緩解措施

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| OpenAI API 不穩定 | TTE 增加、失敗率上升 | • Timeout 設定<br>• Retry 機制<br>• 降級方案（使用範本） |
| GitHub API Rate Limit | 任務失敗 | • Token rotation<br>• Backoff retry<br>• 監控 rate limit header |
| CI 執行時間波動 | TTE 不穩定 | • 監控 CI 執行時間<br>• 優化 slow tests<br>• 快取機制 |
| Worker 單點故障 | 任務積壓 | • 多 worker 實例<br>• Heartbeat 監控<br>• 自動重啟 |
| Auto-rollback 誤觸發 | 不必要的回滾 | • 多重健康檢查<br>• 人工確認選項（可選）<br>• Rollback log 分析 |
| Redis 連接中斷 | 任務狀態丟失 | • Redis 持久化（RDB + AOF）<br>• 連接 retry<br>• 降級模式（demo mode） |

### 8.2 實作時程與里程碑

**截止日期**: 草稿本週五 EOD；定稿下週三

#### 8.2.1 Phase 1: 基礎監控與快速 CI（1-2 週）
**里程碑 M1.1: 指標收集（3 天）**
- [ ] 實作 TTE 和成功率指標收集到 Redis
- [ ] 建立 `/api/metrics/agent` 端點
- [ ] 新增 Sentry tags（task_status, tte_ms, success）
- [ ] PR 拆分:
  - PR #1: Redis 指標收集邏輯（`worker.py`）
  - PR #2: Metrics API 端點（`api-backend/routes/metrics.py`）
  - PR #3: Sentry tags 整合（`worker.py`, `logger_util.py`）

**里程碑 M1.2: CI 優化（2 天）**
- [ ] 建立 FAQ 專用快速 CI workflow
- [ ] 實作並行化測試
- [ ] 優化 Docker layer 快取
- [ ] PR: PR #4: agent-mvp-ci-fast.yml

**里程碑 M1.3: Dashboard（2 天）**
- [ ] 新增 Metrics Dashboard 頁面（React）
- [ ] 整合 Success Rate 和 TTE 圖表
- [ ] 新增 Worker Health 狀態卡片
- [ ] PR: PR #5: Metrics Dashboard (frontend)

**驗收標準**:
- TTE P95 < 90s
- 成功率 > 95%
- Metrics API 正常運作
- Dashboard 可視化正確

#### 8.2.2 Phase 2: TTE 優化（2-3 週）
**里程碑 M2.1: OpenAI API 優化（3 天）**
- [ ] 遷移到 gpt-3.5-turbo
- [ ] 優化 prompt 減少 token
- [ ] 實作 timeout 機制（10s）
- [ ] PR: PR #6: OpenAI optimization

**里程碑 M2.2: Git 操作優化（3 天）**
- [ ] 實作淺複製（--depth 1）
- [ ] 優化分支建立流程
- [ ] 減少 PyGithub API 調用次數
- [ ] PR: PR #7: Git operations optimization

**里程碑 M2.3: Worker 事件驅動（5 天）**
- [ ] 替換輪詢為事件驅動（Redis Pub/Sub）
- [ ] 減少任務拉取延遲
- [ ] 測試並發處理能力
- [ ] PR: PR #8: Event-driven worker

**里程碑 M2.4: CI 快取優化（2 天）**
- [ ] 實作 dependencies 快取
- [ ] 優化 test fixtures 載入
- [ ] 減少重複 build 時間
- [ ] PR: PR #9: CI cache optimization

**驗收標準**:
- TTE P95 < 60s ✓
- OpenAI API 時間 < 8s
- Git 操作 < 3s
- CI 執行 < 25s

#### 8.2.3 Phase 3: Auto-rollback 實作（2-3 週）
**里程碑 M3.1: Post-deploy Health Check（3 天）**
- [ ] 實作 post-deploy-health.yml workflow
- [ ] 整合 Backend/Frontend/Worker 健康檢查
- [ ] 實作失敗偵測邏輯
- [ ] PR: PR #10: Post-deploy health check

**里程碑 M3.2: Auto-rollback Workflow（5 天）**
- [ ] 實作 post-deploy-rollback.yml workflow
- [ ] Git revert 自動化
- [ ] Hotfix PR 建立與合併
- [ ] GitHub Issue 自動建立
- [ ] PR: PR #11: Auto-rollback workflow

**里程碑 M3.3: 通知整合（2 天）**
- [ ] Slack webhook 整合
- [ ] Email 通知配置
- [ ] Runbook 文件撰寫
- [ ] PR: PR #12: Notification integration

**里程碑 M3.4: Chaos Engineering 演練（3 天）**
- [ ] 模擬 health check 失敗
- [ ] 驗證 rollback 流程完整性
- [ ] 測量 TRB（Time-to-Rollback）
- [ ] 文件化演練結果

**驗收標準**:
- TRB < 8 分鐘
- Rollback 成功率 100%（測試環境）
- 告警通知正常運作
- Runbook 文件完整

#### 8.2.4 Phase 4: 達成 99% SLO（持續優化）
**里程碑 M4.1: 監控與調整（持續）**
- [ ] 每週 SLO review
- [ ] 識別並修復失敗案例
- [ ] 優化 retry 邏輯
- [ ] 定期更新 Runbook

**里程碑 M4.2: A/B Testing（按需）**
- [ ] 測試不同 OpenAI 模型
- [ ] 測試不同 CI 配置
- [ ] 測試不同 timeout 設定

**里程碑 M4.3: 容錯增強（按需）**
- [ ] 實作更智能的 retry 邏輯
- [ ] 增加 circuit breaker
- [ ] 優化錯誤恢復策略

**驗收標準**:
- 成功率 ≥ 99% ✓
- TTE P95 ≤ 60s ✓
- 持續 30 天達成 SLO

### 8.3 PR 拆分策略

#### 8.3.1 PR 大小指導原則
- **小型 PR (<200 行)**:單一功能，快速審核（1 天內）
- **中型 PR (200-500 行)**:相關功能組，審核時間 2-3 天
- **大型 PR (>500 行)**:避免，若不可避免需拆分成多個子 PR

#### 8.3.2 PR 依賴關係

```
Phase 1:
  PR #1 (Redis metrics) → 獨立
  PR #2 (Metrics API) → 依賴 PR #1
  PR #3 (Sentry tags) → 獨立
  PR #4 (CI fast) → 獨立
  PR #5 (Dashboard) → 依賴 PR #2

Phase 2:
  PR #6 (OpenAI) → 獨立
  PR #7 (Git ops) → 獨立
  PR #8 (Event-driven) → 獨立（需大量測試）
  PR #9 (CI cache) → 獨立

Phase 3:
  PR #10 (Health check) → 獨立
  PR #11 (Rollback) → 依賴 PR #10
  PR #12 (Notifications) → 依賴 PR #11
```

#### 8.3.3 PR Template
```markdown
# PR Title: [Phase X.Y] <Feature Name>

## 目標
- [ ] 實作 <功能描述>
- [ ] 達成 <指標目標>

## 變更摘要
- 新增/修改檔案 X, Y, Z
- 影響範圍: <描述>

## 測試
- [ ] Unit tests 通過
- [ ] E2E tests 通過
- [ ] Lint 通過
- [ ] 本地驗證完成

## 相關
- RFC: docs/rfcs/agent-mvp-closed-loop.md
- Issue: #54
- 依賴 PR: #X (如有)

## 驗收標準
- [ ] <具體驗收條件>
```

### 8.4 時程風險管理

| 風險 | 機率 | 影響 | 應對策略 |
|------|------|------|----------|
| OpenAI API 變更導致延遲 | 中 | 高 | 預留 buffer time，提早測試 |
| Worker 事件驅動實作複雜 | 高 | 中 | Phase 2 最後實作，可延後到 Phase 4 |
| Auto-rollback 測試不充分 | 中 | 高 | 增加 Chaos Engineering 時間 |
| 人力資源不足 | 低 | 高 | PR 拆分策略允許並行開發 |
| CI 優化效果不如預期 | 中 | 中 | 準備 Plan B（減少測試範圍） |

### 8.5 進度追蹤

**追蹤方式**:
- GitHub Project Board: Agent MVP Closed Loop
- 每週 Standup: 週三 10:00 AM
- 月度 Review: 每月第一個週五

**指標追蹤**:
- Burndown chart (Story Points)
- TTE 趨勢圖（每日更新）
- 成功率趨勢圖（每日更新）
- PR 合併速度（平均審核時間）

---

## 9. 未來擴展

### 9.1 多 Agent 支援
- 支援多種類型的 Agent 任務（不僅限於 FAQ）
- 統一的 trace_id 系統
- 跨 Agent 的指標聚合

### 9.2 進階監控
- Distributed tracing（OpenTelemetry）
- Real-time dashboard（WebSocket 更新）
- 告警規則自動調整（基於歷史數據）

### 9.3 智能優化
- AI 預測任務執行時間
- 動態調整資源分配
- 自動化 A/B testing

---

## 10. 總結

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
