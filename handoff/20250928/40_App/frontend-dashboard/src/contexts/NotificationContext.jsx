import React, { createContext, useState, useEffect, useContext } from 'react';

const NotificationContext = createContext();

export function NotificationProvider({ children }) {
  const [showPhase3Welcome, setShowPhase3Welcome] = useState(false);
  
  useEffect(() => {
    const hasSeenWelcome = localStorage.getItem('phase3_welcome_shown');
    const deploymentDate = new Date('2025-10-18T00:00:00Z');
    const lastLoginStr = localStorage.getItem('last_login');
    const userLastLogin = lastLoginStr ? new Date(lastLoginStr) : new Date(0);
    
    if (!hasSeenWelcome && userLastLogin < deploymentDate) {
      setTimeout(() => {
        setShowPhase3Welcome(true);
      }, 1000);
    }
    
    localStorage.setItem('last_login', new Date().toISOString());
  }, []);
  
  const dismissWelcome = () => {
    setShowPhase3Welcome(false);
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
