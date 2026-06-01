'use client';

import React, { useCallback, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  type Connection,
  type Edge,
  type Node,
  type ReactFlowInstance,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { nodeTypes } from '../nodes';
import { edgeTypes } from '../edges';
import { useWorkflowStore } from '@/store/workflow-store';
import type { WorkflowNode, WorkflowEdge } from '@/types';
import { createDefaultNode } from '../nodes/nodeTypes';

// Convert store nodes to React Flow nodes
const convertToReactFlowNodes = (nodes: WorkflowNode[]): Node[] => {
  return nodes.map((node) => ({
    id: node.id,
    type: node.type,
    position: node.position,
    data: {
      id: node.id,
      type: node.type,
      label: node.label,
      config: node.config,
    },
    style: node.style,
  }));
};

// Convert React Flow nodes back to store nodes
const convertFromReactFlowNodes = (nodes: Node[]): WorkflowNode[] => {
  return nodes.map((node) => {
    const data = node.data as any;
    return {
      id: node.id,
      type: data.type,
      label: data.label,
      config: data.config || {},
      position: node.position,
      style: node.style,
    };
  });
};

// Convert store edges to React Flow edges
const convertToReactFlowEdges = (edges: WorkflowEdge[]): Edge[] => {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle || undefined,
    targetHandle: edge.targetHandle || undefined,
    label: edge.label,
    style: edge.style,
    animated: edge.animated,
    data: edge.data,
    type: 'custom',
  }));
};

// Convert React Flow edges back to store edges
const convertFromReactFlowEdges = (edges: Edge[]): WorkflowEdge[] => {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle || undefined,
    targetHandle: edge.targetHandle || undefined,
    label: edge.label,
    style: edge.style,
    animated: edge.animated,
    data: edge.data,
  }));
};

interface WorkflowCanvasProps {
  workflowId?: string;
  onConnect?: (connection: Connection) => void;
  readOnly?: boolean;
}

export default function WorkflowCanvas({
  workflowId,
  onConnect,
  readOnly = false,
}: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] =
    React.useState<ReactFlowInstance | null>(null);

  // Get state from store
  const storeNodes = useWorkflowStore((state) => state.nodes);
  const storeEdges = useWorkflowStore((state) => state.edges);
  const setStoreNodes = useWorkflowStore((state) => state.setNodes);
  const setStoreEdges = useWorkflowStore((state) => state.setEdges);
  const addNode = useWorkflowStore((state) => state.addNode);
  const updateNode = useWorkflowStore((state) => state.updateNode);
  const addStoreEdge = useWorkflowStore((state) => state.addEdge);
  const setSelectedNode = useWorkflowStore((state) => state.setSelectedNode);

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState(
    convertToReactFlowNodes(storeNodes)
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    convertToReactFlowEdges(storeEdges)
  );

  // Sync store changes to React Flow
  useEffect(() => {
    setNodes(convertToReactFlowNodes(storeNodes));
  }, [storeNodes, setNodes]);

  useEffect(() => {
    setEdges(convertToReactFlowEdges(storeEdges));
  }, [storeEdges, setEdges]);

  // Sync React Flow changes to store
  useEffect(() => {
    if (nodes.length > 0) {
      setStoreNodes(convertFromReactFlowNodes(nodes));
    }
  }, [nodes, setStoreNodes]);

  useEffect(() => {
    if (edges.length > 0) {
      setStoreEdges(convertFromReactFlowEdges(edges));
    }
  }, [edges, setStoreEdges]);

  // Handle new connections
  const onConnectHandler = useCallback(
    (connection: Connection) => {
      const newEdge: WorkflowEdge = {
        id: `edge_${Date.now()}`,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle || undefined,
        targetHandle: connection.targetHandle || undefined,
        animated: true,
      };

      addStoreEdge(newEdge);
      onConnect?.(connection);
    },
    [addStoreEdge, onConnect]
  );

  // Handle drag over
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop from palette
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const nodeType = event.dataTransfer.getData('application/reactflow');
      if (!nodeType || !reactFlowWrapper.current || !reactFlowInstance) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = createDefaultNode(
        nodeType as WorkflowNode['type'],
        position
      );
      addNode(newNode);
    },
    [reactFlowInstance, addNode]
  );

  // Handle node selection
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id);
    },
    [setSelectedNode]
  );

  // Handle background click to deselect
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  // Handle node position changes
  const onNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      updateNode(node.id, { position: node.position });
    },
    [updateNode]
  );

  // MiniMap node color
  const minimapNodeColor = useCallback((node: Node) => {
    const colors: Record<string, string> = {
      llm: '#1890ff',
      code: '#eb2f96',
      condition: '#faad14',
      parallel: '#52c41a',
      loop: '#722ed1',
      http: '#13c2c2',
      human: '#fa541c',
      sub_workflow: '#2f54eb',
    };
    return colors[node.type || ''] || '#666';
  }, []);

  return (
    <div ref={reactFlowWrapper} style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onConnect={readOnly ? undefined : onConnectHandler}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onNodeDragStop={onNodeDragStop}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onInit={setReactFlowInstance}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        minZoom={0.3}
        maxZoom={2}
        attributionPosition="bottom-left"
        deleteKeyCode={readOnly ? undefined : 'Delete'}
      >
        <Background
          color="#e0e0e0"
          gap={20}
          style={{ opacity: 0.5 }}
        />
        <Controls />
        <MiniMap
          nodeColor={minimapNodeColor}
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
      </ReactFlow>
    </div>
  );
}
