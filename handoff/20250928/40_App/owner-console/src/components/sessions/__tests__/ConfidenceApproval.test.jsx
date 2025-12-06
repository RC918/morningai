import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConfidenceApproval from '../ConfidenceApproval'

// Mock react-i18next
const mockT = (key, fallback) => fallback || key
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

describe('ConfidenceApproval', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onApprove: vi.fn(),
    onRequestChanges: vi.fn(),
    confidence: 0.85,
    confidenceThreshold: 0.8,
    sessionTitle: 'Test Session',
    currentTask: 'Writing tests'
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Dialog Rendering', () => {
    it('should render dialog when isOpen is true', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      expect(screen.getByText('Confidence Review')).toBeInTheDocument()
    })

    it('should not render dialog content when isOpen is false', () => {
      render(<ConfidenceApproval {...defaultProps} isOpen={false} />)
      expect(screen.queryByText('Confidence Review')).not.toBeInTheDocument()
    })
  })

  describe('Session Info', () => {
    it('should display session title', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      expect(screen.getByText('Test Session')).toBeInTheDocument()
    })

    it('should display current task', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      expect(screen.getByText(/Current Task.*Writing tests/)).toBeInTheDocument()
    })

    it('should not display current task when not provided', () => {
      render(<ConfidenceApproval {...defaultProps} currentTask="" />)
      expect(screen.queryByText('Current Task')).not.toBeInTheDocument()
    })
  })

  describe('Confidence Score Display', () => {
    it('should display confidence percentage', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.85} />)
      expect(screen.getByText('85%')).toBeInTheDocument()
    })

    it('should show Meets Threshold badge when confidence >= threshold', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.85} confidenceThreshold={0.8} />)
      expect(screen.getByText('Meets Threshold')).toBeInTheDocument()
    })

    it('should show Below Threshold badge when confidence < threshold', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.7} confidenceThreshold={0.8} />)
      expect(screen.getByText('Below Threshold')).toBeInTheDocument()
    })

    it('should display threshold value', () => {
      render(<ConfidenceApproval {...defaultProps} confidenceThreshold={0.8} />)
      expect(screen.getByText(/Threshold.*80%/)).toBeInTheDocument()
    })
  })

  describe('Confidence Level Classification', () => {
    it('should classify high confidence (>= 0.9)', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.95} />)
      expect(screen.getByText('95%')).toBeInTheDocument()
    })

    it('should classify medium confidence (>= 0.7, < 0.9)', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.75} />)
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('should classify low confidence (< 0.7)', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.5} />)
      expect(screen.getByText('50%')).toBeInTheDocument()
    })
  })

  describe('Risk Assessment', () => {
    it('should display risk assessment when provided', () => {
      render(
        <ConfidenceApproval 
          {...defaultProps} 
          riskAssessment={{ level: 'medium', description: 'Some risk involved' }}
        />
      )
      expect(screen.getByText(/Risk Level.*medium/)).toBeInTheDocument()
      expect(screen.getByText('Some risk involved')).toBeInTheDocument()
    })

    it('should not display risk assessment when not provided', () => {
      render(<ConfidenceApproval {...defaultProps} riskAssessment={null} />)
      expect(screen.queryByText('Risk Level')).not.toBeInTheDocument()
    })
  })

  describe('Contributing Factors', () => {
    const mockFactors = [
      { name: 'Code Coverage', trend: 'positive', impact: 10, description: 'High test coverage' },
      { name: 'Complexity', trend: 'negative', impact: -5, description: 'High cyclomatic complexity' },
      { name: 'Documentation', trend: 'neutral' }
    ]

    it('should display contributing factors', () => {
      render(<ConfidenceApproval {...defaultProps} factors={mockFactors} />)
      expect(screen.getByText('Contributing Factors')).toBeInTheDocument()
      expect(screen.getByText('Code Coverage')).toBeInTheDocument()
      expect(screen.getByText('Complexity')).toBeInTheDocument()
      expect(screen.getByText('Documentation')).toBeInTheDocument()
    })

    it('should display factor descriptions', () => {
      render(<ConfidenceApproval {...defaultProps} factors={mockFactors} />)
      expect(screen.getByText('High test coverage')).toBeInTheDocument()
      expect(screen.getByText('High cyclomatic complexity')).toBeInTheDocument()
    })

    it('should display factor impact with sign', () => {
      render(<ConfidenceApproval {...defaultProps} factors={mockFactors} />)
      expect(screen.getByText('+10%')).toBeInTheDocument()
      expect(screen.getByText('-5%')).toBeInTheDocument()
    })

    it('should not display factors section when empty', () => {
      render(<ConfidenceApproval {...defaultProps} factors={[]} />)
      expect(screen.queryByText('Contributing Factors')).not.toBeInTheDocument()
    })
  })

  describe('Low Confidence Warning', () => {
    it('should show warning when confidence is below threshold', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.7} confidenceThreshold={0.8} />)
      expect(screen.getByText(/confidence score is below the threshold/)).toBeInTheDocument()
    })

    it('should not show warning when confidence meets threshold', () => {
      render(<ConfidenceApproval {...defaultProps} confidence={0.85} confidenceThreshold={0.8} />)
      expect(screen.queryByText(/confidence score is below the threshold/)).not.toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should call onApprove when Approve button is clicked', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      fireEvent.click(screen.getByText('Approve & Continue'))
      expect(defaultProps.onApprove).toHaveBeenCalledWith({ comment: null })
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should call onRequestChanges when Request Changes button is clicked', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      fireEvent.click(screen.getByText('Request Changes'))
      expect(defaultProps.onRequestChanges).toHaveBeenCalledWith({ comment: null })
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should include comment when provided', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      
      const textarea = screen.getByPlaceholderText('Add any notes or feedback...')
      fireEvent.change(textarea, { target: { value: 'Looks good!' } })
      
      fireEvent.click(screen.getByText('Approve & Continue'))
      expect(defaultProps.onApprove).toHaveBeenCalledWith({ comment: 'Looks good!' })
    })

    it('should trim whitespace from comment', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      
      const textarea = screen.getByPlaceholderText('Add any notes or feedback...')
      fireEvent.change(textarea, { target: { value: '  Looks good!  ' } })
      
      fireEvent.click(screen.getByText('Approve & Continue'))
      expect(defaultProps.onApprove).toHaveBeenCalledWith({ comment: 'Looks good!' })
    })

    it('should clear comment after action', () => {
      render(<ConfidenceApproval {...defaultProps} />)
      
      const textarea = screen.getByPlaceholderText('Add any notes or feedback...')
      fireEvent.change(textarea, { target: { value: 'Test comment' } })
      fireEvent.click(screen.getByText('Approve & Continue'))
      
      // Comment should be cleared (value reset)
      expect(textarea.value).toBe('')
    })
  })
})
