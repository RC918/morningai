# Manual Testing Guide: Screen Reader Accessibility

## 目的

本指南提供完整的螢幕閱讀器手動測試流程，確保 MorningAI Dashboard 符合 WCAG 2.1 Level AAA 標準。

## 測試環境設置

### 必需的螢幕閱讀器

#### macOS
- **VoiceOver** (內建)
  - 啟動: `Cmd + F5` 或 系統偏好設定 > 輔助使用 > VoiceOver
  - 版本: macOS 12.0+ 推薦

#### Windows
- **NVDA** (免費開源)
  - 下載: https://www.nvaccess.org/download/
  - 版本: 2023.1+ 推薦
  - 啟動: `Ctrl + Alt + N`

- **JAWS** (商業軟體)
  - 下載: https://www.freedomscientific.com/products/software/jaws/
  - 版本: 2023+ 推薦
  - 免費試用: 40 分鐘模式

#### Linux
- **Orca** (內建於 GNOME)
  - 啟動: `Super + Alt + S`
  - 版本: 42.0+ 推薦

### 瀏覽器支援

| 螢幕閱讀器 | 推薦瀏覽器 | 次要選擇 |
|-----------|-----------|---------|
| VoiceOver | Safari | Chrome |
| NVDA | Firefox | Chrome |
| JAWS | Chrome | Firefox |
| Orca | Firefox | Chrome |

## 測試前準備

### 1. 環境檢查

```bash
# 啟動開發伺服器
cd handoff/20250928/40_App/frontend-dashboard
npm run dev

# 確認無障礙設定已整合
# 檢查 src/App.jsx 包含 AccessibilityProvider
```

### 2. 測試帳號

- **測試帳號**: ryan@morningai.com
- **密碼**: (使用開發環境預設密碼)
- **角色**: Owner

### 3. 測試瀏覽器設置

- 清除快取和 cookies
- 關閉瀏覽器擴充功能（可能干擾測試）
- 確保瀏覽器縮放為 100%

## 核心測試流程

### Test 1: 頁面結構與地標 (Landmarks)

**目標**: 驗證頁面使用正確的 HTML5 語義標籤和 ARIA 地標

#### VoiceOver 測試步驟

1. **啟動 VoiceOver**: `Cmd + F5`
2. **開啟 Rotor**: `VO + U` (VO = Ctrl + Option)
3. **選擇 Landmarks**: 使用左右箭頭切換到 "Landmarks"
4. **驗證地標**:
   ```
   預期聽到:
   - "navigation" (Sidebar)
   - "main" (主內容區域)
   - "banner" (頁首，如果有)
   - "contentinfo" (頁尾，如果有)
   ```

#### NVDA 測試步驟

1. **啟動 NVDA**: `Ctrl + Alt + N`
2. **開啟 Elements List**: `NVDA + F7`
3. **選擇 Landmarks**: 點擊 "Landmarks" 標籤
4. **驗證地標**: 應看到與 VoiceOver 相同的地標列表

#### 通過標準

- ✅ 所有主要區域都有適當的地標
- ✅ 地標名稱清晰且描述性強
- ✅ 沒有多餘或重複的地標
- ✅ 主內容區域標記為 `<main>` 或 `role="main"`

---

### Test 2: 標題層級結構 (Heading Hierarchy)

**目標**: 驗證標題層級正確且邏輯清晰

#### VoiceOver 測試步驟

1. **開啟 Rotor**: `VO + U`
2. **選擇 Headings**: 切換到 "Headings"
3. **驗證層級**:
   ```
   預期結構:
   H1: "Morning AI" (頁面標題)
   H2: "Dashboard" / "Strategies" 等 (主要區段)
   H3: 子區段標題
   H4: 更細的子標題
   ```

#### NVDA 測試步驟

1. **開啟 Elements List**: `NVDA + F7`
2. **選擇 Headings**: 點擊 "Headings" 標籤
3. **檢查層級**: 確認沒有跳級（例如 H1 → H3）

#### 通過標準

- ✅ 每頁只有一個 H1
- ✅ 標題層級不跳級（H1 → H2 → H3，不是 H1 → H3）
- ✅ 標題文字清晰描述內容
- ✅ 所有主要區段都有標題

---

### Test 3: 表單與輸入欄位

**目標**: 驗證所有表單控制項都有正確的標籤和說明

#### 測試頁面
- 登入頁面 (`/login`)
- 設定頁面 (`/settings`)
- 策略管理頁面 (`/strategies`)

#### VoiceOver 測試步驟

1. **導航到表單**: `VO + Cmd + J` (跳到下一個表單控制項)
2. **驗證每個輸入欄位**:
   ```
   預期聽到:
   - 欄位標籤 (例如: "Email")
   - 欄位類型 (例如: "text field" 或 "password field")
   - 必填狀態 (例如: "required")
   - 錯誤訊息 (如果有)
   - 說明文字 (如果有)
   ```

