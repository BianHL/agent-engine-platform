'use client';
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, Button, Space, Select, Drawer, Form, Input, InputNumber, message, Tag, Tooltip, Spin } from 'antd';
import {
  SaveOutlined, PlayCircleOutlined, DeleteOutlined,
  PlusOutlined, SettingOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
  config: Record<string, any>;
}

interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

const NODE_TYPES = [
  { value: 'llm', label: 'LLM', color: '#1890ff' },
  { value: 'condition', label: 'Condition', color: '#faad14' },
  { value: 'parallel', label: 'Parallel', color: '#52c41a' },
  { value: 'loop', label: 'Loop', color: '#722ed1' },
  { value: 'http', label: 'HTTP', color: '#13c2c2' },
  { value: 'code', label: 'Code', color: '#eb2f96' },
  { value: 'human', label: 'Human Review', color: '#fa541c' },
  { value: 'sub_workflow', label: 'Sub Workflow', color: '#2f54eb' },
];

export default function WorkflowEditorPage({ params }: { params: { id: string } }) {
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [edges, setEdges] = useState<WorkflowEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [dragging, setDragging] = useState<string | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [workflowName, setWorkflowName] = useState('');
  const canvasRef = useRef<HTMLDivElement>(null);
  const [form] = Form.useForm();

  // Fetch workflow data on mount
  useEffect(() => {
    if (params.id && params.id !== 'new') {
      api.get(`/workflows/${params.id}`)
        .then((data: any) => {
          setWorkflowName(data.name || '');
          if (data.nodes) setNodes(data.nodes);
          if (data.edges) setEdges(data.edges);
        })
        .catch(() => message.error('Failed to load workflow'))
        .finally(() => setPageLoading(false));
    } else {
      setPageLoading(false);
    }
  }, [params.id]);

  const addNode = useCallback((type: string) => {
    const id = `node_${Date.now()}`;
    const nodeType = NODE_TYPES.find(t => t.value === type);
    const newNode: WorkflowNode = {
      id,
      type,
      label: nodeType?.label || type,
      x: 100 + nodes.length * 180,
      y: 200,
      config: {},
    };
    setNodes(prev => [...prev, newNode]);
  }, [nodes.length]);

  const deleteNode = useCallback((id: string) => {
    setNodes(prev => prev.filter(n => n.id !== id));
    setEdges(prev => prev.filter(e => e.source !== id && e.target !== id));
    if (selectedNode?.id === id) {
      setSelectedNode(null);
      setDrawerOpen(false);
    }
  }, [selectedNode]);

  const handleNodeClick = useCallback((node: WorkflowNode) => {
    setSelectedNode(node);
    form.setFieldsValue({ label: node.label, ...node.config });
    setDrawerOpen(true);
  }, [form]);

  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current) {
      setSelectedNode(null);
      setDrawerOpen(false);
    }
  }, []);

  const handleDragStart = useCallback((id: string) => {
    setDragging(id);
  }, []);

  const handleDragEnd = useCallback((e: React.MouseEvent) => {
    if (!dragging || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setNodes(prev => prev.map(n => n.id === dragging ? { ...n, x, y } : n));
    setDragging(null);
  }, [dragging]);

  const handleSaveNodeConfig = useCallback(() => {
    if (!selectedNode) return;
    const values = form.getFieldsValue();
    const { label, ...config } = values;
    setNodes(prev => prev.map(n =>
      n.id === selectedNode.id ? { ...n, label: label || n.label, config } : n
    ));
    message.success('Node updated');
    setDrawerOpen(false);
  }, [selectedNode, form]);

  const handleConnect = useCallback((sourceId: string, targetId: string) => {
    if (sourceId === targetId) return;
    const exists = edges.some(e => e.source === sourceId && e.target === targetId);
    if (exists) return;
    setEdges(prev => [...prev, { id: `edge_${Date.now()}`, source: sourceId, target: targetId }]);
  }, [edges]);

  const getNodeTypeColor = (type: string) =>
    NODE_TYPES.find(t => t.value === type)?.color || '#666';

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const payload = {
        name: workflowName || 'Untitled Workflow',
        nodes,
        edges,
      };
      if (params.id && params.id !== 'new') {
        await api.put(`/workflows/${params.id}`, payload);
      } else {
        await api.post('/workflows', payload);
      }
      message.success('Workflow saved');
    } catch {
      message.error('Failed to save workflow');
    } finally {
      setSaving(false);
    }
  }, [params.id, workflowName, nodes, edges]);

  const handleRun = useCallback(async () => {
    setRunning(true);
    try {
      await api.post(`/workflows/${params.id}/run`, { nodes, edges });
      message.success('Workflow execution started');
    } catch {
      message.error('Failed to run workflow');
    } finally {
      setRunning(false);
    }
  }, [params.id, nodes, edges]);

  if (pageLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  return (
    <div style={{ padding: 24, height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <strong>Workflow Editor</strong>
          <Select
            placeholder="Add node"
            style={{ width: 160 }}
            options={NODE_TYPES}
            onChange={addNode}
            value={null}
          />
          <Button icon={<SaveOutlined />} type="primary" loading={saving} onClick={handleSave}>Save</Button>
          <Button icon={<PlayCircleOutlined />} loading={running} onClick={handleRun}>Run</Button>
          <Tag>{nodes.length} nodes, {edges.length} edges</Tag>
        </Space>
      </Card>

      <div style={{ flex: 1, display: 'flex', gap: 16 }}>
        {/* Canvas */}
        <div
          ref={canvasRef}
          onClick={handleCanvasClick}
          onMouseUp={handleDragEnd}
          style={{
            flex: 1,
            background: '#fafafa',
            border: '1px solid #d9d9d9',
            borderRadius: 8,
            position: 'relative',
            overflow: 'auto',
            minHeight: 500,
          }}
        >
          {/* Grid background */}
          <svg style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none' }}>
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f0f0f0" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>

          {/* Edges */}
          <svg style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none' }}>
            {edges.map(edge => {
              const sourceNode = nodes.find(n => n.id === edge.source);
              const targetNode = nodes.find(n => n.id === edge.target);
              if (!sourceNode || !targetNode) return null;
              return (
                <line
                  key={edge.id}
                  x1={sourceNode.x + 75}
                  y1={sourceNode.y + 20}
                  x2={targetNode.x + 75}
                  y2={targetNode.y + 20}
                  stroke="#1890ff"
                  strokeWidth={2}
                  markerEnd="url(#arrowhead)"
                />
              );
            })}
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#1890ff" />
              </marker>
            </defs>
          </svg>

          {/* Nodes */}
          {nodes.map(node => (
            <div
              key={node.id}
              draggable
              onMouseDown={() => handleDragStart(node.id)}
              onClick={(e) => { e.stopPropagation(); handleNodeClick(node); }}
              style={{
                position: 'absolute',
                left: node.x,
                top: node.y,
                width: 150,
                padding: '8px 12px',
                background: '#fff',
                border: `2px solid ${selectedNode?.id === node.id ? '#1890ff' : getNodeTypeColor(node.type)}`,
                borderRadius: 8,
                cursor: 'grab',
                boxShadow: selectedNode?.id === node.id ? '0 0 8px rgba(24,144,255,0.3)' : '0 1px 3px rgba(0,0,0,0.1)',
                userSelect: 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Tag color={getNodeTypeColor(node.type)} style={{ margin: 0 }}>{node.type}</Tag>
                <DeleteOutlined
                  style={{ color: '#ff4d4f', fontSize: 12 }}
                  onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }}
                />
              </div>
              <div style={{ marginTop: 4, fontSize: 13, fontWeight: 500 }}>{node.label}</div>
            </div>
          ))}

          {nodes.length === 0 && (
            <div style={{
              position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
              color: '#999', textAlign: 'center',
            }}>
              <PlusOutlined style={{ fontSize: 32, marginBottom: 8 }} />
              <div>Add nodes using the dropdown above</div>
            </div>
          )}
        </div>

        {/* Node config panel */}
        <Drawer
          title={selectedNode ? `Configure: ${selectedNode.label}` : 'Node Config'}
          placement="right"
          width={360}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          extra={
            <Button type="primary" onClick={handleSaveNodeConfig}>Save</Button>
          }
        >
          {selectedNode && (
            <Form form={form} layout="vertical">
              <Form.Item name="label" label="Label">
                <Input />
              </Form.Item>

              {selectedNode.type === 'llm' && (
                <>
                  <Form.Item name="model" label="Model">
                    <Input placeholder="gpt-4o" />
                  </Form.Item>
                  <Form.Item name="prompt" label="Prompt">
                    <Input.TextArea rows={4} placeholder="Enter prompt template. Use {variable} for substitution." />
                  </Form.Item>
                  <Form.Item name="temperature" label="Temperature">
                    <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item name="max_tokens" label="Max Tokens">
                    <InputNumber min={1} max={8000} style={{ width: '100%' }} />
                  </Form.Item>
                </>
              )}

              {selectedNode.type === 'condition' && (
                <Form.Item name="expression" label="Expression">
                  <Input.TextArea rows={3} placeholder='e.g. score > 0.8' />
                </Form.Item>
              )}

              {selectedNode.type === 'http' && (
                <>
                  <Form.Item name="url" label="URL">
                    <Input placeholder="https://api.example.com" />
                  </Form.Item>
                  <Form.Item name="method" label="Method">
                    <Select options={[
                      { value: 'GET', label: 'GET' },
                      { value: 'POST', label: 'POST' },
                      { value: 'PUT', label: 'PUT' },
                      { value: 'DELETE', label: 'DELETE' },
                    ]} />
                  </Form.Item>
                </>
              )}

              {selectedNode.type === 'loop' && (
                <>
                  <Form.Item name="max_iterations" label="Max Iterations">
                    <InputNumber min={1} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item name="exit_condition" label="Exit Condition">
                    <Input placeholder='e.g. done == True' />
                  </Form.Item>
                </>
              )}

              {selectedNode.type === 'code' && (
                <Form.Item name="code" label="Code">
                  <Input.TextArea rows={6} placeholder="# Set result = ..." style={{ fontFamily: 'monospace' }} />
                </Form.Item>
              )}

              <Form.Item label="Retry Count" name="retry_count">
                <InputNumber min={0} max={5} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item label="Timeout (seconds)" name="timeout">
                <InputNumber min={1} max={3600} style={{ width: '100%' }} />
              </Form.Item>

              {/* Edge connections */}
              <Card size="small" title="Connections" style={{ marginTop: 16 }}>
                <div style={{ marginBottom: 8 }}>
                  <Select
                    placeholder="Connect to node..."
                    style={{ width: '100%' }}
                    options={nodes.filter(n => n.id !== selectedNode.id).map(n => ({
                      value: n.id,
                      label: `${n.label} (${n.type})`,
                    }))}
                    onChange={(targetId: string) => targetId && handleConnect(selectedNode.id, targetId)}
                    value={null}
                  />
                </div>
                {edges.filter(e => e.source === selectedNode.id).map(e => {
                  const target = nodes.find(n => n.id === e.target);
                  return (
                    <Tag key={e.id} closable onClose={() => setEdges(prev => prev.filter(edge => edge.id !== e.id))}>
                      → {target?.label || e.target}
                    </Tag>
                  );
                })}
              </Card>
            </Form>
          )}
        </Drawer>
      </div>
    </div>
  );
}
