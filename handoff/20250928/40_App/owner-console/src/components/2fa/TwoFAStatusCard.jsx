import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { Badge } from '@morningai/shared-ui';
import { Button } from '@morningai/shared-ui';
import { Shield, CheckCircle2, AlertCircle, Key } from 'lucide-react';
import { getTwoFAStatus } from '../../lib/2fa-api';

export function TwoFAStatusCard({
  onSetupClick,
  onDisableClick,
  onRegenerateClick,
  refreshTrigger = 0,
}) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getTwoFAStatus();
        setStatus(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load 2FA status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [refreshTrigger]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Two-Factor Authentication
          </CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Two-Factor Authentication
          </CardTitle>
          <CardDescription className="text-destructive flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const isEnabled = status?.enabled ?? false;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Two-Factor Authentication
        </CardTitle>
        <CardDescription>
          Add an extra layer of security to your account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">Status</span>
              {isEnabled ? (
                <Badge variant="default" className="bg-green-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Enabled
                </Badge>
              ) : (
                <Badge variant="outline" className="text-gray-600">
                  Disabled
                </Badge>
              )}
            </div>
            {isEnabled && status?.verified_at && (
              <p className="text-sm text-muted-foreground">
                Enabled on {new Date(status.verified_at).toLocaleDateString()}
              </p>
            )}
          </div>
          {!isEnabled ? (
            <Button onClick={onSetupClick} size="sm">
              Enable 2FA
            </Button>
          ) : (
            <Button onClick={onDisableClick} variant="destructive" size="sm">
              Disable 2FA
            </Button>
          )}
        </div>

        {isEnabled && (
          <div className="pt-4 border-t space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <Key className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Backup Codes</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {status?.backup_codes_remaining ?? 0} codes remaining
                </p>
              </div>
              <Button
                onClick={onRegenerateClick}
                variant="outline"
                size="sm"
                disabled={(status?.backup_codes_remaining ?? 0) > 4}
              >
                Regenerate
              </Button>
            </div>
            {(status?.backup_codes_remaining ?? 0) <= 2 && (
              <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-500 mt-0.5" />
                <p className="text-xs text-yellow-800 dark:text-yellow-200">
                  You have {status?.backup_codes_remaining ?? 0} backup codes remaining. Consider regenerating them.
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
