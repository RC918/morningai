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
# 1. 切換至黃金基準線
git fetch origin
git checkout v2.0.0-2025-final

# 2. 驗證版本
git log -1 --oneline
# 預期輸出: 19408e97 feat(governance): implement EPIC I-3b provider health snapshot API (#3359)

# 3. 重新部署
# (依照您的部署流程執行)
```

### 回滾前檢查清單

- [ ] 確認問題無法透過 hotfix 解決
- [ ] 通知相關團隊成員
- [ ] 備份當前狀態的 logs 和 metrics
- [ ] 確認回滾版本的相容性（資料庫 migrations 等）

### 回滾後驗證

1. 執行 smoke tests
2. 檢查 Orchestrator 健康狀態
3. 驗證 Provider Health 監控正常
4. 確認 RLS 安全門禁運作

---

## 聯絡資訊

- 專案負責人: Ryan Chen (@RC918)
- 緊急聯絡: [依照組織政策填寫]

---

## 版本歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2025-12-31 | 1.0 | 初始版本，建立 v2.0.0-2025-final 黃金基準線 |
