import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { AppleButton } from '@/components/ui/apple-button';
import { AlertCircle, Copy, Download, CheckCircle2 } from 'lucide-react';

interface BackupCodesListProps {
  backupCodes: string[];
  onContinue?: () => void;
}

export function BackupCodesList({ backupCodes, onContinue }: BackupCodesListProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(backupCodes.join('\n'));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy backup codes:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([backupCodes.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `2fa-backup-codes-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <Card className="border-yellow-200 dark:border-yellow-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
            <AlertCircle className="w-5 h-5" />
            Save Your Backup Codes
          </CardTitle>
          <CardDescription>
            Store these codes in a safe place. Each code can only be used once.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-2 p-4 bg-accent rounded-lg font-mono text-sm">
            {backupCodes.map((code, index) => (
              <div
                key={index}
                className="px-3 py-2 bg-background rounded border border-border"
              >
                {code}
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <AppleButton
              onClick={handleCopy}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy All
                </>
              )}
            </AppleButton>
            <AppleButton
              onClick={handleDownload}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              <Download className="w-4 h-4" />
              Download
            </AppleButton>
          </div>

          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <p className="text-xs text-yellow-800 dark:text-yellow-200">
              <strong>Important:</strong> These codes will not be shown again. Make sure to save them before continuing.
            </p>
          </div>

          {onContinue && (
            <AppleButton onClick={onContinue} className="w-full">
              I've Saved My Backup Codes
            </AppleButton>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
