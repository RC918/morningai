# 文案與 i18n 指南

## 概述

清楚、簡潔、可行動的文案是優秀用戶體驗的基礎。本指南涵蓋文案撰寫原則、語氣指南、i18n 流程與翻譯品質標準。

## 文案原則

### 1. 清楚 (Clear)

**避免模糊與專業術語**

```
❌ 錯誤：Leverage our AI-powered solution to optimize your workflow
✅ 正確：Use AI to automate your tasks

❌ 錯誤：系統正在進行資料同步作業
✅ 正確：正在同步資料...
```

**使用簡單詞彙**

```
❌ 錯誤：Utilize, commence, terminate
✅ 正確：Use, start, end

❌ 錯誤：請確認您的認證資訊
✅ 正確：請確認您的登入資訊
```

### 2. 簡潔 (Concise)

**移除冗餘詞彙**

```
❌ 錯誤：In order to save your changes, please click the save button
✅ 正確：Click Save to save your changes

❌ 錯誤：為了要儲存您的變更,請點擊儲存按鈕
✅ 正確：點擊「儲存」以保存變更
```

**使用主動語態**

```
❌ 錯誤：Your changes have been saved by the system
✅ 正確：Saved your changes

❌ 錯誤：您的變更已被系統儲存
✅ 正確：已保存變更
```

### 3. 可行動 (Actionable)

**告訴用戶該做什麼**

```
❌ 錯誤：An error occurred
✅ 正確：Failed to save. Please try again.

❌ 錯誤：發生錯誤
✅ 正確：保存失敗,請重試
```

**使用動詞開頭**

```
✅ 按鈕文案：
- Save (保存)
- Cancel (取消)
- Delete (刪除)
- Create (建立)
- Edit (編輯)
- Export (匯出)

❌ 避免：
- Saving... (改為 "Save")
- Deletion (改為 "Delete")
```

### 4. 一致 (Consistent)

**統一用詞**

| 概念 | 英文 | 繁中 | 避免 |
|------|------|------|------|
| 儲存 | Save | 保存 | 儲存、存檔 |
| 取消 | Cancel | 取消 | 放棄、不要 |
| 刪除 | Delete | 刪除 | 移除、清除 |
| 建立 | Create | 建立 | 新增、創建 |
| 編輯 | Edit | 編輯 | 修改、更改 |
| 設定 | Settings | 設定 | 設置、配置 |
| 登入 | Sign in | 登入 | 登錄、簽入 |
| 登出 | Sign out | 登出 | 登出、簽出 |

## 語氣指南

### 品牌語氣

MorningAI 的語氣是：
- **專業但友善** (Professional yet friendly)
- **自信但謙遜** (Confident yet humble)
- **清楚但不冷漠** (Clear but not cold)

### 情境語氣

#### 成功訊息

```
英文：
- Saved successfully
- Task created
- Changes applied

繁中：
- 已保存
- 已建立任務
- 已套用變更
```

#### 錯誤訊息

```
英文：
- Failed to save. Please try again.
- Invalid email address
- Connection lost. Reconnecting...

繁中：
- 保存失敗,請重試
- 電子郵件格式錯誤
- 連線中斷,正在重新連線...
```

#### 警告訊息

```
英文：
- This action cannot be undone
- You have unsaved changes
- Your session will expire in 5 minutes

繁中：
- 此操作無法復原
- 有未保存的變更
- 您的工作階段將在 5 分鐘後過期
```

#### 引導訊息

```
英文：
- Get started by creating your first task
- Connect your GitHub account to continue
- Upgrade to unlock this feature

繁中：
- 建立第一個任務以開始使用
- 連接您的 GitHub 帳號以繼續
- 升級以解鎖此功能
```

#### 空狀態

```
英文：
- No tasks yet
- Start by creating your first strategy
- Your dashboard is empty. Add widgets to get started.

繁中：
- 尚無任務
- 建立第一個策略以開始
- 您的儀表板是空的。新增小工具以開始使用。
```

## 按鈕文案

### 主要操作

```
英文 → 繁中
- Save → 保存
- Create → 建立
- Submit → 提交
- Confirm → 確認
- Continue → 繼續
- Next → 下一步
- Finish → 完成
```

### 次要操作

```
英文 → 繁中
- Cancel → 取消
- Back → 返回
- Skip → 跳過
- Close → 關閉
- Dismiss → 關閉
```

### 危險操作

```
英文 → 繁中
- Delete → 刪除
- Remove → 移除
- Revoke → 撤銷
- Disable → 停用
```

### 載入狀態

