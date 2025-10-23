/**
 * Unit tests for Path Tracking functionality in appStore
 * Tests trackPathStart, trackPathComplete, trackPathFail methods
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import useAppStore from '../appStore'
import * as Sentry from '@sentry/react'

vi.mock('@sentry/react', () => ({
  captureMessage: vi.fn(),
  captureException: vi.fn()
}))

describe('appStore - Path Tracking', () => {
  beforeEach(() => {
    const { result } = renderHook(() => useAppStore())
    act(() => {
      result.current.activePaths = {}
    })
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('trackPathStart', () => {
    it('should create a new path with unique ID', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      expect(pathId).toBeDefined()
      expect(typeof pathId).toBe('string')
      expect(pathId).toMatch(/^test_path_\d+$/)
    })

    it('should store path in activePaths', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      const activePath = result.current.activePaths[pathId]
      expect(activePath).toBeDefined()
      expect(activePath.pathName).toBe('test_path')
      expect(activePath.startTime).toBeInstanceOf(Date)
      expect(activePath.status).toBe('in_progress')
    })

    it('should handle multiple concurrent paths', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId1, pathId2
      act(() => {
        pathId1 = result.current.trackPathStart('path_1')
        pathId2 = result.current.trackPathStart('path_2')
      })

      expect(result.current.activePaths[pathId1]).toBeDefined()
      expect(result.current.activePaths[pathId2]).toBeDefined()
      expect(pathId1).not.toBe(pathId2)
    })
  })

  describe('trackPathComplete', () => {
    it('should mark path as completed and calculate duration', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      act(() => {
        result.current.trackPathComplete(pathId)
      })

      const completedPath = result.current.activePaths[pathId]
      expect(completedPath.status).toBe('completed')
      expect(completedPath.endTime).toBeInstanceOf(Date)
      expect(completedPath.duration).toBeGreaterThanOrEqual(0)
    })

    it('should send data to Sentry', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      act(() => {
        result.current.trackPathComplete(pathId)
      })

      expect(Sentry.captureMessage).toHaveBeenCalledWith(
        'Path completed: test_path',
        expect.objectContaining({
          level: 'info',
          extra: expect.objectContaining({
            pathId,
            pathName: 'test_path',
            duration: expect.any(Number),
            status: 'completed'
          })
        })
      )
    })

    it('should handle non-existent path gracefully', () => {
      const { result } = renderHook(() => useAppStore())
      
      expect(() => {
        act(() => {
          result.current.trackPathComplete('non_existent_path')
        })
      }).not.toThrow()
    })

    it('should cleanup path after 5 minutes', () => {
      vi.useFakeTimers()
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      act(() => {
        result.current.trackPathComplete(pathId)
      })

      expect(result.current.activePaths[pathId]).toBeDefined()

      act(() => {
        vi.advanceTimersByTime(5 * 60 * 1000)
      })

      expect(result.current.activePaths[pathId]).toBeUndefined()

      vi.useRealTimers()
    })
  })

  describe('trackPathFail', () => {
    it('should mark path as failed and store error', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      const testError = new Error('Test error')
      act(() => {
        result.current.trackPathFail(pathId, testError)
      })

      const failedPath = result.current.activePaths[pathId]
      expect(failedPath.status).toBe('failed')
      expect(failedPath.endTime).toBeInstanceOf(Date)
      expect(failedPath.error).toBe('Test error')
    })

    it('should send error to Sentry', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      const testError = new Error('Test error')
      act(() => {
        result.current.trackPathFail(pathId, testError)
      })

      expect(Sentry.captureException).toHaveBeenCalledWith(testError, {
        extra: expect.objectContaining({
          pathId,
          pathName: 'test_path',
          duration: expect.any(Number)
        })
      })
    })

    it('should handle string error messages', () => {
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      act(() => {
        result.current.trackPathFail(pathId, 'String error message')
      })

      const failedPath = result.current.activePaths[pathId]
      expect(failedPath.error).toBe('String error message')
    })

    it('should handle non-existent path gracefully', () => {
      const { result } = renderHook(() => useAppStore())
      
      expect(() => {
        act(() => {
          result.current.trackPathFail('non_existent_path', new Error('Test'))
        })
      }).not.toThrow()
    })

    it('should cleanup path after 5 minutes', () => {
      vi.useFakeTimers()
      const { result } = renderHook(() => useAppStore())
      
      let pathId
      act(() => {
        pathId = result.current.trackPathStart('test_path')
      })

      act(() => {
        result.current.trackPathFail(pathId, new Error('Test'))
      })

      expect(result.current.activePaths[pathId]).toBeDefined()

      act(() => {
        vi.advanceTimersByTime(5 * 60 * 1000)
      })

      expect(result.current.activePaths[pathId]).toBeUndefined()

      vi.useRealTimers()
    })
  })

  describe('Path Tracking Integration', () => {
    it('should track complete user journey', () => {
      const { result } = renderHook(() => useAppStore())
      
      let loginPathId, dashboardPathId
      
      act(() => {
        loginPathId = result.current.trackPathStart('user_login')
      })
      
      expect(result.current.activePaths[loginPathId].status).toBe('in_progress')
      
      act(() => {
        result.current.trackPathComplete(loginPathId)
      })
      
      expect(result.current.activePaths[loginPathId].status).toBe('completed')
      
      act(() => {
        dashboardPathId = result.current.trackPathStart('dashboard_save_layout')
      })
      
      expect(result.current.activePaths[dashboardPathId].status).toBe('in_progress')
      
      act(() => {
        result.current.trackPathComplete(dashboardPathId)
      })
      
      expect(result.current.activePaths[dashboardPathId].status).toBe('completed')
      expect(Sentry.captureMessage).toHaveBeenCalledTimes(2)
    })

    it('should handle mixed success and failure paths', () => {
      const { result } = renderHook(() => useAppStore())
      
      let successPathId, failPathId
      
      act(() => {
        successPathId = result.current.trackPathStart('success_path')
        failPathId = result.current.trackPathStart('fail_path')
      })
      
      act(() => {
        result.current.trackPathComplete(successPathId)
        result.current.trackPathFail(failPathId, new Error('Failed'))
      })
      
      expect(result.current.activePaths[successPathId].status).toBe('completed')
      expect(result.current.activePaths[failPathId].status).toBe('failed')
      expect(Sentry.captureMessage).toHaveBeenCalledTimes(1)
      expect(Sentry.captureException).toHaveBeenCalledTimes(1)
    })
  })

  describe('Memory Management', () => {
    it('should not leak memory with many paths', () => {
      vi.useFakeTimers()
      const { result } = renderHook(() => useAppStore())
      
      const pathIds = []
      act(() => {
        for (let i = 0; i < 100; i++) {
          const pathId = result.current.trackPathStart(`path_${i}`)
          pathIds.push(pathId)
          result.current.trackPathComplete(pathId)
        }
      })
      
      expect(Object.keys(result.current.activePaths).length).toBe(100)
      
      act(() => {
        vi.advanceTimersByTime(5 * 60 * 1000)
      })
      
      expect(Object.keys(result.current.activePaths).length).toBe(0)
      
      vi.useRealTimers()
    })
  })
})
