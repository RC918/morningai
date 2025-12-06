import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ApprovalWorkflow from '../ApprovalWorkflow'

// Mock react-i18next
const mockT = (key, fallback) => fallback || key
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

// Mock API client
vi.mock('@/lib/api-client', () => ({
  apiClientWithMeta: vi.fn(),
  handleApiError: vi.fn((err, options) => options?.defaultMessage || 'Error')
}))

import * as apiClient from '@/lib/api-client'

describe('ApprovalWorkflow', () => {
  const defaultProps = {
    sessionId: 'session-123',
    taskId: 'task-456',
    isOpen: true,
    onClose: vi.fn(),
    onApproved: vi.fn(),
    onRejected: vi.fn(),
    approvalData: {
      reason: 'This task requires database modifications',
      riskLevel: 'medium',
      affectedResources: [
        { name: 'users_table', type: 'database', action: 'modify' },
        { name: 'config.json', type: 'code', action: 'update' }
      ],
      taskName: 'Update User Schema',
      description: 'Modifying the user table to add new fields'
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()
    apiClient.apiClientWithMeta.mockResolvedValue({})
  })

  describe('Dialog Rendering', () => {
    it('should render dialog when isOpen is true', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('Approval Required')).toBeInTheDocument()
    })

    it('should not render dialog content when isOpen is false', () => {
      render(<ApprovalWorkflow {...defaultProps} isOpen={false} />)
      expect(screen.queryByText('Approval Required')).not.toBeInTheDocument()
    })
  })

  describe('Task Info', () => {
    it('should display task name', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('Update User Schema')).toBeInTheDocument()
    })

    it('should display task description', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('Modifying the user table to add new fields')).toBeInTheDocument()
    })

    it('should not display description when not provided', () => {
      const props = {
        ...defaultProps,
        approvalData: { ...defaultProps.approvalData, description: '' }
      }
      render(<ApprovalWorkflow {...props} />)
      expect(screen.queryByText('Modifying the user table to add new fields')).not.toBeInTheDocument()
    })
  })

  describe('Risk Level', () => {
    it('should display risk level badge', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('MEDIUM')).toBeInTheDocument()
    })

    it('should display risk reason', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('This task requires database modifications')).toBeInTheDocument()
    })

    it('should show high risk styling for high risk level', () => {
      const props = {
        ...defaultProps,
        approvalData: { ...defaultProps.approvalData, riskLevel: 'high' }
      }
      render(<ApprovalWorkflow {...props} />)
      expect(screen.getByText('HIGH')).toBeInTheDocument()
    })

    it('should show low risk styling for low risk level', () => {
      const props = {
        ...defaultProps,
        approvalData: { ...defaultProps.approvalData, riskLevel: 'low' }
      }
      render(<ApprovalWorkflow {...props} />)
      expect(screen.getByText('LOW')).toBeInTheDocument()
    })

    it('should show critical risk styling for critical risk level', () => {
      const props = {
        ...defaultProps,
        approvalData: { ...defaultProps.approvalData, riskLevel: 'critical' }
      }
      render(<ApprovalWorkflow {...props} />)
      expect(screen.getByText('CRITICAL')).toBeInTheDocument()
    })
  })

  describe('Affected Resources', () => {
    it('should display affected resources', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('Affected Resources')).toBeInTheDocument()
      expect(screen.getByText('users_table')).toBeInTheDocument()
      expect(screen.getByText('config.json')).toBeInTheDocument()
    })

    it('should display resource actions', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByText('modify')).toBeInTheDocument()
      expect(screen.getByText('update')).toBeInTheDocument()
    })

    it('should not display affected resources section when empty', () => {
      const props = {
        ...defaultProps,
        approvalData: { ...defaultProps.approvalData, affectedResources: [] }
      }
      render(<ApprovalWorkflow {...props} />)
      expect(screen.queryByText('Affected Resources')).not.toBeInTheDocument()
    })
  })

  describe('Comment Input', () => {
    it('should render comment textarea', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      expect(screen.getByLabelText(/Comment/)).toBeInTheDocument()
    })

    it('should allow typing in comment field', () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      const textarea = screen.getByPlaceholderText('Add a comment for the audit log...')
      fireEvent.change(textarea, { target: { value: 'Approved after review' } })
      expect(textarea.value).toBe('Approved after review')
    })
  })

  describe('Approve Action', () => {
    it('should call API and callbacks when Approve is clicked', async () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      
      fireEvent.click(screen.getByText('Approve'))
      
      await waitFor(() => {
        expect(apiClient.apiClientWithMeta).toHaveBeenCalledWith(
          '/api/sessions/session-123/tasks/task-456/approve',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ comment: undefined })
          })
        )
      })
      
      expect(defaultProps.onApproved).toHaveBeenCalledWith('task-456', '')
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should include comment in API call when provided', async () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      
      const textarea = screen.getByPlaceholderText('Add a comment for the audit log...')
      fireEvent.change(textarea, { target: { value: 'Approved after review' } })
      
      fireEvent.click(screen.getByText('Approve'))
      
      await waitFor(() => {
        expect(apiClient.apiClientWithMeta).toHaveBeenCalledWith(
          '/api/sessions/session-123/tasks/task-456/approve',
          expect.objectContaining({
            body: JSON.stringify({ comment: 'Approved after review' })
          })
        )
      })
    })

    it('should show error when API call fails', async () => {
      apiClient.apiClientWithMeta.mockRejectedValue(new Error('Network error'))
      
      render(<ApprovalWorkflow {...defaultProps} />)
      
      fireEvent.click(screen.getByText('Approve'))
      
      await waitFor(() => {
        expect(screen.getByText('Failed to approve task')).toBeInTheDocument()
      })
    })

    it('should disable buttons while submitting', async () => {
      // Make API call hang
      apiClient.apiClientWithMeta.mockImplementation(() => new Promise(() => {}))
      
      render(<ApprovalWorkflow {...defaultProps} />)
      
      fireEvent.click(screen.getByText('Approve'))
      
      await waitFor(() => {
        expect(screen.getByText('Approve').closest('button')).toBeDisabled()
        expect(screen.getByText('Reject').closest('button')).toBeDisabled()
      })
    })
  })

  describe('Reject Action', () => {
    it('should call API and callbacks when Reject is clicked', async () => {
      render(<ApprovalWorkflow {...defaultProps} />)
      
      fireEvent.click(screen.getByText('Reject'))
      
      await waitFor(() => {
        expect(apiClient.apiClientWithMeta).toHaveBeenCalledWith(
          '/api/sessions/session-123/tasks/task-456/reject',
          expect.objectContaining({
            method: 'POST'
          })
        )
      })
      
      expect(defaultProps.onRejected).toHaveBeenCalledWith('task-456', '')
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should show error when reject API call fails', async () => {
      apiClient.apiClientWithMeta.mockRejectedValue(new Error('Network error'))
      
      render(<ApprovalWorkflow {...defaultProps} />)
      
      fireEvent.click(screen.getByText('Reject'))
      
      await waitFor(() => {
        expect(screen.getByText('Failed to reject task')).toBeInTheDocument()
      })
    })
  })

  describe('Default Values', () => {
    it('should use default values when approvalData is empty', () => {
      render(<ApprovalWorkflow {...defaultProps} approvalData={{}} />)
      
      // Should still render without crashing
      expect(screen.getByText('Approval Required')).toBeInTheDocument()
      // Default risk level is medium
      expect(screen.getByText('MEDIUM')).toBeInTheDocument()
    })
  })
})
