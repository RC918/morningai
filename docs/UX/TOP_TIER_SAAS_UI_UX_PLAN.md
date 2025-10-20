# MorningAI 頂尖 SaaS UI/UX 規劃報告

## 執行摘要

本報告聚焦於將 MorningAI 打造成具備一流體驗的 SaaS 系統，目標是在八週內交付一套可驗證、可量化、可持續演進的 UI/UX 能力組合：明確的資訊架構與使用流程、可落地的設計系統、跨部門協作標準、以及以數據驅動的持續優化機制。報告內容與現有 Milestone「UI/UX 8-Week Roadmap」（#6）與 15 項 GitHub Issues 完整對齊，並提供成功指標、驗收方式與風險控管。

## 產品願景與成功指標

願景是讓不同角色（運營、客服、業務、管理員）以最少學習成本完成關鍵任務，並且每次迭代都能帶來可衡量的體驗提升。

成功指標：
- 首次價值時間（TTV）< 10 分鐘；關鍵路徑成功率 > 95%
- 系統可用性（SUS）> 80；NPS > 35；錯誤率月降 > 20%
- 性能指標 LCP < 2.5s、CLS < 0.1、INP < 200ms；無障礙符合 WCAG 2.1 AA

## 資訊架構與使用者流程

以「公開 Landing Page 與已登入工作區分離」為核心原則，建立清晰的導覽與任務導向流程。
- /：公開 Landing Page（品牌敘事、功能介紹、定價、CTA）
- /login：登入（含 SSO）、/checkout：訂閱方案
- /dashboard：工作主介面（KPI、可自訂小工具、最近決策、快速操作）
- /strategies、/approvals（HITL）、/history、/costs、/settings、/tenant-settings

首次體驗以三步驟（連線組織、設定資料源、建立第一個任務）完成引導，所有步驟可跳過並提供樣板數據與明確空狀態敘事。日常工作重點在自訂儀表板（拖拽、撤銷/重做、儲存狀態可見、搜尋與分類選擇器），審批（風險/影響/信心度/trace_id 一致呈現），以及成本與配額管理（KPI 卡片、趨勢圖、預警設定）。

## 設計系統（Design System）與視覺語言

基於現有 docs/UX/Design System 與 tokens.json，執行以下治理：
- Tokens 作用域化：以容器類（如 .theme-apple）隔離主題變數，避免全域污染，並以 Tailwind 擴展整合，確保 UI 一致與安全遷移
- 元件庫標準化：以 Radix UI + Tailwind 為基礎，梳理組件清單、屬性、狀態、交互（含鍵盤與螢幕閱讀器）、錯誤與空狀態樣式
- 動效預算：單頁動畫 ≤ 3 個、時長 ≤ 600ms、支援 prefers-reduced-motion、以 IntersectionObserver 管理進場；禁用昂貴的無限循環與過度 blur
- 無障礙標準：WCAG 2.1 AA、焦點環、ARIA、鍵盤導航、對比度、語意標籤檢查
- 文案與 i18n：遵循 Copywriting 原則與 i18n 流程，建立 key 命名規範與審校機制，避免直譯

## 數據驅動驗證與持續優化

建立以指標為核心的迭代回路：
- 事件與錯誤：Sentry 追蹤頁面級與區塊級錯誤（顯示事件 ID），結合 post-deploy health 檢查
- 使用性指標：SUS 問卷與 NPS；可用性測試（Week 7，5 位跨角色測試者），AB 測試作為選配（Week 8）
- 行為數據：TTV、任務完成率、關鍵路徑成功率、表單錯誤率與修復率
- 性能：以 Lighthouse 與 Web Vitals 追蹤核心指標，對動效與資源進行預算控管

## 跨部門協作與交付標準

