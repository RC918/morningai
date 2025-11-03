## 描述 (Description)

<!-- 簡要說明此 PR 的目的和變更內容 -->

## i18n 檢查清單（強制）

<!-- 所有用戶可見的變更都必須符合 i18n 要求 -->

- [ ] 所有用戶可見字串使用 `t()` 或 `<Trans>`（無硬編碼字串）
- [ ] 新 translation keys 已加入 `en-US.json` 和 `zh-TW.json`
- [ ] Translation keys 使用適當的命名空間（例如：`settings.2fa.title`）
- [ ] 無障礙屬性（`alt`、`aria-label`、`title`、`placeholder`）已翻譯
- [ ] ESLint i18n 規則通過（無 `i18next/no-literal-string` 錯誤）
- [ ] 已測試語言切換（如有 UI 變更）
- [ ] 不適用 - 此 PR 無用戶可見變更

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
- 📖 [i18n 政策](../CONTRIBUTING.md#i18n-政策強制執行)
- 🎨 Storybook: `pnpm --filter frontend-dashboard storybook`

## 程式碼品質檢查

- [ ] ESLint 通過（0 warnings）：`pnpm lint`
- [ ] TypeScript 類型檢查通過：`pnpm typecheck`
- [ ] 無 `any` 類型（使用適當的類型定義）
- [ ] 所有測試通過：`pnpm test`
- [ ] 程式碼遵循現有模式和慣例

## 提醒
- [ ] 不修改 OpenAPI/資料欄位（若要改，先提 RFC）
- [ ] 設計 PR 僅含 UI/文案/樣式；工程 PR 僅含 API/邏輯
- [ ] 避免使用已廢棄的目錄（如 `tools/frontend-lab`）
