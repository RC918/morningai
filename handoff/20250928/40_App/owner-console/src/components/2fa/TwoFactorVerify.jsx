import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@morningai/shared-ui';
import { AppleButton } from '@/components/apple/apple-button';
import { Shield, AlertCircle } from 'lucide-react';
import { TotpInput } from './TotpInput';

/**
 * TwoFactorVerify Component
 * 
 * Dialog for verifying 2FA codes during login.
 * Features:
 * - TOTP code input with auto-submit
 * - Backup code option
 * - Remember device checkbox
 * - Error handling with retry count
 * - Rate limiting feedback
 */
export function TwoFactorVerify({
  open,
  onClose,
  onVerify,
}) {
  console.info('[2FA] TwoFactorVerify render', { open, build: '86765b16-debug' });
  
  const { t } = useTranslation();
  const [totpCode, setTotpCode] = useState('');
  const [backupCode, setBackupCode] = useState('');
  const [useBackup, setUseBackup] = useState(false);
  const [rememberDevice, setRememberDevice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [attemptsRemaining, setAttemptsRemaining] = useState(5);

  useEffect(() => {
    console.info('[2FA] useEffect open changed', { open });
    if (open) {
      setTotpCode('');
      setBackupCode('');
      setUseBackup(false);
      setRememberDevice(false);
      setError('');
      setAttemptsRemaining(5);
    }
  }, [open]);

  const handleVerify = async () => {
    if (loading) return;

    const code = useBackup ? backupCode : totpCode;
    if (!code || (useBackup && code.length < 16) || (!useBackup && code.length !== 6)) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onVerify({
        code,
        isBackup: useBackup,
        rememberDevice,
      });

    } catch (err) {
      const newAttempts = Math.max(0, attemptsRemaining - 1);
      setAttemptsRemaining(newAttempts);
      
      if (newAttempts <= 0) {
        setError(t('auth.2fa.tooManyAttempts'));
      } else {
        setError(
          useBackup
            ? t('auth.2fa.invalidBackupCode', { attempts: newAttempts })
            : t('auth.2fa.invalidCode', { attempts: newAttempts })
        );
      }
      
      if (useBackup) {
        setBackupCode('');
      } else {
        setTotpCode('');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTotpComplete = (code) => {
    setTotpCode(code);
    setTimeout(() => {
      handleVerify();
    }, 100);
  };

  const handleToggleBackup = () => {
    setUseBackup(!useBackup);
    setError('');
    setTotpCode('');
    setBackupCode('');
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { console.info('[2FA] onOpenChange', { isOpen }); if (!isOpen) onClose(); }}>
      <DialogContent className="sm:max-w-md z-[10001]">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <DialogTitle>{t('auth.2fa.verifyTitle')}</DialogTitle>
          </div>
          <DialogDescription>
            {useBackup
              ? t('auth.2fa.verifyBackupDescription')
              : t('auth.2fa.verifyDescription')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <div className="flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {useBackup ? (
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                {t('auth.2fa.backupCodeLabel')}
              </label>
              <input
                type="text"
                value={backupCode}
                onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                placeholder={t('auth.2fa.backupCodePlaceholder', 'XXXX-XXXX-XXXX-XXXX')}
                disabled={loading || attemptsRemaining === 0}
                className="w-full h-11 px-4 py-3 rounded-xl border-2 border-input bg-background/80 backdrop-blur-sm text-base font-mono transition-all outline-none focus:border-primary focus:ring-[3px] focus:ring-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-muted-foreground">
                {t('auth.2fa.backupCodeHelp')}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                {t('auth.2fa.totpCodeLabel')}
              </label>
              <TotpInput
                value={totpCode}
                onChange={setTotpCode}
                onComplete={handleTotpComplete}
                disabled={loading || attemptsRemaining === 0}
                error={!!error}
              />
              <p className="text-xs text-muted-foreground text-center">
                {t('auth.2fa.totpCodeHelp')}
              </p>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="remember-device"
              checked={rememberDevice}
              onChange={(e) => setRememberDevice(e.target.checked)}
              disabled={loading || attemptsRemaining === 0}
              className="rounded border-input"
            />
            <label
              htmlFor="remember-device"
              className="text-sm text-foreground cursor-pointer"
            >
              {t('auth.2fa.rememberDevice')}
            </label>
          </div>

          <div className="flex flex-col gap-2">
            <AppleButton
              onClick={handleVerify}
              disabled={
                loading ||
                attemptsRemaining === 0 ||
                (useBackup ? !backupCode : totpCode.length !== 6)
              }
              className="w-full"
            >
              {loading ? t('auth.2fa.verifying') : t('auth.2fa.verify')}
            </AppleButton>

            <AppleButton
              variant="ghost"
              onClick={handleToggleBackup}
              disabled={loading || attemptsRemaining === 0}
              className="w-full"
            >
              {useBackup ? t('auth.2fa.useTotpCode') : t('auth.2fa.useBackupCode')}
            </AppleButton>

            <AppleButton
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="w-full"
            >
              {t('auth.2fa.cancel')}
            </AppleButton>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
