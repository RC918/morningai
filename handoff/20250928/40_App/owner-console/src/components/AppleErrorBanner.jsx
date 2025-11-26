import { Alert, AlertDescription, AlertTitle } from '@morningai/shared-ui'
import { AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { AppleButton } from '@/components/apple/apple-button'

/**
 * AppleErrorBanner - A consistent Apple-styled error banner component
 * 
 * This component wraps the shared-ui Alert with Apple design system styling:
 * - Softer border radius (rounded-xl)
 * - Apple typography tokens (text-callout, text-footnote)
 * - Tinted background (not full glassmorphism for accessibility)
 * - Consistent spacing and layout
 * 
 * @param {Object} props
 * @param {string} props.title - Error title
 * @param {string} props.message - Error message
 * @param {Function} props.onRetry - Optional retry callback
 * @param {string} props.retryLabel - Optional custom retry button label
 * @param {React.ReactNode} props.icon - Optional custom icon (defaults to AlertTriangle)
 * @param {string} props.testId - Optional test ID for the alert element (defaults to 'error-alert')
 * @param {string} props.retryTestId - Optional test ID for the retry button (defaults to 'retry-button')
 */
export const AppleErrorBanner = ({ 
  title, 
  message, 
  onRetry, 
  retryLabel,
  icon = <AlertTriangle className="h-4 w-4" />,
  testId = 'error-alert',
  retryTestId = 'retry-button'
}) => {
  const { t } = useTranslation()
  
  return (
    <Alert 
      variant="destructive" 
      data-testid={testId}
      className="rounded-xl border-error-200 bg-error-50/80 dark:bg-error-50/80 text-neutral-900 dark:text-neutral-900"
    >
      {icon}
      <AlertTitle className="text-callout font-semibold text-neutral-900 dark:text-neutral-900">{title}</AlertTitle>
      <AlertDescription className="text-footnote text-neutral-800 dark:text-neutral-800">
        {message}
        {onRetry && (
          <AppleButton 
            onClick={onRetry} 
            variant="outline" 
            size="sm" 
            haptic="light"
            className="ml-4"
            data-testid={retryTestId}
          >
            {retryLabel || t('common.refresh')}
          </AppleButton>
        )}
      </AlertDescription>
    </Alert>
  )
}
