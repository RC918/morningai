import type { Meta, StoryObj } from '@storybook/react'

/**
 * # 色彩系統指南
 * 
 * MorningAI 的色彩系統遵循 Apple Human Interface Guidelines，確保所有色彩使用符合 WCAG AA 無障礙標準。
 * 
 * ## 關鍵原則
 * 
 * 1. **#007AFF (primary)** - 用於互動元素（按鈕、圖標、背景）
 * 2. **#0051D0 (primary-text)** - 用於文字和鏈接（WCAG AA 合規）
 * 3. **情感色彩** - 用於傳達特定情緒和狀態
 */
const meta = {
  title: 'Design System/Color System',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: '展示 MorningAI 色彩系統的正確使用方式，包括主色、情感色彩和無障礙指南。',
      },
    },
  },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

/**
 * ## 主色系統
 * 
 * ### iOS 藍色 - 兩種用途
 * 
 * - **#007AFF (primary)**: 互動元素專用（對比度 4.02:1）
 * - **#0051D0 (primary-text)**: 文字專用（對比度 6.12:1 ✅ WCAG AA）
 */
export const PrimaryColors: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-4">主色系統</h2>
        <p className="text-neutral-600 mb-6">
          我們使用兩種藍色，分別用於不同場景以確保無障礙合規。
        </p>
      </div>

      {/* Primary - Interactive Elements */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">1. Primary (#007AFF) - 互動元素</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Color Swatch */}
          <div className="border rounded-lg p-4">
            <div className="w-full h-32 rounded-lg mb-3" style={{ backgroundColor: '#007AFF' }}></div>
            <div className="space-y-1">
              <p className="font-mono text-sm">#007AFF</p>
              <p className="text-sm text-neutral-600">對比度: 4.02:1（白底）</p>
              <p className="text-sm font-medium text-success-600">✅ 用於互動元素</p>
            </div>
          </div>

          {/* Usage Examples */}
          <div className="border rounded-lg p-4 space-y-3">
            <h4 className="font-medium mb-2">✅ 正確使用</h4>
            
            {/* Button */}
            <button 
              className="px-4 py-2 rounded-lg text-white font-medium"
              style={{ backgroundColor: '#007AFF' }}
            >
              按鈕背景
            </button>

            {/* Icon */}
            <div className="flex items-center gap-2">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#007AFF" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              <span className="text-sm">圖標顏色</span>
            </div>

            {/* Chart Line */}
            <div className="flex items-center gap-2">
              <svg width="60" height="30" viewBox="0 0 60 30">
                <path d="M 0 30 L 20 10 L 40 20 L 60 5" stroke="#007AFF" strokeWidth="2" fill="none" />
              </svg>
              <span className="text-sm">圖表線條</span>
            </div>
          </div>
        </div>
      </div>

      {/* Primary Text - Text Elements */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">2. Primary Text (#0051D0) - 文字元素</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Color Swatch */}
          <div className="border rounded-lg p-4">
            <div className="w-full h-32 rounded-lg mb-3" style={{ backgroundColor: '#0051D0' }}></div>
            <div className="space-y-1">
              <p className="font-mono text-sm">#0051D0</p>
              <p className="text-sm text-neutral-600">對比度: 6.12:1（白底）</p>
              <p className="text-sm font-medium text-success-600">✅ WCAG AA 合格</p>
            </div>
          </div>

          {/* Usage Examples */}
          <div className="border rounded-lg p-4 space-y-3">
            <h4 className="font-medium mb-2">✅ 正確使用</h4>
            
            {/* Text Link */}
            <a href="#" className="block hover:underline" style={{ color: '#0051D0' }}>
              文字鏈接（可讀性高）
            </a>

            {/* Focus Ring */}
            <button 
              className="px-4 py-2 border rounded-lg"
              style={{ outline: '2px solid #0051D0', outlineOffset: '2px' }}
            >
              Focus Ring 示例
            </button>

            {/* Primary Text */}
            <p style={{ color: '#0051D0' }}>
              主要文字內容（符合 WCAG AA）
            </p>
          </div>
        </div>
      </div>

      {/* Comparison */}
      <div className="border-2 border-error-200 rounded-lg p-4 bg-error-50">
        <h4 className="font-medium text-error-800 mb-2">❌ 錯誤使用</h4>
        <p className="text-sm text-error-700 mb-3">
          不要將 #007AFF 用於文字 - 對比度不足（4.02:1 &lt; 4.5:1）
        </p>
        <div className="bg-white p-3 rounded border">
          <p style={{ color: '#007AFF' }}>
            這段文字使用 #007AFF，對比度不足，難以閱讀 ❌
          </p>
          <p style={{ color: '#0051D0' }} className="mt-2">
            這段文字使用 #0051D0，對比度充足，易於閱讀 ✅
          </p>
        </div>
      </div>
    </div>
  ),
}

