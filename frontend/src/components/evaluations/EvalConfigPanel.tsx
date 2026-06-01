'use client';
import React, { useEffect, useState } from 'react';
import { Card, Form, Select, Input, InputNumber, Checkbox, Button, Space, Typography, Divider, Tag, Spin } from 'antd';
import { SettingOutlined, PlayCircleOutlined } from '@ant-design/icons';
import api from '@/lib/api';

const { Text, Title } = Typography;

export interface EvalConfig {
  agent_id: string;
  knowledge_base_id?: string;
  metrics: string[];
  top_k: number;
  retrieval_strategy: string;
  run_name: string;
}

interface EvalConfigPanelProps {
  onRun: (config: EvalConfig) => void;
  running?: boolean;
}

const AVAILABLE_METRICS = [
  { label: 'Faithfulness', value: 'faithfulness', description: 'Does the answer stay grounded in retrieved context?' },
  { label: 'Answer Relevancy', value: 'answer_relevancy', description: 'Is the answer relevant to the question?' },
  { label: 'Context Precision', value: 'context_precision', description: 'Are retrieved contexts in good order?' },
  { label: 'Context Recall', value: 'context_recall', description: 'Does retrieval cover all needed info?' },
  { label: 'Tool Call Accuracy', value: 'tool_call_accuracy', description: 'Were tool calls correct?' },
];

const RETRIEVAL_STRATEGIES = [
  { label: 'Vector Search', value: 'vector' },
  { label: 'Full-Text Search', value: 'fulltext' },
  { label: 'Hybrid (Vector + Full-Text)', value: 'hybrid' },
  { label: 'Knowledge Graph', value: 'kg' },
];

export default function EvalConfigPanel({ onRun, running }: EvalConfigPanelProps) {
  const [form] = Form.useForm();
  const [agents, setAgents] = useState<any[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.listAgents(1, 100),
      api.listKnowledgeBases(1, 100),
    ])
      .then(([agentsRes, kbRes]) => {
        setAgents(agentsRes.items || agentsRes || []);
        setKnowledgeBases(kbRes.items || kbRes || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleRun = async () => {
    try {
      const values = await form.validateFields();
      onRun({
        agent_id: values.agent_id,
        knowledge_base_id: values.knowledge_base_id,
        metrics: values.metrics || ['faithfulness', 'answer_relevancy'],
        top_k: values.top_k || 5,
        retrieval_strategy: values.retrieval_strategy || 'hybrid',
        run_name: values.run_name || `Run ${new Date().toLocaleString()}`,
      });
    } catch {
      // validation errors shown by form
    }
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin />
        </div>
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          <span>Evaluation Configuration</span>
        </Space>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          metrics: ['faithfulness', 'answer_relevancy'],
          top_k: 5,
          retrieval_strategy: 'hybrid',
        }}
      >
        <Form.Item
          name="run_name"
          label="Run Name"
          rules={[{ required: true, message: 'Please enter a run name' }]}
        >
          <Input placeholder="e.g., Baseline Test v1" />
        </Form.Item>

        <Form.Item
          name="agent_id"
          label="Agent"
          rules={[{ required: true, message: 'Please select an agent' }]}
        >
          <Select placeholder="Select agent to evaluate">
            {agents.map(agent => (
              <Select.Option key={agent.id} value={agent.id}>
                <Space>
                  <span>{agent.name}</span>
                  <Tag>{agent.model_name}</Tag>
                </Space>
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="knowledge_base_id"
          label="Knowledge Base (optional)"
        >
          <Select placeholder="Select knowledge base for RAG evaluation" allowClear>
            {knowledgeBases.map(kb => (
              <Select.Option key={kb.id} value={kb.id}>
                <Space>
                  <span>{kb.name}</span>
                  <Tag>{kb.document_count} docs</Tag>
                </Space>
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Divider style={{ margin: '12px 0' }} />

        <Form.Item
          name="metrics"
          label="Evaluation Metrics"
          rules={[{ required: true, message: 'Select at least one metric' }]}
        >
          <Checkbox.Group style={{ width: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {AVAILABLE_METRICS.map(m => (
                <Checkbox key={m.value} value={m.value}>
                  <Space>
                    <Text>{m.label}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>- {m.description}</Text>
                  </Space>
                </Checkbox>
              ))}
            </Space>
          </Checkbox.Group>
        </Form.Item>

        <Divider style={{ margin: '12px 0' }} />

        <Form.Item name="top_k" label="Top K (Retrieval Depth)">
          <InputNumber min={1} max={20} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="retrieval_strategy" label="Retrieval Strategy">
          <Select>
            {RETRIEVAL_STRATEGIES.map(s => (
              <Select.Option key={s.value} value={s.value}>{s.label}</Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          size="large"
          block
          loading={running}
          onClick={handleRun}
        >
          {running ? 'Running Evaluation...' : 'Run Evaluation'}
        </Button>
      </Form>
    </Card>
  );
}
