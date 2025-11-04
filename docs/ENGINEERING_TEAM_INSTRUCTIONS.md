# 工程團隊實作指令文檔

## 文檔資訊
- **建立日期**: 2025-10-20
- **目標**: 指導工程團隊根據 UI/UX 設計文檔建立實作 PR
- **相關文檔**: 
  - docs/UX/SAAS_UX_STRATEGY.md (已合併至 main)
  - docs/UX/Design System/** (已合併至 main)
  - PENDING_DECISIONS_RECOMMENDATIONS.md (待核准)
- **狀態**: 指令文檔 → 待工程團隊執行

---

## 📋 執行摘要

設計 PR #465 已合併至 main 分支,包含完整的 UI/UX 策略與設計系統文檔。工程團隊現在需要根據文檔建立多個實作 PR,按照 8 週路線圖逐步落地。

**關鍵原則**:
1. ✅ **嚴格遵循設計/工程分工**: 工程 PR 只改動 API/邏輯,不改動 UI/文案
2. ✅ **參考設計文檔**: 所有實作需對齊 docs/UX/** 規範
3. ✅ **API 變更需 RFC**: 任何 OpenAPI/Schema 變更需先建立 RFC Issue
4. ✅ **保持向後相容**: 避免破壞性變更,使用功能旗標
5. ✅ **通過所有 CI**: 測試覆蓋率 ≥ 40%,所有檢查通過

---

## 🎯 8 週實作路線圖

### Week 1-2: 基礎修復與對齊

#### PR 1.1: 移除 Dashboard Hero,建立 Landing Page 結構

**目標**: 解決 CTO 報告 P0 問題 - Hero 位置錯誤

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 2.2 (站點結構)
- docs/UX/SAAS_UX_STRATEGY.md § 8.1 (CTO 報告整改)

**實作任務**:

1. **移除 Dashboard Hero** ✅ 高優先級
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/Dashboard.jsx
   
   變更:
   - 移除 Hero 區塊相關代碼
   - 移除 apple-design-tokens 中的 Hero 樣式
   - 保留 Dashboard 核心功能 (小工具、KPI)
   
   測試:
   - 確認 Dashboard 仍正常顯示
   - 確認小工具拖拽功能正常
   - 視覺回歸測試 (截圖對比)
   ```

2. **建立 Landing Page 路由** (如 Product Owner 核准)
   ```
   檔案: 
   - handoff/20250928/40_App/frontend-dashboard/src/App.jsx (新增路由)
   - handoff/20250928/40_App/frontend-dashboard/src/pages/Landing.jsx (新建)
   
   路由結構:
   / → Landing.jsx (公開,未登入)
   /login → Login.jsx
   /dashboard → Dashboard.jsx (需登入)
   
   Landing 內容 (參考 PENDING_DECISIONS_RECOMMENDATIONS.md):
   - Hero 區塊 (從 Dashboard 移過來)
   - 核心功能介紹 (3-4 個)
   - 定價方案
   - CTA (註冊/登入)
   
   注意:
   - 文案需參考 docs/UX/Design System/Copywriting.md
   - 響應式設計需符合 docs/UX/Design System/Tokens.md § 響應式
   ```

3. **API 端點確認** (不需 PR,僅確認)
   ```
   確認以下端點是否存在:
   - GET /api/metrics/cpu (CPU 使用率)
   - GET /api/metrics/memory (內存使用率)
   - GET /api/costs/today (今日成本)
   - GET /api/approvals/pending (待審批任務)
   - GET /api/strategies/active (活躍策略數)
   - GET /api/history/recent?limit=5 (最近決策)
   
   如不存在,建立 RFC Issue 並在 Week 3-4 實作
   ```

**驗收標準**:
- ✅ Dashboard 不再顯示 Hero 區塊
- ✅ Landing Page (如建立) 正常顯示且響應式
- ✅ 所有現有功能不受影響
- ✅ CI 全部通過 (12/12)
- ✅ 視覺回歸測試通過

**預估工時**: 2-3 天

---

#### PR 1.2: 補足空狀態與骨架屏

**目標**: 提升載入體驗與空狀態引導

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 5.4 (骨架與空狀態)
- docs/UX/Design System/Components.md § 共用組件

**實作任務**:

1. **統一骨架屏組件**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/ui/Skeleton.jsx
   
   需求:
   - 使用現有 ContentSkeleton/PageLoader
   - 為所有載入時間 > 800ms 的區域加骨架屏
   - 支援不同形狀 (矩形、圓形、文字)
   
   應用位置:
   - Dashboard 小工具載入
   - 列表頁面 (Strategies, Approvals, History)
   - 詳情頁面
   ```

2. **統一空狀態組件**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/ui/EmptyState.jsx
   
   Props:
   - icon: 圖示 (React 組件)
   - title: 標題
   - description: 描述
   - action: CTA 按鈕 (可選)
   
   範例:
   <EmptyState
     icon={<InboxIcon />}
     title="尚無待審批任務"
     description="當有新的 AI 決策需要審批時,會顯示在這裡"
     action={<Button>建立新任務</Button>}
   />
   
   應用位置:
   - Dashboard (無小工具時)
   - Approvals (無待審批時)
   - History (無歷史記錄時)
   - Strategies (無策略時)
   ```

**驗收標準**:
- ✅ 所有主要頁面都有骨架屏
- ✅ 所有空狀態都有清楚的引導文案與 CTA
- ✅ 文案符合 Copywriting.md 指南
- ✅ CI 通過

**預估工時**: 1-2 天

---

#### PR 1.3: 優化移動端字級與按鈕

**目標**: 解決 CTO 報告 P1 問題 - 響應式設計不完整

**參考文檔**: 
- docs/UX/Design System/Tokens.md § 響應式設計
- docs/UX/SAAS_UX_STRATEGY.md § 8.5 (響應式)

**實作任務**:

1. **調整移動端字級**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/tailwind.config.js
   
   變更:
   - 限制最大字級 (text-5xl → text-3xl on mobile)
   - 調整行高與間距
   
   範例:
   // 桌面
   <h1 className="text-5xl font-bold">標題</h1>
   
   // 改為響應式
   <h1 className="text-3xl md:text-5xl font-bold">標題</h1>
   ```

2. **調整移動端按鈕尺寸**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/ui/button.jsx
   
   變更:
   - 移動端按鈕高度 40px → 44px (符合觸控標準)
   - 按鈕文字 text-base → text-sm on mobile
   
   範例:
   <Button className="h-10 md:h-11 text-sm md:text-base">
     操作
   </Button>
   ```

3. **調整卡片佈局**
   ```
   檔案: Dashboard.jsx, Strategies.jsx, etc.
   
   變更:
   - 桌面: 3-4 欄
   - 平板: 2 欄
   - 手機: 1 欄
   
   範例:
   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
     {widgets.map(widget => <Widget key={widget.id} {...widget} />)}
   </div>
   ```

**驗收標準**:
- ✅ 移動端字級不超過 text-3xl
- ✅ 按鈕尺寸符合觸控標準 (≥ 44px)
- ✅ 卡片佈局響應式正確
- ✅ 無水平滾動
- ✅ CI 通過

**預估工時**: 1 天

---

#### PR 1.4: 動效治理

**目標**: 解決 CTO 報告 P1 問題 - 過度動畫

**參考文檔**: 
- docs/UX/Design System/Animation.md (完整文檔)
- docs/UX/SAAS_UX_STRATEGY.md § 8.4 (動效治理)

**實作任務**:

1. **移除無限循環動畫**
   ```
   檔案: 搜尋所有使用 animate-* 的組件
   
   命令:
   grep -r "animate-spin\|animate-pulse\|animate-bounce" handoff/20250928/40_App/frontend-dashboard/src/
   
   變更:
   - 移除裝飾性無限動畫
   - 保留 LoadingSpinner 的 animate-spin (功能性)
   - 為所有動畫加上條件 (只在載入時顯示)
   ```

2. **移除大半徑模糊**
   ```
   檔案: 搜尋所有使用 blur-* 的組件
   
   命令:
   grep -r "blur-3xl\|blur-2xl" handoff/20250928/40_App/frontend-dashboard/src/
   
   變更:
   - blur-3xl → blur-sm (≤ 8px)
   - 或完全移除 (如果只是裝飾)
   ```

3. **加入 IntersectionObserver**
   ```
   檔案: 建立 useInView hook
   
   位置: handoff/20250928/40_App/frontend-dashboard/src/hooks/useInView.js
   
   範例:
   import { useEffect, useState, useRef } from 'react';
   
   export function useInView(options = {}) {
     const [isInView, setIsInView] = useState(false);
     const ref = useRef(null);
   
     useEffect(() => {
       const observer = new IntersectionObserver(([entry]) => {
         setIsInView(entry.isIntersecting);
       }, options);
   
       if (ref.current) {
         observer.observe(ref.current);
       }
   
       return () => observer.disconnect();
     }, [options]);
   
     return [ref, isInView];
   }
   
   使用:
   const [ref, isInView] = useInView();
   
   <div ref={ref} className={isInView ? 'animate-fade-in' : ''}>
     內容
   </div>
   ```

4. **支援 prefers-reduced-motion**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/tailwind.config.js
   
   變更:
   module.exports = {
     theme: {
       extend: {
         animation: {
           'fade-in': 'fadeIn 0.3s ease-in',
         },
         keyframes: {
           fadeIn: {
             '0%': { opacity: '0' },
             '100%': { opacity: '1' },
           },
         },
       },
     },
     plugins: [
       // 自動支援 prefers-reduced-motion
     ],
   };
   
   CSS:
   @media (prefers-reduced-motion: reduce) {
     * {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
     }
   }
   ```

**驗收標準**:
- ✅ 無無限循環動畫 (除 LoadingSpinner)
- ✅ 無大半徑模糊 (blur ≤ 8px)
- ✅ 動畫只在視窗內播放 (IntersectionObserver)
- ✅ 支援 prefers-reduced-motion
- ✅ 動效預算符合 Animation.md 規範
- ✅ CI 通過

**預估工時**: 2 天

---

### Week 3-4: 設計系統與治理

#### PR 3.1: Tokens 去全域化

**目標**: 解決 CTO 報告 P0 問題 - 全域樣式污染

**參考文檔**: 
- docs/UX/Design System/Tokens.md § Token 架構
- docs/UX/SAAS_UX_STRATEGY.md § 8.3 (全域樣式污染)

**實作任務**:

1. **建立視覺回歸測試基線** (先執行)
   ```
   工具: Playwright
   
   檔案: handoff/20250928/40_App/frontend-dashboard/tests/visual-regression/
   
   測試頁面:
   - Dashboard
   - Sidebar
   - Login
   - Settings
   - Approvals
   
   命令:
   npx playwright test --update-snapshots
   
   結果: 儲存基線截圖至 tests/visual-regression/snapshots/
   ```

2. **移除全域樣式**
   ```
   檔案: 搜尋所有使用 * 選擇器的 CSS
   
   命令:
   grep -r "^\s*\*\s*{" handoff/20250928/40_App/frontend-dashboard/src/
   
   變更:
   - 移除 * { ... } 全域重置
   - 移除 body { ... } 強制覆蓋 (如有)
   ```

3. **建立 Theme 容器**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/styles/theme.css
   
   變更:
   /* 舊的 (全域) */
   * {
     --border-color: rgb(var(--apple-gray-200));
   }
   
   /* 新的 (作用域) */
   .theme-apple {
     --border-color: rgb(var(--apple-gray-200));
     --font-family: var(--apple-font-sans);
     --primary-color: rgb(var(--apple-blue-500));
   }
   
   應用:
   <div className="theme-apple">
     <App />
   </div>
   ```

4. **整合 Tailwind**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/tailwind.config.js
   
   變更:
   module.exports = {
     theme: {
       extend: {
         colors: {
           apple: {
             blue: 'rgb(var(--apple-blue-500) / <alpha-value>)',
             gray: {
               50: 'rgb(var(--apple-gray-50) / <alpha-value>)',
               100: 'rgb(var(--apple-gray-100) / <alpha-value>)',
               // ...
             },
           },
         },
         fontFamily: {
           sans: ['var(--apple-font-sans)', 'system-ui', 'sans-serif'],
         },
       },
     },
   };
   
   使用:
   <div className="bg-apple-blue text-apple-gray-900">內容</div>
   ```

