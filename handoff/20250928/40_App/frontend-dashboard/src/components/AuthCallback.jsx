/**
 * Supabase Auth Callback Handler
 * 
 * This component handles the OAuth callback after successful authentication
 * with Supabase Auth. It processes the authentication tokens and redirects
 * the user to the dashboard.
 * 
 * Security Features:
 * - Automatic token handling by Supabase
 * - httpOnly cookies (when configured)
 * - Refresh token rotation
 * - PKCE verification
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { supabase, getSession } from '@/lib/supabaseClient';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          console.error('Session error:', sessionError);
          setError(sessionError.message);
          setStatus('error');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        if (!session) {
          setError(t('auth.sso.loginFailed'));
          setStatus('error');
          setTimeout(() => navigate('/login'), 3000);
          return;
        }

        setStatus('success');
        
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1500);
      } catch (err) {
        console.error('Auth callback error:', err);
        setError(err.message || t('auth.sso.loginFailed'));
        setStatus('error');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleAuthCallback();
  }, [navigate, t]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md px-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {status === 'processing' && (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  {t('auth.sso.processing')}
                </>
              )}
              {status === 'success' && (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                  {t('auth.sso.success')}
                </>
              )}
              {status === 'error' && (
                <>
                  <XCircle className="h-5 w-5 text-red-600" />
                  {t('auth.sso.error')}
                </>
              )}
            </CardTitle>
            <CardDescription>
              {status === 'processing' && t('auth.sso.processingMessage', { provider: 'SSO' })}
              {status === 'success' && t('auth.sso.successMessage')}
              {status === 'error' && t('auth.sso.redirectingToLogin')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {status === 'processing' && (
              <div className="flex justify-center py-4">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AuthCallback;
