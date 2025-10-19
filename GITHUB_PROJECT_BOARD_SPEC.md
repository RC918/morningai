# GitHub Project Board 規格文檔

**專案名稱**: October Sprint - Self-Healing CI/CD  
**開始日期**: 2025-10-21  
**結束日期**: 2025-11-17  
**類型**: Table View + Board View

---

## 📋 看板列 (Columns)

1. **Backlog** - 待規劃任務
2. **Week 1** - RLS Phase 2 + 自動回滾 (Oct 21-27)
3. **Week 2** - LangGraph 測試 + 自癒 Workflow (Oct 28 - Nov 3)
4. **Week 3** - Distributed Tracing + 性能測試 (Nov 4-10)
5. **Week 4** - SLO 儀表 + Observability (Nov 11-17)
6. **In Progress** - 進行中
7. **Done** - 已完成

---

## 📝 Week 1 任務 (Issues)

### A. RLS Phase 2 實施

**Issue #1: 建立 RLS Migration 001 測試**
- **Title**: [Week 1] RLS Migration 001 - agent_tasks 表驗證
- **Labels**: `week-1`, `rls`, `database`, `priority:high`
- **Assignee**: @RC918
- **Estimate**: 2 hours
- **Description**:
  ```
  驗證 migration 001 (agent_tasks RLS) 是否已正確應用。
  
  **任務**:
  - [ ] 連線 Supabase 確認 agent_tasks 表存在
  - [ ] 確認 RLS 已啟用
  - [ ] 確認 policies 正確運作
  - [ ] 執行 RLS 測試
  
  **驗收標準**:
  - agent_tasks 表 RLS 啟用
  - 多租戶隔離測試通過
  ```

**Issue #2: Supabase 表結構驗證**
- **Title**: [Week 1] 驗證 Supabase 表結構 (tenants, users, platform_bindings)
- **Labels**: `week-1`, `rls`, `database`, `priority:high`
- **Estimate**: 2 hours
- **Description**:
  ```
  連線 Supabase 確認 migration 002 所需的表與欄位存在。
  
  **檢查項目**:
  - [ ] tenants 表 (id, name)
  - [ ] users 表 (id, tenant_id, role)
  - [ ] platform_bindings 表 (tenant_id)
  - [ ] external_integrations 表 (tenant_id)
  - [ ] memory 表 (tenant_id)
  
  **行動**:
  - 如表不存在，註解 migration 002 相應段落
  - 記錄缺失的表，後續新增
  
  **驗收標準**:
  - 生成表結構驗證報告
  - migration 002 調整完成 (如需要)
  ```

**Issue #3: RLS Migration 002 應用**
- **Title**: [Week 1] 應用 RLS Migration 002 - 多租戶表隔離
- **Labels**: `week-1`, `rls`, `database`, `priority:high`
- **Estimate**: 4 hours
- **Description**:
  ```
  應用 migration 002，啟用多租戶 RLS policies。
  
  **任務**:
  - [ ] 在 staging 環境測試 migration 002
  - [ ] 確認 policies 正確建立
  - [ ] 執行多租戶隔離測試
  - [ ] 應用至 production
  
  **驗收標準**:
  - tenants, users, platform_bindings, integrations 表啟用 RLS
  - Helper functions 建立: is_tenant_admin(), current_user_tenant_id()
  - rls_audit_log 表建立
  - 測試覆蓋率 +15%
  ```

**Issue #4: RLS 整合測試**
- **Title**: [Week 1] RLS 多租戶隔離整合測試
- **Labels**: `week-1`, `rls`, `testing`, `priority:high`
- **Estimate**: 4 hours
- **Description**:
  ```
  建立 RLS 整合測試套件，驗證多租戶隔離。
  
  **測試案例**:
  - [ ] 不同 tenant 數據隔離
  - [ ] service_role 全權限
  - [ ] admin 角色權限
  - [ ] 跨租戶訪問防護
  
  **檔案**: tests/test_rls.py
  
  **驗收標準**:
  - 10+ RLS 測試案例
  - 測試覆蓋率 Backend: 44% → 55%
  ```

### B. 自動回滾機制

**Issue #5: 擴展健康檢查**
- **Title**: [Week 1] 擴展 post-deploy-health.yml - DB/Redis/API 檢查
- **Labels**: `week-1`, `ci-cd`, `health-check`, `priority:high`
- **Estimate**: 3 hours
- **Description**:
  ```
  擴展現有健康檢查，新增數據庫、Redis、關鍵 API 端點測試。
  
  **新增檢查**:
  - [ ] Supabase 連線檢查
  - [ ] Redis 連線檢查
  - [ ] /api/governance/status 端點
  - [ ] /api/business-intelligence/summary 端點
  
  **檔案**: .github/workflows/post-deploy-health.yml
  
  **驗收標準**:
  - 健康檢查覆蓋 4+ 關鍵組件
  - 失敗時詳細錯誤日誌
  ```

