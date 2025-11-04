# i18n 工作流程指南

**目標**: 建立標準化的國際化 (i18n) 工作流程  
**優先級**: 🟡 **P1** (Week 3-4 重要任務)  
**預估工時**: 2 天  
**相關 Issue**: #473 (Week 3-4 i18n 工作流程)

---

## 📋 執行摘要

### 目標

建立完整的 i18n 工作流程，包括:
- ✅ Key 命名規範
- ✅ 翻譯審校流程
- ✅ 缺失翻譯檢測
- ✅ 翻譯品質保證

### 當前狀態

根據 `handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/`，我們已經有:
- ✅ `zh-TW.json` (繁體中文)
- ✅ `en.json` (英文)
- ✅ `ja.json` (日文)

但缺少:
- ❌ Key 命名規範
- ❌ 翻譯審校流程
- ❌ 缺失翻譯檢測工具

---

## 🎯 Key 命名規範

### 命名原則

1. **使用點號分隔** (Dot Notation)
   ```json
   {
     "dashboard.title": "儀表板",
     "dashboard.metrics.cpu": "CPU 使用率"
   }
   ```

2. **按功能/頁面分組**
   ```json
   {
     "common.button.save": "儲存",
     "common.button.cancel": "取消",
     "dashboard.title": "儀表板",
     "login.title": "登入"
   }
   ```

3. **使用小寫與底線**
   ```json
   {
     "user_profile.edit_button": "編輯個人資料"
   }
   ```

4. **避免過長的 Key**
   ```json
   // ❌ 不好
   "dashboard_page_metrics_section_cpu_usage_card_title": "CPU 使用率"
   
   // ✅ 好
   "dashboard.metrics.cpu.title": "CPU 使用率"
   ```

### 命名結構

```
<scope>.<feature>.<component>.<element>
```

**範例**:
- `common.button.save` - 通用儲存按鈕
- `dashboard.metrics.cpu.title` - Dashboard 的 CPU 指標標題
- `login.form.email.placeholder` - 登入表單的 Email 佔位符

### 特殊 Key 類型

#### 1. 按鈕 (Buttons)

```json
{
  "common.button.save": "儲存",
  "common.button.cancel": "取消",
  "common.button.delete": "刪除",
  "common.button.edit": "編輯",
  "common.button.submit": "提交",
  "common.button.close": "關閉"
}
```

#### 2. 表單 (Forms)

```json
{
  "login.form.email.label": "電子郵件",
  "login.form.email.placeholder": "請輸入電子郵件",
  "login.form.email.error.required": "電子郵件為必填",
  "login.form.email.error.invalid": "電子郵件格式不正確",
  "login.form.password.label": "密碼",
  "login.form.password.placeholder": "請輸入密碼"
}
```

#### 3. 訊息 (Messages)

```json
{
  "common.message.success.save": "儲存成功",
  "common.message.error.network": "網路錯誤，請稍後再試",
  "common.message.warning.unsaved": "您有未儲存的變更",
  "common.message.info.loading": "載入中..."
}
```

#### 4. 標題與描述 (Titles & Descriptions)

```json
{
  "dashboard.title": "儀表板",
  "dashboard.description": "查看系統性能與 AI 決策",
  "dashboard.metrics.title": "系統指標",
  "dashboard.metrics.description": "實時監控系統性能"
}
```

---

## 📁 檔案結構

### 建議結構

```
src/i18n/
├── locales/
│   ├── zh-TW/
│   │   ├── common.json       # 通用翻譯
│   │   ├── dashboard.json    # Dashboard 翻譯
│   │   ├── login.json        # 登入頁面翻譯
│   │   ├── settings.json     # 設定頁面翻譯
│   │   └── index.js          # 匯出所有翻譯
│   ├── en/
│   │   ├── common.json
│   │   ├── dashboard.json
│   │   ├── login.json
│   │   ├── settings.json
│   │   └── index.js
│   └── ja/
│       ├── common.json
│       ├── dashboard.json
│       ├── login.json
│       ├── settings.json
│       └── index.js
├── config.js                 # i18n 配置
└── index.js                  # i18n 初始化
```

### 範例: common.json

