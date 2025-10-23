# Lighthouse CI 效能監控系統使用指南

## 概述

Lighthouse CI 是一個自動化效能測試系統，在每個 Pull Request 和 main 分支合併時自動執行 Lighthouse 測試，提供效能指標對比和趨勢追蹤。

## 目標

1. **可觀測** - 將「感覺變慢」轉化為數據 (TTI, LCP, CLS, TBT, FCP)
2. **可追溯** - 逐 commit delta (↑/↓) 直接顯示在 PR 評論
3. **可守門** - 效能閾值退步時 fail CI，避免慢頁面合併
4. **可分析** - 生成 trend.csv 供長期趨勢觀察

## 系統架構

### Phase 1: 基礎版 (已實作)

**PR 階段** - 快速反饋：
- 測試公開頁面：`/`, `/login`, `/pricing`
- 執行次數：1 次 (約 2-3 分鐘)
- 路徑過濾：只在 `frontend-dashboard-deploy/**` 變更時觸發
- 自動評論：在 PR 顯示效能對比與 delta

**main 階段** - 精準基線：
- 測試公開頁面（同上）
- 執行次數：3 次（取中位數）
- 自動更新：`.lhci-baseline.json` 與 `trend.csv`
- 自動提交：基線變更自動 commit

### Phase 2: Playwright 認證整合 (選配)

**啟用條件**：
- 設定環境變數 `USE_PLAYWRIGHT_AUTH=1`
- 提供測試帳號 credentials

**額外測試頁面**：
- `/dashboard` (需認證)
- `/settings` (需認證)

## 配置檔案

### `lighthouserc.json` (PR 版本)

```json
{
  "ci": {
    "collect": {
      "url": ["/", "/login", "/pricing"],
      "numberOfRuns": 1,
      "startServerCommand": "cd frontend-dashboard-deploy && pnpm preview --port 4173",
      "settings": {
        "preset": "desktop",
        "formFactor": "desktop",
        "throttlingMethod": "simulate"
      }
    },
    "assert": {
      "assertions": {
        "categories:performance": ["warn", {"minScore": 0.90}],
        "largest-contentful-paint": ["error", {"maxNumericValue": 3000}],
        "total-blocking-time": ["error", {"maxNumericValue": 300}],
        "cumulative-layout-shift": ["error", {"maxNumericValue": 0.1}]
      }
    }
  }
}
```

### `lighthouserc.main.json` (main 版本)

與 PR 版本相同，但：
- `numberOfRuns: 3` (取中位數)
- 可選包含認證頁面
- 使用 `aggregationMethod: "median"`

## 效能閾值

| 指標 | 閾值 | 級別 | 說明 |
|-----|------|------|------|
| Performance Score | ≥ 90% | warn | 整體效能分數 |
| Largest Contentful Paint (LCP) | ≤ 3000ms | error | 最大內容繪製時間 |
| Total Blocking Time (TBT) | ≤ 300ms | error | 總阻塞時間 |
| Cumulative Layout Shift (CLS) | ≤ 0.1 | error | 累積版面配置位移 |
| First Contentful Paint (FCP) | ≤ 2000ms | warn | 首次內容繪製時間 |

**容差範圍**：±5%

## 使用方式

### 1. 開發者工作流程

#### 提交 PR 時

1. 修改 `frontend-dashboard-deploy/` 下的檔案
2. 推送到 GitHub
3. GitHub Actions 自動執行 Lighthouse CI
4. 等待 2-3 分鐘
5. 查看 PR 評論中的效能報告

#### 解讀 PR 評論

```markdown
### 📈 Lighthouse CI 效能報告

#### 效能對比 (本次 vs 基線)

- 🟢 **Largest Contentful Paint (LCP)**: 2.34s (Δ -0.12s, -4.9%)
- 🟢 **Total Blocking Time (TBT)**: 180ms (Δ -20ms, -10.0%)
- 🔻 **Time to Interactive (TTI)**: 3.45s (Δ +0.15s, +4.5%)
- 🟢 **Cumulative Layout Shift (CLS)**: 0.08 (Δ -0.01, -11.1%)
- 🟢 **First Contentful Paint (FCP)**: 1.23s (Δ -0.05s, -3.9%)

⚠️ **效能警告**

以下指標退步超過 5%，請檢查是否需要優化：

- **Time to Interactive (TTI)** 增加了 4.5%
```

