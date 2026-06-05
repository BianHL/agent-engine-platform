'use client';
import React, { useEffect, useState, useMemo } from 'react';
import {
  Card, Row, Col, Button, Tag, Typography, Spin, Input, Space,
  Badge, Empty, Rate, message,
} from 'antd';
import {
  FireOutlined, StarOutlined, SearchOutlined, ShopOutlined,
  AppstoreAddOutlined, ThunderboltOutlined, DatabaseOutlined,
  BranchesOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/lib/api';
import { MarketplaceListItem } from '@/types/marketplace';

const { Title, Paragraph, Text } = Typography;
const { Search } = Input;

const CATEGORIES = [
  'Customer Service', 'Production', 'Supply Chain', 'Finance',
  'Human Resources', 'Quality Control', 'Safety', 'Collaboration',
  'Data Analysis', 'Other',
];

const ASSET_TYPE_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  agent: { label: 'Agent', icon: <ThunderboltOutlined />, color: 'var(--ae-accent-gold)' },
  knowledge_base: { label: 'Knowledge Base', icon: <DatabaseOutlined />, color: 'var(--ae-accent-olive)' },
  workflow: { label: 'Workflow', icon: <BranchesOutlined />, color: 'var(--ae-success)' },
};

export default function MarketplacePage() {
  const router = useRouter();
  const [featured, setFeatured] = useState<MarketplaceListItem[]>([]);
  const [hot, setHot] = useState<MarketplaceListItem[]>([]);
  const [items, setItems] = useState<MarketplaceListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState('latest');
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadItems();
  }, [selectedCategory, sortBy, page, searchKeyword]);

  const loadData = async () => {
    try {
      const [f, h] = await Promise.all([
        api.getFeaturedItems(8),
        api.getHotItems(10),
      ]);
      setFeatured(f);
      setHot(h);
    } catch (err: any) {
      // Featured/hot sections fail silently -- main content still works
      console.warn('Failed to load featured/hot items:', err?.message);
    }
  };

  const loadItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listMarketplaceItems({
        keyword: searchKeyword,
        category: selectedCategory,
        sort_by: sortBy,
        page,
        size: 12,
      });
      setItems(data.items || []);
      setTotal(data.total || 0);
      setError(null);
    } catch (err: any) {
      const msg = err?.message || 'Failed to load marketplace items';
      setError(msg);
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setPage(1);
    // loadItems() will be triggered by useEffect when searchKeyword changes
  };

  // Gradient generator for asset covers (deterministic based on title)
  const getAssetGradient = (title: string) => {
    const gradients = [
      'linear-gradient(135deg, #1c1917 0%, #57534e 100%)',
      'linear-gradient(135deg, #0c4a6e 0%, #38bdf8 100%)',
      'linear-gradient(135deg, #b45309 0%, #fbbf24 100%)',
      'linear-gradient(135deg, #16a34a 0%, #4ade80 100%)',
      'linear-gradient(135deg, #44403c 0%, #a8a29e 100%)',
      'linear-gradient(135deg, #292524 0%, #78716c 100%)',
    ];
    let hash = 0;
    for (let i = 0; i < title.length; i++) hash = title.charCodeAt(i) + ((hash << 5) - hash);
    return gradients[Math.abs(hash) % gradients.length];
  };

  return (
    <div>
      {/* Hero Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.25, 1, 0.5, 1] }}
        className="mb-8"
      >
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
          <ShopOutlined style={{ marginRight: 12, color: 'var(--ae-accent-gold)' }} />
          Marketplace
        </Title>
        <Paragraph style={{ color: 'var(--ae-muted)', fontSize: 14, maxWidth: '65ch', marginTop: 4 }}>
          Discover, try, and clone high-quality AI assets across your organization. Accelerate innovation with proven agents, knowledge bases, and workflows.
        </Paragraph>
      </motion.div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className="mb-6"
      >
        <Search
          placeholder="Search agents, knowledge bases, workflows..."
          allowClear
          enterButton={
            <span className="flex items-center gap-1">
              <SearchOutlined /> Search
            </span>
          }
          size="large"
          onSearch={handleSearch}
          style={{ maxWidth: 600 }}
        />
      </motion.div>

      {/* Category Filters */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.3 }}
        className="mb-8"
      >
        <Space wrap size="small">
          <FilterPill
            active={selectedCategory === ''}
            onClick={() => setSelectedCategory('')}
          >
            All
          </FilterPill>
          {CATEGORIES.map((c) => (
            <FilterPill
              key={c}
              active={selectedCategory === c}
              onClick={() => setSelectedCategory(c)}
            >
              {c}
            </FilterPill>
          ))}
        </Space>
      </motion.div>

      {/* Featured Section */}
      {featured.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
          className="mb-10"
        >
          <div className="flex items-center gap-2 mb-4">
            <StarOutlined style={{ color: 'var(--ae-accent-gold)', fontSize: 16 }} />
            <Title
              level={4}
              style={{
                margin: 0,
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--ae-text)',
                letterSpacing: '-0.01em',
              }}
            >
              Featured
            </Title>
          </div>

          <Row gutter={[16, 16]}>
            {featured.slice(0, 4).map((item, index) => (
              <Col key={item.id} xs={24} sm={12} lg={6}>
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 + index * 0.05, duration: 0.35, ease: [0.25, 1, 0.5, 1] }}
                >
                  <FeaturedCard item={item} gradient={getAssetGradient(item.title)} />
                </motion.div>
              </Col>
            ))}
          </Row>
        </motion.div>
      )}

      {/* Hot Section */}
      {hot.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
          className="mb-10"
        >
          <div className="flex items-center gap-2 mb-4">
            <FireOutlined style={{ color: 'var(--ae-danger)', fontSize: 16 }} />
            <Title
              level={4}
              style={{
                margin: 0,
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--ae-text)',
                letterSpacing: '-0.01em',
              }}
            >
              Trending
            </Title>
          </div>

          <div className="flex gap-3 overflow-x-auto pb-2">
            {hot.slice(0, 6).map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.35 + index * 0.04, duration: 0.3, ease: [0.25, 1, 0.5, 1] }}
                className="flex-shrink-0"
              >
                <HotCard item={item} rank={index + 1} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* All Assets Header */}
      <div className="flex items-center justify-between mb-4">
        <Title
          level={4}
          style={{
            margin: 0,
            fontSize: 16,
            fontWeight: 600,
            color: 'var(--ae-text)',
            letterSpacing: '-0.01em',
          }}
        >
          All Assets
        </Title>
        <Space>
          <Space size="small">
            {['latest', 'hottest', 'rating', 'clones'].map((sort) => (
              <Button
                key={sort}
                type={sortBy === sort ? 'primary' : 'text'}
                size="small"
                onClick={() => { setSortBy(sort); setPage(1); }}
                style={
                  sortBy === sort
                    ? { background: 'var(--ae-accent-gold)', borderColor: 'var(--ae-accent-gold)' }
                    : { color: 'var(--ae-muted)' }
                }
              >
                {sort === 'latest' && 'Latest'}
                {sort === 'hottest' && 'Hot'}
                {sort === 'rating' && 'Top Rated'}
                {sort === 'clones' && 'Most Cloned'}
              </Button>
            ))}
          </Space>
          <Button
            type="primary"
            icon={<AppstoreAddOutlined />}
            onClick={() => router.push('/marketplace/submit')}
            style={{ background: 'var(--ae-accent-gold)', borderColor: 'var(--ae-accent-gold)' }}
          >
            Submit
          </Button>
        </Space>
      </div>

      {/* Items Grid */}
      {loading ? (
        <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '48px 0' }}>
          <p style={{ color: 'var(--ae-muted)', marginBottom: 16 }}>{error}</p>
          <Button icon={<ReloadOutlined />} onClick={() => { loadItems(); loadData(); }}>
            Retry
          </Button>
        </div>
      ) : items.length === 0 ? (
        <Empty description="No assets found" />
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {items.map((item, index) => (
              <Col key={item.id} xs={24} sm={12} md={8} lg={6}>
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03, duration: 0.3, ease: [0.25, 1, 0.5, 1] }}
                >
                  <AssetCard item={item} gradient={getAssetGradient(item.title)} />
                </motion.div>
              </Col>
            ))}
          </Row>
          {total > 12 && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Button
                onClick={() => setPage(page + 1)}
                disabled={items.length < 12}
                style={{ borderRadius: 6 }}
              >
                Load More
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Filter Pill ───
function FilterPill({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 text-sm font-medium rounded-full transition-all duration-fast ease-out-quart"
      style={{
        background: active ? 'var(--ae-accent-gold)' : 'rgba(255,255,255,0.5)',
        color: active ? 'rgba(255,255,255,0.95)' : 'var(--ae-muted)',
        border: active ? '1px solid var(--ae-accent-gold)' : '1px solid var(--ae-line)',
      }}
      onMouseEnter={(e) => {
        if (!active) {
          (e.currentTarget as HTMLButtonElement).style.background = 'var(--ae-line-strong)';
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.5)';
        }
      }}
    >
      {children}
    </button>
  );
}

