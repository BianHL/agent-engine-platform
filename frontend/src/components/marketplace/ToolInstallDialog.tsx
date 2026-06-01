'use client';
import React, { useState } from 'react';
import { Modal, Form, Input, Switch, Typography, Space, Tag, Alert, Divider, message } from 'antd';
import { DownloadOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons';
import api from '@/lib/api';
import type { ToolMarketplaceItem } from '@/types/marketplace';

const { Text, Paragraph, Title } = Typography;
const { TextArea } = Input;

interface ToolInstallDialogProps {
  tool: ToolMarketplaceItem | null;
  open: boolean;
  onClose: () => void;
  onInstalled?: () => void;
}

export default function ToolInstallDialog({ tool, open, onClose, onInstalled }: ToolInstallDialogProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'config' | 'confirm' | 'done'>('config');

  const isInstalled = tool?.installed ?? false;

  const handleInstall = async () => {
    if (!tool) return;
    setLoading(true);
    try {
      const config = form.getFieldsValue();
      await api.createTool({
        name: tool.name,
        description: tool.description,
        tool_type: 'marketplace',
        config,
        enabled: true,
      });
      message.success(`${tool.display_name} installed successfully`);
      setStep('done');
      onInstalled?.();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || 'Installation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUninstall = async () => {
    if (!tool) return;
    setLoading(true);
    try {
      await api.deleteTool(tool.id);
      message.success(`${tool.display_name} uninstalled`);
      onInstalled?.();
      onClose();
    } catch {
      message.error('Uninstall failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStep('config');
    form.resetFields();
    onClose();
  };

  if (!tool) return null;

  const configFields = tool.config_schema?.properties as Record<string, any> | undefined;

  return (
    <Modal
      title={
        <Space>
          {isInstalled ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <DownloadOutlined />}
          {isInstalled ? `Manage ${tool.display_name}` : `Install ${tool.display_name}`}
        </Space>
      }
      open={open}
      onCancel={handleClose}
      width={520}
      footer={null}
    >
      {step === 'done' ? (
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
          <Title level={4}>Installation Complete</Title>
          <Paragraph type="secondary">
            {tool.display_name} has been installed and is ready to use.
          </Paragraph>
          <Space>
            <button
              onClick={handleClose}
              style={{
                padding: '8px 24px',
                background: '#1890ff',
                color: '#fff',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              Done
            </button>
          </Space>
        </div>
      ) : (
        <>
          {/* Tool Info */}
          <div style={{ marginBottom: 16 }}>
            <Paragraph>{tool.description}</Paragraph>
            <Space>
              <Tag>{tool.category}</Tag>
              <Tag>v{tool.version}</Tag>
              <Tag>by {tool.author}</Tag>
              {tool.license && <Tag>{tool.license}</Tag>}
            </Space>
          </div>

          <Divider style={{ margin: '16px 0' }} />

          {isInstalled ? (
            /* Installed state - manage */
            <div>
              <Alert
                message="This tool is currently installed"
                type="success"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <button
                onClick={handleUninstall}
                disabled={loading}
                style={{
                  padding: '8px 24px',
                  background: '#ff4d4f',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: 14,
                  width: '100%',
                }}
              >
                {loading ? 'Uninstalling...' : 'Uninstall Tool'}
              </button>
            </div>
          ) : (
            /* Not installed - config form */
            <Form form={form} layout="vertical">
              {configFields && Object.keys(configFields).length > 0 && (
                <>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>Configuration</Text>
                  {Object.entries(configFields).map(([key, schema]: [string, any]) => (
                    <Form.Item
                      key={key}
                      name={key}
                      label={schema.title || key}
                      help={schema.description}
                      rules={schema.required ? [{ required: true }] : undefined}
                    >
                      {schema.type === 'boolean' ? (
                        <Switch />
                      ) : schema.type === 'integer' || schema.type === 'number' ? (
                        <Input type="number" placeholder={schema.default?.toString() || ''} />
                      ) : (
                        <Input placeholder={schema.default?.toString() || ''} />
                      )}
                    </Form.Item>
                  ))}
                  <Divider style={{ margin: '12px 0' }} />
                </>
              )}

              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={handleClose}
                  style={{
                    flex: 1,
                    padding: '8px 24px',
                    background: '#f5f5f5',
                    border: '1px solid #d9d9d9',
                    borderRadius: 6,
                    cursor: 'pointer',
                    fontSize: 14,
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleInstall}
                  disabled={loading}
                  style={{
                    flex: 2,
                    padding: '8px 24px',
                    background: '#1890ff',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                    fontSize: 14,
                  }}
                >
                  {loading ? 'Installing...' : 'Install'}
                </button>
              </div>
            </Form>
          )}
        </>
      )}
    </Modal>
  );
}
