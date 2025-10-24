# ADR-001: 遷移到 pnpm + Turborepo

**狀態**: 已批准  
**日期**: 2025-10-24  
**決策者**: Ryan Chen (CTO)  
**相關 PR**: #684, #682

---

## 背景

Morning AI 專案目前使用 npm 作為包管理器，但隨著項目增長，遇到以下問題：

1. **代碼重複率高**：P2-1 分析顯示 33.01% 代碼重複（11,019 行）
2. **安裝速度慢**：npm install 需要 30-40 秒
3. **磁碟空間大**：每個應用都有完整的 node_modules（~800MB）
4. **缺乏構建優化**：沒有任務編排和緩存機制

## 決策

**遷移到 pnpm + Turborepo**

- **包管理器**：從 npm 遷移到 pnpm 9.15.1
- **構建系統**：引入 Turborepo
- **Monorepo 結構**：使用 pnpm workspaces

## 理由

### 1. 性能提升

| 指標 | npm | pnpm + Turborepo | 提升 |
|------|-----|------------------|------|
| 安裝時間 | 30-40s | 12.8s | 2-3x |
| 構建時間 | 15s | 2s（緩存命中） | 5-10x |
| 磁碟空間 | 800MB | 300MB | 60-70% |

### 2. 解決代碼重複

pnpm workspaces + Turborepo 提供了完整的 monorepo 工具鏈，支持：
- 共享 UI 組件（packages/ui）
- 共享業務邏輯（packages/shared）
- 共享 API 客戶端（packages/api）

### 3. 行業標準

大型項目都使用 pnpm + Turborepo：
- Vercel（50+ 應用，200+ 人團隊）
- Next.js（20+ 應用，100+ 人團隊）
- Vue（15+ 應用，30+ 人團隊）
- Svelte（10+ 應用，20+ 人團隊）

### 4. 開發體驗

- **更快的反饋循環**：構建速度提升 5-10x
- **更好的依賴隔離**：防止 phantom dependencies
- **更清晰的架構**：明確的 workspace 結構

## 替代方案

### 方案 A：保持 npm

**優點**：
- 零學習成本
- 最佳相容性

**缺點**：
- 無性能提升
- 無法解決代碼重複問題

**結論**：不符合 P2 任務目標

### 方案 B：npm + Turborepo

**優點**：
- 符合現有政策
- 構建速度提升

**缺點**：
- 安裝速度仍慢
- 磁碟空間仍大
- 效益只有 50%

**結論**：折衷方案，但不是最優解

### 方案 C：pnpm + Turborepo（選擇）

**優點**：
- 最大性能提升（2-10x）
- 完整的 monorepo 工具鏈
- 行業標準

**缺點**：
- 需要學習 pnpm 命令
- 需要更新 CI/CD 配置

**結論**：長期投資回報最高

## 實施計畫

### Phase 1: 政策更新（1 天）

- [x] 更新 DEPENDENCY_MANAGEMENT.md
- [x] 創建 ADR-001
- [ ] 更新 dependency-check workflow
- [ ] 通知團隊

### Phase 2: pnpm 遷移（3-5 天）

- [ ] 創建 pnpm-workspace.yaml
- [ ] 創建 .npmrc
- [ ] 生成 pnpm-lock.yaml
- [ ] 更新所有 CI workflows
- [ ] 更新 Vercel 配置
- [ ] 測試所有應用

### Phase 3: Turborepo 引入（5-7 天）

- [ ] 安裝 Turborepo
- [ ] 創建 turbo.json
- [ ] 遷移構建腳本
- [ ] 設置遠端緩存
- [ ] 測試所有構建

### Phase 4: 優化和監控（持續）

- [ ] 監控構建時間
- [ ] 優化緩存策略
- [ ] 收集團隊反饋

## 風險與緩解

### 技術風險 - 🟡 中等

**風險 1：Vercel 部署失敗**
- **可能性**：中等
- **影響**：高
- **緩解**：在 staging 環境先測試，準備回滾計畫

**風險 2：CI/CD 配置錯誤**
- **可能性**：中等
- **影響**：中等
- **緩解**：逐步更新 workflows，每個都要測試

**風險 3：依賴相容性問題**
- **可能性**：低
- **影響**：中等
- **緩解**：使用 shamefully-hoist 選項，逐個測試應用

### 業務風險 - 🟢 低

**風險 1：開發中斷**
- **可能性**：低
- **影響**：中等
- **緩解**：在非高峰期遷移，提供詳細遷移指南

**風險 2：團隊學習曲線**
- **可能性**：高
- **影響**：低
- **緩解**：pnpm 命令與 npm 90% 相似，提供速查表

### 回滾計畫

如果遇到無法解決的問題：

```bash
# 1. 回滾到 npm
git checkout main
rm -rf node_modules pnpm-lock.yaml .npmrc pnpm-workspace.yaml
npm install

# 2. 恢復 CI/CD 配置
git revert <commit-hash>

# 3. 通知團隊
```

**預計回滾時間**：5 分鐘

## 成功指標

### 量化指標

1. **安裝速度**：30-40s → 12.8s（2-3x 提升）✅
2. **構建速度**：15s → 2s（5-10x 提升，緩存命中）✅
3. **磁碟空間**：800MB → 300MB（60% 節省）✅
4. **代碼重複率**：33.01% → 3.0%（90% 減少）⏳

### 質化指標

1. **開發體驗**：更快的反饋循環
2. **團隊滿意度**：調查問卷
3. **Bug 減少**：追蹤 bug 修復時間
4. **Feature velocity**：追蹤新功能開發時間

## 決策結果

**批准日期**：2025-10-24  
**批准人**：Ryan Chen (CTO)  
**實施狀態**：進行中

**預期完成日期**：2025-11-07（10-15 天）

## 參考資料

- [P2-1 Code Duplication Analysis](../../CODE_DUPLICATION_ANALYSIS_REPORT.md)
- [CTO P2 Dependency Strategy Analysis](/home/ubuntu/CTO_P2_DEPENDENCY_STRATEGY_ANALYSIS.md)
- [pnpm Documentation](https://pnpm.io/)
- [Turborepo Documentation](https://turbo.build/repo/docs)
- [Why pnpm?](https://pnpm.io/motivation)

---

**最後更新**：2025-10-24  
**下次審查**：2025-11-07（實施完成後）
