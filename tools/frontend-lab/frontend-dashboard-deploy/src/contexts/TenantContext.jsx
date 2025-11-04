import React, { createContext, useContext, useState, useEffect } from 'react';

const TenantContext = createContext(null);

export const TenantProvider = ({ children }) => {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTenantInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'}/api/tenant/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          setError('Tenant information not found. Please contact support.');
        } else {
          throw new Error('Failed to fetch tenant information');
        }
        setLoading(false);
        return;
      }

      const data = await response.json();
      
      setTenant({
        id: data.tenant_id,
        name: data.tenant_name,
        createdAt: data.created_at
      });

      setLoading(false);
    } catch (err) {
      console.error('Error fetching tenant info:', err);
      setError(err.message || 'Failed to load tenant information');
      setLoading(false);
    }
  };

  const refreshTenant = () => {
    fetchTenantInfo();
  };

  useEffect(() => {
    fetchTenantInfo();
  }, []);

  const value = {
    tenant,
    loading,
    error,
    refreshTenant
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => {
  const context = useContext(TenantContext);
  
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  
  return context;
};
