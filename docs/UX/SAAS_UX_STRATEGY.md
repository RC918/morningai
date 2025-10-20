# MorningAI SaaS 頂尖用戶體驗策略

## 文檔資訊
- **版本**: 1.0.0
- **建立日期**: 2025-10-20
- **負責人**: UI/UX 設計團隊
- **狀態**: 草案 → 審核中
- **相關文檔**: CTO_VALIDATION_REPORT_PR462_DESIGNER.md, CONTRIBUTING.md

---

## 一、願景與成功指標

### 1.1 產品願景
MorningAI 致力於打造一個讓不同角色（運營、客服、業務、管理員）能以**最少學習成本完成任務**的 AI 驅動自動化平台。我們的 UI/UX 目標是建立可持續演進的設計系統與驗證機制，確保每次迭代都能提升用戶價值。

### 1.2 核心成功指標

#### 效率指標
- **首次價值時間 (TTV)**: < 10 分鐘
- **任務完成率**: > 90%
- **關鍵路徑成功率**: > 95%

#### 質量指標
- **錯誤率**: 月降 > 20%
- **崩潰率**: 連續下降
- **NPS (淨推薦值)**: > 35

#### 可用性指標
- **SUS (系統可用性量表)**: > 80
- **可及性**: WCAG 2.1 AA 標準
- **性能**: LCP < 2.5s, CLS < 0.1, INP < 200ms

---

## 二、產品定位與資訊架構

### 2.1 現況問題診斷

