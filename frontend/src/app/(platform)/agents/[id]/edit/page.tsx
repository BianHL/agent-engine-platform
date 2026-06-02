'use client';
import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Select, Button, Typography, message, Spin, Space, Tag } from 'antd';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Agent, ModelProvider, ModelConfig } from '@/types';

const { Title } = Typography;
const { TextArea } = Input;

export default function EditAgentPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [fetching, setFetching] = useState(true);

  const selectedProvider = Form.useWatch('model_provider', form);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setFetching(true);
        const [p, c] = await Promise.all([api.listProviders(), api.listModelConfigs()]);
        if (!cancelled) {
          setProviders(p);
          setConfigs(c.filter((m: ModelConfig) => m.enabled));
        }
      } catch {
        message.error('Failed to load models');
      } finally {
        if (!cancelled) setFetching(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (agentId) {
      api.getAgent(agentId)
        .then((data) => {
          setAgent(data);
          form.setFieldsValue({
            name: data.name,
            description: data.description,
            model_provider: data.model_provider,
            model_name: data.model_name,
            system_prompt: data.system_prompt,
          });
        })
        .catch(() => message.error('Failed to load agent'))
        .finally(() => setLoading(false));
    }
  }, [agentId, form]);

  const providerOptions = providers
    .filter((p) => p.status === 'active')
    .map((p) => ({ label: p.name, value: p.provider_type }));

  const modelOptions = configs
    .filter((m) => {
      const provider = providers.find((p) => p.provider_type === selectedProvider);
      return provider ? m.provider_id === provider.id : false;
    })
    .map((m) => ({ label: m.display_name || m.model_name, value: m.model_name }));

  const onFinish = async (values: any) => {
    setSaving(true);
    try {
      await api.updateAgent(agentId, values);
      message.success('Agent updated');
      router.push(`/agents/${agentId}`);
    } catch {
      message.error('Failed to update agent');
    } finally {
      setSaving(false);
    }
  };

  if (loading || fetching) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!agent) return <div>Agent not found</div>;

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Space>
          <Title level={4} style={{ margin: 0 }}>Edit Agent</Title>
          <Tag color={agent.status === 'published' ? 'green' : 'default'}>{agent.status}</Tag>
        </Space>
        <Button onClick={() => router.push(`/agents/${agentId}`)}>Back to Details</Button>
      </div>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="name" label="Name" rules={[{ required: true, message: 'Please enter agent name' }]}>
            <Input placeholder="Agent name" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="What does this agent do?" />
          </Form.Item>
          <Form.Item name="model_provider" label="Model Provider" rules={[{ required: true }]}>
            <Select
              placeholder="Select a provider"
              options={providerOptions}
              onChange={() => form.setFieldValue('model_name', undefined)}
            />
          </Form.Item>
          <Form.Item name="model_name" label="Model" rules={[{ required: true }]}>
            <Select
              placeholder="Select a model"
              options={modelOptions}
              disabled={!selectedProvider || modelOptions.length === 0}
            />
          </Form.Item>
          <Form.Item name="system_prompt" label="System Prompt" rules={[{ required: true, message: 'Please enter system prompt' }]}>
            <TextArea rows={6} placeholder="You are a helpful assistant..." />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={saving}>Save Changes</Button>
              <Button onClick={() => router.push(`/agents/${agentId}`)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
