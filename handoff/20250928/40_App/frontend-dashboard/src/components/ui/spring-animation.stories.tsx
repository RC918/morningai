import type { Meta, StoryObj } from '@storybook/react';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useRef, useEffect } from 'react';
import {
  springPresets,
  getSpringConfig,
  getSpringVariants,
  triggerHaptic,
  getHapticAnimation,
  getContextualAnimation,
  getUserContext,
  createAnimationSequence,
  getStaggerConfig,
  getAnimationMetrics,
  trackAnimation
} from '../../lib/spring-animation';
import '../../styles/spring-animations.css';

const meta: Meta = {
  title: 'Design System/Spring Animation System',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Apple-level spring animation system with haptic feedback simulation and contextual animations.'
      }
    }
  }
};

export default meta;
type Story = StoryObj;


export const SpringPresets: Story = {
  render: () => {
    const [activePreset, setActivePreset] = useState<string | null>(null);
    
    const presets = [
      { name: 'gentle', label: 'Gentle', description: '溫和的彈性動畫', color: 'bg-blue-100 dark:bg-blue-900' },
      { name: 'default', label: 'Default', description: '標準 iOS 動畫（推薦）', color: 'bg-green-100 dark:bg-green-900' },
      { name: 'bouncy', label: 'Bouncy', description: '活潑、有趣的彈性', color: 'bg-purple-100 dark:bg-purple-900' },
      { name: 'snappy', label: 'Snappy', description: '快速、響應式', color: 'bg-orange-100 dark:bg-orange-900' },
      { name: 'smooth', label: 'Smooth', description: '優雅、流暢', color: 'bg-pink-100 dark:bg-pink-900' },
      { name: 'wobbly', label: 'Wobbly', description: '誇張的彈性效果', color: 'bg-yellow-100 dark:bg-yellow-900' }
    ];
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">6 種彈性預設</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊查看不同彈性動畫的效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {presets.map((preset) => (
            <motion.button
              key={preset.name}
              onClick={() => setActivePreset(preset.name)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={getSpringConfig(preset.name as keyof typeof springPresets)}
              className={`${preset.color} p-6 rounded-xl shadow-md text-left relative overflow-hidden`}
            >
              <div className="relative z-10">
                <h3 className="text-lg font-semibold mb-1">{preset.label}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">{preset.description}</p>
              </div>
              
              <AnimatePresence>
                {activePreset === preset.name && (
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    transition={getSpringConfig(preset.name as keyof typeof springPresets)}
                    className="absolute inset-0 bg-white/20 dark:bg-black/20"
                  />
                )}
              </AnimatePresence>
            </motion.button>
          ))}
        </div>
        
        {/* 技術參數展示 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">技術參數</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(springPresets).map(([name, config]) => (
              <div key={name} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="font-semibold capitalize mb-2">{name}</h4>
                <div className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                  <div>Stiffness: {config.stiffness}</div>
                  <div>Damping: {config.damping}</div>
                  <div>Mass: {config.mass}</div>
                  <div>Duration: {config.duration}s</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
};


export const AnimationVariants: Story = {
  render: () => {
    const [activeVariant, setActiveVariant] = useState<string | null>(null);
    
    const variants = [
      { name: 'fade', label: 'Fade', description: '淡入淡出' },
      { name: 'scale', label: 'Scale', description: '縮放' },
      { name: 'pop', label: 'Pop', description: '彈出' },
      { name: 'bounce', label: 'Bounce', description: '彈跳' },
      { name: 'slideUp', label: 'Slide Up', description: '向上滑動' },
      { name: 'slideDown', label: 'Slide Down', description: '向下滑動' },
      { name: 'slideLeft', label: 'Slide Left', description: '向左滑動' },
      { name: 'slideRight', label: 'Slide Right', description: '向右滑動' },
      { name: 'shake', label: 'Shake', description: '搖晃' },
      { name: 'pulse', label: 'Pulse', description: '脈衝' }
    ];
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">動畫變體</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕查看不同的動畫效果</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {variants.map((variant) => (
            <button
              key={variant.name}
              onClick={() => setActiveVariant(variant.name)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {variant.label}
            </button>
          ))}
        </div>
        
        {/* 動畫展示區域 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[300px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {activeVariant && (
              <motion.div
                key={activeVariant}
                variants={getSpringVariants(activeVariant, 'default')}
                initial="initial"
                animate="animate"
                exit="exit"
                className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl"
              >
                <h3 className="text-2xl font-bold mb-2">
                  {variants.find(v => v.name === activeVariant)?.label}
                </h3>
                <p className="text-blue-100">
                  {variants.find(v => v.name === activeVariant)?.description}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  }
};


export const HapticFeedback: Story = {
  render: () => {
    const haptics = [
      { type: 'light', label: 'Light', description: '輕微', color: 'bg-gray-500' },
      { type: 'medium', label: 'Medium', description: '中等', color: 'bg-blue-500' },
      { type: 'heavy', label: 'Heavy', description: '重度', color: 'bg-purple-500' },
      { type: 'success', label: 'Success', description: '成功', color: 'bg-green-500' },
      { type: 'warning', label: 'Warning', description: '警告', color: 'bg-yellow-500' },
      { type: 'error', label: 'Error', description: '錯誤', color: 'bg-red-500' },
      { type: 'selection', label: 'Selection', description: '選擇', color: 'bg-indigo-500' }
    ];
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">觸覺反饋模擬</h2>
          <p className="text-gray-600 dark:text-gray-400">點擊按鈕體驗不同強度的觸覺反饋</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {haptics.map((haptic) => (
            <motion.button
              key={haptic.type}
              onClick={(e) => triggerHaptic(e.currentTarget, haptic.type as any)}
              whileHover={{ scale: 1.05 }}
              whileTap={getHapticAnimation(haptic.type as any)}
              className={`${haptic.color} text-white p-6 rounded-xl shadow-md`}
            >
              <h3 className="text-lg font-semibold mb-1">{haptic.label}</h3>
              <p className="text-sm opacity-90">{haptic.description}</p>
            </motion.button>
          ))}
        </div>
        
        {/* CSS 類名範例 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名範例</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {haptics.map((haptic) => (
              <button
                key={`css-${haptic.type}`}
                className={`haptic-${haptic.type} ${haptic.color} text-white px-4 py-3 rounded-lg`}
              >
                .haptic-{haptic.type}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }
};


export const ButtonInteractions: Story = {
  render: () => {
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">按鈕互動</h2>
          <p className="text-gray-600 dark:text-gray-400">Apple 風格的按鈕按壓效果</p>
        </div>
        
        {/* Framer Motion 按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">Framer Motion 按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={getSpringConfig('snappy')}
              onClick={(e) => triggerHaptic(e.currentTarget, 'medium')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md"
            >
              Primary Button
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={getSpringConfig('bouncy')}
              onClick={(e) => triggerHaptic(e.currentTarget, 'success')}
              className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md"
            >
              Success Button
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={getSpringConfig('default')}
              onClick={(e) => triggerHaptic(e.currentTarget, 'warning')}
              className="px-6 py-3 bg-yellow-600 text-white rounded-lg shadow-md"
            >
              Warning Button
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={getSpringConfig('wobbly')}
              onClick={(e) => triggerHaptic(e.currentTarget, 'error')}
              className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md"
            >
              Error Button
            </motion.button>
          </div>
        </div>
        
        {/* CSS 類名按鈕 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 類名按鈕</h3>
          <div className="flex flex-wrap gap-4">
            <button className="btn-spring-press px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md">
              Standard Press
            </button>
            
            <button className="btn-spring-press-heavy px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md">
              Heavy Press
            </button>
            
            <button className="hover-lift px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md">
              Hover Lift
            </button>
            
            <button className="hover-scale px-6 py-3 bg-pink-600 text-white rounded-lg shadow-md">
              Hover Scale
            </button>
          </div>
        </div>
      </div>
    );
  }
};


export const ModalAnimations: Story = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">模態對話框動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">iOS 風格的 Sheet 動畫</p>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={getSpringConfig('snappy')}
          onClick={() => setIsOpen(true)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md"
        >
          打開 Modal
        </motion.button>
        
        <AnimatePresence>
          {isOpen && (
            <>
              {/* 背景遮罩 */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsOpen(false)}
                className="fixed inset-0 bg-black/40 z-40"
              />
              
              {/* 對話框 */}
              <motion.div
                variants={getSpringVariants('slideUp', 'default')}
                initial="initial"
                animate="animate"
                exit="exit"
                className="fixed inset-x-4 bottom-4 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-2xl z-50 max-w-md mx-auto"
              >
                <h3 className="text-xl font-bold mb-4">iOS 風格 Sheet</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  這是一個使用彈性動畫的模態對話框，模擬 iOS 的 Sheet 效果。
                </p>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  transition={getSpringConfig('snappy')}
                  onClick={() => setIsOpen(false)}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md"
                >
                  關閉
                </motion.button>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    );
  }
};


