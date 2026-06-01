'use client';

import React from 'react';
import {
  Space,
  Button,
  Card,
  Typography,
  Tag,
  Divider,
  Tooltip,
  Badge,
} from 'antd';
import {
  SaveOutlined,
  PlayCircleOutlined,
  UndoOutlined,
  RedoOutlined,
  ClearOutlined,
  DownloadOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useWorkflowStore } from '@/store/workflow-store';

const { Text } = Typography;

interface ToolbarProps {
  workflowId?: string;
  workflowName?: string;
  onSave?: () => Promise<void>;
  onRun?: () => Promise<void>;
  onImport?: () => void;
  onExport?: () => void;
  readOnly?: boolean;
}

export default function Toolbar({
  workflowId,
  workflowName = 'Untitled Workflow',
  onSave,
  onRun,
  onImport,
  onExport,
  readOnly = false,
}: ToolbarProps) {
  const nodes = useWorkflowStore((state) => state.nodes);
  const edges = useWorkflowStore((state) => state.edges);
  const isExecuting = useWorkflowStore((state) => state.isExecuting);

  // Simple undo/redo implementation
  const handleUndo = () => {
    // Store has undo capability via zundo
    const store = useWorkflowStore.getState() as any;
    if (store.undo) {
      store.undo();
    }
  };

  const handleRedo = () => {
    // Store has redo capability via zundo
    const store = useWorkflowStore.getState() as any;
    if (store.redo) {
      store.redo();
    }
  };

  const handleClear = () => {
    // Confirm and clear
    if (window.confirm('Are you sure you want to clear all nodes and edges?')) {
      useWorkflowStore.getState().reset();
    }
  };

  // Check if undo/redo is available
  const store = useWorkflowStore.getState() as any;
  const canUndo = store.undo?.state?.past?.length > 0;
  const canRedo = store.undo?.state?.future?.length > 0;

  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        {/* Left: Title and Stats */}
        <Space>
          <strong>{workflowName}</strong>
          <Tag color="blue">{nodes.length} nodes</Tag>
          <Tag color="green">{edges.length} edges</Tag>
          {workflowId && <Tag color="purple">ID: {workflowId.slice(0, 8)}</Tag>}
        </Space>

        {/* Middle: Edit Controls */}
        {!readOnly && (
          <Space>
            <Tooltip title="Undo (Ctrl+Z)">
              <Button
                icon={<UndoOutlined />}
                disabled={!canUndo}
                onClick={handleUndo}
              >
                Undo
              </Button>
            </Tooltip>

            <Tooltip title="Redo (Ctrl+Y)">
              <Button
                icon={<RedoOutlined />}
                disabled={!canRedo}
                onClick={handleRedo}
              >
                Redo
              </Button>
            </Tooltip>

            <Divider type="vertical" />

            <Tooltip title="Clear canvas">
              <Button
                icon={<ClearOutlined />}
                onClick={handleClear}
                danger
              >
                Clear
              </Button>
            </Tooltip>

            <Divider type="vertical" />

            <Tooltip title="Import workflow">
              <Button icon={<UploadOutlined />} onClick={onImport}>
                Import
              </Button>
            </Tooltip>

            <Tooltip title="Export workflow">
              <Button icon={<DownloadOutlined />} onClick={onExport}>
                Export
              </Button>
            </Tooltip>
          </Space>
        )}

        {/* Right: Save & Run */}
        {!readOnly && (
          <Space>
            <Badge dot={nodes.length > 0}>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={onSave}
                disabled={nodes.length === 0}
              >
                Save
              </Button>
            </Badge>

            <Badge dot={edges.length > 0}>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={onRun}
                loading={isExecuting}
                disabled={nodes.length === 0 || edges.length === 0}
                style={{ background: '#52c41a' }}
              >
                Run
              </Button>
            </Badge>
          </Space>
        )}
      </div>
    </Card>
  );
}