根據 CTO 驗收報告 (PR #462)，當前架構存在以下嚴重問題：

#### 🔴 P0 - 阻塞性問題
1. **Hero 區塊位置錯誤** (-3.0 分)
   - 問題：將 Landing Page 的 Hero 區塊放在已登入的 Dashboard 內
   - 影響：用戶困惑、浪費螢幕空間、違反 UX 最佳實踐
   - 參考：Apple、Gmail、Notion 均無在已登入介面放置 Hero

2. **違反工程/設計分工原則** (-1.5 分)
   - 問題：設計 PR 包含業務邏輯修改、i18n 遷移
   - 影響：代碼審查困難、回滾風險、測試覆蓋不足

3. **全域樣式污染風險** (-1.0 分)
   - 問題：使用 `*` 全域選擇器、強制覆蓋 body 樣式
   - 影響：破壞現有組件、與 Tailwind 衝突、維護困難

#### 🟡 P1 - 高優先級問題
4. **性能問題 - 過度動畫** (-0.8 分)
   - 問題：無限循環動畫、大半徑模糊 (blur-3xl)
   - 影響：電池消耗、滾動性能、無障礙問題

5. **響應式設計不完整** (-0.5 分)
   - 問題：移動端字體過大、按鈕佔用過多空間
   - 影響：移動端用戶體驗差

6. **無障礙性問題** (-0.4 分)
   - 問題：缺少 prefers-reduced-motion、aria-label
   - 影響：殘障用戶無法使用、法律合規風險

### 2.2 正確的站點結構

```
/                           → 公開 Landing Page (未登入)
├── Hero 區塊              → 品牌敘事、產品價值、CTA
├── 功能介紹               → 核心能力展示
├── 定價方案               → 透明定價
└── CTA (註冊/登入)        → 轉化入口

/login                      → 登入頁面
├── SSO 選項               → Google, Apple, GitHub
├── 密碼登入               → 傳統登入
└── 忘記密碼               → 重置流程

/dashboard                  → 工作主介面 (已登入)
├── 系統狀態總覽           → KPI、趨勢圖
├── 自訂小工具             → 拖拽、保存、重置
├── 最近決策               → AI 執行歷史
└── 快速操作               → 常用任務入口

/strategies                 → 策略管理
/approvals                  → 決策審批 (HITL)
/history                    → 歷史分析
/costs                      → 成本分析
/settings                   → 系統設置
/tenant-settings            → 租戶設置
/checkout                   → 訂閱方案
```

### 2.3 導航原則

#### 主導航 (左側固定側欄)
- **穩定性**: 始終可見，提供空間穩定性
- **層級**: 單層扁平結構，避免多層嵌套
- **狀態**: 當前頁面高亮、待辦數量徽章
- **折疊**: 支援折疊模式，節省空間

#### 頁首與面包屑
- **頁首**: 僅在需要的流程頁出現 (設定、結帳)
- **面包屑**: 深層頁面提供返回路徑
- **操作**: 頁面級操作 (保存、匯出、設定)

#### 權限與可見性
- **功能旗標**: 依 `AVAILABLE_FEATURES` 控制菜單顯示
- **角色權限**: 依用戶角色顯示/隱藏功能
- **WIP 頁面**: 不可用功能顯示 WIPPage，提供明確說明與 CTA

---

## 三、核心用戶旅程與流暢操作

### 3.1 首次體驗 (First-run Experience)

#### 問題現況
- Dashboard 內有 Hero 區塊，干擾首次使用
- 缺少引導流程，用戶不知從何開始
- 空狀態缺少敘事與 CTA

#### 改進方案

**極簡啟動引導 (3 步驟，每步 < 1 分鐘)**

```
步驟 1: 連線組織
├── 選擇租戶 / 建立新組織
├── 邀請團隊成員 (可跳過)
└── 下一步

步驟 2: 設定資料源
├── 連接 GitHub / Slack / 其他服務
├── 授權存取權限
└── 下一步

步驟 3: 建立第一個任務
├── 選擇任務類型 (FAQ 更新、代碼生成等)
├── 填寫基本資訊
└── 提交任務

完成 → 進入 Dashboard
├── 顯示樣板數據
├── 預設小工具配置
└── 提供「查看任務進度」CTA
```

**設計原則**
- ✅ 可跳過：每步都可跳過，直接進入 Dashboard
- ✅ 進度可見：顯示「步驟 1/3」
- ✅ 樣板數據：提供預設配置，降低學習成本
- ✅ 空狀態敘事：清楚說明下一步該做什麼

### 3.2 日常工作流程

#### 3.2.1 自訂儀表板

**現況問題**
- 保存狀態不明確，用戶不確定是否已保存
- 缺少撤銷/重做功能
- 移除元素無確認，容易誤操作

**改進方案**

```
編輯模式
├── 頂部工具列
│   ├── 保存 (顯示最近保存時間)
│   ├── 撤銷 / 重做
│   ├── 還原預設
│   └── 完成編輯
├── 小工具操作
│   ├── 拖拽重新排列
│   ├── 移除 (輕量確認)
│   └── 調整大小 (如支援)
└── 添加小工具
    ├── 搜尋小工具
    ├── 分類篩選
    └── 預覽效果
```

**狀態反饋**
- 🟢 已保存：顯示「已保存 · 2 分鐘前」
- 🟡 未保存：顯示「有未保存的變更」
- 🔴 保存失敗：顯示錯誤訊息與重試按鈕

#### 3.2.2 決策與審批 (HITL)

**用戶目標**
- 快速查看待審批任務
- 了解風險、影響、信心度
- 批准或拒絕決策

**介面設計**

```
待審批列表
├── 卡片視圖
│   ├── 任務標題
│   ├── 風險等級 (高/中/低)
│   ├── 預期影響
│   ├── 信心度 (87%)
│   ├── 追蹤 ID (trace_id)
│   └── 操作 (批准/拒絕/查看詳情)
└── 詳情頁
    ├── 完整描述
    ├── 變更預覽 (如 PR diff)
    ├── 相關資訊 (請求者、時間)
    └── 審批操作
```

**設計原則**
- ✅ 資訊層級：卡片顯示關鍵資訊，詳情頁顯示完整內容
- ✅ 風險突出：高風險任務使用紅色標記
- ✅ 快速操作：支援批量批准/拒絕
- ✅ 追蹤鏈路：顯示 trace_id，方便追蹤

#### 3.2.3 成本與配額管理

**用戶目標**
- 了解今日成本、本月成本
- 查看成本節省
- 配額剩餘與預警

**介面設計**

```
成本儀表板
├── KPI 卡片 (可釘選)
│   ├── 今日成本: $45.67
│   ├── 本月成本: $1,234.56
│   ├── 成本節省: $123.45
│   └── 配額剩餘: 75%
├── 趨勢圖
│   ├── 過去 30 天成本趨勢
│   ├── 按服務分類 (OpenAI, Supabase, Redis)
│   └── 異常標註
└── 預警設定
    ├── 每日預算上限
    ├── 配額警告閾值
    └── 通知方式 (Email, Slack)
```

**設計原則**
- ✅ 即時可見：Dashboard 顯示今日成本
- ✅ 超限預警：配額 < 20% 時顯示警告
- ✅ 成本歸因：按服務、按任務分類
- ✅ 節省可見：突出顯示 AI 帶來的成本節省

### 3.3 付費升級流程

**設計原則**
- ✅ 非侵入式：側欄與空狀態顯示升級入口
- ✅ 價值驅動：在關鍵時機植入「升級解鎖」提示
- ✅ 透明定價：清楚顯示各方案差異
- ✅ 無縫結帳：保留 /checkout 頁面，支援 Stripe/TapPay

**升級觸發點**
1. 配額用盡：「升級以獲得更多配額」
2. 功能限制：「此功能僅限專業版」
3. 團隊規模：「邀請更多成員需升級」

### 3.4 失敗與恢復

**錯誤模式分類**

```
頁面級錯誤
├── 404 Not Found
├── 500 Server Error
└── 網路斷線

區塊級錯誤
├── API 請求失敗
├── 資料載入失敗
└── 權限不足

行為級錯誤
├── 表單驗證失敗
├── 操作失敗 (保存、刪除)
└── 檔案上傳失敗
```

**統一錯誤介面**

```
錯誤提示
├── 錯誤圖示
├── 錯誤標題 (簡短描述)
├── 錯誤詳情 (技術資訊)
├── Sentry 事件 ID (方便追蹤)
└── 操作按鈕
    ├── 重試
    ├── 回報問題
    └── 聯繫支援
```

**設計原則**
- ✅ 清楚說明：告訴用戶發生了什麼
- ✅ 提供方案：告訴用戶該怎麼做
- ✅ 可追蹤：提供 Sentry 事件 ID
- ✅ 快速恢復：一鍵重試、回報問題

---

## 四、設計系統與規範

### 4.1 設計 Token 系統

#### 問題現況
- `apple-design-tokens.css` 使用全域選擇器 (`*`)
- 強制覆蓋 `body` 樣式，破壞現有組件
- 與 Tailwind CSS 配置重複，雙源維護

#### 改進方案

**Token 作用域化**

```css
/* ❌ 錯誤：全域污染 */
@layer base {
  * {
    border-color: rgb(var(--apple-gray-200));
  }
  body {
    font-family: var(--apple-font-sans);
  }
}

/* ✅ 正確：作用域限制 */
.theme-apple {
  --border-color: rgb(var(--apple-gray-200));
  --font-family: var(--apple-font-sans);
  --font-size: var(--apple-text-base);
  --text-color: rgb(var(--apple-text-primary));
}

.theme-apple * {
  border-color: var(--border-color);
}

.theme-apple body {
  font-family: var(--font-family);
  font-size: var(--font-size);
  color: var(--text-color);
}
```

**與 Tailwind 整合**

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        apple: {
          blue: 'rgb(var(--apple-blue-500) / <alpha-value>)',
          gray: {
            100: 'rgb(var(--apple-gray-100) / <alpha-value>)',
            200: 'rgb(var(--apple-gray-200) / <alpha-value>)',
            // ...
          }
        }
      },
      fontFamily: {
        sans: ['var(--apple-font-sans)', 'system-ui', 'sans-serif'],
      }
    }
  }
}
```

**設計原則**
- ✅ 單一來源：Tailwind 為主，CSS 變數為輔
- ✅ 作用域限制：使用 `.theme-apple` 容器
- ✅ 漸進式遷移：不一次性改變全站樣式
- ✅ 視覺回歸測試：截圖對比所有現有頁面

### 4.2 動效治理

#### 問題現況
- 無限循環動畫 (`repeat: Infinity`)
- 大半徑模糊 (`blur-3xl`) 消耗大量 GPU
- 缺少 `prefers-reduced-motion` 支援
- 動畫在不可見區域仍持續運行

#### 改進方案

**動效指南**

```jsx
// ❌ 錯誤：無限循環 + 大半徑模糊
<motion.div
  animate={{
    scale: [1, 1.2, 1],
    opacity: [0.3, 0.5, 0.3],
  }}
  transition={{
    duration: 8,
    repeat: Infinity,  // ❌ 無限循環
    ease: "easeInOut"
  }}
  className="blur-3xl"  // ❌ 大半徑模糊
