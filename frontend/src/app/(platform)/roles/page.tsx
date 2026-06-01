'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Button, Space, Modal, Form, Input,
  Popconfirm, message, Spin, Checkbox, Descriptions, Divider,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, SafetyOutlined,
  KeyOutlined, UserOutlined, SettingOutlined, DatabaseOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system_role: boolean;
  created_at: string;
  updated_at: string;
}

// Available permissions organized by category
const PERMISSION_CATEGORIES = {
  agents: {
    label: 'Agents',
    icon: <KeyOutlined />,
    permissions: [
      { value: 'agents:read', label: 'View Agents' },
      { value: 'agents:create', label: 'Create Agents' },
      { value: 'agents:update', label: 'Update Agents' },
      { value: 'agents:delete', label: 'Delete Agents' },
      { value: 'agents:publish', label: 'Publish Agents' },
    ],
  },
  knowledge: {
    label: 'Knowledge',
    icon: <DatabaseOutlined />,
    permissions: [
      { value: 'knowledge:read', label: 'View Knowledge Bases' },
      { value: 'knowledge:create', label: 'Create Knowledge Bases' },
      { value: 'knowledge:update', label: 'Update Knowledge Bases' },
      { value: 'knowledge:delete', label: 'Delete Knowledge Bases' },
      { value: 'knowledge:upload', label: 'Upload Documents' },
    ],
  },
  workflows: {
    label: 'Workflows',
    icon: <SettingOutlined />,
    permissions: [
      { value: 'workflows:read', label: 'View Workflows' },
      { value: 'workflows:create', label: 'Create Workflows' },
      { value: 'workflows:update', label: 'Update Workflows' },
      { value: 'workflows:delete', label: 'Delete Workflows' },
      { value: 'workflows:execute', label: 'Execute Workflows' },
    ],
  },
  users: {
    label: 'Users & Roles',
    icon: <UserOutlined />,
    permissions: [
      { value: 'users:read', label: 'View Users' },
      { value: 'users:create', label: 'Create Users' },
      { value: 'users:update', label: 'Update Users' },
      { value: 'users:delete', label: 'Delete Users' },
      { value: 'roles:read', label: 'View Roles' },
      { value: 'roles:manage', label: 'Manage Roles' },
    ],
  },
  admin: {
    label: 'Admin',
    icon: <SafetyOutlined />,
    permissions: [
      { value: 'tenants:read', label: 'View Tenants' },
      { value: 'tenants:manage', label: 'Manage Tenants' },
      { value: 'audit:read', label: 'View Audit Logs' },
      { value: 'settings:manage', label: 'Manage Settings' },
      { value: 'admin:*', label: 'Full Admin Access' },
    ],
  },
};