5. **漸進式遷移**
   ```
   策略: 逐個組件遷移,避免一次性破壞
   
   優先級:
   1. Dashboard (高風險)
   2. Sidebar (高風險)
   3. 表單組件 (中風險)
   4. 其他頁面 (低風險)
   
   每個組件遷移後:
   - 執行視覺回歸測試
   - 確認無破壞性變更
   - 提交獨立 commit
   ```

**驗收標準**:
- ✅ 無 * 全域選擇器
- ✅ 所有樣式在 .theme-apple 容器內
- ✅ Tailwind 整合正確
- ✅ 視覺回歸測試通過 (無變化)
- ✅ CI 通過

**預估工時**: 3-4 天

---

#### PR 3.2: i18n 流程落地

**目標**: 解決 CTO 報告 P2 問題 - 翻譯品質

**參考文檔**: 
- docs/UX/Design System/Copywriting.md § i18n 流程
- docs/UX/SAAS_UX_STRATEGY.md § 8.7 (翻譯品質)

**實作任務**:

1. **建立翻譯審校流程**
   ```
   檔案: .github/workflows/i18n-review.yml (新建)
   
   觸發條件:
   - PR 修改 **/locales/** 檔案
   
   檢查項目:
   - Key 命名規範 (namespace.section.key)
   - 英文/繁中對照完整性
   - 避免直譯 (使用 linter 檢查常見錯誤)
   
   範例 linter 規則:
   - 避免 "進行" (直譯 "perform")
   - 避免 "利用" (直譯 "utilize")
   - 避免被動語態
   ```

