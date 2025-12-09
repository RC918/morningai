import { TooltipContent } from '@morningai/shared-ui'

/**
 * OwnerTooltipContent - Neutral-styled tooltip for Owner Console
 * 
 * Wraps TooltipContent with consistent neutral styling for header and sidebar tooltips.
 * Supports both light and dark modes with responsive colors.
 * 
 * @param {Object} props
 * @param {string} props.side - Tooltip position ('top' | 'right' | 'bottom' | 'left')
 * @param {React.ReactNode} props.children - Tooltip content
 */
const NEUTRAL_TOOLTIP_CONTENT_CLASS =
  'z-50 bg-white text-neutral-900 dark:bg-neutral-800 dark:text-neutral-50 rounded-md shadow-sm border border-neutral-200 dark:border-neutral-700 px-2 py-1 text-xs'

const NEUTRAL_TOOLTIP_ARROW_CLASS =
  'bg-white fill-white dark:bg-neutral-800 dark:fill-neutral-800'

const OwnerTooltipContent = ({ side = 'bottom', children, ...props }) => (
  <TooltipContent
    side={side}
    sideOffset={8}
    className={NEUTRAL_TOOLTIP_CONTENT_CLASS}
    arrowClassName={NEUTRAL_TOOLTIP_ARROW_CLASS}
    {...props}
  >
    {children}
  </TooltipContent>
)

export { OwnerTooltipContent, NEUTRAL_TOOLTIP_CONTENT_CLASS, NEUTRAL_TOOLTIP_ARROW_CLASS }
export default OwnerTooltipContent
