import { cloneElement } from 'react'
import { cn } from '@morningai/shared-ui'

/**
 * SessionStatusCard - Standardized status filter card for Agent Sessions page
 * 
 * Design Specification:
 * - Fixed height: h-24 (96px) for consistent visual alignment
 * - Internal padding: px-4 py-3 (16px horizontal, 12px vertical)
 * - Icon container: 28x28px (h-7 w-7) with rounded-lg
 * - Typography: label text-xs font-medium, value text-2xl font-semibold
 * - Active state: light tinted background + subtle shadow + primary colored value
 * - Focus state: 2px ring with accessibility color (#0284c7)
 * 
 * @param {Object} props
 * @param {string} props.label - Card label text
 * @param {string|number} props.value - Numeric value to display
 * @param {React.ReactElement} props.icon - Icon element (will be cloned with consistent sizing)
 * @param {'default'|'blue'|'green'|'yellow'|'red'} props.variant - Color variant for icon background
 * @param {boolean} props.isActive - Whether this card is currently selected
 * @param {Function} props.onClick - Click handler
 * @param {string} [props.className] - Additional className for the wrapper
 */

const variantStyles = {
  default: {
    iconBg: 'bg-[var(--neutral-100)]',
    iconText: 'text-[var(--neutral-600)]',
    activeBg: 'bg-[var(--neutral-50)]',
    activeBorder: 'border-[var(--neutral-200)]',
    activeValue: 'text-[var(--neutral-700)]',
  },
  blue: {
    iconBg: 'bg-[var(--primary-50)]',
    iconText: 'text-[var(--primary-600)]',
    activeBg: 'bg-[var(--primary-50)]',
    activeBorder: 'border-[var(--primary-100)]',
    activeValue: 'text-[var(--primary-600)]',
  },
  green: {
    iconBg: 'bg-[var(--success-50)]',
    iconText: 'text-[var(--success-600)]',
    activeBg: 'bg-[var(--success-50)]',
    activeBorder: 'border-[var(--success-100)]',
    activeValue: 'text-[var(--success-600)]',
  },
  yellow: {
    iconBg: 'bg-[var(--warning-50)]',
    iconText: 'text-[var(--warning-600)]',
    activeBg: 'bg-[var(--warning-50)]',
    activeBorder: 'border-[var(--warning-100)]',
    activeValue: 'text-[var(--warning-600)]',
  },
  red: {
    iconBg: 'bg-[var(--error-50)]',
    iconText: 'text-[var(--error-600)]',
    activeBg: 'bg-[var(--error-50)]',
    activeBorder: 'border-[var(--error-100)]',
    activeValue: 'text-[var(--error-600)]',
  },
}

function SessionStatusCard({
  label,
  value,
  icon,
  variant = 'default',
  isActive = false,
  onClick,
  className,
}) {
  const styles = variantStyles[variant] || variantStyles.default

  return (
    <button
      type="button"
      aria-pressed={isActive}
      onClick={onClick}
      className={cn(
        'text-left w-full rounded-xl transition-all duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0284c7] focus-visible:ring-offset-2',
        className
      )}
    >
      <div
        className={cn(
          // Base card styles - fixed height for consistency
          'relative h-24 w-full rounded-xl border px-4 py-3',
          'flex flex-col justify-between',
          'transition-all duration-150',
          // Default state
          'border-[var(--border)] bg-[var(--surface)] shadow-sm',
          // Hover state (only when not active)
          !isActive && 'hover:shadow-md hover:border-[var(--neutral-300)]',
          // Active state - light tinted background + subtle shadow
          isActive && [
            styles.activeBg,
            styles.activeBorder,
            'shadow-md',
          ]
        )}
      >
        {/* Subtle left highlight for active state */}
        {isActive && (
          <div 
            className={cn(
              'pointer-events-none absolute inset-y-3 left-1.5 w-0.5 rounded-full',
              variant === 'default' ? 'bg-[var(--neutral-400)]' : styles.iconText
            )}
            aria-hidden="true"
          />
        )}
        
        {/* Top row: Label + Icon */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[var(--text-secondary)]">
            {label}
          </span>
          <div
            className={cn(
              'flex h-7 w-7 items-center justify-center rounded-lg shrink-0',
              styles.iconBg,
              styles.iconText
            )}
          >
            {icon && cloneElement(icon, { 
              className: 'w-4 h-4',
              'aria-hidden': 'true'
            })}
          </div>
        </div>
        
        {/* Bottom row: Value */}
        <div className="flex items-baseline">
          <span
            className={cn(
              'text-2xl font-semibold transition-colors duration-150',
              isActive ? styles.activeValue : 'text-[var(--text-primary)]'
            )}
          >
            {value}
          </span>
        </div>
      </div>
    </button>
  )
}

export { SessionStatusCard }
export default SessionStatusCard
