# Agent MVP Closed Loop — RFC (Draft)
## 1. 目標（TTE≤1m、成功率≥99%）
## 2. 系統流程（FAQ→PR→CI→Auto-merge→Deploy）
## 3. 權限設計（GitHub token scope / branch 保護 / auto-merge 條件）
## 4. trace_id / pr_url 數據流（Redis Key schema + Sentry breadcrumbs）
## 5. 失敗回復策略（重試/回滾/告警）
## 6. e2e 測試情境（多輪 / 佇列壓力 / 超時）
## 7. 指標與觀測（Sentry tags / APP_VERSION / heartbeat關聯）
## 8. 風險與時程（里程碑與拆分 PR）
