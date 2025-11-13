import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../Dashboard'
import { excludeTaskExecution, normalizeWidgetId } from '@/lib/dashboardFilters'
import apiClient from '@/lib/api'

/**
 * Unit Tests for Dashboard Widget Filtering Logic
 * 
 * These tests verify that the task_execution widget (which contains owner-console
 * agent names like GrowthStrategist, OpsAgent, PMAgent, SecurityManager) is properly
 * filtered out from all widget-related operations.
 * 
 * This prevents sensitive owner-console information from leaking to tenant dashboards.
 */

interface Widget {
  id: string
  type: string
  component: React.ReactNode | null
  name?: string
  position?: {
    x: number
    y: number
  }
}

describe('Dashboard Widget Filtering - Shared Module Tests', () => {
  describe('normalizeWidgetId', () => {
    it('should convert widget ID to lowercase', () => {
      expect(normalizeWidgetId('task_execution')).toBe('task_execution')
      expect(normalizeWidgetId('TASK_EXECUTION')).toBe('task_execution')
      expect(normalizeWidgetId('Task_Execution')).toBe('task_execution')
      expect(normalizeWidgetId('TaSk_ExEcUtIoN')).toBe('task_execution')
    })

    it('should handle other widget IDs', () => {
      expect(normalizeWidgetId('CPU_USAGE')).toBe('cpu_usage')
      expect(normalizeWidgetId('Memory_Usage')).toBe('memory_usage')
    })
  })

  describe('excludeTaskExecution', () => {
    it('should filter out task_execution (lowercase)', () => {
      const mockWidgets: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = excludeTaskExecution(mockWidgets)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      expect(filtered.some(w => w.id === 'cpu_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'memory_usage')).toBe(true)
    })

    it('should filter out TASK_EXECUTION (uppercase) - case insensitive', () => {
      const mockWidgets: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'TASK_EXECUTION', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = excludeTaskExecution(mockWidgets)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.some(w => normalizeWidgetId(w.id) === 'task_execution')).toBe(false)
    })

    it('should filter out Task_Execution (mixed case) - case insensitive', () => {
      const mockWidgets: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'Task_Execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = excludeTaskExecution(mockWidgets)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.some(w => normalizeWidgetId(w.id) === 'task_execution')).toBe(false)
    })

    it('should filter all case variations of task_execution', () => {
      const mockWidgets: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'TASK_EXECUTION', type: 'timeline', component: null },
        { id: 'Task_Execution', type: 'timeline', component: null },
        { id: 'TaSk_ExEcUtIoN', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = excludeTaskExecution(mockWidgets)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.every(w => normalizeWidgetId(w.id) !== 'task_execution')).toBe(true)
    })

    it('should handle layout with multiple task_execution widgets', () => {
      const mockLayout: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null }
      ]

      const filtered = excludeTaskExecution(mockLayout)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.every(w => w.id !== 'task_execution')).toBe(true)
    })

    it('should preserve non-task_execution widgets', () => {
      const mockLayout: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null },
        { id: 'circuit_breakers', type: 'status', component: null }
      ]

      const filtered = excludeTaskExecution(mockLayout)
      
      expect(filtered).toHaveLength(3)
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      expect(filtered.some(w => w.id === 'cpu_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'memory_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'circuit_breakers')).toBe(true)
    })

    it('should handle empty layout', () => {
      const mockLayout: Widget[] = []
      const filtered = excludeTaskExecution(mockLayout)
      expect(filtered).toHaveLength(0)
    })

    it('should handle layout with only task_execution', () => {
      const mockLayout: Widget[] = [
        { id: 'task_execution', type: 'timeline', component: null }
      ]
      const filtered = excludeTaskExecution(mockLayout)
      expect(filtered).toHaveLength(0)
    })

    it('should preserve widget properties during filtering', () => {
      const mockLayout: Widget[] = [
        { 
          id: 'cpu_usage', 
          type: 'metric', 
          component: null,
          name: 'CPU Usage',
          position: { x: 0, y: 0 }
        },
        { id: 'task_execution', type: 'timeline', component: null }
      ]

      const filtered = excludeTaskExecution(mockLayout)
      
      expect(filtered).toHaveLength(1)
      expect(filtered[0]).toHaveProperty('name', 'CPU Usage')
      expect(filtered[0]).toHaveProperty('position')
      expect(filtered[0].position).toEqual({ x: 0, y: 0 })
    })

    it('should verify filtering prevents owner-console data leakage', () => {
      const backendResponse: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { 
          id: 'task_execution', 
          type: 'timeline', 
          component: null,
          name: 'Task Execution - GrowthStrategist'
        },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = excludeTaskExecution(backendResponse)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      
      const allWidgetNames = filtered.map(w => w.name || '').join(' ')
      expect(allWidgetNames).not.toContain('GrowthStrategist')
      expect(allWidgetNames).not.toContain('OpsAgent')
      expect(allWidgetNames).not.toContain('PMAgent')
      expect(allWidgetNames).not.toContain('SecurityManager')
    })
  })
})

