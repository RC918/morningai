import React, { useState, useEffect } from 'react';
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
import { Shield, AlertCircle } from 'lucide-react';
import { TotpInput } from './TotpInput';
import { verifyTwoFALogin } from '@/lib/2fa-api';

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
  onSuccess,
  email,
  password,
}) {
  const { t } = useTranslation();
  const [totpCode, setTotpCode] = useState('');
  const [backupCode, setBackupCode] = useState('');
  const [useBackup, setUseBackup] = useState(false);
  const [rememberDevice, setRememberDevice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [attemptsRemaining, setAttemptsRemaining] = useState(5);

  useEffect(() => {
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
      const result = await verifyTwoFALogin({
        email,
        password,
        totp_code: useBackup ? undefined : code,
        backup_code: useBackup ? code : undefined,
        remember_device: rememberDevice,
      });

      if (result.success) {
        onSuccess();
      } else {
        setAttemptsRemaining(prev => Math.max(0, prev - 1));
        
        if (attemptsRemaining <= 1) {
          setError(t('auth.2fa.tooManyAttempts'));
        } else {
          setError(
            useBackup
              ? t('auth.2fa.invalidBackupCode', { attempts: attemptsRemaining - 1 })
              : t('auth.2fa.invalidCode', { attempts: attemptsRemaining - 1 })
          );
        }
        
        if (useBackup) {
          setBackupCode('');
        } else {
          setTotpCode('');
        }
      }
    } catch (err) {
      setError(err.message || t('auth.login.loginError'));
      setAttemptsRemaining(prev => Math.max(0, prev - 1));
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
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
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
              <AppleInput
                type="text"
                value={backupCode}
                onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                disabled={loading || attemptsRemaining === 0}
                className="font-mono"
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
