# Manual Testing Guide: Keyboard Navigation

## 目的

本指南提供完整的鍵盤導航手動測試流程，確保 MorningAI Dashboard 完全可透過鍵盤操作，符合 WCAG 2.1 Level AAA 標準。

## 測試環境設置

### 瀏覽器要求

- **Chrome**: 版本 120+
- **Firefox**: 版本 120+
- **Safari**: 版本 17+
- **Edge**: 版本 120+

### 測試前準備

1. **關閉滑鼠**: 在測試期間完全不使用滑鼠
2. **清除快取**: 確保測試最新版本
3. **全螢幕模式**: 按 `F11` (Windows/Linux) 或 `Cmd + Ctrl + F` (macOS)
4. **啟用焦點指示器**: 確保瀏覽器顯示焦點輪廓

### 鍵盤快捷鍵參考

#### 基本導航

| 按鍵 | 功能 |
|------|------|
| `Tab` | 移到下一個可聚焦元素 |
| `Shift + Tab` | 移到上一個可聚焦元素 |
| `Enter` | 啟動按鈕或連結 |
| `Space` | 啟動按鈕、切換 checkbox |
| `Escape` | 關閉對話框、選單或面板 |
| `Arrow Keys` | 在選單、radio group、tabs 中導航 |

#### 應用程式快捷鍵

| 按鍵 | 功能 |
|------|------|
| `Cmd/Ctrl + K` | 開啟全域搜尋 (Spotlight) |
| `Cmd/Ctrl + /` | 顯示快捷鍵說明 |
| `Cmd/Ctrl + ,` | 開啟設定 |

---

## 核心測試流程

### Test 1: 基本頁面導航

**目標**: 驗證使用者可以用 Tab 鍵訪問所有互動元素

#### 測試步驟

1. **載入首頁**: 開啟 `http://localhost:5173`
2. **按 Tab 鍵**: 從頁面頂部開始
3. **記錄焦點順序**: 記下每個獲得焦點的元素

#### 預期焦點順序（登入前）

```
1. Skip to content 連結
2. Logo 連結
3. "Login" 按鈕
4. "Sign Up" 按鈕
5. SSO 登入按鈕（如果有）
```

#### 預期焦點順序（登入後 - Dashboard）

```
1. Skip to content 連結
2. Sidebar 收合按鈕
3. Dashboard 導航連結
4. Strategies 導航連結
5. Approvals 導航連結
6. History 導航連結
7. Costs 導航連結
8. Governance 導航連結
9. Settings 導航連結
10. Dark Mode 切換按鈕
11. Language 切換按鈕
12. Accessibility 設定按鈕
13. Logout 按鈕
14. 主內容區域的第一個互動元素
```

#### 通過標準

- ✅ 所有互動元素都可透過 Tab 鍵訪問
- ✅ 焦點順序符合視覺順序（從上到下、從左到右）
- ✅ 焦點指示器清晰可見
- ✅ 沒有焦點陷阱（除了模態對話框）
- ✅ 沒有跳過重要的互動元素
- ✅ 隱藏或禁用的元素不接收焦點

---

### Test 2: Skip to Content 連結

**目標**: 驗證鍵盤使用者可以快速跳過導航區域

#### 測試步驟

1. **載入任何頁面**: 登入後的任何頁面
2. **按 Tab 鍵一次**: 焦點應移到 "Skip to content" 連結
3. **檢查可見性**: 連結應該可見（不是隱藏的）
4. **按 Enter**: 焦點應跳到主內容區域
5. **驗證焦點位置**: 確認焦點在主內容的第一個元素

#### 通過標準

- ✅ "Skip to content" 連結是第一個可聚焦元素
- ✅ 連結在獲得焦點時可見
- ✅ 按 Enter 後焦點移到主內容
- ✅ 主內容有 `id="main-content"` 或類似標識
- ✅ 跳過後可以繼續用 Tab 鍵導航

---

### Test 3: 表單導航與操作

**目標**: 驗證所有表單控制項都可透過鍵盤操作

