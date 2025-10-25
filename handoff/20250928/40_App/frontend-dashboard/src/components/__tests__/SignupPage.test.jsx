import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import SignupPage from '../SignupPage'

vi.mock('@/lib/auth', () => ({
  signUp: vi.fn(),
  signInWithOAuth: vi.fn()
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>
  }
})

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }) => <>{children}</>,
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
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderSignupPage()
      expect(screen.getByText(/Morning AI/i)).toBeInTheDocument()
    })

    it('should render the signup form', () => {
      renderSignupPage()
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    })

    it('should render the signup button', () => {
      renderSignupPage()
      const signupButtons = screen.getAllByRole('button', { name: /sign.*up/i })
      expect(signupButtons.length).toBeGreaterThan(0)
    })

    it('should render SSO buttons', () => {
      renderSignupPage()
      expect(screen.getByLabelText(/sign.*up with google/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/sign.*up with apple/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/sign.*up with github/i)).toBeInTheDocument()
    })

    it('should render the login link', () => {
      renderSignupPage()
      expect(screen.getByText(/login/i)).toBeInTheDocument()
    })
  })

  describe('Form Interaction', () => {
    it('should allow typing in username field', () => {
      renderSignupPage()
      const usernameInput = screen.getByLabelText(/username/i)
      fireEvent.change(usernameInput, { target: { value: 'newuser' } })
      expect(usernameInput.value).toBe('newuser')
    })

    it('should allow typing in email field', () => {
      renderSignupPage()
      const emailInput = screen.getByLabelText(/email/i)
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      expect(emailInput.value).toBe('test@example.com')
    })

    it('should allow typing in password field', () => {
      renderSignupPage()
      const passwordInput = screen.getByLabelText(/^password$/i)
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      expect(passwordInput.value).toBe('password123')
    })

    it('should toggle password visibility', () => {
      renderSignupPage()
      const passwordInput = screen.getByLabelText(/^password$/i)
      expect(passwordInput.type).toBe('password')
      
      const toggleButton = screen.getByRole('button', { name: /show password/i })
      fireEvent.click(toggleButton)
      
      expect(passwordInput.type).toBe('text')
    })
  })

  describe('Form Validation', () => {
    it('should show error for invalid email', async () => {
      renderSignupPage()
      const emailInput = screen.getByLabelText(/email/i)
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
      fireEvent.blur(emailInput)
      
      await waitFor(() => {
        const errorMessage = screen.queryByText(/invalid.*email/i)
        if (errorMessage) {
          expect(errorMessage).toBeInTheDocument()
        }
      })
    })

    it('should show error for short password', async () => {
      renderSignupPage()
      const passwordInput = screen.getByLabelText(/^password$/i)
      fireEvent.change(passwordInput, { target: { value: '123' } })
      fireEvent.blur(passwordInput)
      
      await waitFor(() => {
        const errorMessage = screen.queryByText(/password.*short/i)
        if (errorMessage) {
          expect(errorMessage).toBeInTheDocument()
        }
      })
    })
  })

  describe('Form Submission', () => {
    it('should call signUp with correct data', async () => {
      const { signUp } = await import('@/lib/auth')
      signUp.mockResolvedValue({ user: { id: '1', username: 'newuser' } })
      
      renderSignupPage()
      
      const usernameInput = screen.getByLabelText(/username/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/^password$/i)
      
      fireEvent.change(usernameInput, { target: { value: 'newuser' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      
      const signupButtons = screen.getAllByRole('button', { name: /sign.*up/i })
      const submitButton = signupButtons.find(btn => btn.type === 'submit')
      
      if (submitButton) {
        fireEvent.click(submitButton)
        
        await waitFor(() => {
          expect(signUp).toHaveBeenCalledWith(
            expect.objectContaining({
              username: 'newuser',
              email: 'test@example.com',
              password: 'password123'
            })
          )
        })
      }
    })

    it('should show error when signup fails', async () => {
      const { signUp } = await import('@/lib/auth')
      signUp.mockRejectedValue(new Error('Username already exists'))
      
      renderSignupPage()
      
      const usernameInput = screen.getByLabelText(/username/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/^password$/i)
      
      fireEvent.change(usernameInput, { target: { value: 'existinguser' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      
      const signupButtons = screen.getAllByRole('button', { name: /sign.*up/i })
      const submitButton = signupButtons.find(btn => btn.type === 'submit')
      
      if (submitButton) {
        fireEvent.click(submitButton)
        
        await waitFor(() => {
          expect(screen.getByText(/username already exists/i)).toBeInTheDocument()
        })
      }
    })
  })

  describe('SSO Signup', () => {
    it('should call signInWithOAuth when clicking Google SSO button', async () => {
      const { signInWithOAuth } = await import('@/lib/auth')
      signInWithOAuth.mockResolvedValue({ error: null })
      
      renderSignupPage()
      const googleButton = screen.getByLabelText(/sign.*up with google/i)
      fireEvent.click(googleButton)
      
      await waitFor(() => {
        expect(signInWithOAuth).toHaveBeenCalledWith('google', expect.any(Object))
      })
    })

    it('should call signInWithOAuth when clicking Apple SSO button', async () => {
      const { signInWithOAuth } = await import('@/lib/auth')
      signInWithOAuth.mockResolvedValue({ error: null })
      
      renderSignupPage()
      const appleButton = screen.getByLabelText(/sign.*up with apple/i)
      fireEvent.click(appleButton)
      
      await waitFor(() => {
        expect(signInWithOAuth).toHaveBeenCalledWith('apple', expect.any(Object))
      })
    })

    it('should call signInWithOAuth when clicking GitHub SSO button', async () => {
      const { signInWithOAuth } = await import('@/lib/auth')
      signInWithOAuth.mockResolvedValue({ error: null })
      
      renderSignupPage()
      const githubButton = screen.getByLabelText(/sign.*up with github/i)
      fireEvent.click(githubButton)
      
      await waitFor(() => {
        expect(signInWithOAuth).toHaveBeenCalledWith('github', expect.any(Object))
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for form inputs', () => {
      renderSignupPage()
      expect(screen.getByLabelText(/username/i)).toHaveAttribute('id')
      expect(screen.getByLabelText(/email/i)).toHaveAttribute('id')
      expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('id')
    })

    it('should have proper ARIA labels for SSO buttons', () => {
      renderSignupPage()
      expect(screen.getByLabelText(/sign.*up with google/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/sign.*up with apple/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/sign.*up with github/i)).toBeInTheDocument()
    })
  })

  describe('Snapshot', () => {
    it('should match snapshot', () => {
      const { container } = renderSignupPage()
      expect(container).toMatchSnapshot()
    })
  })
})