#### NVDA 測試步驟

1. **表單模式**: NVDA 會自動進入表單模式
2. **使用 Tab 鍵**: 在表單控制項間移動
3. **驗證朗讀內容**: 確認與 VoiceOver 相同的資訊

#### 通過標準

- ✅ 所有輸入欄位都有可見標籤
- ✅ 標籤與輸入欄位正確關聯 (`<label for="...">`)
- ✅ 必填欄位標記為 `required` 或 `aria-required="true"`
- ✅ 錯誤訊息與欄位關聯 (`aria-describedby`)
- ✅ 說明文字清晰且有幫助

---

### Test 4: 按鈕與互動元素

**目標**: 驗證所有按鈕和連結都有清晰的標籤

#### VoiceOver 測試步驟

1. **導航到按鈕**: `VO + Cmd + J`
2. **驗證每個按鈕**:
   ```
   預期聽到:
   - 按鈕文字或 aria-label
   - "button" 角色
   - 狀態 (例如: "pressed" 或 "expanded")
   ```

#### 測試案例

| 元素 | 預期朗讀 | 位置 |
|------|---------|------|
| 登入按鈕 | "Login, button" | `/login` |
| 深色模式切換 | "Toggle dark mode, button" | Sidebar |
| 無障礙設定 | "Open accessibility settings, button" | Sidebar |
| 儲存按鈕 | "Save, button" | `/settings` |

#### 通過標準

- ✅ 所有按鈕都有描述性文字或 `aria-label`
- ✅ 圖示按鈕有 `aria-label`（不依賴視覺圖示）
- ✅ 切換按鈕有 `aria-pressed` 狀態
- ✅ 展開/收合按鈕有 `aria-expanded` 狀態

---

### Test 5: 動態內容與即時區域 (Live Regions)

**目標**: 驗證動態更新的內容會被螢幕閱讀器通知

#### 測試場景

1. **Toast 通知**
   - 觸發: 登入成功、儲存設定、錯誤訊息
   - 預期: 螢幕閱讀器自動朗讀通知內容

2. **載入狀態**
   - 觸發: 頁面載入、資料更新
   - 預期: 朗讀 "Loading..." 或相關訊息

3. **表單驗證**
   - 觸發: 提交無效表單
   - 預期: 朗讀錯誤訊息

#### VoiceOver 測試步驟

1. **觸發動態更新**: 例如點擊 "Save" 按鈕
2. **等待通知**: VoiceOver 應自動朗讀更新
3. **驗證內容**: 確認朗讀的內容正確且清晰

#### NVDA 測試步驟

1. **確認 NVDA 設定**: 設定 > 物件呈現 > 報告動態內容變更 (已啟用)
2. **觸發動態更新**
3. **驗證朗讀**

#### 通過標準

- ✅ Toast 通知使用 `role="status"` 或 `aria-live="polite"`
- ✅ 緊急通知使用 `aria-live="assertive"`
- ✅ 載入狀態有 `aria-busy="true"` 或 `aria-live` 區域
- ✅ 錯誤訊息即時通知使用者

---

### Test 6: 無障礙設定面板

**目標**: 驗證無障礙設定面板本身的可訪問性

#### 測試步驟

1. **開啟設定面板**:
   - 使用鍵盤: Tab 到 "Accessibility" 按鈕，按 Enter
   - 使用螢幕閱讀器: 導航到按鈕並啟動

2. **驗證面板開啟**:
   ```
   預期聽到:
   - "Accessibility settings opened" (即時通知)
   - "Accessibility Settings, dialog" (焦點移到面板)
   ```

3. **導航設定項目**:
   - 使用 Tab 鍵在控制項間移動
   - 驗證每個設定的標籤和狀態

4. **測試焦點陷阱**:
   - 按 Tab 到最後一個控制項
   - 再按 Tab，焦點應回到第一個控制項
   - 按 Shift + Tab，焦點應移到前一個控制項

5. **關閉面板**:
   - 按 Escape 鍵
   - 驗證焦點返回到觸發按鈕

#### 設定項目驗證

| 設定 | 預期朗讀 | 控制項類型 |
|------|---------|-----------|
| Reduced Motion | "Reduced Motion, checkbox, checked/unchecked" | Checkbox |
| High Contrast | "High Contrast, checkbox" | Checkbox |
| Font Size | "Font Size, Medium, button" | Radio group |
| Screen Reader | "Screen Reader Announcements, checkbox" | Checkbox |

#### 通過標準

- ✅ 面板開啟時有即時通知
- ✅ 焦點自動移到面板內第一個控制項
- ✅ 焦點陷阱正常運作（Tab 循環）
- ✅ Escape 鍵可關閉面板
- ✅ 關閉後焦點返回觸發按鈕
- ✅ 所有設定項目都有清晰標籤
- ✅ 設定變更有即時反饋

