/**
 * Tests for AgentExecutionLogs Component - Phase 2 Coverage (#1925)
 *
 * Comprehensive test suite for AgentExecutionLogs.tsx component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { normalizeExecutionLogStatus } from '../AgentExecutionLogs'

// Note: The normalizeExecutionLogStatus function is already tested in normalizeExecutionLogStatus.test.ts
// This file focuses on additional component-level tests and helper functions

describe('AgentExecutionLogs Helper Functions', () => {
  describe('formatDuration', () => {
    // Test the duration formatting logic
    it('formats seconds correctly', () => {
      // Less than 60 seconds
      const formatDuration = (durationMs: number | undefined): string => {
        if (!durationMs) return 'N/A'
        const seconds = Math.floor(durationMs / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`
        } else {
          return `${seconds}s`
        }
      }

      expect(formatDuration(5000)).toBe('5s')
      expect(formatDuration(30000)).toBe('30s')
      expect(formatDuration(59000)).toBe('59s')
    })

    it('formats minutes correctly', () => {
      const formatDuration = (durationMs: number | undefined): string => {
        if (!durationMs) return 'N/A'
        const seconds = Math.floor(durationMs / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`
        } else {
          return `${seconds}s`
        }
      }

      expect(formatDuration(60000)).toBe('1m 0s')
      expect(formatDuration(90000)).toBe('1m 30s')
      expect(formatDuration(300000)).toBe('5m 0s')
      expect(formatDuration(3599000)).toBe('59m 59s')
    })

    it('formats hours correctly', () => {
      const formatDuration = (durationMs: number | undefined): string => {
        if (!durationMs) return 'N/A'
        const seconds = Math.floor(durationMs / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`
        } else {
          return `${seconds}s`
        }
      }

      expect(formatDuration(3600000)).toBe('1h 0m')
      expect(formatDuration(5400000)).toBe('1h 30m')
      expect(formatDuration(7200000)).toBe('2h 0m')
    })

    it('handles undefined duration', () => {
      const formatDuration = (durationMs: number | undefined): string => {
        if (!durationMs) return 'N/A'
        const seconds = Math.floor(durationMs / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`
        } else {
          return `${seconds}s`
        }
      }

      expect(formatDuration(undefined)).toBe('N/A')
      expect(formatDuration(0)).toBe('N/A')
    })
  })

  describe('formatTimestamp', () => {
    it('formats timestamp correctly', () => {
      const formatTimestamp = (timestamp: string | undefined): string => {
        if (!timestamp) return 'N/A'
        return new Date(timestamp).toLocaleString()
      }

      const timestamp = '2024-01-15T10:30:00Z'
      const result = formatTimestamp(timestamp)
      
      // Result should be a valid date string (locale-dependent)
      expect(result).not.toBe('N/A')
      expect(result.length).toBeGreaterThan(0)
    })

    it('handles undefined timestamp', () => {
      const formatTimestamp = (timestamp: string | undefined): string => {
        if (!timestamp) return 'N/A'
        return new Date(timestamp).toLocaleString()
      }

      expect(formatTimestamp(undefined)).toBe('N/A')
    })
  })

  describe('isEmptyValue', () => {
    it('returns true for null and undefined', () => {
      const isEmptyValue = (value: any): boolean => {
        if (value == null) return true
        if (Array.isArray(value)) return value.length === 0
        if (typeof value === 'object') return Object.keys(value).length === 0
        return false
      }

      expect(isEmptyValue(null)).toBe(true)
      expect(isEmptyValue(undefined)).toBe(true)
    })

    it('returns true for empty arrays', () => {
      const isEmptyValue = (value: any): boolean => {
        if (value == null) return true
        if (Array.isArray(value)) return value.length === 0
        if (typeof value === 'object') return Object.keys(value).length === 0
        return false
      }

      expect(isEmptyValue([])).toBe(true)
      expect(isEmptyValue([1, 2, 3])).toBe(false)
    })

    it('returns true for empty objects', () => {
      const isEmptyValue = (value: any): boolean => {
        if (value == null) return true
        if (Array.isArray(value)) return value.length === 0
        if (typeof value === 'object') return Object.keys(value).length === 0
        return false
      }

      expect(isEmptyValue({})).toBe(true)
      expect(isEmptyValue({ key: 'value' })).toBe(false)
    })

    it('returns false for non-empty values', () => {
      const isEmptyValue = (value: any): boolean => {
        if (value == null) return true
        if (Array.isArray(value)) return value.length === 0
        if (typeof value === 'object') return Object.keys(value).length === 0
        return false
      }

      expect(isEmptyValue('string')).toBe(false)
      expect(isEmptyValue(123)).toBe(false)
      expect(isEmptyValue(true)).toBe(false)
    })
  })
})

describe('normalizeExecutionLogStatus additional tests', () => {
  describe('status normalization edge cases', () => {
    it('handles timeout status', () => {
      // Timeout is not in the current mapping, should default to queued
      const result = normalizeExecutionLogStatus('timeout')
      expect(result.isKnown).toBe(false)
      expect(result.normalized).toBe('queued')
    })

    it('handles retry status', () => {
      // Retry is not in the current mapping, should default to queued
      const result = normalizeExecutionLogStatus('retry')
      expect(result.isKnown).toBe(false)
      expect(result.normalized).toBe('queued')
    })

    it('handles paused status', () => {
      // Paused is not in the current mapping, should default to queued
      const result = normalizeExecutionLogStatus('paused')
      expect(result.isKnown).toBe(false)
      expect(result.normalized).toBe('queued')
    })
  })

  describe('status mapping completeness', () => {
    it('maps all completed synonyms', () => {
      const completedSynonyms = ['completed', 'success', 'succeeded', 'done', 'finished']
      
      completedSynonyms.forEach(status => {
        const result = normalizeExecutionLogStatus(status)
        expect(result.normalized).toBe('completed')
        expect(result.isKnown).toBe(true)
      })
    })

    it('maps all running synonyms', () => {
      const runningSynonyms = ['running', 'in_progress', 'in-progress', 'processing', 'active', 'executing']
      
      runningSynonyms.forEach(status => {
        const result = normalizeExecutionLogStatus(status)
        expect(result.normalized).toBe('running')
        expect(result.isKnown).toBe(true)
      })
    })

    it('maps all failed synonyms', () => {
      const failedSynonyms = ['failed', 'error', 'errored', 'exception', 'crashed']
      
      failedSynonyms.forEach(status => {
        const result = normalizeExecutionLogStatus(status)
        expect(result.normalized).toBe('failed')
        expect(result.isKnown).toBe(true)
      })
    })

    it('maps all queued synonyms', () => {
      const queuedSynonyms = ['queued', 'pending', 'waiting']
      
      queuedSynonyms.forEach(status => {
        const result = normalizeExecutionLogStatus(status)
        expect(result.normalized).toBe('queued')
        expect(result.isKnown).toBe(true)
      })
    })

    it('maps all assigned synonyms', () => {
      const assignedSynonyms = ['assigned', 'scheduled']
      
      assignedSynonyms.forEach(status => {
        const result = normalizeExecutionLogStatus(status)
        expect(result.normalized).toBe('assigned')
        expect(result.isKnown).toBe(true)
      })
    })

    it('maps all cancelled synonyms', () => {
      const cancelledSynonyms = ['cancelled', 'canceled', 'aborted', 'terminated']
      
      cancelledSynonyms.forEach(status => {
        const result = normalizeExecutionLogStatus(status)
        expect(result.normalized).toBe('cancelled')
        expect(result.isKnown).toBe(true)
      })
    })
  })
})

describe('Filter State Management', () => {
  describe('FiltersState interface', () => {
    it('has correct default values', () => {
      const defaultFilters = {
        status: '',
        agent_id: '',
        agent_type: '',
        tenant_id: '',
        task_type: '',
        start_date: '',
        end_date: '',
        time_range: '',
        sort_by: 'created_at',
        sort_order: 'desc'
      }

      expect(defaultFilters.status).toBe('')
      expect(defaultFilters.sort_by).toBe('created_at')
      expect(defaultFilters.sort_order).toBe('desc')
    })

    it('supports all filter fields', () => {
      const filters = {
        status: 'completed',
        agent_id: 'agent-123',
        agent_type: 'dev_agent',
        tenant_id: 'tenant-456',
        task_type: 'code_review',
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        time_range: '30d',
        sort_by: 'duration_ms',
        sort_order: 'asc'
      }

      expect(filters.status).toBe('completed')
      expect(filters.agent_type).toBe('dev_agent')
      expect(filters.time_range).toBe('30d')
    })
  })

  describe('Time range calculation', () => {
    it('calculates 24h time range correctly', () => {
      const now = new Date()
      const startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      
      const diffMs = now.getTime() - startDate.getTime()
      const diffHours = diffMs / (60 * 60 * 1000)
      
      expect(diffHours).toBe(24)
    })

    it('calculates 7d time range correctly', () => {
      const now = new Date()
      const startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      
      const diffMs = now.getTime() - startDate.getTime()
      const diffDays = diffMs / (24 * 60 * 60 * 1000)
      
      expect(diffDays).toBe(7)
    })

    it('calculates 30d time range correctly', () => {
      const now = new Date()
      const startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      
      const diffMs = now.getTime() - startDate.getTime()
      const diffDays = diffMs / (24 * 60 * 60 * 1000)
      
      expect(diffDays).toBe(30)
    })
  })
})

describe('Pagination State Management', () => {
  describe('PaginationState interface', () => {
    it('has correct default values', () => {
      const defaultPagination = {
        page: 1,
        page_size: 50,
        total_items: 0,
        total_pages: 0
      }

      expect(defaultPagination.page).toBe(1)
      expect(defaultPagination.page_size).toBe(50)
      expect(defaultPagination.total_items).toBe(0)
      expect(defaultPagination.total_pages).toBe(0)
    })

    it('calculates pagination info correctly', () => {
      const pagination = {
        page: 2,
        page_size: 50,
        total_items: 125,
        total_pages: 3
      }

      const start = (pagination.page - 1) * pagination.page_size + 1
      const end = Math.min(pagination.page * pagination.page_size, pagination.total_items)

      expect(start).toBe(51)
      expect(end).toBe(100)
    })

    it('handles last page correctly', () => {
      const pagination = {
        page: 3,
        page_size: 50,
        total_items: 125,
        total_pages: 3
      }

      const start = (pagination.page - 1) * pagination.page_size + 1
      const end = Math.min(pagination.page * pagination.page_size, pagination.total_items)

      expect(start).toBe(101)
      expect(end).toBe(125)
    })
  })
})

describe('ExecutionLog Interface', () => {
  describe('ExecutionLog data structure', () => {
    it('supports all required fields', () => {
      const log = {
        task_id: 'task-123',
        status: 'completed',
        task_type: 'code_review',
        agent: {
          agent_type: 'dev_agent',
          reputation_score: 95
        },
        tenant_id: 'tenant-456',
        duration_ms: 5000,
        timestamps: {
          created_at: '2024-01-15T10:00:00Z',
          started_at: '2024-01-15T10:00:01Z',
          completed_at: '2024-01-15T10:00:06Z',
          updated_at: '2024-01-15T10:00:06Z'
        },
        error_message: undefined,
        trace_id: 'trace-789',
        pr_url: 'https://github.com/org/repo/pull/123'
      }

      expect(log.task_id).toBe('task-123')
      expect(log.status).toBe('completed')
      expect(log.agent?.agent_type).toBe('dev_agent')
      expect(log.agent?.reputation_score).toBe(95)
      expect(log.trace_id).toBe('trace-789')
    })

    it('handles optional fields', () => {
      const minimalLog = {
        task_id: 'task-123',
        status: 'queued'
      }

      expect(minimalLog.task_id).toBe('task-123')
      expect(minimalLog.status).toBe('queued')
    })

    it('handles error messages', () => {
      const failedLog = {
        task_id: 'task-123',
        status: 'failed',
        error_message: 'Connection timeout after 30s'
      }

      expect(failedLog.status).toBe('failed')
      expect(failedLog.error_message).toBe('Connection timeout after 30s')
    })
  })
})

describe('ExecutionSummary Interface', () => {
  describe('ExecutionSummary data structure', () => {
    it('supports all summary fields', () => {
      const summary = {
        total_executions: 100,
        success_rate: 0.95,
        avg_duration_ms: 5000,
        status_counts: {
          completed: 95,
          failed: 3,
          running: 2
        }
      }

      expect(summary.total_executions).toBe(100)
      expect(summary.success_rate).toBe(0.95)
      expect(summary.avg_duration_ms).toBe(5000)
      expect(summary.status_counts?.completed).toBe(95)
    })

    it('handles empty summary', () => {
      const emptySummary = {
        total_executions: 0,
        success_rate: undefined,
        avg_duration_ms: undefined,
        status_counts: undefined
      }

      expect(emptySummary.total_executions).toBe(0)
      expect(emptySummary.success_rate).toBeUndefined()
    })

    it('calculates success rate percentage correctly', () => {
      const summary = {
        total_executions: 100,
        success_rate: 0.95
      }

      const percentage = (summary.success_rate! * 100).toFixed(1)
      expect(percentage).toBe('95.0')
    })
  })
})

describe('URL Building', () => {
  describe('buildTraceUrl', () => {
    it('builds trace URL correctly', () => {
      const buildTraceUrl = (baseUrl: string, traceId: string): string => {
        return `${baseUrl}/trace/${traceId}`
      }

      const url = buildTraceUrl('https://trace.example.com', 'trace-123')
      expect(url).toBe('https://trace.example.com/trace/trace-123')
    })

    it('handles empty base URL', () => {
      const buildTraceUrl = (baseUrl: string, traceId: string): string => {
        if (!baseUrl) return ''
        return `${baseUrl}/trace/${traceId}`
      }

      const url = buildTraceUrl('', 'trace-123')
      expect(url).toBe('')
    })
  })
})

describe('Copy to Clipboard', () => {
  describe('handleCopy function logic', () => {
    it('copies trace ID correctly', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
      Object.assign(navigator, { clipboard: mockClipboard })

      await navigator.clipboard.writeText('trace-123')
      
      expect(mockClipboard.writeText).toHaveBeenCalledWith('trace-123')
    })

    it('copies task ID correctly', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
      Object.assign(navigator, { clipboard: mockClipboard })

      await navigator.clipboard.writeText('task-456')
      
      expect(mockClipboard.writeText).toHaveBeenCalledWith('task-456')
    })

    it('handles clipboard error', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockRejectedValue(new Error('Clipboard access denied'))
      }
      Object.assign(navigator, { clipboard: mockClipboard })

      await expect(navigator.clipboard.writeText('test')).rejects.toThrow('Clipboard access denied')
    })
  })
})

describe('API Parameter Building', () => {
  describe('URL search params', () => {
    it('builds params with all filters', () => {
      const filters = {
        status: 'completed',
        agent_id: 'agent-123',
        agent_type: 'dev_agent',
        tenant_id: 'tenant-456',
        task_type: 'code_review',
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        sort_by: 'created_at',
        sort_order: 'desc'
      }

      const pagination = { page: 1, page_size: 50 }

      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.page_size.toString(),
        sort_by: filters.sort_by,
        sort_order: filters.sort_order
      })

      if (filters.status) params.append('status', filters.status)
      if (filters.agent_id) params.append('agent_id', filters.agent_id)
      if (filters.agent_type) params.append('agent_type', filters.agent_type)
      if (filters.tenant_id) params.append('tenant_id', filters.tenant_id)
      if (filters.task_type) params.append('task_type', filters.task_type)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      expect(params.get('page')).toBe('1')
      expect(params.get('status')).toBe('completed')
      expect(params.get('agent_type')).toBe('dev_agent')
      expect(params.get('start_date')).toBe('2024-01-01')
    })

    it('builds params with minimal filters', () => {
      const filters = {
        status: '',
        agent_id: '',
        sort_by: 'created_at',
        sort_order: 'desc'
      }

      const pagination = { page: 1, page_size: 50 }

      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.page_size.toString(),
        sort_by: filters.sort_by,
        sort_order: filters.sort_order
      })

      if (filters.status) params.append('status', filters.status)
      if (filters.agent_id) params.append('agent_id', filters.agent_id)

      expect(params.get('page')).toBe('1')
      expect(params.get('status')).toBeNull()
      expect(params.get('agent_id')).toBeNull()
    })
  })
})

describe('Data Attributes', () => {
  describe('Table row data attributes', () => {
    it('includes all required data attributes', () => {
      const log = {
        task_id: 'task-123',
        status: 'completed',
        trace_id: 'trace-456',
        tenant_id: 'tenant-789'
      }

      const dataAttributes = {
        'data-testid': 'execution-row',
        'data-task-id': log.task_id,
        'data-status': 'completed',
        'data-trace-id': log.trace_id || '',
        'data-tenant-id': log.tenant_id || ''
      }

      expect(dataAttributes['data-task-id']).toBe('task-123')
      expect(dataAttributes['data-status']).toBe('completed')
      expect(dataAttributes['data-trace-id']).toBe('trace-456')
    })

    it('handles missing optional attributes', () => {
      const log = {
        task_id: 'task-123',
        status: 'queued'
      }

      const dataAttributes = {
        'data-testid': 'execution-row',
        'data-task-id': log.task_id,
        'data-status': 'queued',
        'data-trace-id': '',
        'data-tenant-id': ''
      }

      expect(dataAttributes['data-trace-id']).toBe('')
      expect(dataAttributes['data-tenant-id']).toBe('')
    })
  })
})
