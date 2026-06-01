'use client';
import React from 'react';
import { Card, Empty, Typography } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';

const { Text } = Typography;

export interface MetricData {
  name: string;
  value: number;
}

interface EvalResultChartProps {
  metrics: MetricData[];
  title?: string;
  height?: number;
  type?: 'radar' | 'bar' | 'gauge';
}

const METRIC_COLORS: Record<string, string> = {
  faithfulness: '#1890ff',
  answer_relevancy: '#52c41a',
  context_precision: '#faad14',
  context_recall: '#722ed1',
  tool_call_accuracy: '#eb2f96',
};

const METRIC_LABELS: Record<string, string> = {
  faithfulness: 'Faithfulness',
  answer_relevancy: 'Answer Relevancy',
  context_precision: 'Context Precision',
  context_recall: 'Context Recall',
  tool_call_accuracy: 'Tool Call Accuracy',
};

export default function EvalResultChart({ metrics, title = 'Evaluation Metrics', height = 350, type = 'radar' }: EvalResultChartProps) {
  if (!metrics || metrics.length === 0) {
    return (
      <Card title={title}>
        <Empty description="No evaluation results yet" />
      </Card>
    );
  }

  const getOption = () => {
    if (type === 'radar') {
      return {
        title: { show: false },
        tooltip: {
          trigger: 'item',
          formatter: (params: any) => {
            const data = params.data || params;
            let html = `<strong>${data.name || ''}</strong><br/>`;
            if (data.value) {
              metrics.forEach((m, i) => {
                html += `${METRIC_LABELS[m.name] || m.name}: ${(data.value[i] * 100).toFixed(1)}%<br/>`;
              });
            }
            return html;
          },
        },
        radar: {
          indicator: metrics.map(m => ({
            name: METRIC_LABELS[m.name] || m.name,
            max: 1,
          })),
          shape: 'polygon',
          splitNumber: 5,
          axisName: {
            color: '#666',
            fontSize: 12,
          },
          splitLine: { lineStyle: { color: '#e8e8e8' } },
          splitArea: { show: true, areaStyle: { color: ['rgba(24,144,255,0.02)', 'rgba(24,144,255,0.05)'] } },
        },
        series: [{
          type: 'radar',
          data: [{
            value: metrics.map(m => m.value),
            name: 'Score',
            areaStyle: { color: 'rgba(24,144,255,0.15)' },
            lineStyle: { color: '#1890ff', width: 2 },
            itemStyle: { color: '#1890ff' },
          }],
        }],
      };
    }

    if (type === 'bar') {
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: (params: any) => {
            const p = params[0];
            return `${METRIC_LABELS[p.name] || p.name}: ${(p.value * 100).toFixed(1)}%`;
          },
        },
        grid: { left: 60, right: 20, top: 20, bottom: 40 },
        xAxis: {
          type: 'category',
          data: metrics.map(m => METRIC_LABELS[m.name] || m.name),
          axisLabel: { rotate: metrics.length > 4 ? 20 : 0, fontSize: 11 },
        },
        yAxis: {
          type: 'value',
          max: 1,
          axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
        },
        series: [{
          type: 'bar',
          data: metrics.map(m => ({
            value: m.value,
            itemStyle: { color: METRIC_COLORS[m.name] || '#1890ff', borderRadius: [4, 4, 0, 0] },
          })),
          barWidth: '50%',
          label: {
            show: true,
            position: 'top',
            formatter: (p: any) => `${(p.value * 100).toFixed(1)}%`,
            fontSize: 11,
          },
        }],
      };
    }

    if (type === 'gauge') {
      const avg = metrics.reduce((sum, m) => sum + m.value, 0) / metrics.length;
      return {
        series: [{
          type: 'gauge',
          startAngle: 200,
          endAngle: -20,
          min: 0,
          max: 1,
          splitNumber: 10,
          axisLine: {
            lineStyle: {
              width: 20,
              color: [
                [0.3, '#ff4d4f'],
                [0.6, '#faad14'],
                [0.8, '#52c41a'],
                [1, '#1890ff'],
              ],
            },
          },
          pointer: { itemStyle: { color: 'auto' } },
          axisTick: { distance: -20, length: 6, lineStyle: { color: '#fff', width: 1 } },
          splitLine: { distance: -20, length: 16, lineStyle: { color: '#fff', width: 2 } },
          axisLabel: { color: 'inherit', distance: 30, fontSize: 11, formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
          detail: {
            valueAnimation: true,
            formatter: (v: number) => `${(v * 100).toFixed(1)}%`,
            color: 'inherit',
            fontSize: 24,
            offsetCenter: [0, '70%'],
          },
          title: { offsetCenter: [0, '90%'], fontSize: 14 },
          data: [{ value: avg, name: 'Average Score' }],
        }],
      };
    }

    return {};
  };

  return (
    <Card title={title} size="small">
      <ReactECharts option={getOption()} style={{ height }} opts={{ renderer: 'canvas' }} />
    </Card>
  );
}
