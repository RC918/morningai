import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import CodeReviewPanel from '../CodeReviewPanel'

// Mock react-i18next with interpolation support
const mockT = (key, fallbackOrParams, params) => {
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

// Mock window.open
const mockWindowOpen = vi.fn()
Object.defineProperty(window, 'open', { value: mockWindowOpen, writable: true })

describe('CodeReviewPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Empty State', () => {
    it('should render empty state when no PR URL and no file changes', () => {
      render(<CodeReviewPanel />)
      expect(screen.getByText('No pull request created yet')).toBeInTheDocument()
    })

    it('should not render empty state when PR URL is provided', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" />)
      expect(screen.queryByText('No pull request created yet')).not.toBeInTheDocument()
    })

    it('should not render empty state when file changes exist', () => {
      render(<CodeReviewPanel fileChanges={[{ path: 'test.js', changeType: 'added', additions: 10, deletions: 0 }]} />)
      expect(screen.queryByText('No pull request created yet')).not.toBeInTheDocument()
    })
  })

  describe('PR Header', () => {
    it('should render PR header with View PR button', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" />)
      expect(screen.getByText('Pull Request')).toBeInTheDocument()
      expect(screen.getByText('View PR')).toBeInTheDocument()
    })

    it('should open PR URL in new tab when View PR is clicked', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" />)
      fireEvent.click(screen.getByText('View PR'))
      expect(mockWindowOpen).toHaveBeenCalledWith('https://github.com/test/repo/pull/1', '_blank')
    })
  })

  describe('PR Status Badge', () => {
    it('should show Approved badge for approved status', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" prStatus="approved" />)
      expect(screen.getByText('Approved')).toBeInTheDocument()
    })

    it('should show Changes Requested badge for changes_requested status', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" prStatus="changes_requested" />)
      expect(screen.getByText('Changes Requested')).toBeInTheDocument()
    })

    it('should show Pending Review badge for pending status', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" prStatus="pending" />)
      expect(screen.getByText('Pending Review')).toBeInTheDocument()
    })

    it('should show Merged badge for merged status', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" prStatus="merged" />)
      expect(screen.getByText('Merged')).toBeInTheDocument()
    })

    it('should show Closed badge for closed status', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" prStatus="closed" />)
      expect(screen.getByText('Closed')).toBeInTheDocument()
    })
  })

  describe('CI Checks Status', () => {
    it('should render CI checks summary with counts', () => {
      render(
        <CodeReviewPanel 
          prUrl="https://github.com/test/repo/pull/1"
          checksStatus={{ passed: 10, failed: 2, pending: 1, total: 13 }}
        />
      )
      expect(screen.getByText('CI Checks')).toBeInTheDocument()
      expect(screen.getByText(/10\/13 checks passed/)).toBeInTheDocument()
    })

    it('should show Failed badge when there are failed checks', () => {
      render(
        <CodeReviewPanel 
          prUrl="https://github.com/test/repo/pull/1"
          checksStatus={{ passed: 10, failed: 2, pending: 0, total: 12 }}
        />
      )
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })

    it('should show Pending badge when there are pending checks', () => {
      render(
        <CodeReviewPanel 
          prUrl="https://github.com/test/repo/pull/1"
          checksStatus={{ passed: 10, failed: 0, pending: 2, total: 12 }}
        />
      )
      expect(screen.getByText('Pending')).toBeInTheDocument()
    })

    it('should show Passed badge when all checks pass', () => {
      render(
        <CodeReviewPanel 
          prUrl="https://github.com/test/repo/pull/1"
          checksStatus={{ passed: 12, failed: 0, pending: 0, total: 12 }}
        />
      )
      expect(screen.getByText('Passed')).toBeInTheDocument()
    })

    it('should render individual checks when checks array is provided', () => {
      render(
        <CodeReviewPanel 
          prUrl="https://github.com/test/repo/pull/1"
          checksStatus={{ 
            checks: [
              { name: 'lint', status: 'success' },
              { name: 'test', status: 'failure' }
            ]
          }}
        />
      )
      expect(screen.getByText('lint')).toBeInTheDocument()
      expect(screen.getByText('test')).toBeInTheDocument()
    })
  })

  describe('File Changes', () => {
    const mockFileChanges = [
      { path: 'src/index.js', changeType: 'modified', additions: 10, deletions: 5 },
      { path: 'src/new-file.js', changeType: 'added', additions: 50, deletions: 0, preview: 'const x = 1;' }
    ]

    it('should render file changes list', () => {
      render(<CodeReviewPanel fileChanges={mockFileChanges} />)
      expect(screen.getByText('Files Changed (2)')).toBeInTheDocument()
      expect(screen.getByText('src/index.js')).toBeInTheDocument()
      expect(screen.getByText('src/new-file.js')).toBeInTheDocument()
    })

    it('should show file count in header', () => {
      render(<CodeReviewPanel fileChanges={mockFileChanges} />)
      expect(screen.getByText('Files Changed (2)')).toBeInTheDocument()
    })

    it('should show change type badge', () => {
      render(<CodeReviewPanel fileChanges={mockFileChanges} />)
      expect(screen.getByText('modified')).toBeInTheDocument()
      expect(screen.getByText('added')).toBeInTheDocument()
    })

    it('should show additions and deletions count', () => {
      render(<CodeReviewPanel fileChanges={mockFileChanges} />)
      expect(screen.getByText('+10')).toBeInTheDocument()
      expect(screen.getByText('-5')).toBeInTheDocument()
    })

    it('should expand file to show preview when clicked', () => {
      render(<CodeReviewPanel fileChanges={mockFileChanges} />)
      
      // Preview should not be visible initially
      expect(screen.queryByText('const x = 1;')).not.toBeInTheDocument()
      
      // Click to expand
      fireEvent.click(screen.getByText('src/new-file.js'))
      
      // Preview should now be visible
      expect(screen.getByText('const x = 1;')).toBeInTheDocument()
    })

    it('should collapse file when clicked again', () => {
      render(<CodeReviewPanel fileChanges={mockFileChanges} />)
      
      // Expand
      fireEvent.click(screen.getByText('src/new-file.js'))
      expect(screen.getByText('const x = 1;')).toBeInTheDocument()
      
      // Collapse
      fireEvent.click(screen.getByText('src/new-file.js'))
      expect(screen.queryByText('const x = 1;')).not.toBeInTheDocument()
    })
  })

  describe('Review Comments', () => {
    const mockComments = [
      { author: 'reviewer1', body: 'Looks good!', filePath: 'src/index.js', line: 10, resolved: false },
      { author: 'reviewer2', body: 'Please fix this', resolved: true }
    ]

    it('should render review comments', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" reviewComments={mockComments} />)
      expect(screen.getByText('Review Comments (2)')).toBeInTheDocument()
      expect(screen.getByText('reviewer1')).toBeInTheDocument()
      expect(screen.getByText('Looks good!')).toBeInTheDocument()
    })

    it('should show comment count in header', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" reviewComments={mockComments} />)
      expect(screen.getByText('Review Comments (2)')).toBeInTheDocument()
    })

    it('should show file path and line number for inline comments', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" reviewComments={mockComments} />)
      expect(screen.getByText('src/index.js:10')).toBeInTheDocument()
    })

    it('should show Resolved badge for resolved comments', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" reviewComments={mockComments} />)
      expect(screen.getByText('Resolved')).toBeInTheDocument()
    })
  })

  describe('Reviewers', () => {
    const mockReviewers = [
      { name: 'Alice', status: 'approved' },
      { name: 'Bob', status: 'changes_requested' },
      { name: 'Charlie', status: 'pending' }
    ]

    it('should render reviewers list', () => {
      render(<CodeReviewPanel prUrl="https://github.com/test/repo/pull/1" reviewers={mockReviewers} />)
      expect(screen.getByText('Reviewers')).toBeInTheDocument()
      expect(screen.getByText('Alice')).toBeInTheDocument()
      expect(screen.getByText('Bob')).toBeInTheDocument()
      expect(screen.getByText('Charlie')).toBeInTheDocument()
    })
  })
})
