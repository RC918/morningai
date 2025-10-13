# 🚀 Morning AI v{VERSION} Release Notes

**{RELEASE_TITLE}**

---

## 📅 Release Information

- **Version**: v{VERSION}
- **Release Date**: {YYYY-MM-DD}
- **Tag**: `v{VERSION}`
- **Production URL**: https://morningai-backend-v2.onrender.com
- **Branch**: `{BRANCH_NAME}`
- **Devin Session**: {DEVIN_SESSION_URL}

---

## ✨ 主要亮點 (Key Highlights)

### 🎯 {HIGHLIGHT_1_TITLE}
- **{METRIC_1}** - {DESCRIPTION}
- **{METRIC_2}** - {DESCRIPTION}
- **{METRIC_3}** - {DESCRIPTION}

### 🚀 {HIGHLIGHT_2_TITLE}
- **{FEATURE_1}** - {DESCRIPTION}
- **{FEATURE_2}** - {DESCRIPTION}
- **{FEATURE_3}** - {DESCRIPTION}

### 📊 {HIGHLIGHT_3_TITLE}
- **{PERFORMANCE_1}** - {DESCRIPTION}
- **{PERFORMANCE_2}** - {DESCRIPTION}
- **{PERFORMANCE_3}** - {DESCRIPTION}

---

## 📊 詳細數據 (Performance Data)

### {METRIC_CATEGORY_1}

```
{METRIC_NAME}: {VALUE}
{COMPARISON}: {BASELINE} → {CURRENT} ({CHANGE}%)

High Priority Items:
├── {ITEM_1}: {VALUE}
├── {ITEM_2}: {VALUE}
└── {ITEM_3}: {VALUE}

Medium Priority Items:
├── {ITEM_4}: {VALUE}
└── {ITEM_5}: {VALUE}
```

### {METRIC_CATEGORY_2}

```
{ENDPOINT_HEALTH} ({SAMPLE_SIZE} requests):
├── Success Rate: {SUCCESS_RATE}%
├── Average Latency: {AVG_LATENCY}ms
├── P95 Latency: {P95_LATENCY}ms
└── Error Rate: {ERROR_RATE}%

Endpoint Availability:
├── /health: ✅ 200 OK
├── /healthz: ✅ 200 OK
├── /api/{ENDPOINT_1}: ✅ 200 OK
└── /api/{ENDPOINT_2}: ✅ 200 OK
```

### {METRIC_CATEGORY_3}

```
Category 1 ({CATEGORY_NAME}): ✅ PASSED - {DETAILS}
Category 2 ({CATEGORY_NAME}): ⚠️ PARTIAL - {DETAILS}
Category 3 ({CATEGORY_NAME}): ✅ PASSED - {DETAILS}
Category 4 ({CATEGORY_NAME}): ✅ PASSED - {DETAILS}
Category 5 ({CATEGORY_NAME}): ⚠️ PARTIAL - {DETAILS}
Category 6 ({CATEGORY_NAME}): ✅ COMPLETED - {DETAILS}
```

---

## 🔧 技術改進 (Technical Improvements)

### 新增功能 (New Features)

- **{FEATURE_1}** - {DESCRIPTION}
- **{FEATURE_2}** - {DESCRIPTION}
- **{FEATURE_3}** - {DESCRIPTION}
- **{FEATURE_4}** - {DESCRIPTION}

### 架構優化 (Architecture Improvements)

- **{OPTIMIZATION_1}** - {DESCRIPTION}
- **{OPTIMIZATION_2}** - {DESCRIPTION}
- **{OPTIMIZATION_3}** - {DESCRIPTION}

### Bug 修復 (Bug Fixes)

- **{BUG_1}** - {DESCRIPTION}
- **{BUG_2}** - {DESCRIPTION}
- **{BUG_3}** - {DESCRIPTION}

### 測試改進 (Test Improvements)

- **{TEST_1}** - {DESCRIPTION}
- **{TEST_2}** - {DESCRIPTION}
- **{TEST_3}** - {DESCRIPTION}

---

## 🔄 Breaking Changes

### {BREAKING_CHANGE_1}

**影響範圍**: {SCOPE}

