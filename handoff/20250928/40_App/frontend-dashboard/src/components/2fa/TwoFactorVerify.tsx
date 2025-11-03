import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@morningai/shared-ui';
import { AppleButton } from '@/components/ui/apple-button';
import { Shield, AlertCircle } from 'lucide-react';
import { TotpInput } from './TotpInput';

interface TwoFactorVerifyProps {
  open: boolean;
  onClose: () => void;
  onVerify: (params: {
    code: string;
    isBackup: boolean;
    rememberDevice: boolean;
  }) => Promise<void>;
}

/**
 * TwoFactorVerify Component
 * 
 * Dialog for verifying 2FA code during login.
 * Features:
 * - TOTP code input with auto-submit
 * - Backup code option
 * - Remember device checkbox
 * - Error handling with retry count
 * - Loading states
 * - Programmatic focus management
 */
export function TwoFactorVerify({
  open,
  onClose,
  onVerify,
}: TwoFactorVerifyProps) {
  const { t } = useTranslation();
  const [totpCode, setTotpCode] = useState('');
  const [backupCode, setBackupCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [rememberDevice, setRememberDevice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attemptsRemaining, setAttemptsRemaining] = useState(5);
  const backupInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setTotpCode('');
      setBackupCode('');
      setUseBackupCode(false);
      setRememberDevice(false);
      setError(null);
      setAttemptsRemaining(5);
    }
  }, [open]);

  useEffect(() => {
    if (open && useBackupCode && backupInputRef.current && attemptsRemaining > 0) {
      backupInputRef.current.focus();
    }
  }, [open, useBackupCode, attemptsRemaining]);

  const handleVerifyTotp = async (code: string) => {
    if (loading) return;

    try {
      setLoading(true);
      setError(null);

      await onVerify({
        code,
        isBackup: false,
        rememberDevice,
      });

    } catch (err) {
      const newAttempts = attemptsRemaining - 1;
      setAttemptsRemaining(newAttempts);
      
      if (newAttempts <= 0) {
        setError(t('auth.2fa.tooManyAttempts'));
      } else {
        setError(
          t('auth.2fa.invalidCode', {
            attempts: newAttempts,
            defaultValue: `Invalid code. ${newAttempts} attempts remaining.`,
          })
        );
      }
      setTotpCode('');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyBackupCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!backupCode || loading) return;

    try {
      setLoading(true);
      setError(null);

      await onVerify({
        code: backupCode,
        isBackup: true,
        rememberDevice,
      });

    } catch (err) {
      const newAttempts = attemptsRemaining - 1;
      setAttemptsRemaining(newAttempts);
      
      if (newAttempts <= 0) {
        setError(t('auth.2fa.tooManyAttempts'));
      } else {
        setError(
          t('auth.2fa.invalidBackupCode', {
            attempts: newAttempts,
            defaultValue: `Invalid backup code. ${newAttempts} attempts remaining.`,
          })
        );
      }
      setBackupCode('');
    } finally {
      setLoading(false);
    }
  };

  const handleTotpComplete = (code: string) => {
    handleVerifyTotp(code);
  };

  const toggleBackupCode = () => {
    setUseBackupCode(!useBackupCode);
    setError(null);
    setTotpCode('');
    setBackupCode('');
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            {t('auth.2fa.verifyTitle')}
          </DialogTitle>
          <DialogDescription>
            {useBackupCode
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

          {!useBackupCode ? (
            <>
              <TotpInput
                value={totpCode}
                onChange={setTotpCode}
                onComplete={handleTotpComplete}
                disabled={loading || attemptsRemaining <= 0}
                error={!!error}
              />

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="remember-device"
                  checked={rememberDevice}
                  onChange={(e) => setRememberDevice(e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 rounded border-input text-primary focus:ring-2 focus:ring-primary/20"
                />
                <label
                  htmlFor="remember-device"
                  className="text-sm text-muted-foreground cursor-pointer"
                >
                  {t('auth.2fa.rememberDevice')}
                </label>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  onClick={toggleBackupCode}
                  disabled={loading}
                  className="text-sm text-primary hover:underline disabled:opacity-50"
                >
                  {t('auth.2fa.useBackupCode')}
                </button>
              </div>
            </>
          ) : (
            <form onSubmit={handleVerifyBackupCode} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="backup-code" className="text-sm font-medium text-foreground">
                  {t('auth.2fa.backupCodeLabel')}
                </label>
                <input
                  ref={backupInputRef}
                  id="backup-code"
                  type="text"
                  value={backupCode}
                  onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                  placeholder={t('auth.2fa.backupCodePlaceholder', 'XXXX-XXXX-XXXX-XXXX')}
                  disabled={loading || attemptsRemaining <= 0}
                  className="w-full h-11 px-4 py-3 rounded-xl border-2 border-input bg-background/80 backdrop-blur-sm text-base transition-all outline-none focus:border-primary focus:ring-[3px] focus:ring-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-muted-foreground">
                  {t('auth.2fa.backupCodeHelp')}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="remember-device-backup"
                  checked={rememberDevice}
                  onChange={(e) => setRememberDevice(e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 rounded border-input text-primary focus:ring-2 focus:ring-primary/20"
                />
                <label
                  htmlFor="remember-device-backup"
                  className="text-sm text-muted-foreground cursor-pointer"
                >
                  {t('auth.2fa.rememberDevice')}
                </label>
              </div>

              <AppleButton
                type="submit"
                disabled={loading || !backupCode || attemptsRemaining <= 0}
                className="w-full"
              >
                {loading ? t('auth.2fa.verifying') : t('auth.2fa.verify')}
              </AppleButton>

              <div className="text-center">
                <button
                  type="button"
                  onClick={toggleBackupCode}
                  disabled={loading}
                  className="text-sm text-primary hover:underline disabled:opacity-50"
                >
                  {t('auth.2fa.useTotpCode')}
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="flex gap-2">
          <AppleButton
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={loading}
            className="flex-1"
          >
            {t('auth.2fa.cancel')}
          </AppleButton>
        </div>
      </DialogContent>
    </Dialog>
  );
}
