'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Button, Table, Modal, Form, Input, Select, Tag, Typography, message,
  Space, Popconfirm, Badge, Alert, Row, Col, Statistic
} from 'antd';
import {
  KeyOutlined, PlusOutlined, StopOutlined, CopyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

interface ApiToken {
  id: string;
  name: string;
  permissions: string[];
  expires_at: string;
  last_used_at: string | null;
  status: string;
  created_at: string;
  token_prefix?: string;
}

interface CreatedToken extends ApiToken {
  token: string;
}

const PERMISSION_OPTIONS = [
  { label: 'Agent - Read', value: 'agent:read' },
  { label: 'Agent - Create', value: 'agent:create' },
  { label: 'Agent - Update', value: 'agent:update' },
  { label: 'Agent - Delete', value: 'agent:delete' },
  { label: 'Knowledge - Read', value: 'knowledge:read' },
  { label: 'Knowledge - Create', value: 'knowledge:create' },
  { label: 'Chat - Send', value: 'chat:send' },
  { label: 'Workflow - Read', value: 'workflow:read' },
  { label: 'Workflow - Run', value: 'workflow:run' },
];

export default function TokensPage() {
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [createdToken, setCreatedToken] = useState<CreatedToken | null>(null);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const loadTokens = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listTokens();
      setTokens(Array.isArray(data) ? data : []);
    } catch {
      message.error('Failed to load tokens');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTokens();
  }, [loadTokens]);

  const handleCreate = async (values: { name: string; permissions: string[]; expiry_days: number }) => {
    setCreating(true);
    try {
      const result = await api.createToken(values);
      setCreatedToken(result);
      setShowCreateModal(false);
      setShowTokenModal(true);
      form.resetFields();
      message.success('Token created successfully');
      loadTokens();
    } catch {
      message.error('Failed to create token');
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (tokenId: string) => {
    try {
      await api.revokeToken(tokenId);
      message.success('Token revoked');
      loadTokens();
    } catch {
      message.error('Failed to revoke token');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Copied to clipboard');
  };

  const getStatusBadge = (status: string) => {
    if (status === 'active') return <Badge status="success" text="Active" />;
    if (status === 'revoked') return <Badge status="error" text="Revoked" />;
    return <Badge status="warning" text={status} />;
  };

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date();
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: ApiToken) => (
        <Space>
          <KeyOutlined style={{ color: record.status === 'active' ? '#1890ff' : '#999' }} />
          <Text strong>{name}</Text>
          {record.token_prefix && <Text type="secondary" code>{record.token_prefix}...</Text>}
        </Space>
      ),
    },
    {
      title: 'Permissions',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (perms: string[]) => (
        <Space wrap size={4}>
          {perms && perms.length > 0 ? perms.map(p => <Tag key={p} color="blue">{p}</Tag>) : <Tag color="green">Full Access</Tag>}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: ApiToken) => (
        <Space direction="vertical" size={0}>
          {getStatusBadge(status)}
          {status === 'active' && isExpired(record.expires_at) && (
            <Text type="danger" style={{ fontSize: 12 }}>Expired</Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Expires',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : 'Never',
    },
    {
      title: 'Last Used',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      render: (date: string | null) => date ? new Date(date).toLocaleString() : <Text type="secondary">Never</Text>,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: ApiToken) => (
        <Space>
          {record.status === 'active' && (
            <Popconfirm
              title="Revoke this token?"
              description="This action cannot be undone. Any applications using this token will lose access."
              onConfirm={() => handleRevoke(record.id)}
              okText="Revoke"
              cancelText="Cancel"
              okButtonProps={{ danger: true }}
            >
              <Button size="small" danger icon={<StopOutlined />}>Revoke</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  const activeTokens = tokens.filter(t => t.status === 'active');
  const revokedTokens = tokens.filter(t => t.status === 'revoked');

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}><KeyOutlined style={{ marginRight: 8 }} />API Keys</Title>
        <Paragraph type="secondary">
          Manage API keys for programmatic access to the platform. Tokens are shown only once at creation.
        </Paragraph>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="Total Tokens" value={tokens.length} prefix={<KeyOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Active" value={activeTokens.length} valueStyle={{ color: '#3f8600' }} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Revoked" value={revokedTokens.length} valueStyle={{ color: '#cf1322' }} prefix={<StopOutlined />} />
          </Card>
        </Col>
      </Row>

      <Card
        title="API Tokens"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>
            Create Token
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tokens}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* Create Token Modal */}
      <Modal
        title="Create API Token"
        open={showCreateModal}
        onCancel={() => setShowCreateModal(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ expiry_days: 30, permissions: [] }}>
          <Form.Item name="name" label="Token Name" rules={[{ required: true, message: 'Please enter a name' }]}>
            <Input placeholder="e.g., CI/CD Pipeline, Development Key" />
          </Form.Item>
          <Form.Item name="permissions" label="Permissions">
            <Select
              mode="multiple"
              placeholder="Select permissions (leave empty for full access)"
              options={PERMISSION_OPTIONS}
              allowClear
            />
          </Form.Item>
          <Form.Item name="expiry_days" label="Expiration (days)">
            <Select options={[
              { label: '7 days', value: 7 },
              { label: '30 days', value: 30 },
              { label: '90 days', value: 90 },
              { label: '365 days', value: 365 },
            ]} />
          </Form.Item>
          <Alert
            message="Important"
            description="The token will be shown only once. Copy it immediately and store it securely."
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={creating}>Create Token</Button>
              <Button onClick={() => setShowCreateModal(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Show Created Token Modal */}
      <Modal
        title="Token Created Successfully"
        open={showTokenModal}
        onCancel={() => { setShowTokenModal(false); setCreatedToken(null); }}
        footer={[
          <Button key="close" onClick={() => { setShowTokenModal(false); setCreatedToken(null); }}>
            Close
          </Button>,
        ]}
        width={600}
      >
        {createdToken && (
          <div>
            <Alert
              message="Copy your token now"
              description="This is the only time you'll see this token. Store it securely."
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <div style={{ marginBottom: 16 }}>
              <Text strong>Name:</Text> {createdToken.name}
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Token:</Text>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginTop: 8,
                padding: 12,
                background: '#f5f5f5',
                borderRadius: 6,
                border: '1px solid #d9d9d9'
              }}>
                <Text code style={{ flex: 1, wordBreak: 'break-all' }}>{createdToken.token}</Text>
                <Button
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(createdToken.token)}
                  size="small"
                />
              </div>
            </div>
            <div>
              <Text strong>Expires:</Text> {new Date(createdToken.expires_at).toLocaleString()}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
