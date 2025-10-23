import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Users, Plus, Settings } from 'lucide-react'

const TenantManagement = () => {
  const { t } = useTranslation()
  const mockTenants = [
    { id: 'tenant_001', name: 'Acme Corp', status: 'active', agents: 12, users: 5 },
    { id: 'tenant_002', name: 'TechStart Inc', status: 'active', agents: 8, users: 3 },
    { id: 'tenant_003', name: 'Global Solutions', status: 'suspended', agents: 0, users: 2 }
  ]

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

      <Card>
        <CardHeader>
          <CardTitle>{t('tenants.activeTenants')}</CardTitle>
          <CardDescription>{t('tenants.allTenants')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockTenants.map((tenant) => (
              <div key={tenant.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-semibold text-gray-900">{tenant.name}</p>
                  <p className="text-sm text-gray-600">ID: {tenant.id}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">{tenant.agents} {t('tenants.agents')}</p>
                    <p className="text-sm text-gray-600">{tenant.users} {t('tenants.users')}</p>
                  </div>
                  <Badge variant={tenant.status === 'active' ? 'default' : 'destructive'}>
                    {t(`tenants.${tenant.status}`)}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default TenantManagement
