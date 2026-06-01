'use client';

import React, { useState } from 'react';
import {
  Card, Button, Input, Select, Tabs, Space, Typography, Tag, Divider,
  Row, Col, Slider, Switch, message, Modal
} from 'antd';
import {
  PlayCircleOutlined, SaveOutlined, CopyOutlined, UndoOutlined,
  RedoOutlined, ExperimentOutlined, BulbOutlined, CodeOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface PromptBlock {
  id: string;
  type: 'system' | 'user' | 'assistant' | 'variable' | 'context';
  content: string;
  label: string;
}

export default function PromptEditorPage() {
  const [blocks, setBlocks] = useState<PromptBlock[]>([
    { id: '1', type: 'system', content: '你是一个专业的AI助手。', label: 'System Prompt' },
    { id: '2', type: 'user', content: '{{input}}', label: 'User Input' }
  ]);
  const [activeBlock, setActiveBlock] = useState<string>('1');
  const [model, setModel] = useState('gpt-4');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState('');
  const [variables, setVariables] = useState<Record<string, string>>({});

  const addBlock = (type: PromptBlock['type']) => {
    const newBlock: PromptBlock = {
      id: Date.now().toString(),
      type,
      content: '',
      label: `${type.charAt(0).toUpperCase() + type.slice(1)} Block`
    };
    setBlocks([...blocks, newBlock]);
    setActiveBlock(newBlock.id);
  };

  const updateBlock = (id: string, content: string) => {
    setBlocks(blocks.map(b => b.id === id ? { ...b, content } : b));
  };

  const deleteBlock = (id: string) => {
    if (blocks.length <= 1) {
      message.warning('至少需要保留一个 Prompt 块');
      return;
    }
    setBlocks(blocks.filter(b => b.id !== id));
    if (activeBlock === id) setActiveBlock(blocks[0].id);
  };

  const testPrompt = async () => {
    setTesting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setTestResult('这是测试结果示例。AI 将根据您的 Prompt 生成响应。');
      message.success('测试完成');
    } catch (error) {
      message.error('测试失败');
    } finally {
      setTesting(false);
    }
  };

  const exportPrompt = () => {
    const prompt = blocks.map(b => `[${b.type}]\n${b.content}`).join('\n\n');
    navigator.clipboard.writeText(prompt);
    message.success('Prompt 已复制到剪贴板');
  };

  const getBlockColor = (type: PromptBlock['type']) => {
    const colors = { system: '#722ed1', user: '#1890ff', assistant: '#52c41a', variable: '#fa8c16', context: '#13c2c2' };
    return colors[type] || '#666';
  };

  const getBlockIcon = (type: PromptBlock['type']) => {
    const icons = { system: '⚙️', user: '👤', assistant: '🤖', variable: '📝', context: '📚' };
    return icons[type] || '📄';
  };

  const renderPreview = () => {
    return blocks.map(b => {
      let content = b.content;
      Object.entries(variables).forEach(([key, value]) => {
        content = content.replace(new RegExp(`{{${key}}}`, 'g'), value);
      });
      return `[${b.type}]\n${content}`;
    }).join('\n\n');
  };

  const activeBlockData = blocks.find(b => b.id === activeBlock);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <div className="flex items-center space-x-4">
          <Title level={4} className="mb-0"><CodeOutlined className="mr-2" />Prompt 可视化编排</Title>
          <Tag color="blue">Beta</Tag>
        </div>
        <Space>
          <Button icon={<UndoOutlined />}>撤销</Button>
          <Button icon={<RedoOutlined />}>重做</Button>
          <Button icon={<CopyOutlined />} onClick={exportPrompt}>导出</Button>
          <Button icon={<SaveOutlined />}>保存模板</Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={testPrompt} loading={testing}>测试运行</Button>
        </Space>
      </div>

      <div className="flex-1 flex">
        <div className="w-80 border-r bg-gray-50 p-4 overflow-auto">
          <div className="mb-4">
            <Text strong>Prompt 块</Text>
            <Button type="link" size="small" onClick={() => addBlock('system')} className="float-right">+ 添加</Button>
          </div>
          <div className="space-y-2">
            {blocks.map(block => (
              <Card
                key={block.id} size="small"
                className={`cursor-pointer transition-all ${activeBlock === block.id ? 'border-blue-500 shadow-md' : ''}`}
                onClick={() => setActiveBlock(block.id)}
                style={{ borderLeft: `4px solid ${getBlockColor(block.type)}` }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span>{getBlockIcon(block.type)}</span>
                    <Text strong>{block.label}</Text>
                  </div>
                  <Tag color={getBlockColor(block.type)}>{block.type}</Tag>
                </div>
                <Text type="secondary" className="text-xs block mt-1 truncate">{block.content || '点击编辑...'}</Text>
              </Card>
            ))}
          </div>
          <Divider />
          <div className="space-y-2">
            <Text strong>添加块类型</Text>
            <div className="grid grid-cols-2 gap-2">
              {(['system', 'user', 'assistant', 'variable', 'context'] as const).map(type => (
                <Button key={type} size="small" onClick={() => addBlock(type)} icon={<span>{getBlockIcon(type)}</span>}>{type}</Button>
              ))}
            </div>
          </div>
          <Divider />
          <div>
            <Text strong>变量</Text>
            <div className="mt-2 space-y-2">
              {blocks.flatMap(b => b.content.match(/\{\{(\w+)\}\}/g) || [])
                .filter((v, i, a) => a.indexOf(v) === i)
                .map(v => {
                  const varName = v.replace(/\{\{|\}\}/g, '');
                  return (
                    <div key={varName} className="flex items-center space-x-2">
                      <Tag color="orange">{varName}</Tag>
                      <Input size="small" placeholder="测试值" value={variables[varName]}
                        onChange={e => setVariables({ ...variables, [varName]: e.target.value })} />
                    </div>
                  );
                })}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b bg-white">
            <Row gutter={16}>
              <Col span={8}>
                <Text strong>模型</Text>
                <Select value={model} onChange={setModel} className="w-full mt-1"
                  options={[
                    { value: 'gpt-4', label: 'GPT-4' },
                    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
                    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' }
                  ]} />
              </Col>
              <Col span={8}>
                <Text strong>Temperature: {temperature}</Text>
                <Slider min={0} max={2} step={0.1} value={temperature} onChange={setTemperature} className="mt-1" />
              </Col>
              <Col span={8}>
                <Text strong>Max Tokens: {maxTokens}</Text>
                <Slider min={256} max={8192} step={256} value={maxTokens} onChange={setMaxTokens} className="mt-1" />
              </Col>
            </Row>
          </div>
          <div className="flex-1 p-4 overflow-auto">
            {activeBlockData && (
              <Card
                title={
                  <div className="flex items-center space-x-2">
                    <span>{getBlockIcon(activeBlockData.type)}</span>
                    <Input value={activeBlockData.label}
                      onChange={e => setBlocks(blocks.map(b => b.id === activeBlock ? { ...b, label: e.target.value } : b))}
                      variant="borderless" className="text-lg font-bold" />
                  </div>
                }
                extra={
                  <Space>
                    <Select value={activeBlockData.type}
                      onChange={type => setBlocks(blocks.map(b => b.id === activeBlock ? { ...b, type } : b))}
                      options={[
                        { value: 'system', label: 'System' }, { value: 'user', label: 'User' },
                        { value: 'assistant', label: 'Assistant' }, { value: 'variable', label: 'Variable' },
                        { value: 'context', label: 'Context' }
                      ]} />
                    <Button danger size="small" onClick={() => deleteBlock(activeBlock)}>删除</Button>
                  </Space>
                }
              >
                <TextArea value={activeBlockData.content} onChange={e => updateBlock(activeBlock, e.target.value)}
                  placeholder="输入 Prompt 内容..." autoSize={{ minRows: 10, maxRows: 30 }} className="font-mono" />
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <Text type="secondary" className="text-sm">
                    <BulbOutlined className="mr-1" />提示: 使用 {'{{变量名}'} 定义变量，可在左侧设置测试值
                  </Text>
                </div>
              </Card>
            )}
          </div>
        </div>

        <div className="w-96 border-l bg-gray-50 flex flex-col">
          <Tabs className="flex-1 flex flex-col"
            items={[
              {
                key: 'preview', label: '预览',
                children: (
                  <div className="p-4 flex-1 overflow-auto">
                    <Card size="small">
                      <Text strong>完整 Prompt 预览</Text>
                      <pre className="mt-2 p-3 bg-gray-100 rounded text-sm whitespace-pre-wrap">{renderPreview()}</pre>
                    </Card>
                  </div>
                )
              },
              {
                key: 'test', label: '测试',
                children: (
                  <div className="p-4 flex-1 flex flex-col">
                    <div className="flex-1 overflow-auto mb-4">
                      {testResult ? (
                        <Card size="small">
                          <Text strong>测试结果</Text>
                          <div className="mt-2 p-3 bg-green-50 rounded">{testResult}</div>
                        </Card>
                      ) : (
                        <div className="text-center text-gray-400 py-8">
                          <ExperimentOutlined className="text-4xl mb-2" />
                          <div>点击"测试运行"查看结果</div>
                        </div>
                      )}
                    </div>
                    <Button type="primary" block icon={<PlayCircleOutlined />} onClick={testPrompt} loading={testing}>测试运行</Button>
                  </div>
                )
              },
              {
                key: 'templates', label: '模板',
                children: (
                  <div className="p-4 overflow-auto">
                    <div className="space-y-3">
                      {[
                        { name: '客服助手', desc: '专业的客服对话模板' },
                        { name: '代码生成', desc: '代码生成和解释模板' },
                        { name: '文案创作', desc: '营销文案创作模板' },
                        { name: '数据分析', desc: '数据分析和报告模板' },
                        { name: '翻译助手', desc: '多语言翻译模板' }
                      ].map((template, i) => (
                        <Card key={i} size="small" hoverable onClick={() => message.info(`加载模板: ${template.name}`)}>
                          <Text strong>{template.name}</Text>
                          <br />
                          <Text type="secondary" className="text-sm">{template.desc}</Text>
                        </Card>
                      ))}
                    </div>
                  </div>
                )
              }
            ]}
          />
        </div>
      </div>
    </div>
  );
}