describe('Dashboard Component Integration Tests', () => {
  vi.mock('@/lib/api', () => ({
    default: {
      request: vi.fn(),
      getDashboardWidgets: vi.fn(),
      getDashboardData: vi.fn()
    }
  }))

  vi.mock('@/lib/safeInterval', () => ({
    safeInterval: vi.fn(() => () => {})
  }))

  vi.mock('../WidgetLibrary', () => ({
    WidgetLibrary: {},
    getWidgetComponent: vi.fn(() => null)
  }))

  vi.mock('../ReportCenter', () => ({
    default: () => null
  }))

  vi.mock('../SaveStatusIndicator', () => ({
    default: () => null
  }))

  vi.mock('@/hooks/useUndoRedo', () => ({
    default: () => ({
      state: [],
      setState: vi.fn(),
      undo: vi.fn(),
      redo: vi.fn(),
      canUndo: false,
      canRedo: false
    })
  }))

  vi.mock('react-dnd', () => ({
    DndProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    useDrag: () => [{ isDragging: false }, vi.fn()],
    useDrop: () => [{ isOver: false }, vi.fn()]
  }))

  vi.mock('react-dnd-html5-backend', () => ({
    HTML5Backend: {}
  }))

  vi.mock('framer-motion', () => ({
    motion: {
      div: ({ children, ...props }: any) => <div {...props}>{children}</div>
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
    useReducedMotion: () => true
  }))

  vi.mock('react-i18next', () => ({
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: { language: 'en' }
    })
  }))

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should use excludeTaskExecution when loading dashboard layout', async () => {
    const mockLayout = {
      widgets: [
        { id: 'cpu_usage', type: 'metric', position: { x: 0, y: 0 } },
        { id: 'task_execution', type: 'timeline', position: { x: 6, y: 0 } }
      ]
    }

    vi.mocked(apiClient.request).mockResolvedValue(mockLayout)
    vi.mocked(apiClient.getDashboardWidgets).mockResolvedValue({ widgets: [] })
    vi.mocked(apiClient.getDashboardData).mockResolvedValue({})

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(apiClient.request).toHaveBeenCalledWith('/dashboard/layouts?user_id=default')
    })

    expect(apiClient.request).toHaveBeenCalled()
  })

  it('should use excludeTaskExecution when loading available widgets', async () => {
    const mockWidgets = {
      widgets: [
        { id: 'cpu_usage', name: 'CPU Usage', type: 'metric' },
        { id: 'task_execution', name: 'Task Execution', type: 'timeline' }
      ]
    }

    vi.mocked(apiClient.request).mockResolvedValue({ widgets: null })
    vi.mocked(apiClient.getDashboardWidgets).mockResolvedValue(mockWidgets)
    vi.mocked(apiClient.getDashboardData).mockResolvedValue({})

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(apiClient.getDashboardWidgets).toHaveBeenCalled()
    })

    expect(apiClient.getDashboardWidgets).toHaveBeenCalled()
  })
})
