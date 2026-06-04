import React from 'react';
import { Handle, Position, NodeProps, type Node } from '@xyflow/react';
import { DeleteOutlined, CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useWorkflowStore } from '@/store/workflow-store';
import type { WorkflowNodeData, NodeExecutionStatus, NodeType } from '@/types';
import { getNodeTypeConfig } from './nodeTypes';

const statusIcons = {
  completed: <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />,
  running: <LoadingOutlined style={{ color: '#1890ff', fontSize: '16px' }} spin />,
  failed: <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '16px' }} />,
  pending: null,
};

export default function BaseNode({ data, selected }: NodeProps) {
  const { deleteNode, setSelectedNode, nodeExecutionStatus } = useWorkflowStore();

  if (!data || !('id' in data)) {
    return null;
  }

  const nodeData = data as WorkflowNodeData;
  const nodeType = nodeData.type as NodeType;
  const nodeConfig = getNodeTypeConfig(nodeType);
  const nodeId = nodeData.id;
  const executionStatus: NodeExecutionStatus = nodeExecutionStatus[nodeId] || {
    status: 'pending',
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteNode(nodeId);
  };

  const handleClick = () => {
    setSelectedNode(nodeId);
  };

  return (
    <div
      onClick={handleClick}
      style={{
        padding: '12px',
        borderRadius: '12px',
        background: selected ? '#e6f7ff' : '#fff',
        border: `2px solid ${selected ? '#1890ff' : nodeConfig.color}`,
        boxShadow: selected
          ? '0 0 0 2px rgba(24, 144, 255, 0.2), 0 4px 12px rgba(0,0,0,0.15)'
          : '0 2px 8px rgba(0,0,0,0.1)',
        minWidth: '160px',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
      className="workflow-node"
    >
      {/* Input Handle (Left) */}
      {nodeType !== 'llm' && (
        <Handle
          type="target"
          position={Position.Left}
          style={{
            background: nodeConfig.color,
            width: '12px',
            height: '12px',
            border: '2px solid #fff',
          }}
        />
      )}

      {/* Node Header */}
      <div style={{ marginBottom: '8px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '8px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              flex: 1,
            }}
          >
            <span style={{ fontSize: '18px' }}>{nodeConfig.icon}</span>
            <strong style={{ fontSize: '13px' }}>{nodeData.label || nodeConfig.label}</strong>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {statusIcons[executionStatus.status as keyof typeof statusIcons]}
            <DeleteOutlined
              onClick={handleDelete}
              style={{
                color: '#ff4d4f',
                fontSize: '14px',
                cursor: 'pointer',
                opacity: selected ? 1 : 0,
                transition: 'opacity 0.2s',
              }}
              className="delete-icon"
            />
          </div>
        </div>
      </div>

      {/* Node Description */}
      <div
        style={{
          fontSize: '11px',
          color: '#666',
          lineHeight: '1.4',
        }}
      >
        {nodeConfig.description}
      </div>

      {/* Output Handle (Right) */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        style={{
          background: nodeConfig.color,
          width: '12px',
          height: '12px',
          border: '2px solid #fff',
        }}
      />

      {/* Conditional handle for condition nodes */}
      {nodeType === 'condition' && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            style={{
              background: '#52c41a',
              width: '10px',
              height: '10px',
              top: '30%',
              border: '2px solid #fff',
            }}
          />
          <Handle
            type="source"
            position={Position.Right}
            id="false"
            style={{
              background: '#ff4d4f',
              width: '10px',
              height: '10px',
              top: '70%',
              border: '2px solid #fff',
            }}
          />
        </>
      )}

      {/* Loop back handle */}
      {nodeType === 'iteration' && (
        <Handle
          type="source"
          position={Position.Bottom}
          id="loop"
          style={{
            background: '#722ed1',
            width: '10px',
            height: '10px',
            border: '2px solid #fff',
          }}
        />
      )}
    </div>
  );
}
