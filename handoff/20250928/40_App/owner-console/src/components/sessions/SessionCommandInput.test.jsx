import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SessionCommandInput from './SessionCommandInput'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key, fallback) => fallback || key
  })
}))

vi.mock('@morningai/shared-ui', () => ({
  AppleButton: ({ children, onClick, disabled, ...props }) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  )
}))

describe('SessionCommandInput', () => {
  const defaultProps = {
    sessionId: 'test-session-123',
    sessionStatus: 'running',
    onSendCommand: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders command input and quick action buttons', () => {
      render(<SessionCommandInput {...defaultProps} />)

      expect(screen.getByPlaceholderText('Type a command or instruction...')).toBeInTheDocument()
      expect(screen.getByText('Quick actions:')).toBeInTheDocument()
      expect(screen.getByText('Continue')).toBeInTheDocument()
      expect(screen.getByText('Explain current step')).toBeInTheDocument()
      expect(screen.getByText('Skip this task')).toBeInTheDocument()
      expect(screen.getByText('Retry last action')).toBeInTheDocument()
    })

    it('returns null when session status is completed', () => {
      const { container } = render(
        <SessionCommandInput {...defaultProps} sessionStatus="completed" />
      )
      expect(container.firstChild).toBeNull()
    })

    it('returns null when session status is failed', () => {
      const { container } = render(
        <SessionCommandInput {...defaultProps} sessionStatus="failed" />
      )
      expect(container.firstChild).toBeNull()
    })

    it('returns null when session status is cancelled', () => {
      const { container } = render(
        <SessionCommandInput {...defaultProps} sessionStatus="cancelled" />
      )
      expect(container.firstChild).toBeNull()
    })

    it('returns null when disabled prop is true', () => {
      const { container } = render(
        <SessionCommandInput {...defaultProps} disabled={true} />
      )
      expect(container.firstChild).toBeNull()
    })

    it('renders for running session status', () => {
      render(<SessionCommandInput {...defaultProps} sessionStatus="running" />)
      expect(screen.getByPlaceholderText('Type a command or instruction...')).toBeInTheDocument()
    })

    it('renders for paused session status', () => {
      render(<SessionCommandInput {...defaultProps} sessionStatus="paused" />)
      expect(screen.getByPlaceholderText('Type a command or instruction...')).toBeInTheDocument()
    })
  })

  describe('Quick Commands', () => {
    it('calls onSendCommand with correct data when Continue is clicked', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      await userEvent.click(screen.getByText('Continue'))

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            sessionId: 'test-session-123',
            command: 'continue',
            type: 'quick_command'
          })
        )
      })
    })

    it('calls onSendCommand with correct data when Explain is clicked', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      await userEvent.click(screen.getByText('Explain current step'))

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            sessionId: 'test-session-123',
            command: 'explain',
            type: 'quick_command'
          })
        )
      })
    })

    it('calls onSendCommand with correct data when Skip is clicked', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      await userEvent.click(screen.getByText('Skip this task'))

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            sessionId: 'test-session-123',
            command: 'skip',
            type: 'quick_command'
          })
        )
      })
    })

    it('calls onSendCommand with correct data when Retry is clicked', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      await userEvent.click(screen.getByText('Retry last action'))

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            sessionId: 'test-session-123',
            command: 'retry',
            type: 'quick_command'
          })
        )
      })
    })

    it('disables quick command buttons while sending', async () => {
      const onSendCommand = vi.fn().mockImplementation(() => new Promise(() => {}))
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      await userEvent.click(screen.getByText('Continue'))

      const buttons = screen.getAllByRole('button')
      const quickButtons = buttons.filter(btn => btn.textContent.includes('Continue') || 
        btn.textContent.includes('Explain') || 
        btn.textContent.includes('Skip') || 
        btn.textContent.includes('Retry'))
      
      quickButtons.forEach(btn => {
        expect(btn).toBeDisabled()
      })
    })
  })

  describe('User Command Input', () => {
    it('sends user command when Enter is pressed', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            sessionId: 'test-session-123',
            command: 'test command'
          })
        )
      })
    })

    it('does not send command when Shift+Enter is pressed', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Shift>}{Enter}{/Shift}')

      expect(onSendCommand).not.toHaveBeenCalled()
    })

    it('clears input after successful send', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(input).toHaveValue('')
      })
    })

    it('does not send empty command', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.click(input)
      await userEvent.keyboard('{Enter}')

      expect(onSendCommand).not.toHaveBeenCalled()
    })

    it('does not send whitespace-only command', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, '   ')
      await userEvent.keyboard('{Enter}')

      expect(onSendCommand).not.toHaveBeenCalled()
    })

    it('trims command before sending', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, '  test command  ')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            command: 'test command'
          })
        )
      })
    })
  })

  describe('Command History Navigation', () => {
    it('navigates to previous command with ArrowUp', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      
      await userEvent.type(input, 'first command')
      await userEvent.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledTimes(1)
      })

      const textarea = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(textarea, 'second command')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledTimes(2)
      })

      const currentInput = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.click(currentInput)
      await userEvent.keyboard('{ArrowUp}')

      await waitFor(() => {
        const inputAfterNav = screen.getByPlaceholderText('Type a command or instruction...')
        expect(inputAfterNav).toHaveValue('second command')
      })
    })

    it('navigates forward in history with ArrowDown', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      
      await userEvent.type(input, 'first command')
      await userEvent.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledTimes(1)
      })

      const textarea = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(textarea, 'second command')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledTimes(2)
      })

      const currentInput = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.click(currentInput)
      await userEvent.keyboard('{ArrowUp}')

      await waitFor(() => {
        const inputAfterNav = screen.getByPlaceholderText('Type a command or instruction...')
        expect(inputAfterNav).toHaveValue('second command')
      })

      await userEvent.keyboard('{ArrowDown}')

      await waitFor(() => {
        const inputAfterDown = screen.getByPlaceholderText('Type a command or instruction...')
        expect(inputAfterDown).toHaveValue('')
      })
    })

    it('does not navigate history when input has text', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      
      await userEvent.type(input, 'first command')
      await userEvent.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledTimes(1)
      })

      const textarea = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(textarea, 'current text')
      
      const beforeArrowUp = screen.getByPlaceholderText('Type a command or instruction...')
      const valueBefore = beforeArrowUp.value
      
      await userEvent.keyboard('{ArrowUp}')

      const afterArrowUp = screen.getByPlaceholderText('Type a command or instruction...')
      expect(afterArrowUp).toHaveValue(valueBefore)
    })
  })

  describe('Escape Key', () => {
    it('clears input and collapses on Escape', async () => {
      render(<SessionCommandInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Escape}')

      expect(input).toHaveValue('')
    })
  })

  describe('isSending State', () => {
    it('prevents double submit while sending', async () => {
      const onSendCommand = vi.fn().mockImplementation(() => new Promise(() => {}))
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Enter}')

      fireEvent.change(input, { target: { value: 'another command' } })
      await userEvent.keyboard('{Enter}')

      expect(onSendCommand).toHaveBeenCalledTimes(1)
    })
  })

  describe('Expanded State', () => {
    it('expands to textarea on focus', async () => {
      render(<SessionCommandInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      expect(input.tagName).toBe('INPUT')

      await userEvent.click(input)

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText('Type a command or instruction...')
        expect(textarea.tagName).toBe('TEXTAREA')
      })
    })

    it('shows hint text when expanded', async () => {
      render(<SessionCommandInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.click(input)

      await waitFor(() => {
        expect(screen.getByText('Press Enter to send, Shift+Enter for new line, Esc to cancel')).toBeInTheDocument()
      })
    })

    it('shows collapse button when expanded', async () => {
      render(<SessionCommandInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.click(input)

      await waitFor(() => {
        expect(screen.getByLabelText('Collapse input')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('handles onSendCommand error gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const onSendCommand = vi.fn().mockRejectedValue(new Error('Network error'))
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to send command:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })

    it('handles quick command error gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const onSendCommand = vi.fn().mockRejectedValue(new Error('Network error'))
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      await userEvent.click(screen.getByText('Continue'))

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to send quick command:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Accessibility', () => {
    it('has proper aria-labels on input', () => {
      render(<SessionCommandInput {...defaultProps} />)

      expect(screen.getByLabelText('Command input')).toBeInTheDocument()
    })

    it('has proper aria-labels on quick command buttons', () => {
      render(<SessionCommandInput {...defaultProps} />)

      expect(screen.getByLabelText('Continue')).toBeInTheDocument()
      expect(screen.getByLabelText('Explain current step')).toBeInTheDocument()
      expect(screen.getByLabelText('Skip this task')).toBeInTheDocument()
      expect(screen.getByLabelText('Retry last action')).toBeInTheDocument()
    })

    it('has proper aria-label on send button', () => {
      render(<SessionCommandInput {...defaultProps} />)

      expect(screen.getByLabelText('Send command')).toBeInTheDocument()
    })
  })

  describe('Timestamp', () => {
    it('includes timestamp in command payload', async () => {
      const onSendCommand = vi.fn().mockResolvedValue(undefined)
      render(<SessionCommandInput {...defaultProps} onSendCommand={onSendCommand} />)

      const input = screen.getByPlaceholderText('Type a command or instruction...')
      await userEvent.type(input, 'test command')
      await userEvent.keyboard('{Enter}')

      await waitFor(() => {
        expect(onSendCommand).toHaveBeenCalledWith(
          expect.objectContaining({
            timestamp: expect.any(String)
          })
        )
      })

      const call = onSendCommand.mock.calls[0][0]
      expect(new Date(call.timestamp).toISOString()).toBe(call.timestamp)
    })
  })
})
