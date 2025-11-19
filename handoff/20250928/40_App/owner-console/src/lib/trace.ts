/**
 * Trace URL utilities for building links to observability platforms
 */

/**
 * Builds a safe trace viewer URL with proper encoding
 * @param baseUrl - The base URL of the trace viewer (e.g., https://jaeger.example.com)
 * @param traceId - The trace ID to link to
 * @returns The complete trace viewer URL with encoded trace ID
 * @throws Error if baseUrl is empty or traceId is empty
 */
export function buildTraceUrl(baseUrl: string, traceId: string): string {
  if (!baseUrl || baseUrl.trim() === '') {
    throw new Error('Base URL is required')
  }
  
  if (!traceId || traceId.trim() === '') {
    throw new Error('Trace ID is required')
  }

  const safeBase = baseUrl.replace(/\/+$/, '')
  
  const encodedTraceId = encodeURIComponent(String(traceId))
  
  try {
    return new URL(`/trace/${encodedTraceId}`, safeBase).toString()
  } catch (error) {
    return `${safeBase}/trace/${encodedTraceId}`
  }
}
