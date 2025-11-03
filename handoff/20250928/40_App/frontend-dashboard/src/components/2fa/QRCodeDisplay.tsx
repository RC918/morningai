import React from 'react';
import { Card, CardContent } from '@morningai/shared-ui';

interface QRCodeDisplayProps {
  qrCode: string;
  secret: string;
}

export function QRCodeDisplay({ qrCode, secret }: QRCodeDisplayProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6 flex flex-col items-center space-y-4">
          <div className="bg-white p-4 rounded-lg">
            <img
              src={qrCode}
              alt="2FA QR Code"
              className="w-64 h-64"
            />
          </div>
          <div className="text-center space-y-2">
            <p className="text-sm text-muted-foreground">
              Scan this QR code with your authenticator app
            </p>
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">
                Or enter this code manually:
              </p>
              <code className="block px-3 py-2 bg-accent rounded-lg text-sm font-mono break-all">
                {secret}
              </code>
            </div>
          </div>
        </CardContent>
      </Card>
      <div className="text-xs text-muted-foreground space-y-1">
        <p className="font-medium">Recommended authenticator apps:</p>
        <ul className="list-disc list-inside space-y-0.5 ml-2">
          <li>Google Authenticator</li>
          <li>Microsoft Authenticator</li>
          <li>Authy</li>
          <li>1Password</li>
        </ul>
      </div>
    </div>
  );
}
