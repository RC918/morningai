import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useTenant } from '../contexts/TenantContext';
import { AppleButton } from './ui/apple-button';
import { apiClient } from '../lib/api-client';

interface Member {
  id: string
  email?: string
  display_name?: string
  role: string
  created_at?: string
}

interface TenantInfo {
  member_count?: number
  task_count?: number
}

interface ApiErrorResponse {
  error?: {
    message?: string
  }
}

const TenantSettings = (): React.ReactElement => {
  const { t } = useTranslation();
  const { tenant, loading: tenantLoading, error: tenantError } = useTenant();
  const [members, setMembers] = useState<Member[]>([]);
  const [tenantInfo, setTenantInfo] = useState<TenantInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingMember, setUpdatingMember] = useState<string | null>(null);

  useEffect(() => {
    fetchTenantData();
  }, []);

  const fetchTenantData = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      const [membersData, infoData] = await Promise.all([
        apiClient<{ members?: Member[] }>('/api/tenant/members', {
          method: 'GET'
        }),
        apiClient<TenantInfo>('/api/tenant/info', {
          method: 'GET'
        })
      ]);

      setMembers(membersData.members || []);
      setTenantInfo(infoData);
      setLoading(false);
    } catch (err: unknown) {
      console.error('Error fetching tenant data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load tenant data');
      setLoading(false);
    }
  };

  const updateMemberRole = async (memberId: string, newRole: string): Promise<void> => {
    try {
      setUpdatingMember(memberId);

      await apiClient(`/api/tenant/members/${memberId}`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole })
      });

      await fetchTenantData();
      setUpdatingMember(null);
    } catch (err: unknown) {
      console.error('Error updating member role:', err);
      alert(`Failed to update member: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setUpdatingMember(null);
    }
  };

  if (tenantLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">{t('tenant.loading')}</p>
        </div>
      </div>
    );
  }

  if (tenantError || error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-error-50 border border-error-200 rounded-lg p-6 max-w-md">
          <h2 className="text-error-800 font-semibold mb-2">{t('tenant.errorTitle')}</h2>
          <p className="text-error-600">{tenantError || error}</p>
          <AppleButton
            onClick={fetchTenantData}
            variant="destructive"
            className="mt-4"
            aria-label={t('tenant.retryAriaLabel')}
          >
            {t('tenant.retry')}
          </AppleButton>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t('tenant.title')}</h1>
          <p className="text-gray-600 mt-2">{t('tenant.description')}</p>
        </div>

        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <h2 className="text-xl font-semibold mb-4">{t('tenant.organization.title')}</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">{t('tenant.organization.name')}</p>
              <p className="text-lg font-medium">{tenant?.name || 'N/A'}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">{t('tenant.organization.id')}</p>
              <p className="text-sm font-mono text-gray-700">{tenant?.id || 'N/A'}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">{t('tenant.organization.totalMembers')}</p>
              <p className="text-lg font-medium">{tenantInfo?.member_count || 0}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">{t('tenant.organization.totalTasks')}</p>
              <p className="text-lg font-medium">{tenantInfo?.task_count || 0}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">{t('tenant.organization.created')}</p>
              <p className="text-sm text-gray-700">
                {tenant?.createdAt ? new Date(tenant.createdAt).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">{t('tenant.members.title')}</h2>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" aria-label={t('tenant.members.title')}>
              <caption className="sr-only">{t('tenant.members.tableCaption')}</caption>
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('tenant.members.email')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('tenant.members.displayName')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('tenant.members.role')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('tenant.members.joined')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    {t('tenant.members.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {members.map((member) => (
                  <tr key={member.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {member.email || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {member.display_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={member.role}
                        onChange={(e) => updateMemberRole(member.id, e.target.value)}
                        disabled={updatingMember === member.id}
                        className="text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        aria-label={t('tenant.members.changeRoleAriaLabel', { email: member.email || member.display_name })}
                      >
                        <option value="viewer">{t('tenant.members.roles.viewer')}</option>
                        <option value="member">{t('tenant.members.roles.member')}</option>
                        <option value="admin">{t('tenant.members.roles.admin')}</option>
                        <option value="owner">{t('tenant.members.roles.owner')}</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {member.created_at ? new Date(member.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {updatingMember === member.id && (
                        <span className="text-blue-600">{t('tenant.members.updating')}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {members.length === 0 && (
              <div className="text-center py-8 text-gray-600">
                {t('tenant.members.noMembers')}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantSettings;
