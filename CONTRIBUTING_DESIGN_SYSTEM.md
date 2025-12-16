# 設計系統治理規則

本文檔定義 MorningAI 設計系統的治理規則和流程，防止未來設計系統漂移。

## 目錄

- [Token 管理](#token-管理)
- [組件開發規則](#組件開發規則)
- [Apple 組件規則](#apple-組件規則)
- [Dashboard 卡片 Archetypes](#dashboard-卡片-archetypes)
- [文檔同步](#文檔同步)
- [Code Review Checklist](#code-review-checklist)
- [CI 檢查](#ci-檢查)
- [廢棄組件處理](#廢棄組件處理)
- [#2303 驗收標準覆蓋矩陣](#2303-驗收標準覆蓋矩陣)

## Token 管理

### 唯一真相來源

`packages/shared-ui/src/tokens.json` 是設計系統 tokens 的唯一真相來源（Single Source of Truth）。

### Token 變更流程

1. **提出變更**：在 Issue 中說明變更動機和影響
2. **Design Review**：任何 token 變更必須經過 design review
3. **更新 tokens.json**：修改 `packages/shared-ui/src/tokens.json`
4. **重新建置**：執行 `pnpm --filter @morningai/shared-ui build`
5. **CI 驗證**：CI 會自動檢查 token 同步狀態

### Token 使用規範

<!-- 示意範例：展示正確與錯誤用法對比，非完整可執行程式碼 -->
```tsx
// ✅ 好的做法 - 使用 CSS 變數
<div className="bg-[var(--color-primary-600)] p-[var(--space-md)]">
  內容
</div>

// ❌ 不好的做法 - 硬編碼顏色
<div className="bg-blue-600 p-4">
  內容
</div>

// ❌ 不好的做法 - 使用 raw hex
<div style={{ backgroundColor: '#2563eb' }}>
  內容
</div>
```

## 組件開發規則

### 基本原則

1. **優先使用 shared-ui** - 開發新功能前，先檢查 shared-ui 是否有可用元件
2. **不要重複造輪子** - 避免在應用層重新實作已存在的元件
3. **新元件放 shared-ui** - 如果元件會被多個應用使用，應加入 shared-ui
4. **使用 Design Tokens** - 使用 CSS 變數而非硬編碼顏色/間距

### 組件位置決策樹

```
需要新組件？
├── 會被多個應用使用？
│   ├── 是 → 放在 packages/shared-ui/
│   └── 否 → 放在應用層（如 owner-console/src/components/）
└── 是現有 shared-ui 組件的變體？
    ├── 是 → 在應用層建立 wrapper/adapter
    └── 否 → 評估是否應該擴展 shared-ui 組件
```

### 禁止事項

- ❌ 在應用層直接 import Radix UI（`@radix-ui/react-*`）
- ❌ 在應用層直接 import MUI（`@mui/*`）
- ❌ 在應用層直接 import Headless UI（`@headlessui/*`）
- ❌ 在應用層直接 import Chakra UI（`@chakra-ui/*`）

### 允許的例外

- ✅ `lucide-react`（圖示）
- ✅ `recharts`（圖表）
- ✅ `date-fns`（日期處理）
- ✅ `framer-motion`（動畫）

## Apple 組件規則

### 歸屬原則

| 組件類型 | 歸屬位置 | 說明 |
|----------|----------|------|
| **視覺原語** | `@morningai/shared-ui` | 如 AppleButton，純視覺、無業務邏輯 |
| **體驗組件** | 各應用層 | 如 AppleHero、ControlCenter，包含業務邏輯或僅特定應用使用 |
| **Adapter** | 各應用層 | 包裝 shared-ui 組件，加入 app-specific 行為（haptics 等） |

### Apple 組件開發規則

1. **消費 Design Tokens**：新 Apple 組件必須消費 design tokens（不可自定義平行色彩系統）
2. **跨應用共用**：若需跨應用共用，必須先在 shared-ui 建立基礎視覺組件
3. **應用層 Adapter**：應用層可建立 adapter 加入 app-specific 行為
4. **主題一致性**：Apple 主題（theme-apple.css）必須基於 tokens.json 的 CSS 變數

### 現有 Apple 組件清單

**shared-ui（跨應用）：**

| 組件 | 說明 |
|------|------|
| `AppleButton` | iOS 風格按鈕（4 種變體，3 種尺寸，Spring 動畫） |
| `AppleInput` | iOS 風格輸入框（浮動標籤，錯誤/成功狀態） |

**frontend-dashboard（產品特定）：**

| 組件 | 說明 |
|------|------|
| `apple-action-sheet` | iOS 風格操作表 |
| `apple-control-center` | iOS 風格控制中心 |
| `apple-live-activity` | iOS 風格實時活動 |
| `apple-modal` | iOS 風格對話框 |
| `apple-picker` | iOS 風格選擇器 |
| `apple-segmented-control` | iOS 風格分段控制器 |
| `apple-sheet` | iOS 風格底部抽屜 |
| `apple-spotlight` | iOS 風格 Spotlight 搜尋 |
| `apple-tab-bar` | iOS 風格標籤欄 |
| `apple-toast` | iOS 風格輕提示 |

### Apple 組件遷移指南

當 frontend-dashboard 中的 Apple 組件需要被其他應用使用時：

1. 提取純視覺邏輯到 shared-ui
2. 保留業務邏輯在應用層
3. 建立 adapter 模式連接兩者

<!-- 示意範例：展示 Adapter 模式的結構，實際實作需依組件需求調整 -->
```tsx
// packages/shared-ui/src/components/ui/apple-modal-base.tsx
// 純視覺組件，無業務邏輯，接收 onConfirm 作為 prop 但不處理業務邏輯
export function AppleModalBase({ children, onConfirm, ...props }) {
  return (
    <div className="apple-modal-base" {...props}>
      {children}
      {/* 內部確認按鈕會綁定 onConfirm */}
      <button onClick={onConfirm}>確認</button>
    </div>
  )
}

// frontend-dashboard/src/components/apple/apple-modal.tsx
// 應用層 adapter，加入業務邏輯
import { AppleModalBase } from '@morningai/shared-ui'

export function AppleModal({ onConfirm, ...props }) {
  const handleConfirm = () => {
    // 業務邏輯
    trackEvent('modal_confirm')
    onConfirm?.()
  }
  return <AppleModalBase {...props} onConfirm={handleConfirm} />
}
```

## Dashboard 卡片 Archetypes

### Archetype 選擇指南

| Archetype | 用途 | Icon 規格 | 互動性 | 使用場景 |
|-----------|------|-----------|--------|----------|
| **StatCard** | KPI 展示 | 40×40px 圓形 | 無 | 數據統計、指標展示 |
| **StatusCard** | 狀態篩選 | 28×28px 方形 | 有 (onClick, isActive) | 篩選器、狀態切換 |
| **MetricCard** | 實體摘要 | 依內容 | 無 | 詳細指標、趨勢展示 |
| **SettingsCard** | 設定面板 | 依內容 | 按鈕動作 | 設定頁面、配置面板 |
| **SectionCard** | 區塊容器 | 可選 | 可選 action | 內容分組、區塊標題 |

### 卡片開發規則

1. **優先使用 Archetype**：新卡片應優先使用現有 archetype
2. **不要自訂卡片樣式**：避免在應用層自訂卡片樣式
3. **擴展而非重寫**：如需新功能，應擴展現有 archetype 而非重寫

### 卡片使用範例

<!-- ✅ 可複製範例：包含完整 imports，可直接使用 -->
```tsx
import { 
  StatCard, 
  StatusCard, 
  SettingsCard,
  SectionCard,
  Button
} from '@morningai/shared-ui'
import { DollarSign, Shield } from 'lucide-react'

// StatCard - KPI 展示
<StatCard 
  label="總收入" 
  value="$45,231" 
  trend="+12.5%" 
  icon={<DollarSign />}
/>

// StatusCard - 狀態篩選
<StatusCard 
  label="進行中" 
  count={12} 
  isActive={true}
  onClick={() => setFilter('active')}
/>

// SettingsCard - 設定面板
<SettingsCard
  title="雙因素認證"
  description="增強帳戶安全性"
  icon={<Shield />}
  action={<Button>設定</Button>}
/>
```

## 文檔同步

### 文檔更新規則

1. **新組件必須同時建立 Storybook story**
2. **PR 描述必須說明是否影響設計系統**
3. **定期審查文檔與實際的一致性**

### 文檔位置

| 文檔 | 位置 | 說明 |
|------|------|------|
| 組件 README | `packages/shared-ui/README.md` | 組件清單和使用說明 |
| Storybook Stories | `packages/shared-ui/src/components/**/*.stories.tsx` | 互動式文檔 |
| 使用指南 | `docs/shared-ui-guide.md` | 完整使用指南 |
| 速查表 | `docs/UI_UX_CHEATSHEET.md` | 常用命令和路徑 |
| 本文檔 | `CONTRIBUTING_DESIGN_SYSTEM.md` | 治理規則 |

## Code Review Checklist

### 一般組件 Checklist

- [ ] 是否使用 shared-ui 組件？
- [ ] 是否遵循卡片 archetype 規格？
- [ ] 是否使用 design tokens？
- [ ] 是否有 Storybook story？
- [ ] 是否有單元測試？

### Apple 組件 Checklist

- [ ] 是否消費 tokens.json 的 CSS 變數？
- [ ] 若為視覺原語，是否放在 shared-ui？
- [ ] 若為應用層 adapter，是否正確包裝 shared-ui 組件？
- [ ] 是否有完整的 stories + tests + a11y tests？
- [ ] 是否支援 `prefers-reduced-motion`？

### Token 變更 Checklist

- [ ] 是否更新了 `packages/shared-ui/src/tokens.json`？
- [ ] 是否執行了 `pnpm --filter @morningai/shared-ui build`？
- [ ] 是否更新了相關文檔？
- [ ] 是否經過 design review？

## CI 檢查

### 自動化檢查項目

| 檢查項目 | 說明 | 阻擋合併 |
|----------|------|----------|
| Token 同步檢查 | 驗證 tokens.json 與 CSS 變數一致 | 是 |
| UI Import 檢查 | 禁止直接 import UI 元件庫 | 是 |
| Hex Color 檢查 | 偵測 raw hex colors | 是 |
| Storybook Build | 驗證 Storybook 可正常建置 | 是 |
| A11y 測試 | 無障礙測試 | 是 |

### 執行 Audit 腳本

```bash
# 執行完整 audit
./scripts/phase2_audit.sh

# 針對特定檔案
./scripts/phase2_audit.sh --file <target_file>

# 量測 bundle size
./scripts/measure-bundle-size.sh
```

## 廢棄組件處理

### 標記廢棄

當組件需要廢棄時：

1. 在組件上方加入 `@deprecated` JSDoc 註解
2. 在 CONTRIBUTING_DESIGN_SYSTEM.md 中記錄
3. 設定移除時間表

<!-- 示意範例：展示 @deprecated 標記格式 -->
```tsx
/**
 * @deprecated 請使用 @morningai/shared-ui 的 StatCard
 * 將在 v2.0.0 移除
 */
export function LegacyStatCard() {
  // ...
}
```

### 已廢棄組件清單

| 組件 | 位置 | 替代方案 | 移除時間 |
|------|------|----------|----------|
| `LegacyCard` | owner-console | 依使用情境選擇（見下方 Decision Flow） | Phase 3 完成後 |

### LegacyCard 替換 Decision Flow

遷移 `LegacyCard` 時，依以下流程選擇替代方案：

```
1. 卡片是否只是純容器（無特定語意）？
   └── 是 → 使用 `Card`（通用容器）

2. 是否用於展示 KPI / 數據統計？
   └── 是 → 使用 `StatCard`
   └── 典型場景：總收入、用戶數、轉換率

3. 是否用於狀態篩選 / 切換？
   └── 是 → 使用 `StatusCard`
   └── 典型場景：任務狀態篩選、標籤切換

4. 是否用於設定面板 / 配置項？
   └── 是 → 使用 `SettingsCard`
   └── 典型場景：2FA 設定、通知偏好、API 金鑰

5. 是否用於區塊分組 / 標題容器？
   └── 是 → 使用 `SectionCard`
   └── 典型場景：Dashboard 區塊、表單分組

6. 都不符合？
   └── 提 Issue 評估是否需要新增 Archetype
   └── 或擴展現有 shared-ui 組件
```

**典型場景對照表**：

| Archetype | 典型場景 | 常見 Anti-pattern |
|-----------|----------|-------------------|
| `Card` | 純容器、自訂內容 | 用於 KPI 展示（應用 StatCard） |
| `StatCard` | 總收入、用戶數、轉換率 | 加入互動按鈕（應用 SettingsCard） |
| `StatusCard` | 任務狀態篩選、標籤切換 | 展示詳細數據（應用 StatCard） |
| `SettingsCard` | 2FA 設定、通知偏好 | 純展示無動作（應用 StatCard） |
| `SectionCard` | Dashboard 區塊、表單分組 | 單一 KPI 展示（應用 StatCard） |

## #2303 驗收標準覆蓋矩陣

本文檔對應 [Issue #2303](https://github.com/RC918/morningai/issues/2303) 的驗收標準：

| 驗收標準 | 文檔位置 | 執行方式 | 狀態 |
|----------|----------|----------|------|
| 建立 `CONTRIBUTING_DESIGN_SYSTEM.md` | 根目錄 | Manual | ✅ |
| PR template 新增設計系統 checklist | `.github/pull_request_template.md` | Manual | ✅ |
| CI 檢查 token 同步狀態 | `token-sync-check.yml` | **CI（結構驗證）** | ✅ |
| 標記舊組件為 deprecated | [廢棄組件處理](#廢棄組件處理) | Manual（文檔記錄） | ✅ |
| Apple 組件歸屬規則章節 | [Apple 組件規則](#apple-組件規則) | Manual | ✅ |
| Apple 組件 Code Review checklist | [Code Review Checklist](#code-review-checklist) | Manual | ✅ |

**備註**：
- Token 同步 CI 目前驗證 `tokens.json` 結構完整性（必要 categories、accessibility tokens）
- 完整的 CSS 變數同步驗證將在後續 Issue 中實作

## 相關文檔

- [CONTRIBUTING.md](CONTRIBUTING.md) - 一般貢獻指南
- [docs/shared-ui-guide.md](docs/shared-ui-guide.md) - Shared UI 使用指南
- [docs/UI_UX_CHEATSHEET.md](docs/UI_UX_CHEATSHEET.md) - UI/UX 速查表
- [DESIGN_SYSTEM_GUIDELINES.md](DESIGN_SYSTEM_GUIDELINES.md) - 設計系統指南

---

**最後更新**: 2025-12-15