**遷移指南**:
```bash
# Before
{OLD_CODE_EXAMPLE}

# After
{NEW_CODE_EXAMPLE}
```

**時間表**:
- {DATE_1}: 棄用警告
- {DATE_2}: 強制遷移
- {DATE_3}: 移除舊版支援

---

## ⚠️ 已知問題 (Known Issues)

### Issue #1: {ISSUE_TITLE}

**症狀**: {DESCRIPTION}

**影響**: {IMPACT}

**暫時解決方案**:
```bash
{WORKAROUND_COMMANDS}
```

**修復計畫**: {FIX_PLAN}

### Issue #2: {ISSUE_TITLE}

**症狀**: {DESCRIPTION}

**影響**: {IMPACT}

**追蹤**: {GITHUB_ISSUE_URL}

---

## 📋 待辦事項 (TODO)

### 立即優先 (Immediate Priority)

1. **{TODO_1_TITLE}**
   ```bash
   # {DESCRIPTION}
   {COMMANDS_OR_STEPS}
   ```

2. **{TODO_2_TITLE}**
   ```bash
   # {DESCRIPTION}
   {COMMANDS_OR_STEPS}
   ```

### 短期目標 (Short-term Goals)

3. **{TODO_3_TITLE}**
   - {DETAIL_1}
   - {DETAIL_2}
   - {DETAIL_3}

4. **{TODO_4_TITLE}**
   - {DETAIL_1}
   - {DETAIL_2}

### 中期規劃 (Medium-term Planning)

5. **{TODO_5_TITLE}**
   - {DETAIL_1}
   - {DETAIL_2}

---

## 🔄 升級指南 (Upgrade Guide)

### 從 v{OLD_VERSION} 升級

#### 1. 更新環境變數

```bash
# 新增的環境變數
{NEW_ENV_VAR_1}={VALUE}
{NEW_ENV_VAR_2}={VALUE}

# 棄用的環境變數（仍支援但建議移除）
# {DEPRECATED_ENV_VAR_1}
# {DEPRECATED_ENV_VAR_2}
```

#### 2. 資料庫遷移（如適用）

```bash
# 備份資料庫
{BACKUP_COMMAND}

# 執行遷移
{MIGRATION_COMMAND}

# 驗證遷移
{VERIFICATION_COMMAND}
```

#### 3. 更新依賴

```bash
# Backend
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt --upgrade

# Orchestrator
cd ../orchestrator
pip install -r requirements.txt --upgrade
pip install -e . --upgrade

# Frontend
cd ../frontend-dashboard
npm install
```

#### 4. 驗證升級

```bash
# 健康檢查
curl https://morningai-backend-v2.onrender.com/health

# 版本驗證
curl https://morningai-backend-v2.onrender.com/api/version
```

---

## 🔙 回滾指令 (Rollback Instructions)

### 緊急回滾到穩定版本

```bash
# 1. 回滾到前一個穩定版本
git checkout v{PREVIOUS_STABLE_VERSION}

# 2. 創建緊急修復分支
git checkout -b hotfix/emergency-rollback-$(date +%s)

# 3. 查看可用版本
git tag --list --sort=-version:refname

# 4. 回滾到特定版本
git checkout v{TARGET_VERSION}
git checkout -b hotfix/rollback-to-v{TARGET_VERSION}
```

### 生產環境回滾

```bash
# 1. Render 服務回滾
# 前往 Render Dashboard > morningai-backend-v2 > Deploys
# 選擇穩定的部署版本並點擊 "Redeploy"

# 2. 驗證回滾成功
curl -sS https://morningai-backend-v2.onrender.com/health | jq '.version'

# 3. 強制重新部署特定提交（謹慎使用）
git push origin v{TARGET_VERSION}:main --force-with-lease
```

### 資料庫回滾（如適用）

```bash
# 1. 檢查備份
{LIST_BACKUPS_COMMAND}

# 2. 還原備份
{RESTORE_BACKUP_COMMAND}

# 3. 驗證資料完整性
{VERIFY_DATA_COMMAND}
```

---

## 🚀 部署狀態 (Deployment Status)

### 當前狀態

- **生產環境**: ✅ 已部署並驗證
- **健康檢查**: ✅ 所有端點正常
- **效能監控**: ✅ 符合 SLA 要求
- **安全掃描**: ✅ 無已知漏洞

