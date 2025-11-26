/* eslint-disable i18next/no-literal-string */
/* NOTE: This file is exempted from strict i18n checks to maintain PR scope.
 * i18n improvements will be addressed in a dedicated PR (see Issue #1328).
 * This aligns with local ESLint config which already exempts stories/tests.
 */

import type { Meta, StoryObj } from '@storybook/react';
import '../../materials.css';

const MaterialShowcase = ({ 
  materialClass, 
  title, 
  description 
}: { 
  materialClass: string; 
  title: string; 
  description: string;
}) => (
  <div className="relative h-64 rounded-xl overflow-hidden">
    {/* Background pattern */}
    <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500">
      <div className="absolute inset-0" style={{
        backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.05) 10px, rgba(255,255,255,.05) 20px)',
      }} />
    </div>
    
    {/* Material layer */}
    <div className={`${materialClass} absolute inset-0 flex items-center justify-center`}>
      <div className="text-center p-6">
        <h3 className="text-2xl font-bold mb-2">{title}</h3>
        <p className="text-neutral-600 dark:text-neutral-300">{description}</p>
      </div>
    </div>
  </div>
);

const meta: Meta<typeof MaterialShowcase> = {
  title: 'Design System/Material System',
  component: MaterialShowcase,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'iOS-style material system with frosted glass effects. Based on Apple Human Interface Guidelines.',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof MaterialShowcase>;

export const UltraThin: Story = {
  args: {
    materialClass: 'material-ultra-thin',
    title: 'Ultra Thin',
    description: 'Lightest blur effect - 10px blur, 50% opacity',
  },
};

export const Thin: Story = {
  args: {
    materialClass: 'material-thin',
    title: 'Thin',
    description: 'Light blur effect - 15px blur, 60% opacity',
  },
};

export const Regular: Story = {
  args: {
    materialClass: 'material-regular',
    title: 'Regular',
    description: 'Standard blur effect - 20px blur, 70% opacity',
  },
};

export const Thick: Story = {
  args: {
    materialClass: 'material-thick',
    title: 'Thick',
    description: 'Heavy blur effect - 30px blur, 80% opacity',
  },
};

export const Chrome: Story = {
  args: {
    materialClass: 'material-chrome',
    title: 'Chrome',
    description: 'Strongest blur effect - 40px blur, 90% opacity',
  },
};

export const AllMaterials: Story = {
  render: () => (
    <div className="space-y-4">
      <MaterialShowcase 
        materialClass="material-ultra-thin" 
        title="Ultra Thin" 
        description="10px blur, 50% opacity" 
      />
      <MaterialShowcase 
        materialClass="material-thin" 
        title="Thin" 
        description="15px blur, 60% opacity" 
      />
      <MaterialShowcase 
        materialClass="material-regular" 
        title="Regular" 
        description="20px blur, 70% opacity" 
      />
      <MaterialShowcase 
        materialClass="material-thick" 
        title="Thick" 
        description="30px blur, 80% opacity" 
      />
      <MaterialShowcase 
        materialClass="material-chrome" 
        title="Chrome" 
        description="40px blur, 90% opacity" 
      />
    </div>
  ),
};

export const MaterialCard: Story = {
  render: () => (
    <div className="relative h-96 rounded-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500" />
      
      <div className="absolute inset-0 flex items-center justify-center p-8">
        <div className="material-card p-6 max-w-md">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">總收入</h3>
            <svg className="w-6 h-6 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className="text-3xl font-bold mb-2">$12,345</p>
          <p className="text-sm text-neutral-500">+12.5% 較上月</p>
        </div>
      </div>
    </div>
  ),
};

export const MaterialNavbar: Story = {
  render: () => (
    <div className="relative h-96 rounded-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500">
        <div className="absolute inset-0" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.05) 10px, rgba(255,255,255,.05) 20px)',
        }} />
      </div>
      
      <nav className="material-navbar relative">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <h1 className="text-xl font-bold">MorningAI</h1>
            <nav className="flex gap-6">
              <a href="#" className="text-neutral-700 hover:text-primary-600">Dashboard</a>
              <a href="#" className="text-neutral-700 hover:text-primary-600">Analytics</a>
              <a href="#" className="text-neutral-700 hover:text-primary-600">Settings</a>
            </nav>
          </div>
          <button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
            升級 Pro
          </button>
        </div>
      </nav>
    </div>
  ),
};

