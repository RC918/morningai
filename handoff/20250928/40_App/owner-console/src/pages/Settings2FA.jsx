import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TwoFAStatusCard } from '../components/2fa/TwoFAStatusCard';
import { TwoFASetupWizard } from '../components/2fa/TwoFASetupWizard';
import { DisableTwoFAModal } from '../components/2fa/DisableTwoFAModal';
import { RegenerateBackupCodesModal } from '../components/2fa/RegenerateBackupCodesModal';

export default function Settings2FA() {
  const { t } = useTranslation();
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleSetupComplete = () => {
    setShowSetupWizard(false);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDisableSuccess = () => {
    setShowDisableModal(false);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleRegenerateSuccess = () => {
    setShowRegenerateModal(false);
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">{t('settings.2fa.title')}</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          {t('settings.2fa.subtitle')}
        </p>
      </div>

      {showSetupWizard ? (
        <TwoFASetupWizard
          onComplete={handleSetupComplete}
          onCancel={() => setShowSetupWizard(false)}
        />
      ) : (
        <TwoFAStatusCard
          onSetupClick={() => setShowSetupWizard(true)}
          onDisableClick={() => setShowDisableModal(true)}
          onRegenerateClick={() => setShowRegenerateModal(true)}
          refreshTrigger={refreshTrigger}
        />
      )}

      <DisableTwoFAModal
        open={showDisableModal}
        onClose={() => setShowDisableModal(false)}
        onSuccess={handleDisableSuccess}
      />

      <RegenerateBackupCodesModal
        open={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        onSuccess={handleRegenerateSuccess}
      />
    </div>
  );
}
