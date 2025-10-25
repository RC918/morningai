# UI/UX 快速上手指南 (5 分鐘)

**目標讀者**: 新加入團隊的設計師、前端工程師、產品經理  
**閱讀時間**: 5 分鐘  
**最後更新**: 2025-10-25

---

## 🎯 三步驟開始使用

### 步驟 1: 了解我們完成了什麼 (1 分鐘)

MorningAI 已完成 **8-Week UI/UX Roadmap** 和 **Phase 1 Week 1 Apple-Level 設計系統**：

✅ **100% 完成** - 18/18 Issues, 16 PRs, 10,000+ 行代碼  
✅ **完整測試框架** - 可用性測試、A/B 測試、指標分析  
✅ **Apple-Level 設計系統** - 5 個核心設計系統（字體、色彩、材質、陰影、間距）  
✅ **生產就緒** - 所有功能已合併至 main 分支

**快速查看成果**:
```bash
# 查看完整功能清單
cat docs/UI_UX_ISSUE_STATUS.md

# 查看 Week 7-8 測試框架實作
cat docs/UX/WEEK_7_8_COMPLETION_REPORT.md
```

### 步驟 2: 找到你需要的資源 (2 分鐘)

#### 🎨 設計師

**你需要的文檔**:
- [Design Tokens](docs/UX/tokens.json) - 色彩、字體、間距、圓角、陰影系統
- [設計系統文檔](docs/UX/) - 字體系統、色彩系統、材質系統、陰影系統、間距系統
- [設計系統指南](DESIGN_SYSTEM_GUIDELINES.md) - 設計規範與最佳實踐
- [UI/UX 資源指南](docs/UI_UX_RESOURCES.md) - 完整資源索引

**你的工作流程**:
1. 使用 Design Tokens 設計新組件
2. 創建 Design PR（只改動 `docs/UX/**`, `docs/**.md`, `frontend/樣式與文案`）
3. 提交 PR 等待審查

#### 💻 前端工程師

