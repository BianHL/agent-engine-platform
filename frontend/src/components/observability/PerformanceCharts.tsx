'use client';
import React from 'react';
import { Card, Col, Row, Typography, Skeleton, Space, Statistic } from 'antd';
import { FieldTimeOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { MetricsData } from '@/app/(platform)/observability/page';

const { Text } = Typography;

interface Props {
  metrics: MetricsData | null;
  loading: boolean;
}

export default function PerformanceCharts({ metrics, loading }: Props) {
  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Row gutter={[16, 16]}>
          {[1, 2, 3].map((i) => (
            <Col xs={24} lg={8} key={i}>
              <Card bordered={false}><Skeleton active paragraph={{ rows: 4 }} /></Card>
            </Col>
          ))}
          <Col span={24}>
            <Card bordered={false}><Skeleton active paragraph={{ rows: 6 }} /></Card>
          </Col>
        </Row>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>
        No performance data available
      </div>
    );
  }

  // Percentile comparison bar chart
  const percentileOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 60, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'category' as const,
      data: ['P50', 'P90', 'P99'],
    },
    yAxis: {
      type: 'value' as const,
      name: 'ms',
    },
    series: [
      {
        type: 'bar',
        data: [
          { value: metrics.p50, itemStyle: { color: '#52c41a', borderRadius: [4, 4, 0, 0] } },
          { value: metrics.p90, itemStyle: { color: '#faad14', borderRadius: [4, 4, 0, 0] } },
          { value: metrics.p99, itemStyle: { color: '#ff4d4f', borderRadius: [4, 4, 0, 0] } },
        ],
        barWidth: 60,
        label: {
          show: true,
          position: 'top' as const,
          formatter: '{c}ms',
          fontWeight: 'bold' as const,
        },
      },
    ],
  };

  // Latency distribution - box plot style using custom series
  const latencyTimes = (metrics.latency_series || []).map((p) => p.time);
  const latencyValues = (metrics.latency_series || []).map((p) => p.value);

  const latencyDistributionOption = {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        return `${p.name}<br/>Latency: ${p.value}ms`;
      },
    },
    grid: { left: 60, right: 30, top: 30, bottom: 50 },
    xAxis: {
      type: 'category' as const,
      data: latencyTimes,
      axisLabel: { fontSize: 11, rotate: 30 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Latency (ms)',
      axisLabel: { fontSize: 11 },
    },
    visualMap: {
      show: false,
      pieces: [
        { lte: metrics.p50, color: '#52c41a' },
        { gt: metrics.p50, lte: metrics.p90, color: '#faad14' },
        { gt: metrics.p90, color: '#ff4d4f' },
      ],
    },
    series: [
      {
        type: 'line',
        data: latencyValues,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.15 },
        markLine: {
          silent: true,
          data: [
            { yAxis: metrics.p50, label: { formatter: 'P50', position: 'end' as const }, lineStyle: { color: '#52c41a', type: 'dashed' as const } },
            { yAxis: metrics.p90, label: { formatter: 'P90', position: 'end' as const }, lineStyle: { color: '#faad14', type: 'dashed' as const } },
            { yAxis: metrics.p99, label: { formatter: 'P99', position: 'end' as const }, lineStyle: { color: '#ff4d4f', type: 'dashed' as const } },
          ],
        },
      },
    ],
  };

  // Latency heatmap-style histogram
  const buckets = [0, 50, 100, 200, 500, 1000, 2000, 5000];
  const bucketLabels = buckets.map((b, i) => {
    if (i === buckets.length - 1) return `>${b}ms`;
    return `${b}-${buckets[i + 1]}ms`;
  });

  // Simulate histogram from latency series
  const histogramData = bucketLabels.map((label, i) => {
    const min = buckets[i];
    const max = i < buckets.length - 1 ? buckets[i + 1] : Infinity;
    const count = latencyValues.filter((v) => v >= min && v < max).length;
    return { name: label, value: count };
  });

  const histogramOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: 80, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'category' as const,
      data: bucketLabels,
      axisLabel: { fontSize: 10, rotate: 20 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Requests',
    },
    series: [
      {
        type: 'bar',
        data: histogramData.map((d, i) => ({
          value: d.value,
          itemStyle: {
            color: i <= 2 ? '#52c41a' : i <= 4 ? '#faad14' : '#ff4d4f',
            borderRadius: [4, 4, 0, 0],
          },
        })),
        barMaxWidth: 50,
      },
    ],
  };

  // QPS vs Latency dual axis
  const dualAxisOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { bottom: 0 },
    grid: { left: 60, right: 60, top: 20, bottom: 50 },
    xAxis: {
      type: 'category' as const,
      data: (metrics.qps_series || []).map((p) => p.time),
      axisLabel: { fontSize: 11 },
    },
    yAxis: [
      {
        type: 'value' as const,
        name: 'QPS',
        position: 'left' as const,
        axisLabel: { fontSize: 11 },
      },
      {
        type: 'value' as const,
        name: 'Latency (ms)',
        position: 'right' as const,
        axisLabel: { fontSize: 11 },
      },
    ],
    series: [
      {
        name: 'QPS',
        type: 'line',
        data: (metrics.qps_series || []).map((p) => p.value),
        smooth: true,
        showSymbol: false,
        itemStyle: { color: '#1890ff' },
        areaStyle: { opacity: 0.1, color: '#1890ff' },
      },
      {
        name: 'Latency',
        type: 'line',
        yAxisIndex: 1,
        data: (metrics.latency_series || []).map((p) => p.value),
        smooth: true,
        showSymbol: false,
        itemStyle: { color: '#faad14' },
        lineStyle: { type: 'dashed' as const },
      },
    ],
  };

  return (
    <div style={{ padding: 24 }}>
      {/* Percentile Summary */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="P50 Latency"
              value={metrics.p50}
              prefix={<FieldTimeOutlined />}
              suffix="ms"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="P90 Latency"
              value={metrics.p90}
              prefix={<FieldTimeOutlined />}
              suffix="ms"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="P99 Latency"
              value={metrics.p99}
              prefix={<FieldTimeOutlined />}
              suffix="ms"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="Percentile Comparison" bordered={false}>
            <ReactECharts option={percentileOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={16}>
          <Card title="Latency Distribution Over Time" bordered={false}>
            {latencyTimes.length > 0 ? (
              <ReactECharts option={latencyDistributionOption} style={{ height: 300 }} />
            ) : (
              <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                No latency data
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Latency Histogram" bordered={false}>
            <ReactECharts option={histogramOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="QPS vs Latency (Dual Axis)" bordered={false}>
            {(metrics.qps_series?.length ?? 0) > 0 ? (
              <ReactECharts option={dualAxisOption} style={{ height: 300 }} />
            ) : (
              <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                No data available
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