#### 測試頁面
- 登入頁面 (`/login`)
- 設定頁面 (`/settings`)
- 策略管理頁面 (`/strategies`)

#### 測試步驟 - 登入表單

1. **導航到 Email 欄位**: 按 Tab 鍵
2. **輸入 Email**: 直接輸入文字
3. **移到 Password 欄位**: 按 Tab 鍵
4. **輸入密碼**: 直接輸入文字
5. **移到 "Remember me" checkbox**: 按 Tab 鍵
6. **切換 checkbox**: 按 Space 鍵
7. **移到 "Login" 按鈕**: 按 Tab 鍵
8. **提交表單**: 按 Enter 或 Space 鍵

#### 測試步驟 - 複雜表單（設定頁面）

1. **文字輸入欄位**:
   - Tab 到欄位
   - 輸入文字
   - 驗證可以編輯和刪除

2. **Checkbox**:
   - Tab 到 checkbox
   - 按 Space 切換
   - 驗證視覺狀態改變

3. **Radio buttons**:
   - Tab 到 radio group
   - 使用 Arrow keys 在選項間移動
   - 驗證只有一個選項被選中

4. **Select dropdown**:
   - Tab 到 select
   - 按 Space 或 Enter 開啟
   - 使用 Arrow keys 選擇選項
   - 按 Enter 確認選擇

5. **自訂元件 (AppleInput, ApplePicker)**:
   - 驗證行為與原生控制項一致
   - 測試所有互動方式

#### 通過標準

- ✅ 所有表單控制項都可透過 Tab 鍵訪問
- ✅ 文字欄位可以輸入、編輯、刪除
- ✅ Checkbox 可以用 Space 切換
- ✅ Radio buttons 可以用 Arrow keys 導航
- ✅ Select dropdown 可以用鍵盤開啟和選擇
- ✅ 表單可以用 Enter 提交
- ✅ 錯誤訊息在提交後獲得焦點或被通知
- ✅ 必填欄位有清晰的視覺和程式化指示

---

### Test 4: 按鈕與連結

**目標**: 驗證所有按鈕和連結都可透過鍵盤啟動

#### 測試案例

| 元素類型 | 啟動方式 | 測試位置 |
|---------|---------|---------|
| 標準按鈕 | Enter 或 Space | 所有頁面 |
| 連結 | Enter | Sidebar, 內容區域 |
| 圖示按鈕 | Enter 或 Space | Sidebar, Toolbar |
| 切換按鈕 | Enter 或 Space | Dark Mode, Language |
| 分割按鈕 | Enter (主動作), Arrow keys (選單) | 如果有 |

#### 測試步驟

1. **Tab 到按鈕**: 使用 Tab 鍵
2. **檢查焦點指示器**: 確認按鈕有清晰的焦點輪廓
3. **啟動按鈕**: 按 Enter 或 Space
4. **驗證動作**: 確認按鈕功能正常執行
5. **檢查焦點管理**: 驗證焦點移到適當位置

#### AppleButton 特定測試

```jsx
// 測試所有 AppleButton 變體
<AppleButton variant="primary">Primary</AppleButton>
<AppleButton variant="secondary">Secondary</AppleButton>
<AppleButton variant="ghost">Ghost</AppleButton>
<AppleButton variant="destructive">Destructive</AppleButton>
```

#### 通過標準

- ✅ 所有按鈕都可透過 Tab 鍵訪問
- ✅ 按鈕可以用 Enter 和 Space 啟動
- ✅ 連結只能用 Enter 啟動（不是 Space）
- ✅ 禁用的按鈕不接收焦點
- ✅ 圖示按鈕有清晰的焦點指示器
- ✅ 按鈕啟動後焦點管理正確

---

### Test 5: 模態對話框與焦點陷阱

**目標**: 驗證模態對話框的焦點管理符合最佳實踐

#### 測試場景
- 確認刪除對話框
- 編輯策略對話框
- Apple Modal
- Apple Action Sheet
- 無障礙設定面板

#### 測試步驟 - 開啟對話框

