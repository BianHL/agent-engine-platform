'use client';
import React from 'react';
import { Card, Empty, Typography, Space, Tag, Table } from 'antd';
import { SwapOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';

const { Text } = Typography;

export interface ComparisonRun {
  id: string;
  name: string;
  metrics: Record<string, number>;
  created_at: string;
}

interface EvalComparisonProps {
  runs: ComparisonRun[];
}

const METRIC_LABELS: Record<string, string> = {
  faithfulness: 'Faithfulness',
  answer_relevancy: 'Answer Relevancy',
  context_precision: 'Context Precision',
  context_recall: 'Context Recall',
  tool_call_accuracy: 'Tool Call Accuracy',
};

const RUN_COLORS = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#eb2f96', '#13c2c2'];

export default function EvalComparison({ runs }: EvalComparisonProps) {
  if (!runs || runs.length < 2) {
    return (
      <Card
        title={<Space><SwapOutlined /> Comparison</Space>}
        size="small"
      >
        <Empty description="Select at least 2 runs to compare" />
      </Card>
    );
  }

  // Get all metric names
  const allMetrics = Array.from(new Set(runs.flatMap(r => Object.keys(r.metrics))));

  // Radar chart option
  const radarOption = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        let html = `<strong>${params.name || ''}</strong><br/>`;
        allMetrics.forEach((m, i) => {
          const val = params.value?.[i];
          if (val !== undefined) {
            html += `${METRIC_LABELS[m] || m}: ${(val * 100).toFixed(1)}%<br/>`;
          }
        });
        return html;
      },
    },
    legend: {
      data: runs.map(r => r.name),
      bottom: 0,
    },
    radar: {
      indicator: allMetrics.map(m => ({
        name: METRIC_LABELS[m] || m,
        max: 1,
      })),
      shape: 'polygon',
      splitNumber: 5,
      axisName: { color: '#666', fontSize: 11 },
      splitLine: { lineStyle: { color: '#e8e8e8' } },
      splitArea: { show: true, areaStyle: { color: ['rgba(24,144,255,0.02)', 'rgba(24,144,255,0.05)'] } },
    },
    series: [{
      type: 'radar',
      data: runs.map((run, i) => ({
        value: allMetrics.map(m => run.metrics[m] || 0),
        name: run.name,
        lineStyle: { color: RUN_COLORS[i % RUN_COLORS.length], width: 2 },
        itemStyle: { color: RUN_COLORS[i % RUN_COLORS.length] },
        areaStyle: { color: `${RUN_COLORS[i % RUN_COLORS.length]}15` },
      })),
    }],
  };

  // Bar chart option
  const barOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        let html = `<strong>${params[0]?.axisValue || ''}</strong><br/>`;
        params.forEach((p: any) => {
          html += `${p.marker} ${p.seriesName}: ${(p.value * 100).toFixed(1)}%<br/>`;
        });
        return html;
      },
    },
    legend: { data: runs.map(r => r.name), bottom: 0 },
    grid: { left: 80, right: 20, top: 20, bottom: 50 },
    xAxis: {
      type: 'category',
      data: allMetrics.map(m => METRIC_LABELS[m] || m),
      axisLabel: { rotate: allMetrics.length > 4 ? 20 : 0, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      max: 1,
      axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
    },
    series: runs.map((run, i) => ({
      name: run.name,
      type: 'bar',
      data: allMetrics.map(m => run.metrics[m] || 0),
      itemStyle: { color: RUN_COLORS[i % RUN_COLORS.length], borderRadius: [4, 4, 0, 0] },
    })),
  };

  // Build comparison table data
  const tableData = allMetrics.map(metric => {
    const row: any = { metric };
    runs.forEach((run, i) => {
      row[`run_${i}`] = run.metrics[metric] || 0;
    });
    // Find best
    const scores = runs.map(r => r.metrics[metric] || 0);
    const maxIdx = scores.indexOf(Math.max(...scores));
    row.bestIdx = maxIdx;
    return row;
  });

  const tableColumns = [
    {
      title: 'Metric',
      dataIndex: 'metric',
      key: 'metric',
      width: 160,
      render: (name: string) => <Text strong>{METRIC_LABELS[name] || name}</Text>,
    },
    ...runs.map((run, i) => ({
      title: (
        <Space>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: RUN_COLORS[i % RUN_COLORS.length], display: 'inline-block' }} />
          {run.name}
        </Space>
      ),
      dataIndex: `run_${i}`,
      key: `run_${i}`,
      width: 120,
      render: (score: number, record: any) => (
        <Space>
          <Text style={{ color: record.bestIdx === i ? '#52c41a' : undefined, fontWeight: record.bestIdx === i ? 600 : 400 }}>
            {(score * 100).toFixed(1)}%
          </Text>
          {record.bestIdx === i && <Tag color="success" style={{ marginLeft: 4 }}>Best</Tag>}
        </Space>
      ),
    })),
  ];

  return (
    <Space direction="vertical" style={{ width: '100%' }} size={16}>
      <Card title={<Space><SwapOutlined /> Radar Comparison</Space>} size="small">
        <ReactECharts option={radarOption} style={{ height: 350 }} />
      </Card>

      <Card title="Bar Comparison" size="small">
        <ReactECharts option={barOption} style={{ height: 300 }} />
      </Card>

      <Card title="Detailed Comparison" size="small">
        <Table
          columns={tableColumns}
          dataSource={tableData}
          rowKey="metric"
          pagination={false}
          size="small"
        />
      </Card>
    </Space>
  );
}
