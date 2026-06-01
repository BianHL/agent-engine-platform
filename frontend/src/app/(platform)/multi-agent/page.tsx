'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, message, Spin, Descriptions, Drawer, List, Divider,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, PlayCircleOutlined,
  TeamOutlined, UserOutlined, RobotOutlined, SettingOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Crew {
  id: string;
  name: string;
  description?: string;
  agents: string[];
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

interface Agent {
  id: string;
  name: string;
  description?: string;
  model_name: string;
  status: string;
}

const STATUS_COLORS: Record<string, string> = {
  active: 'success',
  inactive: 'default',
  draft: 'default',
  published: 'success',
};

export default function MultiAgentPage() {
  const [crews, setCrews] = useState<Crew[]>([]);
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [agentsLoading, setAgentsLoading] = useState(true);

  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCrew, setEditingCrew] = useState<Crew | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  // Execution drawer
  const [executeDrawerOpen, setExecuteDrawerOpen] = useState(false);
  const [executingCrew, setExecutingCrew] = useState<Crew | null>(null);
  const [executionInput, setExecutionInput] = useState('');
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  const fetchCrews = useCallback(() => {
    setLoading(true);
    api.get<any[]>('/multi-agent/crews')
      .then(setCrews)
      .catch(() => message.error('Failed to load crews'))
      .finally(() => setLoading(false));
  }, []);

  const fetchAgents = useCallback(() => {
    setAgentsLoading(true);
    api.listAgents(1, 100)
      .then((res) => {
        const agents = res.items || res || [];
        setAvailableAgents(agents);
      })
      .catch(() => message.error('Failed to load agents'))
      .finally(() => setAgentsLoading(false));
  }, []);

  useEffect(() => {
    fetchCrews();
    fetchAgents();
  }, [fetchCrews, fetchAgents]);

  const handleCreate = () => {
    setEditingCrew(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (crew: Crew) => {
    setEditingCrew(crew);
    form.setFieldsValue({
      name: crew.name,
      description: crew.description,
      agents: crew.agents,
      status: crew.status,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingCrew) {
        await api.put(`/multi-agent/crews/${editingCrew.id}`, values);
        message.success('Crew updated');
      } else {
        await api.post('/multi-agent/crews', values);
        message.success('Crew created');
      }

      setModalOpen(false);
      form.resetFields();
      fetchCrews();
    } catch (e: any) {
      if (e.errorFields) {
        return; // Validation error
      }
      message.error(editingCrew ? 'Failed to update crew' : 'Failed to create crew');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/multi-agent/crews/${id}`);
      message.success('Crew deleted');
      fetchCrews();
    } catch {
      message.error('Failed to delete crew');
    }
  };

  const handleExecute = async () => {
    if (!executingCrew) return;

    setExecuting(true);
    setExecutionResult(null);

    try {
      const result = await api.post(`/multi-agent/crews/${executingCrew.id}/execute`, {
        input: executionInput,
      });
      setExecutionResult(result);
      message.success('Execution completed');
    } catch {
      message.error('Execution failed');
    } finally {
      setExecuting(false);
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <TeamOutlined />
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
      title: 'Agents',
      dataIndex: 'agents',
      key: 'agents',
      render: (agentIds: string[]) => (
        <Space size="small">
          {agentIds?.slice(0, 3).map((id) => (
            <Tag key={id} icon={<RobotOutlined />} color="blue">
              {availableAgents.find((a) => a.id === id)?.name || id}
            </Tag>
          ))}
          {agentIds?.length > 3 && <Tag>+{agentIds.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={STATUS_COLORS[status]}>{status}</Tag>,
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
      width: 180,
      render: (_: any, record: Crew) => (
        <Space>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => {
              setExecutingCrew(record);
              setExecutionInput('');
              setExecutionResult(null);
              setExecuteDrawerOpen(true);
            }}
          >
            Run
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Delete this crew?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Multi-Agent Crews</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create Crew
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={crews}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingCrew ? 'Edit Crew' : 'Create Crew'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Crew Name"
            rules={[{ required: true, message: 'Please enter crew name' }]}
          >
            <Input placeholder="e.g., Research Team" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Describe this crew's purpose" />
          </Form.Item>
          <Form.Item
            name="agents"
            label="Agents"
            rules={[{ required: true, message: 'Please select at least one agent' }]}
          >
            <Select
              mode="multiple"
              placeholder="Select agents to include in this crew"
              loading={agentsLoading}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={availableAgents.map((agent) => ({
                value: agent.id,
                label: agent.name,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="status"
            label="Status"
            initialValue="active"
          >
            <Select>
              <Select.Option value="active">Active</Select.Option>
              <Select.Option value="inactive">Inactive</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Execution Drawer */}
      <Drawer
        title={`Execute Crew: ${executingCrew?.name || ''}`}
        open={executeDrawerOpen}
        onClose={() => setExecuteDrawerOpen(false)}
        width={600}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setExecuteDrawerOpen(false)}>Cancel</Button>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                loading={executing}
                onClick={handleExecute}
                disabled={!executionInput.trim()}
              >
                Execute
              </Button>
            </Space>
          </div>
        }
      >
        {executingCrew && (
          <>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Description">
                {executingCrew.description || 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Agents">
                <Space size="small" wrap>
                  {executingCrew.agents.map((id) => {
                    const agent = availableAgents.find((a) => a.id === id);
                    return (
                      <Tag key={id} icon={<RobotOutlined />} color="blue">
                        {agent?.name || id}
                      </Tag>
                    );
                  })}
                </Space>
              </Descriptions.Item>
            </Descriptions>

            <Divider>Execution</Divider>

            <div style={{ marginBottom: 16 }}>
              <Text strong>Input:</Text>
              <TextArea
                rows={4}
                value={executionInput}
                onChange={(e) => setExecutionInput(e.target.value)}
                placeholder="Enter input for the crew to process..."
                style={{ marginTop: 8 }}
              />
            </div>

            {executionResult && (
              <>
                <Divider>Result</Divider>
                <Card size="small">
                  <pre style={{
                    whiteSpace: 'pre-wrap',
                    margin: 0,
                    fontSize: 13,
                    maxHeight: 400,
                    overflow: 'auto',
                  }}>
                    {JSON.stringify(executionResult, null, 2)}
                  </pre>
                </Card>
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
}
