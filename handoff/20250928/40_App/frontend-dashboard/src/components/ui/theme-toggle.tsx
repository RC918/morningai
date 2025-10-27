import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@morningai/shared-ui';
import { useTheme, type Theme } from '../../contexts/ThemeContext';

export function ThemeToggle(): React.ReactElement {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}

export function ThemeSelect(): React.ReactElement {
  const { theme, setTheme } = useTheme();

  return (
    <select
      value={theme}
      onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setTheme(e.target.value as Theme)}
      className="bg-background border border-input rounded-md px-3 py-2 text-sm"
    >
      <option value="light">Light</option>
      <option value="dark">Dark</option>
      <option value="system">System</option>
    </select>
  );
}