2. **更新翻譯檔案**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/locales/
   
   結構:
   locales/
   ├── en-US/
   │   ├── common.json
   │   ├── auth.json
   │   ├── dashboard.json
   │   └── errors.json
   └── zh-TW/
       ├── common.json
       ├── auth.json
       ├── dashboard.json
       └── errors.json
   
   Key 命名:
   {
     "auth.login.title": "Sign In",
     "auth.login.form.email.label": "Email",
     "auth.login.form.email.placeholder": "Enter your email",
     "auth.login.form.submit": "Sign In"
   }
   ```

3. **建立文案指南**
   ```
   檔案: docs/UX/Design System/Copywriting.md (已存在,參考即可)
   
   工程團隊需遵循:
   - 清楚、簡潔、可行動
   - 避免行銷套語
   - 避免被動語態
   - 英文/繁中對照自然
   ```

**驗收標準**:
- ✅ 所有文案使用 i18n key (無硬編碼)
- ✅ 英文/繁中對照完整
- ✅ 翻譯自然,無直譯
- ✅ CI 通過 (i18n-review)

**預估工時**: 2 天

---

#### PR 3.3: Storybook 建立 (可選)

**目標**: 建立組件展示與測試環境

**參考文檔**: 
- docs/UX/Design System/Components.md
- PENDING_DECISIONS_RECOMMENDATIONS.md § 決策 4

**實作任務**:

1. **安裝 Storybook**
   ```
   命令:
   cd handoff/20250928/40_App/frontend-dashboard
   npx storybook@latest init
   
   選擇: VITE + React
   ```

2. **建立 Stories**
   ```
   檔案: src/components/ui/button.stories.jsx
   
   範例:
   import { Button } from './button';
   
   export default {
     title: 'UI/Button',
     component: Button,
     argTypes: {
       variant: {
         control: 'select',
         options: ['default', 'destructive', 'outline', 'ghost'],
       },
       size: {
         control: 'select',
         options: ['default', 'sm', 'lg'],
       },
     },
   };
   
   export const Default = {
     args: {
       children: 'Button',
       variant: 'default',
     },
   };
   
   export const Destructive = {
     args: {
       children: 'Delete',
       variant: 'destructive',
     },
   };
   ```

3. **建立所有基礎組件 Stories**
   ```
   組件清單:
   - Button
   - Input
   - Select
   - Dialog
   - Dropdown Menu
   - Tooltip
   - Card
   - Skeleton
   - EmptyState
   ```

**驗收標準**:
- ✅ Storybook 正常運行
- ✅ 所有基礎組件有 Stories
- ✅ Stories 涵蓋所有 variants 與 states
- ✅ CI 通過

**預估工時**: 1-2 天

---

### Week 5-6: 儀表板深度體驗

#### PR 5.1: 自訂儀表板操作模型

**目標**: 提升儀表板自訂體驗

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 3.2.1 (自訂儀表板)
- docs/UX/SAAS_UX_STRATEGY.md § 5.2 (Dashboard 優化)

**實作任務**:

1. **儲存狀態可見**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/Dashboard.jsx
   
   需求:
   - 顯示最近保存時間 ("已保存 · 2 分鐘前")
   - 顯示未保存狀態 ("有未保存的變更")
   - 顯示保存失敗 ("保存失敗,請重試")
   
   實作:
   const [saveStatus, setSaveStatus] = useState('saved'); // 'saved' | 'unsaved' | 'saving' | 'error'
   const [lastSavedAt, setLastSavedAt] = useState(null);
   
   <div className="flex items-center gap-2">
     {saveStatus === 'saved' && (
       <span className="text-sm text-gray-500">
         已保存 · {formatRelativeTime(lastSavedAt)}
       </span>
     )}
     {saveStatus === 'unsaved' && (
       <span className="text-sm text-yellow-600">
         有未保存的變更
       </span>
     )}
     {saveStatus === 'error' && (
       <span className="text-sm text-red-600">
         保存失敗 · <button onClick={handleRetry}>重試</button>
       </span>
     )}
   </div>
   ```

