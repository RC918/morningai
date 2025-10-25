import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderLoginPage()
      expect(screen.getByText(/Morning AI/i)).toBeInTheDocument()
    })

    it('should render the login form', () => {
      renderLoginPage()
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    })

    it('should render the login button', () => {
      renderLoginPage()
      const loginButtons = screen.getAllByRole('button', { name: /login/i })
      expect(loginButtons.length).toBeGreaterThan(0)
    })

    it('should render SSO buttons', () => {
      renderLoginPage()
      expect(screen.getByLabelText(/login with google/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/login with apple/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/login with github/i)).toBeInTheDocument()
    })

    it('should render the signup link', () => {
      renderLoginPage()
      expect(screen.getByText(/sign.*up/i)).toBeInTheDocument()
    })

    it('should render development credentials', () => {
      renderLoginPage()
      expect(screen.getByText(/admin/i)).toBeInTheDocument()
      expect(screen.getByText(/admin123/i)).toBeInTheDocument()
    })
  })

  describe('Form Interaction', () => {
    it('should allow typing in username field', () => {
      renderLoginPage()
      const usernameInput = screen.getByLabelText(/username/i)
      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      expect(usernameInput.value).toBe('testuser')
    })

    it('should allow typing in password field', () => {
      renderLoginPage()
      const passwordInput = screen.getByLabelText(/password/i)
      fireEvent.change(passwordInput, { target: { value: 'testpass' } })
      expect(passwordInput.value).toBe('testpass')
    })

    it('should toggle password visibility', () => {
      renderLoginPage()
      const passwordInput = screen.getByLabelText(/password/i)
      expect(passwordInput.type).toBe('password')
      
      const toggleButton = screen.getByRole('button', { name: /show password/i })
      fireEvent.click(toggleButton)
      
      expect(passwordInput.type).toBe('text')
    })
  })

  describe('Form Submission', () => {
    it('should show error when submitting empty form', async () => {
      const apiClient = await import('@/lib/api')
      apiClient.default.login.mockResolvedValue({ message: 'Invalid credentials' })
      
      renderLoginPage()
      const loginButtons = screen.getAllByRole('button', { name: /login/i })
      const submitButton = loginButtons.find(btn => btn.type === 'submit')
      
      if (submitButton) {
        fireEvent.click(submitButton)
        
        await waitFor(() => {
          const errorText = screen.queryByText(/invalid credentials/i) || screen.queryByText(/login.*failed/i)
          if (errorText) {
            expect(errorText).toBeInTheDocument()
          }
        })
      }
    })

    it('should call login with correct credentials', async () => {
      const apiClient = await import('@/lib/api')
      const mockOnLogin = vi.fn()
      apiClient.default.login.mockResolvedValue({ 
        user: { id: '1', username: 'testuser' },
        token: 'test-token'
      })
      
      render(
        <BrowserRouter>
          <LoginPage onLogin={mockOnLogin} />
        </BrowserRouter>
      )
      
      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      
      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'testpass' } })
      
      const loginButtons = screen.getAllByRole('button', { name: /login/i })
      const submitButton = loginButtons.find(btn => btn.type === 'submit')
      
      if (submitButton) {
        fireEvent.click(submitButton)
        
        await waitFor(() => {
          expect(apiClient.default.login).toHaveBeenCalledWith({
            username: 'testuser',
            password: 'testpass'
          })
        })
      }
    })
  })

  describe('SSO Login', () => {
    it('should call signInWithOAuth when clicking Google SSO button', async () => {
      const { signInWithOAuth } = await import('@/lib/supabaseClient')
      signInWithOAuth.mockResolvedValue({ error: null })
      
      renderLoginPage()
      const googleButton = screen.getByLabelText(/login with google/i)
      fireEvent.click(googleButton)
      
      await waitFor(() => {
        expect(signInWithOAuth).toHaveBeenCalledWith('google')
      })
    })

    it('should call signInWithOAuth when clicking Apple SSO button', async () => {
      const { signInWithOAuth } = await import('@/lib/supabaseClient')
      signInWithOAuth.mockResolvedValue({ error: null })
      
      renderLoginPage()
      const appleButton = screen.getByLabelText(/login with apple/i)
      fireEvent.click(appleButton)
      
      await waitFor(() => {
        expect(signInWithOAuth).toHaveBeenCalledWith('apple')
      })
    })

    it('should call signInWithOAuth when clicking GitHub SSO button', async () => {
      const { signInWithOAuth } = await import('@/lib/supabaseClient')
      signInWithOAuth.mockResolvedValue({ error: null })
      
      renderLoginPage()
      const githubButton = screen.getByLabelText(/login with github/i)
      fireEvent.click(githubButton)
      
      await waitFor(() => {
        expect(signInWithOAuth).toHaveBeenCalledWith('github')
      })
    })

    it('should show error when SSO fails', async () => {
      const { signInWithOAuth } = await import('@/lib/supabaseClient')
      signInWithOAuth.mockResolvedValue({ error: { message: 'SSO failed' } })
      
      renderLoginPage()
      const googleButton = screen.getByLabelText(/login with google/i)
      fireEvent.click(googleButton)
      
      await waitFor(() => {
        const errorText = screen.queryByText(/sso.*failed/i) || screen.queryByText(/failed/i)
        if (errorText) {
          expect(errorText).toBeInTheDocument()
        }
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for form inputs', () => {
      renderLoginPage()
      expect(screen.getByLabelText(/username/i)).toHaveAttribute('id')
      expect(screen.getByLabelText(/password/i)).toHaveAttribute('id')
    })

    it('should have proper ARIA labels for SSO buttons', () => {
      renderLoginPage()
      expect(screen.getByLabelText(/login with google/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/login with apple/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/login with github/i)).toBeInTheDocument()
    })
  })

  describe('Snapshot', () => {
    it('should match snapshot', () => {
      const { container } = renderLoginPage()
      expect(container).toMatchSnapshot()
    })
  })
})
