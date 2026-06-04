'use client';

import React, { useState } from 'react';
import { Card, Button, Space, Typography, Tag, Descriptions, Collapse, Badge } from 'antd';
import {
  PlayCircleOutlined, PauseCircleOutlined, StepForwardOutlined,
  StopOutlined, BugOutlined, CheckCircleOutlined, LoadingOutlined,
  CloseCircleOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { useWorkflowStore } from '@/store/workflow-store';
import type { NodeExecutionStatus } from '@/types';

const { Text, Paragraph } = Typography;

interface WorkflowDebuggerProps {
  workflowId?: string;
  onRun?: () => Promise<void>;
  onStep?: (nodeId: string) => Promise<void>;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
}

export default function WorkflowDebugger({
  workflowId,
  onRun,
  onStep,
  onPause,
  onResume,
  onStop,
}: WorkflowDebuggerProps) {
  const nodes = useWorkflowStore((state) => state.nodes);
  const edges = useWorkflowStore((state) => state.edges);
  const nodeExecutionStatus = useWorkflowStore((state) => state.nodeExecutionStatus);
  const isExecuting = useWorkflowStore((state) => state.isExecuting);
  const [breakpoints, setBreakpoints] = useState<Set<string>>(new Set());
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const toggleBreakpoint = (nodeId: string) => {
    setBreakpoints((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId); else next.add(nodeId);
      return next;
    });
  };

  const getStatusIcon = (status: NodeExecutionStatus['status']) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'running': return <LoadingOutlined style={{ color: '#1890ff' }} spin />;
      case 'failed': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default: return <ClockCircleOutlined style={{ color: '#999' }} />;
    }
  };

  const getStatusColor = (status: NodeExecutionStatus['status']) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const executedCount = Object.values(nodeExecutionStatus).filter((s) => s.status === 'completed').length;
  const failedCount = Object.values(nodeExecutionStatus).filter((s) => s.status === 'failed').length;

  return (
    <Card
      title={<Space><BugOutlined /><span>Debugger</span>{isExecuting && <Tag color="processing">Running</Tag>}</Space>}
      size="small"
      style={{ height: '100%', overflow: 'auto' }}
      extra={
        <Space>
          {!isExecuting ? (
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={onRun} size="small" disabled={nodes.length === 0}>Run</Button>
          ) : (
            <>
              <Button icon={<PauseCircleOutlined />} onClick={onPause} size="small">Pause</Button>
              <Button icon={<StepForwardOutlined />} onClick={() => onStep?.(selectedNodeId || '')} size="small">Step</Button>
              <Button icon={<StopOutlined />} onClick={onStop} size="small" danger>Stop</Button>
            </>
          )}
        </Space>
      }
    >
      <Descriptions size="small" column={2} style={{ marginBottom: 12 }}>
        <Descriptions.Item label="Nodes">{nodes.length}</Descriptions.Item>
        <Descriptions.Item label="Edges">{edges.length}</Descriptions.Item>
        <Descriptions.Item label="Executed">{executedCount}</Descriptions.Item>
        <Descriptions.Item label="Failed"><Text type={failedCount > 0 ? 'danger' : undefined}>{failedCount}</Text></Descriptions.Item>
        <Descriptions.Item label="Breakpoints">{breakpoints.size}</Descriptions.Item>
      </Descriptions>

      <Collapse
        size="small"
        ghost
        items={[{
          key: 'nodes',
          label: <Text strong>Node Execution Status</Text>,
          children: (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {nodes.map((node) => {
                const status = nodeExecutionStatus[node.id] || { status: 'pending' };
                const hasBreakpoint = breakpoints.has(node.id);
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 8px',
                      borderRadius: '4px', background: selectedNodeId === node.id ? '#e6f7ff' : '#fafafa',
                      cursor: 'pointer', borderLeft: hasBreakpoint ? '3px solid #ff4d4f' : '3px solid transparent',
                    }}
                  >
                    <Badge dot={hasBreakpoint} color="red" offset={[-2, 2]}>
                      {getStatusIcon(status.status)}
                    </Badge>
                    <Text style={{ flex: 1, fontSize: '12px' }}>{node.label}</Text>
                    <Tag color={getStatusColor(status.status)} style={{ margin: 0 }}>{status.status}</Tag>
                    <Button type="text" size="small" onClick={(e) => { e.stopPropagation(); toggleBreakpoint(node.id); }} style={{ padding: '0 4px', color: hasBreakpoint ? '#ff4d4f' : '#999' }}>●</Button>
                  </div>
                );
              })}
            </div>
          ),
        }]}
      />

      {selectedNodeId && nodeExecutionStatus[selectedNodeId] && (
        <Card size="small" style={{ marginTop: 12 }} title="Node Details">
          <Descriptions size="small" column={1}>
            <Descriptions.Item label="Node">{nodes.find((n) => n.id === selectedNodeId)?.label}</Descriptions.Item>
            <Descriptions.Item label="Status"><Tag color={getStatusColor(nodeExecutionStatus[selectedNodeId].status)}>{nodeExecutionStatus[selectedNodeId].status}</Tag></Descriptions.Item>
            {nodeExecutionStatus[selectedNodeId].started_at && <Descriptions.Item label="Started">{nodeExecutionStatus[selectedNodeId].started_at}</Descriptions.Item>}
            {nodeExecutionStatus[selectedNodeId].completed_at && <Descriptions.Item label="Completed">{nodeExecutionStatus[selectedNodeId].completed_at}</Descriptions.Item>}
            {nodeExecutionStatus[selectedNodeId].error ? <Descriptions.Item label="Error"><Text type="danger">{String(nodeExecutionStatus[selectedNodeId].error)}</Text></Descriptions.Item> : null}
          </Descriptions>
          {nodeExecutionStatus[selectedNodeId].result ? (
            <div style={{ marginTop: 8 }}>
              <Text strong style={{ fontSize: '12px' }}>Output:</Text>
              <Paragraph code style={{ fontSize: '11px', maxHeight: 150, overflow: 'auto', marginTop: 4 }}>
                {JSON.stringify(nodeExecutionStatus[selectedNodeId].result, null, 2)}
              </Paragraph>
            </div>
          ) : null}
        </Card>
      )}
    </Card>
  );
}
