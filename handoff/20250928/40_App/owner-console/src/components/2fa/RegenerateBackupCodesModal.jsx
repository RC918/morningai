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
import { regenerateBackupCodes } from '../../lib/2fa-api';
import { BackupCodesList } from './BackupCodesList';

export function RegenerateBackupCodesModal({ open, onClose, onSuccess }) {
  const { t } = useTranslation();
  const [password, setPassword] = useState('');
  const [newCodes, setNewCodes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password) return;

    try {
      setLoading(true);
      setError(null);
      const data = await regenerateBackupCodes({ password });
      setNewCodes(data.backup_codes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate backup codes');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    setPassword('');
    setNewCodes(null);
    setError(null);
    onSuccess();
    onClose();
  };

  const handleClose = () => {
    if (!loading && !newCodes) {
      setPassword('');
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('settings.2fa.backupCodes.regenerateTitle')}</DialogTitle>
          <DialogDescription>
            {newCodes
              ? t('settings.2fa.backupCodes.saveDescription')
              : t('settings.2fa.backupCodes.regenerateDescription')}
          </DialogDescription>
        </DialogHeader>

        {!newCodes ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-500 mt-0.5" />
              <p className="text-xs text-yellow-800 dark:text-yellow-200">
                <strong>{t('settings.2fa.backupCodes.regenerateWarning')}</strong> {t('settings.2fa.backupCodes.regenerateWarningMessage')}
              </p>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">{t('settings.2fa.backupCodes.passwordLabel')}</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                {t('settings.2fa.backupCodes.passwordHelper')}
              </p>
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
                disabled={loading || !password}
                className="flex-1"
              >
                {loading ? t('settings.2fa.backupCodes.regenerating') : t('settings.2fa.backupCodes.regenerateButton')}
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <BackupCodesList backupCodes={newCodes} onContinue={handleComplete} />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
