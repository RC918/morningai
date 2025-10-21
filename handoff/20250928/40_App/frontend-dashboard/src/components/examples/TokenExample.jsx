/**
 * TokenExample Component
 * 
 * 此元件示範如何使用 theme-apple.css 中定義的 CSS 變數（Design Tokens）
 * 
 * 使用方式：
 * 1. 確保 App.jsx 根容器有 .theme-apple class
 * 2. 在元件的 style 或 className 中使用 CSS 變數
 * 3. 支援 Dark Mode（自動切換 .theme-apple.dark 變數）
 */

import React from 'react'

export const TokenExample = () => {
  return (
    <div style={{
      padding: 'var(--spacing-6)',
      backgroundColor: 'var(--bg-primary)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-md)'
    }}>
      {/* 標題 - 使用 typography tokens */}
      <h2 style={{
        fontSize: 'var(--font-size-2xl)',
        fontWeight: 'var(--font-weight-bold)',
        color: 'var(--text-primary)',
        marginBottom: 'var(--spacing-4)'
      }}>
        Design Token 範例
      </h2>

      {/* 描述文字 */}
      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--text-secondary)',
        lineHeight: 'var(--line-height-relaxed)',
        marginBottom: 'var(--spacing-6)'
      }}>
        此元件使用 theme-apple.css 定義的 CSS 變數，確保設計一致性並支援 Dark Mode。
      </p>

      {/* 按鈕範例 - 使用 color tokens */}
      <div style={{
        display: 'flex',
        gap: 'var(--spacing-3)',
        marginBottom: 'var(--spacing-6)'
      }}>
        <button style={{
          padding: 'var(--spacing-2) var(--spacing-4)',
          backgroundColor: 'var(--color-primary)',
          color: 'white',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          fontSize: 'var(--font-size-sm)',
          fontWeight: 'var(--font-weight-medium)',
          cursor: 'pointer',
          transition: 'all var(--transition-base)',
          boxShadow: 'var(--shadow-sm)'
        }}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = 'var(--color-primary-hover)'
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'var(--color-primary)'
        }}
        >
          Primary Button
        </button>

        <button style={{
          padding: 'var(--spacing-2) var(--spacing-4)',
          backgroundColor: 'var(--color-secondary)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-md)',
          fontSize: 'var(--font-size-sm)',
          fontWeight: 'var(--font-weight-medium)',
          cursor: 'pointer',
          transition: 'all var(--transition-base)'
        }}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = 'var(--color-secondary-hover)'
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'var(--color-secondary)'
        }}
        >
          Secondary Button
        </button>
      </div>

      {/* 卡片範例 - 使用 spacing, shadow, border tokens */}
      <div style={{
        padding: 'var(--spacing-4)',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-md)',
        marginBottom: 'var(--spacing-4)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: 'var(--font-weight-semibold)',
          color: 'var(--text-primary)',
          marginBottom: 'var(--spacing-2)'
        }}>
          卡片標題
        </h3>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--text-secondary)',
          lineHeight: 'var(--line-height-normal)'
        }}>
          這是一個使用 Design Tokens 的卡片元件範例。
        </p>
      </div>

      {/* 狀態標籤範例 - 使用 semantic color tokens */}
      <div style={{
        display: 'flex',
        gap: 'var(--spacing-2)',
        flexWrap: 'wrap'
      }}>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-success-light)',
          color: 'var(--color-success)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          成功
        </span>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-warning-light)',
          color: 'var(--color-warning)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          警告
        </span>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-error-light)',
          color: 'var(--color-error)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          錯誤
        </span>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-info-light)',
          color: 'var(--color-info)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          資訊
        </span>
      </div>
    </div>
  )
}

export default TokenExample
