'use client';
import React from 'react';
import { Avatar, Tag, Space, Typography, Button } from 'antd';
import {
  UserOutlined,
  RobotOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { ChatMessage as ChatMessageType } from '@/types';
import MarkdownRenderer from './MarkdownRenderer';

const { Text } = Typography;

interface Props {
  message: ChatMessageType;
  streaming?: boolean;
  onStop?: () => void;
}

export default function ChatMessage({ message, streaming, onStop }: Props) {
  const isUser = message.role === 'user';

  // 格式化时间戳
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        padding: '16px 0',
        flexDirection: isUser ? 'row-reverse' : 'row',
        animation: 'fadeIn 0.3s ease-in',
      }}
    >
      {/* 头像 */}
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{
          backgroundColor: isUser ? '#1890ff' : '#52c41a',
          flexShrink: 0,
          width: 36,
          height: 36,
        }}
      />

      {/* 消息内容容器 */}
      <div style={{ flex: 1, maxWidth: 'calc(100% - 60px)' }}>
        {/* 消息头部：名称和时间 */}
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4, gap: 8 }}>
          <Text strong style={{ fontSize: 13 }}>
            {isUser ? 'You' : message.agent_name || 'Assistant'}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {formatTime(message.created_at)}
          </Text>
          {message.status && (
            <Tag
              icon={
                message.status === 'completed' ? (
                  <CheckCircleOutlined />
                ) : message.status === 'failed' ? (
                  <CloseCircleOutlined />
                ) : (
                  <LoadingOutlined />
                )
              }
              color={message.status === 'completed' ? 'success' : message.status === 'failed' ? 'error' : 'processing'}
              style={{ fontSize: 11, margin: 0 }}
            >
              {message.status}
            </Tag>
          )}
        </div>

        {/* 消息气泡 */}
        <div
          style={{
            maxWidth: '100%',
            padding: isUser ? '12px 16px' : 0,
            borderRadius: 12,
            backgroundColor: isUser ? '#1890ff' : 'transparent',
            color: isUser ? '#fff' : '#333',
          }}
        >
          <div style={{ wordBreak: 'break-word' }}>
            {isUser ? (
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{message.content}</div>
            ) : (
              <div style={{ position: 'relative' }}>
                <MarkdownRenderer content={message.content} />
                {/* 流式输入光标 */}
                {streaming && (
                  <span
                    style={{
                      display: 'inline-block',
                      width: 8,
                      height: 16,
                      background: '#52c41a',
                      marginLeft: 4,
                      animation: 'blink 1s infinite',
                      verticalAlign: 'middle',
                    }}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* 工具调用信息（如果有） */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <Space direction="vertical" style={{ marginTop: 8, width: '100%' }}>
            {message.tool_calls.map((tool, index) => (
              <div
                key={index}
                style={{
                  padding: 12,
                  background: '#f6f8fa',
                  borderRadius: 6,
                  border: '1px solid #e1e4e8',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <Tag color="blue">{tool.function?.name || 'Tool Call'}</Tag>
                  {tool.status === 'completed' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  {tool.status === 'failed' && <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                  {tool.status === 'running' && <LoadingOutlined />}
                </div>
                {tool.output && (
                  <div style={{ marginTop: 8, padding: 8, background: '#fff', borderRadius: 4 }}>
                    <Text code style={{ fontSize: 12 }}>{tool.output}</Text>
                  </div>
                )}
              </div>
            ))}
          </Space>
        )}

        {/* 停止按钮 */}
        {streaming && !isUser && onStop && (
          <Button
            type="link"
            size="small"
            onClick={onStop}
            style={{ padding: 0, marginTop: 8, color: '#ff4d4f' }}
          >
            Stop Generating
          </Button>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
