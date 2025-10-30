/**
 * Offline Indicator Component
 * Issue #774 - PWA Implementation
 * Feature Flag: OWNER_CONSOLE_PWA
 * 
 * Shows offline/online status
 */
import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription } from './ui/alert';
import { WifiOff, Wifi } from 'lucide-react';
import { isOffline, onConnectionChange } from '../lib/pwa';

export const OfflineIndicator: React.FC = () => {
  const [offline, setOffline] = useState(isOffline());
  const [showOnlineMessage, setShowOnlineMessage] = useState(false);

  useEffect(() => {
    const cleanup = onConnectionChange((isOnline) => {
      setOffline(!isOnline);
      
      if (isOnline && offline) {
        setShowOnlineMessage(true);
        setTimeout(() => setShowOnlineMessage(false), 3000);
      }
    });

    return cleanup;
  }, [offline]);

  if (!offline && !showOnlineMessage) {
    return null;
  }

  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-md">
      <Alert variant={offline ? 'destructive' : 'default'}>
        {offline ? (
          <>
            <WifiOff className="h-4 w-4" />
            <AlertDescription className="ml-2">
              You're offline. Some features may be limited.
            </AlertDescription>
          </>
        ) : (
          <>
            <Wifi className="h-4 w-4" />
            <AlertDescription className="ml-2">
              You're back online!
            </AlertDescription>
          </>
        )}
      </Alert>
    </div>
  );
};

export default OfflineIndicator;
