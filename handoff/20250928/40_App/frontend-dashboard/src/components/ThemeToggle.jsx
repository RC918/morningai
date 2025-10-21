import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

export const ThemeToggle = ({ variant = 'default' }) => {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark)
    
    setIsDark(shouldBeDark)
    updateTheme(shouldBeDark)
  }, [])

  const updateTheme = (dark) => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
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
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleTheme}
        className="w-9 h-9 rounded-lg"
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {isDark ? (
          <Sun className="w-5 h-5 text-gray-300 hover:text-white transition-colors" />
        ) : (
          <Moon className="w-5 h-5 text-gray-600 hover:text-gray-900 transition-colors" />
        )}
      </Button>
    )
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={toggleTheme}
      className="gap-2"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? (
        <>
          <Sun className="w-4 h-4" />
          <span>Light Mode</span>
        </>
      ) : (
        <>
          <Moon className="w-4 h-4" />
          <span>Dark Mode</span>
        </>
      )}
    </Button>
  )
}