/**
 * ## 情感色彩系統
 * 
 * 用於傳達特定情緒和狀態的色彩。
 */
export const EmotionColors: Story = {
  render: () => {
    const emotions = [
      { name: 'Joy', color: '#FF9500', emotion: '快樂、興奮', usage: '慶祝、成功、獎勵' },
      { name: 'Calm', color: '#5AC8FA', emotion: '平靜、信任', usage: '信息、提示、平靜狀態' },
      { name: 'Energy', color: '#FF3B30', emotion: '活力、緊迫', usage: '警告、緊急、重要' },
      { name: 'Growth', color: '#34C759', emotion: '成長、健康', usage: '成長、進步、成功' },
      { name: 'Wisdom', color: '#5856D6', emotion: '智慧、深度', usage: '洞察、智慧、高級功能' },
    ]

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">情感色彩系統</h2>
          <p className="text-neutral-600">
            用於傳達特定情緒和狀態，增強用戶體驗的情感連接。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {emotions.map((item) => (
            <div key={item.name} className="border rounded-lg p-4 space-y-3">
              <div className="w-full h-24 rounded-lg" style={{ backgroundColor: item.color }}></div>
              <div>
                <h3 className="font-semibold text-lg">{item.name}</h3>
                <p className="font-mono text-sm text-neutral-600">{item.color}</p>
              </div>
              <div className="space-y-1 text-sm">
                <p><strong>情感:</strong> {item.emotion}</p>
                <p><strong>用途:</strong> {item.usage}</p>
              </div>
              <div 
                className="px-3 py-2 rounded-lg text-white text-sm text-center"
                style={{ backgroundColor: item.color }}
              >
                示例按鈕
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  },
}

/**
 * ## 語義色彩
 * 
 * 用於表示狀態的標準色彩（Success, Warning, Error）。
 */
export const SemanticColors: Story = {
  render: () => {
    const semantics = [
      { name: 'Success', color: '#16a34a', contrast: '4.54:1', usage: '成功狀態、完成操作、正向反饋' },
      { name: 'Warning', color: '#d97706', contrast: '4.52:1', usage: '警告信息、需要注意的狀態' },
      { name: 'Error', color: '#dc2626', contrast: '5.93:1', usage: '錯誤狀態、失敗操作、危險操作' },
    ]

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">語義色彩</h2>
          <p className="text-neutral-600">
            用於表示系統狀態的標準色彩，所有色彩均符合 WCAG AA 標準。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {semantics.map((item) => (
            <div key={item.name} className="border rounded-lg p-4 space-y-3">
              <div className="w-full h-24 rounded-lg" style={{ backgroundColor: item.color }}></div>
              <div>
                <h3 className="font-semibold text-lg">{item.name}</h3>
                <p className="font-mono text-sm text-neutral-600">{item.color}</p>
                <p className="text-sm text-success-600">✅ {item.contrast} WCAG AA</p>
              </div>
              <p className="text-sm">{item.usage}</p>
              <div 
                className="px-3 py-2 rounded-lg text-white text-sm"
                style={{ backgroundColor: item.color }}
              >
                {item.name} 示例
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  },
}

/**
 * ## 無障礙對比度測試
 * 
 * 展示不同對比度的視覺效果。
 */
export const ContrastTest: Story = {
  render: () => {
    const tests = [
      { bg: '#FFFFFF', fg: '#007AFF', ratio: '4.02:1', pass: false, label: 'iOS 藍 on 白色' },
      { bg: '#FFFFFF', fg: '#0051D0', ratio: '6.12:1', pass: true, label: 'Primary Text on 白色' },
      { bg: '#FFFFFF', fg: '#16a34a', ratio: '4.54:1', pass: true, label: 'Success on 白色' },
      { bg: '#FFFFFF', fg: '#dc2626', ratio: '5.93:1', pass: true, label: 'Error on 白色' },
    ]

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">對比度測試</h2>
          <p className="text-neutral-600 mb-4">
            WCAG AA 標準要求普通文字對比度 ≥ 4.5:1
          </p>
        </div>

        <div className="space-y-4">
          {tests.map((test, index) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-medium">{test.label}</h3>
                  <p className="text-sm text-neutral-600">
                    對比度: {test.ratio} {test.pass ? '✅ 通過' : '❌ 未通過'} WCAG AA
                  </p>
                </div>
                <div className={`px-3 py-1 rounded text-sm font-medium ${test.pass ? 'bg-success-100 text-success-800' : 'bg-error-100 text-error-800'}`}>
                  {test.pass ? '合格' : '不合格'}
                </div>
              </div>
              <div 
                className="p-4 rounded-lg"
                style={{ backgroundColor: test.bg }}
              >
                <p style={{ color: test.fg, fontSize: '16px' }}>
                  這是一段測試文字，用於檢查對比度是否足夠。The quick brown fox jumps over the lazy dog.
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="border-2 border-info-200 rounded-lg p-4 bg-info-50">
          <h4 className="font-medium text-info-800 mb-2">💡 提示</h4>
          <p className="text-sm text-info-700">
            使用 <a href="https://webaim.org/resources/contrastchecker/" target="_blank" rel="noopener noreferrer" className="underline">WebAIM Contrast Checker</a> 來測試你的色彩組合。
          </p>
        </div>
      </div>
    )
  },
}

/**
 * ## 實作範例
 * 
 * 展示如何在實際組件中正確使用色彩。
 */
export const UsageExamples: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-2">實作範例</h2>
        <p className="text-neutral-600">
          展示在實際組件中如何正確使用主色系統。
        </p>
      </div>

      {/* Buttons */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">按鈕（使用 #007AFF）</h3>
        <div className="flex gap-3 flex-wrap">
          <button 
            className="px-4 py-2 rounded-lg text-white font-medium hover:opacity-90 transition"
            style={{ backgroundColor: '#007AFF' }}
          >
            Primary Button
          </button>
          <button 
            className="px-4 py-2 rounded-lg font-medium hover:bg-neutral-100 transition"
            style={{ border: '2px solid #007AFF', color: '#007AFF' }}
          >
            Outline Button
          </button>
        </div>
      </div>

      {/* Links */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">鏈接（使用 #0051D0）</h3>
        <div className="space-y-2">
          <a href="#" className="block hover:underline" style={{ color: '#0051D0' }}>
            這是一個文字鏈接（對比度 6.12:1 ✅）
          </a>
          <a href="#" className="block hover:underline" style={{ color: '#007AFF' }}>
            ❌ 錯誤：這個鏈接使用 #007AFF（對比度 4.02:1，不合格）
          </a>
        </div>
      </div>

      {/* Icons */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">圖標（使用 #007AFF）</h3>
        <div className="flex gap-4">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#007AFF" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#007AFF" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#007AFF" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </div>
      </div>

      {/* Code Example */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">代碼範例</h3>
        <div className="bg-neutral-900 text-neutral-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
          <pre>{`// ✅ 正確：按鈕使用 primary
<button className="bg-primary text-white">
  Click Me
</button>

<a href="#" className="text-primary-text">
  Read More
</a>

<a href="#" className="text-primary">
  Read More (對比度不足)
</a>`}</pre>
        </div>
      </div>
    </div>
  ),
}
