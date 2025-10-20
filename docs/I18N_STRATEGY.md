# i18n 翻譯策略與工作流程

## 概述

本文檔定義 MorningAI 專案的國際化 (i18n) 翻譯策略，確保設計團隊與工程團隊的分工清晰，避免重複工作與合併衝突。

---

## 核心原則

### 1. 分工規則

**設計團隊負責**:
- 所有翻譯內容的撰寫與審校
- 提交獨立的「設計 PR: i18n 翻譯更新」
- 維護翻譯品質與語氣一致性

**工程團隊負責**:
- 在程式碼中使用翻譯 keys (如 `t('dashboard.hero.title')`)
- 整合 i18next 框架與路由
- **不得**在工程 PR 中修改 `en-US.json` 或 `zh-TW.json`

### 2. 單一來源原則

**推薦方案**: 單一 i18n PR (由設計團隊提交)

**理由**:
- 避免多個 PRs 同時修改翻譯檔案造成衝突
- 集中審查翻譯品質與語氣
- 符合 `CONTRIBUTING.md` § 分工規則 (i18n 屬於「文案」範疇)

---

## 工作流程

### Phase 1: 設計團隊準備翻譯

**時間**: Week 3-4 (設計系統建立階段)

**步驟**:
1. 設計團隊根據 `docs/UX/Design System/Copywriting.md` 撰寫所有翻譯內容
2. 建立分支: `design/i18n-translations`
3. 修改檔案:
   - `handoff/20250928/40_App/frontend-dashboard/src/locales/en-US.json`
   - `handoff/20250928/40_App/frontend-dashboard/src/locales/zh-TW.json`
4. 提交 PR: `設計 PR: i18n 翻譯更新 (Week 1-8)`

**PR 內容範例**:
```json
// en-US.json
{
  "dashboard": {
    "title": "Dashboard",
    "widgets": {
      "cpu": "CPU Usage",
      "memory": "Memory Usage",
      "cost": "Today's Cost"
    }
  },
  "empty_states": {
    "no_data": "No data available",
    "cta": "Get Started"
  }
}
```

### Phase 2: 工程團隊使用翻譯

**時間**: Week 1-8 (各功能實作階段)

**步驟**:
1. 工程團隊在程式碼中使用翻譯 keys:
   ```jsx
   import { useTranslation } from 'react-i18next';
   
   function Dashboard() {
     const { t } = useTranslation();
     return <h1>{t('dashboard.title')}</h1>;
   }
   ```
2. **不修改** `en-US.json` 或 `zh-TW.json`
3. 如需新增翻譯 key，在 PR 描述中註明，由設計團隊補充

### Phase 3: 翻譯審校與更新

**時間**: 持續進行

**步驟**:
1. 設計團隊定期審校翻譯品質
2. 發現問題時建立新的「設計 PR: i18n 翻譯修正」
3. 遵循相同的 PR 流程

---

## 翻譯檔案結構

### 目錄位置
```
handoff/20250928/40_App/frontend-dashboard/src/locales/
├── en-US.json  # 英文翻譯 (主要語言)
└── zh-TW.json  # 繁體中文翻譯
```

### 命名規範

**Key 命名規則**:
- 使用小寫與底線: `dashboard.widgets.cpu_usage`
- 按功能模組分組: `dashboard.*`, `approvals.*`, `settings.*`
- 避免過長的巢狀: 最多 3 層 (`module.section.key`)

**範例**:
```json
{
  "dashboard": {
    "title": "Dashboard",
    "widgets": {
      "cpu_usage": "CPU Usage",
      "memory_usage": "Memory Usage"
    }
  },
  "approvals": {
    "pending": "Pending Approvals",
    "approved": "Approved"
  }
}
```

---

## 翻譯品質標準

### 語氣指南

參考 `docs/UX/Design System/Copywriting.md`:

**英文 (en-US)**:
- 清晰、簡潔、可行動
- 避免行銷套語與過度修飾
- 使用主動語態