1. **觸發對話框**: Tab 到觸發按鈕，按 Enter
2. **驗證焦點移動**: 焦點應自動移到對話框內
3. **檢查焦點位置**: 通常是第一個可聚焦元素或關閉按鈕

#### 測試步驟 - 焦點陷阱

1. **Tab 到最後一個元素**: 在對話框內按 Tab 鍵
2. **再按 Tab**: 焦點應回到對話框內的第一個元素
3. **Shift + Tab 測試**: 從第一個元素按 Shift + Tab
4. **驗證循環**: 焦點應移到最後一個元素

#### 測試步驟 - 關閉對話框

1. **按 Escape 鍵**: 對話框應關閉
2. **驗證焦點返回**: 焦點應返回到觸發按鈕
3. **測試其他關閉方式**:
   - Tab 到 "Close" 按鈕，按 Enter
   - Tab 到 "Cancel" 按鈕，按 Enter
   - 驗證所有方式都正確返回焦點

#### 無障礙設定面板特定測試

```
測試流程:
1. Tab 到 Sidebar 的 "Accessibility" 按鈕
2. 按 Enter 開啟面板
3. 驗證焦點移到面板內第一個控制項
4. Tab 遍歷所有設定項目:
   - Reduced Motion checkbox
   - High Contrast checkbox
   - Font Size radio group
   - Screen Reader checkbox
   - Keyboard Shortcuts checkbox
   - Focus Indicators radio group
   - Reset button
   - Done button
5. 從 Done 按鈕按 Tab，焦點應回到 Reduced Motion
6. 按 Escape 關閉面板
7. 驗證焦點返回到 "Accessibility" 按鈕
```

#### 通過標準

- ✅ 對話框開啟時焦點自動移入
- ✅ 焦點陷阱正常運作（Tab 循環）
- ✅ Shift + Tab 反向循環正常
- ✅ Escape 鍵可關閉對話框
- ✅ 關閉後焦點返回到觸發元素
- ✅ 背景內容無法透過 Tab 訪問
- ✅ 對話框內所有控制項都可訪問

---

### Test 6: 下拉選單與導航

**目標**: 驗證下拉選單和導航元件的鍵盤操作

#### 測試元件
- Language Switcher
- User Profile Menu (如果有)
- Apple Action Sheet
- Apple Picker

#### 測試步驟 - 下拉選單

1. **開啟選單**:
   - Tab 到觸發按鈕
   - 按 Enter 或 Space 或 Arrow Down

2. **導航選項**:
   - 使用 Arrow Up/Down 在選項間移動
   - 驗證焦點指示器清晰可見

3. **選擇選項**:
   - 按 Enter 選擇當前選項
   - 驗證選單關閉
   - 驗證選擇生效

4. **關閉選單**:
   - 按 Escape 關閉（不選擇）
   - 驗證焦點返回觸發按鈕

#### Language Switcher 特定測試

```
測試流程:
1. Tab 到 Language Switcher 按鈕
2. 按 Enter 開啟選單
3. 使用 Arrow Down 移到 "English"
4. 按 Enter 選擇
5. 驗證語言切換成功
6. 驗證焦點返回按鈕
```

#### Apple Picker 特定測試

```
測試流程:
1. Tab 到 Picker 觸發按鈕
2. 按 Enter 開啟 Picker
3. 使用 Arrow Up/Down 滾動選項
4. 按 Enter 確認選擇
5. 驗證 Picker 關閉
6. 驗證選擇值更新
```

#### 通過標準

- ✅ 選單可以用 Enter, Space, 或 Arrow keys 開啟
- ✅ Arrow keys 可以在選項間導航
- ✅ Enter 可以選擇當前選項
- ✅ Escape 可以關閉選單（不選擇）
- ✅ 關閉後焦點返回觸發按鈕
- ✅ 選中的選項有視覺指示
- ✅ 選單開啟時焦點在第一個或選中的選項

---

### Test 7: Tabs 與 SegmentedControl

**目標**: 驗證 tabs 導航符合 ARIA 最佳實踐

