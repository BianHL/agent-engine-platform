'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, message, Spin, Descriptions, Tabs, List, Progress, Statistic,
  Row, Col, DatePicker,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, PlayCircleOutlined, ExperimentOutlined,
  FileTextOutlined, RocketOutlined, BarChartOutlined, CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface EvaluationDataset {
  id: string;
  name: string;
  description?: string;
  question_count: number;
  created_at: string;
}

interface EvaluationRun {
  id: string;
  dataset_id: string;
  dataset_name?: string;
  agent_id: string;
  agent_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_questions: number;
  passed: number;
  failed: number;
  score?: number;
  created_at: string;
  completed_at?: string;
}

interface EvaluationResult {
  id: string;
  run_id: string;
  question: string;
  expected_answer: string;
  actual_answer: string;
  passed: boolean;
  score: number;
  reasoning?: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
};

export default function EvaluationsPage() {
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [results, setResults] = useState<EvaluationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('runs');

  // Dataset modal
  const [datasetModalOpen, setDatasetModalOpen] = useState(false);
  const [submittingDataset, setSubmittingDataset] = useState(false);
  const [datasetForm] = Form.useForm();

  // Run modal
  const [runModalOpen, setRunModalOpen] = useState(false);
  const [submittingRun, setSubmittingRun] = useState(false);
  const [runForm] = Form.useForm();
  const [agents, setAgents] = useState<any[]>([]);

  const fetchData = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<any[]>('/evaluations/datasets'),
      api.get<any[]>('/evaluations/runs'),
      api.listAgents(1, 100),
    ])
      .then(([datasetsData, runsData, agentsData]) => {
        setDatasets(datasetsData || []);
        setRuns(runsData || []);
        setAgents(agentsData.items || agentsData || []);
      })
      .catch(() => message.error('Failed to load evaluation data'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreateDataset = async () => {
    try {
      const values = await datasetForm.validateFields();
      setSubmittingDataset(true);
      await api.post('/evaluations/datasets', values);
      message.success('Dataset created');
      setDatasetModalOpen(false);
      datasetForm.resetFields();
      fetchData();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error('Failed to create dataset');
    } finally {
      setSubmittingDataset(false);
    }
  };

  const handleDeleteDataset = async (id: string) => {
    try {
      await api.delete(`/evaluations/datasets/${id}`);
      message.success('Dataset deleted');
      fetchData();
    } catch {
      message.error('Failed to delete dataset');
    }
  };

  const handleCreateRun = async () => {
    try {
      const values = await runForm.validateFields();
      setSubmittingRun(true);
      await api.post('/evaluations/runs', values);
      message.success('Evaluation run started');
      setRunModalOpen(false);
      runForm.resetFields();
      fetchData();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error('Failed to start evaluation run');
    } finally {
      setSubmittingRun(false);
    }
  };

  const handleDeleteRun = async (id: string) => {
    try {
      await api.delete(`/evaluations/runs/${id}`);
      message.success('Run deleted');
      fetchData();
    } catch {
      message.error('Failed to delete run');
    }
  };

  const handleViewResults = async (runId: string) => {
    try {
      const data = await api.get<EvaluationResult[]>(`/evaluations/runs/${runId}/results`);
      setResults(data || []);
      setActiveTab('results');
    } catch {
      message.error('Failed to load results');
    }
  };

  const datasetColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (desc: string) => desc || '-',
    },
    {
      title: 'Questions',
      dataIndex: 'question_count',
      key: 'question_count',
      width: 120,
      render: (count: number) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: any, record: EvaluationDataset) => (
        <Popconfirm
          title="Delete this dataset?"
          onConfirm={() => handleDeleteDataset(record.id)}
        >
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  const runColumns = [
    {
      title: 'Dataset',
      dataIndex: 'dataset_name',
      key: 'dataset_name',
      render: (name: string, record: EvaluationRun) => name || record.dataset_id,
    },
    {
      title: 'Agent',
      dataIndex: 'agent_name',
      key: 'agent_name',
      render: (name: string, record: EvaluationRun) => name || record.agent_id,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <Tag color={STATUS_COLORS[status]}>{status}</Tag>,
    },
    {
      title: 'Progress',
      key: 'progress',
      width: 150,
      render: (_: any, record: EvaluationRun) => {
        if (record.status === 'completed') {
          return <Progress percent={100} size="small" status="success" />;
        }
        if (record.status === 'running') {
          const percent = Math.round(
            ((record.passed + record.failed) / record.total_questions) * 100
          );
          return <Progress percent={percent} size="small" status="active" />;
        }
        return <Progress percent={0} size="small" />;
      },
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score: number | undefined) =>
        score !== undefined ? (
          <Tag color={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'}>
            {score.toFixed(1)}%
          </Tag>
        ) : '-',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: any, record: EvaluationRun) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              size="small"
              icon={<BarChartOutlined />}
              onClick={() => handleViewResults(record.id)}
            >
              Results
            </Button>
          )}
          <Popconfirm
            title="Delete this run?"
            onConfirm={() => handleDeleteRun(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const resultColumns = [
    {
      title: 'Status',
      dataIndex: 'passed',
      key: 'passed',
      width: 80,
      render: (passed: boolean) => (
        passed ? (
          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />
        ) : (
          <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
        )
      ),
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score: number) => `${score.toFixed(1)}%`,
    },
    {
      title: 'Question',
      dataIndex: 'question',
      key: 'question',
      ellipsis: true,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Evaluations</Title>
        <Space>
          <Button
            icon={<PlusOutlined />}
            onClick={() => setDatasetModalOpen(true)}
          >
            New Dataset
          </Button>
          <Button
            type="primary"
            icon={<RocketOutlined />}
            onClick={() => setRunModalOpen(true)}
          >
            Run Evaluation
          </Button>
        </Space>
      </div>

      {runs.length > 0 && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Runs"
                value={runs.length}
                prefix={<ExperimentOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Completed"
                value={runs.filter((r) => r.status === 'completed').length}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Running"
                value={runs.filter((r) => r.status === 'running').length}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Avg Score"
                value={
                  runs
                    .filter((r) => r.score !== undefined)
                    .reduce((sum, r) => sum + (r.score || 0), 0) /
                  Math.max(runs.filter((r) => r.score !== undefined).length, 1)
                }
                suffix="%"
                precision={1}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'runs',
              label: `Evaluation Runs (${runs.length})`,
              children: (
                <Table
                  columns={runColumns}
                  dataSource={runs}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 20 }}
                  expandable={{
                    expandedRowRender: (record: EvaluationRun) => (
                      <Descriptions column={2} size="small">
                        <Descriptions.Item label="Run ID">{record.id}</Descriptions.Item>
                        <Descriptions.Item label="Dataset ID">{record.dataset_id}</Descriptions.Item>
                        <Descriptions.Item label="Agent ID">{record.agent_id}</Descriptions.Item>
                        <Descriptions.Item label="Total Questions">{record.total_questions}</Descriptions.Item>
                        <Descriptions.Item label="Passed">
                          <Tag color="success">{record.passed}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Failed">
                          <Tag color="error">{record.failed}</Tag>
                        </Descriptions.Item>
                      </Descriptions>
                    ),
                  }}
                />
              ),
            },
            {
              key: 'datasets',
              label: `Datasets (${datasets.length})`,
              children: (
                <Table
                  columns={datasetColumns}
                  dataSource={datasets}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 20 }}
                />
              ),
            },
            {
              key: 'results',
              label: `Results (${results.length})`,
              children: (
                <Table
                  columns={resultColumns}
                  dataSource={results}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 20 }}
                  expandable={{
                    expandedRowRender: (record: EvaluationResult) => (
                      <Card size="small" title="Details">
                        <div style={{ marginBottom: 8 }}>
                          <Text strong>Expected Answer:</Text>
                          <p style={{ marginTop: 4 }}>{record.expected_answer}</p>
                        </div>
                        <div style={{ marginBottom: 8 }}>
                          <Text strong>Actual Answer:</Text>
                          <p style={{ marginTop: 4 }}>{record.actual_answer}</p>
                        </div>
                        {record.reasoning && (
                          <div>
                            <Text strong>Reasoning:</Text>
                            <p style={{ marginTop: 4 }}>{record.reasoning}</p>
                          </div>
                        )}
                      </Card>
                    ),
                  }}
                />
              ),
            },
          ]}
        />
      </Card>

      {/* Create Dataset Modal */}
      <Modal
        title="Create Evaluation Dataset"
        open={datasetModalOpen}
        onOk={handleCreateDataset}
        onCancel={() => setDatasetModalOpen(false)}
        confirmLoading={submittingDataset}
        width={600}
      >
        <Form form={datasetForm} layout="vertical">
          <Form.Item
            name="name"
            label="Dataset Name"
            rules={[{ required: true }]}
          >
            <Input placeholder="e.g., Medical Knowledge Test" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Describe this evaluation dataset" />
          </Form.Item>
          <Form.Item
            name="questions"
            label="Questions (JSON)"
            rules={[{ required: true }]}
            help="Array of objects with question and expected_answer fields"
          >
            <TextArea
              rows={8}
              placeholder={`[\n  {\n    "question": "What is the capital of France?",\n    "expected_answer": "Paris"\n  }\n]`}
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Run Modal */}
      <Modal
        title="Run Evaluation"
        open={runModalOpen}
        onOk={handleCreateRun}
        onCancel={() => setRunModalOpen(false)}
        confirmLoading={submittingRun}
      >
        <Form form={runForm} layout="vertical">
          <Form.Item
            name="dataset_id"
            label="Dataset"
            rules={[{ required: true }]}
          >
            <Select placeholder="Select evaluation dataset">
              {datasets.map((ds) => (
                <Select.Option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.question_count} questions)
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="agent_id"
            label="Agent to Evaluate"
            rules={[{ required: true }]}
          >
            <Select placeholder="Select agent to evaluate">
              {agents.map((agent) => (
                <Select.Option key={agent.id} value={agent.id}>
                  {agent.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