### CI/CD 通過檢查

| Check | Status | Duration |
|-------|--------|----------|
| ✅ orchestrator-e2e | Pass | {DURATION} |
| ✅ post-deploy-health | Pass | {DURATION} |
| ✅ post-deploy-health-assertions | Pass | {DURATION} |
| ✅ ops-agent-sandbox-e2e | Pass | {DURATION} |
| ✅ backend-ci (test) | Pass | {DURATION} |
| ✅ backend-ci (lint) | Pass | {DURATION} |
| ✅ frontend-ci (build) | Pass | {DURATION} |

### 下一步行動

1. **{ACTION_1}** - {DESCRIPTION}
2. **{ACTION_2}** - {DESCRIPTION}
3. **{ACTION_3}** - {DESCRIPTION}

---

## 📞 支援資訊 (Support Information)

### 技術聯絡

- **開發團隊**: @RC918
- **Devin 執行記錄**: {DEVIN_SESSION_URL}
- **GitHub Repository**: https://github.com/RC918/morningai
- **Pull Request**: {PR_URL}

### 監控和告警

- **生產監控**: https://morningai-backend-v2.onrender.com/health
- **CI/CD 狀態**: https://github.com/RC918/morningai/actions
- **錯誤追蹤**: Sentry Dashboard

### 文檔資源

- **API 文檔**: `/handoff/20250928/30_API/`
- **架構文檔**: `/docs/ARCHITECTURE.md`
- **環境變數**: `/docs/config/env_schema.md`
- **本地設定**: `/docs/setup_local.md`
- **CI 矩陣**: `/docs/ci_matrix.md`

---

## 🎯 下一個版本預告 (Next Release Preview)

### v{NEXT_VERSION} 規劃

**預計發布**: {EXPECTED_DATE}

**主要功能**:
- {PLANNED_FEATURE_1}
- {PLANNED_FEATURE_2}
- {PLANNED_FEATURE_3}

**技術債清理**:
- {TECH_DEBT_1}
- {TECH_DEBT_2}

---

**🎉 Morning AI v{VERSION} - {RELEASE_TITLE}**

*{CLOSING_REMARKS}*

---

## Template Usage Instructions

### How to Use This Template

1. **Copy this template** when preparing a new release
2. **Replace all `{PLACEHOLDER}` values** with actual data:
   - `{VERSION}`: e.g., `9.1.0`
   - `{RELEASE_TITLE}`: e.g., `Phase 9 Complete - Commercialization & PWA`
   - `{YYYY-MM-DD}`: e.g., `2025-10-13`
   - `{BRANCH_NAME}`: e.g., `devin/1760123456-phase9-final`
   - `{DEVIN_SESSION_URL}`: Devin session link
   - All other placeholders with relevant data

3. **Remove unused sections** if not applicable
4. **Add screenshots** for visual changes using:
   ```markdown
   ![Description](path/to/screenshot.png)
   ```

5. **Link related PRs and issues**:
   ```markdown
   - Closes #123
   - Related to #456
   ```

6. **Save as** `RELEASE_NOTES_v{VERSION}.md` in the project root

### Required Sections

These sections should ALWAYS be included:
- Release Information
- Key Highlights
- Technical Improvements
- Deployment Status
- Support Information

### Optional Sections

Include these only when relevant:
- Breaking Changes (for major versions)
- Known Issues (if any critical issues exist)
- TODO (for incomplete items)
- Upgrade Guide (for versions requiring migration)
- Rollback Instructions (for production releases)
- Next Release Preview (at end of phase)

### Checklist Before Publishing

- [ ] All placeholders replaced with actual values
- [ ] Metrics and data verified
- [ ] Links tested (PR, issues, documentation)
- [ ] Screenshots added for UI changes
- [ ] Breaking changes clearly documented
- [ ] Rollback instructions tested
- [ ] Support contacts updated
- [ ] Spell check completed
- [ ] Reviewed by CTO/tech lead

---

**Template Version**: 1.0  
**Last Updated**: Phase 11 Task 5 (2025-10-13)  
**Maintainer**: Morning AI Engineering Team
