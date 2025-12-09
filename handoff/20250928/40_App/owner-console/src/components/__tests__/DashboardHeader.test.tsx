import type { ReactNode } from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

// Mock all external dependencies before importing the component
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key,
  }),
}))

vi.mock('@morningai/shared-ui', () => ({
  Button: ({ children, ...props }: { children: ReactNode; [key: string]: unknown }) => (
    <button {...props}>{children}</button>
  ),
  Avatar: ({ children, className }: { children: ReactNode; className?: string }) => (
    <div className={className} data-testid="avatar">{children}</div>
  ),
  AvatarImage: ({ src, alt }: { src?: string; alt?: string }) => (
    src ? <img src={src} alt={alt} data-testid="avatar-image" /> : null
  ),
  AvatarFallback: ({ children, className }: { children: ReactNode; className?: string }) => (
    <span className={className} data-testid="avatar-fallback">{children}</span>
  ),
  DropdownMenu: ({ children }: { children: ReactNode }) => (
    <div data-testid="dropdown-menu">{children}</div>
  ),
  DropdownMenuTrigger: ({ children, asChild }: { children: ReactNode; asChild?: boolean }) => (
    <div data-testid="dropdown-trigger">{asChild ? children : <button>{children}</button>}</div>
  ),
  DropdownMenuContent: ({ children, align, className }: { children: ReactNode; align?: string; className?: string }) => (
    <div data-testid="dropdown-content" data-align={align} className={className} role="menu">{children}</div>
  ),
  DropdownMenuItem: ({ children, onClick, className, asChild }: { children: ReactNode; onClick?: () => void; className?: string; asChild?: boolean }) => (
    <div 
      data-testid="dropdown-item" 
      onClick={onClick} 
      className={className}
      role="menuitem"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick?.()
        }
      }}
    >
      {children}
    </div>
  ),
  DropdownMenuSeparator: () => <hr data-testid="dropdown-separator" />,
  DropdownMenuLabel: ({ children, className }: { children: ReactNode; className?: string }) => (
    <div data-testid="dropdown-label" className={className}>{children}</div>
  ),
}))

vi.mock('../LanguageSwitcher', () => ({
  LanguageSwitcher: ({ variant, className }: { variant?: string; className?: string }) => (
    <div data-testid="language-switcher" data-variant={variant} className={className} />
  ),
}))

// Import component after all mocks are set up
import DashboardHeader from '../DashboardHeader'

const defaultUser = {
  name: 'Test User',
  email: 'test@example.com',
  role: 'Admin',
  avatar: 'https://example.com/avatar.jpg',
}

const renderDashboardHeader = (props = {}) => {
  const defaultProps = {
    user: defaultUser,
    title: 'Dashboard',
    subtitle: 'Welcome back',
    notificationCount: 0,
    onLogout: vi.fn(),
  }
  const user = userEvent.setup()
  const result = render(
    <MemoryRouter>
      <DashboardHeader {...defaultProps} {...props} />
    </MemoryRouter>
  )
  return { ...result, user, ...defaultProps, ...props }
}

