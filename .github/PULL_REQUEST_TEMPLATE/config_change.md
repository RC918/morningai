<!--
================================================================================
CONFIGURATION CHANGE PR TEMPLATE - 配置變更 PR 模板
================================================================================

適用時機 (When to Use):
- 新增、修改或刪除環境變數
- 更新 env.schema.yaml
- 更新 settings.py 配置
- 更新 render.yaml IaC 設定
- 任何影響配置管理的變更

注意事項 (Important Notes):
- 此模板強制要求 Evidence Ledger 文檔
- 所有配置變更必須記錄在 CONFIGURATION_CHANGELOG.md
- 配置變更需要明確的審批者

其他模板:
- 一般開發: ?template=default.md
- Phase 2 遷移: ?template=phase2.md
- 緊急修復: ?template=hotfix.md

文檔參考: docs/config/CONFIGURATION_CHANGELOG.md
================================================================================
-->

## PR Title 格式（必須）

<!-- PR title 必須符合以下格式，否則 CI 會失敗 -->

**格式：** `feat(config): <description>` 或 `fix(config): <description>`

**常用類型：** `feat:`, `fix:`, `refactor:`, `chore:`

## 描述 (Description)

<!-- 簡要說明此配置變更的目的 -->

## 配置變更摘要 (Configuration Change Summary)

### 變更類型 (Change Type)

- [ ] **新增 (Added)** - 新增環境變數或配置
- [ ] **修改 (Modified)** - 修改現有配置的預設值或行為
- [ ] **棄用 (Deprecated)** - 標記配置為棄用
- [ ] **移除 (Removed)** - 移除配置

### 受影響的變數 (Affected Variables)

| 變數名稱 | 變更類型 | 舊值 | 新值 | 說明 |
|----------|----------|------|------|------|
| `EXAMPLE_VAR` | Added | N/A | `default` | 說明 |

### 變更理由 (Rationale)

<!-- 詳細說明為什麼需要這個配置變更 -->

## Evidence Ledger 更新（強制）

<!-- 所有配置變更必須記錄在 Evidence Ledger -->

- [ ] 已更新 `docs/config/CONFIGURATION_CHANGELOG.md`
- [ ] 包含完整的變更記錄（日期、變數、舊值、新值、理由、審批者）
- [ ] 已連結相關 Issue/PR

## 配置檔案檢查清單 (Configuration Files Checklist)

### env.schema.yaml（如適用）

- [ ] 已新增/更新變數定義
- [ ] 包含 `type`、`required`、`default`、`description`
- [ ] 包含 `category` 和 `security_level`
- [ ] 敏感資料使用 `type: secret`
- [ ] 已執行 `python scripts/generate-env-examples.py`
- [ ] 已執行 `python scripts/generate-env-reference.py`
- [ ] 不適用

### settings.py（如適用）

- [ ] 已新增/更新 Field 定義
- [ ] 使用正確的類型（`str`、`int`、`bool`、`Literal`、`SecretStr`）
- [ ] 敏感資料使用 `SecretStr` + `@property` 模式
- [ ] 包含 `alias`、`description`、`default`
- [ ] 不適用

### render.yaml（如適用）

- [ ] 已同步 IaC 設定
- [ ] 敏感資料使用 `sync: false`
- [ ] 不適用

## 安全性檢查 (Security Checklist)

- [ ] 敏感資料（密碼、API keys）使用 `SecretStr` 類型
- [ ] 敏感資料在 env.schema.yaml 中標記為 `security_level: sensitive` 或 `critical`
- [ ] 沒有在程式碼中硬編碼敏感資料
- [ ] 沒有在日誌中輸出敏感資料（使用 `repr=False`）

## 向後相容性 (Backward Compatibility)

- [ ] 此變更向後相容（現有部署不受影響）
- [ ] 此變更不向後相容，已記錄遷移步驟
- [ ] 已新增 deprecation warning（如棄用現有配置）

### 遷移步驟（如不向後相容）

<!-- 描述如何從舊配置遷移到新配置 -->

## 測試 (Testing)

- [ ] 已驗證 settings.py 可正常載入
- [ ] 已驗證 env.schema.yaml 驗證通過
- [ ] 已測試預設值行為
- [ ] 已測試環境變數覆蓋行為

## 相關 Issues/PRs

<!-- 連結相關的 GitHub Issues 和 PRs -->

Fixes #

## 審批者 (Approver)

<!-- 配置變更需要明確的審批者，請標記適當的審批者 -->

- [ ] @<approver-username>

## 提醒

- [ ] 所有環境變數已在 `config/env.schema.yaml` 中定義
- [ ] 已執行生成腳本更新 .env.example 和 ENV_REFERENCE.md
- [ ] 已更新 Evidence Ledger（CONFIGURATION_CHANGELOG.md）
- [ ] 敏感資料不會出現在日誌或錯誤訊息中
