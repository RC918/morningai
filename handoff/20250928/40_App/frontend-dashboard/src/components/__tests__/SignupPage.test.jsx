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
  AppleButton: ({ children, ...props }) => <button {...props}>{children}</button>
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
  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderSignupPage()
      expect(container).toBeTruthy()
    })

    it('should match snapshot', () => {
      const { container } = renderSignupPage()
      expect(container).toMatchSnapshot()
    })
  })
})
