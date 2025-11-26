# Apple Design System 使用指南

## 概述

本指南說明如何在 MorningAI 專案中使用 Apple 風格設計系統，包含 iOS 字體系統、情感化色彩、Spring 動畫等完整設計語言。

## 目錄

1. [iOS 字體系統](#ios-字體系統)
2. [情感化色彩系統](#情感化色彩系統)
3. [Apple 組件庫](#apple-組件庫)
4. [Spring 動畫](#spring-動畫)
5. [Glassmorphism 效果](#glassmorphism-效果)
6. [完整頁面範例](#完整頁面範例)

---

## iOS 字體系統

### 可用字體類別

MorningAI 設計系統提供完整的 iOS 字體階層：

#### Display 級別（超大標題）
```tsx
<h1 className="text-display-1">超大標題 (Display 1)</h1>
<h1 className="text-display-2">大標題 (Display 2)</h1>
<h1 className="text-display-3">中標題 (Display 3)</h1>
```

#### Title 級別（標題）
```tsx
<h1 className="text-large-title">Large Title</h1>
<h2 className="text-title-1">Title 1</h2>
<h3 className="text-title-2">Title 2</h3>
<h4 className="text-title-3">Title 3</h4>
```

#### Body 級別（內文）
```tsx
<p className="text-body">標準內文</p>
<p className="text-callout">重點內文</p>
<p className="text-subhead">副標題</p>
```

#### Small 級別（小字）
```tsx
<p className="text-footnote">註腳文字</p>
<span className="text-caption-1">說明文字 1</span>
<span className="text-caption-2">說明文字 2</span>
```

### 使用範例

#### ❌ 錯誤（使用通用 Tailwind）
```tsx
<h1 className="text-3xl font-bold text-neutral-900">
  Dashboard
</h1>
<p className="text-sm text-neutral-600">
  系統概覽
</p>
```

#### ✅ 正確（使用 iOS 字體系統）
```tsx
<h1 className="text-large-title text-neutral-900">
  Dashboard
</h1>
<p className="text-body text-neutral-600">
  系統概覽
</p>
```

---

## 情感化色彩系統

### 五大情感色彩

MorningAI 設計系統提供五種情感化色彩，每種都有完整的明暗模式支援：

#### 1. Joy（喜悅 - 橙色）
```tsx
<div className="bg-joy text-joy-foreground">
  成功訊息、正面反饋
</div>
```

#### 2. Calm（平靜 - 藍色）
```tsx
<div className="bg-calm text-calm-foreground">
  資訊提示、穩定狀態
</div>
```

#### 3. Energy（活力 - 紅色）
```tsx
<div className="bg-energy text-energy-foreground">
  警告訊息、需要注意
</div>
```

#### 4. Growth（成長 - 綠色）
```tsx
<div className="bg-growth text-growth-foreground">
  成功狀態、正向成長
</div>
```

#### 5. Wisdom（智慧 - 紫色）
```tsx
<div className="bg-wisdom text-wisdom-foreground">
  洞察資訊、深度分析
</div>
```

### 語義化色彩映射

根據內容類型選擇適當的情感色彩：

| 內容類型 | 推薦色彩 | 範例 |
|---------|---------|------|
| 成功/完成 | Growth (綠) | 任務完成、測試通過 |
| 資訊/穩定 | Calm (藍) | 系統狀態、一般通知 |
| 警告/注意 | Joy (橙) | 需要審核、待處理 |
| 錯誤/危險 | Energy (紅) | 失敗訊息、錯誤狀態 |
| 洞察/智慧 | Wisdom (紫) | AI 建議、深度分析 |

### 使用範例

```tsx
// 狀態卡片
<Card className="bg-growth/10 border-growth">
  <CardContent>
    <h3 className="text-title-3 text-growth-foreground">
      部署成功
    </h3>
    <p className="text-body text-growth-foreground/80">
      應用程式已成功部署到生產環境
    </p>
  </CardContent>
</Card>

// 警告橫幅
<Alert className="bg-energy/10 border-energy">
  <AlertTriangle className="text-energy" />
  <AlertDescription className="text-energy-foreground">
    CI 檢查失敗，請查看詳細日誌
  </AlertDescription>
</Alert>
```

---

## Apple 組件庫

### 可用組件

MorningAI 提供 15+ 個 Apple 風格組件：

#### 核心組件
- `AppleButton` - iOS 風格按鈕（支援 haptic feedback）
- `AppleInput` - iOS 風格輸入框
- `AppleModal` - iOS 風格模態框
- `AppleSheet` - iOS 風格底部彈出層
- `AppleToast` - iOS 風格提示訊息

#### 進階組件
- `AppleLiveActivity` - 即時活動顯示
- `AppleControlCenter` - 控制中心
- `AppleActionSheet` - 動作選單
- `AppleSpotlight` - 搜尋介面
- `AppleTabBar` - 標籤列
- `ApplePicker` - 選擇器
- `AppleSegmentedControl` - 分段控制器

### AppleButton 使用範例

```tsx
import { AppleButton } from '@/components/ui/apple-button'

// 主要按鈕
<AppleButton variant="primary" haptic="medium">
  確認
</AppleButton>

// 次要按鈕
<AppleButton variant="outline" haptic="light">
  取消
</AppleButton>

// 危險按鈕
<AppleButton variant="destructive" haptic="heavy">
  刪除
</AppleButton>

// 載入狀態
<AppleButton disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  處理中...
</AppleButton>
```

### AppleInput 使用範例

```tsx
import { AppleInput } from '@/components/ui/apple-input'
import { User, Lock } from 'lucide-react'

// 基本輸入框
<AppleInput
  label="電子郵件"
  placeholder="your@email.com"
  leftIcon={<User className="w-4 h-4" />}
  haptic="light"
/>

// 密碼輸入框
<AppleInput
  type="password"
  label="密碼"
  placeholder="輸入密碼"
  leftIcon={<Lock className="w-4 h-4" />}
  showPasswordToggle
  haptic="light"
/>
```

---

## Spring 動畫

### 標準 Spring 參數

MorningAI 使用 Apple 標準的 Spring 物理動畫：

```tsx
import { motion } from 'framer-motion'

// 標準 Spring 動畫
<motion.div
  whileHover={{ scale: 1.05 }}
  transition={{
    type: 'spring',
    stiffness: 500,
    damping: 30
  }}
>
  懸停時放大
</motion.div>

// 使用 cubic-bezier（Apple 標準）
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{
    duration: 0.6,
    ease: [0.22, 1, 0.36, 1] // Apple 標準 easing
  }}
>
  淡入並上移
</motion.div>
```

### 預設 Easing 曲線

```css
/* index.css 中已定義 */
--ease-apple: cubic-bezier(0.34, 1.56, 0.64, 1);
--ease-smooth: cubic-bezier(0.22, 1, 0.36, 1);
```

---

## Glassmorphism 效果

### 標準毛玻璃效果

```tsx
// 毛玻璃卡片
<div className="bg-white/80 backdrop-blur-xl shadow-lg rounded-2xl p-6">
  <h3 className="text-title-3">毛玻璃效果</h3>
  <p className="text-body">背景模糊，半透明</p>
</div>

// 深色模式毛玻璃
<div className="bg-neutral-900/80 dark:bg-white/10 backdrop-blur-xl">
  深色模式毛玻璃
</div>
```

### 進階毛玻璃效果

```tsx
// 多層次毛玻璃
<div className="relative">
  <div className="absolute inset-0 bg-gradient-to-br from-joy/20 to-calm/20 backdrop-blur-2xl" />
  <div className="relative z-10 p-8">
    <h2 className="text-large-title">內容</h2>
  </div>
</div>
```

---

## 完整頁面範例

### 範例 1：Dashboard 頁面

```tsx
import { AppleButton } from '@/components/ui/apple-button'
import { Card, CardContent, CardHeader, CardTitle } from '@morningai/shared-ui'

const Dashboard = () => {
  return (
    <div className="p-6 space-y-6">
      {/* 頁面標題 */}
      <div>
        <h1 className="text-large-title text-neutral-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-body text-neutral-600 dark:text-neutral-400 mt-2">
          系統概覽與即時監控
        </p>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-growth/10 border-growth">
          <CardHeader>
            <CardTitle className="text-title-3 text-growth-foreground">
              活躍用戶
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-display-3 font-bold text-growth-foreground">
              1,234
            </p>
            <p className="text-footnote text-growth-foreground/70 mt-2">
              較上週增長 12%
            </p>
          </CardContent>
        </Card>

        <Card className="bg-calm/10 border-calm">
          <CardHeader>
            <CardTitle className="text-title-3 text-calm-foreground">
              系統狀態
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-display-3 font-bold text-calm-foreground">
              正常
            </p>
            <p className="text-footnote text-calm-foreground/70 mt-2">
              所有服務運行中
            </p>
          </CardContent>
        </Card>

        <Card className="bg-wisdom/10 border-wisdom">
          <CardHeader>
            <CardTitle className="text-title-3 text-wisdom-foreground">
              AI 建議
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-display-3 font-bold text-wisdom-foreground">
              3
            </p>
            <p className="text-footnote text-wisdom-foreground/70 mt-2">
              待審核的優化建議
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 操作按鈕 */}
      <div className="flex gap-3">
        <AppleButton variant="primary" haptic="medium">
          新增任務
        </AppleButton>
        <AppleButton variant="outline" haptic="light">
          查看報告
        </AppleButton>
      </div>
    </div>
  )
}
```

### 範例 2：登入頁面

```tsx
import { AppleButton } from '@/components/ui/apple-button'
import { AppleInput } from '@/components/ui/apple-input'
import { Card, CardContent, CardHeader, CardTitle } from '@morningai/shared-ui'
import { User, Lock } from 'lucide-react'

const LoginPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900">
      <div className="w-full max-w-md px-4">
        <div className="text-center mb-8">
          <h1 className="text-display-3 font-bold text-neutral-900 dark:text-white">
            Morning AI
          </h1>
          <p className="text-body text-neutral-600 dark:text-neutral-400 mt-2">
            AI 驅動的自主編排平台
          </p>
        </div>

        <Card className="bg-white/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-title-2">登入</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <AppleInput
              label="電子郵件"
              placeholder="your@email.com"
              leftIcon={<User className="w-4 h-4" />}
              haptic="light"
            />

            <AppleInput
              type="password"
              label="密碼"
              placeholder="輸入密碼"
              leftIcon={<Lock className="w-4 h-4" />}
              showPasswordToggle
              haptic="light"
            />

            <AppleButton variant="primary" className="w-full" haptic="medium">
              登入
            </AppleButton>

            <p className="text-center text-footnote text-neutral-600 dark:text-neutral-400">
              還沒有帳號？{' '}
              <a href="/signup" className="text-primary-600 hover:text-primary-700">
                註冊
              </a>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

---

## 遷移檢查清單

### 字體系統遷移

- [ ] 將 `text-3xl` 替換為 `text-display-3` 或 `text-large-title`
- [ ] 將 `text-2xl` 替換為 `text-title-1`
- [ ] 將 `text-xl` 替換為 `text-title-2`
- [ ] 將 `text-lg` 替換為 `text-title-3`
- [ ] 將 `text-base` 替換為 `text-body`
- [ ] 將 `text-sm` 替換為 `text-subhead` 或 `text-footnote`
- [ ] 將 `text-xs` 替換為 `text-caption-1` 或 `text-caption-2`

### 色彩系統遷移

- [ ] 檢查硬編碼的 hex 色碼（如 `#FF6B35`）
- [ ] 將成功狀態改用 `bg-growth` 或 `text-growth`
- [ ] 將資訊狀態改用 `bg-calm` 或 `text-calm`
- [ ] 將警告狀態改用 `bg-joy` 或 `text-joy`
- [ ] 將錯誤狀態改用 `bg-energy` 或 `text-energy`
- [ ] 將洞察狀態改用 `bg-wisdom` 或 `text-wisdom`

### 組件遷移

- [ ] 將標準 `<button>` 替換為 `<AppleButton>`
- [ ] 將標準 `<input>` 替換為 `<AppleInput>`
- [ ] 為互動元素添加 `haptic` 屬性
- [ ] 檢查是否需要使用進階 Apple 組件（Modal, Sheet, Toast 等）

### 動畫遷移

- [ ] 將標準 `transition` 替換為 Spring 動畫
- [ ] 使用 Apple 標準 easing: `[0.22, 1, 0.36, 1]`
- [ ] 為懸停效果添加 `whileHover` 動畫
- [ ] 為點擊效果添加 `whileTap` 動畫

### 主題整合

- [ ] 確認 `theme-apple` class 已應用到根元素
- [ ] 確認 `index.css` 包含完整設計系統
- [ ] 確認 `theme-apple.css` 已正確引入
- [ ] 測試深色模式切換

---

## 常見問題

### Q: 何時使用 `text-large-title` vs `text-display-1`?

**A:** 
- `text-large-title`: 用於頁面主標題（如 Dashboard 標題）
- `text-display-1/2/3`: 用於 Hero 區塊、Landing Page 的超大標題

### Q: 如何選擇情感色彩？

**A:** 根據內容的情感意圖：
- 成功/成長 → Growth (綠)
- 穩定/資訊 → Calm (藍)
- 警告/待處理 → Joy (橙)
- 錯誤/危險 → Energy (紅)
- 洞察/智慧 → Wisdom (紫)

### Q: Haptic feedback 是什麼？

**A:** Haptic feedback 是 iOS 的觸覺反饋。在 Web 上，`AppleButton` 會模擬這個效果（通過動畫和視覺反饋）。參數：
- `light`: 輕微反饋（次要操作）
- `medium`: 中等反饋（一般操作）
- `heavy`: 強烈反饋（重要/危險操作）

### Q: 如何確保無障礙性？

**A:** 
1. 使用語義化 HTML 標籤
2. 為互動元素添加 `aria-label`
3. 確保色彩對比度符合 WCAG AAA 標準（設計系統已內建）
4. 支援鍵盤導航
5. 使用 `AppleAccessibilitySettings` 組件提供無障礙選項

---

## 相關資源

- [Storybook 組件文檔](http://localhost:6006)
- [Tailwind v4 文檔](https://tailwindcss.com/docs)
- [Framer Motion 文檔](https://www.framer.com/motion/)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)

---

**最後更新**: 2025-11-25  
**版本**: 1.0.0  
**維護者**: MorningAI 團隊
