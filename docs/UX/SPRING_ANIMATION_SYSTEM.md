# Spring Animation System - Apple-Level UI/UX

## 概述

Spring Animation System 實現了 Apple Human Interface Guidelines 中的彈性動畫系統，為 UI 提供自然、流暢的物理感動效。基於彈簧物理模型，創造出符合人類直覺的動畫體驗。

## 為什麼使用彈性動畫？

### Apple 的設計哲學
Apple 在 iOS 和 macOS 中廣泛使用彈性動畫，因為它們：
- **自然**：模擬真實世界的物理運動
- **流暢**：沒有突兀的開始和結束
- **響應式**：可以在動畫進行中被打斷和重新開始
- **愉悅**：為用戶提供愉悅的互動體驗

### 與傳統緩動函數的對比

```javascript
// 傳統緩動 (Easing)
transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
// 問題：固定時長，無法中斷，缺乏物理感

// 彈性動畫 (Spring)
transition: { type: 'spring', stiffness: 170, damping: 26 }
// 優勢：自然減速，可中斷，符合物理直覺
```

## 6 種彈性預設

### 1. Gentle (溫和)
**最柔和的彈性動畫**

```javascript
{
  stiffness: 120,
  damping: 14,
  mass: 0.5,
  duration: 0.6
}
```

**適用場景**:
- 背景元素的淡入淡出
- 次要信息的顯示
- 環境變化（如主題切換）
- 不需要引起注意的動畫

**範例**:
```jsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={getSpringConfig('gentle')}
>
  背景內容
</motion.div>
```

### 2. Default (標準)
**標準 iOS 動畫（推薦）**

```javascript
{
  stiffness: 170,
  damping: 26,
  mass: 1,
  duration: 0.5
}
```

**適用場景**:
- 大多數 UI 元素的動畫
- 卡片展開/收起
- 模態對話框
- 導航過渡

**範例**:
```jsx
<motion.div
  variants={getSpringVariants('slideUp', 'default')}
  initial="initial"
  animate="animate"
>
  標準動畫
</motion.div>
```

### 3. Bouncy (彈跳)
**活潑、有趣的彈性動畫**

```javascript
{
  stiffness: 260,
  damping: 20,
  mass: 0.8,
  duration: 0.7
}
```

**適用場景**:
- 成功反饋
- 遊戲化元素
- 慶祝動畫
- 需要強調的互動

**範例**:
```jsx
<motion.button
  whileTap={{ scale: 0.95 }}
  whileHover={{ scale: 1.05 }}
  transition={getSpringConfig('bouncy')}
>
  點擊我
</motion.button>
```

### 4. Snappy (敏捷)
**快速、響應式的動畫**

```javascript
{
  stiffness: 300,
  damping: 30,
  mass: 0.6,
  duration: 0.4
}
```

**適用場景**:
- 按鈕按壓反饋
- 快速切換
- 下拉菜單
- 工具提示

**範例**:
```jsx
<motion.div
  variants={getSpringVariants('pop', 'snappy')}
  animate="animate"
>
  快速反饋
</motion.div>
```

### 5. Smooth (流暢)
**優雅、流暢的動畫**

```javascript
{
  stiffness: 100,
  damping: 20,
  mass: 1.2,
  duration: 0.8
}
```

**適用場景**:
- 大型元素的移動
- 頁面過渡
- 滾動動畫
- 需要優雅感的場景

**範例**:
```jsx
<motion.div
  variants={getSpringVariants('slideLeft', 'smooth')}
  initial="initial"
  animate="animate"
>
  優雅過渡
</motion.div>
```

### 6. Wobbly (搖擺)
**誇張的彈性效果**

```javascript
{
  stiffness: 180,
  damping: 12,
  mass: 1,
  duration: 0.9
}
```

**適用場景**:
- 錯誤提示
- 引起注意的元素
- 特殊效果
- 遊戲化互動

**範例**:
```jsx
<motion.div
  variants={getSpringVariants('shake', 'wobbly')}
  animate="animate"
>
  注意！
</motion.div>
```

## 動畫變體類型

### 基礎動畫

#### Fade (淡入淡出)
```jsx
<motion.div variants={getSpringVariants('fade', 'default')}>
  淡入淡出
</motion.div>
```

#### Scale (縮放)
```jsx
<motion.div variants={getSpringVariants('scale', 'default')}>
  縮放動畫
</motion.div>
```

#### Pop (彈出)
```jsx
<motion.button variants={getSpringVariants('pop', 'snappy')}>
  按鈕彈出
</motion.button>
```

