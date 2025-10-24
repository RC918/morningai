import { useId } from 'react'
import { useTranslation } from 'react-i18next'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { AlertCircle } from 'lucide-react'

/**
 * Accessible form field component with ARIA support and live region error announcements
 * Follows WCAG 2.1 AA guidelines for form accessibility
 * 
 * @param {Object} props
 * @param {string} props.label - Field label text
 * @param {string} props.name - Field name
 * @param {string} props.type - Input type
 * @param {string} props.error - Error message (if any)
 * @param {boolean} props.required - Whether field is required
 * @param {string} props.description - Optional field description
 * @param {Object} props.inputProps - Additional props to pass to Input
 */
export const FormField = ({
  label,
  name,
  type = 'text',
  error,
  required = false,
  description,
  inputProps = {},
  ...props
}) => {
  const { t } = useTranslation()
  const fieldId = useId()
  const errorId = `${fieldId}-error`
  const descriptionId = `${fieldId}-description`
  
  const hasError = Boolean(error)
  
  const ariaDescribedBy = [
    description && descriptionId,
    hasError && errorId
  ].filter(Boolean).join(' ') || undefined
  
  return (
    <div className="space-y-2">
      <Label htmlFor={fieldId}>
        {label}
        {required && (
          <span className="text-error-500 ml-1" aria-label={t('form.required', 'required')}>
            *
          </span>
        )}
      </Label>
      
      {description && (
        <p id={descriptionId} className="text-sm text-muted-foreground">
          {description}
        </p>
      )}
      
      <Input
        id={fieldId}
        name={name}
        type={type}
        aria-invalid={hasError}
        aria-describedby={ariaDescribedBy}
        aria-required={required}
        {...inputProps}
        {...props}
      />
      
      {hasError && (
        <div
          id={errorId}
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
          className="flex items-start gap-2 text-sm text-error-600"
        >
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}

export default FormField
