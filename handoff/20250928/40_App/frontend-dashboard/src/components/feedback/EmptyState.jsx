import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { useTranslation } from 'react-i18next'

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  action,
  actionLabel,
  illustration,
  className = ''
}) => {
  const { t } = useTranslation()
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}
    >
      {illustration ? (
        <img src={illustration} alt="" aria-hidden="true" role="presentation" className="w-64 h-64 mb-6" />
      ) : Icon && (
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
          <Icon className="w-10 h-10 text-gray-600" />
        </div>
      )}
      
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-gray-600 text-center max-w-md mb-6">
        {description}
      </p>
      
      {action && (
        <Button onClick={action} size="lg">
          {actionLabel || t('feedback.emptyState.defaultPrimaryAction')}
        </Button>
      )}
    </motion.div>
  )
}

export default EmptyState
