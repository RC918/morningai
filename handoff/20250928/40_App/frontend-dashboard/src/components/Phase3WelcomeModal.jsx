import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Users, Shield, UserCog } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function Phase3WelcomeModal({ isOpen, onClose }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const handleGoToSettings = () => {
    onClose();
    navigate('/tenant-settings');
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-2xl">{t('phase3Welcome.title')}</DialogTitle>
          <DialogDescription className="text-base font-semibold text-gray-900 pt-2">
            {t('phase3Welcome.subtitle')}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="flex items-start gap-3">
            <Users className="w-6 h-6 text-blue-500 mt-1" />
            <div className="space-y-1">
              <p className="font-semibold text-gray-900">{t('phase3Welcome.teamManagement.title')}</p>
              <p className="text-sm text-gray-600">
                {t('phase3Welcome.teamManagement.description')}
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <Shield className="w-6 h-6 text-green-500 mt-1" />
            <div className="space-y-1">
              <p className="font-semibold text-gray-900">{t('phase3Welcome.enhancedSecurity.title')}</p>
              <p className="text-sm text-gray-600">
                {t('phase3Welcome.enhancedSecurity.description')}
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <UserCog className="w-6 h-6 text-purple-500 mt-1" />
            <div className="space-y-1">
              <p className="font-semibold text-gray-900">{t('phase3Welcome.rolePermissions.title')}</p>
              <p className="text-sm text-gray-600">
                {t('phase3Welcome.rolePermissions.description')}
              </p>
            </div>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
            <p className="text-sm text-blue-900">
              {t('phase3Welcome.migrationNotice')}
            </p>
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            {t('phase3Welcome.laterButton')}
          </Button>
          <Button onClick={handleGoToSettings}>
            {t('phase3Welcome.settingsButton')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
