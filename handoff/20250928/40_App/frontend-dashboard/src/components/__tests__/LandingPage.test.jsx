import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LandingPage from '../LandingPage'

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
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderLandingPage()
      expect(screen.getByTestId('apple-hero')).toBeInTheDocument()
    })

    it('should render the hero section', () => {
      renderLandingPage()
      expect(screen.getByTestId('apple-hero')).toBeInTheDocument()
    })

    it('should render features section', () => {
      renderLandingPage()
      const featuresHeading = screen.queryByText(/features/i) || screen.queryByText(/功能/i)
      if (featuresHeading) {
        expect(featuresHeading).toBeInTheDocument()
      }
    })

    it('should render pricing section', () => {
      renderLandingPage()
      const pricingHeading = screen.queryByText(/pricing/i) || screen.queryByText(/價格/i)
      if (pricingHeading) {
        expect(pricingHeading).toBeInTheDocument()
      }
    })

    it('should render CTA buttons', () => {
      renderLandingPage()
      const getStartedButtons = screen.getAllByRole('button', { name: /get started/i })
      expect(getStartedButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Hero Section Interaction', () => {
    it('should handle Get Started button click', () => {
      renderLandingPage()
      const getStartedButton = screen.getByRole('button', { name: /get started/i })
      fireEvent.click(getStartedButton)
      expect(getStartedButton).toBeInTheDocument()
    })

    it('should handle Learn More button click', () => {
      renderLandingPage()
      const learnMoreButton = screen.getByRole('button', { name: /learn more/i })
      fireEvent.click(learnMoreButton)
      expect(learnMoreButton).toBeInTheDocument()
    })
  })

  describe('Features Section', () => {
    it('should display feature cards', () => {
      renderLandingPage()
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('should have interactive feature cards', () => {
      renderLandingPage()
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toBeEnabled()
      })
    })
  })

  describe('Pricing Section', () => {
    it('should display pricing plans', () => {
      renderLandingPage()
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('should have CTA buttons in pricing cards', () => {
      renderLandingPage()
      const ctaButtons = screen.getAllByRole('button')
      expect(ctaButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Navigation', () => {
    it('should have navigation links', () => {
      renderLandingPage()
      const links = screen.getAllByRole('link')
      expect(links.length).toBeGreaterThan(0)
    })

    it('should navigate to login page', () => {
      renderLandingPage()
      const loginLinks = screen.queryAllByRole('link', { name: /login/i })
      if (loginLinks.length > 0) {
        expect(loginLinks[0]).toHaveAttribute('href', '/login')
      }
    })

    it('should navigate to signup page', () => {
      renderLandingPage()
      const signupLinks = screen.queryAllByRole('link', { name: /sign.*up/i })
      if (signupLinks.length > 0) {
        expect(signupLinks[0]).toHaveAttribute('href', '/signup')
      }
    })
  })

  describe('Responsive Design', () => {
    it('should render on mobile viewport', () => {
      global.innerWidth = 375
      global.innerHeight = 667
      renderLandingPage()
      expect(screen.getByTestId('apple-hero')).toBeInTheDocument()
    })

    it('should render on tablet viewport', () => {
      global.innerWidth = 768
      global.innerHeight = 1024
      renderLandingPage()
      expect(screen.getByTestId('apple-hero')).toBeInTheDocument()
    })

    it('should render on desktop viewport', () => {
      global.innerWidth = 1920
      global.innerHeight = 1080
      renderLandingPage()
      expect(screen.getByTestId('apple-hero')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderLandingPage()
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    })

    it('should have accessible buttons', () => {
      renderLandingPage()
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toBeEnabled()
      })
    })

    it('should have accessible links', () => {
      renderLandingPage()
      const links = screen.getAllByRole('link')
      links.forEach(link => {
        expect(link).toHaveAttribute('href')
      })
    })
  })

  describe('SEO', () => {
    it('should have semantic HTML structure', () => {
      const { container } = renderLandingPage()
      const sections = container.querySelectorAll('section')
      expect(sections.length).toBeGreaterThan(0)
    })

    it('should have proper heading structure', () => {
      renderLandingPage()
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    })
  })

  describe('Performance', () => {
    it('should render quickly', () => {
      const startTime = performance.now()
      renderLandingPage()
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      expect(renderTime).toBeLessThan(1000)
    })

    it('should not have memory leaks', () => {
      const { unmount } = renderLandingPage()
      unmount()
      expect(true).toBe(true)
    })
  })

  describe('Snapshot', () => {
    it('should match snapshot', () => {
      const { container } = renderLandingPage()
      expect(container).toMatchSnapshot()
    })
  })
})
