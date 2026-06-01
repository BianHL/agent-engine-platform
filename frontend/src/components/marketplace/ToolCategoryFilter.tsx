'use client';
import React from 'react';
import { Space, Tag, Typography, Badge } from 'antd';
import {
  RobotOutlined, DatabaseOutlined, ApiOutlined, ThunderboltOutlined,
  MessageOutlined, CloudOutlined, BarChartOutlined, SafetyOutlined,
  ToolOutlined, AppstoreOutlined,
} from '@ant-design/icons';
import { TOOL_CATEGORIES, type ToolCategory } from '@/types/marketplace';

const { Text } = Typography;

const CATEGORY_CONFIG: Record<ToolCategory, { icon: React.ReactNode; color: string }> = {
  AI: { icon: <RobotOutlined />, color: '#722ed1' },
  Data: { icon: <DatabaseOutlined />, color: '#1890ff' },
  Integration: { icon: <ApiOutlined />, color: '#13c2c2' },
  Automation: { icon: <ThunderboltOutlined />, color: '#fa8c16' },
  Communication: { icon: <MessageOutlined />, color: '#52c41a' },
  Storage: { icon: <CloudOutlined />, color: '#2f54eb' },
  Analytics: { icon: <BarChartOutlined />, color: '#eb2f96' },
  Security: { icon: <SafetyOutlined />, color: '#f5222d' },
  Utility: { icon: <ToolOutlined />, color: '#595959' },
};

interface ToolCategoryFilterProps {
  selected: string;
  onChange: (category: string) => void;
  counts?: Record<string, number>;
}

export default function ToolCategoryFilter({ selected, onChange, counts }: ToolCategoryFilterProps) {
  return (
    <div>
      <Space wrap size={[8, 8]}>
        <Tag
          icon={<AppstoreOutlined />}
          color={!selected ? 'blue' : undefined}
          style={{ cursor: 'pointer', padding: '4px 12px', fontSize: 13 }}
          onClick={() => onChange('')}
        >
          All
          {counts?.total != null && (
            <Badge count={counts.total} style={{ marginLeft: 6, backgroundColor: '#d9d9d9' }} overflowCount={999} />
          )}
        </Tag>
        {TOOL_CATEGORIES.map((cat) => {
          const config = CATEGORY_CONFIG[cat];
          const isActive = selected === cat;
          return (
            <Tag
              key={cat}
              icon={config.icon}
              color={isActive ? config.color : undefined}
              style={{
                cursor: 'pointer',
                padding: '4px 12px',
                fontSize: 13,
                borderColor: isActive ? config.color : undefined,
              }}
              onClick={() => onChange(isActive ? '' : cat)}
            >
              {cat}
              {counts?.[cat] != null && (
                <Badge
                  count={counts[cat]}
                  style={{ marginLeft: 6, backgroundColor: isActive ? '#fff' : '#d9d9d9' }}
                  overflowCount={999}
                />
              )}
            </Tag>
          );
        })}
      </Space>
    </div>
  );
}
