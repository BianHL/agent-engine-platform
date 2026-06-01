'use client';
import React from 'react';
import { Card, Tag, Typography, Space, Rate, Badge, Avatar, Tooltip } from 'antd';
import {
  DownloadOutlined, StarFilled, CheckCircleFilled, ExperimentOutlined,
  RobotOutlined, DatabaseOutlined, ApiOutlined, ThunderboltOutlined,
  MessageOutlined, CloudOutlined, BarChartOutlined, SafetyOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import type { ToolMarketplaceItem, ToolCategory } from '@/types/marketplace';

const { Text, Paragraph } = Typography;

const CATEGORY_ICON_MAP: Record<ToolCategory, React.ReactNode> = {
  AI: <RobotOutlined />,
  Data: <DatabaseOutlined />,
  Integration: <ApiOutlined />,
  Automation: <ThunderboltOutlined />,
  Communication: <MessageOutlined />,
  Storage: <CloudOutlined />,
  Analytics: <BarChartOutlined />,
  Security: <SafetyOutlined />,
  Utility: <ToolOutlined />,
};

const CATEGORY_COLOR_MAP: Record<ToolCategory, string> = {
  AI: '#722ed1',
  Data: '#1890ff',
  Integration: '#13c2c2',
  Automation: '#fa8c16',
  Communication: '#52c41a',
  Storage: '#2f54eb',
  Analytics: '#eb2f96',
  Security: '#f5222d',
  Utility: '#595959',
};

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  active: { color: 'green', label: 'Stable' },
  beta: { color: 'orange', label: 'Beta' },
  deprecated: { color: 'red', label: 'Deprecated' },
};

interface ToolCardProps {
  tool: ToolMarketplaceItem;
  onClick?: (tool: ToolMarketplaceItem) => void;
  viewMode?: 'grid' | 'list';
}

export default function ToolCard({ tool, onClick, viewMode = 'grid' }: ToolCardProps) {
  const categoryIcon = CATEGORY_ICON_MAP[tool.category as ToolCategory] || <ToolOutlined />;
  const categoryColor = CATEGORY_COLOR_MAP[tool.category as ToolCategory] || '#595959';
  const statusCfg = STATUS_CONFIG[tool.status] || STATUS_CONFIG.active;

  if (viewMode === 'list') {
    return (
      <Card
        hoverable
        onClick={() => onClick?.(tool)}
        style={{ marginBottom: 8 }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Avatar
            size={48}
            icon={categoryIcon}
            style={{ backgroundColor: categoryColor, flexShrink: 0 }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <Space>
              <Text strong style={{ fontSize: 15 }}>{tool.display_name}</Text>
              {tool.verified && <CheckCircleFilled style={{ color: '#1890ff', fontSize: 14 }} />}
              {tool.featured && <Badge count="Featured" style={{ backgroundColor: '#52c41a' }} />}
              <Tag color={statusCfg.color} style={{ marginLeft: 4 }}>{statusCfg.label}</Tag>
            </Space>
            <Paragraph ellipsis={{ rows: 1 }} style={{ marginBottom: 0, marginTop: 4 }}>
              {tool.description}
            </Paragraph>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexShrink: 0 }}>
            <div style={{ textAlign: 'center' }}>
              <Rate disabled value={tool.avg_rating} allowHalf style={{ fontSize: 12 }} />
              <div><Text type="secondary" style={{ fontSize: 12 }}>{tool.rating_count}</Text></div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <DownloadOutlined style={{ fontSize: 16, color: '#8c8c8c' }} />
              <div><Text type="secondary" style={{ fontSize: 12 }}>{tool.install_count}</Text></div>
            </div>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>v{tool.version}</Text>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Badge.Ribbon text={tool.featured ? 'Featured' : undefined} color="green">
      <Card
        hoverable
        onClick={() => onClick?.(tool)}
        style={{ height: '100%' }}
        styles={{
          body: { padding: 16, display: 'flex', flexDirection: 'column', height: '100%' },
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <Avatar
            size={40}
            icon={categoryIcon}
            style={{ backgroundColor: categoryColor, flexShrink: 0 }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <Space size={4}>
              <Text strong style={{ fontSize: 14 }} ellipsis>{tool.display_name}</Text>
              {tool.verified && <CheckCircleFilled style={{ color: '#1890ff', fontSize: 13 }} />}
            </Space>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>{tool.author}</Text>
            </div>
          </div>
        </div>

        <Paragraph
          ellipsis={{ rows: 2 }}
          style={{ marginBottom: 12, flex: 1, minHeight: 44, fontSize: 13 }}
        >
          {tool.description}
        </Paragraph>

        <Space wrap size={[4, 4]} style={{ marginBottom: 12 }}>
          <Tag color={categoryColor} style={{ margin: 0 }}>{tool.category}</Tag>
          <Tag color={statusCfg.color} style={{ margin: 0 }}>{statusCfg.label}</Tag>
          {tool.tags.slice(0, 2).map((tag) => (
            <Tag key={tag} style={{ margin: 0 }}>{tag}</Tag>
          ))}
        </Space>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f0f0f0', paddingTop: 8 }}>
          <Space size={12}>
            <Tooltip title={`${tool.avg_rating.toFixed(1)} / 5`}>
              <Space size={4}>
                <StarFilled style={{ color: '#faad14', fontSize: 13 }} />
                <Text type="secondary" style={{ fontSize: 12 }}>{tool.avg_rating.toFixed(1)}</Text>
              </Space>
            </Tooltip>
            <Tooltip title="Installations">
              <Space size={4}>
                <DownloadOutlined style={{ fontSize: 13, color: '#8c8c8c' }} />
                <Text type="secondary" style={{ fontSize: 12 }}>{tool.install_count}</Text>
              </Space>
            </Tooltip>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>v{tool.version}</Text>
        </div>
      </Card>
    </Badge.Ribbon>
  );
}
