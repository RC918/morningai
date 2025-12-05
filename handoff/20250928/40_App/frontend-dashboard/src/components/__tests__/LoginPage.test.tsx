import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../LoginPage'

vi.mock('@/lib/api', () => ({
  default: {
    login: vi.fn()
  }
}))

vi.mock('@/lib/supabaseClient', () => ({
  signInWithOAuth: vi.fn()
}))

vi.mock('@/components/ui/apple-button', () => ({
  AppleButton: ({ children, ...props }: { children: React.ReactNode; [key: string]: any }) => <button {...props}>{children}</button>
}))

vi.mock('@/components/ui/apple-input', () => ({
  AppleInput: ({ label, ...props }: { label?: string; [key: string]: any }) => (
    <div>
      {label && <label htmlFor={props.id}>{label}</label>}
      <input {...props} />
    </div>
  )
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    Link: ({ children, to, ...props }: { children: React.ReactNode; to: string; [key: string]: any }) => <a href={to} {...props}>{children}</a>
  }
})

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: any }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => true
}))

const renderLoginPage = () => {
  const user = userEvent.setup()
  const result = render(
    <BrowserRouter>
      <LoginPage onLogin={vi.fn()} />
    </BrowserRouter>
  )
  return { ...result, user }
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderLoginPage()
      // Submit button exists (text may be i18n key in test environment)
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeInTheDocument()
    })

    it('should render email input field', () => {
      renderLoginPage()
      // Use getByLabelText for email input (label is associated via htmlFor)
      const emailInput = screen.getByLabelText(/email/i)
      expect(emailInput).toBeInTheDocument()
      expect(emailInput).toHaveAttribute('name', 'email')
      expect(emailInput).toHaveAttribute('type', 'email')
    })

    it('should render password input field', () => {
      renderLoginPage()
      // Use getByLabelText for password input (label is associated via htmlFor)
      const passwordInput = screen.getByLabelText(/password/i)
      expect(passwordInput).toBeInTheDocument()
      expect(passwordInput).toHaveAttribute('name', 'password')
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('should render submit button', () => {
      const { container } = renderLoginPage()
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeInTheDocument()
    })

    it('should render SSO buttons', () => {
      renderLoginPage()
      // Query SSO buttons by aria-label (these have proper aria-labels)
      const googleButton = screen.getByRole('button', { name: /google/i })
      const appleButton = screen.getByRole('button', { name: /apple/i })
      const githubButton = screen.getByRole('button', { name: /github/i })
      
      expect(googleButton).toBeInTheDocument()
      expect(appleButton).toBeInTheDocument()
      expect(githubButton).toBeInTheDocument()
    })

    it('should render forgot password link', () => {
      const { container } = renderLoginPage()
      // Link href is reliable even when text is i18n key
      const forgotPasswordLink = container.querySelector('a[href="/forgot-password"]')
      expect(forgotPasswordLink).toBeInTheDocument()
    })
  })

  describe('Form Interaction', () => {
    it('should update email field on change', async () => {
      const { user } = renderLoginPage()
      // Use getByLabelText for better accessibility testing
      const emailInput = screen.getByLabelText(/email/i)
      
      await user.clear(emailInput)
      await user.type(emailInput, 'test@example.com')
      
      expect(emailInput).toHaveValue('test@example.com')
    })

    it('should update password field on change', async () => {
      const { user } = renderLoginPage()
      // Use getByLabelText for better accessibility testing
      const passwordInput = screen.getByLabelText(/password/i)
      
      await user.clear(passwordInput)
      await user.type(passwordInput, 'testpassword')
      
      expect(passwordInput).toHaveValue('testpassword')
    })
  })

  describe('Accessibility', () => {
    it('should have accessible SSO button labels', () => {
      renderLoginPage()
      
      // All SSO buttons should have aria-labels
      const googleButton = screen.getByRole('button', { name: /google/i })
      const appleButton = screen.getByRole('button', { name: /apple/i })
      const githubButton = screen.getByRole('button', { name: /github/i })
      
      expect(googleButton).toHaveAccessibleName()
      expect(appleButton).toHaveAccessibleName()
      expect(githubButton).toHaveAccessibleName()
    })

    it('should have proper form structure', () => {
      const { container } = renderLoginPage()
      
      // Form should exist
      const form = container.querySelector('form')
      expect(form).toBeInTheDocument()
      
      // Email input should be accessible by label and have proper attributes
      const emailInput = screen.getByLabelText(/email/i)
      expect(emailInput).toHaveAttribute('required')
      
      // Password input should be accessible by label and have proper attributes
      const passwordInput = screen.getByLabelText(/password/i)
      expect(passwordInput).toBeInTheDocument()
      expect(passwordInput).toHaveAttribute('required')
    })
  })
})
