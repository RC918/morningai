import type { Meta, StoryObj } from '@storybook/react';

const ShadowShowcase = ({ 
  shadowClass, 
  title, 
  description 
}: { 
  shadowClass: string; 
  title: string; 
  description: string;
}) => (
  <div className={`${shadowClass} bg-white dark:bg-gray-800 p-6 rounded-xl`}>
    <h3 className="text-lg font-bold mb-2">{title}</h3>
    <p className="text-gray-600 dark:text-gray-300 text-sm">{description}</p>
  </div>
);

const meta: Meta<typeof ShadowShowcase> = {
  title: 'Design System/Shadow System',
  component: ShadowShowcase,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'iOS-style 5-level shadow system for creating depth and elevation. Based on Apple Human Interface Guidelines.',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ShadowShowcase>;

export const Level1SubtleLift: Story = {
  args: {
    shadowClass: 'shadow-sm',
    title: 'Level 1: Subtle Lift',
    description: '0 1px 2px - 最輕微的提升效果',
  },
};

export const Level2LightElevation: Story = {
  args: {
    shadowClass: 'shadow-md',
    title: 'Level 2: Light Elevation',
    description: '0 2px 4px - 輕度提升效果',
  },
};

export const Level3MediumElevation: Story = {
  args: {
    shadowClass: 'shadow-lg',
    title: 'Level 3: Medium Elevation',
    description: '0 4px 8px - 標準提升效果（推薦）',
  },
};

export const Level4HighElevation: Story = {
  args: {
    shadowClass: 'shadow-xl',
    title: 'Level 4: High Elevation',
    description: '0 8px 16px - 高度提升效果',
  },
};

export const Level5MaximumElevation: Story = {
  args: {
    shadowClass: 'shadow-2xl',
    title: 'Level 5: Maximum Elevation',
    description: '0 16px 32px - 最大提升效果',
  },
};

export const AllShadows: Story = {
  render: () => (
    <div className="space-y-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <ShadowShowcase 
        shadowClass="shadow-sm" 
        title="Level 1: Subtle Lift" 
        description="0 1px 2px - 輸入框、列表項" 
      />
      <ShadowShowcase 
        shadowClass="shadow-md" 
        title="Level 2: Light Elevation" 
        description="0 2px 4px - 次要卡片、下拉菜單" 
      />
      <ShadowShowcase 
        shadowClass="shadow-lg" 
        title="Level 3: Medium Elevation" 
        description="0 4px 8px - 主要卡片、導航欄" 
      />
      <ShadowShowcase 
        shadowClass="shadow-xl" 
        title="Level 4: High Elevation" 
        description="0 8px 16px - 模態對話框、浮動按鈕" 
      />
      <ShadowShowcase 
        shadowClass="shadow-2xl" 
        title="Level 5: Maximum Elevation" 
        description="0 16px 32px - 全屏模態、拖拽元素" 
      />
    </div>
  ),
};

export const CardSystem: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      {/* 基礎卡片 */}
      <div className="shadow-md bg-white dark:bg-gray-800 p-4 rounded-lg">
        <h4 className="font-semibold mb-2">基礎卡片</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">shadow-md</p>
        <p className="text-2xl font-bold mt-2">1,234</p>
      </div>
      
      {/* 重要卡片 */}
      <div className="shadow-lg bg-white dark:bg-gray-800 p-6 rounded-xl">
        <h4 className="font-semibold mb-2">重要卡片</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">shadow-lg</p>
        <p className="text-2xl font-bold mt-2">5,678</p>
      </div>
      
      {/* 浮動卡片 */}
      <div className="shadow-xl bg-white dark:bg-gray-800 p-8 rounded-2xl">
        <h4 className="font-semibold mb-2">浮動卡片</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">shadow-xl</p>
        <p className="text-2xl font-bold mt-2">9,012</p>
      </div>
    </div>
  ),
};

