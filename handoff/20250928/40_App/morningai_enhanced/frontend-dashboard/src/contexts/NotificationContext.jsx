import React, { createContext, useState, useEffect, useContext } from 'react';
import apiClient from '@/lib/api';

const NotificationContext = createContext();

export function NotificationProvider({ children }) {
  const [showPhase3Welcome, setShowPhase3Welcome] = useState(false);
  
  useEffect(() => {
    const checkWelcomeModal = async () => {
      try {
        const deploymentDateStr = import.meta.env.VITE_PHASE3_DEPLOYMENT_DATE || '2025-10-18T00:00:00Z';
        const deploymentDate = new Date(deploymentDateStr);
        
        const response = await apiClient.get('/user/preferences');
        const hasSeenWelcome = response?.data?.phase3_welcome_shown || false;
        
        const userProfile = await apiClient.get('/user/profile');
        const userCreatedAt = userProfile?.data?.created_at 
          ? new Date(userProfile.data.created_at) 
          : new Date();
        
        if (!hasSeenWelcome && userCreatedAt < deploymentDate) {
          setTimeout(() => {
            setShowPhase3Welcome(true);
          }, 1500);
        }
      } catch (error) {
        console.warn('Failed to check welcome modal status:', error);
        const hasSeenWelcomeLocal = localStorage.getItem('phase3_welcome_shown');
        if (!hasSeenWelcomeLocal) {
          setTimeout(() => {
            setShowPhase3Welcome(true);
          }, 1500);
        }
      }
    };
    
    checkWelcomeModal();
  }, []);
  
  const dismissWelcome = async () => {
    setShowPhase3Welcome(false);
    
    try {
      await apiClient.post('/user/preferences', {
        phase3_welcome_shown: true
      });
    } catch (error) {
      console.warn('Failed to save welcome modal status to backend:', error);
    }
    
    localStorage.setItem('phase3_welcome_shown', 'true');
  };
  
  return (
    <NotificationContext.Provider 
      value={{ 
        showPhase3Welcome, 
        dismissWelcome 
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}
