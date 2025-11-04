/**
 * PWA Install Prompt Component
 * Issue #774 - PWA Implementation
 * Feature Flag: OWNER_CONSOLE_PWA
 * 
 * Shows install prompt for PWA
 */
import React, { useState, useEffect } from 'react';
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui';
import { Download, X } from 'lucide-react';
import { isPWAInstallable, showInstallPrompt, isRunningAsPWA } from '../lib/pwa';

export const PWAInstallPrompt: React.FC = () => {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    if (isRunningAsPWA()) {
      return;
    }

    if (isPWAInstallable()) {
      setShowPrompt(true);
    }

    const handleInstallable = () => {
      setShowPrompt(true);
    };

    const handleInstalled = () => {
      setShowPrompt(false);
    };

    window.addEventListener('pwa-installable', handleInstallable);
    window.addEventListener('pwa-installed', handleInstalled);

    return () => {
      window.removeEventListener('pwa-installable', handleInstallable);
      window.removeEventListener('pwa-installed', handleInstalled);
    };
  }, []);

  const handleInstall = async () => {
    setIsInstalling(true);
    
    try {
      const result = await showInstallPrompt();
      
      if (result === 'accepted') {
        setShowPrompt(false);
      } else if (result === 'unavailable') {
        console.warn('Install prompt unavailable');
      }
    } catch (error) {
      console.error('Error installing PWA:', error);
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      const sevenDays = 7 * 24 * 60 * 60 * 1000;
      
      if (Date.now() - dismissedTime < sevenDays) {
        setShowPrompt(false);
      }
    }
  }, []);

  if (!showPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      <Card className="shadow-lg">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              <Download className="h-5 w-5 text-primary" />
              <CardTitle className="text-base">Install App</CardTitle>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={handleDismiss}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription className="text-sm">
            Install Morning AI for a better experience
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Faster loading times</li>
            <li>• Offline access</li>
            <li>• Push notifications</li>
            <li>• Native app experience</li>
          </ul>
          <Button
            onClick={handleInstall}
            disabled={isInstalling}
            className="w-full"
          >
            {isInstalling ? 'Installing...' : 'Install Now'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default PWAInstallPrompt;