// ─── Featured Card ───
function FeaturedCard({ item, gradient }: { item: MarketplaceListItem; gradient: string }) {
  const router = useRouter();
  const typeConfig = ASSET_TYPE_CONFIG[item.asset_type] || { label: item.asset_type, icon: <AppstoreAddOutlined />, color: 'var(--ae-muted)' };

  return (
    <Card
      hoverable
      onClick={() => router.push(`/marketplace/${item.id}`)}
      bordered={false}
      style={{
        borderRadius: 8,
        overflow: 'hidden',
        border: '1px solid var(--ae-line)',
        transition: 'box-shadow 150ms cubic-bezier(0.25, 1, 0.5, 1)',
      }}
      bodyStyle={{ padding: 0 }}
    >
      {/* Cover */}
      <div
        style={{
          height: 120,
          background: gradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        <span
          style={{
            fontSize: 48,
            fontWeight: 800,
            color: 'rgba(255,255,255,0.25)',
            letterSpacing: '-0.04em',
            userSelect: 'none',
          }}
        >
          {item.title.charAt(0)}
        </span>
        {item.featured && (
          <Badge
            count="Featured"
            style={{
              position: 'absolute',
              top: 12,
              right: 12,
              background: 'var(--ae-success)',
              fontSize: 11,
              fontWeight: 600,
              padding: '2px 10px',
              borderRadius: 4,
            }}
          />
        )}
      </div>

      {/* Content */}
      <div style={{ padding: 16 }}>
        <div className="flex items-center gap-2 mb-2">
          <span style={{ color: typeConfig.color, fontSize: 12 }}>{typeConfig.icon}</span>
          <Text style={{ fontSize: 12, color: typeConfig.color, fontWeight: 500 }}>
            {typeConfig.label}
          </Text>
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
          ellipsis
        >
          {item.title}
        </Text>

        <Paragraph
          ellipsis={{ rows: 2 }}
          style={{
            fontSize: 13,
            color: 'var(--ae-muted)',
            marginBottom: 12,
            lineHeight: 1.5,
            minHeight: 40,
          }}
        >
          {item.summary || 'No description available'}
        </Paragraph>

        <div className="flex items-center justify-between">
          <Rate
            disabled
            value={item.avg_rating}
            style={{ fontSize: 12 }}
          />
          <Text style={{ fontSize: 12, color: 'var(--ae-muted)' }}>
            {item.usage_count} uses
          </Text>
        </div>
      </div>
    </Card>
  );
}

// ─── Hot Card (compact horizontal) ───
function HotCard({ item, rank }: { item: MarketplaceListItem; rank: number }) {
  const router = useRouter();

  return (
    <Card
      size="small"
      hoverable
      onClick={() => router.push(`/marketplace/${item.id}`)}
      bordered={false}
      style={{
        width: 220,
        borderRadius: 8,
        border: '1px solid var(--ae-line)',
        background: 'var(--ae-panel-strong)',
      }}
      bodyStyle={{ padding: 12 }}
    >
      <Space>
        <Badge
          count={rank}
          style={{
            backgroundColor: rank <= 3 ? 'var(--ae-accent-gold)' : 'var(--ae-muted)',
            fontWeight: 700,
            fontSize: 11,
            minWidth: 20,
            height: 20,
            lineHeight: '20px',
            borderRadius: 4,
          }}
        />
        <Text
          ellipsis
          style={{
            maxWidth: 140,
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--ae-text)',
          }}
        >
          {item.title}
        </Text>
      </Space>
      <div className="mt-1 flex items-center justify-between">
        <Text style={{ fontSize: 11, color: 'var(--ae-muted)' }}>
          {item.usage_count} uses
        </Text>
        {item.avg_rating > 0 && (
          <Rate disabled value={item.avg_rating} style={{ fontSize: 10 }} />
        )}
      </div>
    </Card>
  );
}

// ─── Standard Asset Card ───
function AssetCard({ item, gradient }: { item: MarketplaceListItem; gradient: string }) {
  const router = useRouter();
  const typeConfig = ASSET_TYPE_CONFIG[item.asset_type] || { label: item.asset_type, icon: <AppstoreAddOutlined />, color: 'var(--ae-muted)' };

  return (
    <Card
      hoverable
      onClick={() => router.push(`/marketplace/${item.id}`)}
      bordered={false}
      style={{
        height: '100%',
        borderRadius: 8,
        border: '1px solid var(--ae-line)',
        overflow: 'hidden',
        transition: 'box-shadow 150ms cubic-bezier(0.25, 1, 0.5, 1)',
      }}
      bodyStyle={{ padding: 0 }}
      cover={
        <div
          style={{
            height: 140,
            background: gradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          <span
            style={{
              fontSize: 40,
              fontWeight: 800,
              color: 'rgba(255,255,255,0.2)',
              letterSpacing: '-0.04em',
              userSelect: 'none',
            }}
          >
            {item.title.charAt(0)}
          </span>
        </div>
      }
    >
      <div style={{ padding: 16 }}>
        <div className="flex items-center gap-2 mb-2">
          <span style={{ color: typeConfig.color, fontSize: 12 }}>{typeConfig.icon}</span>
          <Text style={{ fontSize: 12, color: typeConfig.color, fontWeight: 500 }}>
            {typeConfig.label}
          </Text>
          {item.featured && (
            <Tag
              style={{
                margin: 0,
                marginLeft: 'auto',
                fontSize: 11,
                fontWeight: 600,
                borderRadius: 4,
                border: 'none',
                background: 'rgba(111,155,124,0.1)',
                color: 'var(--ae-success)',
              }}
            >
              Featured
            </Tag>
          )}
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
          ellipsis
        >
          {item.title}
        </Text>

        <Paragraph
          ellipsis={{ rows: 2 }}
          style={{
            fontSize: 13,
            color: 'var(--ae-muted)',
            marginBottom: 12,
            lineHeight: 1.5,
            minHeight: 40,
          }}
        >
          {item.summary || 'No description available'}
        </Paragraph>

        <div className="flex items-center justify-between">
          <Space size="small">
            {item.category && (
              <Text style={{ fontSize: 11, color: 'var(--ae-muted)' }}>
                {item.category}
              </Text>
            )}
          </Space>
          <Text style={{ fontSize: 11, color: 'var(--ae-muted)' }}>
            {item.usage_count} uses
          </Text>
        </div>
      </div>
    </Card>
  );
}
