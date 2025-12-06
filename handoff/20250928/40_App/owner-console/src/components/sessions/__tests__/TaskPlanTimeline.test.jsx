import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskPlanTimeline from '../TaskPlanTimeline'

// Mock react-i18next
const mockT = (key, fallback) => fallback || key
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

describe('TaskPlanTimeline', () => {
  const mockTasks = [
    { id: 1, name: 'Analyze code', status: 'completed', type: 'ANALYZE_CODE', description: 'Analyze the codebase' },
    { id: 2, name: 'Write code', status: 'running', type: 'WRITE_CODE' },
    { id: 3, name: 'Write tests', status: 'pending', type: 'WRITE_TEST' },
    { id: 4, name: 'Create PR', status: 'pending', type: 'CODE_REVIEW' }
  ]

  const defaultProps = {
    tasks: mockTasks,
    completedTasks: 1,
    totalTasks: 4,
    confidence: 0.85,
    editable: false,
    onTaskReorder: vi.fn(),
    onTaskEdit: vi.fn(),
    onTaskApprove: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Progress Header', () => {
    it('should display progress percentage', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      expect(screen.getByText('25%')).toBeInTheDocument()
    })

    it('should display completed/total tasks', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      expect(screen.getByText('1 / 4 tasks')).toBeInTheDocument()
    })

    it('should display confidence score', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      expect(screen.getByText('85%')).toBeInTheDocument()
    })

    it('should show 0% progress when no tasks', () => {
      render(<TaskPlanTimeline {...defaultProps} totalTasks={0} completedTasks={0} />)
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('should apply correct color for high confidence', () => {
      render(<TaskPlanTimeline {...defaultProps} confidence={0.9} />)
      const confidenceText = screen.getByText('90%')
      expect(confidenceText).toHaveClass('text-growth')
    })

    it('should apply correct color for medium confidence', () => {
      render(<TaskPlanTimeline {...defaultProps} confidence={0.7} />)
      const confidenceText = screen.getByText('70%')
      expect(confidenceText).toHaveClass('text-wisdom')
    })

    it('should apply correct color for low confidence', () => {
      render(<TaskPlanTimeline {...defaultProps} confidence={0.5} />)
      const confidenceText = screen.getByText('50%')
      expect(confidenceText).toHaveClass('text-energy')
    })
  })

  describe('Task List', () => {
    it('should render all tasks', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      expect(screen.getByText('Analyze code')).toBeInTheDocument()
      expect(screen.getByText('Write code')).toBeInTheDocument()
      expect(screen.getByText('Write tests')).toBeInTheDocument()
      expect(screen.getByText('Create PR')).toBeInTheDocument()
    })

    it('should display task numbers', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
    })

    it('should display task type badges', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      expect(screen.getByText('ANALYZE_CODE')).toBeInTheDocument()
      expect(screen.getByText('WRITE_CODE')).toBeInTheDocument()
      expect(screen.getByText('WRITE_TEST')).toBeInTheDocument()
      expect(screen.getByText('CODE_REVIEW')).toBeInTheDocument()
    })
  })

  describe('Task Status Icons', () => {
    it('should show completed icon for completed tasks', () => {
      const { container } = render(<TaskPlanTimeline {...defaultProps} />)
      // Completed tasks should have growth color
      const completedIcon = container.querySelector('.text-growth')
      expect(completedIcon).toBeInTheDocument()
    })

    it('should show running icon for running tasks', () => {
      const { container } = render(<TaskPlanTimeline {...defaultProps} />)
      // Running tasks should have calm color with animation
      const runningIcon = container.querySelector('.text-calm.animate-pulse')
      expect(runningIcon).toBeInTheDocument()
    })

    it('should show waiting approval icon', () => {
      const tasksWithApproval = [
        { id: 1, name: 'Task needing approval', status: 'waiting_approval', type: 'WRITE_CODE' }
      ]
      const { container } = render(<TaskPlanTimeline {...defaultProps} tasks={tasksWithApproval} />)
      // Waiting approval should have wisdom color
      const approvalIcon = container.querySelector('.text-wisdom')
      expect(approvalIcon).toBeInTheDocument()
    })

    it('should show failed icon for failed tasks', () => {
      const tasksWithFailed = [
        { id: 1, name: 'Failed task', status: 'failed', type: 'WRITE_CODE', errorMessage: 'Test error' }
      ]
      const { container } = render(<TaskPlanTimeline {...defaultProps} tasks={tasksWithFailed} />)
      // Failed tasks should have energy color
      const failedIcon = container.querySelector('.text-energy')
      expect(failedIcon).toBeInTheDocument()
    })
  })

  describe('Task Expansion', () => {
    it('should expand task to show details when clicked', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      
      // Description should not be visible initially
      expect(screen.queryByText('Analyze the codebase')).not.toBeInTheDocument()
      
      // Click expand button
      const expandButtons = screen.getAllByText('Expand')
      fireEvent.click(expandButtons[0])
      
      // Description should now be visible
      expect(screen.getByText('Analyze the codebase')).toBeInTheDocument()
    })

    it('should collapse task when clicked again', () => {
      render(<TaskPlanTimeline {...defaultProps} />)
      
      // Expand
      const expandButtons = screen.getAllByText('Expand')
      fireEvent.click(expandButtons[0])
      expect(screen.getByText('Analyze the codebase')).toBeInTheDocument()
      
      // Collapse
      fireEvent.click(screen.getByText('Collapse'))
      expect(screen.queryByText('Analyze the codebase')).not.toBeInTheDocument()
    })

    it('should show error message for failed tasks when expanded', () => {
      const tasksWithFailed = [
        { id: 1, name: 'Failed task', status: 'failed', type: 'WRITE_CODE', errorMessage: 'Test error message' }
      ]
      render(<TaskPlanTimeline {...defaultProps} tasks={tasksWithFailed} />)
      
      fireEvent.click(screen.getByText('Expand'))
      expect(screen.getByText('Test error message')).toBeInTheDocument()
    })

    it('should show timestamps when expanded', () => {
      const tasksWithTimestamps = [
        { 
          id: 1, 
          name: 'Task with timestamps', 
          status: 'completed', 
          type: 'WRITE_CODE',
          startedAt: '2024-01-15T10:00:00Z',
          completedAt: '2024-01-15T10:30:00Z',
          duration: '30m'
        }
      ]
      render(<TaskPlanTimeline {...defaultProps} tasks={tasksWithTimestamps} />)
      
      fireEvent.click(screen.getByText('Expand'))
      // Check that timestamps are displayed (format may vary)
      expect(screen.getByText(/Started/)).toBeInTheDocument()
      expect(screen.getByText(/Completed/)).toBeInTheDocument()
    })
  })

  describe('Approval Action', () => {
    it('should show approve button for waiting_approval tasks when expanded', () => {
      const tasksWithApproval = [
        { id: 1, name: 'Task needing approval', status: 'waiting_approval', type: 'WRITE_CODE', approvalReason: 'Needs review' }
      ]
      render(<TaskPlanTimeline {...defaultProps} tasks={tasksWithApproval} />)
      
      fireEvent.click(screen.getByText('Expand'))
      expect(screen.getByText('Approve')).toBeInTheDocument()
    })

    it('should call onTaskApprove when approve button is clicked', () => {
      const tasksWithApproval = [
        { id: 1, name: 'Task needing approval', status: 'waiting_approval', type: 'WRITE_CODE' }
      ]
      render(<TaskPlanTimeline {...defaultProps} tasks={tasksWithApproval} />)
      
      fireEvent.click(screen.getByText('Expand'))
      fireEvent.click(screen.getByText('Approve'))
      
      expect(defaultProps.onTaskApprove).toHaveBeenCalledWith(1)
    })
  })

  describe('Editable Mode', () => {
    it('should show drag handle when editable', () => {
      const { container } = render(<TaskPlanTimeline {...defaultProps} editable={true} />)
      // Should have grip vertical icons
      const gripIcons = container.querySelectorAll('.text-neutral-400')
      expect(gripIcons.length).toBeGreaterThan(0)
    })

    it('should show edit button for pending tasks when editable and expanded', () => {
      render(<TaskPlanTimeline {...defaultProps} editable={true} />)
      
      // Expand a pending task
      const expandButtons = screen.getAllByText('Expand')
      fireEvent.click(expandButtons[2]) // Third task is pending
      
      expect(screen.getByText('Edit Task')).toBeInTheDocument()
    })

    it('should call onTaskEdit when edit button is clicked', () => {
      render(<TaskPlanTimeline {...defaultProps} editable={true} />)
      
      // Expand a pending task
      const expandButtons = screen.getAllByText('Expand')
      fireEvent.click(expandButtons[2])
      
      fireEvent.click(screen.getByText('Edit Task'))
      expect(defaultProps.onTaskEdit).toHaveBeenCalledWith(mockTasks[2])
    })

    it('should not show edit button for non-pending tasks', () => {
      render(<TaskPlanTimeline {...defaultProps} editable={true} />)
      
      // Expand a completed task
      const expandButtons = screen.getAllByText('Expand')
      fireEvent.click(expandButtons[0])
      
      expect(screen.queryByText('Edit Task')).not.toBeInTheDocument()
    })

    it('should not show drag handle when not editable', () => {
      render(<TaskPlanTimeline {...defaultProps} editable={false} />)
      // When not editable, tasks should not be draggable
      const expandButtons = screen.getAllByText('Expand')
      // Check that none of the task containers have draggable="true"
      expandButtons.forEach(btn => {
        const taskContainer = btn.closest('[draggable="true"]')
        expect(taskContainer).toBeNull()
      })
    })
  })

  describe('Task Type Icons', () => {
    it('should render correct icon for each task type', () => {
      const allTaskTypes = [
        { id: 1, name: 'Analyze', status: 'pending', type: 'ANALYZE_CODE' },
        { id: 2, name: 'Write', status: 'pending', type: 'WRITE_CODE' },
        { id: 3, name: 'Test', status: 'pending', type: 'WRITE_TEST' },
        { id: 4, name: 'Run Test', status: 'pending', type: 'RUN_TEST' },
        { id: 5, name: 'Review', status: 'pending', type: 'CODE_REVIEW' },
        { id: 6, name: 'Setup', status: 'pending', type: 'SETUP_ENVIRONMENT' },
        { id: 7, name: 'Deploy', status: 'pending', type: 'DEPLOYMENT' },
        { id: 8, name: 'Verify', status: 'pending', type: 'VERIFICATION' },
        { id: 9, name: 'Document', status: 'pending', type: 'DOCUMENTATION' },
        { id: 10, name: 'Cleanup', status: 'pending', type: 'CLEANUP' }
      ]
      
      render(<TaskPlanTimeline {...defaultProps} tasks={allTaskTypes} totalTasks={10} />)
      
      // All task types should be rendered
      expect(screen.getByText('ANALYZE_CODE')).toBeInTheDocument()
      expect(screen.getByText('WRITE_CODE')).toBeInTheDocument()
      expect(screen.getByText('WRITE_TEST')).toBeInTheDocument()
      expect(screen.getByText('RUN_TEST')).toBeInTheDocument()
      expect(screen.getByText('CODE_REVIEW')).toBeInTheDocument()
      expect(screen.getByText('SETUP_ENVIRONMENT')).toBeInTheDocument()
      expect(screen.getByText('DEPLOYMENT')).toBeInTheDocument()
      expect(screen.getByText('VERIFICATION')).toBeInTheDocument()
      expect(screen.getByText('DOCUMENTATION')).toBeInTheDocument()
      expect(screen.getByText('CLEANUP')).toBeInTheDocument()
    })
  })

  describe('Status Colors', () => {
    it('should apply correct background color for completed tasks', () => {
      const { container } = render(<TaskPlanTimeline {...defaultProps} />)
      const completedCard = container.querySelector('.bg-growth-10')
      expect(completedCard).toBeInTheDocument()
    })

    it('should apply correct background color for running tasks', () => {
      const { container } = render(<TaskPlanTimeline {...defaultProps} />)
      const runningCard = container.querySelector('.bg-calm-10')
      expect(runningCard).toBeInTheDocument()
    })

    it('should apply correct background color for pending tasks', () => {
      const { container } = render(<TaskPlanTimeline {...defaultProps} />)
      const pendingCards = container.querySelectorAll('.bg-\\[var\\(--surface\\)\\]')
      expect(pendingCards.length).toBeGreaterThan(0)
    })
  })
})