export const MaterialPopover: Story = {
  render: () => (
    <div className="relative h-96 rounded-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500" />
      
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="material-popover rounded-xl p-6 max-w-sm">
          <h3 className="text-lg font-semibold mb-2">通知設置</h3>
          <p className="text-neutral-600 dark:text-neutral-300 mb-4">
            選擇您想要接收的通知類型
          </p>
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded" />
              <span>電子郵件通知</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded" />
              <span>推送通知</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="rounded" />
              <span>SMS 通知</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  ),
};

export const MaterialWithShadows: Story = {
  render: () => (
    <div className="relative h-auto rounded-xl overflow-hidden p-8">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500" />
      
      <div className="relative grid grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5].map((level) => (
          <div key={level} className={`material-regular material-shadow-${level} p-6 rounded-xl`}>
            <h4 className="font-semibold mb-2">Shadow Level {level}</h4>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Material with shadow-{level}
            </p>
          </div>
        ))}
      </div>
    </div>
  ),
};

export const MaterialModal: Story = {
  render: () => (
    <div className="relative h-96 rounded-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500">
        <div className="absolute inset-0" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.05) 10px, rgba(255,255,255,.05) 20px)',
        }} />
      </div>
      
      {/* Overlay */}
      <div className="material-overlay absolute inset-0" />
      
      {/* Modal */}
      <div className="absolute inset-0 flex items-center justify-center p-8">
        <div className="material-thick material-shadow-5 rounded-2xl p-8 max-w-md relative">
          <h2 className="text-2xl font-bold mb-4">確認操作</h2>
          <p className="text-neutral-600 dark:text-neutral-300 mb-6">
            此操作無法撤銷，確定要繼續嗎？
          </p>
          <div className="flex gap-3">
            <button className="flex-1 bg-neutral-200 hover:bg-neutral-300 px-4 py-2 rounded-lg transition-colors">
              取消
            </button>
            <button className="flex-1 bg-error-600 hover:bg-error-700 text-white px-4 py-2 rounded-lg transition-colors">
              確認
            </button>
          </div>
        </div>
      </div>
    </div>
  ),
};

export const DarkMode: Story = {
  render: () => (
    <div className="dark">
      <div className="relative h-auto rounded-xl overflow-hidden p-8 bg-neutral-900">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-700 to-pink-700" />
        
        <div className="relative space-y-4">
          <MaterialShowcase 
            materialClass="material-ultra-thin" 
            title="Ultra Thin (Dark)" 
            description="Dark mode material" 
          />
          <MaterialShowcase 
            materialClass="material-regular" 
            title="Regular (Dark)" 
            description="Dark mode material" 
          />
          <MaterialShowcase 
            materialClass="material-chrome" 
            title="Chrome (Dark)" 
            description="Dark mode material" 
          />
        </div>
      </div>
    </div>
  ),
};

export const BackdropUtilities: Story = {
  render: () => (
    <div className="relative h-auto rounded-xl overflow-hidden p-8">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500" />
      
      <div className="relative grid grid-cols-2 gap-6">
        <div className="backdrop-blur-sm bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-sm</h4>
          <p className="text-sm text-neutral-600">10px blur</p>
        </div>
        <div className="backdrop-blur-md bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-md</h4>
          <p className="text-sm text-neutral-600">20px blur</p>
        </div>
        <div className="backdrop-blur-lg bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-lg</h4>
          <p className="text-sm text-neutral-600">30px blur</p>
        </div>
        <div className="backdrop-blur-xl bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-xl</h4>
          <p className="text-sm text-neutral-600">40px blur</p>
        </div>
        <div className="backdrop-glass bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-glass</h4>
          <p className="text-sm text-neutral-600">blur + saturate</p>
        </div>
        <div className="backdrop-glass-vibrant bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-glass-vibrant</h4>
          <p className="text-sm text-neutral-600">blur + saturate + brightness</p>
        </div>
      </div>
    </div>
  ),
};