---

### Test 7: 表格與資料網格

**目標**: 驗證表格有正確的結構和標題

#### 測試頁面
- 歷史分析 (`/history`)
- 成本分析 (`/costs`)
- 代理治理 (`/governance`)

#### VoiceOver 測試步驟

1. **導航到表格**: `VO + Cmd + T`
2. **開啟 Rotor**: `VO + U` → "Tables"
3. **驗證表格結構**:
   ```
   預期聽到:
   - "Table with X rows and Y columns"
   - 表格標題 (caption)
   - 欄位標題 (column headers)
   ```

4. **導航表格內容**:
   - `VO + →`: 移到下一個儲存格
   - `VO + ←`: 移到上一個儲存格
   - `VO + ↓`: 移到下一列
   - `VO + ↑`: 移到上一列

#### NVDA 測試步驟

1. **進入表格**: NVDA 會自動偵測表格
2. **表格導航模式**:
   - `Ctrl + Alt + 方向鍵`: 在儲存格間移動
   - `Ctrl + Alt + Home`: 移到表格開頭
   - `Ctrl + Alt + End`: 移到表格結尾

#### 通過標準

- ✅ 表格使用 `<table>` 元素（不是 div）
- ✅ 有 `<caption>` 或 `aria-label` 描述表格
- ✅ 標題列使用 `<th>` 元素
- ✅ 標題有 `scope="col"` 或 `scope="row"`
- ✅ 複雜表格使用 `headers` 屬性關聯
- ✅ 可排序的欄位有 `aria-sort` 屬性

---

### Test 8: 模態對話框與彈出視窗

**目標**: 驗證模態對話框的焦點管理和鍵盤操作

#### 測試場景
- 確認刪除對話框
- 編輯策略對話框
- Apple Action Sheet
- Apple Modal

#### VoiceOver 測試步驟

1. **開啟對話框**: 觸發對話框（例如點擊 "Delete" 按鈕）
2. **驗證開啟**:
   ```
   預期聽到:
   - 對話框標題
   - "dialog" 或 "alertdialog" 角色
   - 對話框內容
   ```

3. **測試焦點陷阱**:
   - Tab 鍵應只在對話框內循環
   - 無法 Tab 到對話框外的元素

4. **測試關閉**:
   - 按 Escape 鍵應關閉對話框
   - 點擊 "Cancel" 或 "Close" 按鈕
   - 驗證焦點返回到觸發元素

#### 通過標準

- ✅ 對話框有 `role="dialog"` 或 `role="alertdialog"`
- ✅ 對話框有 `aria-labelledby` 指向標題
- ✅ 對話框有 `aria-describedby` 指向描述（如果有）
- ✅ 開啟時焦點移到對話框內
- ✅ 焦點陷阱正常運作
- ✅ Escape 鍵可關閉對話框
- ✅ 關閉後焦點返回觸發元素
- ✅ 背景內容標記為 `aria-hidden="true"`

---

### Test 9: 圖片與圖示

**目標**: 驗證所有圖片都有適當的替代文字

#### VoiceOver 測試步驟

1. **開啟 Rotor**: `VO + U` → "Images"
2. **檢查每個圖片**:
   ```
   預期聽到:
   - 描述性的 alt 文字
   - 或 "decorative image" (裝飾性圖片)
   ```

#### 測試案例

| 圖片類型 | 預期 alt 文字 | 位置 |
|---------|--------------|------|
| Logo | "Morning AI" | Sidebar |
| 使用者頭像 | 使用者名稱 | Sidebar |
| 圖表 | 圖表描述 | Dashboard |
| 裝飾性圖示 | `alt=""` 或 `aria-hidden="true"` | 各處 |

#### 通過標準

- ✅ 所有有意義的圖片都有 `alt` 文字
- ✅ 裝飾性圖片有 `alt=""` 或 `aria-hidden="true"`
- ✅ 複雜圖片（圖表）有詳細描述
- ✅ SVG 圖示有 `aria-label` 或 `<title>` 元素
- ✅ 圖示按鈕不依賴圖示傳達功能

---

### Test 10: 鍵盤快捷鍵

**目標**: 驗證鍵盤快捷鍵可被螢幕閱讀器使用者發現和使用

#### 測試快捷鍵

| 快捷鍵 | 功能 | 測試方法 |
|-------|------|---------|
| `Cmd/Ctrl + K` | 開啟全域搜尋 | 按下快捷鍵，驗證搜尋框開啟 |
| `Cmd/Ctrl + /` | 顯示快捷鍵說明 | 按下快捷鍵，驗證說明顯示 |
| `Escape` | 關閉對話框/面板 | 開啟任何對話框，按 Escape |