#### 測試元件
- Apple SegmentedControl
- 任何使用 tabs 的頁面

#### 測試步驟

1. **Tab 到 tab list**: 焦點應移到當前選中的 tab
2. **使用 Arrow keys 導航**:
   - Arrow Right: 移到下一個 tab
   - Arrow Left: 移到上一個 tab
   - Home: 移到第一個 tab
   - End: 移到最後一個 tab

3. **自動啟動 vs 手動啟動**:
   - **自動**: Arrow key 移動時自動切換 tab panel
   - **手動**: 需要按 Enter 或 Space 啟動

4. **Tab 到 panel**: 從 tab list 按 Tab 應移到當前 panel 內容

#### Apple SegmentedControl 特定測試

```
測試流程:
1. Tab 到 SegmentedControl
2. 驗證焦點在當前選中的 segment
3. 按 Arrow Right 移到下一個 segment
4. 驗證 segment 自動啟動（如果是自動模式）
5. 按 Home 移到第一個 segment
6. 按 End 移到最後一個 segment
7. Tab 離開 SegmentedControl
```

#### 通過標準

- ✅ Tab 鍵移到當前選中的 tab
- ✅ Arrow keys 可以在 tabs 間導航
- ✅ Home/End 鍵移到第一個/最後一個 tab
- ✅ Tab 鍵從 tab list 移到 panel 內容
- ✅ 只有選中的 tab 在 tab 順序中
- ✅ Tab panel 有 `role="tabpanel"`
- ✅ Tab 有 `aria-selected` 屬性

---

### Test 8: 表格導航

**目標**: 驗證表格可以透過鍵盤有效導航

#### 測試頁面
- 歷史分析 (`/history`)
- 成本分析 (`/costs`)
- 代理治理 (`/governance`)

#### 測試步驟 - 簡單表格

1. **Tab 到表格**: 焦點移到表格內第一個互動元素
2. **Tab 遍歷儲存格**: 如果儲存格有互動元素（連結、按鈕）
3. **驗證焦點順序**: 應該是從左到右、從上到下

#### 測試步驟 - 資料網格 (Data Grid)

如果表格實作為 `role="grid"`:

1. **Tab 到網格**: 焦點移到第一個儲存格
2. **使用 Arrow keys 導航**:
   - Arrow Right: 下一個儲存格
   - Arrow Left: 上一個儲存格
   - Arrow Down: 下一列
   - Arrow Up: 上一列
   - Home: 列的第一個儲存格
   - End: 列的最後一個儲存格
   - Ctrl + Home: 第一列第一個儲存格
   - Ctrl + End: 最後一列最後一個儲存格

3. **編輯儲存格** (如果可編輯):
   - 按 Enter 進入編輯模式
   - 編輯內容
   - 按 Enter 或 Tab 確認
   - 按 Escape 取消

#### 可排序表格測試

1. **Tab 到欄位標題**: 如果標題是按鈕或連結
2. **按 Enter 或 Space**: 觸發排序
3. **驗證排序**: 確認表格重新排序
4. **檢查 aria-sort**: 標題應有 `aria-sort="ascending"` 或 `"descending"`

#### 通過標準

- ✅ 表格內的互動元素都可透過 Tab 訪問
- ✅ 如果是 grid，Arrow keys 可以導航儲存格
- ✅ 可排序的欄位標題可以用鍵盤啟動
- ✅ 排序狀態有視覺和程式化指示
- ✅ 表格有適當的 ARIA 屬性
- ✅ 複雜表格有鍵盤導航說明

---

### Test 9: 拖放操作

**目標**: 驗證拖放功能有鍵盤替代方案

#### 測試場景
- 重新排序列表項目
- 移動卡片或元件
- 調整大小

#### 測試步驟

1. **Tab 到可拖放元素**: 元素應該可聚焦
2. **啟動拖放模式**:
   - 按 Space 或 Enter 進入拖放模式
   - 應該有視覺或聽覺反饋

