import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun } from 'lucide-react'
import { AppleButton } from '@/components/apple/apple-button'
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
      <AppleButton
        variant="ghost"
        size="icon-sm"
        onClick={toggleTheme}
        haptic="light"
        aria-label={isDark ? t('feedback.switchToLightMode') : t('feedback.switchToDarkMode')}
      >
        {isDark ? (
          <Sun className="w-5 h-5 text-neutral-900 dark:text-neutral-50" />
        ) : (
          <Moon className="w-5 h-5 text-neutral-900 dark:text-neutral-50" />
        )}
      </AppleButton>
    )
  }

  return (
    <AppleButton
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      haptic="light"
      aria-label={isDark ? t('feedback.switchToLightMode') : t('feedback.switchToDarkMode')}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-neutral-900 dark:text-neutral-50" />
      ) : (
        <Moon className="w-5 h-5 text-neutral-900 dark:text-neutral-50" />
      )}
    </AppleButton>
  )
}

export default DarkModeToggle
