import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { 
  FileText, 
  Search, 
  Inbox, 
  Database, 
  Users, 
  Settings,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Zap
} from 'lucide-react'
import { useTranslation } from 'react-i18next'

const emptyStateVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: {
      duration: 0.5,
      ease: "easeOut"
    }
  }
}

const iconVariants = {
  hidden: { scale: 0, rotate: -180 },
  visible: { 
    scale: 1, 
    rotate: 0,
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 15,
      delay: 0.2
    }
  }
}

const floatingVariants = {
  animate: {
    y: [-5, 5, -5],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
}

export const EmptyStateLibrary = ({
  variant = 'default',
  icon: CustomIcon,
  title,
  description,
  primaryAction,
  primaryActionLabel,
  secondaryAction,
  secondaryActionLabel,
  illustration,
  className = ''
}) => {
  const { t } = useTranslation()
  const variants = {
    default: {
      icon: CustomIcon || Inbox,
      bgColor: 'bg-gray-100',
      iconColor: 'text-gray-400',
      titleColor: 'text-gray-900',
      descColor: 'text-gray-600'
    },
    search: {
      icon: CustomIcon || Search,
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-500',
      titleColor: 'text-blue-900',
      descColor: 'text-blue-600'
    },
    noData: {
      icon: CustomIcon || Database,
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-500',
      titleColor: 'text-purple-900',
      descColor: 'text-purple-600'
    },
    error: {
      icon: CustomIcon || XCircle,
      bgColor: 'bg-red-50',
      iconColor: 'text-red-500',
      titleColor: 'text-red-900',
      descColor: 'text-red-600'
    },
    success: {
      icon: CustomIcon || CheckCircle,
      bgColor: 'bg-green-50',
      iconColor: 'text-green-500',
      titleColor: 'text-green-900',
      descColor: 'text-green-600'
    },
    warning: {
      icon: CustomIcon || AlertCircle,
      bgColor: 'bg-yellow-50',
      iconColor: 'text-yellow-500',
      titleColor: 'text-yellow-900',
      descColor: 'text-yellow-600'
    },
    loading: {
      icon: CustomIcon || Clock,
      bgColor: 'bg-indigo-50',
      iconColor: 'text-indigo-500',
      titleColor: 'text-indigo-900',
      descColor: 'text-indigo-600'
    },
    premium: {
      icon: CustomIcon || Zap,
      bgColor: 'bg-gradient-to-br from-yellow-50 to-orange-50',
      iconColor: 'text-orange-500',
      titleColor: 'text-orange-900',
      descColor: 'text-orange-600'
    }
  }

  const currentVariant = variants[variant] || variants.default
  const Icon = currentVariant.icon

  return (
    <motion.div
      variants={emptyStateVariants}
      initial="hidden"
      animate="visible"
      className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}
    >
      {illustration ? (
        <motion.img 
          src={illustration} 
          alt=""
          aria-hidden="true"
          role="presentation"
          className="w-64 h-64 mb-6"
          variants={floatingVariants}
          animate="animate"
        />
      ) : (
        <motion.div
          variants={iconVariants}
          initial="hidden"
          animate="visible"
          className={`w-24 h-24 ${currentVariant.bgColor} rounded-2xl flex items-center justify-center mb-6 shadow-lg`}
        >
          <motion.div
            variants={floatingVariants}
            animate="animate"
          >
            <Icon className={`w-12 h-12 ${currentVariant.iconColor}`} />
          </motion.div>
        </motion.div>
      )}
      
      <motion.h3 
        className={`text-2xl font-bold ${currentVariant.titleColor} mb-3 text-center`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {title}
      </motion.h3>
      
      <motion.p 
        className={`${currentVariant.descColor} text-center max-w-md mb-8 leading-relaxed`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        {description}
      </motion.p>
      
      <motion.div 
        className="flex flex-col sm:flex-row gap-3"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        {primaryAction && (
          <Button 
            onClick={primaryAction} 
            size="lg"
            className="shadow-lg hover:shadow-xl transition-shadow"
          >
            {primaryActionLabel || t('feedback.emptyState.defaultPrimaryAction')}
          </Button>
        )}
        {secondaryAction && (
          <Button 
            onClick={secondaryAction} 
            variant="outline"
            size="lg"
          >
            {secondaryActionLabel || t('feedback.emptyState.defaultSecondaryAction')}
          </Button>
        )}
      </motion.div>
    </motion.div>
  )
}

export const NoDataState = (props) => {
  const { t } = useTranslation()
  return (
    <EmptyStateLibrary
      variant="noData"
      title={t('feedback.emptyState.noData.title')}
      description={t('feedback.emptyState.noData.description')}
      {...props}
    />
  )
}

export const NoSearchResults = (props) => {
  const { t } = useTranslation()
  return (
    <EmptyStateLibrary
      variant="search"
      title={t('feedback.emptyState.noSearchResults.title')}
      description={t('feedback.emptyState.noSearchResults.description')}
      {...props}
    />
  )
}

export const ErrorState = (props) => {
  const { t } = useTranslation()
  return (
    <EmptyStateLibrary
      variant="error"
      title={t('feedback.emptyState.error.title')}
      description={t('feedback.emptyState.error.description')}
      {...props}
    />
  )
}

export const SuccessState = (props) => {
  const { t } = useTranslation()
  return (
    <EmptyStateLibrary
      variant="success"
      title={t('feedback.emptyState.success.title')}
      description={t('feedback.emptyState.success.description')}
      {...props}
    />
  )
}

export const LoadingState = (props) => {
  const { t } = useTranslation()
  return (
    <EmptyStateLibrary
      variant="loading"
      title={t('feedback.emptyState.loading.title')}
      description={t('feedback.emptyState.loading.description')}
      {...props}
    />
  )
}

export const PremiumFeatureState = (props) => {
  const { t } = useTranslation()
  return (
    <EmptyStateLibrary
      variant="premium"
      title={t('feedback.emptyState.premium.title')}
      description={t('feedback.emptyState.premium.description')}
      primaryActionLabel={t('feedback.emptyState.premium.primaryAction')}
      secondaryActionLabel={t('feedback.emptyState.premium.secondaryAction')}
      {...props}
    />
  )
}

export default EmptyStateLibrary
