import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

export const DarkModeToggle = ({ variant = 'default' }) => {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark)
    
    setIsDark(shouldBeDark)
    updateTheme(shouldBeDark)
  }, [])

  const updateTheme = (dark) => {
    const root = document.documentElement
    if (dark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  const toggleTheme = () => {
    const newIsDark = !isDark
    setIsDark(newIsDark)
    updateTheme(newIsDark)
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light')
  }

  if (variant === 'compact') {
    return (
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center justify-center"
        aria-label={isDark ? '切換到淺色模式' : '切換到深色模式'}
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
      aria-label={isDark ? '切換到淺色模式' : '切換到深色模式'}
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
