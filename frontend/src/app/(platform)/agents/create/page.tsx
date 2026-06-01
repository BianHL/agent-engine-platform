'use client';
import React, { useState } from 'react';
import { Card, Form, Input, Select, Button, Typography, message } from 'antd';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

const { Title } = Typography;
const { TextArea } = Input;

export default function CreateAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

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
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ model_provider: 'openai', model_name: 'gpt-4o' }}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
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
              { label: 'DeepSeek V3', value: 'deepseek-chat' },
            ]} />
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
