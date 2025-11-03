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
import { disableTwoFA } from '@/lib/2fa-api';

interface DisableTwoFAModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function DisableTwoFAModal({ open, onClose, onSuccess }: DisableTwoFAModalProps) {
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
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
          <DialogTitle>Disable Two-Factor Authentication</DialogTitle>
          <DialogDescription>
            This will remove 2FA protection from your account. You can re-enable it at any time.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-500 mt-0.5" />
            <p className="text-xs text-yellow-800 dark:text-yellow-200">
              <strong>Warning:</strong> Disabling 2FA will make your account less secure.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <AppleInput
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              showPasswordToggle
              required
              disabled={loading}
            />
            <AppleInput
              type="text"
              label="Current TOTP Code"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              required
              disabled={loading}
              helperText="Enter the 6-digit code from your authenticator app"
            />
          </div>

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
              variant="destructive"
              disabled={loading || !password || totpCode.length !== 6}
              className="flex-1"
            >
              {loading ? 'Disabling...' : 'Disable 2FA'}
            </AppleButton>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
