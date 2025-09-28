import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalAgents: 15,
    activeDecisions: 42,
    systemHealth: 98.5,
    dailyTasks: 156
  })

  const [recentActivity, setRecentActivity] = useState([
    { id: 1, type: 'decision', message: 'Meta-Agent processed strategic decision #1247', time: '2 minutes ago' },
    { id: 2, type: 'task', message: 'QA Agent completed testing suite validation', time: '5 minutes ago' },
    { id: 3, type: 'alert', message: 'System performance optimized by 12%', time: '8 minutes ago' },
    { id: 4, type: 'decision', message: 'CEO Agent approved budget allocation', time: '15 minutes ago' }
  ])

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
        const response = await fetch(`${apiUrl}/api/stats`)
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        }
      } catch (error) {
        console.log('Using fallback stats data')
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Morning AI Dashboard</h2>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total AI Agents</h3>
            <p className="text-3xl font-bold text-blue-600">{stats.totalAgents}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Decisions</h3>
            <p className="text-3xl font-bold text-green-600">{stats.activeDecisions}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">System Health</h3>
            <p className="text-3xl font-bold text-emerald-600">{stats.systemHealth}%</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Daily Tasks</h3>
            <p className="text-3xl font-bold text-purple-600">{stats.dailyTasks}</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-3 ${
                      activity.type === 'decision' ? 'bg-blue-500' :
                      activity.type === 'task' ? 'bg-green-500' : 'bg-yellow-500'
                    }`}></div>
                    <p className="text-sm text-gray-900">{activity.message}</p>
                  </div>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Deploy New Agent
          </button>
          <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
            Run System Check
          </button>
          <button className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors">
            View Analytics
          </button>
        </div>
      </div>
    </div>
  )
}