```
英文 → 繁中
- Saving... → 正在保存...
- Loading... → 載入中...
- Processing... → 處理中...
- Uploading... → 上傳中...
```

## 表單文案

### 標籤

```
英文 → 繁中
- Email → 電子郵件
- Password → 密碼
- Name → 姓名
- Company → 公司
- Phone → 電話
- Address → 地址
```

### 佔位符

```
英文 → 繁中
- Enter your email → 輸入您的電子郵件
- Search... → 搜尋...
- Type a message → 輸入訊息
- Select an option → 選擇選項
```

### 幫助文字

```
英文 → 繁中
- We'll never share your email → 我們不會分享您的電子郵件
- At least 8 characters → 至少 8 個字元
- Optional → 選填
- Required → 必填
```

### 錯誤訊息

```
英文 → 繁中
- This field is required → 此欄位為必填
- Invalid email address → 電子郵件格式錯誤
- Password must be at least 8 characters → 密碼至少需要 8 個字元
- Passwords do not match → 密碼不相符
```

## i18n 流程

### 分工

**設計師**
1. 撰寫英文文案 (en-US)
2. 提供繁中翻譯建議 (zh-TW)
3. 提交 i18n key 與翻譯草稿

**母語者審校**
1. 審校英文文案 (語法、語氣)
2. 審校繁中翻譯 (自然度、準確性)
3. 提供修改建議

**工程師**
1. 整合 i18n key 到系統
2. 驗證翻譯顯示效果
3. 處理複數與變數

### i18n Key 命名

```
{namespace}.{section}.{element}.{variant}

範例：
- dashboard.widgets.cpu.title
- auth.login.form.email.label
- errors.validation.required
- buttons.actions.save
```

### 翻譯檔案結構

```json
// en-US.json
{
  "dashboard": {
    "title": "Dashboard",
    "widgets": {
      "cpu": {
        "title": "CPU Usage",
        "description": "Current CPU utilization"
      }
    }
  },
  "auth": {
    "login": {
      "title": "Sign In",
      "form": {
        "email": {
          "label": "Email",
          "placeholder": "Enter your email"
        },
        "password": {
          "label": "Password",
          "placeholder": "Enter your password"
        }
      },
      "buttons": {
        "submit": "Sign In",
        "forgot": "Forgot password?"
      }
    }
  },
  "errors": {
    "validation": {
      "required": "This field is required",
      "email": "Invalid email address"
    }
  }
}
```

```json
// zh-TW.json
{
  "dashboard": {
    "title": "儀表板",
    "widgets": {
      "cpu": {
        "title": "CPU 使用率",
        "description": "目前 CPU 使用率"
      }
    }
  },
  "auth": {
    "login": {
      "title": "登入",
      "form": {
        "email": {
          "label": "電子郵件",
          "placeholder": "輸入您的電子郵件"
        },
        "password": {
          "label": "密碼",
          "placeholder": "輸入您的密碼"
        }
      },
      "buttons": {
        "submit": "登入",
        "forgot": "忘記密碼?"
      }
    }
  },
  "errors": {
    "validation": {
      "required": "此欄位為必填",
      "email": "電子郵件格式錯誤"
    }
  }
}
```

### 使用範例

```jsx
import { useTranslation } from 'react-i18next'

function LoginForm() {
  const { t } = useTranslation()

  return (
    <form>
      <h1>{t('auth.login.title')}</h1>
      
      <div>
        <label htmlFor="email">
          {t('auth.login.form.email.label')}
        </label>
        <input
          id="email"
          type="email"
          placeholder={t('auth.login.form.email.placeholder')}
        />
      </div>

      <div>
        <label htmlFor="password">
          {t('auth.login.form.password.label')}
        </label>
        <input
          id="password"
          type="password"
          placeholder={t('auth.login.form.password.placeholder')}
        />
      </div>

      <button type="submit">
        {t('auth.login.buttons.submit')}
      </button>
    </form>
  )
}
```

### 複數處理

```json
// en-US.json
{
  "tasks": {
    "count": "{{count}} task",
    "count_plural": "{{count}} tasks"
  }
}

// zh-TW.json
{
  "tasks": {
    "count": "{{count}} 個任務"
  }
}
```

```jsx
// 使用
{t('tasks.count', { count: 1 })}  // "1 task" / "1 個任務"
{t('tasks.count', { count: 5 })}  // "5 tasks" / "5 個任務"
```

### 變數插值

```json
// en-US.json
{
  "welcome": "Welcome back, {{name}}!",
  "saved": "Saved {{count}} items"
}

// zh-TW.json
{
  "welcome": "歡迎回來,{{name}}!",
  "saved": "已保存 {{count}} 個項目"
}
```

