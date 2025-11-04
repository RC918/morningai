# Shared UI 採用公告

**發布日期**: 2025-11-01  
**生效日期**: 立即生效  
**目標受眾**: 全體開發團隊

---

## 📢 重要變更通知

MorningAI 現在使用統一的設計系統 `@morningai/shared-ui` 作為唯一的 UI 元件庫。所有新的 UI 開發都必須優先使用 shared-ui 中的元件。

---

## 🎯 為什麼要使用 Shared UI？

### 優勢

1. **一致性** - 所有應用使用相同的設計語言和視覺風格
2. **效率** - 不需要重複實作相同的元件
3. **品質** - 所有元件都經過測試、無障礙優化和性能優化
4. **維護性** - 集中維護，bug 修復和改進會自動惠及所有應用
5. **Apple-Level 設計** - 完整的 iOS 風格設計系統，包含 Spring 動畫和材質系統

### 包含的元件

Shared UI 提供 47 個完整測試的元件，包括：

- **Apple 風格元件**: Button, Input, Card, Modal, Toast, Badge, Avatar, Skeleton
- **表單元件**: Form, Select, Checkbox, Radio, Switch, Slider
- **佈局元件**: Container, Grid, Stack, Divider
- **導航元件**: Tabs, Breadcrumb, Pagination
- **反饋元件**: Alert, Progress, Spinner, Empty State
- **數據展示**: Table, List, Timeline, Stats

完整列表請參考 [Shared UI 使用指南](./shared-ui-guide.md)

---

## 📋 新的開發流程

### 開發新 UI 功能時

1. **檢查 shared-ui** - 先查看是否有可用的元件
   ```bash
   # 查看所有可用元件
   cat packages/shared-ui/src/index.ts
   
   # 或啟動 Storybook 瀏覽
   pnpm --filter frontend-dashboard storybook
   ```

2. **使用 shared-ui 元件**
   ```tsx
   import { Button, Card, Input } from '@morningai/shared-ui'
   
   function MyComponent() {
     return (
       <Card>
         <Input placeholder="輸入..." />
         <Button>提交</Button>
       </Card>
     )
   }
   ```

3. **如果需要新元件** - 加入 shared-ui 而非應用層
   - 在 `packages/shared-ui/src/components/` 建立元件
   - 加入 Storybook story
   - 更新 `packages/shared-ui/src/index.ts`
   - 執行測試和 build

4. **提交 PR 時** - 使用新的 PR 模板檢查清單
   - 確認已檢查 shared-ui 是否有可用元件
   - 確認沒有重複實作已存在的元件
   - 確認使用 Design Tokens 而非硬編碼

---

## 🚫 已廢棄的目錄

以下目錄已廢棄，**請勿使用**：

- ⛔ `tools/frontend-lab/` - 已遷移到 `handoff/20250928/40_App/frontend-dashboard/`

如果誤用廢棄目錄，CI 會自動阻止 PR 合併。

---

## 📚 資源與文件

### 必讀文件

1. **[Shared UI 使用指南](./shared-ui-guide.md)** - 完整的使用指南（399 行）
   - 安裝與配置
   - 元件使用範例
   - Design Tokens 參考
   - 動畫系統
   - 最佳實踐
   - FAQ

2. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - 貢獻規則
   - 設計系統與 Shared UI section
   - 如何加入新元件
   - PR 檢查清單

3. **[PR 模板](.github/pull_request_template.md)** - 新增設計系統檢查清單

### 互動式文件

- **Storybook**: `pnpm --filter frontend-dashboard storybook`
  - 瀏覽所有可用元件
  - 查看互動式範例
  - 測試不同的 props 組合

---

## 🔍 PR 審查重點

從現在開始，所有包含 UI 變更的 PR 都會被檢查：

### 必須確認的項目

- [ ] 已檢查 `@morningai/shared-ui` 是否有可用的元件
- [ ] 如果需要新元件，已將其加入 `packages/shared-ui/` 而非應用層
- [ ] 新元件已加入 Storybook story
- [ ] 沒有在應用層重複實作已存在於 shared-ui 的元件
- [ ] 使用 Design Tokens 而非硬編碼顏色/間距
- [ ] 沒有使用已廢棄的目錄（如 `tools/frontend-lab`）

### Code Review 重點

Reviewers 會特別注意：

1. 是否有重複實作 shared-ui 已有的元件
2. 是否正確使用 Design Tokens
3. 新元件是否應該加入 shared-ui
4. 是否遵循 Apple-Level 設計規範

---

## 💡 常見問題

### Q: 如果 shared-ui 沒有我需要的元件怎麼辦？

**A**: 評估該元件是否會被多個應用使用：
- **是** → 加入 `packages/shared-ui/`
- **否** → 可以在應用層實作，但仍需使用 Design Tokens

### Q: 我可以修改 shared-ui 元件的樣式嗎？

**A**: 
- **推薦**: 使用元件提供的 props 和 variants
- **可以**: 使用 className 覆蓋樣式（但要小心維護性）
- **不推薦**: 直接修改 shared-ui 的原始碼（除非是 bug 修復或功能增強）

### Q: 如何請求新的 Design Token？

**A**: 
1. 在 `packages/shared-ui/` 提交 issue
2. 說明使用場景和需求
3. 等待設計系統團隊審核
4. 批准後會加入 `tokens.json`

### Q: Storybook 在哪裡運行？

**A**: 
```bash
# 本地運行
pnpm --filter frontend-dashboard storybook

# 訪問 http://localhost:6006
```

### Q: 如何測試 shared-ui 元件？

**A**:
```bash
# 在 shared-ui 目錄
cd packages/shared-ui
pnpm test

# 或在 root 目錄
pnpm --filter @morningai/shared-ui test
```

---

## 📅 時間表

- **立即生效**: 所有新的 UI 開發必須優先使用 shared-ui
- **1 週內**: 熟悉 shared-ui 文件和 Storybook
- **2 週內**: 團隊分享會 - 討論使用經驗和問題
- **持續**: 收集反饋，改進 shared-ui

---

## 🤝 需要幫助？

### 聯絡方式

- **文件問題**: 查看 [Shared UI 使用指南](./shared-ui-guide.md)
- **技術問題**: 在 `packages/shared-ui/` 提交 issue
- **設計問題**: 聯絡設計系統團隊 (@RC918)
- **緊急問題**: 在開發群組詢問

### 反饋渠道

我們歡迎任何反饋！請通過以下方式提供：

1. **GitHub Issues** - 報告 bug 或請求功能
2. **PR Comments** - 在 code review 中討論
3. **團隊會議** - 定期分享使用經驗

---

## ✅ 行動項目

請所有開發者在本週內完成：

- [ ] 閱讀 [Shared UI 使用指南](./shared-ui-guide.md)
- [ ] 本地運行 Storybook 並瀏覽可用元件
- [ ] 檢查當前正在開發的功能是否可以使用 shared-ui
- [ ] 在下一個 PR 中使用新的 PR 模板檢查清單

---

**感謝大家的配合！讓我們一起打造世界級的設計系統。** 🎨✨
