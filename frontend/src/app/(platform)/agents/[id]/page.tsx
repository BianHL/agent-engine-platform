'use client';
import React, { useEffect, useState } from 'react';
import { Card, Descriptions, Button, Tag, Typography, Spin, message, Space } from 'antd';
import { useParams, useRouter } from 'next/navigation';
import { PlayCircleOutlined, EditOutlined } from '@ant-design/icons';
import api from '@/lib/api';
import { Agent } from '@/types';

const { Title } = Typography;

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      api.getAgent(params.id as string).then(setAgent).catch(() => message.error('Not found')).finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!agent) return <div>Agent not found</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4}>{agent.name}</Title>
        <Space>
          <Button icon={<EditOutlined />} onClick={() => router.push(`/agents/${agent.id}/edit`)}>Edit</Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => router.push(`/agents/${agent.id}/chat`)}>Start Chat</Button>
        </Space>
      </div>
      <Card>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="Status"><Tag color={agent.status === 'published' ? 'green' : 'default'}>{agent.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="Model">{agent.model_provider} / {agent.model_name}</Descriptions.Item>
          <Descriptions.Item label="Description" span={2}>{agent.description || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="System Prompt" span={2}><pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{agent.system_prompt}</pre></Descriptions.Item>
          <Descriptions.Item label="Version">{agent.version}</Descriptions.Item>
          <Descriptions.Item label="Created">{agent.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
