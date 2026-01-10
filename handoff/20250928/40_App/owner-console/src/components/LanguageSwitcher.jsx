import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, Check } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { motion, AnimatePresence } from 'framer-motion'

const languages = [
  { code: 'en-US', name: 'English' },
  { code: 'zh-TW', name: '繁體中文' }
]

export const LanguageSwitcher = ({ variant = 'default', className = '' }) => {
  const { t, i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0]

  const changeLanguage = (langCode) => {
    i18n.changeLanguage(langCode)
    setIsOpen(false)
  }

  if (variant === 'compact') {
    return (
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <AppleButton 
            variant="outline" 
            size="icon-sm" 
            haptic="light"
            className={className}
            aria-label={t('common.changeLanguage')}
          >
            <Globe className="w-5 h-5" />
          </AppleButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          align="end" 
          className="w-48 !bg-white dark:!bg-neutral-800 border border-neutral-200 dark:border-neutral-700"
          style={{ backgroundColor: 'white' }}
        >
          <AnimatePresence>
            {languages.map((lang) => (
              <motion.div
                key={lang.code}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2 }}
              >
                <DropdownMenuItem
                  onClick={() => changeLanguage(lang.code)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <span>{lang.name}</span>
                  {i18n.language === lang.code && (
                    <Check className="w-4 h-4 text-success-600" />
                  )}
                </DropdownMenuItem>
              </motion.div>
            ))}
          </AnimatePresence>
        </DropdownMenuContent>
      </DropdownMenu>
    )
  }

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <AppleButton variant="outline" haptic="light" className={`${className} min-w-32`}>
          <Globe className="w-4 h-4 mr-2" />
          <span>{currentLanguage.name}</span>
        </AppleButton>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-48 !bg-white dark:!bg-neutral-800 border border-neutral-200 dark:border-neutral-700"
        style={{ backgroundColor: 'white' }}
      >
        <AnimatePresence>
          {languages.map((lang) => (
            <motion.div
              key={lang.code}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
            >
              <DropdownMenuItem
                onClick={() => changeLanguage(lang.code)}
                className="flex items-center justify-between cursor-pointer"
              >
                <span>{lang.name}</span>
                {i18n.language === lang.code && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  >
                    <Check className="w-4 h-4 text-success-600" />
                  </motion.div>
                )}
              </DropdownMenuItem>
            </motion.div>
          ))}
        </AnimatePresence>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default LanguageSwitcher
