# Phase 4: 訂閱與金流整合 - 完整交付

**版本**: 2.0 (已整合點數系統)
**日期**: 2025-09-12

---

## 1. 概述

本階段已將原有的金流系統與全新的點數系統進行了深度整合，形成一個統一、彈性的商業化底層架構。此方案不僅支持傳統的訂閱制，更引入了靈活的點數消耗和混合支付模式，為 Morning AI 的多樣化商業策略奠定堅實基礎。

## 2. 核心交付物

本交付包包含完整的設計、架構、程式碼和測試方案，符合 `HANDOFF_STANDARD_v2` 規範。

### 2.1. 產品與需求 (`/01-product`)

- **`PRD.md`**: 更新後的產品需求文檔，詳細描述了訂閱、點數、混合支付的業務邏輯。
- **`billing-rules.md`**: 詳細定義了點數折抵規則（最高30%）、退款策略、混合支付的扣款順序。

### 2.2. 體驗與設計 (`/02-design`)

- **`figma-link.txt`**: 指向最新的 Figma 設計稿，包含支付頁面、點數中心、訂閱管理頁面的完整 UI/UX 設計。
- **`design-system/`**: 包含與金流相關的組件（如價格卡片、支付按鈕）的 Design Tokens。

### 2.3. 系統與資料 (`/03-arch`)

- **`erd.puml`**: 最新的資料庫實體關係圖，增加了 `POINTS` 和 `POINT_TRANSACTIONS` 表，並優化了 `TRANSACTIONS` 表結構。
- **`openapi.yaml`**: 更新後的 API 規格，增加了 `/points` 相關的端點，並優化了 `/payments/checkout` 的請求體，加入了 `points_to_deduct` 參數。
- **`events.md`**: 新增了 `points.added`, `points.deducted`, `points.refunded` 等事件。

### 2.4. 實作方式與程式碼腳手架 (`/10-implementation`)

- **`repo-skeleton/`**: 提供了金流服務、點數服務、訂閱服務三個微服務的完整目錄結構和程式碼骨架 (FastAPI)。
- **`docker-compose.yml`**: 一鍵啟動包含所有服務和資料庫的本地開發環境。
- **`migration.sql`**: 完整的資料庫遷移腳本，用於創建和更新所有相關表格。
- **`seed.sql`**: 包含測試用戶、訂閱方案、點數包和初始點數餘額的種子數據。

### 2.5. 測試與品質 (`/06-testing`)

- **`test-plan.md`**: 詳盡的測試計劃，覆蓋了單元測試、整合測試和 E2E 測試。
- **`postman-collection.json`**: 可直接導入 Postman 的 API 測試集合，方便快速驗證所有金流與點數相關的 API。
- **`curl-examples.sh`**: 提供了一系列 curl 指令，用於快速測試核心場景。

## 3. 快速啟動與驗證

### 3.1. 環境啟動

```bash
# 1. 啟動所有服務
docker-compose up -d

# 2. 執行資料庫遷移
docker-compose exec db psql -U user -d morningai -f /docker-entrypoint-initdb.d/migration.sql

# 3. 注入種子數據
docker-compose exec db psql -U user -d morningai -f /docker-entrypoint-initdb.d/seed.sql
```

### 3.2. 核心場景測試

請執行 `curl-examples.sh` 腳本或使用 Postman 集合來驗證以下核心場景：

1.  **用戶註冊與獲取 Token**
2.  **查詢點數餘額** (預期: 500)
3.  **創建訂閱並使用點數折抵**
4.  **模擬支付成功 Webhook**
5.  **再次查詢點數餘額** (預期: 點數已扣除)
6.  **查詢交易記錄**
7.  **加購點數包**
8.  **再次查詢點數餘額** (預期: 點數已增加)

## 4. 與自治系統的整合

- **治理主控台**: 金流儀表板已整合到主控台，可實時監控收入、訂閱數、點數流動等關鍵指標。
- **Meta-Agent**: Meta-Agent 會分析用戶的消費行為。例如，當檢測到某用戶頻繁小額加購點數時，會主動觸發一個工作流，通過郵件或 App 內通知，向該用戶推薦更划算的年度訂閱或大額點數包。
- **自動化運營**: 當 Stripe Webhook 連續多次失敗時，會自動觸發一個「金流告警」工作流，通知 InfraMaintainer Agent 檢查服務狀態，並在 Slack 的 `#morningai-alerts` 頻道中創建一個高優先級事件。

通過本次整合，Morning AI 的商業化能力得到了極大的增強，為未來的市場擴展和收入增長提供了堅實的技術保障。

