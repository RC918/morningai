import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskEditor from '../TaskEditor'

// Mock react-i18next
const mockT = (key, fallback) => fallback || key
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

describe('TaskEditor', () => {
  const mockTask = {
    id: 1,
    name: 'Write unit tests',
    description: 'Add comprehensive unit tests for the component',
    type: 'WRITE_TEST'
  }

  const defaultProps = {
    task: mockTask,
    isOpen: true,
    onClose: vi.fn(),
    onSave: vi.fn(),
    onDelete: vi.fn(),
    isNewTask: false
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Dialog Rendering', () => {
    it('should render dialog when isOpen is true', () => {
      render(<TaskEditor {...defaultProps} />)
      expect(screen.getByText('Edit Task')).toBeInTheDocument()
    })

    it('should not render dialog content when isOpen is false', () => {
      render(<TaskEditor {...defaultProps} isOpen={false} />)
      expect(screen.queryByText('Edit Task')).not.toBeInTheDocument()
    })

    it('should show Add New Task title when isNewTask is true', () => {
      render(<TaskEditor {...defaultProps} isNewTask={true} />)
      expect(screen.getByText('Add New Task')).toBeInTheDocument()
    })
  })

  describe('Form Fields', () => {
    it('should display task name input with current value', () => {
      render(<TaskEditor {...defaultProps} />)
      const nameInput = screen.getByLabelText(/Task Name/)
      expect(nameInput.value).toBe('Write unit tests')
    })

    it('should display task description textarea with current value', () => {
      render(<TaskEditor {...defaultProps} />)
      const descInput = screen.getByLabelText(/Description/)
      expect(descInput.value).toBe('Add comprehensive unit tests for the component')
    })

    it('should display task type selector with current value selected', () => {
      render(<TaskEditor {...defaultProps} />)
      // The WRITE_TEST button should be selected (has primary styling)
      const writeTestButton = screen.getByText('Write Test')
      expect(writeTestButton.closest('button')).toHaveClass('border-primary-500')
    })

    it('should allow changing task name', () => {
      render(<TaskEditor {...defaultProps} />)
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: 'New task name' } })
      expect(nameInput.value).toBe('New task name')
    })

    it('should allow changing task description', () => {
      render(<TaskEditor {...defaultProps} />)
      const descInput = screen.getByLabelText(/Description/)
      fireEvent.change(descInput, { target: { value: 'New description' } })
      expect(descInput.value).toBe('New description')
    })

    it('should allow changing task type', () => {
      render(<TaskEditor {...defaultProps} />)
      const codeReviewButton = screen.getByText('Code Review')
      fireEvent.click(codeReviewButton)
      expect(codeReviewButton.closest('button')).toHaveClass('border-primary-500')
    })
  })

  describe('Task Types', () => {
    it('should display all task type options', () => {
      render(<TaskEditor {...defaultProps} />)
      expect(screen.getByText('Analyze Code')).toBeInTheDocument()
      expect(screen.getByText('Write Code')).toBeInTheDocument()
      expect(screen.getByText('Write Test')).toBeInTheDocument()
      expect(screen.getByText('Run Test')).toBeInTheDocument()
      expect(screen.getByText('Code Review')).toBeInTheDocument()
      expect(screen.getByText('Setup Environment')).toBeInTheDocument()
      expect(screen.getByText('Deployment')).toBeInTheDocument()
      expect(screen.getByText('Verification')).toBeInTheDocument()
      expect(screen.getByText('Documentation')).toBeInTheDocument()
      expect(screen.getByText('Cleanup')).toBeInTheDocument()
    })
  })

  describe('Validation', () => {
    it('should show error when task name is empty', () => {
      render(<TaskEditor {...defaultProps} />)
      
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: '' } })
      
      fireEvent.click(screen.getByText('Save'))
      
      expect(screen.getByText('Task name is required')).toBeInTheDocument()
      expect(defaultProps.onSave).not.toHaveBeenCalled()
    })

    it('should show error when task name is too long', () => {
      render(<TaskEditor {...defaultProps} />)
      
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: 'a'.repeat(201) } })
      
      fireEvent.click(screen.getByText('Save'))
      
      expect(screen.getByText('Task name must be less than 200 characters')).toBeInTheDocument()
      expect(defaultProps.onSave).not.toHaveBeenCalled()
    })

    it('should clear error when user starts typing', () => {
      render(<TaskEditor {...defaultProps} />)
      
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: '' } })
      fireEvent.click(screen.getByText('Save'))
      
      expect(screen.getByText('Task name is required')).toBeInTheDocument()
      
      fireEvent.change(nameInput, { target: { value: 'New name' } })
      expect(screen.queryByText('Task name is required')).not.toBeInTheDocument()
    })
  })

  describe('Save Action', () => {
    it('should call onSave with updated task data', () => {
      render(<TaskEditor {...defaultProps} />)
      
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: 'Updated task name' } })
      
      const descInput = screen.getByLabelText(/Description/)
      fireEvent.change(descInput, { target: { value: 'Updated description' } })
      
      fireEvent.click(screen.getByText('Code Review'))
      
      fireEvent.click(screen.getByText('Save'))
      
      expect(defaultProps.onSave).toHaveBeenCalledWith({
        ...mockTask,
        name: 'Updated task name',
        description: 'Updated description',
        type: 'CODE_REVIEW'
      })
    })

    it('should trim whitespace from name and description', () => {
      render(<TaskEditor {...defaultProps} />)
      
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: '  Trimmed name  ' } })
      
      const descInput = screen.getByLabelText(/Description/)
      fireEvent.change(descInput, { target: { value: '  Trimmed description  ' } })
      
      fireEvent.click(screen.getByText('Save'))
      
      expect(defaultProps.onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Trimmed name',
          description: 'Trimmed description'
        })
      )
    })

    it('should call onClose after successful save', () => {
      render(<TaskEditor {...defaultProps} />)
      fireEvent.click(screen.getByText('Save'))
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Delete Action', () => {
    it('should show delete button when not a new task', () => {
      render(<TaskEditor {...defaultProps} isNewTask={false} />)
      expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    it('should not show delete button when is a new task', () => {
      render(<TaskEditor {...defaultProps} isNewTask={true} />)
      expect(screen.queryByText('Delete')).not.toBeInTheDocument()
    })

    it('should not show delete button when onDelete is not provided', () => {
      render(<TaskEditor {...defaultProps} onDelete={undefined} />)
      expect(screen.queryByText('Delete')).not.toBeInTheDocument()
    })

    it('should call onDelete with task id when delete is clicked', () => {
      render(<TaskEditor {...defaultProps} />)
      fireEvent.click(screen.getByText('Delete'))
      expect(defaultProps.onDelete).toHaveBeenCalledWith(1)
    })

    it('should call onClose after delete', () => {
      render(<TaskEditor {...defaultProps} />)
      fireEvent.click(screen.getByText('Delete'))
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  describe('Cancel Action', () => {
    it('should call onClose when cancel is clicked', () => {
      render(<TaskEditor {...defaultProps} />)
      fireEvent.click(screen.getByText('Cancel'))
      expect(defaultProps.onClose).toHaveBeenCalled()
    })

    it('should not call onSave when cancel is clicked', () => {
      render(<TaskEditor {...defaultProps} />)
      fireEvent.click(screen.getByText('Cancel'))
      expect(defaultProps.onSave).not.toHaveBeenCalled()
    })
  })

  describe('Form Reset', () => {
    it('should reset form when dialog opens with different task', () => {
      const { rerender } = render(<TaskEditor {...defaultProps} />)
      
      // Change the name
      const nameInput = screen.getByLabelText(/Task Name/)
      fireEvent.change(nameInput, { target: { value: 'Changed name' } })
      
      // Close and reopen with different task
      rerender(<TaskEditor {...defaultProps} isOpen={false} />)
      rerender(<TaskEditor {...defaultProps} isOpen={true} task={{ ...mockTask, name: 'Different task' }} />)
      
      // Should show the new task's name
      expect(screen.getByLabelText(/Task Name/).value).toBe('Different task')
    })

    it('should use default type when task has no type', () => {
      render(<TaskEditor {...defaultProps} task={{ id: 1, name: 'No type task' }} />)
      
      // Default type is WRITE_CODE
      const writeCodeButton = screen.getByText('Write Code')
      expect(writeCodeButton.closest('button')).toHaveClass('border-primary-500')
    })
  })

  describe('New Task Mode', () => {
    it('should start with empty fields for new task', () => {
      render(<TaskEditor {...defaultProps} task={null} isNewTask={true} />)
      
      const nameInput = screen.getByLabelText(/Task Name/)
      expect(nameInput.value).toBe('')
      
      const descInput = screen.getByLabelText(/Description/)
      expect(descInput.value).toBe('')
    })

    it('should use default type for new task', () => {
      render(<TaskEditor {...defaultProps} task={null} isNewTask={true} />)
      
      // Default type is WRITE_CODE
      const writeCodeButton = screen.getByText('Write Code')
      expect(writeCodeButton.closest('button')).toHaveClass('border-primary-500')
    })
  })
})
