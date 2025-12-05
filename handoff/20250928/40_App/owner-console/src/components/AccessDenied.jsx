import { Alert, AlertDescription, AlertTitle } from '@morningai/shared-ui'
import { ShieldX } from 'lucide-react'
import { useTranslation } from 'react-i18next'

/**
 * AccessDenied - A consistent Apple-styled access denied banner component
 * 
 * This component displays a user-friendly message when a user lacks the required
 * permissions to access a feature. Used for platform_admin restricted features.
 * 
 * Design follows Apple design system styling:
 * - Softer border radius (rounded-xl)
 * - Apple typography tokens (text-callout, text-footnote)
 * - Tinted background (amber/warning color scheme)
 * - Consistent spacing and layout
 * 
 * @param {Object} props
 * @param {string} props.title - Optional custom title (defaults to i18n key)
 * @param {string} props.message - Optional custom message (defaults to i18n key)
 * @param {string} props.requiredRole - Optional role name to display (e.g., "Platform Admin")
 * @param {React.ReactNode} props.icon - Optional custom icon (defaults to ShieldX)
 * @param {string} props.testId - Optional test ID for the alert element
 */
export const AccessDenied = ({ 
  title, 
  message, 
  requiredRole,
  icon = <ShieldX className="h-5 w-5" />,
  testId = 'access-denied-alert'
}) => {
  const { t } = useTranslation()
  
  const displayTitle = title || t('common.accessDenied.title')
  const displayMessage = message || (requiredRole 
    ? t('common.accessDenied.messageWithRole', { role: requiredRole })
    : t('common.accessDenied.message'))
  
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4" data-testid={testId}>
      <Alert 
        className="max-w-md rounded-xl border-warning-200 bg-warning-50/80 dark:bg-warning-900/20 text-neutral-900 dark:text-neutral-100"
      >
        <div className="flex items-start gap-3">
          <div className="text-warning-600 dark:text-warning-400 mt-1">
            {icon}
          </div>
          <div className="flex-1">
            <AlertTitle className="text-callout font-semibold text-neutral-900 dark:text-neutral-100">
              {displayTitle}
            </AlertTitle>
            <AlertDescription className="text-footnote text-neutral-700 dark:text-neutral-300 mt-1">
              {displayMessage}
            </AlertDescription>
          </div>
        </div>
      </Alert>
    </div>
  )
}

export default AccessDenied
