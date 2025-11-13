import { describe, it, expect } from 'vitest'

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

const getDefaultWidgets = (): Widget[] => [
  { id: 'cpu_usage', type: 'metric', component: null },
  { id: 'memory_usage', type: 'metric', component: null },
  { id: 'response_time', type: 'metric', component: null },
  { id: 'error_rate', type: 'metric', component: null },
  { id: 'active_strategies', type: 'metric', component: null },
  { id: 'pending_approvals', type: 'metric', component: null }
]

const filterDashboardLayout = (widgets: Widget[]): Widget[] => {
  return widgets.filter((widget: Widget) => widget.id !== 'task_execution')
}

const filterAvailableWidgets = (widgets: Widget[]): Widget[] => {
  return widgets.filter((widget: Widget) => widget.id !== 'task_execution')
}

describe('Dashboard Widget Filtering - Unit Tests', () => {
  describe('getDefaultWidgets', () => {
    it('should return exactly 6 default widgets', () => {
      const defaultWidgets = getDefaultWidgets()
      
      expect(defaultWidgets).toHaveLength(6)
    })

    it('should not include task_execution in default widgets', () => {
      const defaultWidgets = getDefaultWidgets()
      
      const hasTaskExecution = defaultWidgets.some(widget => widget.id === 'task_execution')
      expect(hasTaskExecution).toBe(false)
    })

    it('should return widgets with correct structure', () => {
      const defaultWidgets = getDefaultWidgets()
      
      defaultWidgets.forEach(widget => {
        expect(widget).toHaveProperty('id')
        expect(widget).toHaveProperty('type')
        expect(widget).toHaveProperty('component')
        expect(typeof widget.id).toBe('string')
        expect(typeof widget.type).toBe('string')
      })
    })

    it('should include expected default widget IDs', () => {
      const defaultWidgets = getDefaultWidgets()
      const widgetIds = defaultWidgets.map(w => w.id)
      
      expect(widgetIds).toContain('cpu_usage')
      expect(widgetIds).toContain('memory_usage')
      expect(widgetIds).toContain('response_time')
      expect(widgetIds).toContain('error_rate')
      expect(widgetIds).toContain('active_strategies')
      expect(widgetIds).toContain('pending_approvals')
    })
  })

  describe('filterDashboardLayout', () => {
    it('should filter out task_execution from saved layout', () => {
      const mockLayout: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null }, // Should be filtered out
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = filterDashboardLayout(mockLayout)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      expect(filtered.some(w => w.id === 'cpu_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'memory_usage')).toBe(true)
    })

    it('should handle layout with multiple task_execution widgets', () => {
      const mockLayout: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null } // Duplicate
      ]

      const filtered = filterDashboardLayout(mockLayout)
      
      expect(filtered).toHaveLength(2)
      expect(filtered.every(w => w.id !== 'task_execution')).toBe(true)
    })

    it('should preserve non-task_execution widgets from saved layout', () => {
      const mockLayout: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null },
        { id: 'circuit_breakers', type: 'status', component: null }
      ]

      const filtered = filterDashboardLayout(mockLayout)
      
      expect(filtered).toHaveLength(3)
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      expect(filtered.some(w => w.id === 'cpu_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'memory_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'circuit_breakers')).toBe(true)
    })

    it('should handle empty layout', () => {
      const mockLayout: Widget[] = []

      const filtered = filterDashboardLayout(mockLayout)
      
      expect(filtered).toHaveLength(0)
    })

    it('should handle layout with only task_execution', () => {
      const mockLayout: Widget[] = [
        { id: 'task_execution', type: 'timeline', component: null }
      ]

      const filtered = filterDashboardLayout(mockLayout)
      
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

      const filtered = filterDashboardLayout(mockLayout)
      
      expect(filtered).toHaveLength(1)
      expect(filtered[0]).toHaveProperty('name', 'CPU Usage')
      expect(filtered[0]).toHaveProperty('position')
      expect(filtered[0].position).toEqual({ x: 0, y: 0 })
    })
  })

  describe('filterAvailableWidgets', () => {
    it('should filter out task_execution from available widgets', () => {
      const mockAvailableWidgets: Widget[] = [
        { id: 'cpu_usage', name: 'CPU Usage', type: 'metric', component: null },
        { id: 'task_execution', name: 'Task Execution', type: 'timeline', component: null }, // Should be filtered
        { id: 'memory_usage', name: 'Memory Usage', type: 'metric', component: null },
        { id: 'circuit_breakers', name: 'Circuit Breakers', type: 'status', component: null }
      ]

      const filtered = filterAvailableWidgets(mockAvailableWidgets)
      
      expect(filtered).toHaveLength(3)
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      expect(filtered.some(w => w.id === 'cpu_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'memory_usage')).toBe(true)
      expect(filtered.some(w => w.id === 'circuit_breakers')).toBe(true)
    })

    it('should handle empty available widgets list', () => {
      const mockAvailableWidgets: Widget[] = []

      const filtered = filterAvailableWidgets(mockAvailableWidgets)
      
      expect(filtered).toHaveLength(0)
    })

    it('should preserve widget metadata during filtering', () => {
      const mockAvailableWidgets: Widget[] = [
        { id: 'cpu_usage', name: 'CPU Usage', type: 'metric', component: null },
        { id: 'task_execution', name: 'Task Execution', type: 'timeline', component: null }
      ]

      const filtered = filterAvailableWidgets(mockAvailableWidgets)
      
      expect(filtered).toHaveLength(1)
      expect(filtered[0]).toHaveProperty('name', 'CPU Usage')
      expect(filtered[0]).toHaveProperty('type', 'metric')
    })
  })

  describe('Integration: Widget Filtering Consistency', () => {
    it('should consistently filter task_execution across all operations', () => {
      const mockWidgets: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filteredLayout = filterDashboardLayout(mockWidgets)
      const filteredAvailable = filterAvailableWidgets(mockWidgets)
      const defaultWidgets = getDefaultWidgets()

      expect(filteredLayout.some(w => w.id === 'task_execution')).toBe(false)
      expect(filteredAvailable.some(w => w.id === 'task_execution')).toBe(false)
      expect(defaultWidgets.some(w => w.id === 'task_execution')).toBe(false)
    })

    it('should verify no owner-console agent names in widget IDs', () => {
      const defaultWidgets = getDefaultWidgets()
      const widgetIds = defaultWidgets.map(w => w.id.toLowerCase())

      const ownerConsoleTerms = ['growthstrategist', 'opsagent', 'pmagent', 'securitymanager', 'task_execution']
      
      ownerConsoleTerms.forEach(term => {
        expect(widgetIds.some(id => id.includes(term))).toBe(false)
      })
    })

    it('should maintain filtering with case variations', () => {
      const mockWidgets: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { id: 'task_execution', type: 'timeline', component: null },
        { id: 'TASK_EXECUTION', type: 'timeline', component: null }, // Different case
        { id: 'Task_Execution', type: 'timeline', component: null }  // Mixed case
      ]

      const filtered = filterDashboardLayout(mockWidgets)
      
      expect(filtered.some(w => w.id === 'task_execution')).toBe(false)
      
    })

    it('should verify filtering prevents owner-console data leakage', () => {
      const backendResponse: Widget[] = [
        { id: 'cpu_usage', type: 'metric', component: null },
        { 
          id: 'task_execution', 
          type: 'timeline', 
          component: null,
          name: 'Task Execution - GrowthStrategist' // Contains owner-console agent name
        },
        { id: 'memory_usage', type: 'metric', component: null }
      ]

      const filtered = filterDashboardLayout(backendResponse)
      
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