```json
{
  "button": {
    "save": "儲存",
    "cancel": "取消",
    "delete": "刪除",
    "edit": "編輯",
    "submit": "提交",
    "close": "關閉",
    "confirm": "確認",
    "back": "返回",
    "next": "下一步",
    "previous": "上一步"
  },
  "message": {
    "success": {
      "save": "儲存成功",
      "delete": "刪除成功",
      "update": "更新成功"
    },
    "error": {
      "network": "網路錯誤，請稍後再試",
      "unknown": "發生未知錯誤",
      "permission": "您沒有權限執行此操作"
    },
    "warning": {
      "unsaved": "您有未儲存的變更",
      "confirm_delete": "確定要刪除嗎？"
    },
    "info": {
      "loading": "載入中...",
      "processing": "處理中..."
    }
  },
  "time": {
    "second": "秒",
    "minute": "分鐘",
    "hour": "小時",
    "day": "天",
    "week": "週",
    "month": "月",
    "year": "年",
    "ago": "前",
    "just_now": "剛剛"
  },
  "status": {
    "active": "啟用",
    "inactive": "停用",
    "pending": "待處理",
    "completed": "已完成",
    "failed": "失敗"
  }
}
```

### 範例: dashboard.json

```json
{
  "title": "儀表板",
  "description": "查看系統性能與 AI 決策",
  "metrics": {
    "title": "系統指標",
    "cpu": {
      "title": "CPU 使用率",
      "description": "當前 CPU 使用率"
    },
    "memory": {
      "title": "內存使用率",
      "description": "當前內存使用率"
    },
    "response_time": {
      "title": "響應時間",
      "description": "平均響應時間"
    },
    "error_rate": {
      "title": "錯誤率",
      "description": "系統錯誤率"
    }
  },
  "decisions": {
    "title": "最近決策",
    "empty": "目前沒有決策記錄",
    "status": {
      "executed": "已執行",
      "pending": "待審批",
      "failed": "失敗"
    }
  },
  "cost": {
    "title": "成本分析",
    "today": "今日成本",
    "saved": "成本節省",
    "breakdown": "成本分解"
  }
}
```

---

## 🔄 翻譯審校流程

### 流程圖

```
1. 開發者新增 Key (zh-TW)
   ↓
2. 執行缺失翻譯檢測
   ↓
3. 建立翻譯 Issue
   ↓
4. 翻譯人員補充翻譯 (en, ja)
   ↓
5. 審校人員審核
   ↓
6. 合併到 main
```

### 步驟詳解

#### 步驟 1: 開發者新增 Key

當開發者需要新增文字時:

1. **在 `zh-TW/common.json` 或相關檔案新增 Key**
   ```json
   {
     "dashboard.new_feature.title": "新功能"
   }
   ```

2. **在程式碼中使用**
   ```jsx
   import { useTranslation } from 'react-i18next'
   
   function Dashboard() {
     const { t } = useTranslation()
     return <h1>{t('dashboard.new_feature.title')}</h1>
   }
   ```

3. **提交 PR**
   ```bash
   git add .
   git commit -m "feat(i18n): Add new feature title"
   git push
   ```

#### 步驟 2: 執行缺失翻譯檢測

在 PR 中自動執行:

```bash
npm run i18n:check
```

如果有缺失翻譯，CI 會失敗並顯示:

```
❌ Missing translations detected:
- en: dashboard.new_feature.title
- ja: dashboard.new_feature.title
```

#### 步驟 3: 建立翻譯 Issue

自動建立 Issue:

```markdown
## 缺失翻譯

**Key**: `dashboard.new_feature.title`
**中文**: 新功能

需要翻譯:
- [ ] 英文 (en)
- [ ] 日文 (ja)

**相關 PR**: #123
```

#### 步驟 4: 翻譯人員補充翻譯

翻譯人員:

1. **認領 Issue**
2. **補充翻譯**
   ```json
   // en/dashboard.json
   {
     "new_feature": {
       "title": "New Feature"
     }
   }
   
   // ja/dashboard.json
   {
     "new_feature": {
       "title": "新機能"
     }
   }
   ```
3. **提交 PR**
   ```bash
   git checkout -b i18n/dashboard-new-feature
   git add .
   git commit -m "i18n: Add translations for dashboard.new_feature.title"
   git push
   ```

#### 步驟 5: 審校人員審核

審校人員檢查:

- ✅ 翻譯準確性
- ✅ 語氣一致性
- ✅ 文化適應性
- ✅ 格式正確性

#### 步驟 6: 合併到 main

審核通過後合併。

---

## 🛠️ 工具與腳本

