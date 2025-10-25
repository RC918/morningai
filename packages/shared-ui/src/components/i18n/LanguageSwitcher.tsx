import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, Check } from 'lucide-react'
import { Button } from '../ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'
import { motion, AnimatePresence } from 'framer-motion'

const languages = [
  { code: 'en-US', name: 'English', flag: '🇺🇸' },
  { code: 'zh-TW', name: '繁體中文', flag: '🇹🇼' }
]

export const LanguageSwitcher = ({ variant = 'default', className = '' }) => {
  const { i18n } = useTranslation()
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
          <Button 
            variant="outline" 
            size="sm" 
            className={`${className} bg-white hover:bg-gray-50 shadow-md flex items-center justify-center`}
            style={{ width: '40px', height: '40px', padding: '0' }}
          >
            <Globe className="w-5 h-5" style={{ width: '20px', height: '20px' }} />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          align="end" 
          className="w-48 !bg-white dark:!bg-gray-800 border border-gray-200 dark:border-gray-700"
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
                  <span className="flex items-center space-x-2">
                    <span className="text-lg">{lang.flag}</span>
                    <span>{lang.name}</span>
                  </span>
                  {i18n.language === lang.code && (
                    <Check className="w-4 h-4 text-green-600" />
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
        <Button variant="outline" className={`${className} min-w-32`}>
          <Globe className="w-4 h-4 mr-2" />
          <span className="text-lg mr-2">{currentLanguage.flag}</span>
          <span>{currentLanguage.name}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-48 !bg-white dark:!bg-gray-800 border border-gray-200 dark:border-gray-700"
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
                <span className="flex items-center space-x-2">
                  <span className="text-lg">{lang.flag}</span>
                  <span>{lang.name}</span>
                </span>
                {i18n.language === lang.code && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  >
                    <Check className="w-4 h-4 text-green-600" />
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