export const ButtonSystem: Story = {
  render: () => (
    <div className="space-y-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div className="space-y-3">
        <h4 className="font-semibold">主要按鈕</h4>
        <button className="bg-blue-600 text-white shadow-md hover:shadow-lg active:shadow-sm px-6 py-3 rounded-lg transition-shadow">
          主要操作 (shadow-md → shadow-lg)
        </button>
      </div>
      
      <div className="space-y-3">
        <h4 className="font-semibold">次要按鈕</h4>
        <button className="bg-gray-200 dark:bg-gray-700 shadow-sm hover:shadow-md active:shadow-sm px-6 py-3 rounded-lg transition-shadow">
          次要操作 (shadow-sm → shadow-md)
        </button>
      </div>
      
      <div className="space-y-3">
        <h4 className="font-semibold">浮動操作按鈕 (FAB)</h4>
        <button className="w-14 h-14 bg-blue-600 text-white shadow-xl hover:shadow-2xl rounded-full transition-shadow text-2xl">
          +
        </button>
      </div>
    </div>
  ),
};

export const HoverEffects: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div className="shadow-sm hover:shadow-lg bg-white dark:bg-gray-800 p-6 rounded-xl transition-shadow cursor-pointer">
        <h4 className="font-semibold mb-2">Hover 提升</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          shadow-sm → shadow-lg
        </p>
      </div>
      
      <div className="shadow-md hover:shadow-xl bg-white dark:bg-gray-800 p-6 rounded-xl transition-shadow cursor-pointer">
        <h4 className="font-semibold mb-2">Hover 強化</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          shadow-md → shadow-xl
        </p>
      </div>
      
      <div className="shadow-lg hover:shadow-2xl bg-white dark:bg-gray-800 p-6 rounded-xl transition-shadow cursor-pointer">
        <h4 className="font-semibold mb-2">Hover 最大化</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          shadow-lg → shadow-2xl
        </p>
      </div>
      
      <div className="shadow-xl hover:shadow-lg bg-white dark:bg-gray-800 p-6 rounded-xl transition-shadow cursor-pointer">
        <h4 className="font-semibold mb-2">Hover 降低</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          shadow-xl → shadow-lg
        </p>
      </div>
    </div>
  ),
};

export const DarkMode: Story = {
  render: () => (
    <div className="dark">
      <div className="space-y-6 p-8 bg-gray-900 rounded-xl">
        <h3 className="text-white text-xl font-bold mb-4">深色模式陰影</h3>
        <div className="shadow-sm bg-gray-800 p-4 rounded-lg">
          <h4 className="text-white font-semibold">Level 1</h4>
          <p className="text-gray-400 text-sm">深色模式下的輕微陰影</p>
        </div>
        <div className="shadow-md bg-gray-800 p-4 rounded-lg">
          <h4 className="text-white font-semibold">Level 2</h4>
          <p className="text-gray-400 text-sm">深色模式下的輕度陰影</p>
        </div>
        <div className="shadow-lg bg-gray-800 p-6 rounded-xl">
          <h4 className="text-white font-semibold">Level 3</h4>
          <p className="text-gray-400 text-sm">深色模式下的標準陰影</p>
        </div>
        <div className="shadow-xl bg-gray-800 p-6 rounded-xl">
          <h4 className="text-white font-semibold">Level 4</h4>
          <p className="text-gray-400 text-sm">深色模式下的高度陰影</p>
        </div>
        <div className="shadow-2xl bg-gray-800 p-8 rounded-2xl">
          <h4 className="text-white font-semibold">Level 5</h4>
          <p className="text-gray-400 text-sm">深色模式下的最大陰影</p>
        </div>
      </div>
    </div>
  ),
};

