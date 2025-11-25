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
        variant="outline"
        size="icon-sm"
        onClick={toggleTheme}
        haptic="light"
        className="text-neutral-900 dark:text-neutral-50 bg-white/80 dark:bg-neutral-800/80 hover:bg-neutral-50 dark:hover:bg-neutral-700"
        aria-label={isDark ? t('feedback.switchToLightMode') : t('feedback.switchToDarkMode')}
      >
        {isDark ? (
          <Sun className="w-5 h-5" />
        ) : (
          <Moon className="w-5 h-5" />
        )}
      </AppleButton>
    )
  }

  return (
    <AppleButton
      variant="outline"
      size="icon"
      onClick={toggleTheme}
      haptic="light"
      className="text-neutral-900 dark:text-neutral-50 bg-white/80 dark:bg-neutral-800/80 hover:bg-neutral-50 dark:hover:bg-neutral-700"
      aria-label={isDark ? t('feedback.switchToLightMode') : t('feedback.switchToDarkMode')}
    >
      {isDark ? (
        <Sun className="w-5 h-5" />
      ) : (
        <Moon className="w-5 h-5" />
      )}
    </AppleButton>
  )
}

export default DarkModeToggle
