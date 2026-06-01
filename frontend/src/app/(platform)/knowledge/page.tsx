'use client';
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Typography, Tag, message, Space, Modal, Form, Input, InputNumber, Select } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { KnowledgeBase } from '@/types';

const { Title } = Typography;

const EMBEDDING_MODELS = [
  { value: 'text-embedding-3-small', label: 'text-embedding-3-small' },
  { value: 'text-embedding-3-large', label: 'text-embedding-3-large' },
  { value: 'text-embedding-ada-002', label: 'text-embedding-ada-002' },
  { value: 'bge-large-zh-v1.5', label: 'bge-large-zh-v1.5' },
  { value: 'bge-m3', label: 'bge-m3' },
];

export default function KnowledgePage() {
  const router = useRouter();
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const fetchKbs = () => {
    setLoading(true);
    api.listKnowledgeBases().then((d) => setKbs(d.items || [])).catch(() => message.error('Failed to load')).finally(() => setLoading(false));
  };

  useEffect(() => { fetchKbs(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);
      await api.createKnowledgeBase(values);
      message.success('Knowledge base created');
      setModalOpen(false);
      form.resetFields();
      fetchKbs();
    } catch {
      message.error('Failed to create knowledge base');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteKnowledgeBase(id);
      message.success('Deleted');
      setKbs(kbs.filter((k) => k.id !== id));
    } catch {
      message.error('Failed to delete');
    }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (text: string, record: KnowledgeBase) => <a onClick={() => router.push(`/knowledge/${record.id}`)}>{text}</a> },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: 'Documents', dataIndex: 'document_count', key: 'document_count' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color="green">{s}</Tag> },
    {
      title: 'Action', key: 'action', render: (_: any, record: KnowledgeBase) => (
        <Space>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>Delete</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4}>Knowledge Bases</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>Create</Button>
      </div>
      <Card>
        <Table dataSource={kbs} columns={columns} loading={loading} rowKey="id" />
      </Card>

      <Modal
        title="Create Knowledge Base"
        open={modalOpen}
        onOk={handleCreate}
        confirmLoading={creating}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true, message: 'Please enter a name' }]}>
            <Input placeholder="My Knowledge Base" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea placeholder="Describe this knowledge base" />
          </Form.Item>
          <Form.Item name="embedding_model" label="Embedding Model" rules={[{ required: true, message: 'Please select an embedding model' }]}>
            <Select placeholder="Select embedding model" options={EMBEDDING_MODELS} />
          </Form.Item>
          <Form.Item name="chunk_size" label="Chunk Size" initialValue={500}>
            <InputNumber min={100} max={4000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="chunk_overlap" label="Chunk Overlap" initialValue={50}>
            <InputNumber min={0} max={500} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
