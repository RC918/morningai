/**
 * Usability Test Dashboard
 * 
 * Admin interface for managing usability testing sessions, viewing results,
 * and exporting data for analysis.
 * 
 * @component
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui'
import { AppleButton } from '@/components/ui/apple-button'
import { AppleInput } from '@/components/ui/apple-input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@morningai/shared-ui'
import { Alert, AlertDescription } from '@morningai/shared-ui'
import { 
  Play, 
  Square, 
  Download, 
  Trash2, 
  Eye, 
  Users, 
  Clock, 
  CheckCircle2, 
  XCircle,
  AlertCircle,
  BarChart3
} from 'lucide-react'
import { usabilityTest, SUSCalculator, NPSCalculator } from '@/lib/usability-testing'
import SUSQuestionnaire from './SUSQuestionnaire'
import NPSQuestionnaire from './NPSQuestionnaire'

interface Task {
  taskId: string
  taskName: string
  description: string
  startTime: number
  endTime: number | null
  duration: number | null
  success: boolean | null
  errors: Array<{
    timestamp: number
    type: string
    description: string
  }>
  interactions: Array<{
    timestamp: number
    action: string
    target: string
    metadata: Record<string, unknown>
    taskId: string | null
  }>
  notes: Array<{
    timestamp: number
    text: string
  }>
}

interface SessionSummary {
  session_id: string
  participant_id: string
  total_duration_ms: number
  total_duration_minutes: number
  tasks_total: number
  tasks_completed: number
  tasks_successful: number
  tasks_failed: number
  success_rate: string
  total_errors: number
  total_interactions: number
  avg_task_duration_ms: number
  avg_task_duration_seconds: number
  tasks: Array<{
    task_id: string
    task_name: string
    duration_seconds: number | null
    success: boolean | null
    errors: number
    interactions: number
  }>
}

interface Session {
  participantId: string
  sessionId: string
  startTime: number
  tasks: Task[]
  interactions: Array<{
    timestamp: number
    action: string
    target: string
    metadata: Record<string, unknown>
    taskId: string | null
  }>
  currentTask: Task | null
  isRecording: boolean
  startSession: () => void
  startTask: (taskId: string, taskName: string, description: string) => void
  endTask: (success: boolean, notes?: string) => void
  recordError: (errorType: string, description: string) => void
  recordInteraction: (action: string, target: string, metadata?: Record<string, unknown>) => void
  addNote: (note: string) => void
  endSession: () => SessionSummary
  getSessionSummary: () => SessionSummary
  exportData: () => {
    session_id: string
    participant_id: string
    start_time: string
    end_time: string | null
    tasks: Task[]
    interactions: Array<{
      timestamp: number
      action: string
      target: string
      metadata: Record<string, unknown>
      taskId: string | null
    }>
    summary: SessionSummary
  }
}

interface SUSResult {
  participant_id: string
  session_id: string
  timestamp: string
  sus_score: number
  sus_grade: string
  sus_adjective: string
  responses: number[]
}

interface NPSResult {
  participant_id: string
  session_id: string
  timestamp: string
  nps_score: number
  nps_category: string
  nps_rating: string
  comment?: string
}

interface OverallSummary {
  total_sessions: number
  total_participants: number
  total_tasks: number
  completed_tasks: number
  successful_tasks: number
  success_rate: string
  avg_sus_score: string
  nps_score: string | number
  nps_rating: string
}

export function UsabilityTestDashboard(): React.ReactElement {
  const [participantId, setParticipantId] = useState<string>('')
  const [sessionId, setSessionId] = useState<string>('')
  const [currentSession, setCurrentSession] = useState<Session | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSession, setSelectedSession] = useState<Session | null>(null)
  const [showSUS, setShowSUS] = useState<boolean>(false)
  const [showNPS, setShowNPS] = useState<boolean>(false)
  const [susResults, setSusResults] = useState<SUSResult[]>([])
  const [npsResults, setNpsResults] = useState<NPSResult[]>([])

  useEffect(() => {
    loadSessions()
    loadSurveyResults()
  }, [])

  const loadSessions = (): void => {
    const sessionIds: string[] = usabilityTest.listSessions()
    const loadedSessions: any[] = sessionIds
      .map((id: string) => usabilityTest.loadSession(id))
      .filter(Boolean)
      .sort((a: any, b: any) => b.startTime - a.startTime)
    setSessions(loadedSessions)
  }

  const loadSurveyResults = (): void => {
    try {
      const sus: SUSResult[] = JSON.parse(localStorage.getItem('sus_results') || '[]')
      const nps: NPSResult[] = JSON.parse(localStorage.getItem('nps_results') || '[]')
      setSusResults(sus)
      setNpsResults(nps)
    } catch (error) {
      console.error('Failed to load survey results:', error)
    }
  }

  const handleStartSession = (): void => {
    if (!participantId.trim()) {
      alert('Please enter a participant ID')
      return
    }

    const session: any = usabilityTest.start(participantId, sessionId || undefined)
    setCurrentSession(session)
    loadSessions()
  }

  const handleEndSession = (): void => {
    if (!currentSession) return

    const summary = usabilityTest.end()
    if (summary) {
      setCurrentSession(null)
      setShowSUS(true)
      loadSessions()
    }
  }

  const handleSUSComplete = (result: SUSResult): void => {
    const updated: SUSResult[] = [...susResults, result]
    setSusResults(updated)
    localStorage.setItem('sus_results', JSON.stringify(updated))
    setShowSUS(false)
    setShowNPS(true)
  }

  const handleNPSComplete = (result: NPSResult): void => {
    const updated: NPSResult[] = [...npsResults, result]
    setNpsResults(updated)
    localStorage.setItem('nps_results', JSON.stringify(updated))
    setShowNPS(false)
    setParticipantId('')
    setSessionId('')
  }

  const handleViewSession = (session: Session): void => {
    setSelectedSession(session)
  }

  const handleDeleteSession = (sessionId: string): void => {
    if (confirm('Are you sure you want to delete this session?')) {
      usabilityTest.deleteSession(sessionId)
      loadSessions()
      if (selectedSession?.sessionId === sessionId) {
        setSelectedSession(null)
      }
    }
  }

  const handleExportSession = (session: Session): void => {
    const data = session.exportData()
    const blob: Blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url: string = URL.createObjectURL(blob)
    const a: HTMLAnchorElement = document.createElement('a')
    a.href = url
    a.download = `usability-test-${session.sessionId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExportAllData = (): void => {
    const allData = {
      sessions: sessions.map((s: Session) => s.exportData()),
      sus_results: susResults,
      nps_results: npsResults,
      summary: calculateOverallSummary(),
      exported_at: new Date().toISOString()
    }

    const blob: Blob = new Blob([JSON.stringify(allData, null, 2)], { type: 'application/json' })
    const url: string = URL.createObjectURL(blob)
    const a: HTMLAnchorElement = document.createElement('a')
    a.href = url
    a.download = `usability-testing-complete-export-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const calculateOverallSummary = (): OverallSummary => {
    const completedSessions: Session[] = sessions.filter((s: Session) => !s.isRecording)
    
    const totalTasks: number = completedSessions.reduce((sum: number, s: Session) => sum + s.tasks.length, 0)
    const completedTasks: number = completedSessions.reduce(
      (sum: number, s: Session) => sum + s.tasks.filter((t: Task) => t.endTime !== null).length, 
      0
    )
    const successfulTasks: number = completedSessions.reduce(
      (sum: number, s: Session) => sum + s.tasks.filter((t: Task) => t.success === true).length, 
      0
    )

    const avgSUS: number | null = susResults.length > 0
      ? susResults.reduce((sum: number, r: SUSResult) => sum + r.sus_score, 0) / susResults.length
      : null

    const npsScores: number[] = npsResults.map((r: NPSResult) => r.nps_score)
    const npsResult: { nps: number; rating: string } | null = npsScores.length > 0 ? NPSCalculator.calculate(npsScores) : null

    return {
      total_sessions: completedSessions.length,
      total_participants: new Set(completedSessions.map((s: Session) => s.participantId)).size,
      total_tasks: totalTasks,
      completed_tasks: completedTasks,
      successful_tasks: successfulTasks,
      success_rate: completedTasks > 0 ? ((successfulTasks / completedTasks) * 100).toFixed(1) + '%' : 'N/A',
      avg_sus_score: avgSUS ? avgSUS.toFixed(1) : 'N/A',
      nps_score: npsResult ? npsResult.nps : 'N/A',
      nps_rating: npsResult ? npsResult.rating : 'N/A'
    }
  }

  const summary: OverallSummary = calculateOverallSummary()

  if (showSUS) {
    return (
      <div className="container mx-auto py-8">
        <SUSQuestionnaire
          participantId={participantId}
          sessionId={currentSession?.sessionId || ''}
          onComplete={handleSUSComplete}
        />
      </div>
    )
  }

  if (showNPS) {
    return (
      <div className="container mx-auto py-8">
        <NPSQuestionnaire
          participantId={participantId}
          sessionId={currentSession?.sessionId || ''}
          onComplete={handleNPSComplete}
        />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Usability Testing Dashboard</h1>
          <p className="text-muted-foreground">Manage testing sessions and analyze results</p>
        </div>
        <AppleButton onClick={handleExportAllData} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export All Data
        </AppleButton>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Users className="h-4 w-4" />
              Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_sessions}</div>
            <p className="text-xs text-muted-foreground">{summary.total_participants} participants</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.success_rate}</div>
            <p className="text-xs text-muted-foreground">{summary.successful_tasks}/{summary.completed_tasks} tasks</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Avg SUS Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.avg_sus_score}</div>
            <p className="text-xs text-muted-foreground">{susResults.length} responses</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              NPS Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.nps_score}</div>
            <p className="text-xs text-muted-foreground">{summary.nps_rating}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="new-session" className="w-full">
        <TabsList>
          <TabsTrigger value="new-session">New Session</TabsTrigger>
          <TabsTrigger value="sessions">Sessions ({sessions.length})</TabsTrigger>
          <TabsTrigger value="results">Survey Results</TabsTrigger>
        </TabsList>

        <TabsContent value="new-session" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Start New Usability Test Session</CardTitle>
              <CardDescription>
                Enter participant information to begin a new testing session
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <AppleInput
                id="participant-id"
                label="Participant ID *"
                placeholder="e.g., P001, P002, ..."
                value={participantId}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void => setParticipantId(e.target.value)}
                disabled={!!currentSession}
                required
                haptic="light"
              />

              <AppleInput
                id="session-id"
                label="Session ID (optional)"
                placeholder="Auto-generated if left empty"
                value={sessionId}
                onChange={(e: React.ChangeEvent<HTMLInputElement>): void => setSessionId(e.target.value)}
                disabled={!!currentSession}
                haptic="light"
              />

              {currentSession && (
                <Alert>
                  <Clock className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Session Active:</strong> {currentSession.sessionId}
                    <br />
                    Participant: {currentSession.participantId}
                    <br />
                    Duration: {Math.round((Date.now() - currentSession.startTime) / 60000)} minutes
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex gap-2">
                {!currentSession ? (
                  <AppleButton onClick={handleStartSession} className="flex-1">
                    <Play className="h-4 w-4 mr-2" />
                    Start Session
                  </AppleButton>
                ) : (
                  <AppleButton onClick={handleEndSession} variant="destructive" className="flex-1">
                    <Square className="h-4 w-4 mr-2" />
                    End Session & Complete Surveys
                  </AppleButton>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sessions" className="space-y-4">
          {sessions.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No sessions recorded yet. Start a new session to begin testing.
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {sessions.map((session: Session) => {
                const summary: SessionSummary = session.getSessionSummary()
                return (
                  <Card key={session.sessionId}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">
                            {session.participantId}
                          </CardTitle>
                          <CardDescription>
                            Session: {session.sessionId}
                          </CardDescription>
                        </div>
                        <div className="flex gap-2">
                          <AppleButton
                            size="sm"
                            variant="outline"
                            onClick={(): void => handleViewSession(session)}
                          >
                            <Eye className="h-4 w-4" />
                          </AppleButton>
                          <AppleButton
                            size="sm"
                            variant="outline"
                            onClick={(): void => handleExportSession(session)}
                          >
                            <Download className="h-4 w-4" />
                          </AppleButton>
                          <AppleButton
                            size="sm"
                            variant="outline"
                            onClick={(): void => handleDeleteSession(session.sessionId)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </AppleButton>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">Duration</div>
                          <div className="font-medium">{summary.total_duration_minutes} min</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Tasks</div>
                          <div className="font-medium">{summary.tasks_completed}/{summary.tasks_total}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Success Rate</div>
                          <div className="font-medium">{summary.success_rate}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Errors</div>
                          <div className="font-medium">{summary.total_errors}</div>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>SUS Results ({susResults.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {susResults.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No SUS results yet</p>
                ) : (
                  <div className="space-y-2">
                    {susResults.map((result: SUSResult, index: number) => (
                      <div key={index} className="flex justify-between items-center p-2 border rounded">
                        <div>
                          <div className="font-medium">{result.participant_id}</div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(result.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{result.sus_score.toFixed(1)}</div>
                          <div className="text-xs text-muted-foreground">Grade {result.sus_grade}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>NPS Results ({npsResults.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {npsResults.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No NPS results yet</p>
                ) : (
                  <div className="space-y-2">
                    {npsResults.map((result: NPSResult, index: number) => (
                      <div key={index} className="flex justify-between items-center p-2 border rounded">
                        <div>
                          <div className="font-medium">{result.participant_id}</div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(result.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{result.nps_score}/10</div>
                          <div className="text-xs text-muted-foreground">{result.nps_category}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default UsabilityTestDashboard