**圖示說明**：
- 🟢 改善或在容差範圍內
- 🔻 退步超過 5%

#### 效能退步時的處理

如果看到 🔻 警告：

1. **檢查變更**：
   - 是否新增了大型資源（圖片、字型、第三方腳本）？
   - 是否引入了新的依賴套件？
   - 是否修改了關鍵渲染路徑？

2. **本地分析**：
   ```bash
   cd frontend-dashboard-deploy
   pnpm build
   pnpm preview
   # 開啟 Chrome DevTools > Performance 面板分析
   ```

3. **優化建議**：
   - 壓縮圖片（使用 WebP 格式）
   - 使用 code splitting 或 lazy loading
   - 延遲載入非關鍵資源
   - 優化 CSS 和 JavaScript

4. **豁免說明**：
   如果效能退步是預期的（例如新增重要功能），請在 PR 描述中說明原因。

### 2. 本地測試

#### 執行 Lighthouse CI

```bash
cd frontend-dashboard-deploy

# 1. 建置應用
pnpm build

# 2. 啟動預覽伺服器（背景執行）
pnpm preview --port 4173 &

# 3. 執行 Lighthouse CI
pnpm lhci

# 4. 查看報告
ls -la .lhci/
```

#### 生成 PR 評論預覽

```bash
cd frontend-dashboard-deploy
pnpm lhci:pr-comment
cat .lhci-diff.md
```

### 3. 查看趨勢數據

#### 趨勢 CSV 格式

```csv
timestamp,lcp_ms,tbt_ms,tti_ms,cls,fcp_ms
2025-10-22T10:00:00Z,2340,180,3450,0.08,1230
2025-10-22T14:30:00Z,2450,200,3600,0.09,1280
```

#### 使用 Excel/Google Sheets 分析

1. 下載 `trend.csv`
2. 匯入到試算表
3. 建立折線圖追蹤效能趨勢