**繁體中文 (zh-TW)**:
- 避免直譯，保持語意精準
- 使用台灣慣用詞彙 (如「儀表板」而非「控制面板」)
- 保持專業但友善的語氣

### 審校流程

1. **初稿**: 設計團隊撰寫
2. **自我審查**: 檢查拼寫、語法、一致性
3. **同儕審查**: 另一位設計師審查
4. **提交 PR**: 通過 CI 檢查後合併

---

## 避免的反模式

### ❌ 反模式 1: 工程 PR 包含翻譯

**錯誤範例** (PR #483-#486):
```diff
// 工程 PR 中修改 en-US.json
+ "landing": {
+   "hero": {
+     "title": "Welcome to MorningAI"
+   }
+ }
```

**正確做法**:
- 工程 PR 只使用 `t('landing.hero.title')`
- 翻譯內容由設計 PR 提供

### ❌ 反模式 2: 多個 PRs 同時修改翻譯檔案

**問題**:
- PR #483, #484, #485, #486 都修改 `en-US.json`
- 造成 350+ 行重複變更
- 合併時產生衝突

**正確做法**:
- 所有翻譯集中在單一設計 PR
- 工程 PRs 不觸碰翻譯檔案

### ❌ 反模式 3: 硬編碼文字

**錯誤範例**:
```jsx
<h1>Dashboard</h1>  // ❌ 硬編碼
```

**正確做法**:
```jsx
<h1>{t('dashboard.title')}</h1>  // ✅ 使用翻譯 key
```

---

## CI/CD 整合

### 設計 PR 檢查

**必須通過**:
- JSON 格式驗證 (valid JSON syntax)
- Key 一致性檢查 (en-US 與 zh-TW 的 keys 必須相同)
- 無重複 keys

**建議檢查** (未來可加入):
- 翻譯完整性 (所有 keys 都有對應翻譯)
- 字數限制 (避免過長的翻譯導致 UI 溢出)

### 工程 PR 檢查

**必須通過**:
- 不得修改 `src/locales/*.json` (除非是設計 PR)
- 所有使用的翻譯 keys 必須存在於翻譯檔案中

---

## 時間表

| 週次 | 任務 | 負責團隊 |
|------|------|---------|
| Week 1-2 | 識別所有需要翻譯的文字 | 設計 + 工程 |
| Week 3 | 撰寫 Week 1-4 所需翻譯 | 設計 |
| Week 3 | 提交「設計 PR: i18n 翻譯更新 (Week 1-4)」 | 設計 |
| Week 4 | 審校與合併翻譯 PR | 設計 |
| Week 5 | 撰寫 Week 5-8 所需翻譯 | 設計 |
| Week 5 | 提交「設計 PR: i18n 翻譯更新 (Week 5-8)」 | 設計 |
| Week 6 | 審校與合併翻譯 PR | 設計 |
| Week 7-8 | 翻譯品質驗證與修正 | 設計 |

---

## 參考資料

- `docs/UX/Design System/Copywriting.md` - 文案與語氣指南
- `CONTRIBUTING.md` § 分工規則 - 設計 PR vs 工程 PR
- `docs/CTO_WEEK1_VALIDATION_REPORT.md` - Week 1 PRs 問題分析
- [i18next 官方文檔](https://www.i18next.com/)

---

## 決策記錄

**日期**: 2025-10-20  
**決策者**: Ryan Chen (Product Owner)  
**決策**: 採用「單一 i18n PR (由設計團隊提交)」策略

**理由**:
1. 符合分工規則 (i18n 屬於文案範疇)
2. 避免重複與衝突 (Week 1 PRs 包含 350+ 行重複翻譯)
3. 集中審查翻譯品質
4. 降低工程團隊負擔

**替代方案**: 每個 feature 一個 i18n PR (被拒絕，因為會增加協調成本)

---

## 聯絡方式

**翻譯相關問題**:
- 設計團隊: 負責翻譯內容與品質
- 工程團隊: 負責 i18next 框架整合

**衝突解決**:
- 參考 `CONTRIBUTING.md` § 分工規則
- 有疑問時諮詢 CTO 或 Product Owner
