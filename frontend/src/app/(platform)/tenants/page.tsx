'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, message, Spin, Descriptions, Drawer, Statistic, Row, Col,
  Progress, InputNumber, Divider,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, TeamOutlined,
  UserOutlined, DatabaseOutlined, RobotOutlined, BarChartOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Tenant {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'suspended' | 'trial';
  quota?: TenantQuota;
  usage?: TenantUsage;
  created_at: string;
  updated_at: string;
}

interface TenantQuota {
  max_agents: number;
  max_knowledge_bases: number;
  max_workflows: number;
  max_users: number;
  storage_gb: number;
  api_calls_per_month: number;
}

interface TenantUsage {
  agents: number;
  knowledge_bases: number;
  workflows: number;
  users: number;
  storage_gb: number;
  api_calls_this_month: number;
}

const STATUS_COLORS: Record<string, string> = {
  active: 'success',
  suspended: 'error',
  trial: 'warning',
};

const DEFAULT_QUOTA: TenantQuota = {
  max_agents: 10,
  max_knowledge_bases: 5,
  max_workflows: 10,
  max_users: 5,
  storage_gb: 10,
  api_calls_per_month: 10000,
};

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);

  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  // Detail drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  const fetchTenants = useCallback(() => {
    setLoading(true);
    api.get<Tenant[]>('/tenants')
      .then(setTenants)
      .catch(() => message.error('Failed to load tenants'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchTenants(); }, [fetchTenants]);

  const handleCreate = () => {
    setEditingTenant(null);
    form.resetFields();
    form.setFieldsValue({
      status: 'trial',
      quota: DEFAULT_QUOTA,
    });
    setModalOpen(true);
  };

  const handleEdit = (tenant: Tenant) => {
    setEditingTenant(tenant);
    form.setFieldsValue({
      name: tenant.name,
      description: tenant.description,
      status: tenant.status,
      quota: tenant.quota || DEFAULT_QUOTA,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingTenant) {
        await api.put(`/tenants/${editingTenant.id}`, values);
        message.success('Tenant updated');
      } else {
        await api.post('/tenants', values);
        message.success('Tenant created');
      }

      setModalOpen(false);
      form.resetFields();
      fetchTenants();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error(editingTenant ? 'Failed to update tenant' : 'Failed to create tenant');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/tenants/${id}`);
      message.success('Tenant deleted');
      fetchTenants();
    } catch {
      message.error('Failed to delete tenant');
    }
  };

  const handleViewDetails = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setDrawerOpen(true);
  };

  const getUsagePercent = (used: number, max: number) => {
    if (max === 0) return 0;
    return Math.round((used / max) * 100);
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
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <Tag color={STATUS_COLORS[status]}>{status}</Tag>,
    },
    {
      title: 'Users',
      key: 'users',
      width: 100,
      render: (_: any, record: Tenant) => {
        const usage = record.usage?.users || 0;
        const quota = record.quota?.max_users || 5;
        const percent = getUsagePercent(usage, quota);
        return `${usage}/${quota}`;
      },
    },
    {
      title: 'Agents',
      key: 'agents',
      width: 100,
      render: (_: any, record: Tenant) => {
        const usage = record.usage?.agents || 0;
        const quota = record.quota?.max_agents || 10;
        const percent = getUsagePercent(usage, quota);
        return `${usage}/${quota}`;
      },
    },
    {
      title: 'Storage',
      key: 'storage',
      width: 120,
      render: (_: any, record: Tenant) => {
        const usage = record.usage?.storage_gb || 0;
        const quota = record.quota?.storage_gb || 10;
        const percent = getUsagePercent(usage, quota);
        return `${usage.toFixed(1)}GB/${quota}GB`;
      },
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
      render: (_: any, record: Tenant) => (
        <Space>
          <Button
            size="small"
            icon={<BarChartOutlined />}
            onClick={() => handleViewDetails(record)}
          >
            Details
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Delete this tenant?"
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
        <Title level={4} style={{ margin: 0 }}>Tenants</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create Tenant
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={tenants}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingTenant ? 'Edit Tenant' : 'Create Tenant'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Tenant Name"
            rules={[{ required: true }]}
          >
            <Input placeholder="e.g., Acme Corp" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Describe this tenant" />
          </Form.Item>
          <Form.Item
            name="status"
            label="Status"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="trial">Trial</Select.Option>
              <Select.Option value="active">Active</Select.Option>
              <Select.Option value="suspended">Suspended</Select.Option>
            </Select>
          </Form.Item>

          <Divider orientation="left">Quotas</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name={['quota', 'max_agents']}
                label="Max Agents"
                initialValue={10}
              >
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['quota', 'max_knowledge_bases']}
                label="Max Knowledge Bases"
                initialValue={5}
              >
                <InputNumber min={1} max={500} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name={['quota', 'max_workflows']}
                label="Max Workflows"
                initialValue={10}
              >
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['quota', 'max_users']}
                label="Max Users"
                initialValue={5}
              >
                <InputNumber min={1} max={500} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name={['quota', 'storage_gb']}
                label="Storage (GB)"
                initialValue={10}
              >
                <InputNumber min={1} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['quota', 'api_calls_per_month']}
                label="API Calls / Month"
                initialValue={10000}
              >
                <InputNumber min={100} max={10000000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Details Drawer */}
      <Drawer
        title={`Tenant Details: ${selectedTenant?.name || ''}`}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={700}
      >
        {selectedTenant && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="ID" span={2}>{selectedTenant.id}</Descriptions.Item>
              <Descriptions.Item label="Status" span={2}>
                <Tag color={STATUS_COLORS[selectedTenant.status]}>{selectedTenant.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>
                {selectedTenant.description || 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Created">
                {new Date(selectedTenant.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Updated">
                {new Date(selectedTenant.updated_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            <Divider>Usage Overview</Divider>

            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Users"
                    value={selectedTenant.usage?.users || 0}
                    suffix={`/ ${selectedTenant.quota?.max_users || 5}`}
                    prefix={<UserOutlined />}
                  />
                  <Progress
                    percent={getUsagePercent(
                      selectedTenant.usage?.users || 0,
                      selectedTenant.quota?.max_users || 5
                    )}
                    size="small"
                    status={
                      getUsagePercent(
                        selectedTenant.usage?.users || 0,
                        selectedTenant.quota?.max_users || 5
                      ) > 90
                        ? 'exception'
                        : 'normal'
                    }
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Agents"
                    value={selectedTenant.usage?.agents || 0}
                    suffix={`/ ${selectedTenant.quota?.max_agents || 10}`}
                    prefix={<RobotOutlined />}
                  />
                  <Progress
                    percent={getUsagePercent(
                      selectedTenant.usage?.agents || 0,
                      selectedTenant.quota?.max_agents || 10
                    )}
                    size="small"
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Knowledge Bases"
                    value={selectedTenant.usage?.knowledge_bases || 0}
                    suffix={`/ ${selectedTenant.quota?.max_knowledge_bases || 5}`}
                    prefix={<DatabaseOutlined />}
                  />
                  <Progress
                    percent={getUsagePercent(
                      selectedTenant.usage?.knowledge_bases || 0,
                      selectedTenant.quota?.max_knowledge_bases || 5
                    )}
                    size="small"
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={12}>
                <Card size="small">
                  <Statistic
                    title="Storage"
                    value={selectedTenant.usage?.storage_gb || 0}
                    precision={1}
                    suffix={`GB / ${selectedTenant.quota?.storage_gb || 10} GB`}
                  />
                  <Progress
                    percent={getUsagePercent(
                      selectedTenant.usage?.storage_gb || 0,
                      selectedTenant.quota?.storage_gb || 10
                    )}
                    size="small"
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small">
                  <Statistic
                    title="API Calls (This Month)"
                    value={selectedTenant.usage?.api_calls_this_month || 0}
                    suffix={`/ ${selectedTenant.quota?.api_calls_per_month || 10000}`}
                  />
                  <Progress
                    percent={getUsagePercent(
                      selectedTenant.usage?.api_calls_this_month || 0,
                      selectedTenant.quota?.api_calls_per_month || 10000
                    )}
                    size="small"
                  />
                </Card>
              </Col>
            </Row>

            <Card title="Quota Details" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Max Workflows">
                  {selectedTenant.quota?.max_workflows || 10}
                </Descriptions.Item>
                <Descriptions.Item label="Used">
                  {selectedTenant.usage?.workflows || 0}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </>
        )}
      </Drawer>
    </div>
  );
}
