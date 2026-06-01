'use client';
import React, { useEffect, useState } from 'react';
import {
  Card, Button, Tag, Typography, Empty, Spin, message,
  Segmented, Input, Space, Avatar, Dropdown, Modal,
} from 'antd';
import {
  PlusOutlined, PlayCircleOutlined, DeleteOutlined,
  AppstoreOutlined, UnorderedListOutlined, SearchOutlined,
  MoreOutlined, RobotOutlined, EditOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/lib/api';
import { Agent } from '@/types';

const { Title, Text, Paragraph } = Typography;

type ViewMode = 'grid' | 'list';

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await api.listAgents();
      setAgents(data.items || []);
    } catch {
      message.error('Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: 'Delete Agent',
      icon: <ExclamationCircleOutlined />,
      content: 'Are you sure you want to delete this agent? This action cannot be undone.',
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: async () => {
        try {
          await api.deleteAgent(id);
          message.success('Agent deleted');
          loadAgents();
        } catch {
          message.error('Failed to delete agent');
        }
      },
    });
  };

  const filteredAgents = agents.filter((a) =>
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (a.description || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-4">
        {/* Header skeleton */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="h-8 w-32 rounded-md bg-stone-01 animate-pulse mb-2" />
            <div className="h-4 w-48 rounded-md bg-stone-01 animate-pulse" />
          </div>
          <div className="h-9 w-32 rounded-md bg-stone-01 animate-pulse" />
        </div>
        {/* Search skeleton */}
        <div className="h-10 w-80 rounded-md bg-stone-01 animate-pulse mb-6" />
        {/* Grid skeletons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-48 rounded-lg bg-stone-01 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.25, 1, 0.5, 1] }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6"
      >
        <div>
          <Title
            level={2}
            style={{
              margin: 0,
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: '-0.02em',
              color: 'var(--ae-text)',
            }}
          >
            Agents
          </Title>
          <Text style={{ color: 'var(--ae-muted)', fontSize: 14 }}>
            {agents.length} agent{agents.length !== 1 ? 's' : ''} configured
          </Text>
        </div>

        <Space>
          <Segmented
            value={viewMode}
            onChange={(v) => setViewMode(v as ViewMode)}
            options={[
              { value: 'grid', icon: <AppstoreOutlined /> },
              { value: 'list', icon: <UnorderedListOutlined /> },
            ]}
            style={{ background: 'rgba(255,255,255,0.5)' }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => router.push('/agents/create')}
            style={{
              background: 'var(--ae-accent-gold)',
              borderColor: 'var(--ae-accent-gold)',
            }}
          >
            Create Agent
          </Button>
        </Space>
      </motion.div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className="mb-6"
      >
        <Input
          placeholder="Search agents by name or description..."
          prefix={<SearchOutlined style={{ color: 'var(--ae-muted)' }} />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            maxWidth: 480,
            borderRadius: 6,
            background: 'var(--ae-panel-strong)',
          }}
          allowClear
        />
      </motion.div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {filteredAgents.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
          >
            <Empty
              image={
                <div
                  style={{
                    width: 80,
                    height: 80,
                    borderRadius: 16,
                    background: 'rgba(255,255,255,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px',
                  }}
                >
                  <RobotOutlined style={{ fontSize: 36, color: 'var(--ae-muted)' }} />
                </div>
              }
              imageStyle={{ height: 'auto' }}
              description={
                <div>
                  <Text
                    style={{
                      display: 'block',
                      fontSize: 16,
                      fontWeight: 600,
                      color: 'var(--ae-text)',
                      marginBottom: 4,
                    }}
                  >
                    {searchQuery ? 'No agents match your search' : 'No agents yet'}
                  </Text>
                  <Text style={{ color: 'var(--ae-muted)', fontSize: 14 }}>
                    {searchQuery
                      ? 'Try adjusting your search terms'
                      : 'Create your first agent to get started'}
                  </Text>
                </div>
              }
            >
              {!searchQuery && (
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => router.push('/agents/create')}
                  style={{
                    background: 'var(--ae-accent-gold)',
                    borderColor: 'var(--ae-accent-gold)',
                  }}
                >
                  Create Agent
                </Button>
              )}
            </Empty>
          </motion.div>
        ) : viewMode === 'grid' ? (
          <AgentGrid key="grid" agents={filteredAgents} onDelete={handleDelete} />
        ) : (
          <AgentList key="list" agents={filteredAgents} onDelete={handleDelete} />
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Grid View ───
function AgentGrid({ agents, onDelete }: { agents: Agent[]; onDelete: (id: string) => void }) {
  const router = useRouter();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      {agents.map((agent, index) => (
        <motion.div
          key={agent.id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.35,
            delay: index * 0.04,
            ease: [0.25, 1, 0.5, 1],
          }}
        >
          <Card
            hoverable
            onClick={() => router.push(`/agents/${agent.id}`)}
            bordered={false}
            style={{
              background: 'var(--ae-panel-strong)',
              border: '1px solid var(--ae-line)',
              borderRadius: 8,
              transition: 'box-shadow 150ms cubic-bezier(0.25, 1, 0.5, 1)',
            }}
            bodyStyle={{ padding: 20 }}
          >
            <div className="flex items-start justify-between mb-3">
              <Avatar
                size={40}
                icon={<RobotOutlined />}
                style={{
                  background: agent.status === 'published'
                    ? 'rgba(111,155,124,0.1)'
                    : 'rgba(255,255,255,0.5)',
                  color: agent.status === 'published'
                    ? 'var(--ae-success)'
                    : 'var(--ae-muted)',
                  borderRadius: 8,
                }}
              />
              <Dropdown
                menu={{
                  items: [
                    {
                      key: 'chat',
                      icon: <PlayCircleOutlined />,
                      label: 'Chat',
                      onClick: (e) => {
                        e.domEvent.stopPropagation();
                        router.push(`/agents/${agent.id}/chat`);
                      },
                    },
                    {
                      key: 'edit',
                      icon: <EditOutlined />,
                      label: 'Edit',
                      onClick: (e) => {
                        e.domEvent.stopPropagation();
                        router.push(`/agents/${agent.id}`);
                      },
                    },
                    { type: 'divider' as const },
                    {
                      key: 'delete',
                      icon: <DeleteOutlined />,
                      label: 'Delete',
                      danger: true,
                      onClick: (e) => {
                        e.domEvent.stopPropagation();
                        onDelete(agent.id);
                      },
                    },
                  ],
                }}
                trigger={['click']}
              >
                <Button
                  type="text"
                  size="small"
                  icon={<MoreOutlined />}
                  onClick={(e) => e.stopPropagation()}
                  style={{ color: 'var(--ae-muted)' }}
                />
              </Dropdown>
            </div>

            <Text
              style={{
                display: 'block',
                fontSize: 15,
                fontWeight: 600,
                color: 'var(--ae-text)',
                marginBottom: 4,
                lineHeight: 1.3,
              }}
            >
              {agent.name}
            </Text>

            <Paragraph
              ellipsis={{ rows: 2 }}
              style={{
                fontSize: 13,
                color: 'var(--ae-muted)',
                marginBottom: 12,
                minHeight: 40,
                lineHeight: 1.5,
              }}
            >
              {agent.description || 'No description'}
            </Paragraph>

            <Space wrap size="small">
              <Tag
                style={{
                  margin: 0,
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 500,
                  border: 'none',
                  background: agent.status === 'published'
                    ? 'rgba(111,155,124,0.1)'
                    : 'rgba(255,255,255,0.5)',
                  color: agent.status === 'published'
                    ? 'var(--ae-success)'
                    : 'var(--ae-muted)',
                }}
              >
                {agent.status}
              </Tag>
              <Tag
                style={{
                  margin: 0,
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 500,
                  border: 'none',
                  background: 'rgba(255,255,255,0.5)',
                  color: 'var(--ae-muted)',
                }}
              >
                {agent.model_name}
              </Tag>
            </Space>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}

// ─── List View ───
function AgentList({ agents, onDelete }: { agents: Agent[]; onDelete: (id: string) => void }) {
  const router = useRouter();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col gap-2"
    >
      {/* Header Row */}
      <div
        className="hidden md:grid px-4 py-2 text-xs font-medium uppercase tracking-wider"
        style={{
          color: 'var(--ae-muted)',
          letterSpacing: '0.02em',
          gridTemplateColumns: '2fr 1fr 1fr 120px',
          gap: 16,
        }}
      >
        <span>Agent</span>
        <span>Model</span>
        <span>Status</span>
        <span className="text-right">Actions</span>
      </div>

      {agents.map((agent, index) => (
        <motion.div
          key={agent.id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{
            duration: 0.25,
            delay: index * 0.03,
            ease: [0.25, 1, 0.5, 1],
          }}
          className="group flex items-center gap-4 px-4 py-3 rounded-lg cursor-pointer"
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            transition: 'background-color 150ms cubic-bezier(0.25, 1, 0.5, 1), box-shadow 150ms cubic-bezier(0.25, 1, 0.5, 1)',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = 'var(--ae-panel)';
            (e.currentTarget as HTMLElement).style.boxShadow = 'var(--ae-shadow-ambient-low)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = 'var(--ae-panel-strong)';
            (e.currentTarget as HTMLElement).style.boxShadow = 'none';
          }}
          onClick={() => router.push(`/agents/${agent.id}`)}
        >
          {/* Agent Info */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <Avatar
              size={36}
              icon={<RobotOutlined />}
              style={{
                background: agent.status === 'published'
                  ? 'rgba(111,155,124,0.1)'
                  : 'rgba(255,255,255,0.5)',
                color: agent.status === 'published'
                  ? 'var(--ae-success)'
                  : 'var(--ae-muted)',
                borderRadius: 6,
                flexShrink: 0,
              }}
            />
            <div className="min-w-0">
              <Text
                style={{
                  display: 'block',
                  fontWeight: 600,
                  fontSize: 14,
                  color: 'var(--ae-text)',
                  lineHeight: 1.4,
                }}
                ellipsis
              >
                {agent.name}
              </Text>
              <Text
                style={{
                  fontSize: 12,
                  color: 'var(--ae-muted)',
                  lineHeight: 1.4,
                }}
                ellipsis
              >
                {agent.description || 'No description'}
              </Text>
            </div>
          </div>

          {/* Model */}
          <div className="hidden md:block w-32 shrink-0">
            <Tag
              style={{
                margin: 0,
                borderRadius: 4,
                fontSize: 12,
                border: 'none',
                background: 'rgba(255,255,255,0.5)',
                color: 'var(--ae-muted)',
              }}
            >
              {agent.model_name}
            </Tag>
          </div>

          {/* Status */}
          <div className="hidden md:block w-24 shrink-0">
            <span
              className="inline-flex items-center gap-1.5 text-xs font-medium"
              style={{
                color: agent.status === 'published'
                  ? 'var(--ae-success)'
                  : 'var(--ae-muted)',
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: agent.status === 'published'
                    ? 'var(--ae-success)'
                    : 'var(--ae-muted)',
                }}
              />
              {agent.status}
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-1 shrink-0">
            <Button
              type="text"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                router.push(`/agents/${agent.id}/chat`);
              }}
              style={{ color: 'var(--ae-accent-gold)' }}
              className="opacity-0 group-hover:opacity-100 transition-opacity"
            />
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                onDelete(agent.id);
              }}
              style={{ color: 'var(--ae-danger)' }}
              className="opacity-0 group-hover:opacity-100 transition-opacity"
            />
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
