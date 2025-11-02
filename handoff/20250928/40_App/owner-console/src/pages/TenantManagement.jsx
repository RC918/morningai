import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Badge, Button, Alert, AlertDescription, AlertTitle } from '@morningai/shared-ui'
import { Users, Plus, Settings, AlertTriangle, Activity } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const TenantManagement = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tenants, setTenants] = useState([])

  useEffect(() => {
    loadTenants()
  }, [])

  const loadTenants = async () => {
    try {
      setLoading(true)
      setError(null)

      const [infoResponse, membersResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/tenant/info`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }),
        fetch(`${API_BASE_URL}/api/tenant/members`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        })
      ])

      if (!infoResponse.ok || !membersResponse.ok) {
        throw new Error('Failed to fetch tenant data')
      }

      const info = await infoResponse.json()
      const members = await membersResponse.json()

      const tenantsData = info.tenants || []
      const enrichedTenants = tenantsData.map(tenant => ({
        ...tenant,
        users: members.members?.filter(m => m.tenant_id === tenant.id)?.length || 0
      }))

      setTenants(enrichedTenants)
    } catch (error) {
      console.error('Failed to load tenants:', error)
      setError(error.message || 'Failed to load tenant data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Loading tenants...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="w-8 h-8 text-purple-600" />
            {t('tenants.title')}
          </h1>
          <p className="text-gray-600 mt-1">{t('tenants.subtitle')}</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          {t('tenants.addTenant')}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadTenants} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              {t('common.refresh')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t('tenants.activeTenants')}</CardTitle>
          <CardDescription>{t('tenants.allTenants')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tenants.length === 0 ? (
              <p className="text-center text-gray-500 py-8">{t('tenants.noTenants')}</p>
            ) : (
              tenants.map((tenant) => (
                <div key={tenant.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-semibold text-gray-900">{tenant.name}</p>
                    <p className="text-sm text-gray-600">ID: {tenant.id}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-600">{tenant.agents || 0} {t('tenants.agents')}</p>
                      <p className="text-sm text-gray-600">{tenant.users || 0} {t('tenants.users')}</p>
                    </div>
                    <Badge variant={tenant.status === 'active' ? 'default' : 'destructive'}>
                      {t(`tenants.${tenant.status}`)}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      <Settings className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default TenantManagement