export const ColoredShadows: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div 
        className="bg-orange-500 text-white p-6 rounded-xl"
        style={{ boxShadow: '0 4px 12px 0 rgba(255, 149, 0, 0.3)' }}
      >
        <h4 className="font-semibold mb-2">Joy - 橙色陰影</h4>
        <p className="text-sm opacity-90">溫暖、愉悅的氛圍</p>
      </div>
      
      <div 
        className="bg-blue-500 text-white p-6 rounded-xl"
        style={{ boxShadow: '0 4px 12px 0 rgba(90, 200, 250, 0.3)' }}
      >
        <h4 className="font-semibold mb-2">Calm - 藍色陰影</h4>
        <p className="text-sm opacity-90">平靜、專注的氛圍</p>
      </div>
      
      <div 
        className="bg-red-500 text-white p-6 rounded-xl"
        style={{ boxShadow: '0 4px 12px 0 rgba(255, 59, 48, 0.3)' }}
      >
        <h4 className="font-semibold mb-2">Energy - 紅色陰影</h4>
        <p className="text-sm opacity-90">活力、緊急的氛圍</p>
      </div>
      
      <div 
        className="bg-green-500 text-white p-6 rounded-xl"
        style={{ boxShadow: '0 4px 12px 0 rgba(52, 199, 89, 0.3)' }}
      >
        <h4 className="font-semibold mb-2">Growth - 綠色陰影</h4>
        <p className="text-sm opacity-90">成長、成功的氛圍</p>
      </div>
      
      <div 
        className="bg-purple-600 text-white p-6 rounded-xl"
        style={{ boxShadow: '0 4px 12px 0 rgba(88, 86, 214, 0.3)' }}
      >
        <h4 className="font-semibold mb-2">Wisdom - 紫色陰影</h4>
        <p className="text-sm opacity-90">智慧、洞察的氛圍</p>
      </div>
    </div>
  ),
};