/>

// ✅ 正確：可見時播放 + 支援 reduced motion
const [isVisible, setIsVisible] = useState(false)
const prefersReducedMotion = useReducedMotion()

useEffect(() => {
  const observer = new IntersectionObserver(
    ([entry]) => setIsVisible(entry.isIntersecting),
    { threshold: 0.1 }
  )
  observer.observe(ref.current)
  return () => observer.disconnect()
}, [])

<motion.div
  animate={isVisible && !prefersReducedMotion ? {
    scale: [1, 1.1, 1],
    opacity: [0.5, 0.7, 0.5],
  } : {}}
  transition={{
    duration: 4,
    repeat: 3,  // ✅ 有限次數
    ease: "easeInOut"
  }}
  className="blur-sm"  // ✅ 小半徑模糊
/>
```

**動效原則**
- ✅ 只在可見時播放：使用 IntersectionObserver
- ✅ 支援 reduced motion：檢查 `prefers-reduced-motion`
- ✅ 避免無限循環：限制重複次數
- ✅ 只使用 transform 與 opacity：避免觸發 layout reflow
- ✅ 避免大半徑模糊：blur-sm (4px) 為上限

**性能預算**
- 單頁動畫元素 ≤ 5 個
- 動畫時長 ≤ 600ms (微互動 ≤ 200ms)
- 模糊半徑 ≤ 8px
- 同時運行動畫 ≤ 3 個

### 4.3 響應式設計

#### 斷點定義

```js
// Tailwind 斷點
const breakpoints = {
  sm: '640px',   // 手機橫向
  md: '768px',   // 平板直向
  lg: '1024px',  // 平板橫向 / 小筆電
  xl: '1280px',  // 桌面
  '2xl': '1536px' // 大螢幕
}
```

#### 響應式原則

**字體大小**
```css
/* ❌ 錯誤：手機上過大 */
.title {
  @apply text-5xl sm:text-6xl lg:text-7xl xl:text-8xl;
}

/* ✅ 正確：漸進式放大 */
.title {
  @apply text-3xl sm:text-4xl md:text-5xl lg:text-6xl;
}
```

**按鈕尺寸**
```css
/* ❌ 錯誤：手機上過大 */
.button {
  @apply px-8 py-6 text-lg;
}

/* ✅ 正確：響應式調整 */
.button {
  @apply px-4 py-2 text-sm sm:px-6 sm:py-3 sm:text-base;
}
```

**網格佈局**
```css
/* ❌ 錯誤：手機上單列過長 */
.grid {
  @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4;
}

