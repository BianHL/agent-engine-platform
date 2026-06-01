'use client';
import React from 'react';
import { Card, Table, Tag, Progress, Typography, Space, Tooltip } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

export interface MetricRow {
  metric: string;
  score: number;
  min: number;
  max: number;
  count: number;
}

interface EvalMetricsTableProps {
  metrics: MetricRow[];
  loading?: boolean;
}

const METRIC_LABELS: Record<string, string> = {
  faithfulness: 'Faithfulness',
  answer_relevancy: 'Answer Relevancy',
  context_precision: 'Context Precision',
  context_recall: 'Context Recall',
  tool_call_accuracy: 'Tool Call Accuracy',
};

const METRIC_DESCRIPTIONS: Record<string, string> = {
  faithfulness: 'Measures if the answer stays grounded in the retrieved context. Higher = fewer hallucinations.',
  answer_relevancy: 'Measures how relevant the answer is to the original question.',
  context_precision: 'Measures if relevant contexts are ranked higher in retrieval results.',
  context_recall: 'Measures if the retrieval covers all the information needed to answer correctly.',
  tool_call_accuracy: 'Measures if the agent made correct tool calls with proper arguments.',
};

const getScoreColor = (score: number): string => {
  if (score >= 0.8) return '#52c41a';
  if (score >= 0.6) return '#faad14';
  return '#ff4d4f';
};

const getScoreTag = (score: number) => {
  if (score >= 0.8) return <Tag color="success">Excellent</Tag>;
  if (score >= 0.6) return <Tag color="warning">Fair</Tag>;
  return <Tag color="error">Poor</Tag>;
};

export default function EvalMetricsTable({ metrics, loading }: EvalMetricsTableProps) {
  const columns = [
    {
      title: 'Metric',
      dataIndex: 'metric',
      key: 'metric',
      width: 200,
      render: (name: string) => (
        <Space>
          <Text strong>{METRIC_LABELS[name] || name}</Text>
          {METRIC_DESCRIPTIONS[name] && (
            <Tooltip title={METRIC_DESCRIPTIONS[name]}>
              <InfoCircleOutlined style={{ color: '#999', fontSize: 13 }} />
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 200,
      render: (score: number) => (
        <Space>
          <Progress
            percent={Math.round(score * 100)}
            size="small"
            strokeColor={getScoreColor(score)}
            style={{ width: 100 }}
          />
          <Text strong style={{ color: getScoreColor(score), minWidth: 45 }}>
            {(score * 100).toFixed(1)}%
          </Text>
          {getScoreTag(score)}
        </Space>
      ),
    },
    {
      title: 'Min',
      dataIndex: 'min',
      key: 'min',
      width: 80,
      render: (v: number) => <Text type="secondary">{(v * 100).toFixed(1)}%</Text>,
    },
    {
      title: 'Max',
      dataIndex: 'max',
      key: 'max',
      width: 80,
      render: (v: number) => <Text type="secondary">{(v * 100).toFixed(1)}%</Text>,
    },
    {
      title: 'Test Cases',
      dataIndex: 'count',
      key: 'count',
      width: 100,
      render: (count: number) => <Tag>{count}</Tag>,
    },
  ];

  return (
    <Card title="Detailed Metrics" size="small">
      <Table
        columns={columns}
        dataSource={metrics}
        rowKey="metric"
        loading={loading}
        pagination={false}
        size="small"
      />
    </Card>
  );
}
