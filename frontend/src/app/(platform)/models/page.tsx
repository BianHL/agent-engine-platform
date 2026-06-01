'use client';
import React, { useEffect, useState, useCallback } from 'react';
import { Card, Table, Typography, Tag, Tabs, message, Button, Space, Modal, Form, Input, Select, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, StarOutlined } from '@ant-design/icons';
import api from '@/lib/api';
import { ModelProvider, ModelConfig } from '@/types';

const { Title } = Typography;

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'azure_openai', label: 'Azure OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'ollama', label: 'Ollama' },
  { value: 'custom', label: 'Custom' },
];

const MODEL_TYPES = [
  { value: 'llm', label: 'LLM' },
  { value: 'embedding', label: 'Embedding' },
  { value: 'reranker', label: 'Reranker' },
];

export default function ModelsPage() {
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(true);

  // Provider modal state
  const [providerModalOpen, setProviderModalOpen] = useState(false);
  const [providerCreating, setProviderCreating] = useState(false);
  const [providerForm] = Form.useForm();

  // Config modal state
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [configCreating, setConfigCreating] = useState(false);
  const [configForm] = Form.useForm();

  const fetchData = useCallback(() => {
    setLoading(true);
    Promise.all([api.listProviders(), api.listModelConfigs()])
      .then(([p, c]) => { setProviders(p); setConfigs(c); })
      .catch(() => message.error('Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreateProvider = async () => {
    try {
      const values = await providerForm.validateFields();
      setProviderCreating(true);
      await api.createProvider(values);
      message.success('Provider created');
      setProviderModalOpen(false);
      providerForm.resetFields();
      fetchData();
    } catch {
      message.error('Failed to create provider');
    } finally {
      setProviderCreating(false);
    }
  };

  const handleDeleteProvider = async (id: string) => {
    try {
      await api.deleteProvider(id);
      message.success('Provider deleted');
      setProviders((prev) => prev.filter((p) => p.id !== id));
    } catch {
      message.error('Failed to delete provider');
    }
  };

  const handleCreateConfig = async () => {
    try {
      const values = await configForm.validateFields();
      setConfigCreating(true);
      await api.createModelConfig(values);
      message.success('Model config created');
      setConfigModalOpen(false);
      configForm.resetFields();
      fetchData();
    } catch {
      message.error('Failed to create model config');
    } finally {
      setConfigCreating(false);
    }
  };

  const handleDeleteConfig = async (id: string) => {
    try {
      await api.deleteModelConfig(id);
      message.success('Model config deleted');
      setConfigs((prev) => prev.filter((c) => c.id !== id));
    } catch {
      message.error('Failed to delete model config');
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await api.setDefaultModel(id);
      message.success('Default model updated');
      // Refresh to reflect new default
      fetchData();
    } catch {
      message.error('Failed to set default model');
    }
  };

  const providerCols = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'provider_type', key: 'type' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color="green">{s}</Tag> },
    {
      title: 'Actions', key: 'actions', width: 100,
      render: (_: any, record: ModelProvider) => (
        <Popconfirm title="Delete this provider?" onConfirm={() => handleDeleteProvider(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  const configCols = [
    { title: 'Display Name', dataIndex: 'display_name', key: 'display_name' },
    { title: 'Model', dataIndex: 'model_name', key: 'model_name' },
    { title: 'Type', dataIndex: 'model_type', key: 'model_type' },
    { title: 'Default', dataIndex: 'is_default', key: 'is_default', render: (v: boolean) => v ? <Tag color="blue">Default</Tag> : null },
    { title: 'Enabled', dataIndex: 'enabled', key: 'enabled', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Yes' : 'No'}</Tag> },
    {
      title: 'Actions', key: 'actions', width: 150,
      render: (_: any, record: ModelConfig) => (
        <Space>
          {!record.is_default && (
            <Button type="link" icon={<StarOutlined />} size="small" onClick={() => handleSetDefault(record.id)}>
              Set Default
            </Button>
          )}
          <Popconfirm title="Delete this config?" onConfirm={() => handleDeleteConfig(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />} size="small" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>Model Management</Title>
      <Card>
        <Tabs items={[
          {
            key: 'providers',
            label: 'Providers',
            children: (
              <>
                <div style={{ marginBottom: 16, textAlign: 'right' }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setProviderModalOpen(true)}>
                    Create Provider
                  </Button>
                </div>
                <Table dataSource={providers} columns={providerCols} loading={loading} rowKey="id" />
              </>
            ),
          },
          {
            key: 'configs',
            label: 'Model Configs',
            children: (
              <>
                <div style={{ marginBottom: 16, textAlign: 'right' }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setConfigModalOpen(true)}>
                    Create Model Config
                  </Button>
                </div>
                <Table dataSource={configs} columns={configCols} loading={loading} rowKey="id" />
              </>
            ),
          },
        ]} />
      </Card>

      {/* Create Provider Modal */}
      <Modal
        title="Create Provider"
        open={providerModalOpen}
        onOk={handleCreateProvider}
        confirmLoading={providerCreating}
        onCancel={() => { setProviderModalOpen(false); providerForm.resetFields(); }}
      >
        <Form form={providerForm} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true, message: 'Please enter a name' }]}>
            <Input placeholder="My OpenAI Provider" />
          </Form.Item>
          <Form.Item name="provider_type" label="Provider Type" rules={[{ required: true, message: 'Please select a type' }]}>
            <Select placeholder="Select provider type" options={PROVIDER_TYPES} />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true, message: 'Please enter API key' }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="api_base" label="API Base URL">
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Model Config Modal */}
      <Modal
        title="Create Model Config"
        open={configModalOpen}
        onOk={handleCreateConfig}
        confirmLoading={configCreating}
        onCancel={() => { setConfigModalOpen(false); configForm.resetFields(); }}
      >
        <Form form={configForm} layout="vertical">
          <Form.Item name="provider_id" label="Provider" rules={[{ required: true, message: 'Please select a provider' }]}>
            <Select
              placeholder="Select provider"
              options={providers.map((p) => ({ value: p.id, label: p.name }))}
            />
          </Form.Item>
          <Form.Item name="model_name" label="Model Name" rules={[{ required: true, message: 'Please enter model name' }]}>
            <Input placeholder="gpt-4o" />
          </Form.Item>
          <Form.Item name="model_type" label="Model Type" rules={[{ required: true, message: 'Please select model type' }]}>
            <Select placeholder="Select model type" options={MODEL_TYPES} />
          </Form.Item>
          <Form.Item name="display_name" label="Display Name" rules={[{ required: true, message: 'Please enter display name' }]}>
            <Input placeholder="GPT-4o" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