### 1. 缺失翻譯檢測腳本

**檔案**: `scripts/check-i18n.js`

```javascript
const fs = require('fs')
const path = require('path')

const localesDir = path.join(__dirname, '../src/i18n/locales')
const languages = ['zh-TW', 'en', 'ja']

function loadTranslations(lang) {
  const langDir = path.join(localesDir, lang)
  const files = fs.readdirSync(langDir).filter(f => f.endsWith('.json'))
  
  const translations = {}
  files.forEach(file => {
    const content = JSON.parse(fs.readFileSync(path.join(langDir, file), 'utf8'))
    const namespace = file.replace('.json', '')
    translations[namespace] = content
  })
  
  return translations
}

function flattenKeys(obj, prefix = '') {
  let keys = []
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (typeof value === 'object' && value !== null) {
      keys = keys.concat(flattenKeys(value, fullKey))
    } else {
      keys.push(fullKey)
    }
  }
  return keys
}

function checkMissingTranslations() {
  const allTranslations = {}
  languages.forEach(lang => {
    allTranslations[lang] = loadTranslations(lang)
  })
  
  // Get all keys from zh-TW (base language)
  const baseKeys = {}
  Object.entries(allTranslations['zh-TW']).forEach(([namespace, content]) => {
    baseKeys[namespace] = flattenKeys(content)
  })
  
  // Check missing keys in other languages
  const missing = {}
  languages.slice(1).forEach(lang => {
    missing[lang] = {}
    Object.entries(baseKeys).forEach(([namespace, keys]) => {
      const langKeys = flattenKeys(allTranslations[lang][namespace] || {})
      const missingKeys = keys.filter(k => !langKeys.includes(k))
      if (missingKeys.length > 0) {
        missing[lang][namespace] = missingKeys
      }
    })
  })
  
  // Report
  let hasMissing = false
  Object.entries(missing).forEach(([lang, namespaces]) => {
    Object.entries(namespaces).forEach(([namespace, keys]) => {
      if (keys.length > 0) {
        hasMissing = true
        console.error(`❌ Missing translations in ${lang}/${namespace}.json:`)
        keys.forEach(key => console.error(`   - ${key}`))
      }
    })
  })
  
  if (hasMissing) {
    process.exit(1)
  } else {
    console.log('✅ All translations are complete!')
  }
}

checkMissingTranslations()
```

### 2. 翻譯統計腳本

**檔案**: `scripts/i18n-stats.js`

```javascript
const fs = require('fs')
const path = require('path')

const localesDir = path.join(__dirname, '../src/i18n/locales')
const languages = ['zh-TW', 'en', 'ja']

function countKeys(obj) {
  let count = 0
  for (const value of Object.values(obj)) {
    if (typeof value === 'object' && value !== null) {
      count += countKeys(value)
    } else {
      count++
    }
  }
  return count
}

function getStats() {
  const stats = {}
  
  languages.forEach(lang => {
    const langDir = path.join(localesDir, lang)
    const files = fs.readdirSync(langDir).filter(f => f.endsWith('.json'))
    
    let totalKeys = 0
    files.forEach(file => {
      const content = JSON.parse(fs.readFileSync(path.join(langDir, file), 'utf8'))
      totalKeys += countKeys(content)
    })
    
    stats[lang] = totalKeys
  })
  
  return stats
}

const stats = getStats()
const baseCount = stats['zh-TW']

console.log('📊 i18n Translation Statistics\n')
console.log(`Base Language (zh-TW): ${baseCount} keys\n`)

languages.slice(1).forEach(lang => {
  const count = stats[lang]
  const percentage = ((count / baseCount) * 100).toFixed(1)
  const bar = '█'.repeat(Math.floor(percentage / 2))
  console.log(`${lang.padEnd(6)} ${bar} ${percentage}% (${count}/${baseCount})`)
})
```

### 3. 新增到 package.json

```json
{
  "scripts": {
    "i18n:check": "node scripts/check-i18n.js",
    "i18n:stats": "node scripts/i18n-stats.js"
  }
}
```

---

## 📋 翻譯品質檢查清單

### 準確性 (Accuracy)

- [ ] 翻譯意思正確
- [ ] 沒有遺漏或增加資訊
- [ ] 專業術語正確

### 一致性 (Consistency)

- [ ] 相同術語使用相同翻譯
- [ ] 語氣一致 (正式/非正式)
- [ ] 格式一致 (標點符號、大小寫)

