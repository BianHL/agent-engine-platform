'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Button, Select, Input, Typography, Tag, Table,
  Modal, Form, Switch, message, Badge, Space, Row, Col,
  Alert, Popconfirm, Statistic
} from 'antd';
import {
  RocketOutlined, LinkOutlined, CodeOutlined, GlobalOutlined,
  ApiOutlined, CopyOutlined, DeleteOutlined, PlusOutlined
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

interface PublishChannel {
  id: string;
  agent_id: string;
  type: 'api' | 'webapp' | 'iframe' | 'wechat' | 'feishu' | 'discord';
  name: string;
  status: 'active' | 'inactive';
  config: Record<string, any>;
  api_key_prefix?: string;
  total_calls: number;
  calls_today: number;
  created_at: string;
}

export default function PublishPage() {
  const [channels, setChannels] = useState<PublishChannel[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newChannelKey, setNewChannelKey] = useState<string>('');
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [channelsData, agentsData] = await Promise.all([
        api.listPublishChannels(),
        api.listAgents(1, 100),
      ]);
      setChannels(Array.isArray(channelsData) ? channelsData : []);
      setAgents(agentsData.items || agentsData || []);
    } catch {
      message.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (values: any) => {
    setCreating(true);
    try {
      const result = await api.createPublishChannel({
        agent_id: values.agent_id,
        type: values.type,
        name: values.name,
      });
      message.success('Channel created');
      setShowCreateModal(false);
      form.resetFields();

      if (values.type === 'api' && result.config?.api_key) {
        setNewChannelKey(result.config.api_key);
        setShowKeyModal(true);
      }

      loadData();
    } catch {
      message.error('Failed to create channel');
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (channel: PublishChannel, checked: boolean) => {
    try {
      await api.updatePublishChannel(channel.id, {
        status: checked ? 'active' : 'inactive',
      });
      message.success(`Channel ${checked ? 'activated' : 'deactivated'}`);
      loadData();
    } catch {
      message.error('Failed to update channel');
    }
  };

  const handleDelete = async (channelId: string) => {
    try {
      await api.deletePublishChannel(channelId);
      message.success('Channel deleted');
      loadData();
    } catch {
      message.error('Failed to delete channel');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Copied');
  };

  const getBaseUrl = () => {
    if (typeof window !== 'undefined') {
      return window.location.origin;
    }
    return 'https://api.example.com';
  };

  const getChannelIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      api: <ApiOutlined />, webapp: <GlobalOutlined />, iframe: <CodeOutlined />,
      wechat: '💬', feishu: '🐦', discord: '🎮'
    };
    return icons[type] || <LinkOutlined />;
  };

  const getChannelColor = (type: string) => {
    const colors: Record<string, string> = {
      api: 'blue', webapp: 'green', iframe: 'purple', wechat: 'cyan', feishu: 'orange', discord: 'magenta'
    };
    return colors[type] || 'default';
  };

  const totalCalls = channels.reduce((sum, c) => sum + (c.total_calls || 0), 0);
  const callsToday = channels.reduce((sum, c) => sum + (c.calls_today || 0), 0);

  const columns = [
    {
      title: 'Channel',
      dataIndex: 'type',
      key: 'type',
      render: (type: string, record: PublishChannel) => (
        <Space>
          {getChannelIcon(type)}
          <div>
            <Text strong>{record.name}</Text><br />
            <Tag color={getChannelColor(type)}>{type.toUpperCase()}</Tag>
            {record.api_key_prefix && <Text type="secondary" code>{record.api_key_prefix}...</Text>}
          </div>
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) =>
        status === 'active'
          ? <Badge status="success" text="Active" />
          : <Badge status="default" text="Inactive" />,
    },
    {
      title: 'Calls',
      key: 'calls',
      render: (_: any, record: PublishChannel) => (
        <span>{record.total_calls || 0} total / {record.calls_today || 0} today</span>
      ),
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
      render: (_: any, record: PublishChannel) => (
        <Space>
          {record.type === 'api' && record.api_key_prefix && (
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => {
                const endpoint = `${getBaseUrl()}/api/v1/chat/completions`;
                copyToClipboard(endpoint);
              }}
            >
              Copy Endpoint
            </Button>
          )}
          {record.type === 'iframe' && (
            <Button
              size="small"
              icon={<CodeOutlined />}
              onClick={() => {
                const code = `<iframe src="${getBaseUrl()}/embed?agent=${record.agent_id}" width="400" height="600" frameborder="0"></iframe>`;
                copyToClipboard(code);
              }}
            >
              Copy Embed
            </Button>
          )}
          <Switch
            checked={record.status === 'active'}
            onChange={(checked) => handleToggle(record, checked)}
          />
          <Popconfirm
            title="Delete this channel?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}><RocketOutlined style={{ marginRight: 8 }} />Publish</Title>
        <Paragraph type="secondary">
          Publish your Agents as APIs, Web Apps, or embed them in other platforms.
        </Paragraph>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card><Statistic title="Channels" value={channels.length} prefix={<RocketOutlined />} /></Card>
        </Col>
        <Col span={8}>
          <Card><Statistic title="Active" value={channels.filter(c => c.status === 'active').length} valueStyle={{ color: '#3f8600' }} /></Card>
        </Col>
        <Col span={8}>
          <Card><Statistic title="Calls Today" value={callsToday} /></Card>
        </Col>
      </Row>

      <Card
        title="Publish Channels"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>
            New Channel
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={channels}
          rowKey="id"
          loading={loading}
          locale={{ emptyText: 'No channels yet. Create one to get started.' }}
        />
      </Card>

      {/* Create Channel Modal */}
      <Modal
        title="Create Publish Channel"
        open={showCreateModal}
        onCancel={() => setShowCreateModal(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="agent_id" label="Agent" rules={[{ required: true, message: 'Select an agent' }]}>
            <Select
              placeholder="Select an agent"
              showSearch
              optionFilterProp="label"
              options={agents.map((a: any) => ({
                value: a.id,
                label: a.name,
              }))}
            />
          </Form.Item>
          <Form.Item name="type" label="Channel Type" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'api', label: '🔗 API Endpoint' },
                { value: 'webapp', label: '🌐 Web App' },
                { value: 'iframe', label: '📦 Embed (iframe)' },
                { value: 'wechat', label: '💬 WeChat Work' },
                { value: 'feishu', label: '🐦 Feishu' },
                { value: 'discord', label: '🎮 Discord' },
              ]}
            />
          </Form.Item>
          <Form.Item name="name" label="Channel Name" rules={[{ required: true, message: 'Enter a name' }]}>
            <Input placeholder="e.g., Production API" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={creating}>Create Channel</Button>
              <Button onClick={() => setShowCreateModal(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* API Key Display Modal */}
      <Modal
        title="API Key Created"
        open={showKeyModal}
        onCancel={() => { setShowKeyModal(false); setNewChannelKey(''); }}
        footer={[
          <Button key="close" onClick={() => { setShowKeyModal(false); setNewChannelKey(''); }}>Close</Button>,
        ]}
      >
        <Alert
          message="Copy your API key now"
          description="This key will not be shown again."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: 12,
          background: '#f5f5f5', borderRadius: 6, border: '1px solid #d9d9d9'
        }}>
          <Text code style={{ flex: 1, wordBreak: 'break-all' }}>{newChannelKey}</Text>
          <Button icon={<CopyOutlined />} onClick={() => copyToClipboard(newChannelKey)} size="small" />
        </div>
      </Modal>
    </div>
  );
}
