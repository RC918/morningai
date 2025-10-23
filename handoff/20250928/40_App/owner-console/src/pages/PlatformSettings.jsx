import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Save } from 'lucide-react'

const PlatformSettings = () => {
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Settings className="w-8 h-8 text-gray-600" />
          Platform Settings
        </h1>
        <p className="text-gray-600 mt-1">Configure platform-wide settings and policies</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Platform-wide configuration options</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Platform Name</label>
            <input 
              type="text" 
              defaultValue="MorningAI Platform" 
              className="w-full mt-1 px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Support Email</label>
            <input 
              type="email" 
              defaultValue="support@morningai.com" 
              className="w-full mt-1 px-3 py-2 border rounded-lg"
            />
          </div>
          <Button>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security Policies</CardTitle>
          <CardDescription>Configure security and compliance settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Require MFA</p>
              <p className="text-sm text-gray-600">Enforce multi-factor authentication for all users</p>
            </div>
            <input type="checkbox" defaultChecked className="w-5 h-5" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Session Timeout</p>
              <p className="text-sm text-gray-600">Auto-logout after inactivity</p>
            </div>
            <select className="px-3 py-2 border rounded-lg">
              <option>30 minutes</option>
              <option>1 hour</option>
              <option>4 hours</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PlatformSettings
