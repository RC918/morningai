import { describe, it, expect } from 'vitest'
import { normalizeExecutionLogStatus } from '../AgentExecutionLogs'

describe('normalizeExecutionLogStatus', () => {
  describe('known status mappings', () => {
    it('maps completed statuses correctly', () => {
      expect(normalizeExecutionLogStatus('completed')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('success')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('succeeded')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('done')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('finished')).toEqual({ normalized: 'completed', isKnown: true })
    })

    it('maps running statuses correctly', () => {
      expect(normalizeExecutionLogStatus('running')).toEqual({ normalized: 'running', isKnown: true })
      expect(normalizeExecutionLogStatus('in_progress')).toEqual({ normalized: 'running', isKnown: true })
      expect(normalizeExecutionLogStatus('in-progress')).toEqual({ normalized: 'running', isKnown: true })
      expect(normalizeExecutionLogStatus('processing')).toEqual({ normalized: 'running', isKnown: true })
      expect(normalizeExecutionLogStatus('active')).toEqual({ normalized: 'running', isKnown: true })
      expect(normalizeExecutionLogStatus('executing')).toEqual({ normalized: 'running', isKnown: true })
    })

    it('maps failed statuses correctly', () => {
      expect(normalizeExecutionLogStatus('failed')).toEqual({ normalized: 'failed', isKnown: true })
      expect(normalizeExecutionLogStatus('error')).toEqual({ normalized: 'failed', isKnown: true })
      expect(normalizeExecutionLogStatus('errored')).toEqual({ normalized: 'failed', isKnown: true })
      expect(normalizeExecutionLogStatus('exception')).toEqual({ normalized: 'failed', isKnown: true })
      expect(normalizeExecutionLogStatus('crashed')).toEqual({ normalized: 'failed', isKnown: true })
    })

    it('maps queued statuses correctly', () => {
      expect(normalizeExecutionLogStatus('queued')).toEqual({ normalized: 'queued', isKnown: true })
      expect(normalizeExecutionLogStatus('pending')).toEqual({ normalized: 'queued', isKnown: true })
      expect(normalizeExecutionLogStatus('waiting')).toEqual({ normalized: 'queued', isKnown: true })
    })

    it('maps assigned statuses correctly', () => {
      expect(normalizeExecutionLogStatus('assigned')).toEqual({ normalized: 'assigned', isKnown: true })
      expect(normalizeExecutionLogStatus('scheduled')).toEqual({ normalized: 'assigned', isKnown: true })
    })

    it('maps cancelled statuses correctly', () => {
      expect(normalizeExecutionLogStatus('cancelled')).toEqual({ normalized: 'cancelled', isKnown: true })
      expect(normalizeExecutionLogStatus('canceled')).toEqual({ normalized: 'cancelled', isKnown: true })
      expect(normalizeExecutionLogStatus('aborted')).toEqual({ normalized: 'cancelled', isKnown: true })
      expect(normalizeExecutionLogStatus('terminated')).toEqual({ normalized: 'cancelled', isKnown: true })
    })
  })

  describe('case insensitivity', () => {
    it('handles uppercase statuses', () => {
      expect(normalizeExecutionLogStatus('COMPLETED')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('RUNNING')).toEqual({ normalized: 'running', isKnown: true })
      expect(normalizeExecutionLogStatus('FAILED')).toEqual({ normalized: 'failed', isKnown: true })
    })

    it('handles mixed case statuses', () => {
      expect(normalizeExecutionLogStatus('CoMpLeTeD')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('In_Progress')).toEqual({ normalized: 'running', isKnown: true })
    })

    it('handles statuses with whitespace', () => {
      expect(normalizeExecutionLogStatus('  completed  ')).toEqual({ normalized: 'completed', isKnown: true })
      expect(normalizeExecutionLogStatus('\trunning\n')).toEqual({ normalized: 'running', isKnown: true })
    })
  })

  describe('unknown status fallback', () => {
    it('defaults unknown statuses to queued with isKnown=false', () => {
      expect(normalizeExecutionLogStatus('unknown_status')).toEqual({ normalized: 'queued', isKnown: false })
      expect(normalizeExecutionLogStatus('invalid')).toEqual({ normalized: 'queued', isKnown: false })
      expect(normalizeExecutionLogStatus('xyz123')).toEqual({ normalized: 'queued', isKnown: false })
    })

    it('handles undefined status', () => {
      expect(normalizeExecutionLogStatus(undefined)).toEqual({ normalized: 'queued', isKnown: false })
    })

    it('handles empty string status', () => {
      expect(normalizeExecutionLogStatus('')).toEqual({ normalized: 'queued', isKnown: false })
    })
  })

  describe('type safety', () => {
    it('returns StatusBadgeProps status type', () => {
      const result = normalizeExecutionLogStatus('completed')
      const validStatuses: Array<'completed' | 'running' | 'failed' | 'queued' | 'assigned' | 'cancelled'> = [
        'completed', 'running', 'failed', 'queued', 'assigned', 'cancelled'
      ]
      expect(validStatuses).toContain(result.normalized)
    })
  })
})
