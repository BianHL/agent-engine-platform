'use client';
import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Space, Tag, Modal, Form, Input, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

interface Workflow {
  id: string;
  name: string;
  description: string;
  status: string;
  node_count: number;
  created_at: string;
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/workflows');
      setWorkflows(res?.items || res?.data?.items || []);
      setError(null);
    } catch (err: any) {
      const msg = err?.message || 'Failed to load workflows';
      setError(msg);
      message.error(msg);
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchWorkflows(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/workflows', values);
      message.success('Workflow created');
      setModalOpen(false);
      form.resetFields();
      fetchWorkflows();
    } catch {
      message.error('Failed to create workflow');
    }
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: 'Delete workflow?',
      onOk: async () => {
        try {
          await api.delete(`/workflows/${id}`);
          message.success('Deleted');
          fetchWorkflows();
        } catch (err: any) {
          message.error(err?.message || 'Failed to delete workflow');
        }
      },
    });
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'active' ? 'green' : 'default'}>{s}</Tag>,
    },
    { title: 'Nodes', dataIndex: 'node_count', key: 'node_count' },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, record: Workflow) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => router.push(`/workflows/${record.id}/edit`)}>Edit</Button>
          <Button icon={<PlayCircleOutlined />} size="small" type="primary">Run</Button>
          <Button icon={<DeleteOutlined />} size="small" danger onClick={() => handleDelete(record.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="Workflows"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>Create Workflow</Button>}
      >
        {error && !loading ? (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <p style={{ color: 'var(--ae-muted)', marginBottom: 16 }}>{error}</p>
            <Button icon={<ReloadOutlined />} onClick={fetchWorkflows}>
              Retry
            </Button>
          </div>
        ) : !loading && workflows.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--ae-muted)' }}>
            No workflows yet. Click &quot;Create Workflow&quot; to get started.
          </div>
        ) : (
          <Table columns={columns} dataSource={workflows} loading={loading} rowKey="id" />
        )}
      </Card>

      <Modal title="Create Workflow" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input placeholder="My Workflow" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea placeholder="Describe what this workflow does" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
