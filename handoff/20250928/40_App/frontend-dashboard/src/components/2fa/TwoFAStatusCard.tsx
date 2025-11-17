import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { Badge } from '@morningai/shared-ui';
import { AppleButton } from '@/components/ui/apple-button';
import { Shield, CheckCircle2, AlertCircle, Key } from 'lucide-react';
import { getTwoFAStatus } from '@/lib/2fa-api';
import type { TwoFAStatusResponse } from '@/types/2fa';

interface TwoFAStatusCardProps {
  onSetupClick: () => void;
  onDisableClick: () => void;
  onRegenerateClick: () => void;
  refreshTrigger?: number;
}

export function TwoFAStatusCard({
  onSetupClick,
  onDisableClick,
  onRegenerateClick,
  refreshTrigger = 0,
}: TwoFAStatusCardProps) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<TwoFAStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
            {t('settings.2fa.title')}
          </CardTitle>
          <CardDescription>{t('settings.2fa.loading')}</CardDescription>
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
            {t('settings.2fa.title')}
          </CardTitle>
          <CardDescription className="text-destructive flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (status?.feature_disabled) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            {t('settings.2fa.title')}
          </CardTitle>
          <CardDescription>
            {t('settings.2fa.subtitle')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <p className="font-medium text-blue-900 dark:text-blue-100">
                {t('settings.2fa.featureDisabled.title')}
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {t('settings.2fa.featureDisabled.description')}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const isEnabled = status?.enabled ?? false;

  return (
    <Card data-testid="2fa-status-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          {t('settings.2fa.title')}
        </CardTitle>
        <CardDescription>
          {t('settings.2fa.cardDescription')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{t('settings.2fa.status.label')}</span>
              {isEnabled ? (
                <Badge data-testid="2fa-status" variant="default" className="bg-green-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {t('settings.2fa.status.enabled')}
                </Badge>
              ) : (
                <Badge data-testid="2fa-status" variant="outline" className="text-gray-600">
                  {t('settings.2fa.status.disabled')}
                </Badge>
              )}
            </div>
            {isEnabled && status?.verified_at && (
              <p className="text-sm text-muted-foreground">
                {t('settings.2fa.status.enabledOn', { date: new Date(status.verified_at).toLocaleDateString() })}
              </p>
            )}
          </div>
          {!isEnabled ? (
            <AppleButton onClick={onSetupClick} size="sm">
              {t('settings.2fa.actions.enable')}
            </AppleButton>
          ) : (
            <AppleButton onClick={onDisableClick} variant="destructive" size="sm">
              {t('settings.2fa.actions.disable')}
            </AppleButton>
          )}
        </div>

        {isEnabled && (
          <div className="pt-4 border-t space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <Key className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{t('settings.2fa.backupCodes.title')}</span>
                </div>
                <p className="text-xs text-muted-foreground" data-testid="backup-codes-remaining">
                  {t('settings.2fa.backupCodes.remaining', { count: status?.backup_codes_remaining ?? 0 })}
                </p>
              </div>
              <AppleButton
                onClick={onRegenerateClick}
                variant="outline"
                size="sm"
                disabled={(status?.backup_codes_remaining ?? 0) > 4}
              >
                {t('settings.2fa.actions.regenerate')}
              </AppleButton>
            </div>
            {(status?.backup_codes_remaining ?? 0) <= 2 && (
              <div className="flex items-start gap-2 p-3 bg-warning-50 dark:bg-warning-900/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-warning-600 dark:text-warning-500 mt-0.5" />
                <p className="text-xs text-warning-800 dark:text-warning-200">
                  {t('settings.2fa.backupCodes.lowWarning', { count: status?.backup_codes_remaining ?? 0 })}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
