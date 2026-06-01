'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout, message, Modal, Spin, Input, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import dynamic from 'next/dynamic';

import { ReactFlowProvider } from '@xyflow/react';
import api from '@/lib/api';
import { useWorkflowStore } from '@/store/workflow-store';

// Lazy load components
const WorkflowCanvas = dynamic(
  () => import('@/components/workflow/WorkflowCanvas'),
  { ssr: false }
);
const NodePalette = dynamic(
  () => import('@/components/workflow/NodePalette'),
  { ssr: false }
);
const NodeConfigPanel = dynamic(
  () => import('@/components/workflow/NodeConfigPanel'),
  { ssr: false }
);
const Toolbar = dynamic(
  () => import('@/components/workflow/Toolbar'),
  { ssr: false }
);

const { Sider, Content } = Layout;

export default function WorkflowEditPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [configPanelVisible, setConfigPanelVisible] = useState(false);
  const [workflowName, setWorkflowName] = useState('');
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importJson, setImportJson] = useState('');

  const { setNodes, setEdges, setIsExecuting, nodes, edges, reset } =
    useWorkflowStore();

  // Load workflow data
  useEffect(() => {
    const loadWorkflow = async () => {
      if (workflowId && workflowId !== 'new') {
        setLoading(true);
        try {
          const data = await api.get(`/workflows/${workflowId}`);
          setWorkflowName(data.name || 'Untitled Workflow');
          if (data.nodes) setNodes(data.nodes);
          if (data.edges) setEdges(data.edges);
        } catch {
          message.error('Failed to load workflow');
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
        setWorkflowName('New Workflow');
      }
    };

    loadWorkflow();
  }, [workflowId, setNodes, setEdges]);

  // Save workflow
  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const payload = {
        name: workflowName,
        description: '',
        nodes,
        edges,
      };

      if (workflowId && workflowId !== 'new') {
        await api.put(`/workflows/${workflowId}`, payload);
      } else {
        const created = await api.post('/workflows', payload);
        if (created?.id) {
          router.replace(`/workflows/${created.id}/edit`);
        }
      }

      message.success('Workflow saved successfully');
    } catch {
      message.error('Failed to save workflow');
    } finally {
      setSaving(false);
    }
  }, [workflowName, nodes, edges, workflowId, router]);

  // Run workflow
  const handleRun = useCallback(async () => {
    if (!workflowId || workflowId === 'new') {
      message.warning('Please save the workflow first');
      return;
    }

    setRunning(true);
    setIsExecuting(true);

    try {
      await api.post(`/workflows/${workflowId}/run`, { nodes, edges });
      message.success('Workflow execution started');
    } catch {
      message.error('Failed to start workflow execution');
    } finally {
      setRunning(false);
    }
  }, [workflowId, nodes, edges, setIsExecuting]);

  // Import workflow
  const handleImport = useCallback(() => {
    setImportModalVisible(true);
  }, []);

  const handleImportConfirm = useCallback(() => {
    try {
      const data = JSON.parse(importJson);
      if (data.nodes) setNodes(data.nodes);
      if (data.edges) setEdges(data.edges);
      if (data.name) setWorkflowName(data.name);
      message.success('Workflow imported successfully');
      setImportModalVisible(false);
      setImportJson('');
    } catch {
      message.error('Invalid JSON format');
    }
  }, [importJson, setNodes, setEdges]);

  // Export workflow
  const handleExport = useCallback(() => {
    const data = {
      name: workflowName,
      nodes,
      edges,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('Workflow exported');
  }, [workflowName, nodes, edges]);

  // Open config panel when node is selected
  useEffect(() => {
    const selectedNodeId = useWorkflowStore.getState().selectedNodeId;
    setConfigPanelVisible(!!selectedNodeId);
  }, [nodes, edges]);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <Spin size="large" />
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <Layout style={{ height: '100vh' }}>
        <Content style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <div style={{ padding: '12px 24px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => router.push('/workflows')}
              >
                Back
              </Button>
              <Input
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                style={{ maxWidth: 300 }}
                placeholder="Workflow name"
              />
            </div>
          </div>

          {/* Main Canvas Area */}
          <div style={{ flex: 1, position: 'relative' }}>
            <Toolbar
              workflowId={workflowId}
              workflowName={workflowName}
              onSave={handleSave}
              onRun={handleRun}
              onImport={handleImport}
              onExport={handleExport}
            />

            <div style={{ display: 'flex', height: 'calc(100% - 100px)' }}>
              {/* Node Palette */}
              <Sider
                width={280}
                style={{
                  background: '#fff',
                  borderRight: '1px solid #f0f0f0',
                  overflow: 'auto',
                }}
              >
                <Suspense fallback={<Spin />}>
                  <NodePalette />
                </Suspense>
              </Sider>

              {/* Canvas */}
              <div style={{ flex: 1, background: '#fafafa' }}>
                <Suspense fallback={<Spin />}>
                  <WorkflowCanvas workflowId={workflowId} />
                </Suspense>
              </div>
            </div>
          </div>
        </Content>

        {/* Node Config Panel */}
        <NodeConfigPanel
          visible={configPanelVisible}
          onClose={() => setConfigPanelVisible(false)}
        />

        {/* Import Modal */}
        <Modal
          title="Import Workflow"
          open={importModalVisible}
          onOk={handleImportConfirm}
          onCancel={() => {
            setImportModalVisible(false);
            setImportJson('');
          }}
        >
          <Input.TextArea
            rows={10}
            value={importJson}
            onChange={(e) => setImportJson(e.target.value)}
            placeholder="Paste workflow JSON here..."
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        </Modal>
      </Layout>
    </ReactFlowProvider>
  );
}
