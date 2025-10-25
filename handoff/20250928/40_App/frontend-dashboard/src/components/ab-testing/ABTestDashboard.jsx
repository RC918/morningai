/**
 * A/B Test Dashboard
 * 
 * Admin interface for managing A/B tests, viewing results, and analyzing performance.
 * 
 * @component
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AppleButton } from '@/components/ui/apple-button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { 
  Download, 
  TrendingUp, 
  Users, 
  MousePointerClick,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  Trophy
} from 'lucide-react'
import abTestManager, { calculateABTestResults, exportAllABTestData } from '@/lib/ab-testing'

export function ABTestDashboard() {
  const [tests, setTests] = useState([])
  const [selectedTest, setSelectedTest] = useState(null)
  const [results, setResults] = useState(null)

  useEffect(() => {
    loadTests()
  }, [])

  const loadTests = () => {
    const allTests = abTestManager.getAllTests()
    setTests(allTests)
  }

  const handleViewResults = (testId) => {
    try {
      const testResults = calculateABTestResults(testId)
      setResults(testResults)
      setSelectedTest(testId)
    } catch (error) {
      console.error('Failed to calculate results:', error)
      alert('Failed to calculate test results. Make sure the test has data.')
    }
  }

  const handleExportAll = () => {
    const data = exportAllABTestData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ab-tests-export-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExportTest = (testId) => {
    const test = abTestManager.getTest(testId)
    if (!test) return

    const data = test.exportData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ab-test-${testId}-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">A/B Testing Dashboard</h1>
          <p className="text-muted-foreground">Manage experiments and analyze results</p>
        </div>
        <AppleButton onClick={handleExportAll} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export All Data
        </AppleButton>
      </div>

      <Tabs defaultValue="active-tests" className="w-full">
        <TabsList>
          <TabsTrigger value="active-tests">Active Tests ({tests.length})</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="setup">Setup New Test</TabsTrigger>
        </TabsList>

        <TabsContent value="active-tests" className="space-y-4">
          {tests.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No active A/B tests. Create a new test to get started.
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {tests.map((test) => {
                const events = test.getEvents()
                const assignmentCount = events.filter(e => e.event === 'variant_assigned').length
                const conversionCount = events.filter(e => e.event === 'conversion').length
                const conversionRate = assignmentCount > 0 
                  ? ((conversionCount / assignmentCount) * 100).toFixed(2)
                  : '0.00'

                return (
                  <Card key={test.testId}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">{test.testId}</CardTitle>
                          <CardDescription>
                            {test.variants.length} variants
                          </CardDescription>
                        </div>
                        <div className="flex gap-2">
                          <AppleButton
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewResults(test.testId)}
                          >
                            <BarChart3 className="h-4 w-4 mr-2" />
                            View Results
                          </AppleButton>
                          <AppleButton
                            size="sm"
                            variant="outline"
                            onClick={() => handleExportTest(test.testId)}
                          >
                            <Download className="h-4 w-4" />
                          </AppleButton>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">Participants</div>
                          <div className="font-medium flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            {assignmentCount}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Conversions</div>
                          <div className="font-medium flex items-center gap-1">
                            <CheckCircle2 className="h-4 w-4" />
                            {conversionCount}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Conversion Rate</div>
                          <div className="font-medium flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" />
                            {conversionRate}%
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Variants</div>
                          <div className="flex gap-1 flex-wrap">
                            {test.variants.map(v => (
                              <Badge key={v.id} variant="outline" className="text-xs">
                                {v.name || v.id}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {!results ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Select a test from the Active Tests tab to view results.
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Test Results: {results.test_id}</CardTitle>
                  <CardDescription>
                    Total Participants: {results.total_assignments} | 
                    Total Conversions: {results.total_conversions}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.values(results.variants).map((variant) => {
                      const isWinner = results.significance?.winner === variant.variant_id
                      
                      return (
                        <Card key={variant.variant_id} className={isWinner ? 'border-green-500 border-2' : ''}>
                          <CardHeader>
                            <div className="flex justify-between items-start">
                              <div>
                                <CardTitle className="text-base flex items-center gap-2">
                                  {variant.variant_name}
                                  {isWinner && <Trophy className="h-4 w-4 text-yellow-500" />}
                                </CardTitle>
                                <CardDescription>{variant.variant_id}</CardDescription>
                              </div>
                              {isWinner && (
                                <Badge variant="default" className="bg-green-500">
                                  Winner
                                </Badge>
                              )}
                            </div>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <div className="text-sm text-muted-foreground">Participants</div>
                                <div className="text-2xl font-bold">{variant.assignments}</div>
                              </div>
                              <div>
                                <div className="text-sm text-muted-foreground">Conversions</div>
                                <div className="text-2xl font-bold">{variant.conversions}</div>
                              </div>
                            </div>
                            
                            <div>
                              <div className="text-sm text-muted-foreground mb-2">Conversion Rate</div>
                              <div className="flex items-center gap-2">
                                <div className="flex-1 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-blue-500 h-2 rounded-full transition-all"
                                    style={{ width: `${variant.conversion_rate}%` }}
                                  />
                                </div>
                                <div className="text-lg font-bold">{variant.conversion_rate}%</div>
                              </div>
                            </div>

                            <div>
                              <div className="text-sm text-muted-foreground mb-2">Click Rate</div>
                              <div className="flex items-center gap-2">
                                <div className="flex-1 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-green-500 h-2 rounded-full transition-all"
                                    style={{ width: `${variant.click_rate}%` }}
                                  />
                                </div>
                                <div className="text-lg font-bold">{variant.click_rate}%</div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                  </div>

                  {results.significance && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                          <BarChart3 className="h-5 w-5" />
                          Statistical Significance
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <Alert variant={results.significance.is_significant ? 'default' : 'destructive'}>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            {results.significance.is_significant ? (
                              <span>
                                <strong>Statistically Significant!</strong> The results are reliable with {results.significance.confidence_level} confidence.
                              </span>
                            ) : (
                              <span>
                                <strong>Not Statistically Significant.</strong> More data is needed to draw reliable conclusions.
                              </span>
                            )}
                          </AlertDescription>
                        </Alert>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <div className="text-sm text-muted-foreground">Z-Score</div>
                            <div className="text-lg font-bold">{results.significance.z_score}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">P-Value</div>
                            <div className="text-lg font-bold">{results.significance.p_value}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Confidence</div>
                            <div className="text-lg font-bold">{results.significance.confidence_level}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Lift</div>
                            <div className="text-lg font-bold text-green-600">+{results.significance.lift}</div>
                          </div>
                        </div>

                        <div className="text-sm text-muted-foreground">
                          <p><strong>Winner:</strong> {results.significance.winner}</p>
                          <p><strong>Calculated:</strong> {new Date(results.calculated_at).toLocaleString()}</p>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="setup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Setup New A/B Test</CardTitle>
              <CardDescription>
                A/B tests are created programmatically in your code. Use the examples below to get started.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Developer Guide:</strong> A/B tests should be implemented in your React components using the <code>useABTest</code> hook or <code>createABTest</code> function.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Example 1: React Hook</h3>
                  <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
{`import { useABTest } from '@/lib/ab-testing'

function MyComponent() {
  const { variant, isVariant, trackConversion } = useABTest(
    'dashboard-cta',
    [
      { id: 'control', name: 'Original CTA', weight: 1 },
      { id: 'variant-a', name: 'New CTA', weight: 1 }
    ]
  )

  return (
    <div>
      {isVariant('variant-a') ? (
        <button onClick={() => trackConversion()}>
          Try Now - Free!
        </button>
      ) : (
        <button onClick={() => trackConversion()}>
          Get Started
        </button>
      )}
    </div>
  )
}`}
                  </pre>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Example 2: Direct API</h3>
                  <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
{`import { createABTest } from '@/lib/ab-testing'

const test = createABTest('approval-button-color', [
  { id: 'green', name: 'Green Button', weight: 1 },
  { id: 'blue', name: 'Blue Button', weight: 1 }
])

if (test.isVariant('blue')) {
  buttonColor = 'primary'
} else {
  buttonColor = 'success'
}

test.trackConversion({ action: 'approved' })`}
                  </pre>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Example 3: Cost Alert Threshold</h3>
                  <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
{`const test = createABTest('cost-alert-threshold', [
  { id: 'threshold-80', name: '80% Threshold', weight: 1 },
  { id: 'threshold-90', name: '90% Threshold', weight: 1 }
])

const defaultThreshold = test.isVariant('threshold-90') ? 90 : 80

test.trackEvent('threshold_set', { value: threshold })`}
                  </pre>
                </div>
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Best Practices:</strong>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Run tests for at least 1-2 weeks to gather sufficient data</li>
                    <li>Aim for at least 100 participants per variant</li>
                    <li>Only change one variable at a time</li>
                    <li>Track both primary (conversion) and secondary (clicks) metrics</li>
                    <li>Wait for statistical significance (p &lt; 0.05) before declaring a winner</li>
                  </ul>
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ABTestDashboard
