'use client';
import React, { useState } from 'react';
import {
  Card, Table, Tag, Button, Space, Typography, Skeleton, Switch, Modal,
  Form, Input, InputNumber, Select, message, Popconfirm, Tooltip, Badge,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  BellOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';
import type { AlertRule } from '@/app/(platform)/observability/page';

const { Text } = Typography;

interface Props {
  rules: AlertRule[];
  loading: boolean;
  onRefresh: () => void;
}

const severityConfig: Record<string, { color: string; label: string }> = {
  critical: { color: 'red', label: 'Critical' },
  warning: { color: 'orange', label: 'Warning' },
  info: { color: 'blue', label: 'Info' },
};

const metricOptions = [
  { value: 'qps', label: 'QPS' },
  { value: 'latency_p50', label: 'P50 Latency' },
  { value: 'latency_p90', label: 'P90 Latency' },
  { value: 'latency_p99', label: 'P99 Latency' },
  { value: 'error_rate', label: 'Error Rate (%)' },
  { value: 'error_count', label: 'Error Count' },
  { value: 'request_count', label: 'Request Count' },
];

const conditionOptions = [
  { value: 'gt', label: 'Greater than (>)' },
  { value: 'gte', label: 'Greater or equal (>=)' },
  { value: 'lt', label: 'Less than (<)' },
  { value: 'lte', label: 'Less or equal (<=)' },
  { value: 'eq', label: 'Equal to (=)' },
];

const durationOptions = [
  { value: '1m', label: '1 minute' },
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
];

const channelOptions = [
  { value: 'email', label: 'Email' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'slack', label: 'Slack' },
  { value: 'dingtalk', label: 'DingTalk' },
];

export default function AlertRules({ rules, loading, onRefresh }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const openCreate = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      severity: 'warning',
      condition: 'gt',
      duration: '5m',
      enabled: true,
      notify_channels: ['email'],
    });
    setModalOpen(true);
  };

  const openEdit = (rule: AlertRule) => {
    setEditingRule(rule);
    form.setFieldsValue(rule);
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingRule) {
        await api.put(`/observability/alerts/${editingRule.id}`, values);
        message.success('Alert rule updated');
      } else {
        await api.post('/observability/alerts', values);
        message.success('Alert rule created');
      }
      setModalOpen(false);
      onRefresh();
    } catch (err: any) {
      if (err?.errorFields) return; // form validation error
      message.error('Failed to save alert rule');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/observability/alerts/${id}`);
      message.success('Alert rule deleted');
      onRefresh();
    } catch {
      message.error('Failed to delete alert rule');
    }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await api.put(`/observability/alerts/${id}`, { enabled });
      message.success(enabled ? 'Alert enabled' : 'Alert disabled');
      onRefresh();
    } catch {
      message.error('Failed to update alert rule');
    }
  };

  const conditionLabel = (cond: string, threshold: number) => {
    const condMap: Record<string, string> = {
      gt: '>',
      gte: '>=',
      lt: '<',
      lte: '<=',
      eq: '=',
    };
    return `${condMap[cond] || cond} ${threshold}`;
  };

  const columns: ColumnsType<AlertRule> = [
    {
      title: 'Status',
      key: 'enabled',
      width: 80,
      align: 'center',
      render: (_, record) => (
        <Switch
          size="small"
          checked={record.enabled}
          onChange={(checked) => handleToggle(record.id, checked)}
        />
      ),
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <Space>
          <Text strong>{name}</Text>
          {!record.enabled && <Tag>Disabled</Tag>}
        </Space>
      ),
    },
    {
      title: 'Metric',
      dataIndex: 'metric',
      key: 'metric',
      width: 150,
      render: (metric: string) => {
        const opt = metricOptions.find((o) => o.value === metric);
        return <Tag color="geekblue">{opt?.label || metric}</Tag>;
      },
    },
    {
      title: 'Condition',
      key: 'condition',
      width: 140,
      render: (_, record) => (
        <Text code>{conditionLabel(record.condition, record.threshold)}</Text>
      ),
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => {
        const cfg = severityConfig[severity] || severityConfig.info;
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: 'Notify',
      dataIndex: 'notify_channels',
      key: 'notify_channels',
      width: 180,
      render: (channels: string[]) => (
        <Space size={4} wrap>
          {channels?.map((ch) => <Tag key={ch}>{ch}</Tag>)}
        </Space>
      ),
    },
    {
      title: 'Last Triggered',
      dataIndex: 'last_triggered',
      key: 'last_triggered',
      width: 170,
      render: (t?: string) => t ? (
        <Tooltip title={new Date(t).toLocaleString()}>
          <Text type="secondary">{new Date(t).toLocaleString()}</Text>
        </Tooltip>
      ) : <Text type="secondary">Never</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
          />
          <Popconfirm
            title="Delete this alert rule?"
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            cancelText="Cancel"
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Card bordered={false}>
          <Skeleton active paragraph={{ rows: 6 }} />
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card
        bordered={false}
        title={
          <Space>
            <BellOutlined />
            <Text strong>Alert Rules</Text>
            <Badge count={rules.filter((r) => r.enabled).length} style={{ backgroundColor: '#52c41a' }} />
            <Text type="secondary">active</Text>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            New Alert Rule
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={rules}
          rowKey="id"
          pagination={{ pageSize: 10, showTotal: (t) => `Total ${t} rules` }}
          size="middle"
          scroll={{ x: 1100 }}
        />
      </Card>

      <Modal
        title={editingRule ? 'Edit Alert Rule' : 'New Alert Rule'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        okText={editingRule ? 'Update' : 'Create'}
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="Rule Name"
            rules={[{ required: true, message: 'Please enter a rule name' }]}
          >
            <Input placeholder="e.g. High Error Rate Alert" />
          </Form.Item>

          <Space size={16} style={{ display: 'flex' }}>
            <Form.Item
              name="metric"
              label="Metric"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
            >
              <Select options={metricOptions} placeholder="Select metric" />
            </Form.Item>

            <Form.Item
              name="condition"
              label="Condition"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
            >
              <Select options={conditionOptions} />
            </Form.Item>

            <Form.Item
              name="threshold"
              label="Threshold"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} placeholder="100" />
            </Form.Item>
          </Space>

          <Space size={16} style={{ display: 'flex' }}>
            <Form.Item
              name="duration"
              label="Duration"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
            >
              <Select options={durationOptions} />
            </Form.Item>

            <Form.Item
              name="severity"
              label="Severity"
              rules={[{ required: true }]}
              style={{ flex: 1 }}
            >
              <Select
                options={[
                  { value: 'critical', label: 'Critical' },
                  { value: 'warning', label: 'Warning' },
                  { value: 'info', label: 'Info' },
                ]}
              />
            </Form.Item>
          </Space>

          <Form.Item
            name="notify_channels"
            label="Notification Channels"
            rules={[{ required: true, message: 'Select at least one channel' }]}
          >
            <Select mode="multiple" options={channelOptions} placeholder="Select channels" />
          </Form.Item>

          <Form.Item name="enabled" label="Enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
