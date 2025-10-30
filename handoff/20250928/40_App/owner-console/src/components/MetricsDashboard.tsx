/**
 * Metrics Dashboard Component
 * Issue #762 - Metrics Dashboard
 * Feature Flag: MVP_METRICS_DASHBOARD
 * 
 * Displays real-time system metrics, agent performance, and alerts
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Zap,
  Database,
  Server,
  Users
} from 'lucide-react';

interface MetricValue {
  current: number;
  previous?: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
}

interface AlertItem {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
}

interface AgentMetrics {
  agent_id: string;
  agent_type: string;
  status: string;
  reputation_score: number;
  task_success_rate: number;
  active_tasks: number;
}

interface DashboardData {
  system_health: {
    overall_status: 'healthy' | 'degraded' | 'unhealthy';
    error_rate: number;
    avg_latency: number;
    open_circuit_breakers: number;
  };
  metrics: {
    api_request_rate: MetricValue;
    agent_task_success_rate: MetricValue;
    queue_depth: MetricValue;
    active_agents: MetricValue;
  };
  agents: AgentMetrics[];
  alerts: AlertItem[];
}

const MetricCard: React.FC<{
  title: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  icon: React.ReactNode;
  description?: string;
}> = ({ title, value, unit, trend, icon, description }) => {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="h-4 w-4 text-red-500" />;
    return null;
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value.toFixed(2)} {unit}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div className="flex items-center mt-2">
            {getTrendIcon()}
            <span className="text-xs text-muted-foreground ml-1">
              {trend === 'up' ? 'Increasing' : trend === 'down' ? 'Decreasing' : 'Stable'}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const AlertCard: React.FC<{ alert: AlertItem }> = ({ alert }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'warning': return 'default';
      case 'info': return 'secondary';
      default: return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertCircle className="h-4 w-4" />;
      case 'warning': return <AlertCircle className="h-4 w-4" />;
      case 'info': return <CheckCircle className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  return (
    <Alert variant={getSeverityColor(alert.severity) as any}>
      {getSeverityIcon(alert.severity)}
      <AlertTitle className="ml-2">
        <Badge variant={getSeverityColor(alert.severity) as any}>
          {alert.severity.toUpperCase()}
        </Badge>
      </AlertTitle>
      <AlertDescription className="ml-2 mt-2">
        {alert.message}
        <span className="text-xs text-muted-foreground block mt-1">
          {new Date(alert.timestamp).toLocaleString()}
        </span>
      </AlertDescription>
    </Alert>
  );
};

const AgentStatusCard: React.FC<{ agent: AgentMetrics }> = ({ agent }) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-green-500';
      case 'idle': return 'bg-blue-500';
      case 'busy': return 'bg-yellow-500';
      case 'offline': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">
            {agent.agent_type.replace('_', ' ').toUpperCase()}
          </CardTitle>
          <Badge className={getStatusColor(agent.status)}>
            {agent.status}
          </Badge>
        </div>
        <CardDescription className="text-xs">
          ID: {agent.agent_id.substring(0, 8)}...
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Reputation Score</span>
              <span className="font-medium">{agent.reputation_score}/999</span>
            </div>
            <Progress value={(agent.reputation_score / 999) * 100} />
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Success Rate</span>
              <span className="font-medium">{(agent.task_success_rate * 100).toFixed(1)}%</span>
            </div>
            <Progress value={agent.task_success_rate * 100} />
          </div>
          <div className="flex justify-between text-xs pt-2 border-t">
            <span>Active Tasks</span>
            <span className="font-medium">{agent.active_tasks}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const MetricsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        
        const mockData: DashboardData = {
          system_health: {
            overall_status: 'healthy',
            error_rate: 0.02,
            avg_latency: 0.15,
            open_circuit_breakers: 0
          },
          metrics: {
            api_request_rate: { current: 1250, unit: 'req/min', trend: 'up' },
            agent_task_success_rate: { current: 0.96, unit: '%', trend: 'stable' },
            queue_depth: { current: 12, unit: 'tasks', trend: 'down' },
            active_agents: { current: 5, unit: 'agents', trend: 'stable' }
          },
          agents: [
            {
              agent_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
              agent_type: 'dev_agent',
              status: 'active',
              reputation_score: 750,
              task_success_rate: 0.95,
              active_tasks: 3
            },
            {
              agent_id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
              agent_type: 'ops_agent',
              status: 'busy',
              reputation_score: 820,
              task_success_rate: 0.98,
              active_tasks: 5
            },
            {
              agent_id: 'c3d4e5f6-a7b8-9012-cdef-123456789012',
              agent_type: 'pm_agent',
              status: 'idle',
              reputation_score: 680,
              task_success_rate: 0.92,
              active_tasks: 0
            }
          ],
          alerts: [
            {
              id: '1',
              severity: 'warning',
              message: 'Queue depth elevated above normal levels',
              timestamp: new Date().toISOString()
            }
          ]
        };

        setDashboardData(mockData);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
        setLoading(false);
      }
    };

    fetchDashboardData();

    const interval = autoRefresh ? setInterval(fetchDashboardData, 30000) : null;

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!dashboardData) {
    return null;
  }

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'degraded': return 'text-yellow-500';
      case 'unhealthy': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Metrics Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time system performance and agent monitoring
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge 
            variant={dashboardData.system_health.overall_status === 'healthy' ? 'default' : 'destructive'}
            className={getHealthStatusColor(dashboardData.system_health.overall_status)}
          >
            <Activity className="h-3 w-3 mr-1" />
            {dashboardData.system_health.overall_status.toUpperCase()}
          </Badge>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Alerts */}
      {dashboardData.alerts.length > 0 && (
        <div className="space-y-2">
          {dashboardData.alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="API Request Rate"
          value={dashboardData.metrics.api_request_rate.current}
          unit={dashboardData.metrics.api_request_rate.unit}
          trend={dashboardData.metrics.api_request_rate.trend}
          icon={<Zap className="h-4 w-4 text-muted-foreground" />}
          description="Requests per minute"
        />
        <MetricCard
          title="Task Success Rate"
          value={dashboardData.metrics.agent_task_success_rate.current * 100}
          unit="%"
          trend={dashboardData.metrics.agent_task_success_rate.trend}
          icon={<CheckCircle className="h-4 w-4 text-muted-foreground" />}
          description="Agent task completion rate"
        />
        <MetricCard
          title="Queue Depth"
          value={dashboardData.metrics.queue_depth.current}
          unit={dashboardData.metrics.queue_depth.unit}
          trend={dashboardData.metrics.queue_depth.trend}
          icon={<Clock className="h-4 w-4 text-muted-foreground" />}
          description="Tasks waiting in queue"
        />
        <MetricCard
          title="Active Agents"
          value={dashboardData.metrics.active_agents.current}
          unit={dashboardData.metrics.active_agents.unit}
          trend={dashboardData.metrics.active_agents.trend}
          icon={<Users className="h-4 w-4 text-muted-foreground" />}
          description="Currently active agents"
        />
      </div>

      {/* Detailed Tabs */}
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {dashboardData.agents.map((agent) => (
              <AgentStatusCard key={agent.agent_id} agent={agent} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(dashboardData.system_health.error_rate * 100).toFixed(2)}%
                </div>
                <Progress 
                  value={dashboardData.system_health.error_rate * 100} 
                  className="mt-2"
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(dashboardData.system_health.avg_latency * 1000).toFixed(0)}ms
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Target: &lt; 1000ms
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Circuit Breakers</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData.system_health.open_circuit_breakers}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Open circuit breakers
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Detailed performance metrics and trends
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Performance charts and detailed metrics will be displayed here.
                Integration with monitoring backend in progress.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MetricsDashboard;
