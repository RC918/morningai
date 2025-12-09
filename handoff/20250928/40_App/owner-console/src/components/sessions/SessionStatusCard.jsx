import { cloneElement } from 'react'
import { cn } from '@morningai/shared-ui'

/**
 * SessionStatusCard - Standardized status filter card for Agent Sessions page
 * 
 * Design Specification (Unified Status Card Standard - aligned with StatCard):
 * - Fixed dimensions: min-w-[140px] h-24 (96px) for consistent visual alignment
 * - Internal padding: p-4 (16px) matching StatCard
 * - Icon container: 40x40px (h-10 w-10) circular (rounded-full), positioned right-center
 * - Typography: label text-xs font-medium (top-left), value text-2xl font-semibold (below label)
 * - Layout: flex row with content on left, icon on right (matching StatCard)
 * - Active state: light tinted background + subtle shadow + colored border
 * - Focus state: 2px ring with accessibility color (var(--accessibility-focus-outline-color)), only on keyboard focus
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
    activeBg: 'bg-neutral-50',
    activeBorder: 'border-neutral-300',
    activeValue: 'text-[var(--neutral-700)]',
  },
  blue: {
    iconBg: 'bg-[var(--primary-50)]',
    iconText: 'text-[var(--primary-600)]',
    activeBg: 'bg-primary-50',
    activeBorder: 'border-primary-500',  // Match session list card styling
    activeValue: 'text-[var(--primary-600)]',
  },
  green: {
    iconBg: 'bg-[var(--success-50)]',
    iconText: 'text-[var(--success-600)]',
    activeBg: 'bg-success-50',
    activeBorder: 'border-success-500',  // Match session list card styling
    activeValue: 'text-[var(--success-600)]',
  },
  yellow: {
    iconBg: 'bg-[var(--warning-50)]',
    iconText: 'text-[var(--warning-600)]',
    activeBg: 'bg-warning-50',
    activeBorder: 'border-warning-500',  // Match session list card styling
    activeValue: 'text-[var(--warning-600)]',
  },
  red: {
    iconBg: 'bg-[var(--error-50)]',
    iconText: 'text-[var(--error-600)]',
    activeBg: 'bg-error-50',
    activeBorder: 'border-error-500',  // Match session list card styling
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
        // Fixed dimensions for all cards - ensures visual consistency
        'relative min-w-[140px] h-24 w-full',
        'text-left rounded-xl border p-4',
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
        ],
        // Focus state - only visible on keyboard navigation
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accessibility-focus-outline-color)] focus-visible:ring-offset-2',
        className
      )}
    >
      {/* Layout matching StatCard: content left, icon right */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          {/* Label */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-[var(--text-secondary)]">
              {label}
            </span>
          </div>
          {/* Value */}
          <div
            className={cn(
              'text-2xl font-semibold transition-colors duration-150',
              isActive ? styles.activeValue : 'text-[var(--text-primary)]'
            )}
          >
            {value}
          </div>
        </div>
        {/* Icon container - matching StatCard: h-10 w-10 rounded-full */}
        {icon && (
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-full ml-3 shrink-0',
              styles.iconBg,
              styles.iconText
            )}
          >
            {cloneElement(icon, { 
              className: 'w-5 h-5',
              'aria-hidden': 'true'
            })}
          </div>
        )}
      </div>
    </button>
  )
}

export { SessionStatusCard }
export default SessionStatusCard
