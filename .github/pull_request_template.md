## 描述 (Description)

<!-- 簡要說明此 PR 的目的和變更內容 -->

## 設計系統檢查 (Design System Checklist)

如果此 PR 包含 UI 元件變更，請確認：

- [ ] 我已檢查 `@morningai/shared-ui` 是否有可用的元件
- [ ] 如果需要新元件，我已將其加入 `packages/shared-ui/` 而非應用層
- [ ] 新元件已加入 Storybook story（位於 `packages/shared-ui/src/stories/`）
- [ ] 我沒有在應用層重複實作已存在於 shared-ui 的元件
- [ ] 如使用設計 tokens，我已從 `@morningai/shared-ui` 匯入而非硬編碼
- [ ] 不適用 - 此 PR 不包含 UI 元件變更

**相關文件**: 
- 📚 [Shared UI 使用指南](../docs/shared-ui-guide.md)
- 🎨 Storybook: `pnpm --filter frontend-dashboard storybook`

## 提醒
- [ ] 不修改 OpenAPI/資料欄位（若要改，先提 RFC）
- [ ] 設計 PR 僅含 UI/文案/樣式；工程 PR 僅含 API/邏輯
- [ ] 避免使用已廢棄的目錄（如 `tools/frontend-lab`）
