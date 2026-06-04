'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, Typography, Space, Tag, Spin } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ClearOutlined } from '@ant-design/icons';
import { useWorkflowStore } from '@/store/workflow-store';

const { Text } = Typography;

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatflowPreviewProps {
  workflowId?: string;
  onSendMessage?: (message: string) => Promise<string>;
}

export default function ChatflowPreview({ workflowId, onSendMessage }: ChatflowPreviewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const nodes = useWorkflowStore((state) => state.nodes);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      let response = '';
      if (onSendMessage) {
        response = await onSendMessage(input.trim());
      } else {
        response = `[Preview] Simulated response for: "${input.trim()}"`;
      }
      const assistantMsg: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      const errorMsg: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => setMessages([]);
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <Card
      title={<Space><RobotOutlined /><span>Chatflow Preview</span><Tag color="blue">{nodes.length} nodes</Tag></Space>}
      size="small"
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}
      extra={<Button icon={<ClearOutlined />} onClick={handleClear} size="small" disabled={messages.length === 0}>Clear</Button>}
    >
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', background: '#fafafa', minHeight: 200 }}>
        {messages.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#999' }}>
            <RobotOutlined style={{ fontSize: 32, marginBottom: 8 }} />
            <Text type="secondary">Start a conversation to preview the chatflow</Text>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: '8px' }}>
              <div style={{ maxWidth: '80%', padding: '8px 12px', borderRadius: '8px', background: msg.role === 'user' ? '#1890ff' : '#fff', color: msg.role === 'user' ? '#fff' : '#333', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  {msg.role === 'user' ? <UserOutlined style={{ fontSize: 12 }} /> : <RobotOutlined style={{ fontSize: 12 }} />}
                  <Text style={{ fontSize: '10px', color: msg.role === 'user' ? 'rgba(255,255,255,0.8)' : '#999' }}>{msg.role === 'user' ? 'You' : 'Assistant'}</Text>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: '13px' }}>{msg.content}</div>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '8px' }}>
            <div style={{ padding: '8px 12px', borderRadius: '8px', background: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' }}>
              <Spin size="small" /><Text style={{ marginLeft: '8px', fontSize: '13px' }}>Thinking...</Text>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div style={{ padding: '12px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Type a message to test the chatflow..." disabled={loading} />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading} disabled={!input.trim()} />
        </Space.Compact>
      </div>
    </Card>
  );
}
