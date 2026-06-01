'use client';

import React, { useState, useEffect } from 'react';
import {
  Card, Button, Input, Select, Table, Space, Typography, Tag, Modal,
  Form, message, Popconfirm, Tooltip
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined,
  DatabaseOutlined, GlobalOutlined, UserOutlined, SettingOutlined,
  SearchOutlined, ReloadOutlined
} from '@ant-design/icons';
import { api } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

interface Variable {
  id: string;
  key: string;
  value: any;
  scope: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export default function VariablesPage() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingVariable, setEditingVariable] = useState<Variable | null>(null);
  const [searchKey, setSearchKey] = useState('');
  const [filterScope, setFilterScope] = useState<string>('');
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => { loadVariables(); }, []);

  const loadVariables = async () => {
    setLoading(true);
    try {
      const response = await api.get('/variables', {
        params: { scope: filterScope || undefined, key_prefix: searchKey || undefined }
      });
      setVariables(response.data);
    } catch (error) {
      message.error('加载变量列表失败');
    } finally {
      setLoading(false);
    }
  };

  const createVariable = async (values: any) => {
    try {
      await api.post('/variables', values);
      message.success('变量创建成功');
      setShowCreateModal(false);
      form.resetFields();
      loadVariables();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败');
    }
  };

  const updateVariable = async (values: any) => {
    if (!editingVariable) return;
    try {
      await api.put(`/variables/${editingVariable.key}`, values, { params: { scope: editingVariable.scope } });
      message.success('变量更新成功');
      setShowEditModal(false);
      setEditingVariable(null);
      editForm.resetFields();
      loadVariables();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新失败');
    }
  };

  const deleteVariable = async (key: string, scope: string) => {
    try {
      await api.delete(`/variables/${key}`, { params: { scope } });
      message.success('变量删除成功');
      loadVariables();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const copyValue = (value: any) => {
    navigator.clipboard.writeText(typeof value === 'string' ? value : JSON.stringify(value));
    message.success('已复制到剪贴板');
  };

  const getScopeIcon = (scope: string) => {
    const icons: Record<string, React.ReactNode> = {
      global: <GlobalOutlined />, user: <UserOutlined />, session: <SettingOutlined />
    };
    return icons[scope] || <DatabaseOutlined />;
  };

  const getScopeColor = (scope: string) => {
    const colors: Record<string, string> = { global: 'blue', user: 'green', session: 'orange' };
    return colors[scope] || 'default';
  };

  const columns = [
    { title: 'Key', dataIndex: 'key', key: 'key', render: (text: string) => <Text code strong>{text}</Text> },
    { title: 'Value', dataIndex: 'value', key: 'value',
      render: (value: any) => <div className="max-w-xs truncate"><Text code>{typeof value === 'string' ? value : JSON.stringify(value)}</Text></div> },
    { title: 'Scope', dataIndex: 'scope', key: 'scope',
      render: (scope: string) => <Tag icon={getScopeIcon(scope)} color={getScopeColor(scope)}>{scope.toUpperCase()}</Tag> },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Updated', dataIndex: 'updated_at', key: 'updated_at',
      render: (text: string) => new Date(text).toLocaleString() },
    { title: 'Actions', key: 'actions',
      render: (_value: any, record: Variable) => (
        <Space>
          <Tooltip title="复制值"><Button size="small" icon={<CopyOutlined />} onClick={() => copyValue(record.value)} /></Tooltip>
          <Tooltip title="编辑">
            <Button size="small" icon={<EditOutlined />}
              onClick={() => {
                setEditingVariable(record);
                editForm.setFieldsValue({ value: typeof record.value === 'string' ? record.value : JSON.stringify(record.value), description: record.description });
                setShowEditModal(true);
              }} />
          </Tooltip>
          <Popconfirm title="确定删除这个变量？" onConfirm={() => deleteVariable(record.key, record.scope)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ];

  const stats = {
    total: variables.length,
    global: variables.filter(v => v.scope === 'global').length,
    user: variables.filter(v => v.scope === 'user').length,
    session: variables.filter(v => v.scope === 'session').length
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}><DatabaseOutlined className="mr-2" />变量管理</Title>
        <Paragraph type="secondary">管理会话级、用户级和全局级变量，支持 KV 存储</Paragraph>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card><div className="text-center"><div className="text-3xl mb-2">📊</div><Title level={3}>{stats.total}</Title><Text type="secondary">总变量数</Text></div></Card>
        <Card><div className="text-center"><div className="text-3xl mb-2">🌐</div><Title level={3}>{stats.global}</Title><Text type="secondary">全局变量</Text></div></Card>
        <Card><div className="text-center"><div className="text-3xl mb-2">👤</div><Title level={3}>{stats.user}</Title><Text type="secondary">用户变量</Text></div></Card>
        <Card><div className="text-center"><div className="text-3xl mb-2">⚡</div><Title level={3}>{stats.session}</Title><Text type="secondary">会话变量</Text></div></Card>
      </div>

      <Card title="变量列表" extra={
        <Space>
          <Input placeholder="搜索 Key" prefix={<SearchOutlined />} value={searchKey} onChange={e => setSearchKey(e.target.value)} onPressEnter={loadVariables} style={{ width: 200 }} />
          <Select placeholder="筛选 Scope" value={filterScope} onChange={setFilterScope} allowClear style={{ width: 120 }}
            options={[{ value: 'global', label: 'Global' }, { value: 'user', label: 'User' }, { value: 'session', label: 'Session' }]} />
          <Button icon={<ReloadOutlined />} onClick={loadVariables}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>创建变量</Button>
        </Space>
      }>
        <Table columns={columns} dataSource={variables} rowKey="id" loading={loading} pagination={{ pageSize: 20 }} />
      </Card>

      <Modal title="创建变量" open={showCreateModal} onCancel={() => { setShowCreateModal(false); form.resetFields(); }} footer={null}>
        <Form form={form} layout="vertical" onFinish={createVariable}>
          <Form.Item label="Key" name="key" rules={[{ required: true, message: '请输入变量 Key' }]}><Input placeholder="变量名称" /></Form.Item>
          <Form.Item label="Value" name="value" rules={[{ required: true, message: '请输入变量值' }]}><Input.TextArea placeholder="变量值（支持 JSON）" autoSize={{ minRows: 3 }} /></Form.Item>
          <Form.Item label="Scope" name="scope" initialValue="global">
            <Select options={[{ value: 'global', label: '全局' }, { value: 'user', label: '用户' }, { value: 'session', label: '会话' }]} />
          </Form.Item>
          <Form.Item label="Description" name="description"><Input placeholder="变量描述（可选）" /></Form.Item>
          <Form.Item><Space><Button type="primary" htmlType="submit">创建</Button><Button onClick={() => setShowCreateModal(false)}>取消</Button></Space></Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑变量" open={showEditModal} onCancel={() => { setShowEditModal(false); setEditingVariable(null); editForm.resetFields(); }} footer={null}>
        <Form form={editForm} layout="vertical" onFinish={updateVariable}>
          <Form.Item label="Value" name="value" rules={[{ required: true, message: '请输入变量值' }]}><Input.TextArea placeholder="变量值" autoSize={{ minRows: 3 }} /></Form.Item>
          <Form.Item label="Description" name="description"><Input placeholder="变量描述" /></Form.Item>
          <Form.Item><Space><Button type="primary" htmlType="submit">更新</Button><Button onClick={() => setShowEditModal(false)}>取消</Button></Space></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
