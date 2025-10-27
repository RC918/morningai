import React, { useState, useEffect } from 'react';
import { useTenant } from '../contexts/TenantContext';
import { AppleButton } from './ui/apple-button';

const TenantSettings = () => {
  const { tenant, loading: tenantLoading, error: tenantError } = useTenant();
  const [members, setMembers] = useState([]);
  const [tenantInfo, setTenantInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingMember, setUpdatingMember] = useState(null);

  useEffect(() => {
    fetchTenantData();
  }, []);

  const fetchTenantData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('Not authenticated');
        setLoading(false);
        return;
      }

      const [membersRes, infoRes] = await Promise.all([
        fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'}/api/tenant/members`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'}/api/tenant/info`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      if (!membersRes.ok || !infoRes.ok) {
        throw new Error('Failed to fetch tenant data');
      }

      const membersData = await membersRes.json();
      const infoData = await infoRes.json();

      setMembers(membersData.members || []);
      setTenantInfo(infoData);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching tenant data:', err);
      setError(err.message || 'Failed to load tenant data');
      setLoading(false);
    }
  };

  const updateMemberRole = async (memberId, newRole) => {
    try {
      setUpdatingMember(memberId);

      const token = localStorage.getItem('token');
      
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'}/api/tenant/members/${memberId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ role: newRole })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to update member role');
      }

      await fetchTenantData();
      setUpdatingMember(null);
    } catch (err) {
      console.error('Error updating member role:', err);
      alert(`Failed to update member: ${err.message}`);
      setUpdatingMember(null);
    }
  };

  if (tenantLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading tenant information...</p>
        </div>
      </div>
    );
  }

  if (tenantError || error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-semibold mb-2">Error Loading Tenant</h2>
          <p className="text-red-600">{tenantError || error}</p>
          <AppleButton
            onClick={fetchTenantData}
            variant="destructive"
            className="mt-4"
            aria-label="Retry loading tenant information"
          >
            Retry
          </AppleButton>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Tenant Settings</h1>
          <p className="text-gray-600 mt-2">Manage your organization and team members</p>
        </div>

        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <h2 className="text-xl font-semibold mb-4">Organization Information</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Organization Name</p>
              <p className="text-lg font-medium">{tenant?.name || 'N/A'}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">Organization ID</p>
              <p className="text-sm font-mono text-gray-700">{tenant?.id || 'N/A'}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">Total Members</p>
              <p className="text-lg font-medium">{tenantInfo?.member_count || 0}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">Total Tasks</p>
              <p className="text-lg font-medium">{tenantInfo?.task_count || 0}</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600">Created</p>
              <p className="text-sm text-gray-700">
                {tenant?.createdAt ? new Date(tenant.createdAt).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Team Members</h2>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" aria-label="Team members list">
              <caption className="sr-only">Team members with their roles and join dates</caption>
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Display Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Actions
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
                        aria-label={`Change role for ${member.email || member.display_name}`}
                      >
                        <option value="viewer">Viewer</option>
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                        <option value="owner">Owner</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {member.created_at ? new Date(member.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {updatingMember === member.id && (
                        <span className="text-blue-600">Updating...</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {members.length === 0 && (
              <div className="text-center py-8 text-gray-600">
                No members found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantSettings;