### 滑動動畫

#### Slide Up (向上滑動)
```jsx
<motion.div variants={getSpringVariants('slideUp', 'default')}>
  Sheet / Modal
</motion.div>
```

#### Slide Down (向下滑動)
```jsx
<motion.div variants={getSpringVariants('slideDown', 'default')}>
  Dropdown / Menu
</motion.div>
```

#### Slide Left/Right (左右滑動)
```jsx
<motion.div variants={getSpringVariants('slideLeft', 'smooth')}>
  導航過渡
</motion.div>
```

### 特殊動畫

#### Bounce (彈跳)
```jsx
<motion.div variants={getSpringVariants('bounce', 'bouncy')}>
  成功反饋
</motion.div>
```

#### Shake (搖晃)
```jsx
<motion.div variants={getSpringVariants('shake', 'wobbly')}>
  錯誤提示
</motion.div>
```

#### Pulse (脈衝)
```jsx
<motion.div variants={getSpringVariants('pulse', 'default')}>
  通知提示
</motion.div>
```

## 觸覺反饋模擬

### 7 種觸覺反饋類型

#### 1. Light (輕微)
```javascript
triggerHaptic(element, 'light')
// 視覺效果：scale [1, 0.98, 1]
// 時長：10ms
```

**適用場景**：選擇項目、輕觸按鈕

#### 2. Medium (中等)
```javascript
triggerHaptic(element, 'medium')
// 視覺效果：scale [1, 0.96, 1]
// 時長：15ms
```

**適用場景**：確認操作、切換開關

#### 3. Heavy (重度)
```javascript
triggerHaptic(element, 'heavy')
// 視覺效果：scale [1, 0.94, 1.02, 1]
// 時長：20ms
```

**適用場景**：重要操作、刪除確認

#### 4. Success (成功)
```javascript
triggerHaptic(element, 'success')
// 視覺效果：scale [1, 0.95, 1.05, 1]
// 時長：25ms
// 模式：[10, 5, 10]
```

**適用場景**：操作成功、任務完成

#### 5. Warning (警告)
```javascript
triggerHaptic(element, 'warning')
// 視覺效果：x [0, -3, 3, -3, 3, 0]
// 時長：30ms
// 模式：[15, 10, 15]
```

**適用場景**：警告提示、需要注意

#### 6. Error (錯誤)
```javascript
triggerHaptic(element, 'error')
// 視覺效果：x [0, -5, 5, -5, 5, -3, 3, 0]
// 時長：35ms
// 模式：[20, 10, 20, 10, 20]
```

**適用場景**：錯誤提示、操作失敗

#### 7. Selection (選擇)
```javascript
triggerHaptic(element, 'selection')
// 視覺效果：scale [1, 0.99, 1]
// 時長：8ms
```

**適用場景**：列表選擇、Picker 滾動

### 使用範例

```jsx
import { triggerHaptic, getHapticAnimation } from '@/lib/spring-animation';

// 方式 1：直接觸發
const handleClick = (e) => {
  triggerHaptic(e.currentTarget, 'medium');
};

// 方式 2：配合 Framer Motion
<motion.button
  whileTap={getHapticAnimation('medium')}
  onClick={handleClick}
>
  按鈕
</motion.button>

// 方式 3：CSS 類名
<button className="haptic-medium" onClick={handleClick}>
  按鈕
</button>
```

## 上下文感知動畫

### 自動適應用戶環境

```javascript
import { getContextualAnimation, getUserContext } from '@/lib/spring-animation';

// 獲取用戶上下文
const context = getUserContext();
// {
//   isMobile: true/false,
//   isLowPower: true/false,
//   connectionSpeed: 'fast'/'medium'/'slow',
//   userPreference: 'default'/'playful'/'minimal'
// }

// 根據上下文選擇動畫
const animation = getContextualAnimation('slideUp', context);
```

### 適應規則

| 條件 | 動畫預設 | 原因 |
|------|---------|------|
| 低電量模式 | Snappy | 節省資源 |
| 慢速網絡 | Snappy | 減少延遲感 |
| 移動設備 | Smooth | 觸控友好 |
| 用戶偏好：活潑 | Bouncy | 更有表現力 |
| 用戶偏好：簡約 | Gentle | 更微妙 |

### 設置用戶偏好

```javascript
// 保存用戶偏好
localStorage.setItem('animationPreference', 'playful');

// 選項：'default', 'playful', 'minimal'
```

## 連續性動畫

### 動畫序列

