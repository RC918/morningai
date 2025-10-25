/**
 * NPS (Net Promoter Score) Questionnaire Component
 * 
 * Implements the standard NPS survey with automatic scoring and categorization.
 * 
 * @component
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle2, AlertCircle, ThumbsUp, Minus, ThumbsDown } from 'lucide-react'
import { NPSCalculator } from '@/lib/usability-testing'

const NPS_QUESTION = 'How likely are you to recommend this product to a friend or colleague?'

export function NPSQuestionnaire({ onComplete, participantId, sessionId }) {
  const [score, setScore] = useState(null)
  const [feedback, setFeedback] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleScoreSelect = (value) => {
    setScore(value)
  }

  const handleSubmit = () => {
    if (score === null) return

    const category = score >= 9 ? 'Promoter' : score >= 7 ? 'Passive' : 'Detractor'

    const result = {
      participant_id: participantId,
      session_id: sessionId,
      nps_score: score,
      nps_category: category,
      feedback: feedback.trim(),
      timestamp: new Date().toISOString()
    }

    setSubmitted(true)

    if (onComplete) {
      onComplete(result)
    }
  }

  const getCategory = (value) => {
    if (value >= 9) return { label: 'Promoter', color: 'text-green-600', icon: ThumbsUp }
    if (value >= 7) return { label: 'Passive', color: 'text-yellow-600', icon: Minus }
    return { label: 'Detractor', color: 'text-red-600', icon: ThumbsDown }
  }

  if (submitted) {
    const category = getCategory(score)
    const CategoryIcon = category.icon

    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-6 w-6 text-green-600" />
            NPS Survey Complete
          </CardTitle>
          <CardDescription>
            Thank you for your feedback!
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Your Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{score}</div>
                <p className="text-sm text-muted-foreground mt-1">out of 10</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Category
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`flex items-center gap-2 ${category.color}`}>
                  <CategoryIcon className="h-6 w-6" />
                  <span className="text-2xl font-bold">{category.label}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Category Definitions:</strong>
              <ul className="mt-2 space-y-1 text-sm">
                <li><strong>Promoters (9-10):</strong> Loyal enthusiasts who will recommend the product</li>
                <li><strong>Passives (7-8):</strong> Satisfied but unenthusiastic customers</li>
                <li><strong>Detractors (0-6):</strong> Unhappy customers who may damage the brand</li>
              </ul>
            </AlertDescription>
          </Alert>

          {feedback && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Your Feedback:</Label>
              <div className="p-4 bg-muted rounded-md text-sm">
                {feedback}
              </div>
            </div>
          )}

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
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Net Promoter Score (NPS)</CardTitle>
        <CardDescription>
          {NPS_QUESTION}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Not at all likely</span>
            <span>Extremely likely</span>
          </div>
          
          <div className="grid grid-cols-11 gap-2">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => {
              const isSelected = score === value
              const category = getCategory(value)
              
              return (
                <button
                  key={value}
                  onClick={() => handleScoreSelect(value)}
                  className={`
                    aspect-square rounded-lg border-2 transition-all
                    flex items-center justify-center text-lg font-semibold
                    hover:scale-110 hover:shadow-md
                    ${isSelected 
                      ? `${category.color} border-current bg-current/10 scale-110 shadow-md` 
                      : 'border-gray-300 hover:border-gray-400'
                    }
                  `}
                  aria-label={`Score ${value}`}
                >
                  {value}
                </button>
              )
            })}
          </div>

          <div className="flex justify-between text-xs text-muted-foreground pt-2">
            <div className="flex items-center gap-1">
              <ThumbsDown className="h-3 w-3 text-red-600" />
              <span>Detractors (0-6)</span>
            </div>
            <div className="flex items-center gap-1">
              <Minus className="h-3 w-3 text-yellow-600" />
              <span>Passives (7-8)</span>
            </div>
            <div className="flex items-center gap-1">
              <ThumbsUp className="h-3 w-3 text-green-600" />
              <span>Promoters (9-10)</span>
            </div>
          </div>
        </div>

        {score !== null && (
          <div className="space-y-3">
            <Label htmlFor="feedback">
              {score >= 9 
                ? "That's great! What do you like most about the product?" 
                : score >= 7 
                ? "Thank you! What could we do to improve your experience?" 
                : "We're sorry to hear that. What can we do better?"}
            </Label>
            <Textarea
              id="feedback"
              placeholder="Share your thoughts (optional)..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={4}
            />
          </div>
        )}

        {score === null && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Please select a score from 0 to 10 before submitting.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleSubmit} 
          disabled={score === null}
          className="w-full"
          size="lg"
        >
          Submit NPS Survey
        </Button>
      </CardFooter>
    </Card>
  )
}

export default NPSQuestionnaire
