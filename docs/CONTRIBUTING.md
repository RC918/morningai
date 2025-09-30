# Contribution Rules (Devin-friendly)

## 分工規則
- **Design PR**：只允許改動 `docs/UX/**`, `docs/UX/tokens.json`, `docs/**.md`, `frontend/樣式與文案`。
  - 不得改動 `handoff/**/30_API/openapi/**`, `**/api/**`, `**/src/**` 的後端與 API 相關檔。
- **Backend/Engineering PR**：只允許改動 `**/api/**`, `**/src/**`, `handoff/**/30_API/openapi/**`。
  - 不得改動 `docs/UX/**` 與設計稿資源。

## 變更 API / 資料欄位（OpenAPI/DB）
1. 先建立 **RFC Issue**（label: `rfc`），說明動機、影響、相容策略、逐步 rollout。
2. 經 Owner 核准後，才可提交工程 PR。

## 驗收
- 所有 PR 需通過：OpenAPI 驗證、Post-deploy Health 斷言、CI 覆蓋率 Gate。
- 違規改動將被 CI 自動阻擋（見 `.github/workflows/pr-guard.yml`）。