export const ListStaggerAnimation: Story = {
  render: () => {
    const [show, setShow] = useState(true);
    
    const items = [
      { id: 1, title: '項目 1', description: '這是第一個項目' },
      { id: 2, title: '項目 2', description: '這是第二個項目' },
      { id: 3, title: '項目 3', description: '這是第三個項目' },
      { id: 4, title: '項目 4', description: '這是第四個項目' },
      { id: 5, title: '項目 5', description: '這是第五個項目' }
    ];
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">列表交錯動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">子元素依序出現的動畫效果</p>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={getSpringConfig('snappy')}
          onClick={() => setShow(!show)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md"
        >
          {show ? '隱藏' : '顯示'}列表
        </motion.button>
        
        <AnimatePresence>
          {show && (
            <motion.div
              variants={{
                animate: {
                  transition: getStaggerConfig('default', 0.08)
                }
              }}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-4"
            >
              {items.map((item) => (
                <motion.div
                  key={item.id}
                  variants={getSpringVariants('slideUp', 'default')}
                  className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md"
                >
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{item.description}</p>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* CSS 交錯動畫 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">CSS 交錯動畫</h3>
          <div className="stagger-children space-y-4">
            {items.map((item) => (
              <div key={item.id} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold">{item.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-300">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
};


export const FeedbackAnimations: Story = {
  render: () => {
    const [showSuccess, setShowSuccess] = useState(false);
    const [showError, setShowError] = useState(false);
    const successRef = useRef<HTMLDivElement>(null);
    const errorRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
      if (showSuccess && successRef.current) {
        triggerHaptic(successRef.current, 'success');
      }
    }, [showSuccess]);
    
    useEffect(() => {
      if (showError && errorRef.current) {
        triggerHaptic(errorRef.current, 'error');
      }
    }, [showError]);
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">成功/錯誤反饋</h2>
          <p className="text-gray-600 dark:text-gray-400">帶有觸覺反饋的狀態提示</p>
        </div>
        
        <div className="flex gap-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            transition={getSpringConfig('snappy')}
            onClick={() => {
              setShowSuccess(true);
              setTimeout(() => setShowSuccess(false), 3000);
            }}
            className="px-6 py-3 bg-green-600 text-white rounded-lg shadow-md"
          >
            顯示成功
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            transition={getSpringConfig('snappy')}
            onClick={() => {
              setShowError(true);
              setTimeout(() => setShowError(false), 3000);
            }}
            className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-md"
          >
            顯示錯誤
          </motion.button>
        </div>
        
        <div className="space-y-4">
          <AnimatePresence>
            {showSuccess && (
              <motion.div
                ref={successRef}
                variants={getSpringVariants('bounce', 'bouncy')}
                initial="initial"
                animate="animate"
                exit="exit"
                className="bg-green-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3"
              >
                <div className="text-2xl">✓</div>
                <div>
                  <h3 className="font-semibold">操作成功！</h3>
                  <p className="text-sm opacity-90">您的更改已保存</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          <AnimatePresence>
            {showError && (
              <motion.div
                ref={errorRef}
                variants={getSpringVariants('shake', 'wobbly')}
                initial="initial"
                animate="animate"
                exit="exit"
                className="bg-red-500 text-white p-6 rounded-xl shadow-lg flex items-center gap-3"
              >
                <div className="text-2xl">✗</div>
                <div>
                  <h3 className="font-semibold">操作失敗！</h3>
                  <p className="text-sm opacity-90">請稍後再試</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  }
};


export const ContextualAnimations: Story = {
  render: () => {
    const [context, setContext] = useState(getUserContext());
    const [animationKey, setAnimationKey] = useState(0);
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">上下文感知動畫</h2>
          <p className="text-gray-600 dark:text-gray-400">根據用戶環境自動調整動畫</p>
        </div>
        
        {/* 當前上下文 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">當前上下文</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">設備類型：</span>
              <span className="font-semibold ml-2">{context.isMobile ? '移動設備' : '桌面設備'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">低電量模式：</span>
              <span className="font-semibold ml-2">{context.isLowPower ? '是' : '否'}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">網絡速度：</span>
              <span className="font-semibold ml-2">{context.connectionSpeed}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">用戶偏好：</span>
              <span className="font-semibold ml-2">{context.userPreference}</span>
            </div>
          </div>
        </div>
        
        {/* 動畫展示 */}
        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md min-h-[200px] flex items-center justify-center">
          <motion.div
            key={animationKey}
            {...getContextualAnimation('slideUp', context)}
            initial="initial"
            animate="animate"
            className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-2xl shadow-xl"
          >
            <h3 className="text-2xl font-bold">上下文感知動畫</h3>
            <p className="text-blue-100 mt-2">根據您的環境自動調整</p>
          </motion.div>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={getSpringConfig('snappy')}
          onClick={() => setAnimationKey(k => k + 1)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md"
        >
          重新播放動畫
        </motion.button>
      </div>
    );
  }
};


export const PerformanceMonitoring: Story = {
  render: () => {
    const [metrics, setMetrics] = useState(getAnimationMetrics());
    const [isAnimating, setIsAnimating] = useState(false);
    
    const startAnimation = () => {
      setIsAnimating(true);
      trackAnimation('demo-animation');
      
      setTimeout(() => {
        setIsAnimating(false);
        setMetrics(getAnimationMetrics());
      }, 1000);
    };
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">性能監控</h2>
          <p className="text-gray-600 dark:text-gray-400">追蹤動畫性能指標</p>
        </div>
        
        {/* 性能指標 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-blue-600">{metrics.totalAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">總動畫數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-green-600">{metrics.activeAnimations}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">活躍動畫</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-yellow-600">{metrics.droppedFrames}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">掉幀數</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <div className="text-3xl font-bold text-purple-600">{metrics.averageFPS.toFixed(1)}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">平均 FPS</div>
          </div>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={getSpringConfig('snappy')}
          onClick={startAnimation}
          disabled={isAnimating}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md disabled:opacity-50"
        >
          {isAnimating ? '動畫中...' : '開始動畫'}
        </motion.button>
        
        {/* 性能建議 */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <h3 className="text-lg font-semibold mb-4">性能建議</h3>
          <div className="space-y-2 text-sm">
            {metrics.averageFPS < 55 && (
              <div className="text-red-600 dark:text-red-400">
                ⚠️ 平均 FPS 低於 55，建議降級到更簡單的動畫
              </div>
            )}
            {metrics.activeAnimations > 5 && (
              <div className="text-yellow-600 dark:text-yellow-400">
                ⚠️ 同時活躍動畫過多，可能影響性能
              </div>
            )}
            {metrics.droppedFrames > 10 && (
              <div className="text-orange-600 dark:text-orange-400">
                ⚠️ 掉幀數較多，建議優化動畫
              </div>
            )}
            {metrics.averageFPS >= 55 && metrics.activeAnimations <= 5 && metrics.droppedFrames <= 10 && (
              <div className="text-green-600 dark:text-green-400">
                ✓ 性能良好，動畫流暢
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
};


export const CompleteDemo: Story = {
  render: () => {
    const [isCardOpen, setIsCardOpen] = useState(false);
    
    return (
      <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div>
          <h2 className="text-2xl font-bold mb-2">完整演示</h2>
          <p className="text-gray-600 dark:text-gray-400">綜合展示彈性動畫系統的各種功能</p>
        </div>
        
        {/* 互動卡片 */}
        <motion.div
          layout
          onClick={() => setIsCardOpen(!isCardOpen)}
          className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md cursor-pointer"
          whileHover={{ scale: 1.02 }}
          transition={getSpringConfig('default')}
        >
          <motion.h3 layout="position" className="text-xl font-bold mb-2">
            互動卡片
          </motion.h3>
          <motion.p layout="position" className="text-gray-600 dark:text-gray-400">
            點擊展開查看更多內容
          </motion.p>
          
          <AnimatePresence>
            {isCardOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={getSpringConfig('default')}
                className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
              >
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  這是展開的內容區域，使用了彈性動畫來創造流暢的展開效果。
                </p>
                <div className="flex gap-2">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    transition={getSpringConfig('snappy')}
                    onClick={(e) => {
                      e.stopPropagation();
                      triggerHaptic(e.currentTarget, 'success');
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm"
                  >
                    確認
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    transition={getSpringConfig('snappy')}
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsCardOpen(false);
                    }}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm"
                  >
                    取消
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
        
        {/* 功能按鈕組 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Primary', 'Success', 'Warning', 'Error'].map((type, i) => (
            <motion.button
              key={type}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={getSpringConfig('snappy')}
              onClick={(e) => {
                const hapticType = ['medium', 'success', 'warning', 'error'][i];
                triggerHaptic(e.currentTarget, hapticType as any);
              }}
              className={`px-6 py-3 text-white rounded-lg shadow-md ${
                ['bg-blue-600', 'bg-green-600', 'bg-yellow-600', 'bg-red-600'][i]
              }`}
            >
              {type}
            </motion.button>
          ))}
        </div>
      </div>
    );
  }
};