/* ✅ 正確：手機上 2 列 */
.grid {
  @apply grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4;
}
```

**背景裝飾**
```css
/* ❌ 錯誤：手機上溢出 */
.decoration {
  @apply absolute -left-1/4 w-96 h-96;
}

/* ✅ 正確：響應式尺寸 */
.decoration {
  @apply absolute -left-1/4 w-48 h-48 sm:w-64 sm:h-64 lg:w-96 lg:h-96;
}
```

### 4.4 無障礙性 (Accessibility)

#### WCAG 2.1 AA 標準

**鍵盤導航**
- ✅ 所有互動元素可用 Tab 鍵訪問
- ✅ 焦點可見 (focus-visible)
- ✅ 跳過導航連結 (Skip to main content)
- ✅ 快捷鍵支援 (如 Cmd+K 搜尋)

**語義化 HTML**
```jsx
// ❌ 錯誤：缺少語義
<div onClick={handleClick}>按鈕</div>

// ✅ 正確：使用語義元素
<button onClick={handleClick} aria-label="保存變更">
  保存
</button>
```

**ARIA 屬性**
```jsx
// 按鈕
<Button aria-label="關閉對話框">
  <X className="w-4 h-4" aria-hidden="true" />
</Button>

// 裝飾性圖示
<Sparkles className="w-4 h-4" aria-hidden="true" />

// 狀態提示
<div role="status" aria-live="polite">
  已保存變更
</div>

// 錯誤提示
<div role="alert" aria-live="assertive">
  保存失敗，請重試
</div>
```

**色彩對比度**
- 正常文字：對比度 ≥ 4.5:1
- 大文字 (18pt+)：對比度 ≥ 3:1
- 圖形與 UI 元件：對比度 ≥ 3:1

**工具**
- eslint-plugin-jsx-a11y：自動檢測無障礙問題
- axe DevTools：瀏覽器擴充套件
- Lighthouse：自動化測試

### 4.5 文案與 i18n

#### 文案指南

**原則**
- ✅ 清楚：避免模糊、專業術語
- ✅ 可行動：告訴用戶該做什麼
- ✅ 簡潔：避免冗長描述
- ✅ 一致：統一用詞與語氣

**範例**

```json
// ❌ 錯誤：模糊、行銷套語
{
  "hero.badge": "Introducing Morning AI",
  "hero.features.ai.description": "Intelligent decision making"
}

// ✅ 正確：清楚、具體
{
  "hero.badge": "New: Morning AI",
  "hero.features.ai.description": "AI-powered insights in seconds"
}
```

**語氣對照**

| 情境 | 英文 | 繁中 |
|------|------|------|
| 成功 | "Saved successfully" | "已保存" |
| 錯誤 | "Failed to save. Please try again." | "保存失敗，請重試" |
| 警告 | "This action cannot be undone." | "此操作無法復原" |
| 引導 | "Get started by creating your first task." | "建立第一個任務以開始使用" |

#### i18n 流程

**分工**
- 設計師：提交新增 key 的建議稿 (en-US.json, zh-TW.json)
- 工程師：整合 i18n、驗證翻譯、處理複數與變數

**審校機制**
1. 設計師提交翻譯草稿
2. 母語者審校 (英文、繁中)
3. 工程師整合到 i18n 系統
4. QA 驗證顯示效果

---

## 五、性能、穩定性與指標治理

### 5.1 性能預算

#### Core Web Vitals
- **LCP (Largest Contentful Paint)**: < 2.5s
- **CLS (Cumulative Layout Shift)**: < 0.1
- **INP (Interaction to Next Paint)**: < 200ms

#### 資源預算
- 首屏請求數 ≤ 3
- JavaScript bundle ≤ 300KB (gzipped)
- CSS bundle ≤ 50KB (gzipped)
- 圖片 ≤ 200KB (使用 WebP/AVIF)

#### 優化策略

**Code Splitting**
```js
// 路由級別分割
const Dashboard = lazy(() => import('./components/Dashboard'))
const Strategies = lazy(() => import('./components/StrategyManagement'))

// 組件級別分割
const ReportCenter = lazy(() => import('./components/ReportCenter'))
```

**圖表虛擬化**
```jsx
// 大數據集使用虛擬化
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data.slice(-100)}>  {/* 只渲染最近 100 筆 */}
    {/* ... */}
  </LineChart>
</ResponsiveContainer>
```

**圖片優化**
```jsx
// 使用 next-gen 格式
<picture>
  <source srcSet="image.avif" type="image/avif" />
  <source srcSet="image.webp" type="image/webp" />
  <img src="image.jpg" alt="描述" loading="lazy" />
</picture>
```

### 5.2 穩定性監控

#### 前端監控 (Sentry)

**錯誤追蹤**
```js
// 自動捕獲未處理錯誤
Sentry.init({
  dsn: SENTRY_DSN,
  environment: import.meta.env.MODE,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration()
  ],
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
})

