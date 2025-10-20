# FAQ Agent 成本優化指南

## 概述

本指南說明如何優化 FAQ Agent 的 OpenAI Embedding API 成本。

## 成本結構

### OpenAI Embedding 定價 (2024)

| 模型 | 每百萬 Tokens 價格 | 建議用途 |
|------|------------------|---------|
| text-embedding-3-small | $0.02 | 一般用途，成本最低 |
| text-embedding-3-large | $0.13 | 高精度需求 |
| text-embedding-ada-002 | $0.10 | 舊版模型 |

### 預估成本

假設平均每個問題 ~50 tokens (200 字元):
- 1000 個 FAQ: ~$0.001 (使用 text-embedding-3-small)
- 10000 個搜索請求/天: ~$0.01
- **預估月成本**: ~$0.30-$5.00 (取決於使用量)

## 優化策略

### 1. 使用最經濟的模型

```python
# 優先使用 text-embedding-3-small (便宜 6.5 倍)
from tools.embedding_tool import EmbeddingTool

tool = EmbeddingTool(model="text-embedding-3-small")
```

### 2. 實施緩存層

#### 選項 A: Redis 緩存 (推薦用於生產環境)

```python
import redis.asyncio as redis

# 連接 Redis
redis_client = redis.from_url(os.getenv('REDIS_URL'))

# 緩存 embedding 7 天
cache_key = f"emb:{hash(question)}"
cached = await redis_client.get(cache_key)

if cached:
    embedding = json.loads(cached)
else:
    result = await tool.generate_embedding(question)
    await redis_client.setex(cache_key, 86400 * 7, json.dumps(result['embedding']))
```

**節省**: 重複查詢可節省 90-95% 成本

#### 選項 B: PostgreSQL 緩存

```sql
-- 在 faqs 表中已經儲存 embedding
-- 只需在創建/更新時生成一次
-- 搜索時直接使用現有 embedding，無需重新生成
```

### 3. 批次處理

```python
# 一次處理多個問題（最多 2048 個）
questions = [...]  # 大量問題
result = await tool.generate_embeddings_batch(questions, batch_size=100)
```

**節省**: 減少 API 請求次數，降低延遲

### 4. 設定成本上限

```python
class CostLimiter:
    def __init__(self, max_daily_cost=10.0):
        self.max_daily_cost = max_daily_cost
        self.daily_cost = 0.0
    
    def estimate_cost(self, text, model="text-embedding-3-small"):
        tokens = len(text) / 4  # 粗略估計
        return tokens * 0.00002 / 1000
    
    def can_proceed(self, estimated_cost):
        return (self.daily_cost + estimated_cost) <= self.max_daily_cost
```

### 5. 率限制 (Rate Limiting)

```python
import asyncio
from datetime import datetime

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.rpm = requests_per_minute
        self.requests = []
    
    async def acquire(self):
        now = datetime.now()
        # 移除 1 分鐘前的請求
        self.requests = [r for r in self.requests 
                        if (now - r).seconds < 60]
        
        if len(self.requests) >= self.rpm:
            await asyncio.sleep(1)
            return await self.acquire()
        
        self.requests.append(now)
```

## 最佳實踐

### ✅ 推薦做法

1. **FAQ 創建時生成 embedding，搜索時重用**
   - FAQ 數量固定，只需生成一次
   - 每次搜索只需生成查詢的 embedding

2. **使用 Redis 緩存常見查詢**
   - 熱門問題的 embedding 可重用
   - TTL 設為 7 天平衡成本與新鮮度

3. **批次導入 FAQ**
   - 使用 `bulk_create_faqs()` 而非逐個創建
   - 減少 API 往返次數

4. **監控成本**
   ```python
   # 記錄每次 API 調用
   logging.info(f"Embedding cost: ${cost:.6f}, Daily total: ${daily_total:.2f}")
   ```

### ❌ 避免做法

1. **不要每次搜索都重新生成 FAQ embeddings**
   - FAQ 已存儲在數據庫中，直接使用

2. **不要使用過大的模型**
   - text-embedding-3-small 對大多數用例已足夠

3. **不要在沒有緩存的情況下處理重複查詢**

## 實際應用範例

### 場景 1: 初次導入 100 個 FAQ

```python
# 成本估算
average_tokens = 50
cost_per_faq = 50 * 0.00002 / 1000 = $0.000001
total_cost = 100 * $0.000001 = $0.0001
```

**預估**: $0.0001 (不到 1 美分)

### 場景 2: 每天 10000 次搜索

```python
# 假設 50% 查詢可從緩存獲得
unique_queries = 5000
cost_per_query = 50 * 0.00002 / 1000 = $0.000001
daily_cost = 5000 * $0.000001 = $0.005
monthly_cost = $0.005 * 30 = $0.15
```

**預估**: $0.15/月 (有緩存)
**無緩存**: $0.30/月

### 場景 3: 批量更新 1000 個 FAQ

```python
# 使用批次處理
batch_size = 100
batches = 10
total_tokens = 1000 * 50 = 50000
cost = 50000 * 0.00002 / 1000 = $0.001
```

**預估**: $0.001 (不到 1 美分)

## 成本監控儀表板

建議在應用中加入成本追蹤:

```python
async def get_cost_stats():
    stats = {
        'today_cost': daily_cost,
        'month_cost': monthly_cost,
        'cache_hit_rate': cache_hits / total_requests,
        'avg_cost_per_request': daily_cost / request_count,
        'projected_monthly': daily_cost * 30
    }
    return stats
```

## 總結

對於大多數用戶，FAQ Agent 的成本是**微不足道的**（每月 < $5）。關鍵優化措施:

1. ✅ 使用 `text-embedding-3-small`
2. ✅ FAQ embedding 只生成一次並儲存
3. ✅ 搜索查詢使用 Redis 緩存
4. ✅ 批次處理大量操作
5. ✅ 設置每日成本上限作為安全措施

**是的，用戶用多少就需要付多少**，但通過上述優化，實際成本非常低。對於典型使用場景（數百個 FAQ，數千次日搜索），月成本通常在 $0.50-$5.00 之間。