```jsx
// 使用
{t('welcome', { name: 'Ryan' })}  // "Welcome back, Ryan!" / "歡迎回來,Ryan!"
{t('saved', { count: 5 })}  // "Saved 5 items" / "已保存 5 個項目"
```

## 翻譯品質標準

### 避免直譯

```
❌ 錯誤直譯：
- "Introducing Morning AI" → "介紹 Morning AI"
- "Intelligent decision making" → "智能決策製作"
- "Get Started" → "得到開始"

✅ 正確翻譯：
- "Introducing Morning AI" → "全新：Morning AI"
- "Intelligent decision making" → "智能決策"
- "Get Started" → "開始使用"
```

### 保持自然語感

```
❌ 不自然：
- "您的變更已經被成功地儲存了"
- "請您點擊這個按鈕以便繼續"

✅ 自然：
- "已保存變更"
- "點擊「繼續」"
```

### 文化適應

```
英文：
- "Sign up for free trial"
- "No credit card required"

繁中（台灣）：
- "免費試用"
- "無需信用卡"

繁中（中國）：
- "免费试用"
- "无需信用卡"
```

## 審校流程

### 1. 設計師提交

```markdown
## 新增 i18n Keys

### auth.login.title
- en-US: "Sign In"
- zh-TW: "登入"

### auth.login.form.email.label
- en-US: "Email"
- zh-TW: "電子郵件"

### auth.login.form.email.placeholder
- en-US: "Enter your email"
- zh-TW: "輸入您的電子郵件"
```

### 2. 母語者審校

```markdown
## 審校結果

### auth.login.title
- ✅ en-US: "Sign In" (OK)
- ✅ zh-TW: "登入" (OK)

### auth.login.form.email.placeholder
- ✅ en-US: "Enter your email" (OK)
- ⚠️ zh-TW: "輸入您的電子郵件" → 建議改為 "請輸入電子郵件"
```

### 3. 工程師整合

```bash
# 1. 更新 i18n 檔案
# handoff/20250928/40_App/frontend-dashboard/src/locales/en-US.json
# handoff/20250928/40_App/frontend-dashboard/src/locales/zh-TW.json

# 2. 驗證翻譯
pnpm run dev

# 3. 提交工程 PR
git add src/locales/
git commit -m "工程 PR: 整合登入頁面 i18n"
```

## 常見錯誤

### ❌ 過度使用行銷套語

```
❌ 錯誤：
- "Revolutionize your workflow"
- "Unlock the power of AI"
- "Transform your business"

✅ 正確：
- "Automate your tasks"
- "Use AI to save time"
- "Improve your operations"
```

### ❌ 使用被動語態

```
❌ 錯誤：
- "Your changes have been saved"
- "The file was uploaded successfully"

✅ 正確：
- "Saved your changes"
- "Uploaded file"
```

### ❌ 冗長描述

```
❌ 錯誤：
- "In order to proceed with the next step, please click on the continue button below"

✅ 正確：
- "Click Continue"
```

### ❌ 不一致用詞

```
❌ 錯誤：
- 頁面 A: "儲存"
- 頁面 B: "保存"
- 頁面 C: "存檔"

✅ 正確：
- 統一使用: "保存"
```

## 工具與資源

### 翻譯工具
- [i18next](https://www.i18next.com/) - i18n 框架
- [react-i18next](https://react.i18next.com/) - React 整合
- [DeepL](https://www.deepl.com/) - 翻譯參考（需人工審校）

### 文案工具
- [Hemingway Editor](https://hemingwayapp.com/) - 檢查可讀性
- [Grammarly](https://www.grammarly.com/) - 語法檢查
- [LanguageTool](https://languagetool.org/) - 多語言檢查

### 參考資源
- [Google Material Design Writing](https://material.io/design/communication/writing.html)
- [Apple Human Interface Guidelines - Writing](https://developer.apple.com/design/human-interface-guidelines/writing)
- [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/welcome/)

## 檢查清單

### 文案撰寫

- [ ] 清楚：避免模糊與專業術語
- [ ] 簡潔：移除冗餘詞彙
- [ ] 可行動：告訴用戶該做什麼
- [ ] 一致：統一用詞與語氣
- [ ] 友善：專業但不冷漠

### 翻譯品質

- [ ] 避免直譯
- [ ] 保持自然語感
- [ ] 文化適應
- [ ] 用詞一致
- [ ] 經母語者審校

### i18n 整合

- [ ] Key 命名規範
- [ ] 檔案結構正確
- [ ] 複數處理正確
- [ ] 變數插值正確
- [ ] 顯示效果驗證

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |
