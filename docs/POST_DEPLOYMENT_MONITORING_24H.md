# Post-Deployment Monitoring (24h Observation)

## 概述
PR #723 測試覆蓋率改進合併後的 24 小時觀察計畫。

**合併時間**: 2025-10-24  
**觀察期**: 24 小時（至 2025-10-25）  
**相關 PR**: #723 (測試覆蓋率提升至 75.65%)

## 監控指標

### 1. Sentry 錯誤率監控

#### 認證相關錯誤 (401/403)
**監控原因**: PR #723 新增 22 個 JWT 認證測試，需確認生產環境認證行為正常

**監控項目**:
- `401 Unauthorized` 錯誤率
- `403 Forbidden` 錯誤率
- JWT token 驗證失敗次數
- 中文角色名稱（管理員、分析師）認證成功率

**預期基線**:
- 401 錯誤率: < 5% of total requests
- 403 錯誤率: < 2% of total requests
- JWT 驗證失敗: < 1% of authenticated requests

**異常閾值**:
- 🟡 警告: 401/403 錯誤率增加 > 20%
- 🔴 嚴重: 401/403 錯誤率增加 > 50%

**Sentry 查詢**:
```
# 401 錯誤
http.status_code:401 AND environment:production

# 403 錯誤
http.status_code:403 AND environment:production

# JWT 驗證失敗
message:"JWT*" OR message:"token*" AND level:error
```

#### Rate Limiting 錯誤 (429)
**監控原因**: PR #723 新增 30 個 main.py 測試，包含 rate limiting 測試

**監控項目**:
- `429 Too Many Requests` 錯誤率
- Rate limit header 正確性（X-RateLimit-Limit, Remaining, Reset）
- 誤判率（正常用戶被限流）

**預期基線**:
- 429 錯誤率: < 0.5% of total requests
- Rate limit headers 存在率: 100%

**異常閾值**:
- 🟡 警告: 429 錯誤率 > 1%
- 🔴 嚴重: 429 錯誤率 > 5% 或大量正常用戶被限流

**Sentry 查詢**:
```
http.status_code:429 AND environment:production
```

#### Governance 策略錯誤
**監控原因**: PR #723 修改 policy_guard.py，新增 POLICIES_PATH 環境變數支援

**監控項目**:
- Policy 加載失敗
- YAML 解析錯誤
- 權限檢查失敗
- 風險路由決策錯誤

**預期基線**:
- Policy 加載成功率: 100%
- 權限檢查錯誤: < 0.1%

**異常閾值**:
- 🟡 警告: Policy 加載失敗 > 0 次
- 🔴 嚴重: 權限檢查錯誤率 > 1%

**Sentry 查詢**:
```
message:"policy*" OR message:"governance*" AND level:error
message:"POLICIES_PATH" AND level:warning
```

### 2. API 性能監控 (P95 延遲)

#### 關鍵 API Endpoints
**監控原因**: 確認測試改進未引入性能回退

**監控 Endpoints**:
- `POST /api/faq/search` - FAQ 搜尋（最常用）
- `POST /api/faq` - FAQ 創建（需 admin 權限）
- `PUT /api/faq/{id}` - FAQ 更新（需 admin 權限）
- `DELETE /api/faq/{id}` - FAQ 刪除（需 admin 權限）
- `GET /api/agent/tasks` - Agent 任務列表
- `POST /api/agent/tasks` - Agent 任務創建
- `GET /health` - Health check
- `GET /api/health` - API health check

**預期基線** (P95):
- `/api/faq/search`: < 200ms
- `/api/faq` (POST): < 300ms
- `/api/faq/{id}` (PUT/DELETE): < 250ms
- `/api/agent/tasks` (GET): < 150ms
- `/api/agent/tasks` (POST): < 500ms
- `/health`: < 50ms
- `/api/health`: < 100ms

**異常閾值**:
- 🟡 警告: P95 延遲增加 > 30%
- 🔴 嚴重: P95 延遲增加 > 100% 或 > 1000ms

**監控工具**:
- Vercel Analytics (如果使用 Vercel)
- Sentry Performance Monitoring
- CloudWatch Logs Insights (如果使用 AWS)

**查詢範例** (Sentry):
```
transaction:/api/faq/search AND environment:production
```

### 3. Redis 監控

