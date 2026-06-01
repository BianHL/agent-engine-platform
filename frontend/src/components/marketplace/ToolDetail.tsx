'use client';
import React, { useEffect, useState } from 'react';
import {
  Card, Typography, Tag, Space, Button, Tabs, Descriptions, Spin, message,
  Row, Col, Statistic, Divider, Collapse, Empty,
} from 'antd';
import {
  DownloadOutlined, StarFilled, ArrowLeftOutlined, CheckCircleFilled,
  GithubOutlined, LinkOutlined, CopyOutlined, PlayCircleOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import type { ToolMarketplaceItem, ToolExample } from '@/types/marketplace';
import ToolRating from './ToolRating';
import ToolInstallDialog from './ToolInstallDialog';

const { Title, Paragraph, Text } = Typography;

interface ToolDetailProps {
  toolId: string;
  onBack?: () => void;
}

export default function ToolDetail({ toolId, onBack }: ToolDetailProps) {
  const router = useRouter();
  const [tool, setTool] = useState<ToolMarketplaceItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [installOpen, setInstallOpen] = useState(false);

  useEffect(() => {
    loadTool();
  }, [toolId]);

  const loadTool = async () => {
    setLoading(true);
    try {
      const data = await api.getMarketplaceItem(toolId);
      setTool(data);
    } catch {
      message.error('Failed to load tool details');
    } finally {
      setLoading(false);
    }
  };

  const handleTestTool = async () => {
    if (!tool) return;
    try {
      const result = await api.executeTool(tool.name, {});
      message.success('Tool executed successfully');
    } catch (e: any) {
      message.error(e?.response?.data?.detail || 'Test execution failed');
    }
  };

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (!tool) {
    return <Empty description="Tool not found" />;
  }

  const renderExamples = (examples: ToolExample[]) => {
    if (!examples || examples.length === 0) return <Empty description="No examples available" />;

    return (
      <Collapse
        items={examples.map((ex, idx) => ({
          key: idx,
          label: ex.title,
          children: (
            <div>
              <Paragraph>{ex.description}</Paragraph>
              <div style={{ marginBottom: 12 }}>
                <Text strong>Input:</Text>
                <pre style={{
                  background: '#f5f5f5',
                  padding: 12,
                  borderRadius: 6,
                  fontSize: 12,
                  overflow: 'auto',
                  marginTop: 4,
                }}>
                  {JSON.stringify(ex.input, null, 2)}
                </pre>
              </div>
              {ex.expected_output && (
                <div>
                  <Text strong>Expected Output:</Text>
                  <pre style={{
                    background: '#f6ffed',
                    padding: 12,
                    borderRadius: 6,
                    fontSize: 12,
                    marginTop: 4,
                  }}>
                    {ex.expected_output}
                  </pre>
                </div>
              )}
            </div>
          ),
        }))}
      />
    );
  };

  return (
    <div style={{ padding: '0 4px' }}>
      {/* Back button */}
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={onBack || (() => router.push('/marketplace/tools'))}
        style={{ marginBottom: 16 }}
      >
        Back to Tools
      </Button>

      {/* Header Card */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={24}>
          <Col flex="auto">
            <Space wrap style={{ marginBottom: 8 }}>
              <Tag color="blue">{tool.category}</Tag>
              {tool.status === 'beta' && <Tag color="orange">Beta</Tag>}
              {tool.status === 'deprecated' && <Tag color="red">Deprecated</Tag>}
              {tool.verified && (
                <Tag icon={<CheckCircleFilled />} color="processing">Verified</Tag>
              )}
            </Space>
            <Title level={3} style={{ marginBottom: 4 }}>
              {tool.display_name}
              <Text type="secondary" style={{ fontSize: 14, fontWeight: 'normal', marginLeft: 12 }}>
                v{tool.version}
              </Text>
            </Title>
            <Paragraph type="secondary">{tool.description}</Paragraph>
            <Space size="large">
              <Statistic
                title="Rating"
                value={tool.avg_rating}
                suffix={<><StarFilled style={{ color: '#faad14' }} /> / 5 ({tool.rating_count})</>}
              />
              <Statistic title="Installs" value={tool.install_count} prefix={<DownloadOutlined />} />
            </Space>
          </Col>
          <Col>
            <Space direction="vertical" size="middle">
              <Button
                type="primary"
                size="large"
                icon={<DownloadOutlined />}
                onClick={() => setInstallOpen(true)}
              >
                {tool.installed ? 'Manage' : 'Install'}
              </Button>
              <Button
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleTestTool}
              >
                Test Run
              </Button>
              {tool.repository && (
                <Button
                  size="large"
                  icon={<GithubOutlined />}
                  href={tool.repository}
                  target="_blank"
                >
                  Source
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Details Card */}
      <Card>
        <Tabs
          items={[
            {
              key: 'overview',
              label: 'Overview',
              children: (
                <div style={{ minHeight: 200 }}>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label="Author">{tool.author}</Descriptions.Item>
                    <Descriptions.Item label="Category">{tool.category}</Descriptions.Item>
                    <Descriptions.Item label="Version">v{tool.version}</Descriptions.Item>
                    <Descriptions.Item label="Status">
                      <Tag color={tool.status === 'active' ? 'green' : tool.status === 'beta' ? 'orange' : 'red'}>
                        {tool.status}
                      </Tag>
                    </Descriptions.Item>
                    {tool.license && <Descriptions.Item label="License">{tool.license}</Descriptions.Item>}
                    {tool.homepage && (
                      <Descriptions.Item label="Homepage">
                        <a href={tool.homepage} target="_blank" rel="noopener noreferrer">
                          <LinkOutlined /> {tool.homepage}
                        </a>
                      </Descriptions.Item>
                    )}
                    {tool.repository && (
                      <Descriptions.Item label="Repository">
                        <a href={tool.repository} target="_blank" rel="noopener noreferrer">
                          <GithubOutlined /> {tool.repository}
                        </a>
                      </Descriptions.Item>
                    )}
                    <Descriptions.Item label="Tags">
                      <Space wrap>
                        {tool.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)}
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="Created">{tool.created_at}</Descriptions.Item>
                    <Descriptions.Item label="Updated">{tool.updated_at}</Descriptions.Item>
                  </Descriptions>
                </div>
              ),
            },
            {
              key: 'examples',
              label: 'Usage Examples',
              children: (
                <div style={{ minHeight: 200 }}>
                  {renderExamples(tool.examples || [])}
                </div>
              ),
            },
            {
              key: 'config',
              label: 'Configuration',
              children: (
                <div style={{ minHeight: 200 }}>
                  {tool.config_schema ? (
                    <pre style={{
                      background: '#f5f5f5',
                      padding: 16,
                      borderRadius: 8,
                      fontSize: 12,
                      overflow: 'auto',
                    }}>
                      {JSON.stringify(tool.config_schema, null, 2)}
                    </pre>
                  ) : (
                    <Empty description="No configuration schema available" />
                  )}
                </div>
              ),
            },
            {
              key: 'changelog',
              label: 'Changelog',
              children: (
                <div style={{ minHeight: 200 }}>
                  {tool.changelog ? (
                    <div dangerouslySetInnerHTML={{ __html: tool.changelog.replace(/\n/g, '<br/>') }} />
                  ) : (
                    <Empty description="No changelog available" />
                  )}
                </div>
              ),
            },
            {
              key: 'ratings',
              label: `Ratings (${tool.rating_count})`,
              children: (
                <ToolRating
                  toolId={tool.id}
                  avgRating={tool.avg_rating}
                  ratingCount={tool.rating_count}
                  onRatingSubmitted={loadTool}
                />
              ),
            },
          ]}
        />
      </Card>

      {/* Install Dialog */}
      <ToolInstallDialog
        tool={tool}
        open={installOpen}
        onClose={() => setInstallOpen(false)}
        onInstalled={loadTool}
      />
    </div>
  );
}
