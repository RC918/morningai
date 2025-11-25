import { Alert, AlertDescription, AlertTitle, Button } from '@morningai/shared-ui'
import { AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

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
 */
export const AppleErrorBanner = ({ 
  title, 
  message, 
  onRetry, 
  retryLabel,
  icon = <AlertTriangle className="h-4 w-4" />
}) => {
  const { t } = useTranslation()
  
  return (
    <Alert 
      variant="destructive" 
      className="rounded-xl border-error-200 bg-error-50/80 dark:bg-error-900/20"
    >
      {icon}
      <AlertTitle className="text-callout font-semibold">{title}</AlertTitle>
      <AlertDescription className="text-footnote">
        {message}
        {onRetry && (
          <Button 
            onClick={onRetry} 
            variant="outline" 
            size="sm" 
            className="ml-4"
          >
            {retryLabel || t('common.refresh')}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}