### 文化適應性 (Localization)

- [ ] 符合目標語言文化
- [ ] 日期/時間格式正確
- [ ] 貨幣格式正確
- [ ] 單位轉換正確

### 可讀性 (Readability)

- [ ] 語句通順
- [ ] 長度適中 (不會超出 UI 空間)
- [ ] 易於理解

### 技術正確性 (Technical)

- [ ] Key 命名正確
- [ ] JSON 格式正確
- [ ] 沒有語法錯誤

---

## 🎯 常見術語翻譯對照表

### 技術術語

| 中文 | 英文 | 日文 |
|------|------|------|
| 儀表板 | Dashboard | ダッシュボード |
| 登入 | Login | ログイン |
| 登出 | Logout | ログアウト |
| 設定 | Settings | 設定 |
| 個人資料 | Profile | プロフィール |
| 通知 | Notifications | 通知 |
| 搜尋 | Search | 検索 |
| 篩選 | Filter | フィルター |
| 排序 | Sort | ソート |
| 匯出 | Export | エクスポート |
| 匯入 | Import | インポート |

### AI 相關術語

| 中文 | 英文 | 日文 |
|------|------|------|
| 人工智慧 | Artificial Intelligence | 人工知能 |
| 機器學習 | Machine Learning | 機械学習 |
| 深度學習 | Deep Learning | ディープラーニング |
| 神經網路 | Neural Network | ニューラルネットワーク |
| 訓練 | Training | トレーニング |
| 推論 | Inference | 推論 |
| 模型 | Model | モデル |
| 準確率 | Accuracy | 精度 |
| 信心度 | Confidence | 信頼度 |

### 系統相關術語

| 中文 | 英文 | 日文 |
|------|------|------|
| CPU 使用率 | CPU Usage | CPU使用率 |
| 內存使用率 | Memory Usage | メモリ使用率 |
| 響應時間 | Response Time | 応答時間 |
| 錯誤率 | Error Rate | エラー率 |
| 吞吐量 | Throughput | スループット |
| 延遲 | Latency | レイテンシ |
| 可用性 | Availability | 可用性 |
| 擴展性 | Scalability | スケーラビリティ |

---

## 🚀 實作步驟

### Week 3-4 實作計劃

#### Day 1: 建立規範與工具

1. **建立 Key 命名規範文件** ✅ (本文件)
2. **重組翻譯檔案結構**
   ```bash
   # 將單一檔案拆分為多個檔案
   src/i18n/locales/zh-TW.json → src/i18n/locales/zh-TW/*.json
   ```
3. **建立檢測腳本**
   - `scripts/check-i18n.js`
   - `scripts/i18n-stats.js`
4. **更新 package.json**
   - 新增 `i18n:check` 腳本
   - 新增 `i18n:stats` 腳本

#### Day 2: 審校與補充

1. **執行缺失翻譯檢測**
   ```bash
   npm run i18n:check
   ```
2. **補充缺失翻譯**
   - 識別所有缺失的 Key
   - 補充英文翻譯
   - 補充日文翻譯
3. **審校現有翻譯**
   - 檢查準確性
   - 檢查一致性
   - 修正錯誤
4. **建立術語對照表** ✅ (本文件)

---

## 📊 成功標準

### 必須達成

- ✅ 建立 Key 命名規範文件
- ✅ 建立翻譯審校流程
- ✅ 建立缺失翻譯檢測工具
- ✅ 所有語言翻譯完整度 ≥ 95%
- ✅ 建立術語對照表

### 加分項

- ✅ 自動化翻譯 Issue 建立
- ✅ 翻譯記憶庫 (Translation Memory)
- ✅ 機器翻譯輔助

---

## 📝 相關文件

- **Token 作用域化**: `TOKEN_SCOPING_IMPLEMENTATION_PLAN.md`
- **可用性測試**: `USABILITY_TESTING_RECRUITMENT_PLAN.md`
- **API 端點驗證**: `API_ENDPOINT_VERIFICATION_REPORT.md`

---

## 🔗 參考資源

- [i18next 官方文件](https://www.i18next.com/)
- [React i18next](https://react.i18next.com/)
- [Google i18n Style Guide](https://developers.google.com/style/translation)

---

**文件版本**: 1.0  
**最後更新**: 2025-10-21  
**負責人**: Devin AI
