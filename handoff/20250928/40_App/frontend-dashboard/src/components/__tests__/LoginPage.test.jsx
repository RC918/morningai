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

    it('should match snapshot', () => {
      const { container } = renderLoginPage()
      expect(container).toMatchSnapshot()
    })
  })
})
