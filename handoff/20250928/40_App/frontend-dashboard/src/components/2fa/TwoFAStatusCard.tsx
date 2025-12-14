import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SettingsCard, Badge, Button } from '@morningai/shared-ui';
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
      <SettingsCard
        title={t('settings.2fa.title')}
        description={t('settings.2fa.loading')}
        icon={<Shield />}
        variant="blue"
      />
    );
  }

  if (error) {
    return (
      <SettingsCard
        title={t('settings.2fa.title')}
        description={error}
        icon={<Shield />}
        variant="red"
      />
    );
  }

  if (status?.feature_disabled) {
    return (
      <SettingsCard
        title={t('settings.2fa.title')}
        description={t('settings.2fa.subtitle')}
        icon={<Shield />}
        variant="default"
      >
        <div className="flex items-start p-4 bg-[var(--info-50)] rounded-lg border border-[var(--info-200)]">
          <AlertCircle className="w-5 h-5 text-[var(--info-600)] flex-shrink-0 mr-3" />
          <div className="space-y-1">
            <p className="font-medium text-[var(--info-900)]">
              {t('settings.2fa.featureDisabled.title')}
            </p>
            <p className="text-sm text-[var(--info-800)]">
              {t('settings.2fa.featureDisabled.description')}
            </p>
          </div>
        </div>
      </SettingsCard>
    );
  }

  const isEnabled = status?.enabled ?? false;

  return (
    <SettingsCard
      title={t('settings.2fa.title')}
      description={t('settings.2fa.cardDescription')}
      icon={<Shield />}
      variant={isEnabled ? 'green' : 'default'}
    >
      <div className="space-y-4" data-testid="2fa-status-card">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-medium text-[var(--text-primary)]">{t('settings.2fa.status.label')}</span>
              {isEnabled ? (
                <Badge data-testid="2fa-status" variant="default" className="bg-[var(--success-500)] flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {t('settings.2fa.status.enabled')}
                </Badge>
              ) : (
                <Badge data-testid="2fa-status" variant="outline" className="text-[var(--text-secondary)]">
                  {t('settings.2fa.status.disabled')}
                </Badge>
              )}
            </div>
            {isEnabled && status?.verified_at && (
              <p className="text-sm text-[var(--text-secondary)]">
                {t('settings.2fa.status.enabledOn', { date: new Date(status.verified_at).toLocaleDateString() })}
              </p>
            )}
          </div>
          {!isEnabled ? (
            <Button onClick={onSetupClick} size="sm">
              {t('settings.2fa.actions.enable')}
            </Button>
          ) : (
            <Button onClick={onDisableClick} variant="destructive" size="sm">
              {t('settings.2fa.actions.disable')}
            </Button>
          )}
        </div>

        {isEnabled && (
          <div className="pt-4 border-t border-[var(--border)] space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Key className="w-4 h-4 text-[var(--text-secondary)]" />
                  <span className="text-sm font-medium text-[var(--text-primary)]">{t('settings.2fa.backupCodes.title')}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)]" data-testid="backup-codes-remaining">
                  {t('settings.2fa.backupCodes.remaining', { count: status?.backup_codes_remaining ?? 0 })}
                </p>
              </div>
              <Button
                onClick={onRegenerateClick}
                variant="outline"
                size="sm"
                disabled={(status?.backup_codes_remaining ?? 0) > 4}
              >
                {t('settings.2fa.actions.regenerate')}
              </Button>
            </div>
            {(status?.backup_codes_remaining ?? 0) <= 2 && (
              <div className="flex items-start gap-2 p-3 bg-[var(--warning-50)] rounded-lg">
                <AlertCircle className="w-4 h-4 text-[var(--warning-600)]" />
                <p className="text-xs text-[var(--warning-800)]">
                  {t('settings.2fa.backupCodes.lowWarning', { count: status?.backup_codes_remaining ?? 0 })}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </SettingsCard>
  );
}