3. **移動元素**:
   - 使用 Arrow keys 移動
   - 或使用 Tab 選擇目標位置

4. **放下元素**:
   - 按 Space 或 Enter 確認位置
   - 按 Escape 取消

#### 通過標準

- ✅ 所有拖放功能都有鍵盤替代方案
- ✅ 拖放模式有清晰的視覺指示
- ✅ 可以用 Arrow keys 或 Tab 移動
- ✅ 可以用 Space/Enter 確認，Escape 取消
- ✅ 操作完成後有反饋（視覺或聽覺）
- ✅ 有說明文字告知如何使用鍵盤操作

---

### Test 10: 全域快捷鍵

**目標**: 驗證全域快捷鍵在所有頁面都可用

#### 測試快捷鍵

| 快捷鍵 | 功能 | 預期行為 |
|-------|------|---------|
| `Cmd/Ctrl + K` | 開啟 Spotlight 搜尋 | 搜尋框開啟並獲得焦點 |
| `Cmd/Ctrl + /` | 顯示快捷鍵說明 | 說明對話框開啟 |
| `Cmd/Ctrl + ,` | 開啟設定 | 導航到設定頁面 |
| `Escape` | 關閉對話框/面板 | 當前對話框關閉 |

#### 測試步驟

1. **在不同頁面測試**: Dashboard, Strategies, Settings 等
2. **按下快捷鍵**: 例如 `Cmd + K`
3. **驗證功能**: 確認 Spotlight 開啟
4. **檢查焦點**: 焦點應在搜尋輸入框
5. **關閉**: 按 Escape
6. **驗證焦點返回**: 焦點應返回到之前的位置

#### Apple Spotlight 特定測試

```
測試流程:
1. 在 Dashboard 頁面
2. 按 Cmd/Ctrl + K
3. 驗證 Spotlight 開啟
4. 驗證焦點在搜尋輸入框
5. 輸入搜尋詞 "strategy"
6. 使用 Arrow Down 導航結果
7. 按 Enter 選擇結果
8. 驗證導航到正確頁面
```

#### 通過標準

- ✅ 快捷鍵在所有頁面都可用
- ✅ 快捷鍵不與瀏覽器快捷鍵衝突
- ✅ 快捷鍵啟動後焦點管理正確
- ✅ 有快捷鍵說明頁面或對話框
- ✅ 快捷鍵有視覺提示（工具提示或說明）

---

### Test 11: 無障礙設定面板完整測試

**目標**: 全面測試無障礙設定面板的鍵盤操作

#### 測試步驟

1. **開啟面板**:
   ```
   - Tab 到 Sidebar 的 "Accessibility" 按鈕
   - 按 Enter
   - 驗證面板開啟
   - 驗證焦點在面板內第一個控制項
   ```

2. **測試每個設定項目**:

   **Reduced Motion (Checkbox)**:
   ```
   - Tab 到 checkbox
   - 按 Space 切換
   - 驗證視覺狀態改變
   - 驗證頁面動畫減少（如果啟用）
   ```

   **High Contrast (Checkbox)**:
   ```
   - Tab 到 checkbox
   - 按 Space 切換
   - 驗證對比度增加（如果啟用）
   ```

   **Font Size (Radio Group)**:
   ```
   - Tab 到 radio group
   - 使用 Arrow Right/Left 在選項間移動
   - 驗證只有一個選項被選中
   - 驗證字體大小即時改變
   ```

   **Screen Reader Announcements (Checkbox)**:
   ```
   - Tab 到 checkbox
   - 按 Space 切換
   - 驗證狀態改變
   ```

   **Keyboard Shortcuts (Checkbox)**:
   ```
   - Tab 到 checkbox
   - 按 Space 切換
   - 驗證狀態改變
   ```

   **Focus Indicators (Radio Group)**:
   ```
   - Tab 到 radio group
   - 使用 Arrow keys 選擇 "Default" 或 "Enhanced"
   - 驗證焦點指示器樣式改變
   ```

