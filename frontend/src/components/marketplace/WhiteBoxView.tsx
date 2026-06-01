'use client';
import React, { useEffect, useState } from 'react';
import { Spin, Empty, Descriptions, Typography, Tag, Space } from 'antd';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import api from '@/lib/api';
import { MarketplaceItem } from '@/types/marketplace';

const { Text } = Typography;

interface WhiteBoxViewProps {
  item: MarketplaceItem;
}

export default function WhiteBoxView({ item }: WhiteBoxViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadWhitebox();
  }, [item.id]);

  const loadWhitebox = async () => {
    try {
      const data = await api.getWhiteboxView(item.id);
      const rfNodes: Node[] = (data.nodes || []).map((n: any) => ({
        id: n.id,
        type: 'default',
        position: n.position || { x: 0, y: 0 },
        data: {
          label: (
            <div style={{ textAlign: 'center', minWidth: 120 }}>
              <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{n.label}</div>
              {n.config?.description && (
                <div style={{ fontSize: 11, color: '#666', maxWidth: 180 }}>
                  {n.config.description.length > 60
                    ? n.config.description.substring(0, 60) + '...'
                    : n.config.description}
                </div>
              )}
            </div>
          ),
        },
        style: {
          background: n.style?.background || '#1890ff',
          color: '#fff',
          border: '2px solid #fff',
          borderRadius: 12,
          padding: '10px 16px',
          minWidth: 150,
        },
      }));
      const rfEdges: Edge[] = (data.edges || []).map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#1890ff', strokeWidth: 2 },
      }));
      setNodes(rfNodes);
      setEdges(rfEdges);
    } catch {
      setError('无法加载编排逻辑');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (error) return <Empty description={error} />;
  if (nodes.length === 0) return <Empty description="暂无编排逻辑数据" />;

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Tag color="#1890ff">LLM推理</Tag>
          <Tag color="#52c41a">工具调用</Tag>
          <Tag color="#722ed1">知识库</Tag>
          <Tag color="#fa541c">安全检查</Tag>
        </Space>
      </div>
      <div style={{ height: 400, border: '1px solid #f0f0f0', borderRadius: 8 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
        >
          <Background />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <div style={{ marginTop: 16 }}>
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="资产类型">{item.asset_type === 'agent' ? '智能体' : item.asset_type}</Descriptions.Item>
          <Descriptions.Item label="版本">v{item.version}</Descriptions.Item>
          <Descriptions.Item label="可见范围">{item.visibility}</Descriptions.Item>
        </Descriptions>
      </div>
    </div>
  );
}
