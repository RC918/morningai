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
        <p className="text-gray-600 dark:text-gray-300">{description}</p>
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
            <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className="text-3xl font-bold mb-2">$12,345</p>
          <p className="text-sm text-gray-500">+12.5% 較上月</p>
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
              <a href="#" className="text-gray-700 hover:text-blue-600">Dashboard</a>
              <a href="#" className="text-gray-700 hover:text-blue-600">Analytics</a>
              <a href="#" className="text-gray-700 hover:text-blue-600">Settings</a>
            </nav>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
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
          <p className="text-gray-600 dark:text-gray-300 mb-4">
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
            <p className="text-sm text-gray-600 dark:text-gray-300">
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
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            此操作無法撤銷，確定要繼續嗎？
          </p>
          <div className="flex gap-3">
            <button className="flex-1 bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded-lg transition-colors">
              取消
            </button>
            <button className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
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
      <div className="relative h-auto rounded-xl overflow-hidden p-8 bg-gray-900">
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
          <p className="text-sm text-gray-600">10px blur</p>
        </div>
        <div className="backdrop-blur-md bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-md</h4>
          <p className="text-sm text-gray-600">20px blur</p>
        </div>
        <div className="backdrop-blur-lg bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-lg</h4>
          <p className="text-sm text-gray-600">30px blur</p>
        </div>
        <div className="backdrop-blur-xl bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-blur-xl</h4>
          <p className="text-sm text-gray-600">40px blur</p>
        </div>
        <div className="backdrop-glass bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-glass</h4>
          <p className="text-sm text-gray-600">blur + saturate</p>
        </div>
        <div className="backdrop-glass-vibrant bg-white/50 p-6 rounded-xl">
          <h4 className="font-semibold mb-2">backdrop-glass-vibrant</h4>
          <p className="text-sm text-gray-600">blur + saturate + brightness</p>
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
              <button className="px-3 py-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                通知
              </button>
              <button className="px-3 py-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700">
                設置
              </button>
            </div>
          </div>
        </nav>
        
        {/* Cards Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="material-card material-shadow-3 p-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-1">總用戶</h3>
            <p className="text-2xl font-bold">1,234</p>
            <p className="text-xs text-green-600 mt-1">+5.2%</p>
          </div>
          <div className="material-card material-shadow-3 p-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-1">活躍用戶</h3>
            <p className="text-2xl font-bold">856</p>
            <p className="text-xs text-green-600 mt-1">+12.8%</p>
          </div>
          <div className="material-card material-shadow-3 p-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-1">轉換率</h3>
            <p className="text-2xl font-bold">3.2%</p>
            <p className="text-xs text-red-600 mt-1">-0.5%</p>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="material-regular material-shadow-4 rounded-xl p-6">
          <h2 className="text-lg font-bold mb-4">最近活動</h2>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                <div className="w-10 h-10 rounded-full bg-blue-500" />
                <div className="flex-1">
                  <p className="font-medium">用戶操作 {i}</p>
                  <p className="text-sm text-gray-500">2 分鐘前</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  ),
};
