import { useId } from 'react'
import { useTranslation } from 'react-i18next'
import { AppleInput } from '@/components/ui/apple-input'
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
    <AppleInput
      id={fieldId}
      name={name}
      type={type}
      label={label}
      required={required}
      helperText={description}
      state={hasError ? 'error' : 'default'}
      errorText={error}
      aria-invalid={hasError}
      aria-describedby={ariaDescribedBy}
      aria-required={required}
      haptic="light"
      {...inputProps}
      {...props}
    />
  )
}

export default FormField
