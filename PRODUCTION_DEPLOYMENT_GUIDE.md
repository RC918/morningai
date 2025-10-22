# Production Deployment Guide - Ops Agent Worker

## 概述

本指南提供 Ops Agent Worker 生產環境部署的完整流程，包含回滾策略、安全檢查清單和緊急應變程序。

## 部署前檢查清單

### 1. 程式碼品質檢查

- [ ] 所有測試通過 (pytest agents/ops_agent/tests/)
- [ ] 程式碼覆蓋率 ≥ 80%
- [ ] 無 linting 錯誤 (ruff check)
- [ ] 無 type checking 錯誤 (mypy)
- [ ] 所有 PR 已合併到 main 分支
- [ ] CI/CD pipeline 全部通過

### 2. 環境變數配置

確認以下環境變數已在 Render 配置：

```bash
# 必需環境變數
REDIS_URL=redis://...
VERCEL_TOKEN=...
VERCEL_TEAM_ID=...

# 可選環境變數
WORKER_POLL_INTERVAL=5
LOG_LEVEL=INFO
SENTRY_DSN=...
```

### 3. 依賴檢查

- [ ] Redis 服務正常運行
- [ ] Orchestrator API 可訪問
- [ ] Vercel API 可訪問
- [ ] 所有 Python 依賴已安裝

### 4. 監控配置

- [ ] Sentry 錯誤追蹤已配置
- [ ] Render 日誌已啟用
- [ ] Slack 告警已配置
- [ ] UptimeRobot 監控已設置

## 回滾策略

### 方法 1: Git Tag 回滾 (推薦)

#### 部署前創建穩定版本標籤

```bash
# 1. 確認當前版本穩定
cd /home/ubuntu/repos/morningai
git status
git log --oneline -5

# 2. 創建版本標籤
VERSION="v1.0.0-stable-$(date +%Y%m%d)"
git tag -a "$VERSION" -m "Stable version before Ops Agent Worker deployment"
git push origin "$VERSION"

# 3. 記錄當前 commit hash
STABLE_COMMIT=$(git rev-parse HEAD)
echo "Stable commit: $STABLE_COMMIT" > /tmp/deployment_backup.txt
echo "Tag: $VERSION" >> /tmp/deployment_backup.txt
```

#### 回滾到穩定版本

```bash
# 1. 查看可用標籤
git tag -l "v*-stable-*"

# 2. 回滾到指定標籤
git checkout tags/v1.0.0-stable-20251022

# 3. 創建回滾分支
git checkout -b rollback/ops-agent-worker-$(date +%Y%m%d)

# 4. 推送到遠端
git push origin rollback/ops-agent-worker-$(date +%Y%m%d)

# 5. 在 Render 重新部署
# 手動觸發部署或等待自動部署
```

### 方法 2: Render 部署歷史回滾

1. 登入 Render Dashboard
2. 選擇 `morningai-orchestrator-api` 服務
3. 進入 "Deploys" 頁面
4. 找到上一個穩定的部署
5. 點擊 "Redeploy" 按鈕

### 方法 3: 緊急停止 Worker

如果需要立即停止 Worker 而不回滾整個系統：

```bash
# 使用 Dashboard API
curl -X POST http://localhost:8080/api/worker/stop

# 或直接在 Render 停止服務
# Dashboard > Service > Manual Deploy > Stop
```

## 部署流程

### 階段 1: 預生產測試 (Staging)

```bash
# 1. 在本地環境測試
cd /home/ubuntu/repos/morningai

# 2. 啟動 Redis (如果尚未運行)
docker run -d -p 6379:6379 --name redis-staging redis:alpine

# 3. 啟動 Worker
cd agents/ops_agent
python worker.py

# 4. 運行 E2E 測試
cd /home/ubuntu/repos/morningai
python examples/e2e_bug_fix_scenario.py

# 5. 驗證結果
# - 檢查任務是否正確處理
# - 檢查事件是否正確發布
# - 檢查日誌無錯誤
```

