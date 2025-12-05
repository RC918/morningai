import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SignupPage from '../SignupPage'
import {
  SIGNUP_FULL_NAME_LABEL,
  SIGNUP_EMAIL_LABEL,
  SIGNUP_PASSWORD_LABEL,
  SIGNUP_CONFIRM_PASSWORD_LABEL,
  SSO_GOOGLE_BUTTON,
  SSO_APPLE_BUTTON,
  SSO_GITHUB_BUTTON,
} from '@/test/i18n-label-patterns'

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
      // Use shared i18n label pattern constant
      const fullNameInput = screen.getByLabelText(SIGNUP_FULL_NAME_LABEL)
      expect(fullNameInput).toBeInTheDocument()
      expect(fullNameInput).toHaveAttribute('type', 'text')
    })

    it('should render email input field', () => {
      renderSignupPage()
      // Use shared i18n label pattern constant
      const emailInput = screen.getByLabelText(SIGNUP_EMAIL_LABEL)
      expect(emailInput).toBeInTheDocument()
      expect(emailInput).toHaveAttribute('type', 'email')
    })

    it('should render password input field', () => {
      renderSignupPage()
      // Use shared i18n label pattern constant (excludes confirmPassword)
      const passwordInput = screen.getByLabelText(SIGNUP_PASSWORD_LABEL)
      expect(passwordInput).toBeInTheDocument()
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('should render confirm password input field', () => {
      renderSignupPage()
      // Use shared i18n label pattern constant
      const confirmPasswordInput = screen.getByLabelText(SIGNUP_CONFIRM_PASSWORD_LABEL)
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
      // Query SSO buttons using shared pattern constants
      const googleButton = screen.getByRole('button', { name: SSO_GOOGLE_BUTTON })
      const appleButton = screen.getByRole('button', { name: SSO_APPLE_BUTTON })
      const githubButton = screen.getByRole('button', { name: SSO_GITHUB_BUTTON })
      
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
      // Use shared i18n label pattern constant
      const fullNameInput = screen.getByLabelText(SIGNUP_FULL_NAME_LABEL)
      
      await user.clear(fullNameInput)
      await user.type(fullNameInput, 'John Doe')
      
      expect(fullNameInput).toHaveValue('John Doe')
    })

    it('should update email field on change', async () => {
      const { user } = renderSignupPage()
      // Use shared i18n label pattern constant
      const emailInput = screen.getByLabelText(SIGNUP_EMAIL_LABEL)
      
      await user.clear(emailInput)
      await user.type(emailInput, 'test@example.com')
      
      expect(emailInput).toHaveValue('test@example.com')
    })

    it('should update password field on change', async () => {
      const { user } = renderSignupPage()
      // Use shared i18n label pattern constant
      const passwordInput = screen.getByLabelText(SIGNUP_PASSWORD_LABEL)
      
      await user.clear(passwordInput)
      await user.type(passwordInput, 'testpassword123')
      
      expect(passwordInput).toHaveValue('testpassword123')
    })

    it('should update confirm password field on change', async () => {
      const { user } = renderSignupPage()
      // Use shared i18n label pattern constant
      const confirmPasswordInput = screen.getByLabelText(SIGNUP_CONFIRM_PASSWORD_LABEL)
      
      await user.clear(confirmPasswordInput)
      await user.type(confirmPasswordInput, 'testpassword123')
      
      expect(confirmPasswordInput).toHaveValue('testpassword123')
    })
  })

  describe('Accessibility', () => {
    it('should have accessible SSO button labels', () => {
      renderSignupPage()
      
      // All SSO buttons should have aria-labels
      const googleButton = screen.getByRole('button', { name: SSO_GOOGLE_BUTTON })
      const appleButton = screen.getByRole('button', { name: SSO_APPLE_BUTTON })
      const githubButton = screen.getByRole('button', { name: SSO_GITHUB_BUTTON })
      
      expect(googleButton).toHaveAccessibleName()
      expect(appleButton).toHaveAccessibleName()
      expect(githubButton).toHaveAccessibleName()
    })

    it('should have proper form structure', () => {
      const { container } = renderSignupPage()
      
      // Form should exist
      const form = container.querySelector('form')
      expect(form).toBeInTheDocument()
      
      // All required inputs should be accessible by label using shared constants
      const fullNameInput = screen.getByLabelText(SIGNUP_FULL_NAME_LABEL)
      const emailInput = screen.getByLabelText(SIGNUP_EMAIL_LABEL)
      const passwordInput = screen.getByLabelText(SIGNUP_PASSWORD_LABEL)
      const confirmPasswordInput = screen.getByLabelText(SIGNUP_CONFIRM_PASSWORD_LABEL)
      
      expect(fullNameInput).toBeInTheDocument()
      expect(emailInput).toBeInTheDocument()
      expect(passwordInput).toBeInTheDocument()
      expect(confirmPasswordInput).toBeInTheDocument()
    })
  })
})