2. **撤銷/重做功能**
   ```
   檔案: Dashboard.jsx
   
   需求:
   - 支援撤銷 (Ctrl+Z / Cmd+Z)
   - 支援重做 (Ctrl+Shift+Z / Cmd+Shift+Z)
   - 顯示撤銷/重做按鈕
   
   實作:
   const [history, setHistory] = useState([initialLayout]);
   const [currentIndex, setCurrentIndex] = useState(0);
   
   const undo = () => {
     if (currentIndex > 0) {
       setCurrentIndex(currentIndex - 1);
       setLayout(history[currentIndex - 1]);
     }
   };
   
   const redo = () => {
     if (currentIndex < history.length - 1) {
       setCurrentIndex(currentIndex + 1);
       setLayout(history[currentIndex + 1]);
     }
   };
   
   useEffect(() => {
     const handleKeyDown = (e) => {
       if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
         if (e.shiftKey) {
           redo();
         } else {
           undo();
         }
       }
     };
     window.addEventListener('keydown', handleKeyDown);
     return () => window.removeEventListener('keydown', handleKeyDown);
   }, [currentIndex, history]);
   ```

3. **還原預設功能**
   ```
   檔案: Dashboard.jsx
   
   需求:
   - 提供 "還原預設" 按鈕
   - 顯示確認對話框
   
   實作:
   const resetToDefault = () => {
     if (confirm('確定要還原為預設配置嗎？')) {
       setLayout(DEFAULT_LAYOUT);
       setSaveStatus('unsaved');
     }
   };
   
   <Button variant="outline" onClick={resetToDefault}>
     還原預設
   </Button>
   ```

