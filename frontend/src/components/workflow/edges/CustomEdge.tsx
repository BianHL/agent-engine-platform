import React, { useCallback } from 'react';
import {
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
  type Edge,
} from '@xyflow/react';
import { CloseOutlined } from '@ant-design/icons';
import type { WorkflowEdge } from '@/types';

export default function CustomEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeData = data as WorkflowEdge['data'] | undefined;

  const onEdgeClick = useCallback(() => {
    // This would be handled by React Flow's edge deletion
    const event = new CustomEvent('deleteEdge', { detail: { id } });
    window.dispatchEvent(event);
  }, [id]);

  return (
    <>
      <path
        id={id}
        style={{
          stroke: '#1890ff',
          strokeWidth: 2,
          fill: 'none',
          ...style,
        }}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          {edgeData?.label && typeof edgeData.label === 'string' ? (
            <div
              key={`label-${id}`}
              style={{
                background: 'white',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '12px',
                border: '1px solid #ddd',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              {edgeData.label}
            </div>
          ) : null}
          <button
            onClick={onEdgeClick}
            style={{
              background: '#ff4d4f',
              border: 'none',
              borderRadius: '50%',
              width: '16px',
              height: '16px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginLeft: '4px',
              color: 'white',
              fontSize: '10px',
            }}
            title="Delete edge"
          >
            <CloseOutlined style={{ fontSize: '8px' }} />
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
