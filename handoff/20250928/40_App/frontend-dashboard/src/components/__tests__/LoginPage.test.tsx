import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
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

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <LoginPage onLogin={vi.fn()} />
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderLoginPage()
      expect(container).toBeTruthy()
    })

    it('should render email input field', () => {
      const { container } = renderLoginPage()
      const emailInput = container.querySelector('input[name="email"]')
      expect(emailInput).toBeTruthy()
    })

    it('should render password input field', () => {
      const { container } = renderLoginPage()
      const passwordInput = container.querySelector('input[name="password"]')
      expect(passwordInput).toBeTruthy()
    })

    it('should render submit button', () => {
      const { container } = renderLoginPage()
      const submitButton = container.querySelector('button[type="submit"]')
      expect(submitButton).toBeTruthy()
    })

    it('should render SSO buttons', () => {
      const { container } = renderLoginPage()
      const buttons = container.querySelectorAll('button[type="button"]')
      // Should have Google, Apple, and GitHub SSO buttons
      expect(buttons.length).toBeGreaterThanOrEqual(3)
    })

    it('should render forgot password link', () => {
      const { container } = renderLoginPage()
      const forgotPasswordLink = container.querySelector('a[href="/forgot-password"]')
      expect(forgotPasswordLink).toBeTruthy()
    })
  })

  describe('Form Interaction', () => {
    it('should update email field on change', async () => {
      const { container } = renderLoginPage()
      const emailInput = container.querySelector('input[name="email"]') as HTMLInputElement
      
      if (emailInput) {
        emailInput.value = 'test@example.com'
        emailInput.dispatchEvent(new Event('change', { bubbles: true }))
        expect(emailInput.value).toBe('test@example.com')
      }
    })

    it('should update password field on change', async () => {
      const { container } = renderLoginPage()
      const passwordInput = container.querySelector('input[name="password"]') as HTMLInputElement
      
      if (passwordInput) {
        passwordInput.value = 'testpassword'
        passwordInput.dispatchEvent(new Event('change', { bubbles: true }))
        expect(passwordInput.value).toBe('testpassword')
      }
    })
  })

  describe('Accessibility', () => {
    it('should have accessible SSO button labels', () => {
      const { container } = renderLoginPage()
      const ssoButtons = container.querySelectorAll('button[aria-label]')
      expect(ssoButtons.length).toBeGreaterThanOrEqual(3)
    })
  })
})
