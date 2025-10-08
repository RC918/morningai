# Sentry Alert Rules（Issue #80）

## Phase 10 Update: Production Environment Filtering (Issue #166)

**狀態**: ✅ 已更新 (2025-10-07)

所有告警規則已更新為僅監控 `environment:production`，以減少來自 dev/staging 環境的雜訊。

### 已更新規則 (env=production)
- **Frontend Error Alert**: https://sentry.io/organizations/morningai-core/alerts/rules/16293151/
  - 條件: `environment equals production` ✅
  - 閾值: ≥1 error in 5 minutes
- **React Error Alert**: https://sentry.io/organizations/morningai-core/alerts/rules/16330925/
  - 條件: `environment equals production` ✅
  - 閾值: ≥1 error in 5 minutes
- **Backend Error Alert**: https://sentry.io/organizations/morningai-core/alerts/rules/16341755/
  - 條件: `environment equals production` ✅
  - 閾值: >10 errors in 5 minutes

### 手動更新步驟（如需要）
1. 登入 Sentry → Alerts → Rules
2. 編輯每個規則 (Frontend/React/Backend)
3. 新增條件: **IF** `environment` equals `production`
4. 儲存規則
5. 在規則詳情頁面確認

---

## Web Error Alert（必備）
- **範圍**: `environment:production`
- **條件**: 同一錯誤（相同 issue）
- **閾值**: 5 分鐘內 > 10 次
- **動作**: Slack #oncall / Email 通知
- **過濾**: 排除 400/404 錯誤（已在程式碼中透過 `before_send` 過濾）

## Worker Job Failure Alert（必備）
- **範圍**: `environment:production`
- **條件**: Job 失敗事件
- **閾值**: 連續 3 次失敗
- **動作**: Slack #oncall / Email 通知
- **標籤**: `worker:true` 或依實際 RQ worker 標記

---

## 配置方式

### 方式一：Sentry API 自動化腳本

使用 `scripts/configure_sentry_alerts.py` 腳本自動建立告警規則：

```bash
# 設定環境變數
export SENTRY_AUTH_TOKEN="your-sentry-auth-token"
export SENTRY_ORG_SLUG="your-org-slug"
export SENTRY_PROJECT_SLUG="morningai"
export SLACK_WEBHOOK_URL="your-slack-webhook-url"

# 執行腳本（乾跑模式）
python scripts/configure_sentry_alerts.py --dry-run

# 實際建立規則
python scripts/configure_sentry_alerts.py
```

### 方式二：Sentry 後台手動配置

#### 1. Web Error Alert 配置步驟

1. 登入 Sentry → 選擇專案 `morningai`
2. 前往 **Alerts** → **Create Alert Rule**
3. 選擇 **Issues**
4. 配置條件：
   - **WHEN**: An issue is seen
   - **IF**: `event.count` > 10 in 5 minutes
   - **AND**: `environment` equals `production`
   - **THEN**: Send a notification to Slack (#oncall) and Email
5. 過濾條件：
   - 排除 `http.status_code` equals `400`
   - 排除 `http.status_code` equals `404`
   - （註：這些已在程式碼 `before_send` 處理，此處為雙重保險）
6. 儲存規則，命名為：**Web - High Frequency Errors**

#### 2. Worker Job Failure Alert 配置步驟

1. Sentry → **Alerts** → **Create Alert Rule**
2. 選擇 **Issues**
3. 配置條件：
   - **WHEN**: An issue is seen
   - **IF**: `event.count` >= 3 in 15 minutes（允許一定時間窗口）
   - **AND**: `environment` equals `production`
   - **AND**: `tags.worker` equals `true`（或依實際標記）
4. **THEN**: Send a notification to Slack (#oncall) and Email
5. 儲存規則，命名為：**Worker - Job Failures**

---

## 配置完成後

請回填以下資訊：

- **Web Error Rule URL**: _待填入 Sentry 規則連結_
- **Worker Failure Rule URL**: _待填入 Sentry 規則連結_
- **通知管道**: 
  - Slack: #oncall
  - Email: oncall@example.com（待填入實際信箱）

---

## 測試驗證

### 測試 Web Error Alert

```bash
# 觸發 10+ 個相同錯誤
for i in {1..12}; do
  curl -X POST https://morningai-backend-v2.onrender.com/api/test/trigger-error
  sleep 2
done
```

### 測試 Worker Failure Alert

```python
# 在 worker 中手動觸發 3 次連續失敗
from rq import Queue
from redis import Redis

redis_conn = Redis.from_url(os.getenv("REDIS_URL"))
q = Queue("orchestrator", connection=redis_conn)

for i in range(3):
    q.enqueue('worker.failing_task', job_id=f'test-fail-{i}')
```

---

## 參考文件

- [Sentry Alerts Documentation](https://docs.sentry.io/product/alerts/)
- [Sentry API - Alert Rules](https://docs.sentry.io/api/alerts/)


## Backend 規則（回填）
- Error Rule URL: https://sentry.io/organizations/morningai-core/alerts/rules/16341755/
- 通知管道: Email / Slack #oncall


## Sentry 規則回填（2025-10-07）
- Frontend Error Rule URL: https://sentry.io/organizations/morningai-core/alerts/rules/16293151/
- React Error Rule URL:    https://sentry.io/organizations/morningai-core/alerts/rules/16330925/
- Backend Error Rule URL:  https://sentry.io/organizations/morningai-core/alerts/rules/16341755/
- 通知管道: Email / Slack #oncall
