'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Typography, Tag, Tabs, message, Button, Space, Modal, Form,
  Input, Select, Popconfirm, Descriptions, Spin, Empty,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, PlayCircleOutlined, ThunderboltOutlined,
  ApiOutlined, CodeOutlined, SearchOutlined, CalculatorOutlined,
  FileOutlined, DatabaseOutlined, ToolOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const TOOL_ICONS: Record<string, React.ReactNode> = {
  web_search: <SearchOutlined />,
  calculator: <CalculatorOutlined />,
  code_executor: <CodeOutlined />,
  http_request: <ApiOutlined />,
  db_query: <DatabaseOutlined />,
  file_ops: <FileOutlined />,
};

export default function ToolsPage() {
  const [builtinTools, setBuiltinTools] = useState<any[]>([]);
  const [customTools, setCustomTools] = useState<any[]>([]);
  const [allTools, setAllTools] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Type filter
  const [typeFilter, setTypeFilter] = useState<string | undefined>();

  // Create modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  // Test modal
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [testTool, setTestTool] = useState<any>(null);
  const [testParams, setTestParams] = useState('{}');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const fetchData = useCallback(() => {
    setLoading(true);
    Promise.all([api.listBuiltinTools(), api.listTools(typeFilter), api.getToolExecutions()])
      .then(([builtin, all, execs]) => {
        setBuiltinTools(builtin);
        setAllTools(all);
        setCustomTools(all.filter((t: any) => t.tool_type === 'custom' || t.source === 'database'));
        setExecutions(execs);
      })
      .catch(() => message.error('Failed to load tools'))
      .finally(() => setLoading(false));
  }, [typeFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);
      // Parse OpenAPI schema if provided
      if (values.api_schema && typeof values.api_schema === 'string') {
        values.api_schema = JSON.parse(values.api_schema);
      }
      await api.createTool(values);
      message.success('Tool created');
      setCreateModalOpen(false);
      form.resetFields();
      fetchData();
    } catch (e: any) {
      if (e instanceof SyntaxError) {
        message.error('Invalid JSON in API schema');
      } else {
        message.error('Failed to create tool');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteTool(id);
      message.success('Tool deleted');
      fetchData();
    } catch {
      message.error('Failed to delete tool');
    }
  };

  const handleTest = async () => {
    if (!testTool) return;
    setTesting(true);
    setTestResult(null);
    try {
      const params = JSON.parse(testParams);
      const result = await api.executeTool(testTool.name, params);
      setTestResult(result);
    } catch (e: any) {
      setTestResult({ error: e.message });
    } finally {
      setTesting(false);
    }
  };

  const builtinColumns = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      render: (name: string) => (
        <Space>
          {TOOL_ICONS[name] || <ThunderboltOutlined />}
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: 'Type', key: 'type',
      render: () => <Tag color="blue">builtin</Tag>,
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, record: any) => (
        <Button
          size="small"
          icon={<PlayCircleOutlined />}
          onClick={() => {
            setTestTool(record);
            setTestParams(JSON.stringify(
              Object.fromEntries(
                Object.entries(record.input_schema?.properties || {}).map(([k, v]: any) => [k, v.default || ''])
              ),
              null, 2
            ));
            setTestResult(null);
            setTestModalOpen(true);
          }}
        >
          Test
        </Button>
      ),
    },
  ];

  const customColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: 'Type', key: 'type',
      render: (_: any, record: any) => {
        const t = record.tool_type || 'custom';
        const color = t === 'mcp' ? 'purple' : 'green';
        return <Tag color={color}>{t}</Tag>;
      },
    },
    {
      title: 'Enabled', dataIndex: 'enabled', key: 'enabled',
      render: (v: boolean) => v ? <Tag color="success">Yes</Tag> : <Tag>No</Tag>,
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => {
              setTestTool(record);
              setTestParams('{}');
              setTestResult(null);
              setTestModalOpen(true);
            }}
          >
            Test
          </Button>
          <Popconfirm title="Delete this tool?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const executionColumns = [
    { title: 'Tool', dataIndex: 'tool_name', key: 'tool_name' },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'success' ? 'success' : s === 'failed' ? 'error' : 'processing'}>{s}</Tag>,
    },
    {
      title: 'Duration', dataIndex: 'duration_ms', key: 'duration_ms',
      render: (v: number) => v ? `${v}ms` : '-',
    },
    {
      title: 'Created', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Tools</Title>
        <Space>
          <Select
            placeholder="Filter by type"
            allowClear
            style={{ width: 140 }}
            value={typeFilter}
            onChange={(v) => setTypeFilter(v)}
            options={[
              { value: 'builtin', label: 'Built-in' },
              { value: 'custom', label: 'Custom' },
              { value: 'mcp', label: 'MCP' },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            Create Custom Tool
          </Button>
        </Space>
      </div>

      <Card>
        <Tabs
          items={[
            {
              key: 'builtin',
              label: `Built-in (${builtinTools.length})`,
              children: (
                <Table
                  columns={builtinColumns}
                  dataSource={builtinTools}
                  rowKey="name"
                  loading={loading}
                  pagination={false}
                />
              ),
            },
            {
              key: 'custom',
              label: `Custom (${customTools.length})`,
              children: (
                <Table
                  columns={customColumns}
                  dataSource={customTools}
                  rowKey="id"
                  loading={loading}
                  pagination={false}
                  locale={{
                    emptyText: (
                      <Empty
                        image={<ToolOutlined style={{ fontSize: 48, color: '#bbb' }} />}
                        description="No custom tools yet"
                      >
                        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
                          Create one
                        </Button>
                      </Empty>
                    ),
                  }}
                />
              ),
            },
            {
              key: 'history',
              label: `Execution History (${executions.length})`,
              children: (
                <Table
                  columns={executionColumns}
                  dataSource={executions}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 20 }}
                />
              ),
            },
          ]}
        />
      </Card>

      {/* Create Custom Tool Modal */}
      <Modal
        title="Create Custom Tool"
        open={createModalOpen}
        onOk={handleCreate}
        onCancel={() => setCreateModalOpen(false)}
        confirmLoading={creating}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Tool Name" rules={[{ required: true }]}>
            <Input placeholder="my_api_tool" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input placeholder="What this tool does" />
          </Form.Item>
          <Form.Item name="tool_type" label="Type" initialValue="custom">
            <Select options={[
              { value: 'custom', label: 'Custom API' },
              { value: 'mcp', label: 'MCP Server' },
            ]} />
          </Form.Item>
          <Form.Item
            name="api_schema"
            label="OpenAPI Schema (JSON)"
            help="Paste an OpenAPI 3.0 spec to auto-generate tool definitions"
          >
            <TextArea rows={8} placeholder='{"openapi":"3.0.0","info":{"title":"My API"},"paths":{...}}' />
          </Form.Item>
        </Form>
      </Modal>

      {/* Test Tool Modal */}
      <Modal
        title={`Test Tool: ${testTool?.name || ''}`}
        open={testModalOpen}
        onCancel={() => setTestModalOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setTestModalOpen(false)}>Close</Button>,
          <Button key="run" type="primary" loading={testing} onClick={handleTest} icon={<PlayCircleOutlined />}>
            Run
          </Button>,
        ]}
        width={700}
      >
        {testTool && (
          <>
            <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Description">{testTool.description}</Descriptions.Item>
            </Descriptions>
            <div style={{ marginBottom: 12 }}>
              <Text strong>Parameters (JSON):</Text>
              <TextArea
                rows={6}
                value={testParams}
                onChange={(e) => setTestParams(e.target.value)}
                style={{ fontFamily: 'monospace', marginTop: 4 }}
              />
            </div>
            {testResult && (
              <div>
                <Text strong>Result:</Text>
                <pre style={{
                  background: testResult.error ? '#fff1f0' : '#f5f5f5',
                  padding: 12,
                  borderRadius: 6,
                  maxHeight: 300,
                  overflow: 'auto',
                  marginTop: 4,
                  fontSize: 12,
                }}>
                  {JSON.stringify(testResult, null, 2)}
                </pre>
              </div>
            )}
          </>
        )}
      </Modal>
    </div>
  );
}
