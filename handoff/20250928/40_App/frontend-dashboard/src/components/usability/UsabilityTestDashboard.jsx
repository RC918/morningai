/**
 * Usability Test Dashboard
 * 
 * Admin interface for managing usability testing sessions, viewing results,
 * and exporting data for analysis.
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

export function UsabilityTestDashboard() {
  const [participantId, setParticipantId] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [currentSession, setCurrentSession] = useState(null)
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [showSUS, setShowSUS] = useState(false)
  const [showNPS, setShowNPS] = useState(false)
  const [susResults, setSusResults] = useState([])
  const [npsResults, setNpsResults] = useState([])

  useEffect(() => {
    loadSessions()
    loadSurveyResults()
  }, [])

  const loadSessions = () => {
    const sessionIds = usabilityTest.listSessions()
    const loadedSessions = sessionIds
      .map(id => usabilityTest.loadSession(id))
      .filter(Boolean)
      .sort((a, b) => b.startTime - a.startTime)
    setSessions(loadedSessions)
  }

  const loadSurveyResults = () => {
    try {
      const sus = JSON.parse(localStorage.getItem('sus_results') || '[]')
      const nps = JSON.parse(localStorage.getItem('nps_results') || '[]')
      setSusResults(sus)
      setNpsResults(nps)
    } catch (error) {
      console.error('Failed to load survey results:', error)
    }
  }

  const handleStartSession = () => {
    if (!participantId.trim()) {
      alert('Please enter a participant ID')
      return
    }

    const session = usabilityTest.start(participantId, sessionId || undefined)
    setCurrentSession(session)
    loadSessions()
  }

  const handleEndSession = () => {
    if (!currentSession) return

    const summary = usabilityTest.end()
    setCurrentSession(null)
    setShowSUS(true)
    loadSessions()
  }

  const handleSUSComplete = (result) => {
    const updated = [...susResults, result]
    setSusResults(updated)
    localStorage.setItem('sus_results', JSON.stringify(updated))
    setShowSUS(false)
    setShowNPS(true)
  }

  const handleNPSComplete = (result) => {
    const updated = [...npsResults, result]
    setNpsResults(updated)
    localStorage.setItem('nps_results', JSON.stringify(updated))
    setShowNPS(false)
    setParticipantId('')
    setSessionId('')
  }

  const handleViewSession = (session) => {
    setSelectedSession(session)
  }

  const handleDeleteSession = (sessionId) => {
    if (confirm('Are you sure you want to delete this session?')) {
      usabilityTest.deleteSession(sessionId)
      loadSessions()
      if (selectedSession?.sessionId === sessionId) {
        setSelectedSession(null)
      }
    }
  }

  const handleExportSession = (session) => {
    const data = session.exportData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `usability-test-${session.sessionId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExportAllData = () => {
    const allData = {
      sessions: sessions.map(s => s.exportData()),
      sus_results: susResults,
      nps_results: npsResults,
      summary: calculateOverallSummary(),
      exported_at: new Date().toISOString()
    }

    const blob = new Blob([JSON.stringify(allData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `usability-testing-complete-export-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const calculateOverallSummary = () => {
    const completedSessions = sessions.filter(s => !s.isRecording)
    
    const totalTasks = completedSessions.reduce((sum, s) => sum + s.tasks.length, 0)
    const completedTasks = completedSessions.reduce(
      (sum, s) => sum + s.tasks.filter(t => t.endTime !== null).length, 
      0
    )
    const successfulTasks = completedSessions.reduce(
      (sum, s) => sum + s.tasks.filter(t => t.success === true).length, 
      0
    )

    const avgSUS = susResults.length > 0
      ? susResults.reduce((sum, r) => sum + r.sus_score, 0) / susResults.length
      : null

    const npsScores = npsResults.map(r => r.nps_score)
    const npsResult = npsScores.length > 0 ? NPSCalculator.calculate(npsScores) : null

    return {
      total_sessions: completedSessions.length,
      total_participants: new Set(completedSessions.map(s => s.participantId)).size,
      total_tasks: totalTasks,
      completed_tasks: completedTasks,
      successful_tasks: successfulTasks,
      success_rate: completedTasks > 0 ? ((successfulTasks / completedTasks) * 100).toFixed(1) + '%' : 'N/A',
      avg_sus_score: avgSUS ? avgSUS.toFixed(1) : 'N/A',
      nps_score: npsResult ? npsResult.nps : 'N/A',
      nps_rating: npsResult ? npsResult.rating : 'N/A'
    }
  }

  const summary = calculateOverallSummary()

  if (showSUS) {
    return (
      <div className="container mx-auto py-8">
        <SUSQuestionnaire
          participantId={participantId}
          sessionId={currentSession?.sessionId}
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
          sessionId={currentSession?.sessionId}
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
              <div className="space-y-2">
                <Label htmlFor="participant-id">Participant ID *</Label>
                <Input
                  id="participant-id"
                  placeholder="e.g., P001, P002, ..."
                  value={participantId}
                  onChange={(e) => setParticipantId(e.target.value)}
                  disabled={!!currentSession}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="session-id">Session ID (optional)</Label>
                <Input
                  id="session-id"
                  placeholder="Auto-generated if left empty"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  disabled={!!currentSession}
                />
              </div>

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
              {sessions.map((session) => {
                const summary = session.getSessionSummary()
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
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewSession(session)}
                          >
                            <Eye className="h-4 w-4" />
                          </AppleButton>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleExportSession(session)}
                          >
                            <Download className="h-4 w-4" />
                          </AppleButton>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteSession(session.sessionId)}
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
                    {susResults.map((result, index) => (
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
                    {npsResults.map((result, index) => (
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
