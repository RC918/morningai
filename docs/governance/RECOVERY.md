# MorningAI 災難恢復手冊 (Disaster Recovery Playbook)

## 概述

本文件提供 MorningAI 系統的災難恢復程序。當系統發生重大故障時，可依照本手冊快速回滾至已知穩定版本。

---

## 黃金基準線 (Golden Baseline)

| 版本標籤 | 日期 | 說明 |
|---------|------|------|
| `v2.0.0-2025-final` | 2025-12-31 | MorningAI 2025 Final Enterprise Edition |

### v2.0.0-2025-final 包含功能

- 90% Orchestrator 測試覆蓋率
- GeneralCoder 多檔案能力 (D-1b)
- Runtime Drift Detection (EPIC I-1)
- Provider Health Scoring (EPIC I-2)
- Provider Health Alerting (EPIC I-3a)
- Provider Health Snapshot API (EPIC I-3b)
- RLS 安全門禁
- ReviewToFixHandoff schema (EPIC D)
- Contract tests for commit_file() GitHub API

---

## 緊急回滾程序

### 情境：2026 年開春第一天發生崩潰

如果系統在 2026 年初發生重大故障，請執行以下步驟：

```bash
# 1. 取得最新 tags
git fetch origin --tags

# 2. 建立 hotfix 分支（推薦，允許後續緊急修復）
git checkout -b hotfix/rollback-v2.0.0-2025-final v2.0.0-2025-final

# 或者：如果只需要部署精確基準線，可直接 checkout tag（detached HEAD）
# git checkout v2.0.0-2025-final

# 3. 驗證版本
git rev-parse v2.0.0-2025-final
# 預期輸出: 19408e97...（完整 commit hash）

# 4. 重新部署
# (依照您的部署流程執行)
```

### 回滾前檢查清單

- [ ] 確認問題無法透過 hotfix 解決
- [ ] 通知相關團隊成員
- [ ] **備份資料庫**（建立 snapshot 或 point-in-time restore point）
- [ ] 備份當前狀態的 logs 和 metrics
- [ ] 確認回滾版本的相容性。**警告：資料庫 schema 回滾需特別謹慎，請參考 [Database Migrations Guide](../database/MIGRATIONS.md) 了解 downgrade 程序。**

### 回滾後驗證

依照 [Post-Deploy Smoke Test Checklist](../runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) 執行 **MUST-PASS** sections：

1. **Section 1: Backend Health Verification** - 驗證 `/healthz` 和核心 API
2. **Section 2: RLS Verification** - 確認 RLS 安全門禁正常（如適用）
3. **Section 3: Application Smoke Tests** - 執行應用程式功能測試

---

## 聯絡資訊

- 專案負責人: Ryan Chen (@RC918)
- 緊急聯絡: [依照組織政策填寫，例如 PagerDuty/Slack #incidents]

---

## 版本歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2025-12-31 | 1.1 | 改進回滾程序（建立 hotfix 分支）、新增資料庫備份步驟、連結至現有 runbooks |
| 2025-12-31 | 1.0 | 初始版本，建立 v2.0.0-2025-final 黃金基準線 |