4. **移除元素確認**
   ```
   檔案: Dashboard.jsx
   
   需求:
   - 移除小工具時顯示輕量確認
   - 支援撤銷移除
   
   實作:
   const removeWidget = (widgetId) => {
     const widget = widgets.find(w => w.id === widgetId);
     setWidgets(widgets.filter(w => w.id !== widgetId));
     
     // Toast 通知
     toast({
       title: `已移除 ${widget.name}`,
       action: <Button onClick={() => restoreWidget(widget)}>撤銷</Button>,
       duration: 5000,
     });
   };
   ```

**驗收標準**:
- ✅ 儲存狀態清楚可見
- ✅ 撤銷/重做功能正常
- ✅ 還原預設功能正常
- ✅ 移除元素有確認與撤銷
- ✅ CI 通過

**預估工時**: 3 天

---

#### PR 5.2: 小工具清單搜尋與分類

**目標**: 提升小工具選擇體驗

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 5.2 (Dashboard 優化)

**實作任務**:

1. **小工具清單 UI**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/WidgetPicker.jsx (新建)
   
   需求:
   - 顯示所有可用小工具
   - 支援搜尋 (名稱、描述)
   - 支援分類篩選 (系統健康、成本、業務、操作)
   - 顯示小工具預覽
   
   實作:
   const [searchQuery, setSearchQuery] = useState('');
   const [selectedCategory, setSelectedCategory] = useState('all');
   
   const filteredWidgets = AVAILABLE_WIDGETS.filter(widget => {
     const matchesSearch = widget.name.includes(searchQuery) || 
                          widget.description.includes(searchQuery);
     const matchesCategory = selectedCategory === 'all' || 
                            widget.category === selectedCategory;
     return matchesSearch && matchesCategory;
   });
   
   <div className="space-y-4">
     <Input
       placeholder="搜尋小工具..."
       value={searchQuery}
       onChange={(e) => setSearchQuery(e.target.value)}
     />
     
     <div className="flex gap-2">
       <Button variant={selectedCategory === 'all' ? 'default' : 'outline'}
               onClick={() => setSelectedCategory('all')}>
         全部
       </Button>
       <Button variant={selectedCategory === 'health' ? 'default' : 'outline'}
               onClick={() => setSelectedCategory('health')}>
         系統健康
       </Button>
       {/* 其他分類 */}
     </div>
     
     <div className="grid grid-cols-2 gap-4">
       {filteredWidgets.map(widget => (
         <WidgetCard key={widget.id} widget={widget} onAdd={handleAddWidget} />
       ))}
     </div>
   </div>
   ```

2. **小工具 Meta 資訊**
   ```
   檔案: Dashboard.jsx
   
   需求:
   - 顯示資料來源 (API 端點)
   - 顯示更新頻率 (每 30 秒、每 5 分鐘)
   
   實作:
   <div className="text-xs text-gray-500 mt-2">
     資料來源: /api/metrics/cpu · 每 30 秒更新
   </div>
   ```

**驗收標準**:
- ✅ 小工具清單支援搜尋
- ✅ 小工具清單支援分類篩選
- ✅ 小工具卡片顯示 Meta 資訊
- ✅ CI 通過

**預估工時**: 2 天

---

#### PR 5.3: KPI 與趨勢卡片優化

**目標**: 提升資料可視化品質

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 5.3 (可視化)

**實作任務**:

1. **精簡 KPI 卡片**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/KPICard.jsx
   
   需求:
   - 大數字 + 趨勢箭頭
   - 限色彩 (只用品牌色)
   - 限裝飾 (無陰影、無漸變)
   
   實作:
   <Card className="p-6">
     <div className="flex items-center justify-between">
       <div>
         <p className="text-sm text-gray-500">今日成本</p>
         <p className="text-3xl font-bold mt-1">$45.67</p>
       </div>
       <div className="flex items-center gap-1 text-green-600">
         <ArrowDownIcon className="w-4 h-4" />
         <span className="text-sm">12%</span>
       </div>
     </div>
   </Card>
   ```

