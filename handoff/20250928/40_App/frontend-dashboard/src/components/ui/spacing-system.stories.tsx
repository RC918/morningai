import type { Meta, StoryObj } from '@storybook/react';

const SpacingShowcase = ({ 
  size, 
  title, 
  description 
}: { 
  size: string; 
  title: string; 
  description: string;
}) => (
  <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
    <div className="flex items-center gap-4 mb-4">
      <div 
        className="bg-blue-500 rounded"
        style={{ width: size, height: '40px' }}
      />
      <div>
        <h3 className="font-bold">{title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-300">{description}</p>
      </div>
    </div>
  </div>
);

const meta: Meta<typeof SpacingShowcase> = {
  title: 'Design System/Spacing System',
  component: SpacingShowcase,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: '8-level spacing system based on 8px grid. Provides consistent spatial rhythm and visual breathing room.',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof SpacingShowcase>;

export const XS: Story = {
  args: {
    size: '0.25rem',
    title: 'XS - 4px (0.25rem)',
    description: '最小間距 - 圖標與文字、標籤內部',
  },
};

export const SM: Story = {
  args: {
    size: '0.5rem',
    title: 'SM - 8px (0.5rem)',
    description: '緊湊間距 - 表單元素、按鈕組',
  },
};

export const MD: Story = {
  args: {
    size: '1rem',
    title: 'MD - 16px (1rem)',
    description: '標準間距 - 卡片內容、段落（推薦）',
  },
};

export const LG: Story = {
  args: {
    size: '1.5rem',
    title: 'LG - 24px (1.5rem)',
    description: '寬鬆間距 - 區塊間距、卡片間距',
  },
};

export const XL: Story = {
  args: {
    size: '2rem',
    title: 'XL - 32px (2rem)',
    description: '大間距 - 頁面區域、大型卡片',
  },
};

export const TwoXL: Story = {
  args: {
    size: '3rem',
    title: '2XL - 48px (3rem)',
    description: '超大間距 - Hero 區域、主要內容',
  },
};

export const ThreeXL: Story = {
  args: {
    size: '4rem',
    title: '3XL - 64px (4rem)',
    description: '巨大間距 - Landing Page 大區域',
  },
};

export const FourXL: Story = {
  args: {
    size: '6rem',
    title: '4XL - 96px (6rem)',
    description: '最大間距 - 頂級區域、全屏展示',
  },
};

export const AllSpacing: Story = {
  render: () => (
    <div className="space-y-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <SpacingShowcase size="0.25rem" title="XS - 4px" description="最小間距單位" />
      <SpacingShowcase size="0.5rem" title="SM - 8px" description="緊湊間距" />
      <SpacingShowcase size="1rem" title="MD - 16px" description="標準間距（推薦）" />
      <SpacingShowcase size="1.5rem" title="LG - 24px" description="寬鬆間距" />
      <SpacingShowcase size="2rem" title="XL - 32px" description="大間距" />
      <SpacingShowcase size="3rem" title="2XL - 48px" description="超大間距" />
      <SpacingShowcase size="4rem" title="3XL - 64px" description="巨大間距" />
      <SpacingShowcase size="6rem" title="4XL - 96px" description="最大間距" />
    </div>
  ),
};

export const PaddingExamples: Story = {
  render: () => (
    <div className="space-y-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div className="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-md">
        <p className="text-sm">p-2 (8px) - 緊湊內邊距</p>
      </div>
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
        <p>p-4 (16px) - 標準內邊距</p>
      </div>
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
        <p>p-6 (24px) - 寬鬆內邊距</p>
      </div>
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
        <p>p-8 (32px) - 大內邊距</p>
      </div>
    </div>
  ),
};

export const GapExamples: Story = {
  render: () => (
    <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div>
        <h4 className="font-semibold mb-3">gap-2 (8px)</h4>
        <div className="flex gap-2">
          <div className="w-20 h-20 bg-blue-500 rounded-lg" />
          <div className="w-20 h-20 bg-blue-500 rounded-lg" />
          <div className="w-20 h-20 bg-blue-500 rounded-lg" />
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">gap-4 (16px)</h4>
        <div className="flex gap-4">
          <div className="w-20 h-20 bg-green-500 rounded-lg" />
          <div className="w-20 h-20 bg-green-500 rounded-lg" />
          <div className="w-20 h-20 bg-green-500 rounded-lg" />
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">gap-6 (24px)</h4>
        <div className="flex gap-6">
          <div className="w-20 h-20 bg-purple-500 rounded-lg" />
          <div className="w-20 h-20 bg-purple-500 rounded-lg" />
          <div className="w-20 h-20 bg-purple-500 rounded-lg" />
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">gap-8 (32px)</h4>
        <div className="flex gap-8">
          <div className="w-20 h-20 bg-red-500 rounded-lg" />
          <div className="w-20 h-20 bg-red-500 rounded-lg" />
          <div className="w-20 h-20 bg-red-500 rounded-lg" />
        </div>
      </div>
    </div>
  ),
};

export const SpaceBetweenExamples: Story = {
  render: () => (
    <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div>
        <h4 className="font-semibold mb-3">space-y-2 (8px)</h4>
        <div className="space-y-2">
          <div className="bg-blue-500 text-white p-3 rounded-lg">項目 1</div>
          <div className="bg-blue-500 text-white p-3 rounded-lg">項目 2</div>
          <div className="bg-blue-500 text-white p-3 rounded-lg">項目 3</div>
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">space-y-4 (16px)</h4>
        <div className="space-y-4">
          <div className="bg-green-500 text-white p-3 rounded-lg">項目 1</div>
          <div className="bg-green-500 text-white p-3 rounded-lg">項目 2</div>
          <div className="bg-green-500 text-white p-3 rounded-lg">項目 3</div>
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold mb-3">space-y-6 (24px)</h4>
        <div className="space-y-6">
          <div className="bg-purple-500 text-white p-3 rounded-lg">項目 1</div>
          <div className="bg-purple-500 text-white p-3 rounded-lg">項目 2</div>
          <div className="bg-purple-500 text-white p-3 rounded-lg">項目 3</div>
        </div>
      </div>
    </div>
  ),
};

export const CardSystem: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-6 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      {/* 緊湊卡片 */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md space-y-2">
        <h4 className="font-semibold">緊湊卡片</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">p-4, space-y-2</p>
        <p className="text-2xl font-bold">1,234</p>
      </div>
      
      {/* 標準卡片 */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md space-y-4">
        <h4 className="font-semibold">標準卡片</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">p-6, space-y-4</p>
        <p className="text-2xl font-bold">5,678</p>
      </div>
      
      {/* 大型卡片 */}
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-md space-y-6">
        <h4 className="font-semibold">大型卡片</h4>
        <p className="text-sm text-gray-600 dark:text-gray-300">p-8, space-y-6</p>
        <p className="text-2xl font-bold">9,012</p>
      </div>
    </div>
  ),
};

export const FormSystem: Story = {
  render: () => (
    <div className="max-w-md mx-auto p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <form className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg space-y-6">
        <h3 className="text-xl font-bold">註冊表單</h3>
        
        {/* 表單組 - space-y-2 */}
        <div className="space-y-2">
          <label className="block font-medium">姓名</label>
          <input 
            type="text" 
            placeholder="請輸入姓名"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>
        
        <div className="space-y-2">
          <label className="block font-medium">電子郵件</label>
          <input 
            type="email" 
            placeholder="請輸入電子郵件"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>
        
        <div className="space-y-2">
          <label className="block font-medium">密碼</label>
          <input 
            type="password" 
            placeholder="請輸入密碼"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>
        
        {/* 按鈕組 - gap-4 */}
        <div className="flex gap-4 pt-4">
          <button className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
            提交
          </button>
          <button className="flex-1 bg-gray-200 dark:bg-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
            取消
          </button>
        </div>
      </form>
    </div>
  ),
};

export const Navbar: Story = {
  render: () => (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl overflow-hidden">
      <nav className="bg-white dark:bg-gray-800 shadow-md px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <h1 className="text-xl font-bold">MorningAI</h1>
            <div className="flex gap-6">
              <a href="#" className="text-gray-700 dark:text-gray-300 hover:text-blue-600">Dashboard</a>
              <a href="#" className="text-gray-700 dark:text-gray-300 hover:text-blue-600">Analytics</a>
              <a href="#" className="text-gray-700 dark:text-gray-300 hover:text-blue-600">Settings</a>
            </div>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
            升級 Pro
          </button>
        </div>
      </nav>
      
      <div className="p-6">
        <p className="text-gray-600 dark:text-gray-300">
          導航欄使用 px-6 py-4 內邊距，連結間使用 gap-6
        </p>
      </div>
    </div>
  ),
};

export const DashboardLayout: Story = {
  render: () => (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl overflow-hidden">
      {/* 導航欄 */}
      <nav className="bg-white dark:bg-gray-800 shadow-md px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Dashboard</h1>
          <div className="flex gap-2">
            <button className="px-3 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">通知</button>
            <button className="px-3 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">設置</button>
          </div>
        </div>
      </nav>
      
      {/* 主要內容 - py-8 px-6 */}
      <main className="py-8 px-6">
        {/* 統計卡片 - gap-6 mb-8 */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">總用戶</h3>
            <p className="text-3xl font-bold">1,234</p>
            <p className="text-xs text-green-600 mt-1">+5.2%</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">活躍用戶</h3>
            <p className="text-3xl font-bold">856</p>
            <p className="text-xs text-green-600 mt-1">+12.8%</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">轉換率</h3>
            <p className="text-3xl font-bold">3.2%</p>
            <p className="text-xs text-red-600 mt-1">-0.5%</p>
          </div>
        </div>
        
        {/* 主要內容區域 - p-8 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6">最近活動</h2>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                <div className="w-12 h-12 rounded-full bg-blue-500" />
                <div className="flex-1">
                  <p className="font-medium">用戶操作 {i}</p>
                  <p className="text-sm text-gray-500">2 分鐘前</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  ),
};

export const VisualHierarchy: Story = {
  render: () => (
    <div className="max-w-2xl mx-auto p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-lg">
        <h1 className="text-3xl font-bold mb-2">主標題</h1>
        <p className="text-gray-500 mb-8">副標題 - 與主標題緊密相關 (mb-2)</p>
        
        <div className="space-y-6">
          <section className="space-y-4">
            <h2 className="text-2xl font-bold">區塊標題 1</h2>
            <p className="text-gray-600 dark:text-gray-300">
              這是一個內容段落。相關內容使用 space-y-4 分隔。
            </p>
            <div className="space-y-2">
              <h3 className="font-semibold">子標題</h3>
              <p className="text-sm text-gray-500">緊密相關的內容使用 space-y-2</p>
            </div>
          </section>
          
          <section className="space-y-4">
            <h2 className="text-2xl font-bold">區塊標題 2</h2>
            <p className="text-gray-600 dark:text-gray-300">
              不同區塊之間使用 space-y-6 創造明顯分隔。
            </p>
          </section>
        </div>
      </div>
    </div>
  ),
};

export const ResponsiveSpacing: Story = {
  render: () => (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl overflow-hidden">
      <div className="p-4 md:p-6 lg:p-8 bg-white dark:bg-gray-800">
        <h3 className="font-bold mb-4">響應式內邊距</h3>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
          小螢幕: p-4 (16px)
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
          中螢幕: md:p-6 (24px)
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          大螢幕: lg:p-8 (32px)
        </p>
      </div>
      
      <div className="p-4 md:p-6 lg:p-8">
        <div className="space-y-4 md:space-y-6 lg:space-y-8">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg">
            <p className="font-medium">區塊 1</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg">
            <p className="font-medium">區塊 2</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg">
            <p className="font-medium">區塊 3</p>
          </div>
        </div>
      </div>
    </div>
  ),
};

export const NegativeSpacing: Story = {
  render: () => (
    <div className="space-y-8 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <div>
        <h4 className="font-semibold mb-4">頭像組重疊 (-ml-2)</h4>
        <div className="flex">
          <img 
            src="https://i.pravatar.cc/40?img=1" 
            alt="User 1"
            className="w-10 h-10 rounded-full border-2 border-white"
          />
          <img 
            src="https://i.pravatar.cc/40?img=2" 
            alt="User 2"
            className="w-10 h-10 rounded-full border-2 border-white -ml-2"
          />
          <img 
            src="https://i.pravatar.cc/40?img=3" 
            alt="User 3"
            className="w-10 h-10 rounded-full border-2 border-white -ml-2"
          />
          <img 
            src="https://i.pravatar.cc/40?img=4" 
            alt="User 4"
            className="w-10 h-10 rounded-full border-2 border-white -ml-2"
          />
        </div>
      </div>
      
      <div>
        <h4 className="font-semibold mb-4">標籤重疊 (-mt-2)</h4>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md relative">
          <div className="absolute -top-3 left-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
            新功能
          </div>
          <p className="mt-2">這是一個帶有浮動標籤的卡片</p>
        </div>
      </div>
    </div>
  ),
};

export const GridSystem: Story = {
  render: () => (
    <div className="p-8 bg-gray-50 dark:bg-gray-900 rounded-xl">
      <h3 className="text-xl font-bold mb-6">8px 基礎網格系統</h3>
      <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg">
        <div className="grid grid-cols-8 gap-1">
          {Array.from({ length: 96 }, (_, i) => (
            <div 
              key={i}
              className="aspect-square bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-700"
              style={{ width: '8px', height: '8px' }}
            />
          ))}
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-300 mt-4">
          所有間距都基於 8px 的倍數（除了 4px 微調）
        </p>
      </div>
    </div>
  ),
};
