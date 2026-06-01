'use client';
import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  Card, Col, Row, Typography, Select, Space, Button, Spin, message, Tabs, DatePicker,
} from 'antd';
import {
  ReloadOutlined, DownloadOutlined, DashboardOutlined,
  NodeIndexOutlined, WarningOutlined, LineChartOutlined,
  AlertOutlined, ApartmentOutlined,
} from '@ant-design/icons';
import MetricsOverview from '@/components/observability/MetricsOverview';
import RequestTraces from '@/components/observability/RequestTraces';
import ErrorAnalysis from '@/components/observability/ErrorAnalysis';
import PerformanceCharts from '@/components/observability/PerformanceCharts';
import AlertRules from '@/components/observability/AlertRules';
import ServiceMap from '@/components/observability/ServiceMap';
import api from '@/lib/api';
import type { Dayjs } from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;

export type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d' | 'custom';

export interface TimeRangeValue {
  range: TimeRange;
  start?: string;
  end?: string;
}

export interface MetricsData {
  qps: number;
  qps_trend: number;
  avg_latency: number;
  latency_trend: number;
  error_rate: number;
  error_trend: number;
  total_requests: number;
  active_services: number;
  p50: number;
  p90: number;
  p99: number;
  qps_series: { time: string; value: number }[];
  latency_series: { time: string; value: number }[];
  error_series: { time: string; value: number }[];
}

export interface TraceSpan {
  trace_id: string;
  span_id: string;
  parent_span_id?: string;
  service: string;
  operation: string;
  start_time: string;
  duration: number;
  status: 'ok' | 'error' | 'timeout';
  tags?: Record<string, string>;
}

export interface Trace {
  trace_id: string;
  root_service: string;
  root_operation: string;
  start_time: string;
  total_duration: number;
  span_count: number;
  status: 'ok' | 'error' | 'timeout';
  spans: TraceSpan[];
}

export interface ErrorItem {
  id: string;
  service: string;
  error_type: string;
  message: string;
  count: number;
  first_seen: string;
  last_seen: string;
  trend: { time: string; count: number }[];
}

export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: number;
  duration: string;
  severity: 'critical' | 'warning' | 'info';
  enabled: boolean;
  notify_channels: string[];
  last_triggered?: string;
}

export interface ServiceNode {
  id: string;
  name: string;
  type: string;
  status: 'healthy' | 'degraded' | 'down';
  qps: number;
  error_rate: number;
  avg_latency: number;
}

export interface ServiceEdge {
  source: string;
  target: string;
  qps: number;
  error_rate: number;
  avg_latency: number;
}

export interface ServiceMapData {
  nodes: ServiceNode[];
  edges: ServiceEdge[];
}

export default function ObservabilityPage() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<TimeRange>('1h');
  const [activeTab, setActiveTab] = useState('overview');
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [errors, setErrors] = useState<ErrorItem[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [serviceMap, setServiceMap] = useState<ServiceMapData | null>(null);
  const refreshTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const getTimeRangeParams = useCallback((): TimeRangeValue => {
    return { range: timeRange };
  }, [timeRange]);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    const params = getTimeRangeParams();
    try {
      const [metricsRes, tracesRes, errorsRes, alertsRes, mapRes] = await Promise.allSettled([
        api.get('/observability/metrics', { params }),
        api.get('/observability/traces', { params: { ...params, limit: 50 } }),
        api.get('/observability/errors', { params }),
        api.get('/observability/alerts'),
        api.get('/observability/service-map'),
      ]);
      if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value);
      if (tracesRes.status === 'fulfilled') {
        const data = tracesRes.value;
        setTraces(Array.isArray(data) ? data : data?.items ?? []);
      }
      if (errorsRes.status === 'fulfilled') {
        const data = errorsRes.value;
        setErrors(Array.isArray(data) ? data : data?.items ?? []);
      }
      if (alertsRes.status === 'fulfilled') {
        const data = alertsRes.value;
        setAlertRules(Array.isArray(data) ? data : data?.items ?? []);
      }
      if (mapRes.status === 'fulfilled') setServiceMap(mapRes.value);
    } catch {
      message.error('Failed to load observability data');
    } finally {
      setLoading(false);
    }
  }, [getTimeRangeParams]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Auto-refresh every 15 seconds for live tab
  useEffect(() => {
    if (activeTab === 'overview' || activeTab === 'performance') {
      refreshTimerRef.current = setInterval(fetchAllData, 15000);
    }
    return () => {
      if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
    };
  }, [activeTab, fetchAllData]);

  const handleExport = async () => {
    try {
      const params = getTimeRangeParams();
      const blob: Blob = await api.get('/observability/export', {
        params,
        responseType: 'blob',
      } as any);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `observability-report-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('Report exported');
    } catch {
      message.error('Export failed');
    }
  };

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span><DashboardOutlined /> Overview</span>
      ),
      children: (
        <MetricsOverview
          metrics={metrics}
          loading={loading}
          timeRange={timeRange}
        />
      ),
    },
    {
      key: 'performance',
      label: (
        <span><LineChartOutlined /> Performance</span>
      ),
      children: (
        <PerformanceCharts
          metrics={metrics}
          loading={loading}
        />
      ),
    },
    {
      key: 'traces',
      label: (
        <span><NodeIndexOutlined /> Traces</span>
      ),
      children: (
        <RequestTraces
          traces={traces}
          loading={loading}
          timeRange={timeRange}
        />
      ),
    },
    {
      key: 'errors',
      label: (
        <span><WarningOutlined /> Errors</span>
      ),
      children: (
        <ErrorAnalysis
          errors={errors}
          loading={loading}
        />
      ),
    },
    {
      key: 'alerts',
      label: (
        <span><AlertOutlined /> Alerts</span>
      ),
      children: (
        <AlertRules
          rules={alertRules}
          loading={loading}
          onRefresh={fetchAllData}
        />
      ),
    },
    {
      key: 'service-map',
      label: (
        <span><ApartmentOutlined /> Service Map</span>
      ),
      children: (
        <ServiceMap
          data={serviceMap}
          loading={loading}
        />
      ),
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>Observability</Title>
        </Col>
        <Col>
          <Space>
            <Select<TimeRange>
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 140 }}
              options={[
                { value: '1h', label: 'Last 1 hour' },
                { value: '6h', label: 'Last 6 hours' },
                { value: '24h', label: 'Last 24 hours' },
                { value: '7d', label: 'Last 7 days' },
                { value: '30d', label: 'Last 30 days' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchAllData} loading={loading}>
              Refresh
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              Export
            </Button>
          </Space>
        </Col>
      </Row>

      <Card bordered={false} bodyStyle={{ padding: 0 }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{ padding: '0 24px' }}
          tabBarStyle={{ marginBottom: 0 }}
        />
      </Card>
    </div>
  );
}
