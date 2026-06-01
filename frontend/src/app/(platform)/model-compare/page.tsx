'use client';

import React, { useState } from 'react';
import {
  Card, Button, Input, Select, Space, Typography, Tag, Row, Col,
  Slider, message, Divider, Tooltip
} from 'antd';
import {
  ExperimentOutlined, PlayCircleOutlined, ClockCircleOutlined,
  CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import { api } from '@/lib/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ModelResult {
  model: string;
  response: string;
  latency_ms: number;
  tokens_used: number;
  success: boolean;
  error?: string;
}

export default function ModelComparePage() {
  const [prompt, setPrompt] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>(['gpt-4', 'claude-3-opus']);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [results, setResults] = useState<ModelResult[]>([]);
  const [loading, setLoading] = useState(false);

  const availableModels = [
    { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', provider: 'OpenAI' },
    { value: 'claude-3-opus', label: 'Claude 3 Opus', provider: 'Anthropic' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet', provider: 'Anthropic' },
    { value: 'llama-3-70b', label: 'Llama 3 70B', provider: 'Meta' },
    { value: 'qwen-72b', label: 'Qwen 72B', provider: 'Alibaba' }
  ];

  const defaultPresets = [
    { name: '通用对话', prompt: '请解释什么是人工智能', models: ['gpt-4', 'claude-3-opus'] },
    { name: '代码生成', prompt: '用 Python 实现快速排序算法', models: ['gpt-4', 'claude-3-opus'] },
    { name: '创意写作', prompt: '写一首关于春天的诗', models: ['gpt-4', 'claude-3-opus'] },
    { name: '逻辑推理', prompt: '如果所有的猫都怕水，Tom 是一只猫，那么 Tom 怕水吗？', models: ['gpt-4', 'claude-3-opus'] }
  ];

  const runComparison = async () => {
    if (!prompt.trim()) { message.warning('请输入测试 Prompt'); return; }
    if (selectedModels.length < 2) { message.warning('请至少选择 2 个模型'); return; }

    setLoading(true);
    try {
      const response = await api.post('/models/compare', {
        prompt, models: selectedModels,
        system_prompt: systemPrompt || undefined,
        temperature, max_tokens: maxTokens
      });
      setResults(response.data.results);
      message.success('对比完成');
    } catch (error) {
      message.error('对比失败');
    } finally {
      setLoading(false);
    }
  };

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = { 'OpenAI': 'green', 'Anthropic': 'purple', 'Meta': 'blue', 'Alibaba': 'orange' };
    return colors[provider] || 'default';
  };

  const getLatencyColor = (latency: number) => {
    if (latency < 1000) return '#52c41a';
    if (latency < 2000) return '#faad14';
    return '#ff4d4f';
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}><ExperimentOutlined className="mr-2" />多模型对比</Title>
        <Paragraph type="secondary">同一 Prompt 并行调用多个模型，结果并排对比</Paragraph>
      </div>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="测试配置" className="mb-4">
            <div className="space-y-4">
              <div>
                <Text strong>系统提示词（可选）</Text>
                <TextArea value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)}
                  placeholder="设置系统提示词..." autoSize={{ minRows: 2, maxRows: 4 }} className="mt-1" />
              </div>
              <div>
                <Text strong>测试 Prompt *</Text>
                <TextArea value={prompt} onChange={e => setPrompt(e.target.value)}
                  placeholder="输入要测试的 Prompt..." autoSize={{ minRows: 3, maxRows: 6 }} className="mt-1" />
              </div>
              <div>
                <Text strong>选择模型 *</Text>
                <Select mode="multiple" value={selectedModels} onChange={setSelectedModels} className="w-full mt-1"
                  placeholder="选择要对比的模型"
                  options={availableModels.map(m => ({
                    value: m.value,
                    label: <Space><span>{m.label}</span><Tag color={getProviderColor(m.provider)}>{m.provider}</Tag></Space>
                  }))} />
              </div>
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>Temperature: {temperature}</Text>
                  <Slider min={0} max={2} step={0.1} value={temperature} onChange={setTemperature} />
                </Col>
                <Col span={12}>
                  <Text strong>Max Tokens: {maxTokens}</Text>
                  <Slider min={256} max={8192} step={256} value={maxTokens} onChange={setMaxTokens} />
                </Col>
              </Row>
              <Button type="primary" size="large" icon={<PlayCircleOutlined />} onClick={runComparison} loading={loading} block>
                开始对比
              </Button>
            </div>
          </Card>
          <Card title="预设测试" className="mb-4">
            <div className="grid grid-cols-2 gap-3">
              {defaultPresets.map((preset, i) => (
                <Card key={i} size="small" hoverable onClick={() => { setPrompt(preset.prompt); setSelectedModels(preset.models); }}>
                  <Text strong>{preset.name}</Text><br />
                  <Text type="secondary" className="text-sm">{preset.prompt.slice(0, 50)}...</Text>
                </Card>
              ))}
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="模型列表">
            <div className="space-y-2">
              {availableModels.map(model => (
                <div key={model.value} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div><Text strong>{model.label}</Text><br /><Tag color={getProviderColor(model.provider)}>{model.provider}</Tag></div>
                  <CheckCircleOutlined className="text-green-500" />
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {results.length > 0 && (
        <Card title="对比结果" className="mt-4">
          <div className="mb-4">
            <Space>
              <ClockCircleOutlined />
              <Text>总耗时: {Math.max(...results.map(r => r.latency_ms)).toFixed(0)}ms</Text>
              <Divider type="vertical" />
              <Text>成功: {results.filter(r => r.success).length}/{results.length}</Text>
            </Space>
          </div>
          <div className="space-y-4">
            {results.map((result, i) => (
              <Card key={i} size="small" className={result.success ? 'border-green-200' : 'border-red-200'}>
                <div className="flex items-center justify-between mb-2">
                  <Space>
                    <Text strong className="text-lg">{result.model}</Text>
                    {result.success ? <Tag icon={<CheckCircleOutlined />} color="success">成功</Tag> : <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>}
                  </Space>
                  <Space>
                    <Tooltip title="延迟"><Tag color={getLatencyColor(result.latency_ms)}><ClockCircleOutlined /> {result.latency_ms.toFixed(0)}ms</Tag></Tooltip>
                    <Tooltip title="Token 用量"><Tag>{result.tokens_used} tokens</Tag></Tooltip>
                  </Space>
                </div>
                {result.success ? (
                  <div className="p-3 bg-gray-50 rounded"><Text>{result.response}</Text></div>
                ) : (
                  <div className="p-3 bg-red-50 rounded"><Text type="danger">{result.error}</Text></div>
                )}
              </Card>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
