'use client';
import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Select, Button, Typography, message } from 'antd';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import type { ModelProvider, ModelConfig } from '@/types';

const { Title } = Typography;
const { TextArea } = Input;

export default function CreateAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [fetching, setFetching] = useState(true);
  const [form] = Form.useForm();

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
    setLoading(true);
    try {
      const result = await api.createAgent(values);
      message.success('Agent created');
      router.push(`/agents/${result.id}`);
    } catch {
      message.error('Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={4}>Create Agent</Title>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input placeholder="Agent name" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="What does this agent do?" />
          </Form.Item>
          <Form.Item name="model_provider" label="Model Provider" rules={[{ required: true }]}>
            <Select
              loading={fetching}
              placeholder="Select a provider"
              options={providerOptions}
              onChange={() => form.setFieldValue('model_name', undefined)}
            />
          </Form.Item>
          <Form.Item name="model_name" label="Model" rules={[{ required: true }]}>
            <Select
              loading={fetching}
              placeholder="Select a model"
              options={modelOptions}
              disabled={!selectedProvider || modelOptions.length === 0}
            />
          </Form.Item>
          <Form.Item name="system_prompt" label="System Prompt" rules={[{ required: true }]}>
            <TextArea rows={6} placeholder="You are a helpful assistant..." />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>Create</Button>
            <Button style={{ marginLeft: 8 }} onClick={() => router.back()}>Cancel</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
