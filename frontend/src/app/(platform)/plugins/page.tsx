'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Row, Col, Typography, Tag, Button, Space, Input, Select, message,
  Modal, Rate, Empty, Spin, Tabs, List, Avatar,
} from 'antd';
import {
  SearchOutlined, DownloadOutlined, DeleteOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text, Paragraph } = Typography;

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  tags: string[];
  downloads: number;
  rating: number;
  rating_count: number;
}

interface InstalledPlugin {
  id: string;
  plugin_id: string;
  status: string;
  installed_at: string;
}

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [installed, setInstalled] = useState<InstalledPlugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string | undefined>();
  const [sortBy, setSortBy] = useState('popular');

  const fetchPlugins = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/plugins', { params: { category, search, sort_by: sortBy } });
      setPlugins(Array.isArray(res) ? res : []);
    } catch { setPlugins([]); } finally { setLoading(false); }
  }, [category, search, sortBy]);

  const fetchInstalled = useCallback(async () => {
    try {
      const res = await api.get('/plugins/installed');
      setInstalled(Array.isArray(res) ? res : []);
    } catch { setInstalled([]); }
  }, []);

  useEffect(() => { fetchPlugins(); fetchInstalled(); }, []);
  useEffect(() => { fetchPlugins(); }, [category, sortBy]);

  const isInstalled = (id: string) => installed.some(i => i.plugin_id === id);

  const handleInstall = async (id: string) => {
    try {
      await api.post(`/plugins/${id}/install`);
      message.success('Plugin installed');
      fetchInstalled();
      fetchPlugins();
    } catch { message.error('Failed to install'); }
  };

  const handleUninstall = async (id: string) => {
    Modal.confirm({
      title: 'Uninstall plugin?',
      onOk: async () => {
        await api.delete(`/plugins/${id}/uninstall`);
        message.success('Plugin uninstalled');
        fetchInstalled();
      },
    });
  };

  const categoryColors: Record<string, string> = {
    ai: '#1890ff', data: '#52c41a', integration: '#722ed1', automation: '#fa8c16',
    communication: '#13c2c2', storage: '#2f54eb', analytics: '#eb2f96', security: '#f5222d',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4}>Plugin Marketplace</Title>
        <Space>
          <Input placeholder="Search..." prefix={<SearchOutlined />} value={search}
            onChange={e => setSearch(e.target.value)} onPressEnter={fetchPlugins} style={{ width: 200 }} />
          <Select placeholder="Category" allowClear style={{ width: 140 }} value={category} onChange={setCategory}
            options={Object.keys(categoryColors).map(c => ({ value: c, label: c }))} />
          <Select value={sortBy} onChange={setSortBy} options={[
            { value: 'popular', label: 'Popular' }, { value: 'rating', label: 'Top Rated' },
            { value: 'newest', label: 'Newest' },
          ]} />
        </Space>
      </div>

      <Tabs items={[
        {
          key: 'all', label: `All Plugins (${plugins.length})`,
          children: loading ? <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div> :
            plugins.length === 0 ? <Empty description="No plugins found" /> : (
              <Row gutter={[16, 16]}>
                {plugins.map(plugin => (
                  <Col key={plugin.id} xs={24} sm={12} lg={8} xl={6}>
                    <Card hoverable actions={[
                      isInstalled(plugin.id) ?
                        <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleUninstall(plugin.id)}>Uninstall</Button> :
                        <Button type="link" icon={<DownloadOutlined />} onClick={() => handleInstall(plugin.id)}>Install</Button>,
                    ]}>
                      <Card.Meta
                        avatar={<Avatar size={48} style={{ background: categoryColors[plugin.category] || '#666' }}>{plugin.name[0]}</Avatar>}
                        title={<Space>{plugin.name}<Tag color={categoryColors[plugin.category]}>{plugin.category}</Tag></Space>}
                        description={<>
                          <Paragraph ellipsis={{ rows: 2 }}>{plugin.description}</Paragraph>
                          <Space><Rate disabled defaultValue={plugin.rating} allowHalf style={{ fontSize: 12 }} /><Text type="secondary">({plugin.rating_count})</Text></Space>
                        </>}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            ),
        },
        {
          key: 'installed', label: `Installed (${installed.length})`,
          children: installed.length === 0 ? <Empty description="No plugins installed" /> : (
            <List dataSource={installed} renderItem={item => (
              <List.Item actions={[<Button danger icon={<DeleteOutlined />} onClick={() => handleUninstall(item.plugin_id)}>Uninstall</Button>]}>
                <List.Item.Meta title={item.plugin_id} description={<Tag color={item.status === 'active' ? 'green' : 'default'}>{item.status}</Tag>} />
              </List.Item>
            )} />
          ),
        },
      ]} />
    </div>
  );
}