### 階段 2: 創建穩定版本標籤

```bash
# 創建部署前備份點
VERSION="v1.0.0-stable-$(date +%Y%m%d-%H%M)"
git tag -a "$VERSION" -m "Stable version before production deployment"
git push origin "$VERSION"

# 記錄部署信息
cat > /tmp/deployment_info.txt <<EOF
Deployment Date: $(date)
Version: $VERSION
Commit: $(git rev-parse HEAD)
Branch: $(git branch --show-current)
Deployed By: $(git config user.name)
EOF
```

### 階段 3: 部署到生產環境

```bash
# 1. 合併到 main 分支
git checkout main
git pull origin main
git merge --no-ff feature/ops-agent-worker
git push origin main

# 2. 等待 CI/CD 完成
# 監控 GitHub Actions 或 Render 自動部署

# 3. 驗證部署
curl https://morningai-orchestrator-api.onrender.com/health
```

### 階段 4: 生產環境驗證

```bash
# 1. 檢查 Worker 狀態
curl https://morningai-orchestrator-api.onrender.com/api/worker/status

# 2. 提交測試任務
curl -X POST https://morningai-orchestrator-api.onrender.com/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "deployment",
    "payload": {"service": "test"},
    "priority": "P2"
  }'

# 3. 監控任務執行
# 使用 Dashboard: http://localhost:8080
# 或查看 Render 日誌

# 4. 驗證成功標準
# - 任務狀態變為 "completed"
# - 無錯誤日誌
# - Worker CPU/Memory 正常
# - Queue 深度正常
```

## 監控與告警

### 關鍵指標

1. **Worker 健康狀態**
   - Status: running/stopped/error
   - CPU 使用率 < 80%
   - Memory 使用率 < 80%
   - Uptime > 99%

2. **Queue 指標**
   - Pending tasks < 100
   - Processing tasks < 10
   - Task processing time < 5 minutes

3. **錯誤率**
   - Failed tasks < 5%
   - Redis connection errors = 0
   - Vercel API errors < 1%

### 告警配置

```yaml
# Render 告警規則
alerts:
  - name: Worker Down
    condition: status != "running"
    action: slack_notification
    
  - name: High Queue Depth
    condition: pending_tasks > 100
    action: slack_notification
    
  - name: High Error Rate
    condition: error_rate > 5%
    action: pagerduty_alert
```

## 緊急應變程序

### 情境 1: Worker 崩潰

```bash
# 1. 立即檢查日誌
# Render Dashboard > Logs

# 2. 嘗試重啟
curl -X POST http://localhost:8080/api/worker/restart

# 3. 如果重啟失敗，回滾
git checkout tags/v1.0.0-stable-YYYYMMDD
git push origin main --force  # 僅在緊急情況使用
```

### 情境 2: Redis 連接失敗

```bash
# 1. 檢查 Redis 服務狀態
curl https://morningai-orchestrator-api.onrender.com/health

# 2. 檢查 REDIS_URL 環境變數
# Render Dashboard > Environment Variables

# 3. 重啟 Redis 服務 (如果自託管)
docker restart redis

# 4. 重啟 Worker
curl -X POST http://localhost:8080/api/worker/restart
```

### 情境 3: 任務處理緩慢

```bash
# 1. 檢查 Queue 深度
curl https://morningai-orchestrator-api.onrender.com/stats

# 2. 檢查 Worker 資源使用
curl http://localhost:8080/api/worker/status

# 3. 考慮擴展 Worker 數量
# Render Dashboard > Scaling > Increase instances

# 4. 暫時停止低優先級任務
# 使用 Dashboard 手動管理
```

### 情境 4: Vercel API 錯誤

```bash
# 1. 檢查 Vercel Token 有效性
curl -H "Authorization: Bearer $VERCEL_TOKEN" \
  https://api.vercel.com/v2/user

# 2. 檢查 Rate Limiting
# Vercel Dashboard > Settings > Rate Limits

# 3. 如果 Token 過期，更新環境變數
# Render Dashboard > Environment Variables > VERCEL_TOKEN

# 4. 重啟 Worker
curl -X POST http://localhost:8080/api/worker/restart
```

