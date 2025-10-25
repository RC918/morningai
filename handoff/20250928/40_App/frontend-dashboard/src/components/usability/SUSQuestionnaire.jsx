/**
 * SUS (System Usability Scale) Questionnaire Component
 * 
 * Implements the standardized 10-question SUS survey with automatic scoring.
 * 
 * @component
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle2, AlertCircle } from 'lucide-react'
import { SUSCalculator } from '@/lib/usability-testing'

const SUS_QUESTIONS = [
  'I think that I would like to use this system frequently',
  'I found the system unnecessarily complex',
  'I thought the system was easy to use',
  'I think that I would need the support of a technical person to be able to use this system',
  'I found the various functions in this system were well integrated',
  'I thought there was too much inconsistency in this system',
  'I would imagine that most people would learn to use this system very quickly',
  'I found the system very cumbersome to use',
  'I felt very confident using the system',
  'I needed to learn a lot of things before I could get going with this system'
]

const SCALE_LABELS = [
  'Strongly Disagree',
  'Disagree',
  'Neutral',
  'Agree',
  'Strongly Agree'
]

export function SUSQuestionnaire({ onComplete, participantId, sessionId }) {
  const [responses, setResponses] = useState(Array(10).fill(null))
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)

  const handleResponseChange = (questionIndex, value) => {
    const newResponses = [...responses]
    newResponses[questionIndex] = parseInt(value)
    setResponses(newResponses)
  }

  const isComplete = responses.every(r => r !== null)

  const handleSubmit = () => {
    if (!isComplete) return

    const susResult = SUSCalculator.calculate(responses)
    setResult(susResult)
    setSubmitted(true)

    if (onComplete) {
      onComplete({
        participant_id: participantId,
        session_id: sessionId,
        sus_score: susResult.score,
        sus_grade: susResult.grade,
        sus_adjective: susResult.adjective,
        responses: susResult.responses,
        timestamp: new Date().toISOString()
      })
    }
  }

  if (submitted && result) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-6 w-6 text-green-600" />
            SUS Questionnaire Complete
          </CardTitle>
          <CardDescription>
            Thank you for completing the System Usability Scale questionnaire
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  SUS Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{result.score.toFixed(1)}</div>
                <p className="text-sm text-muted-foreground mt-1">out of 100</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Grade
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{result.grade}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  {result.grade === 'A' && 'Excellent'}
                  {result.grade === 'B' && 'Good'}
                  {result.grade === 'C' && 'Average'}
                  {result.grade === 'D' && 'Below Average'}
                  {result.grade === 'F' && 'Poor'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Rating
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{result.adjective}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  {result.score >= 80.3 ? 'Top 10%' : 
                   result.score >= 68 ? 'Above Average' : 
                   result.score >= 51 ? 'Average' : 
                   'Below Average'}
                </p>
              </CardContent>
            </Card>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Industry Benchmark:</strong> The average SUS score is 68. 
              A score above 80.3 is considered excellent (Grade A).
              {result.score >= 80.3 && ' Your score exceeds the excellent threshold!'}
              {result.score >= 68 && result.score < 80.3 && ' Your score is above average.'}
              {result.score < 68 && ' There is room for improvement.'}
            </AlertDescription>
          </Alert>

          <div className="text-sm text-muted-foreground">
            <p><strong>Participant ID:</strong> {participantId}</p>
            <p><strong>Session ID:</strong> {sessionId}</p>
            <p><strong>Completed:</strong> {new Date().toLocaleString()}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>System Usability Scale (SUS)</CardTitle>
        <CardDescription>
          Please rate your agreement with each statement on a scale from 1 (Strongly Disagree) to 5 (Strongly Agree).
          There are no right or wrong answers - we want your honest opinion.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        {SUS_QUESTIONS.map((question, index) => (
          <div key={index} className="space-y-3">
            <Label className="text-base font-medium">
              {index + 1}. {question}
            </Label>
            <RadioGroup
              value={responses[index]?.toString()}
              onValueChange={(value) => handleResponseChange(index, value)}
              className="flex flex-col space-y-2"
            >
              {[1, 2, 3, 4, 5].map((value) => (
                <div key={value} className="flex items-center space-x-3">
                  <RadioGroupItem value={value.toString()} id={`q${index}-${value}`} />
                  <Label 
                    htmlFor={`q${index}-${value}`}
                    className="font-normal cursor-pointer flex-1"
                  >
                    <span className="font-medium">{value}</span> - {SCALE_LABELS[value - 1]}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        ))}

        {!isComplete && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Please answer all {SUS_QUESTIONS.length} questions before submitting.
              {responses.filter(r => r === null).length} question(s) remaining.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleSubmit} 
          disabled={!isComplete}
          className="w-full"
          size="lg"
        >
          Submit SUS Questionnaire
        </Button>
      </CardFooter>
    </Card>
  )
}

export default SUSQuestionnaire
