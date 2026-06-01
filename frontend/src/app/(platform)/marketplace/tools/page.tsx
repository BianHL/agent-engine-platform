'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Row, Col, Typography, Input, Select, Space, Spin, Empty, Button,
  Segmented, Badge, Skeleton, Grid,
} from 'antd';
import {
  AppstoreOutlined, UnorderedListOutlined, SearchOutlined,
  FireOutlined, StarOutlined, ToolOutlined, DownloadOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';
import type { ToolMarketplaceItem } from '@/types/marketplace';
import ToolCard from '@/components/marketplace/ToolCard';
import ToolDetail from '@/components/marketplace/ToolDetail';
import ToolCategoryFilter from '@/components/marketplace/ToolCategoryFilter';
import ToolInstallDialog from '@/components/marketplace/ToolInstallDialog';

const { Title, Paragraph, Text } = Typography;
const { Search } = Input;

// Mock data for development - replace with actual API calls
const MOCK_TOOLS: ToolMarketplaceItem[] = [
  {
    id: '1', name: 'web_search', display_name: 'Web Search', description: 'Search the web for real-time information using multiple search engines.',
    category: 'AI', tags: ['search', 'web', 'real-time'], version: '2.1.0', author: 'Platform Team',
    install_count: 1250, avg_rating: 4.6, rating_count: 89, featured: true, verified: true,
    status: 'active', created_at: '2025-01-15', updated_at: '2025-05-20',
    examples: [{ title: 'Basic Search', description: 'Search for a topic', input: { query: 'latest AI news' } }],
  },
  {
    id: '2', name: 'code_executor', display_name: 'Code Executor', description: 'Execute Python, JavaScript, and shell code in a sandboxed environment.',
    category: 'Utility', tags: ['code', 'sandbox', 'python', 'javascript'], version: '1.5.0', author: 'Platform Team',
    install_count: 980, avg_rating: 4.4, rating_count: 67, featured: true, verified: true,
    status: 'active', created_at: '2025-02-01', updated_at: '2025-05-18',
  },
  {
    id: '3', name: 'database_query', display_name: 'Database Query', description: 'Execute SQL queries against connected databases with safety guardrails.',
    category: 'Data', tags: ['sql', 'database', 'query'], version: '1.2.0', author: 'Data Team',
    install_count: 750, avg_rating: 4.3, rating_count: 45, featured: false, verified: true,
    status: 'active', created_at: '2025-03-10', updated_at: '2025-05-15',
  },
  {
    id: '4', name: 'email_sender', display_name: 'Email Sender', description: 'Send emails with templates, attachments, and scheduling support.',
    category: 'Communication', tags: ['email', 'smtp', 'templates'], version: '1.0.0', author: 'Integration Team',
    install_count: 520, avg_rating: 4.1, rating_count: 32, featured: false, verified: true,
    status: 'active', created_at: '2025-04-01', updated_at: '2025-05-10',
  },
  {
    id: '5', name: 'file_manager', display_name: 'File Manager', description: 'Read, write, and manage files across local and cloud storage.',
    category: 'Storage', tags: ['files', 'cloud', 's3'], version: '1.3.0', author: 'Platform Team',
    install_count: 680, avg_rating: 4.2, rating_count: 38, featured: false, verified: true,
    status: 'active', created_at: '2025-02-20', updated_at: '2025-05-12',
  },
  {
    id: '6', name: 'data_analyzer', display_name: 'Data Analyzer', description: 'Analyze datasets with statistical methods, charts, and export capabilities.',
    category: 'Analytics', tags: ['data', 'statistics', 'charts'], version: '2.0.0', author: 'Analytics Team',
    install_count: 430, avg_rating: 4.5, rating_count: 28, featured: true, verified: true,
    status: 'active', created_at: '2025-03-15', updated_at: '2025-05-22',
  },
  {
    id: '7', name: 'slack_bot', display_name: 'Slack Bot', description: 'Interact with Slack workspaces - send messages, manage channels, and automate workflows.',
    category: 'Integration', tags: ['slack', 'messaging', 'automation'], version: '1.1.0', author: 'Integration Team',
    install_count: 390, avg_rating: 4.0, rating_count: 25, featured: false, verified: false,
    status: 'beta', created_at: '2025-04-10', updated_at: '2025-05-08',
  },
  {
    id: '8', name: 'image_generator', display_name: 'Image Generator', description: 'Generate images from text prompts using DALL-E and Stable Diffusion models.',
    category: 'AI', tags: ['image', 'generation', 'dall-e'], version: '1.0.0', author: 'AI Team',
    install_count: 870, avg_rating: 4.7, rating_count: 56, featured: true, verified: true,
    status: 'active', created_at: '2025-01-25', updated_at: '2025-05-25',
  },
  {
    id: '9', name: 'workflow_automation', display_name: 'Workflow Automation', description: 'Create and manage automated workflows with triggers, conditions, and actions.',
    category: 'Automation', tags: ['workflow', 'automation', 'triggers'], version: '1.4.0', author: 'Automation Team',
    install_count: 310, avg_rating: 4.3, rating_count: 22, featured: false, verified: true,
    status: 'active', created_at: '2025-03-20', updated_at: '2025-05-14',
  },
  {
    id: '10', name: 'security_scanner', display_name: 'Security Scanner', description: 'Scan code and infrastructure for security vulnerabilities and compliance issues.',
    category: 'Security', tags: ['security', 'scanning', 'compliance'], version: '1.2.0', author: 'Security Team',
    install_count: 280, avg_rating: 4.4, rating_count: 18, featured: false, verified: true,
    status: 'active', created_at: '2025-04-05', updated_at: '2025-05-16',
  },
  {
    id: '11', name: 'translation_service', display_name: 'Translation Service', description: 'Translate text between 100+ languages with context-aware accuracy.',
    category: 'AI', tags: ['translation', 'language', 'nlp'], version: '1.1.0', author: 'AI Team',
    install_count: 450, avg_rating: 4.2, rating_count: 30, featured: false, verified: true,
    status: 'active', created_at: '2025-02-28', updated_at: '2025-05-11',
  },
  {
    id: '12', name: 'vector_store', display_name: 'Vector Store', description: 'Store and retrieve vector embeddings for semantic search and RAG applications.',
    category: 'Data', tags: ['vector', 'embeddings', 'rag'], version: '1.0.0', author: 'Data Team',
    install_count: 560, avg_rating: 4.5, rating_count: 35, featured: false, verified: true,
    status: 'beta', created_at: '2025-05-01', updated_at: '2025-05-28',
  },
];

export default function ToolMarketplacePage() {
  const [tools, setTools] = useState<ToolMarketplaceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [sortBy, setSortBy] = useState('featured');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedTool, setSelectedTool] = useState<ToolMarketplaceItem | null>(null);
  const [installTool, setInstallTool] = useState<ToolMarketplaceItem | null>(null);
  const [categoryCounts, setCategoryCounts] = useState<Record<string, number>>({});

  const loadTools = useCallback(async () => {
    setLoading(true);
    try {
      // Try loading from API first, fall back to mock data
      try {
        const data = await api.listMarketplaceItems({
          keyword: searchKeyword,
          category: selectedCategory || undefined,
          asset_type: 'tool',
          sort_by: sortBy,
          page: 1,
          size: 100,
        });
        if (data.items && data.items.length > 0) {
          setTools(data.items);
        } else {
          // Use mock data if API returns empty
          applyFilters(MOCK_TOOLS);
        }
      } catch {
        // Use mock data if API fails
        applyFilters(MOCK_TOOLS);
      }
    } finally {
      setLoading(false);
    }
  }, [searchKeyword, selectedCategory, sortBy]);

  const applyFilters = (data: ToolMarketplaceItem[]) => {
    let filtered = [...data];

    // Filter by search keyword
    if (searchKeyword) {
      const kw = searchKeyword.toLowerCase();
      filtered = filtered.filter(
        (t) =>
          t.display_name.toLowerCase().includes(kw) ||
          t.description.toLowerCase().includes(kw) ||
          t.tags.some((tag) => tag.toLowerCase().includes(kw))
      );
    }

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter((t) => t.category === selectedCategory);
    }

    // Sort
    switch (sortBy) {
      case 'featured':
        filtered.sort((a, b) => (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || b.install_count - a.install_count);
        break;
      case 'popular':
        filtered.sort((a, b) => b.install_count - a.install_count);
        break;
      case 'rating':
        filtered.sort((a, b) => b.avg_rating - a.avg_rating);
        break;
      case 'newest':
        filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
    }

    setTools(filtered);

    // Calculate category counts
    const counts: Record<string, number> = { total: data.length };
    data.forEach((t) => {
      counts[t.category] = (counts[t.category] || 0) + 1;
    });
    setCategoryCounts(counts);
  };

  useEffect(() => {
    loadTools();
  }, [loadTools]);

  useEffect(() => {
    // Re-filter mock data when filters change
    if (tools.length > 0 || !loading) {
      applyFilters(MOCK_TOOLS);
    }
  }, [searchKeyword, selectedCategory, sortBy]);

  const handleSearch = (value: string) => {
    setSearchKeyword(value);
  };

  const handleToolClick = (tool: ToolMarketplaceItem) => {
    setSelectedTool(tool);
  };

  const handleBack = () => {
    setSelectedTool(null);
  };

  // If a tool is selected, show detail view
  if (selectedTool) {
    return (
      <ToolDetail
        toolId={selectedTool.id}
        onBack={handleBack}
      />
    );
  }

  // Skeleton loading component
  const SkeletonGrid = () => (
    <Row gutter={[16, 16]}>
      {Array.from({ length: 8 }).map((_, i) => (
        <Col key={i} xs={24} sm={12} md={8} lg={6}>
          <Card style={{ height: 240 }}>
            <Skeleton active paragraph={{ rows: 4 }} />
          </Card>
        </Col>
      ))}
    </Row>
  );

  const SkeletonList = () => (
    <Space direction="vertical" style={{ width: '100%' }} size={8}>
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <Skeleton active paragraph={{ rows: 1 }} />
        </Card>
      ))}
    </Space>
  );

  return (
    <div style={{ padding: '0 4px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>
          <ToolOutlined style={{ marginRight: 8 }} />
          Tool Marketplace
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Discover, install, and manage tools to extend your agents' capabilities
        </Paragraph>
      </div>

      {/* Search and Controls */}
      <div style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Search
              placeholder="Search tools by name, description, or tags..."
              allowClear
              enterButton={<><SearchOutlined /> Search</>}
              size="large"
              onSearch={handleSearch}
              style={{ maxWidth: 500 }}
            />
          </Col>
          <Col>
            <Space>
              <Select
                value={sortBy}
                onChange={setSortBy}
                style={{ width: 140 }}
                options={[
                  { value: 'featured', label: <><StarOutlined /> Featured</> },
                  { value: 'popular', label: <><FireOutlined /> Popular</> },
                  { value: 'rating', label: 'Top Rated' },
                  { value: 'newest', label: 'Newest' },
                ]}
              />
              <Segmented
                value={viewMode}
                onChange={(v) => setViewMode(v as 'grid' | 'list')}
                options={[
                  { value: 'grid', icon: <AppstoreOutlined /> },
                  { value: 'list', icon: <UnorderedListOutlined /> },
                ]}
              />
            </Space>
          </Col>
        </Row>
      </div>

      {/* Category Filter */}
      <div style={{ marginBottom: 24 }}>
        <ToolCategoryFilter
          selected={selectedCategory}
          onChange={setSelectedCategory}
          counts={categoryCounts}
        />
      </div>

      {/* Results count */}
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary">
          {loading ? 'Loading...' : `${tools.length} tools found`}
        </Text>
      </div>

      {/* Tool Grid/List */}
      {loading ? (
        viewMode === 'grid' ? <SkeletonGrid /> : <SkeletonList />
      ) : tools.length === 0 ? (
        <Empty
          image={<ToolOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
          description={
            <div>
              <Title level={5}>No tools found</Title>
              <Paragraph type="secondary">
                Try adjusting your search or filter criteria
              </Paragraph>
            </div>
          }
        >
          <Button
            type="primary"
            onClick={() => {
              setSearchKeyword('');
              setSelectedCategory('');
            }}
          >
            Clear Filters
          </Button>
        </Empty>
      ) : viewMode === 'grid' ? (
        <Row gutter={[16, 16]}>
          {tools.map((tool) => (
            <Col key={tool.id} xs={24} sm={12} md={8} lg={6}>
              <ToolCard
                tool={tool}
                viewMode="grid"
                onClick={handleToolClick}
              />
            </Col>
          ))}
        </Row>
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size={8}>
          {tools.map((tool) => (
            <ToolCard
              key={tool.id}
              tool={tool}
              viewMode="list"
              onClick={handleToolClick}
            />
          ))}
        </Space>
      )}

      {/* Install Dialog */}
      <ToolInstallDialog
        tool={installTool}
        open={!!installTool}
        onClose={() => setInstallTool(null)}
        onInstalled={() => loadTools()}
      />
    </div>
  );
}
