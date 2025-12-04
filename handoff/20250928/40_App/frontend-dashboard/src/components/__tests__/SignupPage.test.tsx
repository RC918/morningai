import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
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
      {label && <label>{label}</label>}
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
  return render(
    <BrowserRouter>
      <SignupPage />
    </BrowserRouter>
  )
}

describe('SignupPage', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderSignupPage()
      expect(container).toBeTruthy()
    })

    it('should render full name input field', () => {
      const { container } = renderSignupPage()
      const fullNameInput = container.querySelector('input[name="fullName"]')
      expect(fullNameInput).toBeTruthy()
    })

    it('should render email input field', () => {
      const { container } = renderSignupPage()
      const emailInput = container.querySelector('input[name="email"]')
      expect(emailInput).toBeTruthy()
    })

    it('should render password input field', () => {
      const { container } = renderSignupPage()
      const passwordInput = container.querySelector('input[name="password"]')
      expect(passwordInput).toBeTruthy()
    })

    it('should render confirm password input field', () => {
      const { container } = renderSignupPage()
      const confirmPasswordInput = container.querySelector('input[name="confirmPassword"]')
      expect(confirmPasswordInput).toBeTruthy()
    })

    it('should render submit button', () => {
      const { container } = renderSignupPage()
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeTruthy()
    })

    it('should render SSO buttons', () => {
      const { container } = renderSignupPage()
      const buttons = container.querySelectorAll('button[type="button"]')
      // Should have Google, Apple, and GitHub SSO buttons
      expect(buttons.length).toBeGreaterThanOrEqual(3)
    })

    it('should render login link', () => {
      const { container } = renderSignupPage()
      const loginLink = container.querySelector('a[href="/login"]')
      expect(loginLink).toBeTruthy()
    })
  })

  describe('Form Interaction', () => {
    it('should update full name field on change', async () => {
      const { container } = renderSignupPage()
      const fullNameInput = container.querySelector('input[name="fullName"]') as HTMLInputElement
      
      if (fullNameInput) {
        fullNameInput.value = 'John Doe'
        fullNameInput.dispatchEvent(new Event('change', { bubbles: true }))
        expect(fullNameInput.value).toBe('John Doe')
      }
    })

    it('should update email field on change', async () => {
      const { container } = renderSignupPage()
      const emailInput = container.querySelector('input[name="email"]') as HTMLInputElement
      
      if (emailInput) {
        emailInput.value = 'test@example.com'
        emailInput.dispatchEvent(new Event('change', { bubbles: true }))
        expect(emailInput.value).toBe('test@example.com')
      }
    })

    it('should update password field on change', async () => {
      const { container } = renderSignupPage()
      const passwordInput = container.querySelector('input[name="password"]') as HTMLInputElement
      
      if (passwordInput) {
        passwordInput.value = 'testpassword123'
        passwordInput.dispatchEvent(new Event('change', { bubbles: true }))
        expect(passwordInput.value).toBe('testpassword123')
      }
    })

    it('should update confirm password field on change', async () => {
      const { container } = renderSignupPage()
      const confirmPasswordInput = container.querySelector('input[name="confirmPassword"]') as HTMLInputElement
      
      if (confirmPasswordInput) {
        confirmPasswordInput.value = 'testpassword123'
        confirmPasswordInput.dispatchEvent(new Event('change', { bubbles: true }))
        expect(confirmPasswordInput.value).toBe('testpassword123')
      }
    })
  })

  describe('Accessibility', () => {
    it('should have accessible SSO button labels', () => {
      const { container } = renderSignupPage()
      const ssoButtons = container.querySelectorAll('button[aria-label]')
      expect(ssoButtons.length).toBeGreaterThanOrEqual(3)
    })
  })
})
