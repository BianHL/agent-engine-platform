'use client';
import React from 'react';
import { Card, Col, Row, Statistic, Skeleton, Typography, Space, Tag } from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, ThunderboltOutlined,
  FieldTimeOutlined, BugOutlined, ApiOutlined, ClusterOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { MetricsData, TimeRange } from '@/app/(platform)/observability/page';

const { Text } = Typography;

interface Props {
  metrics: MetricsData | null;
  loading: boolean;
  timeRange: TimeRange;
}

function TrendTag({ value }: { value: number }) {
  if (value === 0) return <Tag>0%</Tag>;
  const isUp = value > 0;
  return (
    <Tag color={isUp ? 'green' : 'red'} style={{ marginLeft: 8 }}>
      {isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />} {Math.abs(value).toFixed(1)}%
    </Tag>
  );
}

export default function MetricsOverview({ metrics, loading }: Props) {
  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Row gutter={[16, 16]}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Col xs={24} sm={12} lg={4} key={i}>
              <Card bordered={false}>
                <Skeleton active paragraph={{ rows: 1 }} />
              </Card>
            </Col>
          ))}
          {[1, 2].map((i) => (
            <Col xs={24} lg={12} key={i}>
              <Card bordered={false}>
                <Skeleton active paragraph={{ rows: 4 }} />
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>
        No metrics data available
      </div>
    );
  }

  const qpsChartOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category' as const,
      data: (metrics.qps_series || []).map((p) => p.time),
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'QPS',
      axisLabel: { fontSize: 11 },
    },
    series: [
      {
        type: 'line',
        data: (metrics.qps_series || []).map((p) => p.value),
        smooth: true,
        areaStyle: { opacity: 0.2, color: '#1890ff' },
        itemStyle: { color: '#1890ff' },
        lineStyle: { width: 2 },
        showSymbol: false,
      },
    ],
  };

  const latencyChartOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category' as const,
      data: (metrics.latency_series || []).map((p) => p.time),
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'ms',
      axisLabel: { fontSize: 11 },
    },
    series: [
      {
        type: 'line',
        data: (metrics.latency_series || []).map((p) => p.value),
        smooth: true,
        areaStyle: { opacity: 0.2, color: '#faad14' },
        itemStyle: { color: '#faad14' },
        lineStyle: { width: 2 },
        showSymbol: false,
      },
    ],
  };

  return (
    <div style={{ padding: 24 }}>
      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Statistic
              title="QPS"
              value={metrics.qps}
              precision={1}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix={<TrendTag value={metrics.qps_trend} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Statistic
              title="Avg Latency"
              value={metrics.avg_latency}
              precision={0}
              prefix={<FieldTimeOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix={
                <>
                  <span style={{ fontSize: 14, color: '#999' }}>ms</span>
                  <TrendTag value={metrics.latency_trend} />
                </>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Statistic
              title="Error Rate"
              value={metrics.error_rate}
              precision={2}
              prefix={<BugOutlined />}
              valueStyle={{ color: metrics.error_rate > 5 ? '#ff4d4f' : '#52c41a' }}
              suffix={
                <>
                  <span style={{ fontSize: 14, color: '#999' }}>%</span>
                  <TrendTag value={metrics.error_trend} />
                </>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Statistic
              title="Total Requests"
              value={metrics.total_requests}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#722ed1' }}
              formatter={(val) => {
                const n = Number(val);
                if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
                if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
                return String(n);
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Statistic
              title="Active Services"
              value={metrics.active_services}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              <Text type="secondary" style={{ fontSize: 14 }}>Latency Percentiles</Text>
              <Space size="middle" wrap>
                <div>
                  <Text type="secondary" style={{ fontSize: 11 }}>P50</Text>
                  <div style={{ fontWeight: 600, color: '#52c41a' }}>{metrics.p50}ms</div>
                </div>
                <div>
                  <Text type="secondary" style={{ fontSize: 11 }}>P90</Text>
                  <div style={{ fontWeight: 600, color: '#faad14' }}>{metrics.p90}ms</div>
                </div>
                <div>
                  <Text type="secondary" style={{ fontSize: 11 }}>P99</Text>
                  <div style={{ fontWeight: 600, color: '#ff4d4f' }}>{metrics.p99}ms</div>
                </div>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Trend Charts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="QPS Trend" bordered={false}>
            {metrics.qps_series?.length > 0 ? (
              <ReactECharts option={qpsChartOption} style={{ height: 280 }} />
            ) : (
              <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                No QPS data available
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Latency Trend" bordered={false}>
            {metrics.latency_series?.length > 0 ? (
              <ReactECharts option={latencyChartOption} style={{ height: 280 }} />
            ) : (
              <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                No latency data available
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