3. **測試按鈕**:

   **Reset Button**:
   ```
   - Tab 到 "Reset to Defaults" 按鈕
   - 按 Enter
   - 驗證所有設定恢復預設值
   ```

   **Done Button**:
   ```
   - Tab 到 "Done" 按鈕
   - 按 Enter
   - 驗證面板關閉
   - 驗證焦點返回到觸發按鈕
   ```

4. **測試焦點陷阱**:
   ```
   - 從 Done 按鈕按 Tab
   - 驗證焦點回到 Reduced Motion checkbox
   - 從 Reduced Motion 按 Shift + Tab
   - 驗證焦點移到 Done 按鈕
   ```

5. **測試 Escape 鍵**:
   ```
   - 在面板內任何位置按 Escape
   - 驗證面板關閉
   - 驗證焦點返回到觸發按鈕
   ```

6. **測試持久化**:
   ```
   - 更改多個設定
   - 關閉面板
   - 重新整理頁面
   - 重新開啟面板
   - 驗證設定被保存
   ```

#### 通過標準

- ✅ 面板可以用鍵盤開啟和關閉
- ✅ 所有設定項目都可透過 Tab 訪問
- ✅ Checkbox 可以用 Space 切換
- ✅ Radio group 可以用 Arrow keys 導航
- ✅ 設定變更即時生效
- ✅ 焦點陷阱正常運作
- ✅ Escape 鍵可關閉面板
- ✅ 關閉後焦點返回觸發按鈕
- ✅ 設定被持久化到 localStorage
- ✅ Reset 按鈕恢復所有預設值

---

### Test 12: 焦點指示器可見性

**目標**: 驗證所有互動元素都有清晰的焦點指示器

#### 測試步驟

1. **遍歷所有頁面**: Dashboard, Strategies, Settings 等
2. **Tab 遍歷所有元素**: 記錄焦點指示器
3. **檢查對比度**: 使用瀏覽器開發者工具或對比度檢查器
4. **測試不同主題**: Light mode 和 Dark mode

#### 焦點指示器要求

| 元素類型 | 最小對比度 | 樣式要求 |
|---------|-----------|---------|
| 按鈕 | 3:1 | 2px 輪廓或陰影 |
| 連結 | 3:1 | 下劃線或輪廓 |
| 輸入欄位 | 3:1 | 邊框或輪廓 |
| Checkbox/Radio | 3:1 | 輪廓 |

#### 測試不同焦點指示器模式

```
測試流程:
1. 開啟無障礙設定面板
2. 選擇 "Default" 焦點指示器
3. Tab 遍歷頁面，檢查焦點指示器
4. 選擇 "Enhanced" 焦點指示器
5. Tab 遍歷頁面，檢查增強的焦點指示器
6. 驗證增強模式更明顯（更粗、更高對比度）
```

#### 通過標準

- ✅ 所有互動元素都有焦點指示器
- ✅ 焦點指示器對比度至少 3:1
- ✅ 焦點指示器在 light 和 dark mode 都清晰
- ✅ 焦點指示器不被其他元素遮擋
- ✅ 自訂焦點指示器符合或超越瀏覽器預設
- ✅ Enhanced 模式提供更高可見度

---

## 常見問題與解決方案

### 問題 1: 焦點順序不合邏輯

**症狀**: Tab 鍵焦點跳來跳去，不符合視覺順序

**可能原因**:
- 使用 `tabindex` 正值（`tabindex="1"`, `tabindex="2"` 等）
- CSS 改變視覺順序但 DOM 順序不同

**解決方案**:
```jsx
// ❌ 錯誤: 使用正值 tabindex
<button tabindex="1">First</button>
<button tabindex="2">Second</button>

// ✅ 正確: 使用自然 DOM 順序
<button>First</button>
<button>Second</button>

// ✅ 正確: 只在需要時使用 tabindex="0" 或 "-1"
<div tabindex="0" role="button">Custom Button</div>
<div tabindex="-1">Not in tab order</div>
```

### 問題 2: 焦點陷阱不工作

**症狀**: 在模態對話框內按 Tab 可以移到背景元素

