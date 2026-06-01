'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, message, Spin, Switch, Descriptions, Badge, Tabs, List,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, ApiOutlined,
  GlobalOutlined, SafetyOutlined, RocketOutlined, HistoryOutlined,
  CheckCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Webhook {
  id: string;
  name: string;
  description?: string;
  url: string;
  method: 'POST' | 'GET' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  enabled: boolean;
  secret?: string;
  events: string[];
  created_at: string;
  updated_at: string;
  last_triggered_at?: string;
  success_count: number;
  failure_count: number;
}

interface WebhookDelivery {
  id: string;
  webhook_id: string;
  status: 'success' | 'failed' | 'pending';
  response_status?: number;
  created_at: string;
  request_payload?: Record<string, any>;
  response_body?: string;
  error?: string;
}

const HTTP_METHODS = ['POST', 'GET', 'PUT', 'PATCH'];
const EVENT_TYPES = [
  'conversation.completed',
  'document.uploaded',
  'agent.published',
  'workflow.completed',
  'evaluation.completed',
  'trigger.fired',
];

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('webhooks');

  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<Webhook | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  // Test modal
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [testingWebhook, setTestingWebhook] = useState<Webhook | null>(null);
  const [testPayload, setTestPayload] = useState('{}');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const fetchWebhooks = useCallback(() => {
    setLoading(true);
    api.get<Webhook[]>('/webhooks')
      .then(setWebhooks)
      .catch(() => message.error('Failed to load webhooks'))
      .finally(() => setLoading(false));
  }, []);

  const fetchDeliveries = useCallback(() => {
    api.get<WebhookDelivery[]>('/webhooks/deliveries')
      .then(setDeliveries)
      .catch(() => message.error('Failed to load delivery history'));
  }, []);

  useEffect(() => {
    fetchWebhooks();
    fetchDeliveries();
  }, [fetchWebhooks, fetchDeliveries]);

  const handleCreate = () => {
    setEditingWebhook(null);
    form.resetFields();
    form.setFieldsValue({
      method: 'POST',
      enabled: true,
      events: [],
      headers: { 'Content-Type': 'application/json' },
    });
    setModalOpen(true);
  };

  const handleEdit = (webhook: Webhook) => {
    setEditingWebhook(webhook);
    form.setFieldsValue({
      name: webhook.name,
      description: webhook.description,
      url: webhook.url,
      method: webhook.method,
      headers: webhook.headers || { 'Content-Type': 'application/json' },
      enabled: webhook.enabled,
      events: webhook.events,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      // Parse headers JSON if provided as string
      if (typeof values.headers === 'string') {
        try {
          values.headers = JSON.parse(values.headers);
        } catch {
          message.error('Invalid JSON in headers');
          setSubmitting(false);
          return;
        }
      }

      if (editingWebhook) {
        await api.put(`/webhooks/${editingWebhook.id}`, values);
        message.success('Webhook updated');
      } else {
        await api.post('/webhooks', values);
        message.success('Webhook created');
      }

      setModalOpen(false);
      form.resetFields();
      fetchWebhooks();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error(editingWebhook ? 'Failed to update webhook' : 'Failed to create webhook');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/webhooks/${id}`);
      message.success('Webhook deleted');
      fetchWebhooks();
    } catch {
      message.error('Failed to delete webhook');
    }
  };

  const handleToggleEnabled = async (webhook: Webhook, enabled: boolean) => {
    try {
      await api.patch(`/webhooks/${webhook.id}`, { enabled });
      message.success(`Webhook ${enabled ? 'enabled' : 'disabled'}`);
      fetchWebhooks();
    } catch {
      message.error('Failed to update webhook');
    }
  };

  const handleTest = async () => {
    if (!testingWebhook) return;

    setTesting(true);
    setTestResult(null);

    try {
      const payload = JSON.parse(testPayload);
      const result = await api.post(`/webhooks/${testingWebhook.id}/test`, payload);
      setTestResult(result);
      message.success('Test delivery completed');
    } catch (e: any) {
      setTestResult({ error: e.message || 'Test failed' });
      message.error('Test delivery failed');
    } finally {
      setTesting(false);
    }
  };

  const webhookColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <GlobalOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
      render: (url: string) => (
        <Text code style={{ fontSize: 12 }}>{url}</Text>
      ),
    },
    {
      title: 'Method',
      dataIndex: 'method',
      key: 'method',
      width: 80,
      render: (method: string) => <Tag color="blue">{method}</Tag>,
    },
    {
      title: 'Events',
      dataIndex: 'events',
      key: 'events',
      render: (events: string[]) => (
        <Space size="small" wrap>
          {events?.slice(0, 2).map((e) => (
            <Tag key={e} color="purple">
              {e.split('.')[0]}
            </Tag>
          ))}
          {events?.length > 2 && <Tag>+{events.length - 2}</Tag>}
        </Space>
      ),
    },
    {
      title: 'Success Rate',
      key: 'success_rate',
      width: 120,
      render: (_: any, record: Webhook) => {
        const total = record.success_count + record.failure_count;
        if (total === 0) return <Tag color="default">No data</Tag>;
        const rate = (record.success_count / total) * 100;
        return (
          <Tag color={rate >= 90 ? 'success' : rate >= 70 ? 'warning' : 'error'}>
            {rate.toFixed(0)}%
          </Tag>
        );
      },
    },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record: Webhook) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleEnabled(record, checked)}
        />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_: any, record: Webhook) => (
        <Space>
          <Button
            size="small"
            icon={<RocketOutlined />}
            onClick={() => {
              setTestingWebhook(record);
              setTestPayload('{\n  "test": true\n}');
              setTestResult(null);
              setTestModalOpen(true);
            }}
          >
            Test
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Delete this webhook?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const deliveryColumns = [
    {
      title: 'Webhook',
      dataIndex: 'webhook_id',
      key: 'webhook_id',
      render: (id: string) => {
        const webhook = webhooks.find((w) => w.id === id);
        return webhook?.name || id;
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const color = status === 'success' ? 'success' : status === 'failed' ? 'error' : 'default';
        const icon = status === 'success' ? <CheckCircleOutlined /> : status === 'failed' ? <CloseCircleOutlined /> : null;
        return (
          <Tag icon={icon} color={color}>
            {status}
          </Tag>
        );
      },
    },
    {
      title: 'Response Status',
      dataIndex: 'response_status',
      key: 'response_status',
      width: 120,
      render: (status: number | undefined) => status ? <Tag color="blue">{status}</Tag> : '-',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Webhooks</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create Webhook
        </Button>
      </div>

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'webhooks',
              label: `Webhooks (${webhooks.length})`,
              children: (
                <Table
                  columns={webhookColumns}
                  dataSource={webhooks}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 20 }}
                  expandable={{
                    expandedRowRender: (record: Webhook) => (
                      <Descriptions column={2} size="small" bordered>
                        <Descriptions.Item label="Description" span={2}>
                          {record.description || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label="URL" span={2}>
                          <Text code>{record.url}</Text>
                        </Descriptions.Item>
                        <Descriptions.Item label="Method">{record.method}</Descriptions.Item>
                        <Descriptions.Item label="Last Triggered">
                          {record.last_triggered_at
                            ? new Date(record.last_triggered_at).toLocaleString()
                            : 'Never'}
                        </Descriptions.Item>
                        <Descriptions.Item label="Success Count">
                          <Tag color="success">{record.success_count}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Failure Count">
                          <Tag color="error">{record.failure_count}</Tag>
                        </Descriptions.Item>
                        {record.secret && (
                          <Descriptions.Item label="Secret" span={2}>
                            <Text code>••••••••</Text>
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    ),
                  }}
                />
              ),
            },
            {
              key: 'deliveries',
              label: `Delivery History (${deliveries.length})`,
              children: (
                <Table
                  columns={deliveryColumns}
                  dataSource={deliveries}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 20 }}
                  expandable={{
                    expandedRowRender: (record: WebhookDelivery) => (
                      <Card size="small">
                        <div style={{ marginBottom: 8 }}>
                          <Text strong>Request Payload:</Text>
                          <pre style={{
                            background: '#f6f8fa',
                            padding: 8,
                            borderRadius: 4,
                            margin: '8px 0',
                            fontSize: 12,
                            maxHeight: 200,
                            overflow: 'auto',
                          }}>
                            {JSON.stringify(record.request_payload, null, 2)}
                          </pre>
                        </div>
                        {record.response_body && (
                          <div>
                            <Text strong>Response:</Text>
                            <pre style={{
                              background: '#f6f8fa',
                              padding: 8,
                              borderRadius: 4,
                              margin: '8px 0',
                              fontSize: 12,
                              maxHeight: 200,
                              overflow: 'auto',
                            }}>
                              {record.response_body}
                            </pre>
                          </div>
                        )}
                        {record.error && (
                          <div>
                            <Text strong type="danger">Error:</Text>
                            <Text type="danger">{record.error}</Text>
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

      {/* Create/Edit Modal */}
      <Modal
        title={editingWebhook ? 'Edit Webhook' : 'Create Webhook'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Webhook Name"
            rules={[{ required: true }]}
          >
            <Input placeholder="e.g., Slack Notifications" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Describe this webhook" />
          </Form.Item>
          <Form.Item
            name="url"
            label="Endpoint URL"
            rules={[
              { required: true },
              { type: 'url', message: 'Please enter a valid URL' },
            ]}
          >
            <Input placeholder="https://api.example.com/webhook" />
          </Form.Item>
          <Form.Item
            name="method"
            label="HTTP Method"
            rules={[{ required: true }]}
          >
            <Select>
              {HTTP_METHODS.map((method) => (
                <Select.Option key={method} value={method}>
                  {method}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="headers"
            label="Headers (JSON)"
            help="Custom headers to send with the webhook"
          >
            <TextArea
              rows={3}
              placeholder='{"Authorization": "Bearer xxx"}'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
          <Form.Item
            name="events"
            label="Events"
            rules={[{ required: true, type: 'array', min: 1 }]}
          >
            <Select mode="multiple" placeholder="Select events to trigger this webhook">
              {EVENT_TYPES.map((event) => (
                <Select.Option key={event} value={event}>
                  {event}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="secret"
            label="Secret (optional)"
            help="Used to verify webhook signatures"
          >
            <Input.Password placeholder="Webhook signing secret" />
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

      {/* Test Modal */}
      <Modal
        title={`Test Webhook: ${testingWebhook?.name || ''}`}
        open={testModalOpen}
        onCancel={() => setTestModalOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setTestModalOpen(false)}>Close</Button>,
          <Button
            key="test"
            type="primary"
            icon={<RocketOutlined />}
            loading={testing}
            onClick={handleTest}
          >
            Send Test
          </Button>,
        ]}
        width={700}
      >
        {testingWebhook && (
          <>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="URL">{testingWebhook.url}</Descriptions.Item>
              <Descriptions.Item label="Method">{testingWebhook.method}</Descriptions.Item>
            </Descriptions>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Test Payload (JSON):</Text>
              <TextArea
                rows={6}
                value={testPayload}
                onChange={(e) => setTestPayload(e.target.value)}
                style={{ fontFamily: 'monospace', marginTop: 8 }}
              />
            </div>
            {testResult && (
              <>
                <Text strong>Result:</Text>
                <pre style={{
                  background: testResult.error ? '#fff1f0' : '#f6f8fa',
                  padding: 12,
                  borderRadius: 6,
                  marginTop: 8,
                  maxHeight: 300,
                  overflow: 'auto',
                  fontSize: 12,
                }}>
                  {JSON.stringify(testResult, null, 2)}
                </pre>
              </>
            )}
          </>
        )}
      </Modal>
    </div>
  );
}
