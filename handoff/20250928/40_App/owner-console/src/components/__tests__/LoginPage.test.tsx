import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock all external dependencies before importing the component
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key,
  }),
}))

vi.mock('@morningai/shared-ui', () => ({
  Card: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => (
    <div {...props}>{children}</div>
  ),
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardDescription: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  Alert: ({ children }: { children: React.ReactNode }) => <div role="alert">{children}</div>,
  AlertDescription: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}))

vi.mock('@/components/apple/apple-button', () => ({
  AppleButton: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => (
    <button {...props}>{children}</button>
  ),
}))

vi.mock('@/components/apple/apple-input', () => ({
  AppleInput: ({ label, ...props }: { label?: string; [key: string]: unknown }) => (
    <div>
      {label && <label htmlFor={props.id as string}>{label}</label>}
      <input {...props} />
    </div>
  ),
}))

vi.mock('../LanguageSwitcher', () => ({
  LanguageSwitcher: () => <div data-testid="language-switcher" />,
}))

vi.mock('../2fa/TwoFactorVerify', () => ({
  TwoFactorVerify: ({ open }: { open: boolean }) => (
    open ? <div data-testid="2fa-verify-dialog" /> : null
  ),
}))

vi.mock('../2fa/TwoFactorEnroll', () => ({
  TwoFactorEnroll: ({ open }: { open: boolean }) => (
    open ? <div data-testid="2fa-enroll-dialog" /> : null
  ),
}))

vi.mock('@/lib/redirect-security', () => ({
  sanitizeRedirect: (path: string) => path,
}))

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Import component after all mocks are set up
import LoginPage from '../LoginPage'

const renderLoginPage = (props = {}) => {
  const defaultProps = {
    onLogin: vi.fn(),
    onRefreshUser: vi.fn(),
    redirectPath: '/',
  }
  const user = userEvent.setup()
  const result = render(<LoginPage {...defaultProps} {...props} />)
  return { ...result, user, ...defaultProps, ...props }
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderLoginPage()
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeInTheDocument()
    })

    it('should render email input field', () => {
      renderLoginPage()
      const emailInput = screen.getByLabelText('Email')
      expect(emailInput).toBeInTheDocument()
      expect(emailInput).toHaveAttribute('name', 'email')
      expect(emailInput).toHaveAttribute('type', 'email')
    })

    it('should render password input field', () => {
      renderLoginPage()
      const passwordInput = screen.getByLabelText('auth.login.password')
      expect(passwordInput).toBeInTheDocument()
      expect(passwordInput).toHaveAttribute('name', 'password')
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('should render submit button', () => {
      const { container } = renderLoginPage()
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeInTheDocument()
    })

    it('should render language switcher', () => {
      renderLoginPage()
      const languageSwitcher = screen.getByTestId('language-switcher')
      expect(languageSwitcher).toBeInTheDocument()
    })

    it('should render login card with test id', () => {
      renderLoginPage()
      const loginCard = screen.getByTestId('login-card')
      expect(loginCard).toBeInTheDocument()
    })

    it('should render app logo', () => {
      renderLoginPage()
      const logo = screen.getByAltText('Morning AI')
      expect(logo).toBeInTheDocument()
    })

    it('should render development account info', () => {
      renderLoginPage()
      const devAccountSection = screen.getByText('Development Account')
      expect(devAccountSection).toBeInTheDocument()
    })
  })

  describe('Form Interaction', () => {
    it('should update email field on change', async () => {
      const { user } = renderLoginPage()
      const emailInput = screen.getByLabelText('Email')

      await user.clear(emailInput)
      await user.type(emailInput, 'test@example.com')

      expect(emailInput).toHaveValue('test@example.com')
    })

    it('should update password field on change', async () => {
      const { user } = renderLoginPage()
      const passwordInput = screen.getByLabelText('auth.login.password')

      await user.clear(passwordInput)
      await user.type(passwordInput, 'testpassword')

      expect(passwordInput).toHaveValue('testpassword')
    })

    it('should call onLogin when form is submitted', async () => {
      const onLogin = vi.fn().mockResolvedValue({})
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(onLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        })
      })
    })

    it('should disable submit button while loading', async () => {
      const onLogin = vi.fn().mockImplementation(() => new Promise(() => {}))
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
    })
  })

  describe('2FA Flow', () => {
    it('should show 2FA verify dialog when requires_2fa is true', async () => {
      const onLogin = vi.fn().mockResolvedValue({ requires_2fa: true })
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByTestId('2fa-verify-dialog')).toBeInTheDocument()
      })
    })

    it('should show 2FA verify dialog when next_step is challenge_2fa', async () => {
      const onLogin = vi.fn().mockResolvedValue({
        next_step: 'challenge_2fa',
        tmp_login_token: 'test-token',
      })
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByTestId('2fa-verify-dialog')).toBeInTheDocument()
      })
    })

    it('should show 2FA enroll dialog when next_step is enroll_2fa', async () => {
      const onLogin = vi.fn().mockResolvedValue({
        next_step: 'enroll_2fa',
        tmp_login_token: 'test-token',
      })
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByTestId('2fa-enroll-dialog')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error message when login fails', async () => {
      const onLogin = vi.fn().mockRejectedValue(new Error('Invalid credentials'))
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'wrongpassword')
      await user.click(submitButton)

      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toBeInTheDocument()
      })
    })

    it('should clear error when form is resubmitted', async () => {
      const onLogin = vi.fn()
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockResolvedValueOnce({})
      const { user } = renderLoginPage({ onLogin })

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('auth.login.password')
      const submitButton = screen.getByRole('button', { name: /auth\.login\.loginButton/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'wrongpassword')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      await user.clear(passwordInput)
      await user.type(passwordInput, 'correctpassword')
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper form structure', () => {
      const { container } = renderLoginPage()

      const form = container.querySelector('form')
      expect(form).toBeInTheDocument()

      const emailInput = screen.getByLabelText('Email')
      expect(emailInput).toHaveAttribute('required')

      const passwordInput = screen.getByLabelText('auth.login.password')
      expect(passwordInput).toHaveAttribute('required')
    })

    it('should have accessible input labels', () => {
      renderLoginPage()

      const emailInput = screen.getByLabelText('Email')
      expect(emailInput).toBeInTheDocument()

      const passwordInput = screen.getByLabelText('auth.login.password')
      expect(passwordInput).toBeInTheDocument()
    })
  })

  describe('Props', () => {
    it('should accept custom redirectPath', () => {
      const { container } = renderLoginPage({ redirectPath: '/dashboard' })
      expect(container).toBeInTheDocument()
    })

    it('should accept onRefreshUser callback', () => {
      const onRefreshUser = vi.fn()
      const { container } = renderLoginPage({ onRefreshUser })
      expect(container).toBeInTheDocument()
    })
  })
})