// 手動回報錯誤
try {
  await saveLayout()
} catch (error) {
  Sentry.captureException(error, {
    tags: { feature: 'dashboard', action: 'save_layout' },
    user: { id: user.id, email: user.email }
  })
  showErrorToast('保存失敗，請重試')
}
```

**使用者可見錯誤**
```jsx
// 錯誤邊界
<ErrorBoundary
  fallback={({ error, eventId }) => (
    <ErrorPage
      title="發生錯誤"
      message={error.message}
      eventId={eventId}
      onRetry={() => window.location.reload()}
    />
  )}
>
  <App />
</ErrorBoundary>
```

#### 後端監控

**健康檢查**
```python
@app.route('/healthz')
def health_check():
    """Health check endpoint with comprehensive system status"""
    health_payload = get_health_payload()
    if health_payload.get("status") == "unhealthy":
        return jsonify(health_payload), 500
    return jsonify(health_payload)
```

**SLA 監控**
- 可用性 ≥ 99.5%
- 響應時間 P95 < 500ms
- 錯誤率 < 0.1%

### 5.3 體驗量測

#### 事件追蹤

**關鍵漏斗**
```
首次登入
  ↓
完成引導 (TTV < 10 分鐘)
  ↓
建立第一個任務
  ↓
查看任務結果
  ↓
再次回訪 (D1 留存)
```

**事件定義**
```js
// 用戶註冊
analytics.track('user_signed_up', {
  method: 'google',
  tenant_id: user.tenant_id
})

// 任務建立
analytics.track('task_created', {
  task_type: 'faq_update',
  trace_id: response.trace_id
})

// 儀表板自訂
analytics.track('dashboard_customized', {
  widgets_count: layout.length,
  action: 'save'
})
```

#### 可用性測試

**測試計畫**
- 頻率：每月 5 位用戶
- 任務：首次使用、建立任務、自訂儀表板、審批決策
- 指標：任務完成率、完成時間、錯誤次數、SUS 分數

**SUS 問卷 (System Usability Scale)**
1. 我認為我會經常使用這個系統
2. 我認為這個系統過於複雜
3. 我認為這個系統易於使用
4. 我認為我需要技術支援才能使用這個系統
5. 我認為這個系統的各項功能整合得很好
6. 我認為這個系統有太多不一致的地方
7. 我認為大多數人能很快學會使用這個系統
8. 我認為這個系統使用起來很麻煩
9. 我對使用這個系統感到很有信心
10. 我需要學習很多東西才能使用這個系統

**目標**: SUS > 80 (優秀)

---

## 六、流程與跨部門協作

### 6.1 PR 邊界 (嚴格遵循 CONTRIBUTING.md)

#### 設計 PR
**允許改動**
- ✅ `docs/UX/**` (設計文檔、指南)
- ✅ `docs/UX/tokens.json` (設計 Token)
- ✅ `docs/**.md` (文檔)
- ✅ `frontend/樣式與文案` (CSS、i18n 建議稿)

**禁止改動**
- ❌ `handoff/**/30_API/openapi/**` (API 定義)
- ❌ `**/api/**` (後端 API)
- ❌ `**/src/**` (業務邏輯)
- ❌ i18n 整合 (由工程 PR 處理)

#### 工程 PR
**允許改動**
- ✅ `**/api/**` (後端 API)
- ✅ `**/src/**` (業務邏輯)
- ✅ `handoff/**/30_API/openapi/**` (API 定義)
- ✅ i18n 整合 (整合設計師提供的翻譯)

**禁止改動**
- ❌ `docs/UX/**` (設計文檔)
- ❌ 設計稿資源

### 6.2 變更 API / 資料欄位流程

**RFC (Request for Comments) 流程**
1. 建立 RFC Issue (label: `rfc`)
2. 說明動機、影響、相容策略、逐步 rollout
3. 經 Owner 核准後，才可提交工程 PR

**範例**
```markdown
## RFC: 新增 Dashboard Layout API

### 動機
支援用戶自訂儀表板佈局，需要新增 API 保存/載入佈局

### API 變更
- POST /api/dashboard/layouts
- GET /api/dashboard/layouts?user_id={id}

### 相容策略
- 新增 API，不影響現有功能
- 舊版客戶端使用預設佈局

### Rollout 計畫
1. 部署 API (Week 1)
2. 前端整合 (Week 2)
3. 逐步開放給用戶 (Week 3)
```

### 6.3 驗收清單

**設計審查檢查清單**
- [ ] 組件放置位置是否合理？
- [ ] 是否符合產品定位？
- [ ] 是否符合用戶需求？
- [ ] 是否遵守分工原則？
- [ ] 性能影響是否可接受？
- [ ] 無障礙性是否達標？
- [ ] 是否有視覺回歸測試？

**工程審查檢查清單**
- [ ] OpenAPI 驗證通過
- [ ] Post-deploy Health 斷言通過
- [ ] CI 覆蓋率 Gate 通過
- [ ] 無 API/Schema 破壞性變更 (或有 RFC)
- [ ] i18n 整合正確
- [ ] 性能指標達標

### 6.4 工具鏈

#### 設計系統文檔
- 位置：`docs/UX/Design System/`
- 內容：Token、組件、動效、無障礙、文案指南
- 格式：Markdown + 範例代碼

#### Storybook (工程建立)
```bash
# 安裝 Storybook
pnpm dlx storybook@latest init

# 啟動 Storybook
pnpm run storybook
```

#### 視覺回歸測試
```bash
# 使用 Playwright 截圖
pnpm playwright test --update-snapshots

# 對比截圖
pnpm playwright test
```

#### Workflow 防護
```yaml
# .github/workflows/pr-guard.yml
on:
  pull_request:
    branches: [main]

jobs:
  check-pr-boundaries:
    runs-on: ubuntu-latest
    steps:
      - name: Check Design PR
        if: contains(github.event.pull_request.title, '設計 PR')
        run: |
          # 檢查是否改動了禁止的檔案
          git diff --name-only origin/main | grep -E '(api|src)/' && exit 1 || exit 0
```

---

## 七、針對 CTO 報告 (PR #462) 之整改方案

### 7.1 P0 - 阻塞性問題

#### 問題 1: Hero 區塊位置錯誤 (-3.0 分)

**整改方案**
1. 移除 `Dashboard.jsx` 中的 `AppleHero` 組件
2. 建立 `/` Landing Page (如需要行銷)
3. 將 `AppleHero` 移至 Landing Page
4. Dashboard 首屏聚焦數據與工具

**實施步驟**
```bash
# 1. 建立 Landing Page 組件
touch handoff/20250928/40_App/frontend-dashboard/src/components/LandingPage.jsx

# 2. 移除 Dashboard 中的 Hero
# 編輯 Dashboard.jsx，移除 AppleHero 相關代碼

# 3. 更新路由
# 編輯 App.jsx，新增 Landing Page 路由
```

#### 問題 2: 違反分工原則 (-1.5 分)

**整改方案**
1. 拆分 PR #462 為三個獨立 PR
   - PR #462-design: 只包含 AppleHero, AppleCard, CSS
   - PR #462-i18n: 由工程師處理 i18n 遷移
   - PR #462-integration: 由工程師整合到 Landing Page

**實施步驟**
```bash
# 1. 建立設計分支
git checkout -b design/apple-ui-components

# 2. 只保留設計相關檔案
git add handoff/20250928/40_App/frontend-dashboard/src/components/AppleHero.jsx
git add handoff/20250928/40_App/frontend-dashboard/src/components/AppleCard.jsx
git add handoff/20250928/40_App/frontend-dashboard/src/styles/apple-design-tokens.css

# 3. 提交設計 PR
git commit -m "設計 PR: Apple UI 組件"
```

#### 問題 3: 全域樣式污染 (-1.0 分)

**整改方案**
1. 移除 `*` 全域選擇器
2. 移除 `body` 強制覆蓋
3. 使用 `.theme-apple` 容器作用域
4. 漸進式套用，避免一次性改變全站

**實施步驟**
```css
/* apple-design-tokens.css */

