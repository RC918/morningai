import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { AppleButton } from '@/components/ui/apple-button';
import { Smartphone, Monitor, Tablet, Trash2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * TrustedDevices Component
 * 
 * Displays and manages trusted devices for "Remember this device" functionality.
 * Features:
 * - List of trusted devices with device info
 * - Device type icons (mobile, tablet, desktop)
 * - Last used timestamp
 * - Expiration date
 * - Revoke device functionality
 * - Empty state when no devices
 */
export function TrustedDevices({ className }) {
  const { t } = useTranslation();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [revokingId, setRevokingId] = useState(null);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      setLoading(true);
      setError(null);
      
      setDevices([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trusted devices');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (deviceId) => {
    try {
      setRevokingId(deviceId);
      
      setDevices(devices.filter(d => d.id !== deviceId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke device');
    } finally {
      setRevokingId(null);
    }
  };

  const getDeviceIcon = (deviceName) => {
    const name = deviceName.toLowerCase();
    if (name.includes('mobile') || name.includes('phone')) {
      return <Smartphone className="w-5 h-5" />;
    } else if (name.includes('tablet') || name.includes('ipad')) {
      return <Tablet className="w-5 h-5" />;
    } else {
      return <Monitor className="w-5 h-5" />;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('default', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const isExpiringSoon = (expiresAt) => {
    const expires = new Date(expiresAt);
    const now = new Date();
    const daysUntilExpiry = Math.ceil((expires.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 7;
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{t('settings.2fa.trustedDevices.title')}</CardTitle>
          <CardDescription>
            {t('settings.2fa.trustedDevices.description')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{t('settings.2fa.trustedDevices.title')}</CardTitle>
        <CardDescription>
          {t('settings.2fa.trustedDevices.description')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {devices.length === 0 ? (
          <div className="text-center py-8">
            <Monitor className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">
              {t('settings.2fa.trustedDevices.noDevices')}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {t('settings.2fa.trustedDevices.noDevicesHelp')}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {devices.map((device) => (
              <div
                key={device.id}
                className="flex items-start gap-3 p-4 rounded-lg border border-input bg-background/50 hover:bg-accent/50 transition-colors"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  {getDeviceIcon(device.device_name)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-medium text-foreground">
                        {device.device_name}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {t('settings.2fa.trustedDevices.lastUsed')}: {formatDate(device.last_used_at)}
                      </p>
                      <p className={cn(
                        'text-xs mt-0.5',
                        isExpiringSoon(device.expires_at)
                          ? 'text-yellow-600 dark:text-yellow-500'
                          : 'text-muted-foreground'
                      )}>
                        {t('settings.2fa.trustedDevices.expires')}: {formatDate(device.expires_at)}
                        {isExpiringSoon(device.expires_at) && (
                          <span className="ml-1">
                            ({t('settings.2fa.trustedDevices.expiringSoon')})
                          </span>
                        )}
                      </p>
                    </div>
                    
                    <AppleButton
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRevoke(device.id)}
                      disabled={revokingId === device.id}
                      className="flex-shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </AppleButton>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {devices.length > 0 && (
          <div className="mt-4 p-3 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground">
              {t('settings.2fa.trustedDevices.note')}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