```javascript
import { createAnimationSequence } from '@/lib/spring-animation';

const sequence = createAnimationSequence([
  { duration: 0.3 },  // 步驟 1
  { duration: 0.2 },  // 步驟 2
  { duration: 0.4 }   // 步驟 3
], 'default');

<motion.div
  animate={{
    scale: [1, 1.2, 0.9, 1],
    rotate: [0, 0, 180, 180]
  }}
  transition={sequence}
/>
```

### 交錯動畫

```javascript
import { getStaggerConfig } from '@/lib/spring-animation';

<motion.div
  variants={{
    animate: {
      transition: getStaggerConfig('default', 0.05)
    }
  }}
>
  {items.map((item, i) => (
    <motion.div
      key={i}
      variants={getSpringVariants('slideUp', 'default')}
    >
      {item}
    </motion.div>
  ))}
</motion.div>
```

## 性能監控

### 追蹤動畫性能

```javascript
import { trackAnimation, getAnimationMetrics } from '@/lib/spring-animation';

// 開始追蹤
trackAnimation('my-animation-id');

// 獲取指標
const metrics = getAnimationMetrics();
console.log(metrics);
// {
//   totalAnimations: 150,
//   activeAnimations: 3,
//   droppedFrames: 5,
//   averageFPS: 58.5
// }
```

### 性能指標

- **totalAnimations**: 總動畫數量
- **activeAnimations**: 當前活躍動畫數量
- **droppedFrames**: 掉幀數量
- **averageFPS**: 平均幀率

### 性能優化建議

```javascript
// ✅ 好 - 限制同時動畫數量
if (metrics.activeAnimations < 5) {
  startAnimation();
}

// ✅ 好 - 檢測性能問題
if (metrics.averageFPS < 55) {
  // 降級到更簡單的動畫
  useSimpleAnimation();
}

// ❌ 不好 - 無限制的動畫
items.forEach(item => animateItem(item));
```

## CSS 工具類

### 彈性過渡類

```html
<!-- 溫和彈性 -->
<div class="spring-gentle transition-all">內容</div>

<!-- 標準彈性 -->
<div class="spring-default transition-all">內容</div>

<!-- 彈跳彈性 -->
<div class="spring-bouncy transition-all">內容</div>

<!-- 敏捷彈性 -->
<div class="spring-snappy transition-all">內容</div>

<!-- 流暢彈性 -->
<div class="spring-smooth transition-all">內容</div>

<!-- 搖擺彈性 -->
<div class="spring-wobbly transition-all">內容</div>
```

### 按鈕按壓效果

```html
<button class="btn-spring-press">
  標準按壓
</button>

<button class="btn-spring-press-heavy">
  重度按壓
</button>
```

### Hover 效果

```html
<!-- 提升效果 -->
<div class="spring-hover-lift">懸停提升</div>

<!-- 縮放效果 -->
<div class="spring-hover-scale">懸停縮放</div>

<!-- 發光效果 -->
<div class="spring-hover-glow">懸停發光</div>
```

### 動畫類

```html
<!-- 彈出動畫 -->
<div class="pop-in">彈入</div>

<!-- 彈跳成功 -->
<div class="bounce-success">成功！</div>

<!-- 滑動動畫 -->
<div class="slide-up">向上滑動</div>
<div class="slide-down">向下滑動</div>
<div class="slide-left">向左滑動</div>
<div class="slide-right">向右滑動</div>

<!-- 搖晃動畫 -->
<div class="shake">錯誤提示</div>

<!-- 脈衝動畫 -->
<div class="pulse">通知</div>
```

### 交錯子元素

```html
<div class="stagger-children">
  <div>項目 1</div>
  <div>項目 2</div>
  <div>項目 3</div>
  <!-- 自動交錯動畫，每個延遲 50ms -->
</div>
```

## 實際應用範例

### 按鈕互動

```jsx
import { motion } from 'framer-motion';
import { getSpringConfig, triggerHaptic } from '@/lib/spring-animation';

const Button = ({ children, onClick }) => {
  const handleClick = (e) => {
    triggerHaptic(e.currentTarget, 'medium');
    onClick?.(e);
  };
  
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={getSpringConfig('snappy')}
      onClick={handleClick}
      className="px-6 py-3 bg-blue-600 text-white rounded-lg"
    >
      {children}
    </motion.button>
  );
};
```

### 模態對話框

