import { describe, it, expect } from 'vitest'
import { buildTraceUrl } from '../trace'

describe('buildTraceUrl', () => {
  it('should build a valid trace URL with base URL and trace ID', () => {
    const result = buildTraceUrl('https://jaeger.example.com', 'abc123')
    expect(result).toBe('https://jaeger.example.com/trace/abc123')
  })

  it('should handle base URL with trailing slash', () => {
    const result = buildTraceUrl('https://jaeger.example.com/', 'abc123')
    expect(result).toBe('https://jaeger.example.com/trace/abc123')
  })

  it('should handle base URL with multiple trailing slashes', () => {
    const result = buildTraceUrl('https://jaeger.example.com///', 'abc123')
    expect(result).toBe('https://jaeger.example.com/trace/abc123')
  })

  it('should encode special characters in trace ID', () => {
    const result = buildTraceUrl('https://jaeger.example.com', 'trace/with/slashes')
    expect(result).toBe('https://jaeger.example.com/trace/trace%2Fwith%2Fslashes')
  })

  it('should encode spaces in trace ID', () => {
    const result = buildTraceUrl('https://jaeger.example.com', 'trace with spaces')
    expect(result).toBe('https://jaeger.example.com/trace/trace%20with%20spaces')
  })

  it('should encode special characters like & and = in trace ID', () => {
    const result = buildTraceUrl('https://jaeger.example.com', 'trace&id=123')
    expect(result).toBe('https://jaeger.example.com/trace/trace%26id%3D123')
  })

  it('should throw error if base URL is empty', () => {
    expect(() => buildTraceUrl('', 'abc123')).toThrow('Base URL is required')
  })

  it('should throw error if base URL is whitespace only', () => {
    expect(() => buildTraceUrl('   ', 'abc123')).toThrow('Base URL is required')
  })

  it('should throw error if trace ID is empty', () => {
    expect(() => buildTraceUrl('https://jaeger.example.com', '')).toThrow('Trace ID is required')
  })

  it('should throw error if trace ID is whitespace only', () => {
    expect(() => buildTraceUrl('https://jaeger.example.com', '   ')).toThrow('Trace ID is required')
  })

  it('should handle different observability platforms', () => {
    const jaeger = buildTraceUrl('https://jaeger.gm365.me', 'trace123')
    expect(jaeger).toBe('https://jaeger.gm365.me/trace/trace123')

    const tempo = buildTraceUrl('https://tempo.gm365.me', 'trace123')
    expect(tempo).toBe('https://tempo.gm365.me/trace/trace123')

    const grafana = buildTraceUrl('https://grafana.gm365.me/explore', 'trace123')
    expect(grafana).toBe('https://grafana.gm365.me/trace/trace123')
  })

  it('should handle base URL with path', () => {
    const result = buildTraceUrl('https://example.com/monitoring', 'abc123')
    expect(result).toBe('https://example.com/trace/abc123')
  })
})
