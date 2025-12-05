import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SignupPage from '../SignupPage'

vi.mock('@/lib/supabaseClient', () => ({
  supabase: {
    auth: {
      signUp: vi.fn()
    }
  },
  signInWithOAuth: vi.fn()
}))

vi.mock('@/components/ui/apple-button', () => ({
  AppleButton: ({ children, ...props }: { children: React.ReactNode; [key: string]: any }) => <button {...props}>{children}</button>
}))

vi.mock('@/components/ui/apple-input', () => ({
  AppleInput: ({ label, ...props }: { label: string; [key: string]: any }) => (
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

const renderSignupPage = () => {
  const user = userEvent.setup()
  const result = render(
    <BrowserRouter>
      <SignupPage />
    </BrowserRouter>
  )
  return { ...result, user }
}

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderSignupPage()
      // Submit button exists (text may be i18n key in test environment)
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeInTheDocument()
    })

    it('should render full name input field', () => {
      renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const fullNameInput = screen.getByLabelText(/^auth\.signup\.fullName$|^Full Name$|^姓名$/i)
      expect(fullNameInput).toBeInTheDocument()
      expect(fullNameInput).toHaveAttribute('type', 'text')
    })

    it('should render email input field', () => {
      renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const emailInput = screen.getByLabelText(/^auth\.signup\.email$|^Email$|^電子郵件$/i)
      expect(emailInput).toBeInTheDocument()
      expect(emailInput).toHaveAttribute('type', 'email')
    })

    it('should render password input field', () => {
      renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching (excludes confirmPassword)
      const passwordInput = screen.getByLabelText(/^auth\.signup\.password$|^Password$|^密碼$/i)
      expect(passwordInput).toBeInTheDocument()
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('should render confirm password input field', () => {
      renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const confirmPasswordInput = screen.getByLabelText(/^auth\.signup\.confirmPassword$|^Confirm Password$|^確認密碼$/i)
      expect(confirmPasswordInput).toBeInTheDocument()
      expect(confirmPasswordInput).toHaveAttribute('type', 'password')
    })

    it('should render submit button', () => {
      const { container } = renderSignupPage()
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeInTheDocument()
    })

    it('should render SSO buttons', () => {
      renderSignupPage()
      // Query SSO buttons by aria-label (these have proper aria-labels)
      const googleButton = screen.getByRole('button', { name: /google/i })
      const appleButton = screen.getByRole('button', { name: /apple/i })
      const githubButton = screen.getByRole('button', { name: /github/i })
      
      expect(googleButton).toBeInTheDocument()
      expect(appleButton).toBeInTheDocument()
      expect(githubButton).toBeInTheDocument()
    })

    it('should render login link', () => {
      const { container } = renderSignupPage()
      // Link href is reliable even when text is i18n key
      const loginLink = container.querySelector('a[href="/login"]')
      expect(loginLink).toBeInTheDocument()
    })
  })

  describe('Form Interaction', () => {
    it('should update full name field on change', async () => {
      const { user } = renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const fullNameInput = screen.getByLabelText(/^auth\.signup\.fullName$|^Full Name$|^姓名$/i)
      
      await user.clear(fullNameInput)
      await user.type(fullNameInput, 'John Doe')
      
      expect(fullNameInput).toHaveValue('John Doe')
    })

    it('should update email field on change', async () => {
      const { user } = renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const emailInput = screen.getByLabelText(/^auth\.signup\.email$|^Email$|^電子郵件$/i)
      
      await user.clear(emailInput)
      await user.type(emailInput, 'test@example.com')
      
      expect(emailInput).toHaveValue('test@example.com')
    })

    it('should update password field on change', async () => {
      const { user } = renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const passwordInput = screen.getByLabelText(/^auth\.signup\.password$|^Password$|^密碼$/i)
      
      await user.clear(passwordInput)
      await user.type(passwordInput, 'testpassword123')
      
      expect(passwordInput).toHaveValue('testpassword123')
    })

    it('should update confirm password field on change', async () => {
      const { user } = renderSignupPage()
      // Use getByLabelText with anchored regex for precise i18n matching
      const confirmPasswordInput = screen.getByLabelText(/^auth\.signup\.confirmPassword$|^Confirm Password$|^確認密碼$/i)
      
      await user.clear(confirmPasswordInput)
      await user.type(confirmPasswordInput, 'testpassword123')
      
      expect(confirmPasswordInput).toHaveValue('testpassword123')
    })
  })

  describe('Accessibility', () => {
    it('should have accessible SSO button labels', () => {
      renderSignupPage()
      
      // All SSO buttons should have aria-labels
      const googleButton = screen.getByRole('button', { name: /google/i })
      const appleButton = screen.getByRole('button', { name: /apple/i })
      const githubButton = screen.getByRole('button', { name: /github/i })
      
      expect(googleButton).toHaveAccessibleName()
      expect(appleButton).toHaveAccessibleName()
      expect(githubButton).toHaveAccessibleName()
    })

    it('should have proper form structure', () => {
      const { container } = renderSignupPage()
      
      // Form should exist
      const form = container.querySelector('form')
      expect(form).toBeInTheDocument()
      
      // All required inputs should be accessible by label with anchored regex
      const fullNameInput = screen.getByLabelText(/^auth\.signup\.fullName$|^Full Name$|^姓名$/i)
      const emailInput = screen.getByLabelText(/^auth\.signup\.email$|^Email$|^電子郵件$/i)
      const passwordInput = screen.getByLabelText(/^auth\.signup\.password$|^Password$|^密碼$/i)
      const confirmPasswordInput = screen.getByLabelText(/^auth\.signup\.confirmPassword$|^Confirm Password$|^確認密碼$/i)
      
      expect(fullNameInput).toBeInTheDocument()
      expect(emailInput).toBeInTheDocument()
      expect(passwordInput).toBeInTheDocument()
      expect(confirmPasswordInput).toBeInTheDocument()
    })
  })
})