describe('DashboardHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderDashboardHeader()
      expect(screen.getByRole('banner')).toBeInTheDocument()
    })

    it('should render the title', () => {
      renderDashboardHeader({ title: 'My Dashboard' })
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('My Dashboard')
    })

    it('should render the subtitle when provided', () => {
      renderDashboardHeader({ subtitle: 'Welcome back, user!' })
      expect(screen.getByText('Welcome back, user!')).toBeInTheDocument()
    })

    it('should not render subtitle when not provided', () => {
      renderDashboardHeader({ subtitle: undefined })
      expect(screen.queryByText('Welcome back')).not.toBeInTheDocument()
    })

    it('should render search input', () => {
      renderDashboardHeader()
      const searchInput = screen.getByPlaceholderText('Search...')
      expect(searchInput).toBeInTheDocument()
      expect(searchInput).toHaveAttribute('type', 'text')
    })

    it('should render help button with aria-label', () => {
      renderDashboardHeader()
      const helpButton = screen.getByLabelText('header.help')
      expect(helpButton).toBeInTheDocument()
    })

    it('should render notifications button with aria-label', () => {
      renderDashboardHeader()
      const notificationsButton = screen.getByLabelText('header.notifications')
      expect(notificationsButton).toBeInTheDocument()
    })

    it('should render language switcher', () => {
      renderDashboardHeader()
      const languageSwitcher = screen.getByTestId('language-switcher')
      expect(languageSwitcher).toBeInTheDocument()
      expect(languageSwitcher).toHaveAttribute('data-variant', 'compact')
    })

    it('should render user avatar', () => {
      renderDashboardHeader()
      const avatar = screen.getByTestId('avatar')
      expect(avatar).toBeInTheDocument()
    })

    it('should render user name and role', () => {
      renderDashboardHeader({ user: { name: 'John Doe', role: 'Manager' } })
      // User name appears in both header and dropdown label
      const userNames = screen.getAllByText('John Doe')
      expect(userNames.length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('Manager')).toBeInTheDocument()
    })

    it('should render default user name when not provided', () => {
      renderDashboardHeader({ user: {} })
      // Default user text appears in both header and dropdown label
      const defaultUsers = screen.getAllByText('header.defaultUser')
      expect(defaultUsers.length).toBeGreaterThanOrEqual(1)
    })

    it('should render avatar fallback with first letter of name', () => {
      renderDashboardHeader({ user: { name: 'Alice' } })
      const fallback = screen.getByTestId('avatar-fallback')
      expect(fallback).toHaveTextContent('A')
    })

    it('should render avatar fallback with U when no name', () => {
      renderDashboardHeader({ user: {} })
      const fallback = screen.getByTestId('avatar-fallback')
      expect(fallback).toHaveTextContent('U')
    })
  })

  describe('Notification Badge', () => {
    it('should not show notification badge when count is 0', () => {
      renderDashboardHeader({ notificationCount: 0 })
      const notificationsButton = screen.getByLabelText('header.notifications')
      const badge = notificationsButton.querySelector('.bg-pink-500')
      expect(badge).not.toBeInTheDocument()
    })

    it('should show notification badge when count is greater than 0', () => {
      renderDashboardHeader({ notificationCount: 5 })
      const notificationsButton = screen.getByLabelText('header.notifications')
      const badge = notificationsButton.querySelector('.bg-pink-500')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Search Input', () => {
    it('should update search query on input change', async () => {
      renderDashboardHeader()
      const user = userEvent.setup()
      const searchInput = screen.getByPlaceholderText('Search...')

      await user.type(searchInput, 'test query')

      await waitFor(() => {
        expect(searchInput).toHaveValue('test query')
      })
    })

    it('should clear search query', async () => {
      renderDashboardHeader()
      const user = userEvent.setup()
      const searchInput = screen.getByPlaceholderText('Search...')

      await user.type(searchInput, 'test query')
      await waitFor(() => {
        expect(searchInput).toHaveValue('test query')
      })
      await user.clear(searchInput)

      await waitFor(() => {
        expect(searchInput).toHaveValue('')
      })
    })
  })

  describe('User Dropdown Menu', () => {
    it('should render dropdown menu trigger with user menu aria-label', () => {
      renderDashboardHeader()
      const trigger = screen.getByLabelText('User menu')
      expect(trigger).toBeInTheDocument()
    })

    it('should render dropdown menu content', () => {
      renderDashboardHeader()
      const content = screen.getByTestId('dropdown-content')
      expect(content).toBeInTheDocument()
      expect(content).toHaveAttribute('data-align', 'end')
    })

    it('should render user info in dropdown label', () => {
      renderDashboardHeader({ user: { name: 'Test User', email: 'test@example.com' } })
      const label = screen.getByTestId('dropdown-label')
      expect(label).toBeInTheDocument()
      expect(within(label).getByText('Test User')).toBeInTheDocument()
      expect(within(label).getByText('test@example.com')).toBeInTheDocument()
    })

    it('should render Settings menu item with link to /settings', () => {
      renderDashboardHeader()
      const settingsLink = screen.getByRole('link', { name: /nav\.settings/i })
      expect(settingsLink).toBeInTheDocument()
      expect(settingsLink).toHaveAttribute('href', '/settings')
    })

    it('should render Logout menu item', () => {
      renderDashboardHeader()
      const menuItems = screen.getAllByTestId('dropdown-item')
      const logoutItem = menuItems.find(item => item.textContent?.includes('nav.logout'))
      expect(logoutItem).toBeInTheDocument()
    })

    it('should call onLogout when logout is clicked', async () => {
      const onLogout = vi.fn()
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <DashboardHeader 
            user={defaultUser}
            title="Dashboard"
            notificationCount={0}
            onLogout={onLogout}
          />
        </MemoryRouter>
      )
      
      const menuItems = screen.getAllByTestId('dropdown-item')
      const logoutItem = menuItems.find(item => item.textContent?.includes('nav.logout'))
      
      if (logoutItem) {
        await user.click(logoutItem)
        expect(onLogout).toHaveBeenCalledTimes(1)
      }
    })

    it('should have error styling on logout button', () => {
      renderDashboardHeader()
      const menuItems = screen.getAllByTestId('dropdown-item')
      const logoutItem = menuItems.find(item => item.textContent?.includes('nav.logout'))
      expect(logoutItem).toHaveClass('text-error-600')
    })
  })

  describe('Keyboard Navigation', () => {
    it('should have focusable user menu trigger', () => {
      renderDashboardHeader()
      const trigger = screen.getByLabelText('User menu')
      expect(trigger).toHaveAttribute('class', expect.stringContaining('focus:outline-none'))
      expect(trigger).toHaveAttribute('class', expect.stringContaining('focus:ring-2'))
    })

    it('should have focusable search input', () => {
      renderDashboardHeader()
      const searchInput = screen.getByPlaceholderText('Search...')
      
      // Search input should have focus styles defined
      const className = searchInput.getAttribute('class') || ''
      expect(className).toContain('focus:outline-none')
      expect(className).toContain('focus:ring-2')
    })

    it('should trigger logout on Enter key', async () => {
      const onLogout = vi.fn()
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <DashboardHeader 
            user={defaultUser}
            title="Dashboard"
            notificationCount={0}
            onLogout={onLogout}
          />
        </MemoryRouter>
      )
      
      const menuItems = screen.getAllByTestId('dropdown-item')
      const logoutItem = menuItems.find(item => item.textContent?.includes('nav.logout'))
      
      if (logoutItem) {
        logoutItem.focus()
        await user.keyboard('{Enter}')
        expect(onLogout).toHaveBeenCalledTimes(1)
      }
    })

    it('should trigger logout on Space key', async () => {
      const onLogout = vi.fn()
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <DashboardHeader 
            user={defaultUser}
            title="Dashboard"
            notificationCount={0}
            onLogout={onLogout}
          />
        </MemoryRouter>
      )
      
      const menuItems = screen.getAllByTestId('dropdown-item')
      const logoutItem = menuItems.find(item => item.textContent?.includes('nav.logout'))
      
      if (logoutItem) {
        logoutItem.focus()
        await user.keyboard(' ')
        expect(onLogout).toHaveBeenCalledTimes(1)
      }
    })

    it('should have menu items with role="menuitem"', () => {
      renderDashboardHeader()
      const menuItems = screen.getAllByRole('menuitem')
      expect(menuItems.length).toBeGreaterThan(0)
    })

    it('should have dropdown content with role="menu"', () => {
      renderDashboardHeader()
      const menu = screen.getByRole('menu')
      expect(menu).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper header landmark', () => {
      renderDashboardHeader()
      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('should have accessible buttons with aria-labels', () => {
      renderDashboardHeader()
      
      const helpButton = screen.getByLabelText('header.help')
      const notificationsButton = screen.getByLabelText('header.notifications')
      const userMenuButton = screen.getByLabelText('User menu')
      
      expect(helpButton).toBeInTheDocument()
      expect(notificationsButton).toBeInTheDocument()
      expect(userMenuButton).toBeInTheDocument()
    })

    it('should have proper heading hierarchy', () => {
      renderDashboardHeader({ title: 'Dashboard Title' })
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('Dashboard Title')
    })

    it('should have avatar with proper alt text', () => {
      renderDashboardHeader({ user: { name: 'John Doe', avatar: 'https://example.com/avatar.jpg' } })
      const avatarImage = screen.getByTestId('avatar-image')
      expect(avatarImage).toHaveAttribute('alt', "John Doe's avatar")
    })

    it('should have default avatar alt text when no user name', () => {
      renderDashboardHeader({ user: { avatar: 'https://example.com/avatar.jpg' } })
      const avatarImage = screen.getByTestId('avatar-image')
      expect(avatarImage).toHaveAttribute('alt', 'User avatar')
    })
  })

  describe('Dropdown Menu Styling', () => {
    it('should have proper dropdown content styling', () => {
      renderDashboardHeader()
      const content = screen.getByTestId('dropdown-content')
      expect(content).toHaveClass('w-56')
      expect(content).toHaveClass('rounded-xl')
      expect(content).toHaveClass('border-0')
      expect(content).toHaveClass('bg-white')
      expect(content).toHaveClass('shadow-lg')
    })
  })

  describe('Props', () => {
    it('should use default title from translation when not provided', () => {
      renderDashboardHeader({ title: undefined })
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('dashboard.title')
    })

    it('should handle missing user gracefully', () => {
      renderDashboardHeader({ user: undefined })
      // Default user text appears in both header and dropdown label
      const defaultUsers = screen.getAllByText('header.defaultUser')
      expect(defaultUsers.length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('header.defaultRole')).toBeInTheDocument()
    })

    it('should handle user with only partial data', () => {
      renderDashboardHeader({ user: { name: 'Partial User' } })
      // User name appears in both header and dropdown label
      const userNames = screen.getAllByText('Partial User')
      expect(userNames.length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('header.defaultRole')).toBeInTheDocument()
    })
  })
})