**你需要的資源**:
- [組件庫](handoff/20250928/40_App/frontend-dashboard/src/components/ui/) - 77 個現成組件
- [Storybook 文檔](#啟動-storybook) - 互動式組件預覽
- [快速參考卡](docs/UI_UX_CHEATSHEET.md) - 常用命令與路徑

**你的工作流程**:
1. 查找現有組件（避免重複造輪子）
2. 使用 Design Tokens 保持一致性
3. 創建 Engineering PR（只改動 `**/api/**`, `**/src/**`）
4. 運行測試並提交 PR

#### 📊 產品經理

**你需要的報告**:
- [UI/UX 審查報告](docs/UX/COMPREHENSIVE_UI_UX_AUDIT_REPORT.md) - 83/100 分評估
- [8-Week 路線圖總結](docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md) - 完整進度追蹤
- [可用性測試計畫](docs/UX/USABILITY_TESTING_PLAN.md) - 測試方法與流程

### 步驟 3: 啟動開發環境 (2 分鐘)

#### 啟動 Storybook

```bash
# 進入前端目錄
cd handoff/20250928/40_App/frontend-dashboard

# 安裝依賴（首次運行）
pnpm install

# 啟動 Storybook
pnpm storybook
```

瀏覽器會自動打開 `http://localhost:6006`，你可以看到所有組件的互動式文檔。

#### 啟動開發伺服器

```bash
# 在前端目錄
pnpm dev
```

應用會在 `http://localhost:5173` 啟動。

#### 查看 Design Tokens

```bash
# 查看完整 Token 系統
cat docs/UX/tokens.json | jq .

# 查看色彩系統
cat docs/UX/tokens.json | jq .colors

# 查看間距系統
cat docs/UX/tokens.json | jq .spacing
```

---

## 📚 下一步學習

### 深入了解設計系統

- **[UI/UX 資源指南](docs/UI_UX_RESOURCES.md)** - 完整資源索引（378 行）
- **[UI/UX 速查表](docs/UI_UX_CHEATSHEET.md)** - 一頁速查表
- **[設計系統增強路線圖](docs/UX/DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md)** - 8 週執行計畫

### 了解貢獻規則

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - 分工規則、API 變更流程、驗收標準
- **[PR 規則](#pr-規則快速參考)** - 設計 PR vs 工程 PR

### 查看已完成工作

- **[UI/UX Issue 狀態追蹤](docs/UI_UX_ISSUE_STATUS.md)** - 18/18 Issues 完成狀態
- **[Week 7-8 完成報告](docs/UX/WEEK_7_8_COMPLETION_REPORT.md)** - 測試框架實作報告
- **[8-Week 路線圖總結](docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md)** - 完整進度追蹤

---

## 🚀 常見任務快速參考

### 任務 1: 使用現有組件

```bash
# 1. 搜尋組件
ls handoff/20250928/40_App/frontend-dashboard/src/components/ui/

# 2. 查看組件源碼
cat handoff/20250928/40_App/frontend-dashboard/src/components/ui/button.jsx

# 3. 在 Storybook 中查看範例
pnpm storybook
# 瀏覽器打開後，左側導航找到 "Button"
```

### 任務 2: 創建新組件

```bash
# 1. 查看 Design Tokens
cat docs/UX/tokens.json

# 2. 參考現有組件結構
cat handoff/20250928/40_App/frontend-dashboard/src/components/ui/card.jsx

# 3. 創建新組件（使用 Tokens）
# 在 src/components/ui/ 創建新文件

# 4. 創建 Storybook story
# 在 src/stories/ 創建對應的 .stories.jsx
```

### 任務 3: 查找特定功能的實作

```bash
# 搜尋關鍵字
rg "useUndoRedo" --type tsx

# 查找組件使用範例
rg "import.*Button" --type tsx

# 查找 Design Token 使用
rg "theme-morning-ai" --type tsx
```

### 任務 4: 提交 PR

```bash
# 1. 創建分支
git checkout -b devin/$(date +%s)-your-feature-name

# 2. 提交變更
git add <files>
git commit -m "feat(ux): Your feature description"

# 3. 推送並創建 PR
git push origin devin/$(date +%s)-your-feature-name
gh pr create --title "feat(ux): Your feature" --body "Description"
```

---

## 🆘 需要幫助？

### PR 規則快速參考

**Design PR** (設計師):
- ✅ 允許: `docs/UX/**`, `docs/**.md`, `frontend/樣式與文案`
- ❌ 禁止: `**/api/**`, `**/src/**` 後端與 API

**Engineering PR** (工程師):
- ✅ 允許: `**/api/**`, `**/src/**`, `handoff/**/30_API/openapi/**`
- ❌ 禁止: `docs/UX/**` 設計稿資源

### 常見問題

**Q: 如何查找特定組件的使用方式？**  
A: 查看 Storybook (`pnpm storybook`) 或搜尋專案中的使用範例 (`rg "import.*Button" --type tsx`)

**Q: 如何確保我的改動不會破壞現有樣式？**  
A: 使用 Design Tokens 而非硬編碼值，在 `.theme-morning-ai` 容器內工作

**Q: 如何避免重複工作？**  
A: 先查看 [UI/UX Issue 狀態追蹤](docs/UI_UX_ISSUE_STATUS.md) 和 [UI/UX 資源指南](docs/UI_UX_RESOURCES.md)

### 聯繫方式

- **GitHub Issues**: [UI/UX Milestone #6](https://github.com/RC918/morningai/milestone/6)
- **文檔問題**: 在 GitHub 創建 Issue 並標記 `documentation`
- **設計系統問題**: 在 GitHub 創建 Issue 並標記 `design-system`

---

## ✅ 檢查清單

完成以下檢查清單，確保你已準備好開始工作：

- [ ] 閱讀本快速上手指南（5 分鐘）
- [ ] 啟動 Storybook 並瀏覽組件庫
- [ ] 查看 Design Tokens (`docs/UX/tokens.json`)
- [ ] 了解 PR 規則（Design PR vs Engineering PR）
- [ ] 查看 [UI/UX 速查表](docs/UI_UX_CHEATSHEET.md)
- [ ] 閱讀 [UI/UX 資源指南](docs/UI_UX_RESOURCES.md)（可選，深入了解）

---

**下一步**: 查看 [UI/UX 速查表](docs/UI_UX_CHEATSHEET.md) 獲取常用命令與路徑的快速參考。
