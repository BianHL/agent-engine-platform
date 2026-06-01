'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, message, Spin, Switch, Descriptions, Divider,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, ThunderboltOutlined,
  ClockCircleOutlined, BellOutlined, RocketOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Trigger {
  id: string;
  name: string;
  description?: string;
  type: 'cron' | 'event';
  enabled: boolean;
  config: Record<string, any>;
  target_type: 'workflow' | 'agent' | 'webhook';
  target_id: string;
  created_at: string;
  updated_at: string;
  last_triggered_at?: string;
  next_trigger_at?: string;
}

const TRIGGER_TYPES = [
  { value: 'cron', label: 'Cron Schedule', icon: <ClockCircleOutlined /> },
  { value: 'event', label: 'Event-based', icon: <BellOutlined /> },
];

const TARGET_TYPES = [
  { value: 'workflow', label: 'Workflow' },
  { value: 'agent', label: 'Agent' },
  { value: 'webhook', label: 'Webhook' },
];

export default function TriggersPage() {
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [loading, setLoading] = useState(true);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);

  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTrigger, setEditingTrigger] = useState<Trigger | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchTriggers = useCallback(() => {
    setLoading(true);
    api.get<Trigger[]>('/triggers')
      .then(setTriggers)
      .catch(() => message.error('Failed to load triggers'))
      .finally(() => setLoading(false));
  }, []);

  const fetchTargets = useCallback(() => {
    Promise.all([
      api.get<any[]>('/workflows'),
      api.listAgents(1, 100),
    ])
      .then(([workflowsData, agentsData]) => {
        setWorkflows(workflowsData || []);
        setAgents(agentsData.items || agentsData || []);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchTriggers();
    fetchTargets();
  }, [fetchTriggers, fetchTargets]);

  const handleCreate = () => {
    setEditingTrigger(null);
    form.resetFields();
    form.setFieldsValue({ type: 'cron', enabled: true, target_type: 'workflow' });
    setModalOpen(true);
  };

  const handleEdit = (trigger: Trigger) => {
    setEditingTrigger(trigger);
    form.setFieldsValue({
      name: trigger.name,
      description: trigger.description,
      type: trigger.type,
      enabled: trigger.enabled,
      config: trigger.config,
      target_type: trigger.target_type,
      target_id: trigger.target_id,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingTrigger) {
        await api.put(`/triggers/${editingTrigger.id}`, values);
        message.success('Trigger updated');
      } else {
        await api.post('/triggers', values);
        message.success('Trigger created');
      }

      setModalOpen(false);
      form.resetFields();
      fetchTriggers();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error(editingTrigger ? 'Failed to update trigger' : 'Failed to create trigger');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/triggers/${id}`);
      message.success('Trigger deleted');
      fetchTriggers();
    } catch {
      message.error('Failed to delete trigger');
    }
  };

  const handleToggleEnabled = async (trigger: Trigger, enabled: boolean) => {
    try {
      await api.patch(`/triggers/${trigger.id}`, { enabled });
      message.success(`Trigger ${enabled ? 'enabled' : 'disabled'}`);
      fetchTriggers();
    } catch {
      message.error('Failed to update trigger');
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <ThunderboltOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const config = TRIGGER_TYPES.find((t) => t.value === type);
        return (
          <Tag icon={config?.icon} color={type === 'cron' ? 'blue' : 'purple'}>
            {type}
          </Tag>
        );
      },
    },
    {
      title: 'Schedule/Event',
      key: 'schedule',
      render: (_: any, record: Trigger) => {
        if (record.type === 'cron') {
          return <Tag color="blue">{record.config?.cron || '-'}</Tag>;
        }
        return <Tag color="purple">{record.config?.event_type || '-'}</Tag>;
      },
    },
    {
      title: 'Target',
      key: 'target',
      render: (_: any, record: Trigger) => {
        const targetName =
          record.target_type === 'workflow'
            ? workflows.find((w) => w.id === record.target_id)?.name
            : record.target_type === 'agent'
            ? agents.find((a) => a.id === record.target_id)?.name
            : record.target_id;

        return (
          <Space>
            <Tag color="cyan">{record.target_type}</Tag>
            <Text>{targetName || record.target_id}</Text>
          </Space>
        );
      },
    },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record: Trigger) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleEnabled(record, checked)}
        />
      ),
    },
    {
      title: 'Last Triggered',
      dataIndex: 'last_triggered_at',
      key: 'last_triggered_at',
      width: 180,
      render: (date: string) => (date ? new Date(date).toLocaleString() : '-'),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: any, record: Trigger) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Delete this trigger?"
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
        <Title level={4} style={{ margin: 0 }}>Triggers</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create Trigger
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={triggers}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          expandable={{
            expandedRowRender: (record: Trigger) => (
              <Descriptions column={2} size="small" bordered>
                <Descriptions.Item label="Description" span={2}>
                  {record.description || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Trigger Type">{record.type}</Descriptions.Item>
                <Descriptions.Item label="Target Type">{record.target_type}</Descriptions.Item>
                <Descriptions.Item label="Created">
                  {new Date(record.created_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Next Trigger">
                  {record.next_trigger_at ? new Date(record.next_trigger_at).toLocaleString() : '-'}
                </Descriptions.Item>
                {record.type === 'cron' && (
                  <>
                    <Descriptions.Item label="Cron Expression" span={2}>
                      <code>{record.config?.cron || '-'}</code>
                    </Descriptions.Item>
                  </>
                )}
                {record.type === 'event' && (
                  <>
                    <Descriptions.Item label="Event Type" span={2}>
                      <code>{record.config?.event_type || '-'}</code>
                    </Descriptions.Item>
                    {record.config?.filters && (
                      <Descriptions.Item label="Filters" span={2}>
                        <pre style={{ margin: 0, fontSize: 12 }}>
                          {JSON.stringify(record.config.filters, null, 2)}
                        </pre>
                      </Descriptions.Item>
                    )}
                  </>
                )}
              </Descriptions>
            ),
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingTrigger ? 'Edit Trigger' : 'Create Trigger'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Trigger Name"
            rules={[{ required: true }]}
          >
            <Input placeholder="e.g., Daily Report Generator" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Describe what this trigger does" />
          </Form.Item>
          <Form.Item
            name="type"
            label="Trigger Type"
            rules={[{ required: true }]}
          >
            <Select>
              {TRIGGER_TYPES.map((type) => (
                <Select.Option key={type.value} value={type.value}>
                  {type.icon} {type.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.type !== curr.type}>
            {({ getFieldValue }) => {
              const type = getFieldValue('type');
              return type === 'cron' ? (
                <Form.Item
                  name={['config', 'cron']}
                  label="Cron Expression"
                  rules={[{ required: true }]}
                  help="Standard cron format: * * * * *"
                >
                  <Input placeholder="0 9 * * *" style={{ fontFamily: 'monospace' }} />
                </Form.Item>
              ) : (
                <>
                  <Form.Item
                    name={['config', 'event_type']}
                    label="Event Type"
                    rules={[{ required: true }]}
                  >
                    <Select placeholder="Select event type">
                      <Select.Option value="conversation.completed">Conversation Completed</Select.Option>
                      <Select.Option value="document.uploaded">Document Uploaded</Select.Option>
                      <Select.Option value="agent.published">Agent Published</Select.Option>
                      <Select.Option value="workflow.completed">Workflow Completed</Select.Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    name={['config', 'filters']}
                    label="Event Filters (JSON)"
                  >
                    <TextArea
                      rows={3}
                      placeholder='{"agent_id": "xxx", "status": "success"}'
                      style={{ fontFamily: 'monospace' }}
                    />
                  </Form.Item>
                </>
              );
            }}
          </Form.Item>

          <Divider orientation="left">Target</Divider>

          <Form.Item
            name="target_type"
            label="Target Type"
            rules={[{ required: true }]}
          >
            <Select>
              {TARGET_TYPES.map((type) => (
                <Select.Option key={type.value} value={type.value}>
                  {type.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.target_type !== curr.target_type}>
            {({ getFieldValue }) => {
              const targetType = getFieldValue('target_type');
              const options =
                targetType === 'workflow'
                  ? workflows
                  : targetType === 'agent'
                  ? agents
                  : [];

              return (
                <Form.Item
                  name="target_id"
                  label={`Target ${targetType}`}
                  rules={[{ required: true }]}
                >
                  <Select placeholder={`Select ${targetType}`}>
                    {options.map((item) => (
                      <Select.Option key={item.id} value={item.id}>
                        {item.name}
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>
              );
            }}
          </Form.Item>

          <Form.Item
            name="enabled"
            label="Enabled"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
