# Phase 11 — AI Agent MVP 生態測試（草案）
## 目標
- 驗證 FAQ → PR → CI → Auto-merge → Deploy 的全自動閉環（≤ 1 分鐘）
## 範圍
- 角色：analyst（operator alias）、user（viewer alias）
- 階段資料：trace_id / pr_url 落檔（Redis + Sentry breadcrumb）
## 交付
- RFC（architecture + permissions）
- e2e 場景（多輪問答 / 佇列壓力 / 超時回復）
- 成功指標：TTE (Time To Effect) ≤ 1m、成功率 ≥ 99%
