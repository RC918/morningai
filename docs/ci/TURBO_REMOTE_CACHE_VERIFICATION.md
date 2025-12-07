# Turbo Remote Cache 驗證指南

本文件說明如何驗證 Turborepo 遠端快取是否正確運作。

## 前置條件

確認以下 GitHub Secrets 已設定：
- `TURBO_TOKEN`: Vercel 遠端快取認證 token
- `TURBO_TEAM`: Vercel team slug（例如 `morning-ai`）

## 驗證方法

### 方法 1：檢查 CI 日誌

1. 前往 GitHub Actions 執行頁面
2. 選擇 `frontend-ci` 或 `UX Ops Pipeline` workflow
3. 展開 `build` job（或其他使用 turbo 的 job）
4. 在 "Build frontend with Turborepo" 或 "Build application" 步驟中尋找以下訊息：

**成功啟用遠端快取：**
```
Remote caching enabled
```

**快取命中（Cache HIT）：**
```
@morningai/shared-ui:build: cache hit, replaying logs...
frontend-dashboard:build: cache hit, replaying logs...
```

**快取未命中（Cache MISS）：**
```
@morningai/shared-ui:build: cache miss, executing...
frontend-dashboard:build: cache miss, executing...
```

### 方法 2：比較執行時間

1. 記錄首次執行（cache miss）的 build 時間
2. 在不修改程式碼的情況下重新執行 workflow
3. 比較第二次執行（應為 cache hit）的 build 時間
4. 預期 cache hit 時 build 時間應大幅減少（通常 < 5 秒）

### 方法 3：使用 Vercel Dashboard

1. 登入 https://vercel.com
2. 前往 Team Settings > Turborepo
3. 查看 Remote Cache 使用統計
4. 確認有來自 CI 的快取請求

## 常見問題排查

### 問題：沒有看到 "Remote caching enabled"

**可能原因：**
- `TURBO_TOKEN` 或 `TURBO_TEAM` secrets 未設定
- Token 已過期或無效
- Team slug 不正確

**解決方法：**
1. 前往 https://vercel.com/account/tokens 重新生成 token
2. 確認 team slug 與 Vercel dashboard 中顯示的一致
3. 更新 GitHub Secrets

### 問題：一直是 cache miss

**可能原因：**
- 程式碼或依賴有變更
- `turbo.json` 的 `inputs` 或 `outputs` 配置不正確
- 環境變數差異導致快取 key 不同

**解決方法：**
1. 檢查 `turbo.json` 中的 `env` 配置
2. 確認 CI 環境變數與本地一致
3. 使用 `turbo run build --dry` 檢查快取 key

## 適用的 Workflows 和 Jobs

以下 jobs 已配置 Turbo 遠端快取：

| Workflow | Job | 說明 |
|----------|-----|------|
| `frontend.yml` | `build` | 主要前端建構和測試 |
| `ux-pipeline.yml` | `motion-performance-test` | 動效效能測試 |
| `ux-pipeline.yml` | `accessibility-audit` | 無障礙審計 |

## 相關文件

- [ADR-001: 遷移到 pnpm + Turborepo](../adr/001-pnpm-turborepo-migration.md)
- [Turborepo Remote Caching 官方文件](https://turbo.build/repo/docs/core-concepts/remote-caching)
