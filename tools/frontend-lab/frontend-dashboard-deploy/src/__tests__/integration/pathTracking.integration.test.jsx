/**
 * Integration tests for Path Tracking across components
 * Tests real user journeys with path tracking integration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import * as Sentry from '@sentry/react'
import LoginPage from '@/components/LoginPage'
import Dashboard from '@/components/Dashboard'
import DecisionApproval from '@/components/DecisionApproval'
import CostAnalysis from '@/components/CostAnalysis'
import StrategyManagement from '@/components/StrategyManagement'
import useAppStore from '@/stores/appStore'

vi.mock('@sentry/react', () => ({
  captureMessage: vi.fn(),
  captureException: vi.fn()
}))

vi.mock('@/lib/api', () => ({
  default: {
    login: vi.fn(),
    request: vi.fn()
  }
}))

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('Path Tracking Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    useAppStore.setState({ activePaths: {} })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Login Path Tracking', () => {
    it('should track successful login path', async () => {
      const mockOnLogin = vi.fn()
      const apiClient = await import('@/lib/api')
      apiClient.default.login.mockResolvedValue({
        user: { id: 1, name: 'Test User' },
        token: 'test-token'
      })

      renderWithRouter(<LoginPage onLogin={mockOnLogin} />)

      const usernameInput = screen.getByLabelText(/username|email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /login|登入/i })

      await userEvent.type(usernameInput, 'testuser')
      await userEvent.type(passwordInput, 'password123')
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(mockOnLogin).toHaveBeenCalled()
      })

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: user_login',
          expect.objectContaining({
            level: 'info',
            extra: expect.objectContaining({
              pathName: 'user_login',
              status: 'completed'
            })
          })
        )
      })
    })

    it('should track failed login path', async () => {
      const mockOnLogin = vi.fn()
      const apiClient = await import('@/lib/api')
      apiClient.default.login.mockRejectedValue(new Error('Invalid credentials'))

      renderWithRouter(<LoginPage onLogin={mockOnLogin} />)

      const usernameInput = screen.getByLabelText(/username|email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /login|登入/i })

      await userEvent.type(usernameInput, 'wronguser')
      await userEvent.type(passwordInput, 'wrongpass')
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(Sentry.captureException).toHaveBeenCalledWith(
          expect.any(Error),
          expect.objectContaining({
            extra: expect.objectContaining({
              pathName: 'user_login'
            })
          })
        )
      })
    })

    it('should trigger TTV event on first login', async () => {
      const mockOnLogin = vi.fn()
      const apiClient = await import('@/lib/api')
      apiClient.default.login.mockResolvedValue({
        user: { id: 1, name: 'Test User' },
        token: 'test-token'
      })

      const eventListener = vi.fn()
      window.addEventListener('first-value-operation', eventListener)

      renderWithRouter(<LoginPage onLogin={mockOnLogin} />)

      const usernameInput = screen.getByLabelText(/username|email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /login|登入/i })

      await userEvent.type(usernameInput, 'admin')
      await userEvent.type(passwordInput, 'admin123')
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(eventListener).toHaveBeenCalledWith(
          expect.objectContaining({
            detail: { operation: 'user_login' }
          })
        )
      })

      window.removeEventListener('first-value-operation', eventListener)
    })
  })

  describe('Dashboard Path Tracking', () => {
    it('should track dashboard save layout path', async () => {
      const apiClient = await import('@/lib/api')
      apiClient.default.request.mockResolvedValue({ success: true })

      renderWithRouter(<Dashboard />)

      const saveButton = screen.getByRole('button', { name: /save|儲存/i })
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: dashboard_save_layout',
          expect.objectContaining({
            level: 'info',
            extra: expect.objectContaining({
              pathName: 'dashboard_save_layout',
              status: 'completed'
            })
          })
        )
      })
    })

    it('should track failed dashboard save', async () => {
      const apiClient = await import('@/lib/api')
      apiClient.default.request.mockRejectedValue(new Error('Network error'))

      renderWithRouter(<Dashboard />)

      const saveButton = screen.getByRole('button', { name: /save|儲存/i })
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(Sentry.captureException).toHaveBeenCalledWith(
          expect.any(Error),
          expect.objectContaining({
            extra: expect.objectContaining({
              pathName: 'dashboard_save_layout'
            })
          })
        )
      })
    })
  })

  describe('Decision Approval Path Tracking', () => {
    it('should track decision approval path', async () => {
      renderWithRouter(<DecisionApproval />)

      const approveButtons = screen.getAllByRole('button', { name: /approve|批准/i })
      await userEvent.click(approveButtons[0])

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: decision_approve',
          expect.objectContaining({
            level: 'info',
            extra: expect.objectContaining({
              pathName: 'decision_approve',
              status: 'completed'
            })
          })
        )
      })
    })

    it('should track decision rejection path', async () => {
      renderWithRouter(<DecisionApproval />)

      const rejectButtons = screen.getAllByRole('button', { name: /reject|拒絕/i })
      await userEvent.click(rejectButtons[0])

      const commentInput = screen.getByPlaceholderText(/comment|理由/i)
      await userEvent.type(commentInput, 'Not suitable for current strategy')

      const confirmButton = screen.getByRole('button', { name: /confirm|確認/i })
      await userEvent.click(confirmButton)

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: decision_reject',
          expect.objectContaining({
            level: 'info',
            extra: expect.objectContaining({
              pathName: 'decision_reject',
              status: 'completed'
            })
          })
        )
      })
    })

    it('should trigger TTV event on decision approval', async () => {
      const eventListener = vi.fn()
      window.addEventListener('first-value-operation', eventListener)

      renderWithRouter(<DecisionApproval />)

      const approveButtons = screen.getAllByRole('button', { name: /approve|批准/i })
      await userEvent.click(approveButtons[0])

      await waitFor(() => {
        expect(eventListener).toHaveBeenCalledWith(
          expect.objectContaining({
            detail: { operation: 'decision_approve' }
          })
        )
      })

      window.removeEventListener('first-value-operation', eventListener)
    })
  })

  describe('Cost Analysis Path Tracking', () => {
    it('should track cost analysis view on mount', async () => {
      renderWithRouter(<CostAnalysis />)

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: cost_analysis_view',
          expect.objectContaining({
            level: 'info',
            extra: expect.objectContaining({
              pathName: 'cost_analysis_view',
              status: 'completed'
            })
          })
        )
      }, { timeout: 1000 })
    })

    it('should trigger TTV event on cost analysis view', async () => {
      const eventListener = vi.fn()
      window.addEventListener('first-value-operation', eventListener)

      renderWithRouter(<CostAnalysis />)

      await waitFor(() => {
        expect(eventListener).toHaveBeenCalledWith(
          expect.objectContaining({
            detail: { operation: 'cost_analysis_view' }
          })
        )
      }, { timeout: 1000 })

      window.removeEventListener('first-value-operation', eventListener)
    })
  })

  describe('Strategy Management Path Tracking', () => {
    it('should track strategy management view on mount', async () => {
      renderWithRouter(<StrategyManagement />)

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: strategy_management_view',
          expect.objectContaining({
            level: 'info',
            extra: expect.objectContaining({
              pathName: 'strategy_management_view',
              status: 'completed'
            })
          })
        )
      }, { timeout: 1000 })
    })

    it('should trigger TTV event on strategy management view', async () => {
      const eventListener = vi.fn()
      window.addEventListener('first-value-operation', eventListener)

      renderWithRouter(<StrategyManagement />)

      await waitFor(() => {
        expect(eventListener).toHaveBeenCalledWith(
          expect.objectContaining({
            detail: { operation: 'strategy_management_view' }
          })
        )
      }, { timeout: 1000 })

      window.removeEventListener('first-value-operation', eventListener)
    })
  })

  describe('Complete User Journey', () => {
    it('should track multiple paths in sequence', async () => {
      const mockOnLogin = vi.fn()
      const apiClient = await import('@/lib/api')
      apiClient.default.login.mockResolvedValue({
        user: { id: 1, name: 'Test User' },
        token: 'test-token'
      })
      apiClient.default.request.mockResolvedValue({ success: true })

      const { unmount } = renderWithRouter(<LoginPage onLogin={mockOnLogin} />)

      const usernameInput = screen.getByLabelText(/username|email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /login|登入/i })

      await userEvent.type(usernameInput, 'admin')
      await userEvent.type(passwordInput, 'admin123')
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: user_login',
          expect.any(Object)
        )
      })

      unmount()

      renderWithRouter(<Dashboard />)

      const saveButton = screen.getByRole('button', { name: /save|儲存/i })
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: dashboard_save_layout',
          expect.any(Object)
        )
      })

      expect(Sentry.captureMessage).toHaveBeenCalledTimes(2)
    })
  })

  describe('Concurrent Path Tracking', () => {
    it('should handle multiple concurrent paths', async () => {
      const apiClient = await import('@/lib/api')
      apiClient.default.request.mockResolvedValue({ success: true })

      renderWithRouter(
        <>
          <Dashboard />
          <DecisionApproval />
        </>
      )

      const saveButton = screen.getByRole('button', { name: /save|儲存/i })
      const approveButtons = screen.getAllByRole('button', { name: /approve|批准/i })

      await Promise.all([
        userEvent.click(saveButton),
        userEvent.click(approveButtons[0])
      ])

      await waitFor(() => {
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: dashboard_save_layout',
          expect.any(Object)
        )
        expect(Sentry.captureMessage).toHaveBeenCalledWith(
          'Path completed: decision_approve',
          expect.any(Object)
        )
      })

      expect(Sentry.captureMessage).toHaveBeenCalledTimes(2)
    })
  })
})
