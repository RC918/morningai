import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { Button } from '@morningai/shared-ui';
import { Input } from '@morningai/shared-ui';
import { Label } from '@morningai/shared-ui';
import { Shield, Key, QrCode, FileKey, CheckCircle2 } from 'lucide-react';
import { setupTwoFA, verifyTwoFASetup } from '../../lib/2fa-api';
import { QRCodeDisplay } from './QRCodeDisplay';
import { BackupCodesList } from './BackupCodesList';

export function TwoFASetupWizard({ onComplete, onCancel }) {
  const { t } = useTranslation();
  const [step, setStep] = useState('password');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [setupData, setSetupData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!password) return;

    try {
      setLoading(true);
      setError(null);
      const data = await setupTwoFA({ password });
      setSetupData(data);
      setStep('qr');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to setup 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    if (!totpCode) return;

    try {
      setLoading(true);
      setError(null);
      await verifyTwoFASetup({ code: totpCode });
      setStep('backup');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    setStep('complete');
    setTimeout(() => {
      onComplete();
    }, 1500);
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'password', label: t('settings.2fa.disable.passwordLabel'), icon: Key },
      { id: 'qr', label: 'QR Code', icon: QrCode },
      { id: 'verify', label: t('settings.2fa.setup.verify'), icon: Shield },
      { id: 'backup', label: t('settings.2fa.backupCodes.title'), icon: FileKey },
    ];

    const currentIndex = steps.findIndex(s => s.id === step);

    return (
      <div className="flex items-center justify-between mb-6">
        {steps.map((s, index) => {
          const Icon = s.icon;
          const isActive = s.id === step;
          const isCompleted = index < currentIndex;

          return (
            <React.Fragment key={s.id}>
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isActive
                      ? 'bg-primary text-white'
                      : 'bg-accent text-muted-foreground'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>
                <span className="text-xs font-medium">{s.label}</span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 transition-colors ${
                    index < currentIndex ? 'bg-green-500' : 'bg-accent'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  if (step === 'complete') {
    return (
      <Card>
        <CardContent className="pt-6 flex flex-col items-center space-y-4 py-8">
          <div className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8 text-white" />
          </div>
          <div className="text-center space-y-2">
            <h3 className="text-xl font-semibold">{t('settings.2fa.setup.successTitle')}</h3>
            <p className="text-sm text-muted-foreground">
              {t('settings.2fa.setup.successDescription')}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          {t('settings.2fa.setup.title')}
        </CardTitle>
        <CardDescription>
          {t('settings.2fa.setup.subtitle')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {renderStepIndicator()}

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
            {error}
          </div>
        )}

        {step === 'password' && (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                {t('settings.2fa.setup.passwordPrompt')}
              </p>
              <div className="space-y-2">
                <Label htmlFor="password">{t('settings.2fa.disable.passwordLabel')}</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={loading}
                className="flex-1"
              >
                {t('settings.2fa.setup.cancel')}
              </Button>
              <Button type="submit" disabled={loading || !password} className="flex-1">
                {loading ? t('settings.2fa.setup.verifying') : t('settings.2fa.setup.continue')}
              </Button>
            </div>
          </form>
        )}

        {step === 'qr' && setupData && (
          <div className="space-y-4">
            <QRCodeDisplay qrCode={setupData.qr_code} secret={setupData.secret} />
            <Button onClick={() => setStep('verify')} className="w-full">
              {t('settings.2fa.setup.qrScanned')}
            </Button>
          </div>
        )}

        {step === 'verify' && (
          <form onSubmit={handleVerifySubmit} className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                {t('settings.2fa.setup.verifyPrompt')}
              </p>
              <div className="space-y-2">
                <Label htmlFor="totp-code">{t('settings.2fa.setup.verificationCodeLabel')}</Label>
                <Input
                  id="totp-code"
                  type="text"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder={t('settings.2fa.disable.totpCodePlaceholder')}
                  maxLength={6}
                  required
                  disabled={loading}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep('qr')}
                disabled={loading}
                className="flex-1"
              >
                {t('settings.2fa.setup.back')}
              </Button>
              <Button
                type="submit"
                disabled={loading || totpCode.length !== 6}
                className="flex-1"
              >
                {loading ? t('settings.2fa.setup.verifying') : t('settings.2fa.setup.verify')}
              </Button>
            </div>
          </form>
        )}

        {step === 'backup' && setupData && (
          <BackupCodesList
            backupCodes={setupData.backup_codes}
            onContinue={handleComplete}
          />
        )}
      </CardContent>
    </Card>
  );
}