2. **趨勢圖優化**
   ```
   檔案: handoff/20250928/40_App/frontend-dashboard/src/components/TrendChart.jsx
   
   需求:
   - 使用簡單折線圖 (避免複雜圖表)
   - 限色彩 (最多 3 種顏色)
   - 突出對比與變化
   
   實作:
   import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
   
   <LineChart data={data} width={400} height={200}>
     <XAxis dataKey="date" />
     <YAxis />
     <Tooltip />
     <Line type="monotone" dataKey="cost" stroke="#3b82f6" strokeWidth={2} />
   </LineChart>
   ```

3. **異常標註**
   ```
   檔案: TrendChart.jsx
   
   需求:
   - 標註異常數據點 (超過閾值)
   - 顯示事件標記 (部署、發布)
   
   實作:
   <LineChart data={data}>
     {/* ... */}
     {data.map((point, index) => {
       if (point.cost > THRESHOLD) {
         return (
           <ReferenceDot key={index} x={point.date} y={point.cost} r={5} fill="red" />
         );
       }
     })}
   </LineChart>
   ```

**驗收標準**:
- ✅ KPI 卡片精簡且清楚
- ✅ 趨勢圖限色彩與裝飾
- ✅ 異常標註清楚可見
- ✅ CI 通過

**預估工時**: 2 天

---

### Week 7-8: 量化驗證與優化

#### PR 7.1: 可用性測試與指標回歸

**目標**: 驗證改進效果

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 6.3 (體驗量測)
- PENDING_DECISIONS_RECOMMENDATIONS.md § 決策 3

**實作任務**:

1. **執行可用性測試**
   ```
   測試對象: 5 位用戶 (客服 x2、業務、運營、管理員)
   測試時間: Week 7 (2025-12-02 ~ 2025-12-08)
   測試內容: 參考 PENDING_DECISIONS_RECOMMENDATIONS.md
   
   測試任務:
   1. 首次登入與引導 (10 分鐘)
   2. 自訂儀表板 (15 分鐘)
   3. 提交任務與審批 (15 分鐘)
   4. 查看成本報表 (10 分鐘)
   5. 問卷與訪談 (10 分鐘)
   
   測試指標:
   - SUS 分數 (目標 > 80)
   - 任務完成率 (目標 > 90%)
   - 任務完成時間
   - 錯誤率
   ```

2. **指標回歸分析**
   ```
   檔案: 建立指標儀表板
   
   指標:
   - 首次價值時間 (TTV) < 10 分鐘
   - 任務完成率 > 90%
   - 錯誤率月降 > 20%
   - NPS > 35
   
   工具: Google Analytics, Mixpanel, 或自建
   ```