export const DashboardExample: Story = {
  render: () => (
    <div className="relative h-auto rounded-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500" />
      
      <div className="relative p-8 space-y-6">
        {/* Navbar */}
        <nav className="material-navbar rounded-xl">
          <div className="px-4 py-3 flex items-center justify-between">
            <h1 className="text-xl font-bold">Dashboard</h1>
            <div className="flex gap-2">
              <button className="px-3 py-1 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700">
                通知
              </button>
              <button className="px-3 py-1 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700">
                設置
              </button>
            </div>
          </div>
        </nav>
        
        {/* Cards Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="material-card material-shadow-3 p-4">
            <h3 className="text-sm font-semibold text-neutral-600 mb-1">總用戶</h3>
            <p className="text-2xl font-bold">1,234</p>
            <p className="text-xs text-success-600 mt-1">+5.2%</p>
          </div>
          <div className="material-card material-shadow-3 p-4">
            <h3 className="text-sm font-semibold text-neutral-600 mb-1">活躍用戶</h3>
            <p className="text-2xl font-bold">856</p>
            <p className="text-xs text-success-600 mt-1">+12.8%</p>
          </div>
          <div className="material-card material-shadow-3 p-4">
            <h3 className="text-sm font-semibold text-neutral-600 mb-1">轉換率</h3>
            <p className="text-2xl font-bold">3.2%</p>
            <p className="text-xs text-error-600 mt-1">-0.5%</p>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="material-regular material-shadow-4 rounded-xl p-6">
          <h2 className="text-lg font-bold mb-4">最近活動</h2>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800">
                <div className="w-10 h-10 rounded-full bg-primary-500" />
                <div className="flex-1">
                  <p className="font-medium">用戶操作 {i}</p>
                  <p className="text-sm text-neutral-500">2 分鐘前</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * Emotional Color System
 * 
 * Apple-inspired emotional color palette for status indicators and state communication.
 * Each color conveys specific emotional meaning and follows WCAG AA accessibility standards.
 */
export const EmotionalColors: Story = {
  render: () => (
    <div className="p-8 space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-2">情感化色彩系統</h2>
        <p className="text-neutral-600 mb-6">
          基於 Apple 設計語言的情感色彩系統，每種顏色傳達特定的情感意義，所有顏色符合 WCAG AA 無障礙標準（對比度 ≥ 4.5:1）
        </p>
      </div>

      {/* Color Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Calm - Blue */}
        <div className="space-y-3">
          <div className="bg-calm h-24 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">Calm</span>
          </div>
          <div className="bg-calm-10 p-4 rounded-lg border border-calm">
            <h3 className="font-semibold text-calm mb-1">平靜 / 穩定</h3>
            <p className="text-sm text-neutral-600">用於正常狀態、資訊提示</p>
            <div className="mt-2 text-xs text-calm">
              <code>bg-calm</code> · <code>text-calm</code> · <code>bg-calm-10</code>
            </div>
          </div>
        </div>

        {/* Growth - Green */}
        <div className="space-y-3">
          <div className="bg-growth h-24 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">Growth</span>
          </div>
          <div className="bg-growth-10 p-4 rounded-lg border border-growth">
            <h3 className="font-semibold text-growth mb-1">成長 / 成功</h3>
            <p className="text-sm text-neutral-600">用於成功狀態、完成操作</p>
            <div className="mt-2 text-xs text-growth">
              <code>bg-growth</code> · <code>text-growth</code> · <code>bg-growth-10</code>
            </div>
          </div>
        </div>

        {/* Joy - Orange */}
        <div className="space-y-3">
          <div className="bg-joy h-24 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">Joy</span>
          </div>
          <div className="bg-joy-10 p-4 rounded-lg border border-joy">
            <h3 className="font-semibold text-joy mb-1">警示 / 注意</h3>
            <p className="text-sm text-neutral-600">用於警告狀態、需要關注</p>
            <div className="mt-2 text-xs text-joy">
              <code>bg-joy</code> · <code>text-joy</code> · <code>bg-joy-10</code>
            </div>
          </div>
        </div>

        {/* Energy - Red */}
        <div className="space-y-3">
          <div className="bg-energy h-24 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">Energy</span>
          </div>
          <div className="bg-energy-10 p-4 rounded-lg border border-energy">
            <h3 className="font-semibold text-energy mb-1">錯誤 / 失敗</h3>
            <p className="text-sm text-neutral-600">用於錯誤狀態、失敗操作</p>
            <div className="mt-2 text-xs text-energy">
              <code>bg-energy</code> · <code>text-energy</code> · <code>bg-energy-10</code>
            </div>
          </div>
        </div>

        {/* Wisdom - Purple */}
        <div className="space-y-3">
          <div className="bg-wisdom h-24 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">Wisdom</span>
          </div>
          <div className="bg-wisdom-10 p-4 rounded-lg border border-wisdom">
            <h3 className="font-semibold text-wisdom mb-1">洞察 / 智慧</h3>
            <p className="text-sm text-neutral-600">用於分析數據、智能功能</p>
            <div className="mt-2 text-xs text-wisdom">
              <code>bg-wisdom</code> · <code>text-wisdom</code> · <code>bg-wisdom-10</code>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Examples */}
      <div className="mt-12">
        <h3 className="text-xl font-bold mb-4">使用範例</h3>
        <div className="space-y-4">
          {/* Status Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="material-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-calm-10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-calm" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <span className="text-sm font-medium">正常</span>
              </div>
              <p className="text-2xl font-bold text-calm">128</p>
            </div>

            <div className="material-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-growth-10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-growth" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-sm font-medium">成功</span>
              </div>
              <p className="text-2xl font-bold text-growth">95</p>
            </div>

            <div className="material-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-joy-10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-joy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <span className="text-sm font-medium">警告</span>
              </div>
              <p className="text-2xl font-bold text-joy">12</p>
            </div>

            <div className="material-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-energy-10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-energy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <span className="text-sm font-medium">錯誤</span>
              </div>
              <p className="text-2xl font-bold text-energy">3</p>
            </div>
          </div>

          {/* Status Mapping Example */}
          <div className="material-card p-6">
            <h4 className="font-semibold mb-4">狀態映射規則</h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-calm-10 text-calm font-medium">default</span>
                <span className="text-neutral-600">→ calm (藍) - 正常/穩定</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-growth-10 text-growth font-medium">executed</span>
                <span className="text-neutral-600">→ growth (綠) - 成功/完成</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-joy-10 text-joy font-medium">pending</span>
                <span className="text-neutral-600">→ joy (橙) - 警告/等待中</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-energy-10 text-energy font-medium">failed</span>
                <span className="text-neutral-600">→ energy (紅) - 錯誤/失敗</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-wisdom-10 text-wisdom font-medium">analysis</span>
                <span className="text-neutral-600">→ wisdom (紫) - 洞察/智慧</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Accessibility Note */}
      <div className="material-card p-6 bg-neutral-50">
        <h4 className="font-semibold mb-2 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          無障礙標準
        </h4>
        <p className="text-sm text-neutral-600">
          所有情感色彩都符合 WCAG 2.1 AA 標準，對比度 ≥ 4.5:1，確保色盲用戶和低視力用戶都能清晰辨識。
        </p>
      </div>
    </div>
  ),
};