export const InsetShadows: Story = {
  render: () => (
    <div className="space-y-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div>
        <h4 className="font-semibold mb-3">輸入框 - 內陰影</h4>
        <input 
          type="text"
          placeholder="聚焦查看效果"
          className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          style={{ boxShadow: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.06)' }}
        />
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">按下的按鈕 - 內陰影</h4>
        <button 
          className="px-6 py-3 bg-gray-200 dark:bg-gray-700 rounded-lg"
          style={{ boxShadow: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.06)' }}
        >
          按下狀態
        </button>
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">凹陷面板 - 內陰影</h4>
        <div 
          className="p-6 bg-gray-100 dark:bg-gray-800 rounded-xl"
          style={{ boxShadow: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.06)' }}
        >
          <p className="text-gray-600 dark:text-gray-300">凹陷效果的內容區域</p>
        </div>
      </div>
    </div>
  ),
};

export const ModalDialog: Story = {
  render: () => (
    <div className="relative h-96 bg-gray-100 dark:bg-gray-900 rounded-xl overflow-hidden">
      {/* 背景遮罩 */}
      <div className="absolute inset-0 bg-black/40" />
      
      {/* 對話框 */}
      <div className="absolute inset-0 flex items-center justify-center p-8">
        <div className="shadow-2xl bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md relative z-10">
          <h2 className="text-2xl font-bold mb-4">確認操作</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            此操作無法撤銷，確定要繼續嗎？
          </p>
          <div className="flex gap-3">
            <button className="flex-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-all">
              取消
            </button>
            <button className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg shadow-md hover:shadow-lg transition-all">
              確認
            </button>
          </div>
        </div>
      </div>
    </div>
  ),
};

export const Navbar: Story = {
  render: () => (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl overflow-hidden">
      <nav className="bg-white dark:bg-gray-800 shadow-md">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">MorningAI</h1>
            <div className="flex gap-6">
              <a href="#" className="text-gray-700 dark:text-gray-300 hover:text-blue-600">Dashboard</a>
              <a href="#" className="text-gray-700 dark:text-gray-300 hover:text-blue-600">Analytics</a>
              <a href="#" className="text-gray-700 dark:text-gray-300 hover:text-blue-600">Settings</a>
            </div>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              升級 Pro
            </button>
          </div>
        </div>
      </nav>
      
      <div className="p-8">
        <p className="text-gray-600 dark:text-gray-300">導航欄使用 shadow-md 創造分離感</p>
      </div>
    </div>
  ),
};

export const DropdownMenu: Story = {
  render: () => (
    <div className="relative h-96 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div className="relative inline-block">
        <button className="shadow-sm hover:shadow-md px-4 py-2 bg-white dark:bg-gray-800 rounded-lg transition-shadow">
          選單 ▼
        </button>
        
        <div className="absolute top-full mt-2 shadow-xl bg-white dark:bg-gray-800 rounded-lg py-2 min-w-[200px]">
          <a href="#" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">選項 1</a>
          <a href="#" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">選項 2</a>
          <a href="#" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">選項 3</a>
          <div className="border-t border-gray-200 dark:border-gray-700 my-2"></div>
          <a href="#" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-red-600">刪除</a>
        </div>
      </div>
    </div>
  ),
};

export const DashboardExample: Story = {
  render: () => (
    <div className="p-8 bg-gray-50 dark:bg-gray-900 rounded-xl space-y-6">
      {/* 導航欄 */}
      <nav className="bg-white dark:bg-gray-800 shadow-md rounded-xl px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Dashboard</h1>
          <div className="flex gap-2">
            <button className="px-3 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">通知</button>
            <button className="px-3 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">設置</button>
          </div>
        </div>
      </nav>
      
      {/* 統計卡片 */}
      <div className="grid grid-cols-3 gap-4">
        <div className="shadow-md hover:shadow-lg bg-white dark:bg-gray-800 p-4 rounded-lg transition-shadow cursor-pointer">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">總用戶</h3>
          <p className="text-2xl font-bold">1,234</p>
          <p className="text-xs text-green-600 mt-1">+5.2%</p>
        </div>
        <div className="shadow-md hover:shadow-lg bg-white dark:bg-gray-800 p-4 rounded-lg transition-shadow cursor-pointer">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">活躍用戶</h3>
          <p className="text-2xl font-bold">856</p>
          <p className="text-xs text-green-600 mt-1">+12.8%</p>
        </div>
        <div className="shadow-md hover:shadow-lg bg-white dark:bg-gray-800 p-4 rounded-lg transition-shadow cursor-pointer">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">轉換率</h3>
          <p className="text-2xl font-bold">3.2%</p>
          <p className="text-xs text-red-600 mt-1">-0.5%</p>
        </div>
      </div>
      
      {/* 主要內容 */}
      <div className="shadow-lg bg-white dark:bg-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">最近活動</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
              <div className="w-10 h-10 rounded-full bg-blue-500" />
              <div className="flex-1">
                <p className="font-medium">用戶操作 {i}</p>
                <p className="text-sm text-gray-500">2 分鐘前</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* 浮動操作按鈕 */}
      <button className="fixed bottom-8 right-8 w-14 h-14 bg-blue-600 text-white shadow-xl hover:shadow-2xl rounded-full transition-shadow text-2xl">
        +
      </button>
    </div>
  ),
};

export const ShadowWithMaterial: Story = {
  render: () => (
    <div className="relative h-96 rounded-xl overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500" />
      
      <div className="relative p-8 space-y-6">
        <div className="material-regular shadow-md p-6 rounded-xl">
          <h4 className="font-semibold mb-2">材質 + Level 2 陰影</h4>
          <p className="text-sm text-gray-600 dark:text-gray-300">毛玻璃效果 + 輕度陰影</p>
        </div>
        
        <div className="material-regular shadow-lg p-6 rounded-xl">
          <h4 className="font-semibold mb-2">材質 + Level 3 陰影</h4>
          <p className="text-sm text-gray-600 dark:text-gray-300">毛玻璃效果 + 標準陰影</p>
        </div>
        
        <div className="material-thick shadow-xl p-6 rounded-xl">
          <h4 className="font-semibold mb-2">厚材質 + Level 4 陰影</h4>
          <p className="text-sm text-gray-600 dark:text-gray-300">強毛玻璃效果 + 高度陰影</p>
        </div>
      </div>
    </div>
  ),
};
