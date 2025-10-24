import React from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { withTranslation } from 'react-i18next'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    }
  }

  static getDerivedStateFromError(error) {
    return { 
      hasError: true,
      errorId: Math.random().toString(36).substr(2, 9)
    }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo
    })

    if (window.Sentry) {
      window.Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack
          }
        },
        tags: {
          section: 'error_boundary'
        }
      })
    }

    console.error('Error Boundary caught an error:', error, errorInfo)
  }

  handleRetry() {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    })
  }

  handleGoHome() {
    window.location.href = '/dashboard'
  }

  render() {
    const { t } = this.props
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-100 flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">
                {t('errorBoundary.title')}
              </CardTitle>
              <CardDescription className="text-lg text-gray-600 mt-2">
                {t('errorBoundary.description')}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">{t('errorBoundary.errorDetailsTitle')}</h3>
                <p className="text-sm text-gray-600 mb-2">
                  {t('errorBoundary.errorIdLabel')} <code className="bg-gray-200 px-2 py-1 rounded text-xs">{this.state.errorId}</code>
                </p>
                {this.state.error && (
                  <p className="text-sm text-red-600 font-mono bg-red-50 p-2 rounded">
                    {this.state.error.toString()}
                  </p>
                )}
              </div>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button 
                  onClick={this.handleRetry.bind(this)} 
                  className="flex items-center gap-2"
                  aria-label={t('errorBoundary.reloadAriaLabel')}
                >
                  <RefreshCw className="w-4 h-4" />
                  {t('errorBoundary.reloadButton')}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={this.handleGoHome.bind(this)}
                  className="flex items-center gap-2"
                  aria-label={t('errorBoundary.homeAriaLabel')}
                >
                  <Home className="w-4 h-4" />
                  {t('errorBoundary.homeButton')}
                </Button>
              </div>

              <div className="text-center text-sm text-gray-600">
                {t('errorBoundary.supportMessage')}
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

export default withTranslation()(ErrorBoundary)
