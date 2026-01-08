import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@morningai/shared-ui';
import { AppleButton } from '@/components/ui/apple-button';
import { AppleInput } from '@/components/ui/apple-input';
import { Shield, QrCode, FileKey, CheckCircle2, AlertCircle } from 'lucide-react';
import { enrollTwoFA, verifyEnrollTwoFA } from '@/lib/2fa-api';
import type { TwoFAEnrollResponse } from '@/types/2fa';
import { QRCodeDisplay } from './QRCodeDisplay';
import { BackupCodesList } from './BackupCodesList';

interface TwoFactorEnrollProps {
  open: boolean;
  onClose: () => void;
  onComplete: (params: { code: string; backupCodes: string[] }) => void;
  tmpLoginToken: string;
}

type EnrollStep = 'qr' | 'verify' | 'backup';

export function TwoFactorEnroll({ open, onClose, onComplete, tmpLoginToken }: TwoFactorEnrollProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState<EnrollStep>('qr');
  const [totpCode, setTotpCode] = useState('');
  const [enrollData, setEnrollData] = useState<TwoFAEnrollResponse | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEnrollStart = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await enrollTwoFA(tmpLoginToken);
      setEnrollData(data);
      setStep('qr');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start 2FA enrollment';
      const normalizedError = errorMessage.replace(/TMP_TOKEN_CONSUMED/g, 'TMP_TOKEN_INVALID');
      setError(normalizedError);
    } finally {
      setLoading(false);
    }
  }, [tmpLoginToken]);

  useEffect(() => {
    if (open && tmpLoginToken && !enrollData) {
      handleEnrollStart();
    }
  }, [open, tmpLoginToken, enrollData, handleEnrollStart]);

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!totpCode || totpCode.length !== 6) return;

    try {
      setLoading(true);
      setError(null);
      const response = await verifyEnrollTwoFA({ code: totpCode }, tmpLoginToken);
      setBackupCodes(response.backup_codes);
      setStep('backup');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Invalid verification code';
      const normalizedError = errorMessage.replace(/TMP_TOKEN_CONSUMED/g, 'TMP_TOKEN_INVALID');
      setError(normalizedError);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    onComplete({
      code: totpCode,
      backupCodes: backupCodes,
    });
  };

  const handleDialogClose = () => {
    setStep('qr');
    setTotpCode('');
    setEnrollData(null);
    setBackupCodes([]);
    setError(null);
    onClose();
  };

  const renderStepIndicator = () => {
    const steps = [
      { id: 'qr', label: 'QR Code', icon: QrCode },
      { id: 'verify', label: 'Verify', icon: Shield },
      { id: 'backup', label: 'Backup', icon: FileKey },
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
                      ? 'bg-success-500 text-white'
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
                    index < currentIndex ? 'bg-success-500' : 'bg-accent'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleDialogClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            {t('auth.2fa.enroll.title', 'Set Up Two-Factor Authentication')}
          </DialogTitle>
          <DialogDescription>
            {t('auth.2fa.enroll.description', 'Secure your account with two-factor authentication')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {renderStepIndicator()}

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 'qr' && enrollData && (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground space-y-2">
                <p>{t('auth.2fa.enroll.qrInstructions1', 'Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)')}</p>
                <p>{t('auth.2fa.enroll.qrInstructions2', 'Or manually enter the secret key shown below.')}</p>
              </div>
              <QRCodeDisplay qrCode={enrollData.qr_code} secret={enrollData.secret} />
              <AppleButton onClick={() => setStep('verify')} className="w-full" disabled={loading}>
                {t('auth.2fa.enroll.qrScanned', 'I\'ve Scanned the QR Code')}
              </AppleButton>
            </div>
          )}

          {step === 'verify' && (
            <form onSubmit={handleVerifySubmit} className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {t('auth.2fa.enroll.verifyPrompt', 'Enter the 6-digit code from your authenticator app to verify setup')}
                </p>
                <AppleInput
                  type="text"
                  label={t('auth.2fa.enroll.verificationCodeLabel', 'Verification Code')}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  required
                  disabled={loading}
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <AppleButton
                  type="button"
                  variant="outline"
                  onClick={() => setStep('qr')}
                  disabled={loading}
                  className="flex-1"
                >
                  {t('auth.2fa.enroll.back', 'Back')}
                </AppleButton>
                <AppleButton
                  type="submit"
                  disabled={loading || totpCode.length !== 6}
                  className="flex-1"
                >
                  {loading ? t('auth.2fa.enroll.verifying', 'Verifying...') : t('auth.2fa.enroll.verify', 'Verify')}
                </AppleButton>
              </div>
            </form>
          )}

          {step === 'backup' && backupCodes.length > 0 && (
            <div className="space-y-4">
              <div className="p-4 bg-warning-500/10 border border-warning-500/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-warning-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm space-y-1">
                    <p className="font-semibold text-warning-900 dark:text-warning-100">
                      {t('auth.2fa.enroll.backupCodesWarning', 'Save these backup codes!')}
                    </p>
                    <p className="text-warning-800 dark:text-warning-200">
                      {t('auth.2fa.enroll.backupCodesDescription', 'These codes can be used to access your account if you lose your authenticator device. Store them in a safe place.')}
                    </p>
                  </div>
                </div>
              </div>
              <BackupCodesList
                backupCodes={backupCodes}
                onContinue={handleComplete}
              />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
