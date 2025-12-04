import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@morningai/shared-ui';
import { Button } from '@morningai/shared-ui';
import { Input } from '@morningai/shared-ui';
import { Label } from '@morningai/shared-ui';
import { AlertCircle } from 'lucide-react';
import { disableTwoFA } from '../../lib/2fa-api';

export function DisableTwoFAModal({ open, onClose, onSuccess }) {
  const { t } = useTranslation();
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password || !totpCode) return;

    try {
      setLoading(true);
      setError(null);
      await disableTwoFA({ password, totp_code: totpCode });
      setPassword('');
      setTotpCode('');
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setPassword('');
      setTotpCode('');
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('settings.2fa.disable.title')}</DialogTitle>
          <DialogDescription>
            {t('settings.2fa.disable.description')}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-500" />
            <p className="text-xs text-yellow-800 dark:text-yellow-200">
              <strong>{t('settings.2fa.disable.warning')}</strong> {t('settings.2fa.disable.warningMessage')}
            </p>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-4">
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
            <div className="space-y-2">
              <Label htmlFor="totp-code">{t('settings.2fa.disable.totpCodeLabel')}</Label>
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
              <p className="text-xs text-muted-foreground">
                {t('settings.2fa.disable.totpCodeHelper')}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
              className="flex-1"
            >
              {t('settings.2fa.disable.cancel')}
            </Button>
            <Button
              type="submit"
              variant="destructive"
              disabled={loading || !password || totpCode.length !== 6}
              className="flex-1"
            >
              {loading ? t('settings.2fa.disable.disabling') : t('settings.2fa.disable.confirmButton')}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