```jsx
import { motion, AnimatePresence } from 'framer-motion';
import { getSpringVariants } from '@/lib/spring-animation';

const Modal = ({ isOpen, onClose, children }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40"
          />
          
          {/* 對話框 */}
          <motion.div
            variants={getSpringVariants('slideUp', 'default')}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed inset-x-4 bottom-4 bg-white rounded-2xl p-6"
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
```

### 列表項動畫

```jsx
import { motion } from 'framer-motion';
import { getStaggerConfig, getSpringVariants } from '@/lib/spring-animation';

const List = ({ items }) => {
  return (
    <motion.div
      variants={{
        animate: {
          transition: getStaggerConfig('default', 0.05)
        }
      }}
      initial="initial"
      animate="animate"
    >
      {items.map((item, i) => (
        <motion.div
          key={item.id}
          variants={getSpringVariants('slideUp', 'default')}
          className="p-4 bg-white rounded-lg shadow-md mb-4"
        >
          {item.content}
        </motion.div>
      ))}
    </motion.div>
  );
};
```

### 成功反饋

```jsx
import { motion } from 'framer-motion';
import { getSpringVariants, triggerHaptic } from '@/lib/spring-animation';

const SuccessMessage = ({ message }) => {
  const ref = useRef(null);
  
  useEffect(() => {
    if (ref.current) {
      triggerHaptic(ref.current, 'success');
    }
  }, []);
  
  return (
    <motion.div
      ref={ref}
      variants={getSpringVariants('bounce', 'bouncy')}
      initial="initial"
      animate="animate"
      className="bg-green-500 text-white p-4 rounded-lg"
    >
      ✓ {message}
    </motion.div>
  );
};
```

### 錯誤提示

```jsx
import { motion } from 'framer-motion';
import { getSpringVariants, triggerHaptic } from '@/lib/spring-animation';

const ErrorMessage = ({ message }) => {
  const ref = useRef(null);
  
  useEffect(() => {
    if (ref.current) {
      triggerHaptic(ref.current, 'error');
    }
  }, []);
  
  return (
    <motion.div
      ref={ref}
      variants={getSpringVariants('shake', 'wobbly')}
      initial="initial"
      animate="animate"
      className="bg-red-500 text-white p-4 rounded-lg"
    >
      ✗ {message}
    </motion.div>
  );
};
```

## 可訪問性

### 尊重用戶偏好

系統自動檢測 `prefers-reduced-motion` 並禁用所有動畫：

```javascript
// 自動處理
if (prefersReducedMotion()) {
  return { duration: 0 };
}
```

### CSS 支持

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 最佳實踐

### 1. 選擇合適的預設

```javascript
// ✅ 好 - 根據場景選擇
<motion.button transition={getSpringConfig('snappy')}>
  快速反饋
</motion.button>

<motion.div transition={getSpringConfig('smooth')}>
  大型元素
</motion.div>

// ❌ 不好 - 所有地方都用同一個
<motion.div transition={getSpringConfig('bouncy')}>
  所有內容
</motion.div>
```

### 2. 適度使用觸覺反饋

```javascript
// ✅ 好 - 重要操作使用
<button onClick={() => triggerHaptic(el, 'medium')}>
  確認
</button>

// ❌ 不好 - 過度使用
<div onMouseMove={() => triggerHaptic(el, 'light')}>
  內容
</div>
```

### 3. 監控性能

```javascript
// ✅ 好 - 定期檢查
useEffect(() => {
  const interval = setInterval(() => {
    const metrics = getAnimationMetrics();
    if (metrics.averageFPS < 55) {
      console.warn('Animation performance degraded');
    }
  }, 5000);
  
  return () => clearInterval(interval);
}, []);
```

### 4. 響應用戶上下文

```javascript
// ✅ 好 - 自動適應
const context = getUserContext();
const animation = getContextualAnimation('slideUp', context);

// ❌ 不好 - 忽略用戶環境
const animation = getSpringVariants('slideUp', 'bouncy');
```

## 測試檢查清單

- [ ] 所有動畫在 `prefers-reduced-motion` 下被禁用
- [ ] 觸覺反饋不會過度使用
- [ ] 動畫性能保持在 60 FPS
- [ ] 上下文感知動畫正常工作
- [ ] 連續動畫流暢無卡頓
- [ ] 移動設備上動畫流暢
- [ ] 低電量模式下動畫簡化

## 相關資源

- [Apple Human Interface Guidelines - Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- [Framer Motion - Spring Animations](https://www.framer.com/motion/transition/#spring)
- [iOS Design Patterns](https://developer.apple.com/design/human-interface-guidelines/patterns)
- [Web Animations Performance](https://web.dev/animations/)