#### VoiceOver 測試步驟

1. **尋找快捷鍵說明**:
   - 檢查頁面是否有快捷鍵說明連結
   - 或按 `Cmd + /` 顯示說明

2. **測試每個快捷鍵**:
   - 確認快捷鍵不與螢幕閱讀器快捷鍵衝突
   - 驗證功能正常運作

#### 通過標準

- ✅ 有快捷鍵說明頁面或對話框
- ✅ 快捷鍵不與螢幕閱讀器快捷鍵衝突
- ✅ 快捷鍵可在螢幕閱讀器啟用時使用
- ✅ 快捷鍵有視覺提示（例如工具提示）

---

## 常見問題與解決方案

### 問題 1: VoiceOver 沒有朗讀動態內容

**可能原因**:
- 缺少 `aria-live` 屬性
- `aria-live` 區域在內容更新後才添加

**解決方案**:
```jsx
// ✅ 正確: 先建立 live region，再更新內容
<div aria-live="polite" aria-atomic="true">
  {message}
</div>

// ❌ 錯誤: 動態添加 live region
{showMessage && (
  <div aria-live="polite">{message}</div>
)}
```

### 問題 2: NVDA 朗讀了不必要的內容

**可能原因**:
- 裝飾性元素沒有隱藏
- 重複的標籤

**解決方案**:
```jsx
// 隱藏裝飾性元素
<div aria-hidden="true">
  <Icon />
</div>

// 避免重複標籤
<button aria-label="Close">
  <X aria-hidden="true" />
</button>
```

### 問題 3: 焦點陷阱不工作

**可能原因**:
- 沒有正確處理 Tab 和 Shift+Tab
- 可聚焦元素選擇器不完整

**解決方案**:
```javascript
const focusableElements = dialog.querySelectorAll(
  'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
)
```

---

## 測試報告模板

### 測試資訊

- **測試日期**: YYYY-MM-DD
- **測試人員**: [姓名]
- **螢幕閱讀器**: VoiceOver / NVDA / JAWS
- **版本**: [版本號]
- **瀏覽器**: [瀏覽器名稱和版本]
- **作業系統**: [OS 和版本]

### 測試結果

| 測試項目 | 通過 | 失敗 | 備註 |
|---------|------|------|------|
| Test 1: 頁面結構與地標 | ✅ | ❌ | |
| Test 2: 標題層級結構 | ✅ | ❌ | |
| Test 3: 表單與輸入欄位 | ✅ | ❌ | |
| Test 4: 按鈕與互動元素 | ✅ | ❌ | |
| Test 5: 動態內容與即時區域 | ✅ | ❌ | |
| Test 6: 無障礙設定面板 | ✅ | ❌ | |
| Test 7: 表格與資料網格 | ✅ | ❌ | |
| Test 8: 模態對話框 | ✅ | ❌ | |
| Test 9: 圖片與圖示 | ✅ | ❌ | |
| Test 10: 鍵盤快捷鍵 | ✅ | ❌ | |

### 發現的問題

#### 問題 1: [問題標題]
- **嚴重程度**: Critical / High / Medium / Low
- **位置**: [頁面/元件]
- **描述**: [詳細描述]
- **重現步驟**:
  1. [步驟 1]
  2. [步驟 2]
- **預期行為**: [應該如何]
- **實際行為**: [實際如何]
- **建議修復**: [修復建議]

### 總結

- **通過率**: X/10 (XX%)
- **關鍵發現**: [主要發現]
- **建議**: [改進建議]

---

## 參考資源

### WCAG 2.1 相關準則

- **1.1.1 Non-text Content** (Level A): 所有非文字內容都有替代文字
- **1.3.1 Info and Relationships** (Level A): 資訊、結構和關係可程式化確定
- **2.1.1 Keyboard** (Level A): 所有功能可透過鍵盤操作
- **2.4.3 Focus Order** (Level A): 焦點順序有意義
- **2.4.6 Headings and Labels** (Level AA): 標題和標籤描述主題或目的
- **3.2.4 Consistent Identification** (Level AA): 相同功能的元件一致識別
- **4.1.2 Name, Role, Value** (Level A): 所有 UI 元件的名稱、角色和值可程式化確定
- **4.1.3 Status Messages** (Level AA): 狀態訊息可程式化確定

### 工具與資源

- **VoiceOver 使用指南**: https://support.apple.com/guide/voiceover/welcome/mac
- **NVDA 使用指南**: https://www.nvaccess.org/files/nvda/documentation/userGuide.html
- **JAWS 使用指南**: https://www.freedomscientific.com/training/jaws/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **WebAIM Screen Reader Testing**: https://webaim.org/articles/screenreader_testing/

---

**版本**: 1.0  
**最後更新**: 2025-10-23  
**維護者**: MorningAI UX Team