#### Redis 連接和命中率
**監控原因**: PR #723 新增 17 個 agent 錯誤路徑測試，包含 Redis 失敗處理

**監控項目**:
- Redis 連接成功率
- Cache 命中率
- Rate limiting Redis 操作成功率
- Redis 超時錯誤

**預期基線**:
- Redis 連接成功率: > 99.9%
- Cache 命中率: > 60% (FAQ 搜尋)
- Rate limiting 操作成功率: > 99.5%
- Redis 超時: < 0.1%

**異常閾值**:
- 🟡 警告: 連接成功率 < 99% 或命中率下降 > 20%
- 🔴 嚴重: 連接成功率 < 95% 或大量超時

**監控方式**:
- Redis INFO 命令
- Application logs
- Sentry 錯誤追蹤

**關鍵 Redis 指標**:
```bash
# Redis CLI 查詢
INFO stats
# 關注: keyspace_hits, keyspace_misses, total_connections_received

# Cache 命中率計算
hit_rate = keyspace_hits / (keyspace_hits + keyspace_misses)
```

**Sentry 查詢**:
```
message:"Redis*" AND level:error
message:"redis_client" AND level:warning
```

## 觀察時間表

### 第 1 小時（合併後立即）
- [ ] 檢查 Sentry 是否有新錯誤類型
- [ ] 確認 Redis 連接正常
- [ ] 驗證 rate limiting 正常運作
- [ ] 檢查 API P95 延遲是否正常

### 第 4 小時
- [ ] 檢查 401/403 錯誤率趨勢
- [ ] 檢查 429 錯誤率是否合理
- [ ] 檢查 cache 命中率
- [ ] 檢查 API 性能趨勢

### 第 12 小時
- [ ] 全面檢查所有監控指標
- [ ] 對比合併前後的錯誤率
- [ ] 檢查是否有異常模式
- [ ] 記錄任何需要調整的項目

### 第 24 小時（觀察期結束）
- [ ] 生成完整監控報告
- [ ] 對比所有基線指標
- [ ] 決定是否需要 hotfix
- [ ] 記錄經驗教訓

## 回滾計畫

### 觸發條件
如果出現以下任一情況，考慮回滾：

1. **嚴重錯誤率增加**:
   - 401/403 錯誤率增加 > 50%
   - 429 錯誤率 > 5%
   - Policy 加載失敗導致服務不可用

2. **性能嚴重下降**:
   - 關鍵 API P95 延遲增加 > 100%
   - 任何 API P95 > 1000ms

3. **Redis 問題**:
   - Redis 連接成功率 < 95%
   - 大量 Redis 超時導致服務降級

### 回滾步驟
```bash
# 1. 回滾到合併前的 commit
git revert <merge_commit_hash>

# 2. 創建 hotfix PR
git checkout -b hotfix/revert-coverage-improvements
git push origin hotfix/revert-coverage-improvements

# 3. 快速合併（跳過部分 CI 檢查）
# 需要 admin 權限

# 4. 通知團隊
# 在 Slack/Discord 發布回滾通知
```

## 下一步行動

### 如果觀察期正常
1. ✅ 標記 PR #723 為成功部署
2. 📊 生成監控報告並歸檔
3. 🎯 開始規劃下一批覆蓋率提升（目標 80%）
4. 📝 更新 CONTRIBUTING.md 說明新的覆蓋率要求

### 如果發現問題
1. 🔍 詳細分析問題根因
2. 🐛 創建 bug fix PR
3. 📋 更新測試以覆蓋發現的問題
4. 🔄 重新部署並觀察

## 聯絡人
- **技術負責人**: Ryan Chen (@RC918)
- **Devin Session**: https://app.devin.ai/sessions/438417371dcc4d1f95886422404511ea
- **相關 PR**: #723, #731

## 附錄

### Sentry Dashboard 連結
- [Production Errors](https://sentry.io/organizations/morning-ai/issues/?environment=production)
- [Performance Monitoring](https://sentry.io/organizations/morning-ai/performance/)

### 相關文件
- [TEST_COVERAGE_IMPROVEMENT_REPORT.md](./TEST_COVERAGE_IMPROVEMENT_REPORT.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [PR #723](https://github.com/RC918/morningai/pull/723)
- [PR #731](https://github.com/RC918/morningai/pull/731)