## 回滾決策矩陣

| 問題嚴重程度 | 影響範圍 | 建議行動 | 回滾方法 |
|------------|---------|---------|---------|
| P0 - 嚴重 | 全系統 | 立即回滾 | Git Tag 回滾 |
| P1 - 高 | 單一功能 | 嘗試修復，30分鐘內回滾 | Render 部署歷史 |
| P2 - 中 | 部分功能 | 監控並修復 | 不需要回滾 |
| P3 - 低 | 輕微影響 | 計劃修復 | 不需要回滾 |

## 部署後檢查清單

- [ ] Worker 狀態為 "running"
- [ ] 測試任務成功完成
- [ ] 無錯誤日誌
- [ ] Queue 深度正常
- [ ] CPU/Memory 使用正常
- [ ] 告警系統正常
- [ ] Dashboard 可訪問
- [ ] 文檔已更新
- [ ] 團隊已通知

## 資料備份

### Redis 資料備份

```bash
# 1. 創建 Redis 快照
redis-cli BGSAVE

# 2. 下載備份檔案
# 位置: /var/lib/redis/dump.rdb

# 3. 上傳到 S3 或其他儲存
aws s3 cp /var/lib/redis/dump.rdb \
  s3://morningai-backups/redis/dump-$(date +%Y%m%d-%H%M).rdb
```

### 配置備份

```bash
# 備份所有環境變數
cat > /tmp/env_backup_$(date +%Y%m%d).txt <<EOF
REDIS_URL=$REDIS_URL
VERCEL_TOKEN=***REDACTED***
VERCEL_TEAM_ID=$VERCEL_TEAM_ID
WORKER_POLL_INTERVAL=$WORKER_POLL_INTERVAL
EOF

# 備份 render.yaml
cp render.yaml /tmp/render_backup_$(date +%Y%m%d).yaml
```

## 效能優化建議

### 1. Worker 擴展

```yaml
# render.yaml
services:
  - type: worker
    name: morningai-ops-agent-worker
    scaling:
      minInstances: 1
      maxInstances: 5
      targetCPUPercent: 70
```

### 2. Redis 優化

```bash
# Redis 配置優化
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. 任務優先級

```python
# 調整任務優先級處理順序
PRIORITY_ORDER = ["P0", "P1", "P2", "P3"]
```

## 聯絡資訊

### 緊急聯絡

- **CTO**: Ryan Chen (ryan2939z@gmail.com)
- **Slack Channel**: #ops-agent-alerts
- **PagerDuty**: https://morningai.pagerduty.com

### 資源連結

- **Render Dashboard**: https://dashboard.render.com
- **Orchestrator API**: https://morningai-orchestrator-api.onrender.com
- **Worker Dashboard**: http://localhost:8080
- **GitHub Repo**: https://github.com/RC918/morningai
- **Sentry**: https://sentry.io/morningai

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|-----|------|---------|------|
| 1.0.0 | 2025-10-22 | 初始版本 | Devin AI |

## 附錄

### A. 常用命令速查

```bash
# 檢查 Worker 狀態
curl http://localhost:8080/api/worker/status

# 啟動 Worker
curl -X POST http://localhost:8080/api/worker/start \
  -H "Content-Type: application/json" \
  -d '{"config": {...}}'

# 停止 Worker
curl -X POST http://localhost:8080/api/worker/stop

# 重啟 Worker
curl -X POST http://localhost:8080/api/worker/restart

# 查看 Queue 統計
curl http://localhost:8080/api/queue/stats

# 查看最近任務
curl http://localhost:8080/api/tasks/recent?limit=10
```

### B. 故障排除指南

詳見 `agents/ops_agent/WORKER_INTEGRATION_GUIDE.md` 的 Troubleshooting 章節。

### C. 測試腳本

詳見 `agents/ops_agent/tests/` 目錄。