依 CONTRIBUTING 與設計/工程 PR 邊界工作：
- 設計 PR：僅改 docs/UX/**、docs/**.md、docs/UX/tokens.json；不得影響 API 與工程代碼
- 工程 PR：僅改 **/api/**、**/src/**、handoff/**/30_API/openapi/**；OpenAPI/DB 變更需先走 RFC 流程
- 工作流最佳實踐：所有 CI workflows 需加 branches/branches-ignore、concurrency 與 timeout，避免無限循環；自動合併需限定來源與檔案範圍
- 交付物：高保真模型、高互動原型、元件規格、tokens.json 變更說明、空狀態/錯誤狀態規範、可用性測試腳本與報告

## 8 週落地路線圖與對齊 Issues

完全對齊 Milestone #6（UI/UX 8-Week Roadmap）與現有 15 項 Issues；關鍵里程碑如下。

Week 1-2（體驗基線與性能治理）
- #467 移除 Dashboard Hero，建立 Landing Page（P0）：修正 IA，將品牌敘事回歸公開頁
- #468 補強空狀態與骨架屏（P1）：所有核心頁面具備空狀態敘事與 skeleton
- #469 行動端字級與按鈕尺寸（P1）：移動端優化與可點觸區域治理
- #470 動效治理（P1）：移除無限循環與高成本效果，導入 IntersectionObserver 與 reduced-motion

Week 3-4（設計系統與開發效率）
- #471 Token 作用域化 + Tailwind 整合（P0）：避免全域污染，建立主題容器策略
- #472 i18n 工作流程與翻譯品質（P1）：key 命名規範、審校流程與工具鏈
- #473 Storybook（選配，P2）：建立可視化元件目錄與互動測試基線

Week 5-6（Dashboard 能力）
- #474 Dashboard 自訂（P1）：儲存/撤銷/回溯與狀態可見
- #475 小工具選擇器（P1）：搜尋與分類、預覽
- #476 KPI 與趨勢卡片優化（P1）：資訊密度與可讀性
- #477 確認預設小工具 API（P1）：若缺失以錯誤率/響應時間替代（見建議清單）

Week 7-8（驗證與知識沉澱）
- #478 可用性測試（P1）：5 位跨角色測試者，任務驅動與 SUS/NPS
- #479 指標回歸分析（P1）：TTV、關鍵路徑成功率、錯誤率、性能
- #480 A/B 測試（選配，P2）：針對關鍵文案與引導策略
- #481 完善設計與工程交付文檔（P1）：沉澱規範與最佳實踐

## 驗收準則與風險控管

驗收標準：
- 指標：TTV < 10 分鐘、關鍵路徑成功率 > 95%、SUS > 80、LCP < 2.5s、AA 無障礙
- 視覺回歸：Token 去全域化後，以 Storybook 或視覺回歸工具建立基線，關鍵頁零破壞
- 可用性：Week 7 測試完成並產出報告；Week 8 指標回歸顯著改善
- CI：所有工作流具備 branches filter、concurrency、timeout，PR 需通過所有檢查

風險與對策：
- Token 去全域化波及面大：採分頁/分域漸進遷移，建立視覺回歸與回滾策略
- API 可用性不確定：預設替代方案（錯誤率/響應時間），並在 Week 3-4 規劃工程補齊
- 資源排程緊湊：P0 與 P1 優先，P2（Storybook、A/B）作為選配或穿插

## 與現有代碼與基礎設施對齊

- App.jsx 與 Dashboard.jsx 已具備特徵旗標、骨架、拖拽與 Widget 架構，規劃在此基礎上強化可用性與狀態可見
- Sentry、健康檢查與 CI/CD 已建立，配合本計畫擴充事件與回歸檢查
- docs/UX/* 已提供策略、設計系統與流程文檔，本報告作為統籌規劃與執行指南

## 下一步

- 啟動 Week 1-2 任務（#467、#468、#469、#470）並同步工程排程
- 與 PM/工程/行銷確認 Landing Page 文案與版型，提早佈局 SEO 與轉化漏斗
- 制定可用性測試招募計畫與腳本（提早兩週啟動招募）

—

附：
- Milestone #6：https://github.com/RC918/morningai/milestone/6
- Issues（標籤：UI/UX 8-Week Roadmap）：https://github.com/RC918/morningai/issues?q=is%3Aissue+milestone%3A%22UI%2FUX+8-Week+Roadmap%22
- 設計系統與策略文檔：docs/UX/
