'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  message, Tabs, Progress, Empty,
} from 'antd';
import {
  PlusOutlined, PlayCircleOutlined, PauseCircleOutlined, DeleteOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;

interface AgentVersion {
  id: string;
  agent_id: string;
  version: string;
  system_prompt: string;
  model_provider: string;
  model_name: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

interface ABTest {
  id: string;
  agent_id: string;
  name: string;
  version_a_id: string;
  version_b_id: string;
  traffic_split: number;
  metric: string;
  status: string;
  results: any;
  created_at: string;
}

export default function AgentVersionsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [versions, setVersions] = useState<AgentVersion[]>([]);
  const [abTests, setAbTests] = useState<ABTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [versionModalOpen, setVersionModalOpen] = useState(false);
  const [abTestModalOpen, setAbTestModalOpen] = useState(false);
  const [versionForm] = Form.useForm();
  const [abTestForm] = Form.useForm();

  const fetchAgents = useCallback(async () => {
    try {
      const res = await api.listAgents();
      setAgents(res.items || []);
      if (res.items?.length > 0 && !selectedAgent) setSelectedAgent(res.items[0].id);
    } catch { message.error('Failed to load agents'); }
  }, [selectedAgent]);

  const fetchVersions = useCallback(async () => {
    if (!selectedAgent) return;
    setLoading(true);
    try {
      const res = await api.get(`/agent-versions/${selectedAgent}/versions`);
      setVersions(Array.isArray(res) ? res : []);
    } catch { setVersions([]); } finally { setLoading(false); }
  }, [selectedAgent]);

  const fetchAbTests = useCallback(async () => {
    if (!selectedAgent) return;
    try {
      const res = await api.get(`/agent-versions/${selectedAgent}/ab-tests`);
      setAbTests(Array.isArray(res) ? res : []);
    } catch { setAbTests([]); }
  }, [selectedAgent]);

  useEffect(() => { fetchAgents(); }, []);
  useEffect(() => { if (selectedAgent) { fetchVersions(); fetchAbTests(); } }, [selectedAgent]);

  const handleCreateVersion = async () => {
    try {
      const values = await versionForm.validateFields();
      await api.post(`/agent-versions/${selectedAgent}/versions`, values);
      message.success('Version created');
      setVersionModalOpen(false);
      versionForm.resetFields();
      fetchVersions();
    } catch { message.error('Failed to create version'); }
  };

  const handleActivateVersion = async (id: string) => {
    try {
      await api.put(`/agent-versions/${selectedAgent}/versions/${id}/activate`);
      message.success('Version activated');
      fetchVersions();
    } catch { message.error('Failed to activate version'); }
  };

  const handleDeleteVersion = async (id: string) => {
    Modal.confirm({
      title: 'Delete version?',
      onOk: async () => {
        await api.delete(`/agent-versions/${selectedAgent}/versions/${id}`);
        message.success('Version deleted');
        fetchVersions();
      },
    });
  };

  const handleCreateABTest = async () => {
    try {
      const values = await abTestForm.validateFields();
      await api.post(`/agent-versions/${selectedAgent}/ab-tests`, values);
      message.success('A/B test created');
      setAbTestModalOpen(false);
      abTestForm.resetFields();
      fetchAbTests();
    } catch { message.error('Failed to create A/B test'); }
  };

  const handleStartTest = async (id: string) => {
    try {
      await api.post(`/agent-versions/${selectedAgent}/ab-tests/${id}/start`);
      message.success('Test started');
      fetchAbTests();
    } catch { message.error('Failed to start test'); }
  };

  const handleStopTest = async (id: string) => {
    try {
      await api.post(`/agent-versions/${selectedAgent}/ab-tests/${id}/stop`);
      message.success('Test stopped');
      fetchAbTests();
    } catch { message.error('Failed to stop test'); }
  };

  const versionColumns = [
    { title: 'Version', dataIndex: 'version', key: 'version', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: 'Model', key: 'model', render: (_: any, r: AgentVersion) => <Text>{r.model_provider}/{r.model_name}</Text> },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Status', key: 'status', render: (_: any, r: AgentVersion) => r.is_active ? <Tag color="green">Active</Tag> : <Tag>Inactive</Tag> },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, r: AgentVersion) => (
        <Space>
          {!r.is_active && <Button size="small" type="primary" onClick={() => handleActivateVersion(r.id)}>Activate</Button>}
          {!r.is_active && <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteVersion(r.id)} />}
        </Space>
      ),
    },
  ];

  const abTestColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Metric', dataIndex: 'metric', key: 'metric' },
    { title: 'Traffic Split', key: 'split', render: (_: any, r: ABTest) => <Progress percent={Math.round(r.traffic_split * 100)} size="small" /> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'running' ? 'processing' : s === 'completed' ? 'success' : 'default'}>{s}</Tag> },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, r: ABTest) => (
        <Space>
          {r.status === 'created' && <Button size="small" type="primary" icon={<PlayCircleOutlined />} onClick={() => handleStartTest(r.id)}>Start</Button>}
          {r.status === 'running' && <Button size="small" danger icon={<PauseCircleOutlined />} onClick={() => handleStopTest(r.id)}>Stop</Button>}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4}>Agent Versions & A/B Tests</Title>
        <Select placeholder="Select Agent" style={{ width: 200 }} value={selectedAgent} onChange={setSelectedAgent}
          options={agents.map(a => ({ value: a.id, label: a.name }))} />
      </div>

      {selectedAgent ? (
        <Tabs items={[
          {
            key: 'versions', label: `Versions (${versions.length})`,
            children: (
              <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setVersionModalOpen(true)}>Create Version</Button>}>
                <Table columns={versionColumns} dataSource={versions} loading={loading} rowKey="id" />
              </Card>
            ),
          },
          {
            key: 'ab-tests', label: `A/B Tests (${abTests.length})`,
            children: (
              <Card extra={<Button type="primary" icon={<ExperimentOutlined />} onClick={() => setAbTestModalOpen(true)}>Create A/B Test</Button>}>
                <Table columns={abTestColumns} dataSource={abTests} rowKey="id" />
              </Card>
            ),
          },
        ]} />
      ) : <Empty description="Select an agent to manage versions" />}

      <Modal title="Create Version" open={versionModalOpen} onOk={handleCreateVersion} onCancel={() => setVersionModalOpen(false)}>
        <Form form={versionForm} layout="vertical">
          <Form.Item name="version" label="Version" rules={[{ required: true }]}><Input placeholder="1.0.0" /></Form.Item>
          <Form.Item name="system_prompt" label="System Prompt" rules={[{ required: true }]}><Input.TextArea rows={4} /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="Create A/B Test" open={abTestModalOpen} onOk={handleCreateABTest} onCancel={() => setAbTestModalOpen(false)}>
        <Form form={abTestForm} layout="vertical">
          <Form.Item name="name" label="Test Name" rules={[{ required: true }]}><Input placeholder="My A/B Test" /></Form.Item>
          <Form.Item name="version_a_id" label="Version A (Control)" rules={[{ required: true }]}>
            <Select options={versions.map(v => ({ value: v.id, label: v.version }))} />
          </Form.Item>
          <Form.Item name="version_b_id" label="Version B (Variant)" rules={[{ required: true }]}>
            <Select options={versions.map(v => ({ value: v.id, label: v.version }))} />
          </Form.Item>
          <Form.Item name="traffic_split" label="Traffic to Version B" initialValue={0.5}>
            <Select options={[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].map(v => ({ value: v, label: `${v * 100}%` }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