/* 移除全域重置 */
/* @layer base {
  * {
    border-color: rgb(var(--apple-gray-200));
  }
} */

/* 改為作用域限制 */
.theme-apple {
  --border-color: rgb(var(--apple-gray-200));
  --font-family: var(--apple-font-sans);
  --font-size: var(--apple-text-base);
  --text-color: rgb(var(--apple-text-primary));
}

.theme-apple * {
  border-color: var(--border-color);
}

.theme-apple body {
  font-family: var(--font-family);
  font-size: var(--font-size);
  color: var(--text-color);
}
```

### 7.2 P1 - 高優先級問題

#### 問題 4: 過度動畫 (-0.8 分)

**整改方案**
1. 移除無限循環動畫 (`repeat: Infinity`)
2. 移除大半徑模糊 (`blur-3xl`)
3. 添加 IntersectionObserver，只在可見時播放
4. 添加 `prefers-reduced-motion` 支援

**實施步驟**
```jsx
// AppleHero.jsx

// 添加 Intersection Observer
const [isVisible, setIsVisible] = useState(false)
const prefersReducedMotion = useReducedMotion()
const ref = useRef(null)

useEffect(() => {
  const observer = new IntersectionObserver(
    ([entry]) => setIsVisible(entry.isIntersecting),
    { threshold: 0.1 }
  )
  if (ref.current) {
    observer.observe(ref.current)
  }
  return () => observer.disconnect()
}, [])

// 修改動畫
<motion.div
  ref={ref}
  animate={isVisible && !prefersReducedMotion ? {
    scale: [1, 1.1, 1],
    opacity: [0.5, 0.7, 0.5],
  } : {}}
  transition={{
    duration: 4,
    repeat: 3,  // 限制重複次數
    ease: "easeInOut"
  }}
  className="blur-sm"  // 改為小半徑模糊
/>
```

#### 問題 5: 響應式設計 (-0.5 分)

**整改方案**
1. 縮小移動端字體大小
2. 調整按鈕尺寸
3. 卡片網格改為 2 欄
4. 背景裝飾避免溢出

**實施步驟**
```jsx
// AppleHero.jsx

