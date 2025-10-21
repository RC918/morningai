/**
 * TokenExample Component
 * 
 * This component demonstrates how to use CSS variables (Design Tokens) defined in theme-apple.css
 * 
 * Usage:
 * 1. Ensure App.jsx root container has .theme-apple class
 * 2. Use CSS variables in component style or className
 * 3. Supports Dark Mode (automatically switches .theme-apple.dark variables)
 */

import React from 'react'
import { useTranslation } from 'react-i18next'

export const TokenExample = () => {
  const { t } = useTranslation()
  return (
    <div style={{
      padding: 'var(--spacing-6)',
      backgroundColor: 'var(--bg-primary)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-md)'
    }}>
      {/* Title - using typography tokens */}
      <h2 style={{
        fontSize: 'var(--font-size-2xl)',
        fontWeight: 'var(--font-weight-bold)',
        color: 'var(--text-primary)',
        marginBottom: 'var(--spacing-4)'
      }}>
        {t('tokenExample.title')}
      </h2>

      {/* Description text */}
      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--text-secondary)',
        lineHeight: 'var(--line-height-relaxed)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {t('tokenExample.description')}
      </p>

      {/* Button examples - using color tokens */}
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

      {/* Card example - using spacing, shadow, border tokens */}
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
          {t('tokenExample.cardTitle')}
        </h3>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--text-secondary)',
          lineHeight: 'var(--line-height-normal)'
        }}>
          {t('tokenExample.cardDescription')}
        </p>
      </div>

      {/* Status badge examples - using semantic color tokens */}
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
          {t('tokenExample.statusSuccess')}
        </span>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-warning-light)',
          color: 'var(--color-warning)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          {t('tokenExample.statusWarning')}
        </span>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-error-light)',
          color: 'var(--color-error)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          {t('tokenExample.statusError')}
        </span>
        <span style={{
          padding: 'var(--spacing-1) var(--spacing-3)',
          backgroundColor: 'var(--color-info-light)',
          color: 'var(--color-info)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)'
        }}>
          {t('tokenExample.statusInfo')}
        </span>
      </div>
    </div>
  )
}

export default TokenExample
