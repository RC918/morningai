import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@morningai/shared-ui';

export function QRCodeDisplay({ qrCode, secret }) {
  const { t } = useTranslation();
  
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6 flex flex-col items-center space-y-4">
          <div className="bg-white p-4 rounded-lg">
            <img
              src={qrCode}
              alt={t('settings.2fa.setup.qrAlt')}
              className="w-64 h-64"
            />
          </div>
          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              {t('settings.2fa.setup.qrCodeDescription')}
            </p>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">
                {t('settings.2fa.setup.manualEntry')}
              </p>
              <code className="block px-3 py-2 bg-accent rounded-lg text-sm font-mono break-all">
                {secret}
              </code>
            </div>
          </div>
        </CardContent>
      </Card>
      <div className="text-xs text-muted-foreground space-y-1">
        <p className="font-medium">{t('settings.2fa.setup.recommendedApps')}</p>
        <ul className="list-disc list-inside space-y-0.5 ml-2">
          <li>{t('settings.2fa.setup.apps.google')}</li>
          <li>{t('settings.2fa.setup.apps.microsoft')}</li>
          <li>{t('settings.2fa.setup.apps.authy')}</li>
          <li>{t('settings.2fa.setup.apps.onepassword')}</li>
        </ul>
      </div>
    </div>
  );
}