#### 使用 Python 分析

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('trend.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['lcp_ms'], label='LCP')
plt.plot(df['timestamp'], df['tti_ms'], label='TTI')
plt.xlabel('Date')
plt.ylabel('Time (ms)')
plt.title('Performance Trends')
plt.legend()
plt.show()
```

## Phase 2: Playwright 認證整合

### 啟用步驟

#### 1. 設定 GitHub Secrets

在 GitHub repo 設定以下 secrets：

- `SUPABASE_TEST_URL` - 測試環境 Supabase URL
- `SUPABASE_TEST_KEY` - 測試環境 Supabase anon key
- `TEST_EMAIL` - 測試帳號 email
- `TEST_PASSWORD` - 測試帳號密碼

#### 2. 啟用 Playwright 認證

在 GitHub Actions workflow 中設定環境變數：

```yaml
env:
  USE_PLAYWRIGHT_AUTH: '1'
```

#### 3. 測試帳號準備

確保測試帳號：
- 已在 Supabase 註冊
- 有足夠權限訪問 `/dashboard` 和 `/settings`
- 不會被自動登出（session 有效期足夠長）

### 本地測試 Playwright 認證

```bash
cd frontend-dashboard-deploy

# 1. 設定環境變數
export VITE_SUPABASE_URL="your-test-url"
export VITE_SUPABASE_ANON_KEY="your-test-key"
export TEST_EMAIL="test@example.com"
export TEST_PASSWORD="test-password"

# 2. 安裝 Playwright
pnpm dlx playwright install --with-deps chromium

# 3. 執行認證測試
pnpm dlx playwright test tests/auth.setup.spec.ts

# 4. 檢查 session 是否儲存
ls -la playwright/.auth/storageState.json

# 5. 轉換 cookies
node ../scripts/make-lhci-cookie.js

# 6. 檢查 headers
cat ../LHCI_EXTRA_HEADERS.json

# 7. 執行 Lighthouse CI (含認證頁面)
pnpm lhci:main
```

## 疑難排解

### 問題 1: Lighthouse CI 執行失敗

**症狀**：GitHub Actions 顯示 "No LHCI reports found"

**解決方案**：
1. 檢查 `pnpm build` 是否成功
2. 檢查 `pnpm preview` 是否正常啟動
3. 檢查 port 4173 是否被佔用

### 問題 2: PR 評論未顯示

**症狀**：PR 沒有 Lighthouse CI 評論

**解決方案**：
1. 檢查 GitHub Actions 權限（需要 `pull-requests: write`）
2. 檢查 workflow 是否被路徑過濾排除
3. 檢查 `make-lhci-pr-comment.js` 是否執行成功

### 問題 3: 效能分數波動大

**症狀**：相同代碼的效能分數差異 >10%

**解決方案**：
1. 確認使用 `throttlingMethod: "simulate"`
2. 確認 main 分支使用 `numberOfRuns: 3`
3. 檢查 CI runner 是否資源不足

### 問題 4: Playwright 認證失敗

**症狀**：`auth.setup.spec.ts` 測試失敗

**解決方案**：
1. 檢查測試帳號是否有效
2. 檢查 Supabase URL 和 key 是否正確
3. 調整 `auth.setup.spec.ts` 中的選擇器（根據實際登入表單）
4. 增加等待時間（`timeout: 10000` → `timeout: 30000`）

### 問題 5: 基線衝突

**症狀**：多個 PR 同時更新基線導致衝突

**解決方案**：
- 系統已使用 `concurrency` 防止併發
- 如果仍有衝突，手動 rebase 並重新執行 CI

## 最佳實踐

### 1. 效能優化建議

**圖片優化**：
```bash
# 使用 WebP 格式
cwebp input.png -o output.webp -q 80

# 使用 responsive images
<img 
  srcset="image-320w.webp 320w, image-640w.webp 640w"
  sizes="(max-width: 600px) 320px, 640px"
  src="image-640w.webp"
  alt="..."
/>
```

**Code Splitting**：
```javascript
// 使用 React.lazy 延遲載入
const Dashboard = React.lazy(() => import('./Dashboard'));

// 使用 Suspense
<Suspense fallback={<Loading />}>
  <Dashboard />
</Suspense>
```

**字型優化**：
```css
/* 使用 font-display: swap */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: swap;
}
```

### 2. PR 檢查清單

提交 PR 前確認：

- [ ] 本地執行 `pnpm build` 成功
- [ ] 本地執行 `pnpm lhci` 並檢查分數
- [ ] 新增的圖片已壓縮優化
- [ ] 新增的依賴套件已評估大小影響
- [ ] 效能退步 >5% 已在 PR 描述中說明

### 3. 團隊協作

**效能預算會議**：
- 每月檢視 `trend.csv` 趨勢
- 討論是否需要調整閾值
- 分享效能優化經驗

**效能冠軍制度**：
- 每季選出效能優化貢獻最大的開發者
- 分享優化案例和技巧

## 參考資料

### 官方文件

- [Lighthouse CI 官方文件](https://github.com/GoogleChrome/lighthouse-ci)
- [Lighthouse 評分指南](https://web.dev/performance-scoring/)
- [Core Web Vitals](https://web.dev/vitals/)
- [Playwright Authentication](https://playwright.dev/docs/auth)

### 內部資源

- GitHub Issue: [#590 - 實作 Lighthouse CI 效能監控系統](https://github.com/RC918/morningai/issues/590)
- 配置檔案：
  - `lighthouserc.json` - PR 版本
  - `lighthouserc.main.json` - main 版本
  - `.github/workflows/lhci.yml` - GitHub Actions workflow

### 工具推薦

- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [WebPageTest](https://www.webpagetest.org/)
- [Lighthouse Chrome Extension](https://chrome.google.com/webstore/detail/lighthouse/blipmdconlkpinefehnmjammfjpmpbjk)

## 支援

如有問題或建議，請：

1. 查看本文件的「疑難排解」章節
2. 搜尋 GitHub Issues 中的相關討論
3. 在 GitHub Issue #590 留言
4. 聯繫團隊效能負責人

---

**最後更新**: 2025-10-23  
**版本**: 1.0.0  
**維護者**: Devin AI (@devin-ai-integration)
