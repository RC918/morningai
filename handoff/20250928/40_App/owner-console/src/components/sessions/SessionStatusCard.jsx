import { cloneElement } from 'react'
import { cn } from '@morningai/shared-ui'

/**
 * SessionStatusCard - Standardized status filter card for Agent Sessions page
 * 
 * Design Specification (Unified Status Card Standard):
 * - Fixed dimensions: min-w-[140px] h-24 (96px) for consistent visual alignment
 * - Internal padding: px-4 py-3 (16px horizontal, 12px vertical)
 * - Icon: 20x20px (size-5), no background container, positioned top-right
 * - Typography: label text-xs font-medium (top-left), value text-2xl font-semibold (bottom-left)
 * - Vertical spacing: justify-between for consistent label-to-value distance
 * - Active state: light tinted background + subtle shadow + 2px left highlight (internal, no external ring)
 * - Focus state: 2px ring with accessibility color (var(--accessibility-focus-outline-color)), only on keyboard focus
 * 
 * @param {Object} props
 * @param {string} props.label - Card label text
 * @param {string|number} props.value - Numeric value to display
 * @param {React.ReactElement} props.icon - Icon element (will be cloned with consistent sizing)
 * @param {'default'|'blue'|'green'|'yellow'|'red'} props.variant - Color variant for icon
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
        'text-left rounded-xl border px-4 py-3',
        'flex flex-col justify-between',
        'transition-all duration-150',
        // Default state
        'border-[var(--border)] bg-[var(--surface)] shadow-sm',
        // Hover state (only when not active)
        !isActive && 'hover:shadow-md hover:border-[var(--neutral-300)]',
        // Active state - light tinted background + subtle shadow (no external ring)
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
        {icon && cloneElement(icon, { 
          className: cn('size-5 shrink-0', styles.iconText),
          'aria-hidden': 'true'
        })}
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
    </button>
  )
}

export { SessionStatusCard }
export default SessionStatusCard