// 標題
<h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold">
  {/* 改為漸進式放大 */}
</h1>

// 按鈕
<Button className="px-4 py-2 text-sm sm:px-6 sm:py-3 sm:text-base">
  {/* 響應式尺寸 */}
</Button>

// 卡片網格
<div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
  {/* 手機上 2 欄 */}
</div>

// 背景裝飾
<motion.div
  className="absolute -left-1/4 w-48 h-48 sm:w-64 sm:h-64 lg:w-96 lg:h-96"
  {/* 響應式尺寸 */}
/>
```

#### 問題 6: 無障礙性 (-0.4 分)

**整改方案**
1. 添加 `aria-label` 到互動元素
2. 裝飾性圖示添加 `aria-hidden="true"`
3. 驗證色彩對比度
4. 添加 `prefers-reduced-motion` 支援

**實施步驟**
```jsx
// AppleHero.jsx

// 按鈕
<Button aria-label="開始使用 Morning AI Dashboard">
  {t('hero.cta.primary', 'Get Started')}
</Button>

// 裝飾性圖示
<Sparkles className="w-4 h-4" aria-hidden="true" />

// 色彩對比度驗證
// 使用工具檢查所有文字的對比度 (目標: WCAG AA)
```

### 7.3 P2 - 中優先級問題

#### 問題 7: 翻譯質量 (-0.2 分)

**整改方案**
1. 建立語氣指南
2. 審校流程：設計師 → 母語者 → 工程師
3. 避免直譯，提高語意精準度

**實施步驟**
```json
// en-US.json (改進後)
{
  "hero.badge": "New: Morning AI",
  "hero.features.ai.description": "AI-powered insights in seconds",
  "hero.title.line2": "Intelligent Decision Platform"
}

// zh-TW.json (改進後)
{
  "hero.badge": "全新：Morning AI",
  "hero.features.ai.description": "秒級 AI 洞察",
  "hero.title.line2": "智能決策平台"
}
```

#### 問題 8: 代碼重複 (-0.2 分)

**整改方案**
1. 統一 Token 與 Tailwind 來源
2. 避免雙維護
3. 擇一為主、另一側輔助

**實施步驟**
```js
// tailwind.config.js (統一來源)
export default {
  theme: {
    extend: {
      colors: {
        apple: {
          blue: {
            500: '#3b82f6'  // 單一來源
          }
        }
      }
    }
  }
}

