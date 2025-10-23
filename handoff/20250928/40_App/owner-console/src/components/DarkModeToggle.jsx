import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTranslation } from 'react-i18next'

export const DarkModeToggle = ({ variant = 'default' }) => {
  const { t } = useTranslation()
  const { theme, setTheme, systemTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const currentTheme = theme === 'system' ? systemTheme : theme
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
    <Button
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
    </Button>
  )
}

export default DarkModeToggle