**可能原因**:
- 沒有正確實作焦點陷阱邏輯
- 背景元素沒有設置 `inert` 或 `aria-hidden`

**解決方案**:
```jsx
// 使用 focus-trap-react 或自訂實作
import FocusTrap from 'focus-trap-react'

<FocusTrap>
  <div role="dialog">
    {/* 對話框內容 */}
  </div>
</FocusTrap>

// 背景元素
<div aria-hidden="true" inert>
  {/* 背景內容 */}
</div>
```

### 問題 3: 自訂元件不接收焦點

**症狀**: Tab 鍵跳過自訂元件

**可能原因**:
- 使用 `<div>` 或 `<span>` 而非語義化元素
- 缺少 `tabindex="0"`

**解決方案**:
```jsx
// ❌ 錯誤: div 預設不可聚焦
<div onClick={handleClick}>Click me</div>

// ✅ 正確: 使用 button
<button onClick={handleClick}>Click me</button>

// ✅ 正確: 如果必須使用 div，添加 tabindex 和 role
<div 
  tabindex="0" 
  role="button" 
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick()
    }
  }}
>
  Click me
</div>
```

### 問題 4: Enter 和 Space 行為不一致

**症狀**: 按鈕只響應 Enter 或只響應 Space

**可能原因**:
- 只處理一種按鍵事件
- 使用 `onClick` 但沒有處理鍵盤事件

**解決方案**:
```jsx
// ✅ 正確: 處理 Enter 和 Space
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault() // 防止 Space 滾動頁面
      handleClick()
    }
  }}
>
  Custom Button
</div>

// ✅ 更好: 使用原生 button
<button onClick={handleClick}>
  Native Button
</button>
```

---

## 測試報告模板

### 測試資訊

- **測試日期**: YYYY-MM-DD
- **測試人員**: [姓名]
- **瀏覽器**: [瀏覽器名稱和版本]
- **作業系統**: [OS 和版本]
- **測試模式**: 僅鍵盤（無滑鼠）

### 測試結果

| 測試項目 | 通過 | 失敗 | 備註 |
|---------|------|------|------|
| Test 1: 基本頁面導航 | ✅ | ❌ | |
| Test 2: Skip to Content | ✅ | ❌ | |
| Test 3: 表單導航與操作 | ✅ | ❌ | |
| Test 4: 按鈕與連結 | ✅ | ❌ | |
| Test 5: 模態對話框與焦點陷阱 | ✅ | ❌ | |
| Test 6: 下拉選單與導航 | ✅ | ❌ | |
| Test 7: Tabs 與 SegmentedControl | ✅ | ❌ | |
| Test 8: 表格導航 | ✅ | ❌ | |
| Test 9: 拖放操作 | ✅ | ❌ | N/A |
| Test 10: 全域快捷鍵 | ✅ | ❌ | |
| Test 11: 無障礙設定面板 | ✅ | ❌ | |
| Test 12: 焦點指示器可見性 | ✅ | ❌ | |

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

### 焦點順序記錄

#### Dashboard 頁面

```
1. Skip to content
2. Sidebar toggle
3. Dashboard link (active)
4. Strategies link
5. ...
```

### 總結

- **通過率**: X/12 (XX%)
- **關鍵發現**: [主要發現]
- **建議**: [改進建議]

---

## 參考資源

### WCAG 2.1 相關準則

- **2.1.1 Keyboard** (Level A): 所有功能可透過鍵盤操作
- **2.1.2 No Keyboard Trap** (Level A): 焦點不會被困住
- **2.4.3 Focus Order** (Level A): 焦點順序有意義
- **2.4.7 Focus Visible** (Level AA): 焦點指示器可見
- **3.2.1 On Focus** (Level A): 獲得焦點時不觸發意外變化

### 工具與資源

- **Keyboard Navigation Tester**: https://webaim.org/articles/keyboard/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **Focus Management**: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- **Tab Order**: https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html

---

**版本**: 1.0  
**最後更新**: 2025-10-23  
**維護者**: MorningAI UX Team