3. **撰寫測試報告**
   ```
   檔案: docs/UX/USABILITY_TEST_REPORT.md (新建)
   
   內容:
   - 測試方法與對象
   - 測試結果 (SUS、任務完成率、錯誤率)
   - 發現的問題
   - 改進建議
   ```

**驗收標準**:
- ✅ 完成 5 位用戶測試
- ✅ SUS 分數 > 80
- ✅ 任務完成率 > 90%
- ✅ 撰寫測試報告

**預估工時**: 3-4 天

---

#### PR 7.2: A/B 測試 (可選)

**目標**: 優化關鍵流程

**參考文檔**: 
- docs/UX/SAAS_UX_STRATEGY.md § 9 (8 週路線圖)

**實作任務**:

1. **選擇 A/B 測試項目**
   ```
   候選項目:
   - 小工具預設排序 (按使用頻率 vs 按分類)
   - CTA 文案 ("建立任務" vs "開始使用")
   - 空狀態圖示 (插圖 vs 圖標)
   ```

2. **實施 A/B 測試**
   ```
   工具: LaunchDarkly, Optimizely, 或自建
   
   實作:
   const variant = useFeatureFlag('dashboard-widget-order');
   
   const widgetOrder = variant === 'frequency' 
     ? sortByFrequency(widgets)
     : sortByCategory(widgets);
   ```

3. **分析結果**
   ```
   指標:
   - 任務完成率
   - 任務完成時間
   - 用戶滿意度
   
   決策:
   - 如 variant A 顯著優於 variant B (p < 0.05),採用 variant A
   ```

**驗收標準**:
- ✅ A/B 測試正常運行
- ✅ 收集足夠樣本 (≥ 100 用戶)
- ✅ 分析結果並做出決策

**預估工時**: 2 天

---

## 🔧 通用實作指南

### 1. PR 命名規範

```
工程 PR: [Week X] 功能描述

範例:
- [Week 1] 移除 Dashboard Hero,建立 Landing Page
- [Week 3] Tokens 去全域化與 Tailwind 整合
- [Week 5] 自訂儀表板操作模型優化
```

### 2. PR 描述模板

```markdown
## 目標
簡短描述本 PR 的目標

## 參考文檔
- docs/UX/SAAS_UX_STRATEGY.md § X.X
- docs/UX/Design System/XXX.md

## 變更內容
- [ ] 變更 1
- [ ] 變更 2
- [ ] 變更 3

## 測試
- [ ] 單元測試通過
- [ ] 視覺回歸測試通過 (如適用)
- [ ] 手動測試通過

## 截圖
(如有 UI 變更,附上截圖)

## 驗收標準
- [ ] 標準 1
- [ ] 標準 2
- [ ] CI 全部通過

## Devin Run
https://app.devin.ai/sessions/9cd4942561c44c099a0bd3f159c348d5

## Requested by
Ryan Chen (ryan2939z@gmail.com) / @RC918
```

### 3. 分支命名規範

```
engineering/YYYYMMDD-feature-description

範例:
- engineering/20251020-remove-dashboard-hero
- engineering/20251027-tokens-scoping
- engineering/20251110-dashboard-undo-redo
```

### 4. Commit 訊息規範

```
type(scope): description

type:
- feat: 新功能
- fix: 修復
- refactor: 重構
- style: 樣式調整
- test: 測試
- docs: 文檔

範例:
- feat(dashboard): remove Hero block
- refactor(tokens): scope tokens to .theme-apple container
- feat(dashboard): add undo/redo functionality
```

### 5. 測試要求

**單元測試**:
```bash
cd handoff/20250928/40_App/api-backend
pytest --cov=src --cov-report=xml --cov-fail-under=40
```

**前端測試**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run test
pnpm run test:smoke
```

**視覺回歸測試**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
npx playwright test tests/visual-regression/
```

### 6. CI 檢查清單

所有 PR 必須通過:
- ✅ Backend CI (pytest, coverage ≥ 40%)
- ✅ Frontend CI (build, lint, smoke)
- ✅ OpenAPI 驗證 (如有 API 變更)
- ✅ Env Schema 驗證
- ✅ 視覺回歸測試 (如有 UI 變更)

### 7. API 變更流程

如需變更 API 或 Schema:

