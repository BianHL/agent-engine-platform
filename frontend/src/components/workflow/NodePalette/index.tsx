'use client';

import React, { useCallback } from 'react';
import { Card, Collapse, Typography } from 'antd';
import type { WorkflowNode } from '@/types';
import { NODE_TYPES } from '../nodes/nodeTypes';

const { Text } = Typography;

const { Panel } = Collapse;

export default function NodePalette() {
  const onDragStart = useCallback(
    (event: React.DragEvent, nodeType: WorkflowNode['type']) => {
      event.dataTransfer.setData('application/reactflow', nodeType);
      event.dataTransfer.effectAllowed = 'move';
    },
    []
  );

  const nodeCategories = [
    {
      title: 'AI & Logic',
      types: ['llm', 'condition', 'code'],
    },
    {
      title: 'Control Flow',
      types: ['parallel', 'loop'],
    },
    {
      title: 'Integrations',
      types: ['http', 'human', 'sub_workflow'],
    },
  ];

  return (
    <Card
      title="Node Palette"
      size="small"
      style={{ height: '100%', overflow: 'auto' }}
      bodyStyle={{ padding: '8px' }}
    >
      <Collapse
        defaultActiveKey={['0']}
        size="small"
        ghost
      >
        {nodeCategories.map((category, catIdx) => (
          <Panel header={category.title} key={catIdx}>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {category.types.map((type) => {
                const nodeConfig = NODE_TYPES.find((t) => t.type === type);
                if (!nodeConfig) return null;

                return (
                  <div
                    key={type}
                    draggable
                    onDragStart={(e) => onDragStart(e, nodeConfig.type)}
                    style={{
                      padding: '8px 12px',
                      background: '#fff',
                      border: '1px solid #d9d9d9',
                      borderRadius: '6px',
                      cursor: 'grab',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = nodeConfig.color;
                      e.currentTarget.style.boxShadow = `0 2px 8px ${nodeConfig.color}40`;
                      e.currentTarget.style.transform = 'translateX(4px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#d9d9d9';
                      e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <span style={{ fontSize: '16px' }}>{nodeConfig.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500, fontSize: '12px' }}>
                        {nodeConfig.label}
                      </div>
                      <Text
                        type="secondary"
                        style={{ fontSize: '10px', display: 'block' }}
                      >
                        {nodeConfig.description}
                      </Text>
                    </div>
                    <div
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: nodeConfig.color,
                      }}
                    />
                  </div>
                );
              })}
            </div>
          </Panel>
        ))}
      </Collapse>
    </Card>
  );
}
