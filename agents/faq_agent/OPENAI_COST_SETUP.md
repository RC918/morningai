# OpenAI 成本控制設定指南

## 1. OpenAI 控制台月度用量上限設定

登入 [OpenAI Platform](https://platform.openai.com/usage) 並按照以下步驟設定：

### 設定步驟：
1. 進入 **Settings** → **Billing** → **Limits**
2. 設定 **Monthly usage limit** (建議值：$50-$100/月)
3. 啟用 **Usage notifications** (建議在 80% 時發送提醒)
4. 設定 **Hard limit** 以防止超支

### 建議設定：
- **Soft limit**: $50/月 (發送警告但不中斷服務)
- **Hard limit**: $100/月 (達到後立即停止 API 請求)
- **Notification emails**: 在 50%, 80%, 100% 時發送通知

## 2. 環境變數設定

在 staging/production 環境中設定以下環境變數：

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-...

# 每日成本上限 (USD)
OPENAI_MAX_DAILY_COST=10.0

# 每月成本上限 (USD) - 用於監控
OPENAI_MAX_MONTHLY_COST=100.0
```

### 在 Vercel/Render 設定環境變數：

**Vercel:**
```bash
vercel env add OPENAI_MAX_DAILY_COST
# 輸入: 10.0
```

**Render:**
1. 進入 Dashboard → Environment
2. 新增環境變數：
   - Key: `OPENAI_MAX_DAILY_COST`
   - Value: `10.0`

## 3. 成本估算

### Embedding 成本 (text-embedding-3-small)
- **價格**: $0.02 / 1M tokens
- **預估每個 FAQ**: ~100 tokens (問題 + 答案)
- **1000 個 FAQ**: ~0.002 USD
- **100,000 個搜索**: ~0.2 USD

### 每日預算分配 ($10/day)
- FAQ 創建 (500 個/天): $0.001
- FAQ 搜索 (10,000 次/天): $0.02
- 剩餘緩衝: $9.98

### 月度預算分配 ($100/month)
- FAQ 管理: $0.06/月
- FAQ 搜索: $0.60/月
- 總計約: $0.66/月
- **安全餘額**: 99.34% (約 150x 使用量緩衝)

## 4. 監控與警報

### 已實現的成本追蹤
FAQ Agent 內建成本追蹤功能（見 `COST_OPTIMIZATION_GUIDE.md`）：

```python
# 成本追蹤範例
from tools.faq_management_tool import FAQManagementTool

tool = FAQManagementTool()
stats = await tool.get_stats()

# 監控每日成本
daily_cost = stats['embeddings_created'] * 0.00002  # $0.02/1M tokens估算
if daily_cost > float(os.getenv('OPENAI_MAX_DAILY_COST', 10.0)):
    # 發送警報
    logger.error(f"Daily OpenAI cost exceeded: ${daily_cost:.2f}")
```

### 設定警報（建議）

**1. Sentry 整合** (已支援):
```python
import sentry_sdk
sentry_sdk.capture_message(
    f"OpenAI daily cost exceeded: ${daily_cost}",
    level="error"
)
```

**2. Slack 通知** (需自行實現):
```python
# 當成本超過限制時發送 Slack 通知
if daily_cost > max_daily_cost * 0.8:  # 80% 警告
    send_slack_alert(f"⚠️ OpenAI cost at 80%: ${daily_cost}")
```

## 5. 驗收檢查清單

- [ ] OpenAI 控制台設定月度用量上限
- [ ] 設定 soft limit (建議 $50) 和 hard limit (建議 $100)
- [ ] 啟用用量通知 email
- [ ] 在 staging 環境設定 `OPENAI_MAX_DAILY_COST=10.0`
- [ ] 在 production 環境設定 `OPENAI_MAX_DAILY_COST=10.0`
- [ ] 驗證成本追蹤功能正常運作
- [ ] 設定成本超限警報（Sentry/Slack）

## 6. 緊急應對

如果成本意外飆升：

1. **立即行動**:
   ```bash
   # 停用 OpenAI API Key（在 OpenAI 控制台）
   # 或臨時移除環境變數
   unset OPENAI_API_KEY
   ```

2. **檢查原因**:
   ```sql
   -- 查看最近的 FAQ 操作
   SELECT COUNT(*), DATE(created_at) 
   FROM faqs 
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY DATE(created_at);
   
   -- 查看搜索量
   SELECT COUNT(*), DATE(created_at)
   FROM faq_search_history
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY DATE(created_at);
   ```

3. **分析與修復**:
   - 檢查是否有異常批量操作
   - 檢查是否有循環調用或重試風暴
   - 審查成本優化設定（見 `COST_OPTIMIZATION_GUIDE.md`）

## 7. 相關文檔

- [成本優化指南](./COST_OPTIMIZATION_GUIDE.md)
- [部署腳本](./deploy.sh)
- [整合測試報告](./INTEGRATION_TEST_REPORT.md)
