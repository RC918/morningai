# Redis 安全要求與 CVE-2025-49844 防護指南

## 概述

本文檔說明 MorningAI 專案的 Redis 安全要求，特別針對 CVE-2025-49844 (RediShell) 漏洞的防護措施。

## CVE-2025-49844 (RediShell) 漏洞說明

### 漏洞詳情

- **CVE 編號**: CVE-2025-49844
- **別名**: RediShell
- **類型**: Use-After-Free (用後釋放) 記憶體破壞缺陷
- **影響範圍**: Redis 所有版本 ≤ 8.2.1
- **修補版本**: Redis 8.2.2+
- **嚴重程度**: 🔴 CRITICAL

### 攻擊方式

攻擊者可透過惡意 Lua 腳本：
1. 操控 Redis 垃圾回收器
2. 觸發用後釋放錯誤
3. 突破 Lua 沙盒
4. 在宿主機執行任意程式碼

### 前提條件

- 攻擊者需要執行 Lua 腳本的權限（`EVAL`/`EVALSHA` 命令）
- 通常為已認證用戶或未設認證的 Redis 實例

## MorningAI 專案的 Redis 使用情況

### 當前配置

**主要方案**: Upstash Redis (HTTPS REST API)
- ✅ 雲端託管，自動安全更新
- ✅ HTTPS/TLS 預設啟用
- ✅ 不受 CVE-2025-49844 影響（供應商負責更新）

**備用方案**: 標準 Redis (TCP)
- ⚠️ 需要手動維護版本
- ⚠️ 需要確保 TLS 啟用
- ⚠️ 可能受 CVE-2025-49844 影響

### 使用場景

- Rate limiting (速率限制)
- Caching (快取)
- Task queue (任務佇列)
- **不使用 Lua 腳本功能**

## 安全要求

### 1. Redis 版本要求

**生產環境**:
- ✅ **推薦**: 使用 Upstash Redis (雲端託管)
- ✅ **自架**: Redis 8.2.2 或更高版本
- ❌ **禁止**: Redis ≤ 8.2.1

**開發環境**:
- ⚠️ 可使用舊版本，但必須：
  - 不暴露於公網
  - 啟用認證 (`requirepass`)
  - 禁用 Lua 腳本（透過 ACL）

### 2. TLS 加密要求

**生產環境**:
- ✅ **必須**: 使用 `rediss://` (TLS 加密)
- ❌ **禁止**: 使用 `redis://` (明文連線)

**開發環境**:
- ⚠️ 可使用 `redis://`，但僅限 localhost

### 3. 認證要求

**所有環境**:
- ✅ **必須**: 啟用 Redis 認證
- ✅ **必須**: 使用強密碼（至少 32 字元）
- ❌ **禁止**: 無認證的 Redis 實例

### 4. 網路隔離要求

**生產環境**:
- ✅ **必須**: Redis 不得直接暴露於公網
- ✅ **必須**: 使用防火牆或 VPC 隔離
- ✅ **必須**: 僅允許應用伺服器訪問

## 實作指南

### 環境變數配置

**推薦配置** (Upstash Redis):
```bash
# Upstash Redis (推薦)
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-secret-token
```

**備用配置** (自架 Redis with TLS):
```bash
# 自架 Redis (必須使用 TLS)
REDIS_URL=rediss://user:password@your-redis-host:6380/0
```

**開發環境** (本地 Redis):
```bash
# 本地開發 (僅限 localhost)
REDIS_URL=redis://localhost:6379/0
```

### Python 客戶端版本

**requirements.txt**:
```python
redis>=5.2.0,<6.0.0
upstash-redis>=1.1.0,<2.0.0
```

**版本說明**:
- `redis>=5.2.0`: 確保客戶端支援最新安全特性
- `<6.0.0`: 鎖定主版本，避免破壞性更新
- `upstash-redis>=1.1.0`: 使用最新 Upstash 客戶端

### 安全檢查功能

專案已內建 Redis 安全檢查功能：

```python
from src.utils.redis_client import check_redis_security

# 檢查 Redis 安全狀態
security_status = check_redis_security()

print(f"Status: {security_status['status']}")
print(f"CVE-2025-49844 Risk: {security_status['cve_2025_49844_risk']}")
print(f"Recommendations: {security_status['recommendations']}")
```

**回傳值範例**:
```python
{
    "status": "secure",
    "type": "upstash",
    "message": "Using Upstash Redis (cloud-managed, auto-updated)",
    "cve_2025_49844_risk": "low",
    "recommendations": []
}
```

## 緊急應變措施

### 如果發現使用舊版 Redis

**立即行動**:
1. ⚠️ **停止暴露於公網** - 立即關閉公網訪問
2. ⚠️ **啟用認證** - 設定 `requirepass`
3. ⚠️ **禁用 Lua 腳本** - 透過 ACL 禁用 `EVAL`/`EVALSHA`

**ACL 配置範例**:
```bash
# 禁用 Lua 腳本命令
ACL SETUSER default -eval -evalsha -script
```

**短期方案**:
- 遷移到 Upstash Redis
- 或升級到 Redis 8.2.2+

### 異常活動檢查

**檢查項目**:
1. 不明 Lua 腳本執行記錄
2. 新增或修改的命令
3. 宿主機意外崩潰
4. 異常網路流量

**檢查命令**:
```bash
# 檢查 Redis 日誌
tail -f /var/log/redis/redis-server.log | grep -i "eval\|script"

# 檢查當前連線
redis-cli CLIENT LIST

# 檢查 Redis 版本
redis-cli INFO server | grep redis_version
```

## 監控與告警

### 建議監控指標

1. **Redis 版本** - 確保 ≥ 8.2.2
2. **TLS 狀態** - 確保使用 `rediss://`
3. **認證狀態** - 確保啟用密碼
4. **Lua 腳本執行** - 監控 `EVAL`/`EVALSHA` 命令（應為 0）
5. **異常連線** - 監控非預期來源的連線

### 告警規則

```yaml
# 範例告警規則 (Prometheus)
- alert: RedisVersionVulnerable
  expr: redis_version < 8.2.2
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Redis version vulnerable to CVE-2025-49844"

- alert: RedisTLSDisabled
  expr: redis_tls_enabled == 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Redis TLS encryption disabled"
```

## 參考資料

### 官方資源

- [Redis Security](https://redis.io/docs/management/security/)
- [Redis ACL](https://redis.io/docs/management/security/acl/)
- [Upstash Security](https://upstash.com/docs/redis/overall/security)

### CVE 資訊

- CVE-2025-49844 (RediShell)
- 影響版本: Redis ≤ 8.2.1
- 修補版本: Redis 8.2.2+

### 內部文檔

- [Redis Client 實作](../handoff/20250928/40_App/api-backend/src/utils/redis_client.py)
- [環境變數配置](.env.example)
- [Redis 配置測試](../handoff/20250928/40_App/api-backend/tests/test_redis_config.py)
- [Redis 安全檢查測試](../handoff/20250928/40_App/api-backend/tests/test_redis_security.py)

## 更新歷史

- **2025-10-24**: 初版發布，針對 CVE-2025-49844 防護
- **2025-10-24**: 新增安全檢查功能 `check_redis_security()`
- **2025-10-24**: 更新 Redis 客戶端版本要求

## 聯絡資訊

如有安全疑慮或發現漏洞，請聯繫：
- **安全團隊**: security@morningai.com
- **CTO**: ryan2939z@gmail.com
