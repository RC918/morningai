import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Badge, Button } from '@morningai/shared-ui'
import { Users, Plus, Settings, Activity } from 'lucide-react'
import { getTenantInfo, getTenantMembers } from '@/lib/generated/tenant/tenant'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'

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
        getTenantInfo(),
        getTenantMembers()
      ])

      if (infoResponse.status === 200 && membersResponse.status === 200) {
        const tenantInfo = infoResponse.data
        const members = membersResponse.data.members || []
        
        const enrichedTenant = {
          id: tenantInfo.tenant_id,
          name: tenantInfo.tenant_name,
          agents: 0,
          users: members.length,
          status: 'active'
        }

        setTenants([enrichedTenant])
      } else {
        throw new Error('Failed to load tenant data')
      }
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
          <h1 className="text-large-title font-bold text-neutral-900 dark:text-white flex items-center gap-3">
            <Users className="w-8 h-8 text-accent-600" />
            {t('tenants.title')}
          </h1>
          <p className="text-body text-neutral-600 dark:text-neutral-400 mt-1">{t('tenants.subtitle')}</p>
        </div>
        <AppleButton variant="primary" haptic="medium">
          <Plus className="w-4 h-4 mr-2" />
          {t('tenants.addTenant')}
        </AppleButton>
      </div>

      {error && (
        <AppleErrorBanner
          title={t('common.error')}
          message={error}
          onRetry={loadTenants}
        />
      )}

      <Card className="material-card hover-lift">
        <CardHeader>
          <CardTitle>{t('tenants.activeTenants')}</CardTitle>
          <CardDescription>{t('tenants.allTenants')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tenants.length === 0 ? (
              <p className="text-center text-neutral-500 dark:text-neutral-400 py-8">{t('tenants.noTenants')}</p>
            ) : (
              tenants.map((tenant) => (
                <div key={tenant.id} className="material-card flex items-center justify-between p-4">
                  <div>
                    <p className="text-callout font-semibold text-neutral-900 dark:text-white">{tenant.name}</p>
                    <p className="text-footnote text-neutral-600 dark:text-neutral-400">{t('common.idShort', { id: tenant.id })}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-footnote text-neutral-600 dark:text-neutral-400">{tenant.agents || 0} {t('tenants.agents')}</p>
                      <p className="text-footnote text-neutral-600 dark:text-neutral-400">{tenant.users || 0} {t('tenants.users')}</p>
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
