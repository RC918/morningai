import { useEffect, useState } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { Moon, Sun } from 'lucide-react'
import { AppleButton } from '@/components/ui/apple-button'
import { useTranslation } from 'react-i18next'

export const DarkModeToggle = ({ variant = 'default' }) => {
  const { t } = useTranslation()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const getSystemTheme = () => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return 'light'
  }

  const currentTheme = theme === 'system' ? getSystemTheme() : theme
  const isDark = currentTheme === 'dark'

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark')
  }

  if (variant === 'compact') {
    return (
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center justify-center"
        aria-label={isDark ? t('feedback.switchToLightMode') : t('feedback.switchToDarkMode')}
        style={{ width: '40px', height: '40px' }}
      >
        {isDark ? (
          <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" style={{ width: '20px', height: '20px' }} />
        ) : (
          <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" style={{ width: '20px', height: '20px' }} />
        )}
      </button>
    )
  }

  return (
    <AppleButton
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="rounded-lg flex items-center justify-center"
      aria-label={isDark ? t('feedback.switchToLightMode') : t('feedback.switchToDarkMode')}
      style={{ width: '40px', height: '40px' }}
    >
      {isDark ? (
        <Sun className="w-5 h-5" style={{ width: '20px', height: '20px' }} />
      ) : (
        <Moon className="w-5 h-5" style={{ width: '20px', height: '20px' }} />
      )}
    </AppleButton>
  )
}

export default DarkModeToggle
