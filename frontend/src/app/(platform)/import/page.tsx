'use client';

import React, { useState, useEffect } from 'react';
import {
  Card, Steps, Button, Select, Upload, Table, Progress, Tag, Space,
  Typography, Form, Input, message, Modal, Tabs, List, Avatar, Badge
} from 'antd';
import {
  ImportOutlined, CloudUploadOutlined, CheckCircleOutlined,
  LoadingOutlined, ExclamationCircleOutlined, RocketOutlined,
  FileTextOutlined, RobotOutlined, ToolOutlined, BranchesOutlined
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

interface Platform {
  name: string;
  display_name: string;
  description: string;
  asset_types: string[];
  config_fields: string[];
}

interface ImportTask {
  id: string;
  platform: string;
  asset_type: string;
  status: string;
  progress: number;
  total: number;
  processed: number;
  failed: number;
}

export default function ImportPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');
  const [selectedAssetType, setSelectedAssetType] = useState<string>('');
  const [config, setConfig] = useState<Record<string, string>>({});
  const [assets, setAssets] = useState<any[]>([]);
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [tasks, setTasks] = useState<ImportTask[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPlatforms();
    loadTasks();
  }, []);

  const loadPlatforms = async () => {
    try {
      const response = await api.get('/import/platforms');
      setPlatforms(response.data.platforms);
    } catch (error) {
      message.error('加载平台列表失败');
    }
  };

  const loadTasks = async () => {
    try {
      const response = await api.get('/import/tasks');
      setTasks(response.data.tasks);
    } catch (error) {
      console.error('加载任务列表失败');
    }
  };

  const validateConfig = async () => {
    try {
      setLoading(true);
      const response = await api.post('/import/validate', { platform: selectedPlatform, ...config });
      if (response.data.valid) {
        message.success('配置验证通过');
      } else {
        message.error('配置验证失败');
      }
    } catch (error) {
      message.error('配置验证失败');
    } finally {
      setLoading(false);
    }
  };

  const loadAssets = async () => {
    try {
      setLoading(true);
      const response = await api.post('/import/assets', {
        platform: selectedPlatform,
        asset_type: selectedAssetType,
        config: { platform: selectedPlatform, ...config }
      });
      setAssets(response.data.assets);
      message.success(`找到 ${response.data.total} 个可导入的资产`);
    } catch (error) {
      message.error('加载资产列表失败');
    } finally {
      setLoading(false);
    }
  };

  const executeImport = async () => {
    try {
      setLoading(true);
      const selectedAssetData = assets.filter(a => selectedAssets.includes(a.id));
      const response = await api.post('/import/execute', {
        platform: selectedPlatform,
        asset_type: selectedAssetType,
        assets: selectedAssetData,
        config: { platform: selectedPlatform, ...config }
      });
      message.success(`导入完成: ${response.data.processed} 成功, ${response.data.failed} 失败`);
      loadTasks();
      setCurrentStep(3);
    } catch (error) {
      message.error('导入失败');
    } finally {
      setLoading(false);
    }
  };

  const getPlatformIcon = (name: string) => {
    switch (name) {
      case 'dify': return '🤖';
      case 'coze': return '🎯';
      default: return '📦';
    }
  };

  const getAssetTypeIcon = (type: string) => {
    switch (type) {
      case 'agent': return <RobotOutlined />;
      case 'knowledge': return <FileTextOutlined />;
      case 'tool': return <ToolOutlined />;
      case 'workflow': return <BranchesOutlined />;
      default: return <ImportOutlined />;
    }
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'completed': return <Tag color="success">完成</Tag>;
      case 'processing': return <Tag color="processing">处理中</Tag>;
      case 'failed': return <Tag color="error">失败</Tag>;
      default: return <Tag color="default">等待中</Tag>;
    }
  };

  const assetColumns = [
    { title: '名称', dataIndex: 'name', key: 'name', render: (text: string) => <Text strong>{text}</Text> },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '类型', dataIndex: 'type', key: 'type', render: (type: string) => <Tag>{type}</Tag> }
  ];

  const taskColumns = [
    {
      title: '平台', dataIndex: 'platform', key: 'platform',
      render: (platform: string) => <Space><span>{getPlatformIcon(platform)}</span><Text>{platform}</Text></Space>
    },
    {
      title: '资产类型', dataIndex: 'asset_type', key: 'asset_type',
      render: (type: string) => <Space>{getAssetTypeIcon(type)}<Text>{type}</Text></Space>
    },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => getStatusTag(status) },
    {
      title: '进度', key: 'progress',
      render: (_value: any, record: ImportTask) => (
        <Progress percent={Math.round(record.progress)} size="small" status={record.status === 'failed' ? 'exception' : 'active'} />
      )
    },
    {
      title: '结果', key: 'result',
      render: (_value: any, record: ImportTask) => (
        <Space>
          <Text type="success">{record.processed} 成功</Text>
          {record.failed > 0 && <Text type="danger">{record.failed} 失败</Text>}
        </Space>
      )
    }
  ];

  const steps = [
    {
      title: '选择平台',
      content: (
        <div className="space-y-6">
          <Title level={4}>选择导入平台</Title>
          <Paragraph>选择要导入数据的 AI 平台</Paragraph>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {platforms.map(platform => (
              <Card
                key={platform.name}
                hoverable
                className={selectedPlatform === platform.name ? 'border-blue-500 border-2' : ''}
                onClick={() => setSelectedPlatform(platform.name)}
              >
                <div className="flex items-center space-x-4">
                  <div className="text-4xl">{getPlatformIcon(platform.name)}</div>
                  <div>
                    <Title level={5}>{platform.display_name}</Title>
                    <Text type="secondary">{platform.description}</Text>
                    <div className="mt-2">
                      {platform.asset_types.map(type => (
                        <Tag key={type} icon={getAssetTypeIcon(type)}>{type}</Tag>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )
    },
    {
      title: '配置连接',
      content: (
        <div className="space-y-6">
          <Title level={4}>配置连接信息</Title>
          <Paragraph>输入平台的 API 连接信息</Paragraph>
          <Form layout="vertical">
            {selectedPlatform === 'dify' && (
              <>
                <Form.Item label="API 地址" required>
                  <Input placeholder="https://api.dify.ai" value={config.api_url} onChange={e => setConfig({ ...config, api_url: e.target.value })} />
                </Form.Item>
                <Form.Item label="API Key" required>
                  <Input.Password placeholder="app-xxxxxxxxxx" value={config.api_key} onChange={e => setConfig({ ...config, api_key: e.target.value })} />
                </Form.Item>
              </>
            )}
            {selectedPlatform === 'coze' && (
              <Form.Item label="API Token" required>
                <Input.Password placeholder="pat_xxxxxxxxxx" value={config.api_token} onChange={e => setConfig({ ...config, api_token: e.target.value })} />
              </Form.Item>
            )}
            <Form.Item>
              <Button type="primary" onClick={validateConfig} loading={loading}>验证连接</Button>
            </Form.Item>
          </Form>
        </div>
      )
    },
    {
      title: '选择资产',
      content: (
        <div className="space-y-6">
          <Title level={4}>选择要导入的资产</Title>
          <Tabs
            items={[
              { key: 'agent', label: <span><RobotOutlined /> Agent</span>,
                children: <Button type="primary" onClick={() => { setSelectedAssetType('agent'); loadAssets(); }} loading={loading}>加载 Agent 列表</Button> },
              { key: 'knowledge', label: <span><FileTextOutlined /> 知识库</span>,
                children: <Button type="primary" onClick={() => { setSelectedAssetType('knowledge'); loadAssets(); }} loading={loading}>加载知识库列表</Button> },
              { key: 'tool', label: <span><ToolOutlined /> 工具</span>,
                children: <Button type="primary" onClick={() => { setSelectedAssetType('tool'); loadAssets(); }} loading={loading}>加载工具列表</Button> },
              { key: 'workflow', label: <span><BranchesOutlined /> 工作流</span>,
                children: <Button type="primary" onClick={() => { setSelectedAssetType('workflow'); loadAssets(); }} loading={loading}>加载工作流列表</Button> },
              { key: 'file', label: <span><CloudUploadOutlined /> 文件导入</span>,
                children: (
                  <Dragger accept=".json" customRequest={({ file }) => {}} showUploadList={false}>
                    <p className="ant-upload-drag-icon"><CloudUploadOutlined /></p>
                    <p className="ant-upload-text">点击或拖拽 JSON 文件到此区域上传</p>
                    <p className="ant-upload-hint">支持从 Dify/Coze 导出的 JSON 文件</p>
                  </Dragger>
                )
              }
            ]}
          />
          {assets.length > 0 && (
            <>
              <Table
                columns={assetColumns} dataSource={assets} rowKey="id"
                rowSelection={{ selectedRowKeys: selectedAssets, onChange: (keys) => setSelectedAssets(keys as string[]) }}
                pagination={{ pageSize: 10 }}
              />
              <div className="flex justify-end">
                <Button type="primary" size="large" onClick={executeImport} loading={loading}
                  disabled={selectedAssets.length === 0} icon={<RocketOutlined />}>
                  导入选中的 {selectedAssets.length} 个资产
                </Button>
              </div>
            </>
          )}
        </div>
      )
    },
    {
      title: '导入结果',
      content: (
        <div className="space-y-6 text-center">
          <CheckCircleOutlined className="text-6xl text-green-500 mb-4" />
          <Title level={3}>导入完成</Title>
          <Paragraph>所有选中的资产已成功导入到平台</Paragraph>
          <Button type="primary" onClick={() => setCurrentStep(0)}>继续导入</Button>
        </div>
      )
    }
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <Title level={2}><ImportOutlined className="mr-2" />竞品数据导入</Title>
        <Paragraph type="secondary">从 Dify、Coze 等平台快速导入 Agent、知识库、工具和工作流</Paragraph>
      </div>
      <Card className="mb-6">
        <Steps current={currentStep} items={steps.map(s => ({ title: s.title }))} />
      </Card>
      <Card className="mb-6">{steps[currentStep].content}</Card>
      <div className="flex justify-between">
        {currentStep > 0 && currentStep < 3 && <Button onClick={() => setCurrentStep(currentStep - 1)}>上一步</Button>}
        {currentStep < 2 && <Button type="primary" onClick={() => setCurrentStep(currentStep + 1)} disabled={currentStep === 0 && !selectedPlatform}>下一步</Button>}
      </div>
      <Card className="mt-8" title="导入历史">
        <Table columns={taskColumns} dataSource={tasks} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>
    </div>
  );
}
