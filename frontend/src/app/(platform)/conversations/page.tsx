'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, message, Button, Space, Drawer, List, Empty, Spin, Select,
} from 'antd';
import { MessageOutlined, DeleteOutlined, CommentOutlined, LikeOutlined, DislikeOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { SearchInput } from '@/components/ui';
import MarkdownRenderer from '@/components/MarkdownRenderer';

const { Title, Text } = Typography;

export default function ConversationsPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedConv, setSelectedConv] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Filters
  const [agentFilter, setAgentFilter] = useState<string | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  // Feedback stats
  const [feedbackStats, setFeedbackStats] = useState<Record<string, { positive: number; negative: number }>>({});

  const fetchConversations = useCallback(() => {
    setLoading(true);
    api.listConversations(agentFilter, page, 20)
      .then((res) => {
        const items = Array.isArray(res) ? res : res.items;
        setConversations(items);
      })
      .catch(() => message.error('Failed to load conversations'))
      .finally(() => setLoading(false));
  }, [agentFilter, page]);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      fetchConversations();
      return;
    }
    setLoading(true);
    try {
      const res = await api.searchConversations(query);
      setConversations(Array.isArray(res) ? res : res.items);
    } catch {
      message.error('Search failed');
    } finally {
      setLoading(false);
    }
  }, [fetchConversations]);

  const handleViewMessages = async (conv: any) => {
    setSelectedConv(conv);
    setDrawerOpen(true);
    setMessagesLoading(true);
    try {
      const msgs = await api.getConversationMessages(conv.id);
      setMessages(Array.isArray(msgs) ? msgs : []);
    } catch {
      message.error('Failed to load messages');
    } finally {
      setMessagesLoading(false);
    }

    // Fetch feedback stats for the agent
    if (conv.agent_id && !feedbackStats[conv.agent_id]) {
      try {
        const stats = await api.getFeedbackStats(conv.agent_id);
        setFeedbackStats((prev) => ({
          ...prev,
          [conv.agent_id]: { positive: stats?.positive || 0, negative: stats?.negative || 0 },
        }));
      } catch {
        // silently ignore
      }
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteConversation(id);
      message.success('Conversation deleted');
      setConversations((prev) => prev.filter((c) => c.id !== id));
    } catch {
      message.error('Failed to delete');
    }
  };

  const columns = [
    { title: 'Title', dataIndex: 'title', key: 'title', render: (t: string) => t || 'Untitled' },
    {
      title: 'Agent', dataIndex: 'agent_id', key: 'agent_id', ellipsis: true,
      render: (id: string) => <Text copyable={{ text: id }}>{id.slice(0, 8)}...</Text>,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'active' ? 'success' : 'default'}>{s || 'completed'}</Tag>,
    },
    {
      title: 'Created', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" icon={<MessageOutlined />} onClick={() => handleViewMessages(record)}>
            Messages
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Conversations</Title>
        <Space>
          <SearchInput
            placeholder="Search conversations..."
            onChange={handleSearch}
          />
        </Space>
      </div>

      {/* Feedback summary bar */}
      {Object.keys(feedbackStats).length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space split={<Text type="secondary">|</Text>}>
            {Object.entries(feedbackStats).map(([agentId, stats]) => (
              <Space key={agentId} size={4}>
                <Text type="secondary">{agentId.slice(0, 8)}:</Text>
                <Space size={4}>
                  <LikeOutlined style={{ color: '#52c41a' }} />
                  <Text>{stats.positive}</Text>
                  <DislikeOutlined style={{ color: '#ff4d4f' }} />
                  <Text>{stats.negative}</Text>
                </Space>
              </Space>
            ))}
          </Space>
        </Card>
      )}

      <Table
        columns={columns}
        dataSource={conversations}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: 20,
          onChange: setPage,
          showSizeChanger: false,
        }}
        locale={{
          emptyText: (
            <Empty
              image={<CommentOutlined style={{ fontSize: 48, color: '#bbb' }} />}
              description="No conversations yet"
            >
              <Button type="primary" onClick={() => router.push('/agents')}>
                Start a chat
              </Button>
            </Empty>
          ),
        }}
      />

      <Drawer
        title={selectedConv?.title || 'Conversation Messages'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={640}
      >
        {messagesLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
        ) : messages.length === 0 ? (
          <Empty description="No messages" />
        ) : (
          <List
            dataSource={messages}
            renderItem={(msg: any) => (
              <List.Item style={{ border: 'none', padding: '8px 0' }}>
                <div style={{ width: '100%' }}>
                  <Space style={{ marginBottom: 4 }}>
                    <Tag color={msg.role === 'user' ? 'blue' : msg.role === 'assistant' ? 'green' : 'default'}>
                      {msg.role}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {msg.created_at ? new Date(msg.created_at).toLocaleString() : ''}
                    </Text>
                  </Space>
                  <div style={{
                    padding: '8px 12px',
                    borderRadius: 8,
                    background: msg.role === 'user' ? '#e6f7ff' : msg.role === 'assistant' ? '#f6f6f6' : '#fff',
                    marginLeft: msg.role === 'user' ? 0 : 0,
                  }}>
                    {msg.role === 'assistant' ? (
                      <MarkdownRenderer content={msg.content || ''} />
                    ) : (
                      <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                    )}
                  </div>
                  {msg.feedback && (
                    <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
                      Feedback: <Tag color={msg.feedback.rating === 'positive' ? 'success' : 'error'}>
                        {msg.feedback.rating}
                      </Tag>
                    </div>
                  )}
                </div>
              </List.Item>
            )}
          />
        )}
      </Drawer>
    </div>
  );
}