const ALL_PERMISSIONS = Object.values(PERMISSION_CATEGORIES).flatMap(
  (cat) => cat.permissions
);

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);

  // Create/Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchRoles = useCallback(() => {
    setLoading(true);
    api.get<Role[]>('/roles')
      .then(setRoles)
      .catch(() => message.error('Failed to load roles'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchRoles(); }, [fetchRoles]);

  const handleCreate = () => {
    setEditingRole(null);
    form.resetFields();
    form.setFieldsValue({ permissions: [] });
    setModalOpen(true);
  };

  const handleEdit = (role: Role) => {
    setEditingRole(role);
    form.setFieldsValue({
      name: role.name,
      description: role.description,
      permissions: role.permissions,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      if (editingRole) {
        await api.put(`/roles/${editingRole.id}`, values);
        message.success('Role updated');
      } else {
        await api.post('/roles', values);
        message.success('Role created');
      }

      setModalOpen(false);
      form.resetFields();
      fetchRoles();
    } catch (e: any) {
      if (e.errorFields) return;
      message.error(editingRole ? 'Failed to update role' : 'Failed to create role');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/roles/${id}`);
      message.success('Role deleted');
      fetchRoles();
    } catch {
      message.error('Failed to delete role');
    }
  };

  const getPermissionCategory = (perm: string) => {
    const resource = perm.split(':')[0];
    if (resource === 'agents' || resource === 'admin') return PERMISSION_CATEGORIES.agents;
    if (resource === 'knowledge') return PERMISSION_CATEGORIES.knowledge;
    if (resource === 'workflows') return PERMISSION_CATEGORIES.workflows;
    if (resource === 'users' || resource === 'roles') return PERMISSION_CATEGORIES.users;
    return PERMISSION_CATEGORIES.admin;
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Role) => (
        <Space>
          <SafetyOutlined />
          <Text strong>{name}</Text>
          {record.is_system_role && <Tag color="blue">System</Tag>}
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
      title: 'Permissions',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <Space size="small" wrap>
          {permissions?.slice(0, 3).map((perm) => {
            const permDef = ALL_PERMISSIONS.find((p) => p.value === perm);
            return (
              <Tag key={perm} color="purple">
                {permDef?.label || perm}
              </Tag>
            );
          })}
          {permissions?.length > 3 && (
            <Tag>+{permissions.length - 3}</Tag>
          )}
        </Space>
      ),
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
      width: 120,
      render: (_: any, record: Role) => (
        <Space>
          {!record.is_system_role && (
            <>
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
              <Popconfirm
                title="Delete this role?"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Roles & Permissions</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create Role
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={roles}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          expandable={{
            expandedRowRender: (record: Role) => (
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="Description">
                  {record.description || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Permissions">
                  <div style={{ maxHeight: 300, overflow: 'auto' }}>
                    {Object.entries(PERMISSION_CATEGORIES).map(([catKey, cat]) => {
                      const catPerms = record.permissions?.filter((p) =>
                        p.startsWith(catKey) || (catKey === 'admin' && p.includes('admin'))
                      );
                      if (!catPerms || catPerms.length === 0) return null;

                      return (
                        <div key={catKey} style={{ marginBottom: 12 }}>
                          <Text strong style={{ display: 'block', marginBottom: 4 }}>
                            {cat.icon} {cat.label}
                          </Text>
                          <Space size="small" wrap>
                            {catPerms.map((perm) => {
                              const permDef = cat.permissions.find((p) => p.value === perm);
                              return (
                                <Tag key={perm} color="purple">
                                  {permDef?.label || perm}
                                </Tag>
                              );
                            })}
                          </Space>
                        </div>
                      );
                    })}
                  </div>
                </Descriptions.Item>
              </Descriptions>
            ),
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingRole ? 'Edit Role' : 'Create Role'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Role Name"
            rules={[{ required: true }]}
          >
            <Input placeholder="e.g., Content Manager" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Describe this role's purpose" />
          </Form.Item>

          <Divider>Permissions</Divider>

          <Form.Item
            name="permissions"
            label="Select Permissions"
            rules={[{ required: true, type: 'array', min: 1 }]}
          >
            <Checkbox.Group style={{ width: '100%' }}>
              {Object.entries(PERMISSION_CATEGORIES).map(([catKey, cat]) => (
                <Card key={catKey} size="small" style={{ marginBottom: 12 }}>
                  <Space style={{ marginBottom: 8 }}>
                    {cat.icon}
                    <Text strong>{cat.label}</Text>
                  </Space>
                  <div style={{ marginLeft: 24 }}>
                    <Checkbox
                      value={`admin:*`}
                      style={{ marginBottom: 8, display: 'block' }}
                      onChange={(e) => {
                        if (e.target.checked) {
                          const allPerms = cat.permissions.map((p) => p.value);
                          form.setFieldsValue({
                            permissions: [
                              ...(form.getFieldValue('permissions') || []),
                              ...allPerms,
                            ],
                          });
                        } else {
                          form.setFieldsValue({
                            permissions: (form.getFieldValue('permissions') || []).filter(
                              (p: string) => !cat.permissions.some((cp) => cp.value === p)
                            ),
                          });
                        }
                      }}
                    >
                      <Text strong>Select All {cat.label} Permissions</Text>
                    </Checkbox>
                    {cat.permissions.map((perm) => (
                      <Checkbox
                        key={perm.value}
                        value={perm.value}
                        style={{ display: 'block', marginLeft: 16, marginBottom: 4 }}
                      >
                        {perm.label}
                      </Checkbox>
                    ))}
                  </div>
                </Card>
              ))}
            </Checkbox.Group>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
