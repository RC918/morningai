import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { Button } from '@morningai/shared-ui';
import { AlertCircle, Copy, Download, CheckCircle2 } from 'lucide-react';

export function BackupCodesList({ backupCodes, onContinue }) {
  const { t } = useTranslation();
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
      <Card className="border-warning-200 dark:border-warning-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-warning-800 dark:text-warning-200">
            <AlertCircle className="w-5 h-5" />
            {t('settings.2fa.backupCodes.saveTitle')}
          </CardTitle>
          <CardDescription>
            {t('settings.2fa.backupCodes.saveDescription')}
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
            <Button
              onClick={handleCopy}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  {t('settings.2fa.backupCodes.copied')}
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  {t('settings.2fa.backupCodes.copyAll')}
                </>
              )}
            </Button>
            <Button
              onClick={handleDownload}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              <Download className="w-4 h-4" />
              {t('settings.2fa.backupCodes.download')}
            </Button>
          </div>

          <div className="p-3 bg-warning-50 dark:bg-warning-900/20 rounded-lg">
            <p className="text-xs text-warning-800 dark:text-warning-200">
              <strong>{t('settings.2fa.backupCodes.important')}</strong> {t('settings.2fa.backupCodes.warningMessage')}
            </p>
          </div>

          {onContinue && (
            <Button onClick={onContinue} className="w-full">
              {t('settings.2fa.backupCodes.confirmSaved')}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