**Issue #6: 實施自動回滾邏輯**
- **Title**: [Week 1] 實施自動回滾機制 (GitHub Actions)
- **Labels**: `week-1`, `ci-cd`, `rollback`, `priority:high`
- **Estimate**: 5 hours
- **Description**:
  ```
  實施健康檢查失敗時自動回滾部署。
  
  **任務**:
  - [ ] 新增 RENDER_API_KEY 到 GitHub Secrets
  - [ ] 實施 rollback job (連續2次失敗觸發)
  - [ ] 使用 Render API rollback
  - [ ] Slack/Email 通知
  
  **檔案**: .github/workflows/auto-rollback.yml
  
  **驗收標準**:
  - 健康檢查失敗 → 自動回滾
  - MTTR < 5 分鐘
  - 通知機制運作
  ```

**Issue #7: 回滾測試與驗證**
- **Title**: [Week 1] 測試自動回滾機制
- **Labels**: `week-1`, `ci-cd`, `testing`, `priority:medium`
- **Estimate**: 3 hours
- **Description**:
  ```
  模擬部署失敗，驗證自動回滾行為。
  
  **測試場景**:
  - [ ] 模擬健康檢查失敗
  - [ ] 驗證回滾觸發
  - [ ] 確認服務恢復
  - [ ] 檢查通知發送
  
  **驗收標準**:
  - 回滾測試通過
  - 記錄回滾時間 (target: <5 min)
  ```

### C. 文檔與知識轉移

**Issue #8: 更新 RLS 實施指南**
- **Title**: [Week 1] 更新 RLS_IMPLEMENTATION_GUIDE.md
- **Labels**: `week-1`, `documentation`, `priority:medium`
- **Estimate**: 2 hours
- **Description**:
  ```
  更新 RLS 實施指南，新增多租戶最佳實踐。
  
  **新增內容**:
  - [ ] Migration 002 說明
  - [ ] Helper functions 使用
  - [ ] RLS 測試策略
  - [ ] 常見問題 FAQ
  
  **檔案**: docs/RLS_IMPLEMENTATION_GUIDE.md
  ```

**Issue #9: 自癒 CI/CD 文檔**
- **Title**: [Week 1] 建立 SELF_HEALING_CICD.md
- **Labels**: `week-1`, `documentation`, `priority:medium`
- **Estimate**: 2 hours
- **Description**:
  ```
  建立自癒 CI/CD 機制文檔。
  
  **內容**:
  - [ ] 自動回滾流程說明
  - [ ] 健康檢查配置
  - [ ] 告警機制
  - [ ] 故障排查指南
  
  **檔案**: docs/SELF_HEALING_CICD.md
  ```

---

## 📊 Week 1 里程碑

**Milestone: Week 1 Complete**
- **Due Date**: 2025-10-27
- **Success Criteria**:
  - ✅ 完整 RLS 多租戶隔離 (3+ 表)
  - ✅ 自動回滾機制運作
  - ✅ 測試覆蓋率 Backend: 44% → 55%
  - ✅ 文檔更新完成
  - ✅ Zero production incidents

---

## 🏷️ Labels 定義

- `week-1`, `week-2`, `week-3`, `week-4` - 週度標籤
- `rls` - Row Level Security 相關
- `ci-cd` - CI/CD 流程相關
- `testing` - 測試相關
- `database` - 數據庫相關
- `documentation` - 文檔相關
- `priority:high` - 高優先級
- `priority:medium` - 中優先級
- `priority:low` - 低優先級

---

## 📝 建立指令

### 方式1: GitHub CLI (需先 gh auth login)

```bash
# 建立 Project
gh project create --owner RC918 --title "October Sprint - Self-Healing CI/CD"

# 建立 Issues (範例)
gh issue create --repo RC918/morningai \
  --title "[Week 1] RLS Migration 001 - agent_tasks 表驗證" \
  --label "week-1,rls,database,priority:high" \
  --body "驗證 migration 001 (agent_tasks RLS) 是否已正確應用..."
```

### 方式2: GitHub Web Interface

1. 前往 https://github.com/RC918/morningai/projects
2. 點選 "New project"
3. 選擇 "Table" 模板
4. 命名: "October Sprint - Self-Healing CI/CD"
5. 逐一建立上述 Issues
6. 將 Issues 加入 Project Board

---

**END OF SPEC**
