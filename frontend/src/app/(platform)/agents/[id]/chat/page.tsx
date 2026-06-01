'use client';
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Button, Typography, Space, Alert, Spin, Tag } from 'antd';
import {
  SendOutlined,
  StopOutlined,
  RobotOutlined,
  MessageOutlined,
  ClearOutlined,
  ReloadOutlined,
  PaperClipOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useParams } from 'next/navigation';
import TextareaAutosize from 'react-textarea-autosize';
import ChatMessage from '@/components/ChatMessage';
import { useChatStore } from '@/store/chat';

const { Title, Text } = Typography;

const ACCEPTED_TYPES = '.pdf,.docx,.doc,.txt,.csv,.md,.json,.png,.jpg,.jpeg,.gif,.webp';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

function WelcomeMessage({ onStartChat }: { onStartChat: () => void }) {
  const suggestions = [
    '帮我分析这段代码的性能问题',
    '解释一下这个功能是如何工作的',
    '帮我写一个单元测试',
    '优化这个查询语句',
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        padding: '40px 20px',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 24,
        }}
      >
        <RobotOutlined style={{ fontSize: 40, color: '#fff' }} />
      </div>
      <Title level={3} style={{ marginBottom: 8 }}>
        开始对话
      </Title>
      <Text type="secondary" style={{ fontSize: 14, marginBottom: 32, display: 'block' }}>
        向 Agent 发送消息或上传文件，开始您的对话之旅
      </Text>
      <Space wrap size="middle">
        {suggestions.map((suggestion, index) => (
          <Button
            key={index}
            size="large"
            onClick={() => onStartChat()}
            style={{
              borderRadius: 20,
              height: 40,
              padding: '0 20px',
              border: '1px solid #d9d9d9',
            }}
          >
            {suggestion}
          </Button>
        ))}
      </Space>
    </div>
  );
}

export default function ChatPage() {
  const params = useParams();
  const agentId = params.id as string;
  const [input, setInput] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const {
    messages,
    streaming,
    error,
    sendMessage,
    sendFileMessage,
    clearMessages,
    setStreaming,
    setError,
  } = useChatStore();

  const streamingMessage = messages.find((msg) => msg.role === 'assistant' && streaming);

  useEffect(() => {
    clearMessages();
    setError(null);
  }, [agentId, clearMessages, setError]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB.`);
      return;
    }

    setAttachedFile(file);
    setError(null);

    // Reset file input so same file can be re-selected
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [setError]);

  const handleRemoveFile = useCallback(() => {
    setAttachedFile(null);
  }, []);

  const handleSend = useCallback(async () => {
    const trimmedInput = input.trim();

    if (attachedFile) {
      try {
        await sendFileMessage(agentId, attachedFile, trimmedInput);
        setAttachedFile(null);
        setInput('');
        setError(null);
      } catch (error: any) {
        setError(error.message || 'Upload failed');
      }
      return;
    }

    if (!trimmedInput || streaming) return;

    abortControllerRef.current = new AbortController();
    setInput('');
    setError(null);

    try {
      await sendMessage(agentId, trimmedInput);
    } catch (error: any) {
      setError(error.message || '发送消息失败');
    }
  }, [input, streaming, agentId, sendMessage, sendFileMessage, attachedFile, setError]);

  const handleStop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
  }, [setStreaming]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        if (e.shiftKey) return;
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleClear = useCallback(() => {
    clearMessages();
    setError(null);
    setAttachedFile(null);
  }, [clearMessages, setError]);

  const handleRegenerate = useCallback(() => {
    if (messages.length < 2) return;
    const lastUserMessage = messages[messages.length - 2];
    if (lastUserMessage?.role === 'user') {
      setInput(lastUserMessage.content);
    }
  }, [messages]);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB.`);
      return;
    }

    setAttachedFile(file);
    setError(null);
    textareaRef.current?.focus();
  }, [setError]);

  const canSend = input.trim() || attachedFile;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 160px)',
        background: '#fff',
        borderRadius: 8,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 24px',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <MessageOutlined style={{ fontSize: 20, color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>对话</Title>
          {messages.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              ({messages.length} 条消息)
            </Text>
          )}
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            disabled={messages.length < 2 || streaming}
            onClick={handleRegenerate}
          >
            重新生成
          </Button>
          <Button
            icon={<ClearOutlined />}
            disabled={messages.length === 0 || streaming}
            onClick={handleClear}
          >
            清空对话
          </Button>
        </Space>
      </div>

      {/* Messages */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 24px',
          scrollBehavior: 'smooth',
        }}
      >
        {error && (
          <Alert
            message="出错了"
            description={error}
            type="error"
            showIcon
            closable
            style={{ margin: '16px 0' }}
            onClose={() => setError(null)}
          />
        )}

        {messages.length === 0 ? (
          <WelcomeMessage onStartChat={() => textareaRef.current?.focus()} />
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                streaming={streaming && msg === streamingMessage}
                onStop={handleStop}
              />
            ))}
            {streaming && !streamingMessage && (
              <div style={{ display: 'flex', gap: 12, padding: '16px 0', alignItems: 'center' }}>
                <Spin tip="Agent 正在思考..." />
              </div>
            )}
            <div style={{ height: 80 }} />
          </>
        )}
      </div>

      {/* Input area */}
      <div
        style={{
          padding: '16px 24px',
          borderTop: '1px solid #f0f0f0',
          background: '#fafafa',
        }}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {/* File preview */}
        {attachedFile && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            marginBottom: 8,
            background: '#e6f7ff',
            borderRadius: 6,
            border: '1px solid #91d5ff',
          }}>
            <PaperClipOutlined style={{ color: '#1890ff' }} />
            <Text ellipsis style={{ flex: 1, maxWidth: 300 }}>{attachedFile.name}</Text>
            <Tag>{(attachedFile.size / 1024).toFixed(1)} KB</Tag>
            <Button
              type="text"
              size="small"
              icon={<CloseCircleOutlined />}
              onClick={handleRemoveFile}
            />
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          {/* File upload button */}
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <Button
            icon={<PaperClipOutlined />}
            onClick={() => fileInputRef.current?.click()}
            disabled={streaming}
            size="large"
            style={{ borderRadius: 8, flexShrink: 0 }}
            title="Attach file"
          />

          {/* Text input */}
          <div
            style={{
              flex: 1,
              position: 'relative',
              border: '1px solid #d9d9d9',
              borderRadius: 8,
              background: '#fff',
              transition: 'all 0.3s',
              ...(input.length > 0 || streaming || attachedFile
                ? { borderColor: '#1890ff', boxShadow: '0 0 0 2px rgba(24, 144, 255, 0.2)' }
                : {}),
            }}
          >
            <TextareaAutosize
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={attachedFile ? "Add a message (optional)..." : "输入消息或拖拽文件... (Enter 发送，Shift+Enter 换行)"}
              disabled={streaming}
              minRows={1}
              maxRows={8}
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                borderRadius: 8,
                resize: 'none',
                outline: 'none',
                fontSize: 14,
                lineHeight: 1.5,
                fontFamily: 'inherit',
              }}
            />
          </div>

          {/* Send/Stop */}
          {streaming ? (
            <Button
              type="primary"
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
              size="large"
              style={{ height: 'auto', minHeight: 40, borderRadius: 8 }}
            >
              停止
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!canSend}
              size="large"
              style={{ height: 'auto', minHeight: 40, borderRadius: 8 }}
            >
              发送
            </Button>
          )}
        </div>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
          Enter 发送消息，Shift+Enter 换行 · 支持拖拽上传文件
        </Text>
      </div>
    </div>
  );
}
