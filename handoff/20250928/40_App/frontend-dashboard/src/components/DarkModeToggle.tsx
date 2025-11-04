import React, { useEffect, useState } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { Moon, Sun } from 'lucide-react'
import { AppleButton } from '@/components/ui/apple-button'
import { useTranslation } from 'react-i18next'

interface DarkModeToggleProps {
  variant?: 'default' | 'compact'
}

export const DarkModeToggle = ({ variant = 'default' }: DarkModeToggleProps): React.ReactElement | null => {
  const { t } = useTranslation()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState<boolean>(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const getSystemTheme = (): 'dark' | 'light' => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return 'light'
  }

  const currentTheme: string = theme === 'system' ? getSystemTheme() : theme
  const isDark: boolean = currentTheme === 'dark'

  const toggleTheme = (): void => {
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
          <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" style={{ width: '20px', height: '20px' }} aria-hidden="true" />
        ) : (
          <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" style={{ width: '20px', height: '20px' }} aria-hidden="true" />
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
        <Sun className="w-5 h-5" style={{ width: '20px', height: '20px' }} aria-hidden="true" />
      ) : (
        <Moon className="w-5 h-5" style={{ width: '20px', height: '20px' }} aria-hidden="true" />
      )}
    </AppleButton>
  )
}

export default DarkModeToggle