// apple-design-tokens.css (移除重複)
/* 移除重複的顏色定義 */
/* --apple-blue-500: 59 130 246; */
```

---

## 八、落地路線圖 (8 週)

### Week 1-2: 基礎修復與對齊

**目標**: 修復 P0/P1 問題，建立設計系統基礎

**任務**
- [ ] 移除 Dashboard Hero，建立 Landing Page
- [ ] 補足空狀態與骨架屏
- [ ] 優化移動端字級與按鈕
- [ ] 動效治理 (移除無限動畫、添加 reduced motion)
- [ ] 建立 `docs/UX/Design System/` 草案
- [ ] 文案語氣指南 V1

**交付物**
- 設計 PR: `docs/UX/SAAS_UX_STRATEGY.md`
- 設計 PR: `docs/UX/Design System/` 基礎文檔
- 工程 PR: Dashboard Hero 移除 + Landing Page
- 工程 PR: 動效優化

### Week 3-4: 設計系統與治理

**目標**: 建立完整設計系統，確保一致性

**任務**
- [ ] Tokens 去全域化，建立 `.theme-apple` 容器
- [ ] 視覺回歸測試基線
- [ ] Storybook 套件建立 (工程)
- [ ] i18n 流程與審校機制落地
- [ ] 空狀態與錯誤樣式統一

**交付物**
- 設計 PR: `docs/UX/Design System/Tokens.md`
- 設計 PR: `docs/UX/Design System/Components.md`
- 工程 PR: Tokens 作用域化
- 工程 PR: Storybook 設定

### Week 5-6: 儀表板深度體驗

**目標**: 優化核心功能，提升用戶體驗

**任務**
- [ ] 自訂儀表板「儲存/撤銷/回溯」操作模型
- [ ] 小工具清單搜尋與分類
- [ ] KPI 與趨勢卡片優化
- [ ] 異常標註與事件標記
- [ ] 性能監測儀表板 (前端指標)

**交付物**
- 設計 PR: `docs/UX/User Flows/Dashboard Customization.md`
- 工程 PR: Dashboard 操作模型優化
- 工程 PR: 性能監測整合

### Week 7-8: 量化驗證與優化

**目標**: 驗證改進效果，持續優化

**任務**
- [ ] 可用性測試 (5 位用戶)
- [ ] 指標回歸分析
- [ ] A/B 測試 (如小工具預設排序)
- [ ] 整理「設計與工程交付手冊」
- [ ] 流程固化入 PR 模板與 CI 檢查

**交付物**
- 可用性測試報告
- 指標回歸報告
- 設計與工程交付手冊
- PR 模板更新

---

## 九、交付物與責任分工

### 9.1 設計交付

#### 文檔
- `docs/UX/SAAS_UX_STRATEGY.md` (本文檔)
- `docs/UX/Design System/`
  - `Tokens.md` (設計 Token 規範)
  - `Components.md` (組件指南)
  - `Animation.md` (動效指南)
  - `Accessibility.md` (無障礙指南)
  - `Copywriting.md` (文案與 i18n 指南)
- `docs/UX/User Flows/`
  - `First-run Experience.md`
  - `Dashboard Customization.md`
  - `Decision Approval.md`
  - `Cost Management.md`

#### 高保真設計 (Figma)
- Landing Page
- Dashboard (移除 Hero 後)
- 自訂儀表板流程
- 決策審批流程
- 空狀態與錯誤頁面

### 9.2 工程交付

#### 路由與權限
- Landing Page 路由 (`/`)
- 權限整合 (依 `AVAILABLE_FEATURES`)
- WIP 頁面優化

#### Dashboard 優化
- 移除 Hero 組件
- 自訂儀表板操作模型
- 小工具清單搜尋與分類
- 性能優化 (Code Splitting, 虛擬化)

#### 設計系統整合
- Tokens 作用域化
- Storybook 設定
- 視覺回歸測試

#### i18n 實作
- 整合設計師提供的翻譯
- 審校流程自動化
- 語言切換功能

#### 監控與追蹤
- Sentry 整合
- 性能監測儀表板
- 事件追蹤 (Analytics)

### 9.3 驗收標準

#### CI/CD
- ✅ OpenAPI 驗證通過
- ✅ Post-deploy Health 斷言通過
- ✅ CI 覆蓋率 Gate 通過 (≥ 40%)
- ✅ 無 API/Schema 破壞性變更

#### 性能
- ✅ Lighthouse 分數 ≥ 90
- ✅ LCP < 2.5s
- ✅ CLS < 0.1
- ✅ INP < 200ms

#### 可用性
- ✅ SUS > 80
- ✅ 任務完成率 > 90%
- ✅ 首次價值時間 < 10 分鐘

#### 無障礙
- ✅ WCAG 2.1 AA 標準
- ✅ 鍵盤導航完整
- ✅ 色彩對比度達標

---

## 十、後續需要決策的事項

### 10.1 產品策略
- [ ] 是否建立公開 Landing Page？
  - 如需要：用於 SEO 與行銷
  - 如不需要：維持私域導流 (口耳相傳)
- [ ] 目標用戶角色優先級？
  - 客服、業務、小編、運營、管理員
- [ ] 付費方案定位？
  - 免費版功能範圍
  - 專業版差異化價值

### 10.2 儀表板配置
- [ ] 預設小工具清單 (最多 6 個)
  - 建議：CPU 使用率、內存使用率、響應時間、錯誤率、活躍策略、待審批
- [ ] 優先 KPI
  - 建議：今日成本、成本節省、任務成功率、系統可用性

### 10.3 可用性測試
- [ ] 測試對象名單 (5 位用戶)
  - 角色分佈：客服 2 位、業務 1 位、運營 1 位、管理員 1 位
- [ ] 測試時間
  - 建議：Week 7 (2025-12-02 ~ 2025-12-08)

### 10.4 工具與流程
- [ ] 是否建立 Storybook？
  - 建議：是，方便組件展示與測試
- [ ] 是否啟用視覺回歸測試？
  - 建議：是，使用 Playwright 截圖對比
- [ ] 是否建立設計審查 Workflow？
  - 建議：是，自動檢查 PR 邊界

---

## 十一、附錄

### 11.1 參考資料

#### 設計系統
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design](https://material.io/design)
- [Ant Design](https://ant.design/)
- [Radix UI](https://www.radix-ui.com/)

#### 無障礙
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [A11y Project](https://www.a11yproject.com/)
- [WebAIM](https://webaim.org/)

#### 性能
- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/)

#### 可用性
- [Nielsen Norman Group](https://www.nngroup.com/)
- [System Usability Scale (SUS)](https://www.usability.gov/how-to-and-tools/methods/system-usability-scale.html)

### 11.2 工具清單

#### 設計工具
- Figma (高保真設計)
- FigJam (用戶流程圖)
- Stark (無障礙檢查)

#### 開發工具
- Vite (構建工具)
- Tailwind CSS (樣式框架)
- Radix UI (無頭組件)
- Framer Motion (動效庫)
- React Router (路由)
- Zustand (狀態管理)
- i18next (國際化)

#### 測試工具
- Playwright (E2E 測試、視覺回歸)
- Storybook (組件展示)
- eslint-plugin-jsx-a11y (無障礙檢查)
- Lighthouse (性能測試)
- axe DevTools (無障礙測試)

#### 監控工具
- Sentry (錯誤追蹤)
- Google Analytics (事件追蹤)
- Vercel Analytics (性能監控)

### 11.3 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |

---

## 聯繫方式

如有任何問題或建議，請聯繫：
- UI/UX 設計團隊
- 專案負責人：Ryan Chen (ryan2939z@gmail.com)

---

**文檔狀態**: 草案 → 審核中  
**下一步**: 提交設計 PR，等待審核與批准
