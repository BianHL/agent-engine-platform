'use client';
import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Select, Button, Typography, message, Spin, Space, Tag } from 'antd';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Agent } from '@/types';

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

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
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
            <Select options={[
              { label: 'OpenAI', value: 'openai' },
              { label: 'Anthropic', value: 'anthropic' },
              { label: 'DeepSeek', value: 'deepseek' },
              { label: 'Ollama', value: 'ollama' },
            ]} />
          </Form.Item>
          <Form.Item name="model_name" label="Model" rules={[{ required: true }]}>
            <Select options={[
              { label: 'GPT-4o', value: 'gpt-4o' },
              { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
              { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
              { label: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' },
              { label: 'DeepSeek V3', value: 'deepseek-chat' },
              { label: 'DeepSeek R1', value: 'deepseek-reasoner' },
            ]} />
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
