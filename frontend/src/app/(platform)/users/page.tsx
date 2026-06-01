'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input, Select,
  Popconfirm, message, Spin, Descriptions, Avatar, Badge,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, UserOutlined,
  MailOutlined, SafetyOutlined, TeamOutlined, LockOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface User {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  role: string;
  role_name?: string;
  tenant_id: string;
  tenant_name?: string;
  status: 'active' | 'inactive' | 'pending';
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

interface Role {
  id: string;
  name: string;
  description?: string;
}

interface Tenant {
  id: string;
  name: string;
}

const STATUS_COLORS: Record<string, string> = {
  active: 'success',
  inactive: 'default',
  pending: 'warning',
};

const ROLE_COLORS: Record<string, string> = {
  admin: 'red',
  user: 'blue',
  operator: 'green',
  viewer: 'default',
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);

  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  // Password reset modal
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [resettingUser, setResettingUser] = useState<User | null>(null);
  const [resetting, setResetting] = useState(false);
  const [passwordForm] = Form.useForm();

  const fetchUsers = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<User[]>('/users'),
      api.get<Role[]>('/roles'),
      api.get<Tenant[]>('/tenants'),
    ])
      .then(([usersData, rolesData, tenantsData]) => {
        setUsers(usersData || []);
        setRoles(rolesData || []);
        setTenants(tenantsData || []);
      })
      .catch(() => message.error('Failed to load users'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({ status: 'active' });
    setModalOpen(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      tenant_id: user.tenant_id,
      status: user.status,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingUser) {
        await api.put(`/users/${editingUser.id}`, values);
        message.success('User updated');
      } else {
        await api.post('/users', values);
        message.success('User created');
      }

      setModalOpen(false);
      form.resetFields();
      fetchUsers();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error(editingUser ? 'Failed to update user' : 'Failed to create user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/users/${id}`);
      message.success('User deleted');
      fetchUsers();
    } catch {
      message.error('Failed to delete user');
    }
  };

  const handleResetPassword = (user: User) => {
    setResettingUser(user);
    passwordForm.resetFields();
    setPasswordModalOpen(true);
  };

  const handlePasswordReset = async () => {
    try {
      const values = await passwordForm.validateFields();
      setResetting(true);

      await api.post(`/users/${resettingUser?.id}/reset-password`, values);
      message.success('Password reset successfully');
      setPasswordModalOpen(false);
      passwordForm.resetFields();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error('Failed to reset password');
    } finally {
      setResetting(false);
    }
  };

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (_: any, record: User) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>
              <Text strong>{record.full_name || record.username}</Text>
              {record.status === 'pending' && (
                <Badge status="warning" style={{ marginLeft: 8 }} />
              )}
            </div>
            {record.email && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.email}
              </Text>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string, record: User) => {
        const roleName = record.role_name || role;
        return <Tag color={ROLE_COLORS[role] || 'default'}>{roleName}</Tag>;
      },
    },
    {
      title: 'Tenant',
      dataIndex: 'tenant_name',
      key: 'tenant_name',
      render: (name: string, record: User) => name || record.tenant_id,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <Tag color={STATUS_COLORS[status]}>{status}</Tag>,
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      width: 180,
      render: (date: string) => (date ? new Date(date).toLocaleString() : 'Never'),
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
      render: (_: any, record: User) => (
        <Space>
          <Button
            size="small"
            icon={<LockOutlined />}
            onClick={() => handleResetPassword(record)}
          >
            Reset Password
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Delete this user?"
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
        <Title level={4} style={{ margin: 0 }}>Users</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create User
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          expandable={{
            expandedRowRender: (record: User) => (
              <Descriptions column={2} size="small" bordered>
                <Descriptions.Item label="User ID">{record.id}</Descriptions.Item>
                <Descriptions.Item label="Username">{record.username}</Descriptions.Item>
                <Descriptions.Item label="Full Name">
                  {record.full_name || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Email">
                  {record.email || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Role">{record.role_name || record.role}</Descriptions.Item>
                <Descriptions.Item label="Tenant">{record.tenant_name || record.tenant_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Tag color={STATUS_COLORS[record.status]}>{record.status}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Created">
                  {new Date(record.created_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Last Login" span={2}>
                  {record.last_login_at
                    ? new Date(record.last_login_at).toLocaleString()
                    : 'Never'}
                </Descriptions.Item>
              </Descriptions>
            ),
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingUser ? 'Edit User' : 'Create User'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true }]}
          >
            <Input placeholder="johndoe" prefix={<UserOutlined />} />
          </Form.Item>
          <Form.Item
            name="email"
            label="Email"
            rules={[{ type: 'email', message: 'Invalid email' }]}
          >
            <Input placeholder="john@example.com" prefix={<MailOutlined />} />
          </Form.Item>
          <Form.Item name="full_name" label="Full Name">
            <Input placeholder="John Doe" />
          </Form.Item>
          {!editingUser && (
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, min: 8 }]}
            >
              <Input.Password placeholder="Minimum 8 characters" prefix={<LockOutlined />} />
            </Form.Item>
          )}
          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true }]}
          >
            <Select placeholder="Select role">
              {roles.map((role) => (
                <Select.Option key={role.id} value={role.id}>
                  <SafetyOutlined /> {role.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="tenant_id"
            label="Tenant"
            rules={[{ required: true }]}
          >
            <Select placeholder="Select tenant">
              {tenants.map((tenant) => (
                <Select.Option key={tenant.id} value={tenant.id}>
                  <TeamOutlined /> {tenant.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="status"
            label="Status"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="active">Active</Select.Option>
              <Select.Option value="inactive">Inactive</Select.Option>
              <Select.Option value="pending">Pending</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Password Reset Modal */}
      <Modal
        title={`Reset Password: ${resettingUser?.username || ''}`}
        open={passwordModalOpen}
        onOk={handlePasswordReset}
        onCancel={() => setPasswordModalOpen(false)}
        confirmLoading={resetting}
      >
        <Form form={passwordForm} layout="vertical">
          <Form.Item
            name="new_password"
            label="New Password"
            rules={[{ required: true, min: 8 }]}
            help="Minimum 8 characters"
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="Confirm Password"
            dependencies={['new_password']}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
