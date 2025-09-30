import React, { useState, useEffect } from 'react'
import { Calendar, CheckCircle, Sparkles, Play, Users, TrendingUp, Clock, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import mockData from '@/mocks/dashboard.json'

const Dashboard = () => {
  const [data, setData] = useState({
    todayFocus: [],
    aiAgents: [],
    projects: []
  })

  useEffect(() => {
    setData(mockData)
  }, [])

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low':
        return 'bg-green-100 text-green-700 border-green-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'task':
        return <CheckCircle className="w-5 h-5" />
      case 'meeting':
        return <Calendar className="w-5 h-5" />
      case 'ai-suggestion':
        return <Sparkles className="w-5 h-5" />
      case 'reminder':
        return <Clock className="w-5 h-5" />
      default:
        return <CheckCircle className="w-5 h-5" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-500'
      case 'idle':
        return 'bg-gray-400'
      case 'busy':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-400'
    }
  }

  const getProjectStatusColor = (status) => {
    switch (status) {
      case 'in-progress':
        return 'bg-blue-100 text-blue-700'
      case 'planning':
        return 'bg-purple-100 text-purple-700'
      case 'completed':
        return 'bg-green-100 text-green-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">早安，Ryan 👋</h1>
        <p className="text-gray-600">這是你今天的焦點和 AI 助手狀態</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-[var(--color-accent-orange-500)]" />
                今日焦點
              </CardTitle>
              <CardDescription>需要你關注的事項</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.todayFocus.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-lg border border-gray-200 hover:border-[var(--color-primary-500)] hover:shadow-md transition-all duration-[var(--duration-fast)] cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 text-[var(--color-primary-500)]">
                      {getTypeIcon(item.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 mb-1">{item.title}</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        {item.priority && (
                          <Badge variant="outline" className={getPriorityColor(item.priority)}>
                            {item.priority === 'high' && '高優先級'}
                            {item.priority === 'medium' && '中優先級'}
                            {item.priority === 'low' && '低優先級'}
                          </Badge>
                        )}
                        {item.dueTime && (
                          <span className="text-sm text-gray-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {item.dueTime}
                          </span>
                        )}
                        {item.time && (
                          <span className="text-sm text-gray-500 flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {item.time}
                          </span>
                        )}
                        {item.attendees && (
                          <span className="text-sm text-gray-500 flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {item.attendees} 人
                          </span>
                        )}
                        {item.confidence && (
                          <span className="text-sm text-[var(--color-accent-purple-500)] font-medium">
                            {Math.round(item.confidence * 100)}% 信心度
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {data.todayFocus.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Sparkles className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>太好了！今天沒有待辦事項</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[var(--color-accent-purple-500)]" />
                AI Agent 狀態
              </CardTitle>
              <CardDescription>你的 AI 助手們正在工作</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.aiAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="p-4 rounded-lg border border-gray-200 hover:border-[var(--color-primary-500)] hover:shadow-md transition-all duration-[var(--duration-fast)]"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{agent.avatar}</div>
                      <div>
                        <h4 className="font-medium text-gray-900">{agent.name}</h4>
                        <p className="text-sm text-gray-500">{agent.lastActivity}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                      <span className="text-sm text-gray-600">
                        {agent.status === 'active' ? '運行中' : '閒置'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-sm text-gray-600">已完成任務</span>
                    <span className="font-semibold text-[var(--color-primary-600)]">
                      {agent.tasksCompleted}
                    </span>
                  </div>
                </div>
              ))}
              <Button className="w-full bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] transition-colors duration-[var(--duration-fast)]">
                <Play className="w-4 h-4 mr-2" />
                啟動新的 Agent
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-[var(--color-primary-500)]" />
                專案看板
              </CardTitle>
              <CardDescription>你的專案進度一覽</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.projects.map((project) => (
                <div
                  key={project.id}
                  className="p-4 rounded-lg border border-gray-200 hover:border-[var(--color-primary-500)] hover:shadow-md transition-all duration-[var(--duration-fast)] cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 mb-1">{project.name}</h4>
                      <div className="flex items-center gap-2">
                        <Badge className={getProjectStatusColor(project.status)}>
                          {project.status === 'in-progress' && '進行中'}
                          {project.status === 'planning' && '規劃中'}
                          {project.status === 'completed' && '已完成'}
                        </Badge>
                        {project.aiCollaboration && (
                          <Badge variant="outline" className="border-[var(--color-accent-purple-500)] text-[var(--color-accent-purple-500)]">
                            <Sparkles className="w-3 h-3 mr-1" />
                            AI 協作
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">進度</span>
                      <span className="font-medium text-gray-900">{project.progress}%</span>
                    </div>
                    <Progress value={project.progress} className="h-2" />
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>{project.completedTasks} / {project.tasks} 任務完成</span>
                    </div>
                  </div>
                </div>
              ))}
              {data.projects.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <TrendingUp className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>還沒有專案，開始創建你的第一個專案吧</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

