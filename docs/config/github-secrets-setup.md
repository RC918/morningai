# GitHub Secrets 配置指南

## 概述
env-diagnose workflow 需要以下 GitHub Secrets 才能正常運作。本文件說明如何配置這些 secrets。

## 如何添加 GitHub Secret

1. 前往 GitHub repository: https://github.com/RC918/morningai
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **New repository secret**
4. 輸入 Name 和 Value
5. 點擊 **Add secret**

## 必需的 Secrets

### 1. REDIS_URL (必需)
**用途**: Redis TCP 連線測試

**格式**: `rediss://default:密碼@主機:端口`

**取得方式**:
- 從 Render Dashboard 複製 `morningai-backend-v2` 或 `morningai-agent-worker` 服務的 REDIS_URL
- 或從 Upstash Dashboard 複製

**範例**:
```
rediss://default:AbcD1234XyZ@redis-12345.upstash.io:6379
```

### 2. UPSTASH_REDIS_REST_URL (可選)
**用途**: Redis REST API 測試

**格式**: `https://主機`

**範例**:
```
https://redis-12345.upstash.io
```

### 3. UPSTASH_REDIS_REST_TOKEN (可選)
**用途**: Redis REST API 認證

**格式**: Token 字串

### 4. SUPABASE_URL (必需)
**用途**: Supabase 資料庫連線測試

**格式**: `https://專案ID.supabase.co`

### 5. SUPABASE_SERVICE_ROLE_KEY (必需)
**用途**: Supabase 服務角色認證

### 6. CLOUDFLARE_API_TOKEN (可選)
**用途**: Cloudflare API 測試

### 7. CLOUDFLARE_ZONE_ID (可選)
**用途**: Cloudflare Zone ID

### 8. VERCEL_TOKEN (可選)
**用途**: Vercel 部署 API 測試

### 9. VERCEL_ORG_ID (可選)
**用途**: Vercel 組織 ID

### 10. RENDER_API_KEY (可選)
**用途**: Render 服務 API 測試

### 11. SENTRY_DSN (可選)
**用途**: Sentry 錯誤監控配置

## 測試配置

配置完成後，測試 env-diagnose workflow:

```bash
# 手動觸發 workflow
gh workflow run env-diagnose.yml

# 查看執行結果
gh run list --workflow=env-diagnose.yml --limit 1

# 查看詳細日誌
gh run view --log
```

## 錯誤處理

workflow 現在具有優雅的錯誤處理：
- ✅ **已配置且連線成功**: 顯示綠色成功訊息
- ⚠️ **未配置**: 顯示警告但不會失敗（exit 0）
- ❌ **已配置但連線失敗**: 顯示紅色錯誤訊息並失敗（exit 1）

## 安全注意事項

⚠️ **絕對不要**將 secrets 提交到 git repository
⚠️ **絕對不要**在公開的 Issues 或 PRs 中分享 secrets
✅ **務必**定期輪換 API keys 和 tokens
✅ **務必**使用最小權限原則配置 secrets

## 相關文件

- [env-diagnose workflow](.github/workflows/env-diagnose.yml)
- [Environment Variables Schema](env_schema.yaml)
- [Render Deployment Guide](../sandbox/render-deployment.md)
