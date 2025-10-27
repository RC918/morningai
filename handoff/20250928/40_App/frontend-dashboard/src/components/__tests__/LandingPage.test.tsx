import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LandingPage from '../LandingPage'

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
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    section: ({ children, ...props }) => <section {...props}>{children}</section>,
    h1: ({ children, ...props }) => <h1 {...props}>{children}</h1>,
    h2: ({ children, ...props }) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }) => <p {...props}>{children}</p>
  },
  AnimatePresence: ({ children }) => <>{children}</>,
  useScroll: () => ({ scrollYProgress: { get: () => 0 } }),
  useTransform: () => ({ get: () => 0 }),
  useInView: () => true,
  useReducedMotion: () => true
}))

vi.mock('../AppleHero', () => ({
  default: ({ onGetStarted, onLearnMore }) => (
    <div data-testid="apple-hero">
      <button onClick={onGetStarted}>Get Started</button>
      <button onClick={onLearnMore}>Learn More</button>
    </div>
  )
}))

const renderLandingPage = () => {
  return render(
    <BrowserRouter>
      <LandingPage />
    </BrowserRouter>
  )
}

describe('LandingPage', () => {
  describe('Rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderLandingPage()
      expect(container).toBeTruthy()
    })
  })
})
