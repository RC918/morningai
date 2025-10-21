import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme } from 'next-themes'

export const ThemeToggle = ({ variant = 'default' }) => {
  const { theme, setTheme } = useTheme()
  const isDark = theme === 'dark'

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark')
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
