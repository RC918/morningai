import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TestResultsPanel from '../TestResultsPanel'

// Mock react-i18next with interpolation support
const mockT = (key, fallbackOrParams, params) => {
  // Handle both t('key', 'fallback') and t('key', 'template {{var}}', { var: value })
  const fallback = typeof fallbackOrParams === 'string' ? fallbackOrParams : key
  const variables = typeof fallbackOrParams === 'object' ? fallbackOrParams : params
  
  if (variables) {
    return fallback.replace(/\{\{(\w+)\}\}/g, (_, varName) => variables[varName] ?? '')
  }
  return fallback
}
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

describe('TestResultsPanel', () => {
  describe('Empty State', () => {
    it('should render empty state when no test suites and not running', () => {
      render(<TestResultsPanel />)
      expect(screen.getByText('No test results available')).toBeInTheDocument()
    })

    it('should not render empty state when isRunning is true', () => {
      render(<TestResultsPanel isRunning={true} totalTests={10} />)
      expect(screen.queryByText('No test results available')).not.toBeInTheDocument()
    })

    it('should not render empty state when test suites exist', () => {
      render(<TestResultsPanel testSuites={[{ name: 'Suite 1', tests: [] }]} totalTests={0} />)
      expect(screen.queryByText('No test results available')).not.toBeInTheDocument()
    })
  })

  describe('Summary Card', () => {
    it('should render test summary with counts', () => {
      render(
        <TestResultsPanel 
          testSuites={[{ name: 'Test', tests: [] }]}
          totalTests={100}
          passedTests={80}
          failedTests={15}
          skippedTests={5}
        />
      )
      expect(screen.getByText('Test Summary')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('80')).toBeInTheDocument()
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })

    it('should show pass rate percentage', () => {
      render(
        <TestResultsPanel 
          testSuites={[{ name: 'Test', tests: [] }]}
          totalTests={100}
          passedTests={80}
          failedTests={20}
        />
      )
      expect(screen.getByText('80%')).toBeInTheDocument()
    })

    it('should show 0% pass rate when no tests', () => {
      render(<TestResultsPanel testSuites={[{ name: 'Test', tests: [] }]} totalTests={0} passedTests={0} />)
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('should show Running badge when isRunning is true', () => {
      render(<TestResultsPanel isRunning={true} totalTests={10} />)
      expect(screen.getByText('Running...')).toBeInTheDocument()
    })

    it('should show duration when provided', () => {
      render(
        <TestResultsPanel 
          testSuites={[{ name: 'Test', tests: [] }]}
          totalTests={10}
          passedTests={10}
          duration={5000}
        />
      )
      expect(screen.getByText(/Duration: 5\.00s/)).toBeInTheDocument()
    })

    it('should format duration in milliseconds for short durations', () => {
      render(
        <TestResultsPanel 
          testSuites={[{ name: 'Test', tests: [] }]}
          totalTests={10}
          passedTests={10}
          duration={500}
        />
      )
      expect(screen.getByText(/Duration: 500ms/)).toBeInTheDocument()
    })

    it('should format duration in minutes for long durations', () => {
      render(
        <TestResultsPanel 
          testSuites={[{ name: 'Test', tests: [] }]}
          totalTests={10}
          passedTests={10}
          duration={125000}
        />
      )
      expect(screen.getByText(/Duration: 2m 5s/)).toBeInTheDocument()
    })
  })

  describe('Test Suites', () => {
    const mockTestSuites = [
      {
        name: 'Unit Tests',
        status: 'passed',
        tests: [
          { name: 'should pass test 1', status: 'passed', duration: 100 },
          { name: 'should pass test 2', status: 'passed', duration: 200 }
        ]
      },
      {
        name: 'Integration Tests',
        status: 'failed',
        tests: [
          { name: 'should fail test', status: 'failed', error: 'Expected true to be false' }
        ]
      }
    ]

    it('should render test suites list', () => {
      render(<TestResultsPanel testSuites={mockTestSuites} totalTests={3} />)
      expect(screen.getByText('Test Suites (2)')).toBeInTheDocument()
      expect(screen.getByText('Unit Tests')).toBeInTheDocument()
      expect(screen.getByText('Integration Tests')).toBeInTheDocument()
    })

    it('should show suite count in header', () => {
      render(<TestResultsPanel testSuites={mockTestSuites} totalTests={3} />)
      expect(screen.getByText('Test Suites (2)')).toBeInTheDocument()
    })

    it('should show Passed badge for passing suites', () => {
      const passingSuites = [{ name: 'Passing Suite', status: 'passed', tests: [{ name: 'test', status: 'passed' }] }]
      render(<TestResultsPanel testSuites={passingSuites} totalTests={1} passedTests={1} />)
      // Should have at least one Passed badge (may have multiple due to summary + suite)
      const passedBadges = screen.getAllByText('Passed')
      expect(passedBadges.length).toBeGreaterThan(0)
    })

    it('should show Failed badge for failing suites', () => {
      const failingSuites = [{ name: 'Failing Suite', status: 'failed', tests: [{ name: 'test', status: 'failed' }] }]
      render(<TestResultsPanel testSuites={failingSuites} totalTests={1} failedTests={1} />)
      // Should have at least one Failed badge
      const failedBadges = screen.getAllByText('Failed')
      expect(failedBadges.length).toBeGreaterThan(0)
    })

    it('should expand suite to show tests when clicked', () => {
      render(<TestResultsPanel testSuites={mockTestSuites} totalTests={3} />)
      
      // Tests should not be visible initially
      expect(screen.queryByText('should pass test 1')).not.toBeInTheDocument()
      
      // Click to expand
      fireEvent.click(screen.getByText('Unit Tests'))
      
      // Tests should now be visible
      expect(screen.getByText('should pass test 1')).toBeInTheDocument()
      expect(screen.getByText('should pass test 2')).toBeInTheDocument()
    })

    it('should show test duration when expanded', () => {
      render(<TestResultsPanel testSuites={mockTestSuites} totalTests={3} />)
      
      fireEvent.click(screen.getByText('Unit Tests'))
      
      expect(screen.getByText('100ms')).toBeInTheDocument()
      expect(screen.getByText('200ms')).toBeInTheDocument()
    })

    it('should show error message for failed tests when expanded', () => {
      render(<TestResultsPanel testSuites={mockTestSuites} totalTests={3} />)
      
      fireEvent.click(screen.getByText('Integration Tests'))
      
      expect(screen.getByText('Expected true to be false')).toBeInTheDocument()
    })

    it('should collapse suite when clicked again', () => {
      render(<TestResultsPanel testSuites={mockTestSuites} totalTests={3} />)
      
      // Expand
      fireEvent.click(screen.getByText('Unit Tests'))
      expect(screen.getByText('should pass test 1')).toBeInTheDocument()
      
      // Collapse
      fireEvent.click(screen.getByText('Unit Tests'))
      expect(screen.queryByText('should pass test 1')).not.toBeInTheDocument()
    })
  })

  describe('Suite Status Calculation', () => {
    it('should compute suite counts from tests array', () => {
      const testSuites = [{
        name: 'Test Suite',
        tests: [
          { name: 'test 1', status: 'passed' },
          { name: 'test 2', status: 'passed' },
          { name: 'test 3', status: 'failed' }
        ]
      }]
      
      render(<TestResultsPanel testSuites={testSuites} totalTests={3} />)
      
      // Should show 2/3 (2 passed out of 3 total)
      expect(screen.getByText('2/3')).toBeInTheDocument()
    })

    it('should use explicit counts when provided', () => {
      const testSuites = [{
        name: 'Test Suite',
        totalCount: 10,
        passedCount: 8,
        failedCount: 2,
        tests: []
      }]
      
      render(<TestResultsPanel testSuites={testSuites} totalTests={10} />)
      
      expect(screen.getByText('8/10')).toBeInTheDocument()
    })

    it('should show Running status for running suites', () => {
      const testSuites = [{
        name: 'Running Suite',
        status: 'running',
        tests: []
      }]
      
      render(<TestResultsPanel testSuites={testSuites} totalTests={0} isRunning={true} />)
      
      expect(screen.getByText('Running')).toBeInTheDocument()
    })
  })

  describe('XSS Protection (Issue #2074)', () => {
    it('should escape HTML in test error messages', () => {
      const xssPayload = '<script>alert("XSS")</script>'
      const testSuites = [{
        name: 'XSS Test Suite',
        status: 'failed',
        tests: [
          { name: 'xss test', status: 'failed', error: xssPayload }
        ]
      }]
      
      render(<TestResultsPanel testSuites={testSuites} totalTests={1} failedTests={1} />)
      
      // Expand the suite to see the error
      fireEvent.click(screen.getByText('XSS Test Suite'))
      
      // The script tag should be rendered as text, not executed
      // React automatically escapes content in JSX expressions
      const errorElement = screen.getByText(xssPayload)
      expect(errorElement).toBeInTheDocument()
      expect(errorElement.tagName).toBe('PRE')
      
      // Verify no script elements were created
      expect(document.querySelector('script')).toBeNull()
    })

    it('should escape HTML entities in test names', () => {
      const xssName = '<img src=x onerror="alert(1)">'
      const testSuites = [{
        name: 'Test Suite',
        status: 'passed',
        tests: [
          { name: xssName, status: 'passed' }
        ]
      }]
      
      render(<TestResultsPanel testSuites={testSuites} totalTests={1} passedTests={1} />)
      
      fireEvent.click(screen.getByText('Test Suite'))
      
      // The malicious content should be rendered as text
      expect(screen.getByText(xssName)).toBeInTheDocument()
      
      // Verify no img elements were created from the XSS payload
      expect(document.querySelector('img[src="x"]')).toBeNull()
    })

    it('should escape HTML in suite names', () => {
      const xssSuiteName = '<div onclick="alert(1)">Malicious Suite</div>'
      const testSuites = [{
        name: xssSuiteName,
        status: 'passed',
        tests: []
      }]
      
      render(<TestResultsPanel testSuites={testSuites} totalTests={0} />)
      
      // The malicious content should be rendered as text
      expect(screen.getByText(xssSuiteName)).toBeInTheDocument()
    })
  })
})
