import React from 'react';
import { http, HttpResponse } from 'msw';
import SystemMonitoring from './SystemMonitoring';

export default {
  title: 'Pages/SystemMonitoring',
  component: SystemMonitoring,
  parameters: {
    layout: 'fullscreen',
  },
};

export const Loading = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', async () => {
          await new Promise(resolve => setTimeout(resolve, 10000));
          return HttpResponse.json({});
        }),
      ],
    },
  },
};

export const EmptyHealthData = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', () => {
          return HttpResponse.json(null);
        }),
        http.get('/api/admin/system-metrics', () => {
          return HttpResponse.json({
            cpu: { usage_percent: 45, count: 4 },
            memory: { usage_percent: 62, used_gb: 6.2, total_gb: 10 },
            disk: { usage_percent: 38, used_gb: 38, total_gb: 100 }
          });
        }),
      ],
    },
  },
};

export const EmptyMetricsData = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', () => {
          return HttpResponse.json({
            status: 'healthy',
            uptime_hours: 72,
            services: {
              database: 'healthy',
              redis: 'healthy',
              queue: 'healthy'
            }
          });
        }),
        http.get('/api/admin/system-metrics', () => {
          return HttpResponse.json(null);
        }),
      ],
    },
  },
};

export const HealthySystem = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', () => {
          return HttpResponse.json({
            status: 'healthy',
            uptime_hours: 168,
            services: {
              database: 'healthy',
              redis: 'healthy',
              queue: 'healthy',
              api: 'healthy'
            }
          });
        }),
        http.get('/api/admin/system-metrics', () => {
          return HttpResponse.json({
            cpu: { usage_percent: 35, count: 8 },
            memory: { usage_percent: 58, used_gb: 11.6, total_gb: 20 },
            disk: { usage_percent: 42, used_gb: 420, total_gb: 1000 }
          });
        }),
      ],
    },
  },
};

export const DegradedSystem = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', () => {
          return HttpResponse.json({
            status: 'degraded',
            uptime_hours: 24,
            services: {
              database: 'healthy',
              redis: 'degraded',
              queue: 'healthy',
              api: 'healthy'
            }
          });
        }),
        http.get('/api/admin/system-metrics', () => {
          return HttpResponse.json({
            cpu: { usage_percent: 78, count: 8 },
            memory: { usage_percent: 85, used_gb: 17, total_gb: 20 },
            disk: { usage_percent: 72, used_gb: 720, total_gb: 1000 }
          });
        }),
      ],
    },
  },
};

export const UnhealthySystem = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', () => {
          return HttpResponse.json({
            status: 'unhealthy',
            uptime_hours: 2,
            services: {
              database: 'unhealthy',
              redis: 'degraded',
              queue: 'unhealthy',
              api: 'degraded'
            }
          });
        }),
        http.get('/api/admin/system-metrics', () => {
          return HttpResponse.json({
            cpu: { usage_percent: 95, count: 8 },
            memory: { usage_percent: 98, used_gb: 19.6, total_gb: 20 },
            disk: { usage_percent: 92, used_gb: 920, total_gb: 1000 }
          });
        }),
      ],
    },
  },
};

export const ErrorState = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/admin/system-health', () => {
          return HttpResponse.json(
            { error: 'Failed to fetch system health' },
            { status: 500 }
          );
        }),
        http.get('/api/admin/system-metrics', () => {
          return HttpResponse.json(
            { error: 'Failed to fetch system metrics' },
            { status: 500 }
          );
        }),
      ],
    },
  },
};
