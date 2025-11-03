import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@morningai/shared-ui';
import { AppleButton } from '@/components/ui/apple-button';
import { AppleInput } from '@/components/ui/apple-input';
import { AlertCircle } from 'lucide-react';
import { regenerateBackupCodes } from '@/lib/2fa-api';
import { BackupCodesList } from './BackupCodesList';

interface RegenerateBackupCodesModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function RegenerateBackupCodesModal({
  open,
  onClose,
  onSuccess,
}: RegenerateBackupCodesModalProps) {
  const [password, setPassword] = useState('');
  const [newCodes, setNewCodes] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
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
          <DialogTitle>Regenerate Backup Codes</DialogTitle>
          <DialogDescription>
            {newCodes
              ? 'Save your new backup codes in a safe place'
              : 'Create new backup codes for your account'}
          </DialogDescription>
        </DialogHeader>

        {!newCodes ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-500 mt-0.5" />
              <p className="text-xs text-yellow-800 dark:text-yellow-200">
                <strong>Warning:</strong> This will invalidate all your existing backup codes.
              </p>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
                {error}
              </div>
            )}

            <AppleInput
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              showPasswordToggle
              required
              disabled={loading}
              helperText="Confirm your password to regenerate backup codes"
            />

            <div className="flex gap-2">
              <AppleButton
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={loading}
                className="flex-1"
              >
                Cancel
              </AppleButton>
              <AppleButton
                type="submit"
                disabled={loading || !password}
                className="flex-1"
              >
                {loading ? 'Generating...' : 'Regenerate Codes'}
              </AppleButton>
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
