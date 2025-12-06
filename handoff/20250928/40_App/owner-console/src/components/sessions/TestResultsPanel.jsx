import { useState, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge, Progress } from '@morningai/shared-ui'
import { 
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  TestTube,
  AlertTriangle,
  SkipForward,
  Timer
} from 'lucide-react'

/**
 * TestResultsPanel - Display test execution results
 * 
 * Features:
 * - Show test suite summary (passed, failed, skipped)
 * - Display individual test results with expandable details
 * - Show test duration and error messages
 * - Progress indicator for running tests
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const TestResultsPanel = ({ 
  testSuites = [],
  isRunning = false,
  totalTests = 0,
  passedTests = 0,
  failedTests = 0,
  skippedTests = 0,
  duration = null
}) => {
  const { t } = useTranslation()
  const [expandedSuites, setExpandedSuites] = useState(new Set())

  const toggleSuiteExpand = useCallback((suiteName) => {
    setExpandedSuites(prev => {
      const next = new Set(prev)
      if (next.has(suiteName)) {
        next.delete(suiteName)
      } else {
        next.add(suiteName)
      }
      return next
    })
  }, [])

  const passRate = useMemo(() => {
    if (totalTests === 0) return 0
    return Math.round((passedTests / totalTests) * 100)
  }, [totalTests, passedTests])

  const getTestStatusIcon = useCallback((status) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="w-4 h-4 text-growth" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-energy" />
      case 'skipped':
        return <SkipForward className="w-4 h-4 text-neutral-400" />
      case 'running':
        return <Clock className="w-4 h-4 text-primary-500 animate-pulse" />
      default:
        return <Clock className="w-4 h-4 text-neutral-400" />
    }
  }, [])

  // Compute suite counts from tests array, with fallback to explicit counts if provided
  const getSuiteCounts = useCallback((suite) => {
    const tests = suite.tests ?? []
    const total = suite.totalCount ?? tests.length
    const passed = suite.passedCount ?? tests.filter(t => t.status === 'passed').length
    const failed = suite.failedCount ?? tests.filter(t => t.status === 'failed').length
    const skipped = suite.skippedCount ?? tests.filter(t => t.status === 'skipped').length
    return { total, passed, failed, skipped }
  }, [])

  const getSuiteStatusBadge = useCallback((suite) => {
    if (suite.status === 'running') {
      return { variant: 'secondary', label: t('sessions.tests.status.running', 'Running') }
    }
    const { total, passed, failed } = getSuiteCounts(suite)
    if (failed > 0) {
      return { variant: 'destructive', label: t('sessions.tests.status.failed', 'Failed') }
    }
    if (passed === total && total > 0) {
      return { variant: 'success', label: t('sessions.tests.status.passed', 'Passed') }
    }
    return { variant: 'warning', label: t('sessions.tests.status.partial', 'Partial') }
  }, [t, getSuiteCounts])

  const formatDuration = useCallback((ms) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
  }, [])

  if (testSuites.length === 0 && !isRunning) {
    return (
      <div className="text-center py-8">
        <TestTube className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
        <p className="text-sm text-[var(--text-secondary)]">
          {t('sessions.tests.noTests', 'No test results available')}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <div className="p-4 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)]">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-[var(--text-primary)]">
            {t('sessions.tests.summary', 'Test Summary')}
          </h4>
          {isRunning && (
            <Badge variant="secondary" className="text-xs animate-pulse">
              <Clock className="w-3 h-3" />
              <span>{t('sessions.tests.running', 'Running...')}</span>
            </Badge>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] mb-1">
            <span>{passedTests}/{totalTests} {t('sessions.tests.passed', 'passed')}</span>
            <span>{passRate}%</span>
          </div>
          <Progress value={passRate} className="h-2" />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-3">
          <div className="text-center p-2 rounded-lg bg-[var(--surface)]">
            <p className="text-lg font-semibold text-[var(--text-primary)]">{totalTests}</p>
            <p className="text-xs text-[var(--text-secondary)]">{t('sessions.tests.total', 'Total')}</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-growth-10">
            <p className="text-lg font-semibold text-growth">{passedTests}</p>
            <p className="text-xs text-growth">{t('sessions.tests.passedLabel', 'Passed')}</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-energy-10">
            <p className="text-lg font-semibold text-energy">{failedTests}</p>
            <p className="text-xs text-energy">{t('sessions.tests.failedLabel', 'Failed')}</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800">
            <p className="text-lg font-semibold text-neutral-500">{skippedTests}</p>
            <p className="text-xs text-neutral-500">{t('sessions.tests.skippedLabel', 'Skipped')}</p>
          </div>
        </div>

        {/* Duration */}
        {duration && (
          <div className="flex items-center gap-2 mt-3 text-xs text-[var(--text-secondary)]">
            <Timer className="w-3 h-3" />
            <span>{t('sessions.tests.duration', 'Duration')}: {formatDuration(duration)}</span>
          </div>
        )}
      </div>

      {/* Test Suites */}
      {testSuites.length > 0 && (
        <div className="border border-[var(--border)] rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
            <h4 className="text-sm font-medium text-[var(--text-primary)]">
              {t('sessions.tests.suites', 'Test Suites')} ({testSuites.length})
            </h4>
          </div>
          <div className="divide-y divide-[var(--border)]">
            {testSuites.map((suite, index) => {
              const statusBadge = getSuiteStatusBadge(suite)
              const suiteCounts = getSuiteCounts(suite)
              return (
                <div key={suite.name || index}>
                  <button
                    type="button"
                    onClick={() => toggleSuiteExpand(suite.name)}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--surface-elevated)] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {expandedSuites.has(suite.name) ? (
                        <ChevronDown className="w-4 h-4 text-neutral-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-neutral-400" />
                      )}
                      <TestTube className="w-4 h-4 text-neutral-500" />
                      <span className="text-sm text-[var(--text-primary)] font-medium">
                        {suite.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-[var(--text-secondary)]">
                        {suiteCounts.passed}/{suiteCounts.total}
                      </span>
                      <Badge variant={statusBadge.variant} className="text-xs">
                        {statusBadge.label}
                      </Badge>
                    </div>
                  </button>
                  
                  {/* Expanded Test Cases */}
                  {expandedSuites.has(suite.name) && suite.tests && (
                    <div className="bg-neutral-50 dark:bg-neutral-900 border-t border-[var(--border)]">
                      {suite.tests.map((test, testIndex) => (
                        <div 
                          key={testIndex}
                          className="px-4 py-2 flex items-start gap-3 border-b border-[var(--border)] last:border-b-0"
                        >
                          <div className="mt-1">
                            {getTestStatusIcon(test.status)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-[var(--text-primary)]">
                              {test.name}
                            </p>
                            {test.duration && (
                              <p className="text-xs text-[var(--text-secondary)] mt-1">
                                {formatDuration(test.duration)}
                              </p>
                            )}
                            {test.error && (
                              <div className="mt-2 p-2 rounded bg-energy-10 border border-energy">
                                <div className="flex items-start gap-2">
                                  <AlertTriangle className="w-4 h-4 text-energy flex-shrink-0 mt-1" />
                                  <pre className="text-xs text-energy-dark font-mono whitespace-pre-wrap overflow-x-auto">
                                    {test.error}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default TestResultsPanel