1. **建立 RFC Issue**
   ```
   使用模板: .github/ISSUE_TEMPLATE/rfc.md
   
   內容:
   - 提案動機
   - 影響範圍
   - 相容策略 (版本化/功能旗標/遷移)
   - Rollout 計劃
   ```

2. **等待核准**
   ```
   Product Owner 或 Tech Lead 核准後才可提交 PR
   ```

3. **實作 PR**
   ```
   PR 描述需引用 RFC Issue
   
   範例:
   Implements RFC #123: Add /api/metrics/cpu endpoint
   ```

### 8. 回滾策略

如 PR 合併後發現問題:

1. **立即回滾**
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. **建立 Hotfix PR**
   ```
   分支: hotfix/YYYYMMDD-issue-description
   優先級: 最高
   審查: 快速審查 (< 1 小時)
   ```

3. **Post-mortem**
   ```
   撰寫事後分析報告
   識別根本原因
   改進流程
   ```

---

## 📞 溝通與協作

### 1. 每週同步會議

**時間**: 每週一 10:00 AM

**議程**:
- 上週進度回顧
- 本週計劃
- 阻塞問題討論
- 設計文檔澄清

### 2. 設計文檔問題

如對設計文檔有疑問:

1. **先查閱文檔**
   ```
   docs/UX/SAAS_UX_STRATEGY.md
   docs/UX/Design System/**
   ```

2. **建立 Discussion**
   ```
   GitHub Discussions > Q&A
   標題: [設計問題] 簡短描述
   ```

3. **標記設計團隊**
   ```
   @design-team 請協助澄清...
   ```

### 3. 緊急問題

如遇到阻塞性問題:

1. **Slack 通知**
   ```
   #engineering 頻道
   @channel 緊急: 簡短描述
   ```

2. **建立 Issue**
   ```
   Label: blocker
   Assignee: Tech Lead
   ```

---

## 📊 進度追蹤

### 1. GitHub Project

使用 GitHub Project 追蹤進度:

```
Project: UI/UX Implementation (8-Week Roadmap)

Columns:
- Backlog (待辦)
- In Progress (進行中)
- In Review (審查中)
- Done (完成)

每個 PR 對應一個 Issue,連結到 Project
```

### 2. 每週報告

每週五提交進度報告:

```markdown
# Week X 進度報告

## 完成項目
- [ ] PR #XXX: 功能描述
- [ ] PR #YYY: 功能描述

## 進行中項目
- [ ] PR #ZZZ: 功能描述 (預計下週完成)

## 阻塞問題
- 問題 1: 描述與影響
- 問題 2: 描述與影響

## 下週計劃
- [ ] 任務 1
- [ ] 任務 2
```

---

## 🎯 成功標準

8 週實作完成後,需達成:

### 技術指標
- ✅ 所有 P0/P1 問題解決 (CTO 報告)
- ✅ 測試覆蓋率 ≥ 40%
- ✅ 所有 CI 檢查通過
- ✅ 無破壞性變更

### 性能指標
- ✅ LCP < 2.5s
- ✅ CLS < 0.1
- ✅ INP < 200ms
- ✅ 動效預算符合規範

### 用戶體驗指標
- ✅ SUS 分數 > 80
- ✅ 任務完成率 > 90%
- ✅ 首次價值時間 < 10 分鐘
- ✅ 錯誤率月降 > 20%

### 文檔完整性
- ✅ 所有組件有 Storybook Stories
- ✅ 所有 API 有 OpenAPI 文檔
- ✅ 可用性測試報告完成

---

## 📚 參考資源

### 設計文檔
- docs/UX/SAAS_UX_STRATEGY.md
- docs/UX/Design System/README.md
- docs/UX/Design System/Tokens.md
- docs/UX/Design System/Components.md
- docs/UX/Design System/Animation.md
- docs/UX/Design System/Accessibility.md
- docs/UX/Design System/Copywriting.md
- docs/UX/User Flows/README.md

### 決策文檔
- PENDING_DECISIONS_RECOMMENDATIONS.md
- DESIGN_PR_REVIEW_REPORT.md

### 貢獻指南
- CONTRIBUTING.md
- .github/pull_request_template.md
- .github/ISSUE_TEMPLATE/rfc.md

### 外部資源
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Web Vitals](https://web.dev/vitals/)
- [React Accessibility](https://react.dev/learn/accessibility)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

**文檔版本**: 1.0.0  
**建立日期**: 2025-10-20  
**狀態**: 指令文檔 → 待工程團隊執行
