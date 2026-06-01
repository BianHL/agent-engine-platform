'use client';

import React, { useEffect, useMemo } from 'react';
import {
  Drawer,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Space,
  Divider,
  Tag,
  message,
} from 'antd';
import { useWorkflowStore } from '@/store/workflow-store';
import type { WorkflowNode } from '@/types';
import { getNodeTypeConfig } from '../nodes/nodeTypes';

interface NodeConfigPanelProps {
  visible: boolean;
  onClose: () => void;
}

export default function NodeConfigPanel({
  visible,
  onClose,
}: NodeConfigPanelProps) {
  const selectedNode = useWorkflowStore((state) => {
    const selectedId = state.selectedNodeId;
    return state.nodes.find((n) => n.id === selectedId) || null;
  });

  const updateNode = useWorkflowStore((state) => state.updateNode);
  const [form] = Form.useForm();

  const nodeConfig = useMemo(() => {
    if (!selectedNode) return null;
    return getNodeTypeConfig(selectedNode.type);
  }, [selectedNode]);

  // Reset form when selected node changes
  useEffect(() => {
    if (selectedNode) {
      form.setFieldsValue({
        label: selectedNode.label,
        ...selectedNode.config,
      });
    }
  }, [selectedNode, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const { label, ...config } = values;

      if (selectedNode) {
        updateNode(selectedNode.id, {
          label: label || selectedNode.label,
          config,
        });
        message.success('Node configuration saved');
      }
      onClose();
    } catch (error) {
      // Validation failed
    }
  };

  const renderConfigFields = () => {
    if (!selectedNode) return null;

    switch (selectedNode.type) {
      case 'llm':
        return (
          <>
            <Form.Item
              name="model"
              label="Model"
              rules={[{ required: true, message: 'Please select a model' }]}
            >
              <Select
                placeholder="Select model"
                options={[
                  { value: 'gpt-4o', label: 'GPT-4o' },
                  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
                  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
                  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
                  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
                ]}
              />
            </Form.Item>

            <Form.Item
              name="prompt"
              label="System Prompt"
              rules={[{ required: true, message: 'Please enter a prompt' }]}
            >
              <Input.TextArea
                rows={6}
                placeholder="Enter system prompt. Use {{variable}} for dynamic values."
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item name="temperature" label="Temperature">
              <InputNumber
                min={0}
                max={2}
                step={0.1}
                style={{ width: '100%' }}
                placeholder="0.7"
              />
            </Form.Item>

            <Form.Item name="max_tokens" label="Max Tokens">
              <InputNumber
                min={1}
                max={32000}
                step={100}
                style={{ width: '100%' }}
                placeholder="2000"
              />
            </Form.Item>
          </>
        );

      case 'code':
        return (
          <>
            <Form.Item
              name="language"
              label="Language"
              rules={[{ required: true }]}
            >
              <Select
                options={[
                  { value: 'python', label: 'Python' },
                  { value: 'javascript', label: 'JavaScript' },
                  { value: 'typescript', label: 'TypeScript' },
                ]}
              />
            </Form.Item>

            <Form.Item
              name="code"
              label="Code"
              rules={[{ required: true, message: 'Enter code to execute' }]}
            >
              <Input.TextArea
                rows={10}
                placeholder="# Your code here"
                style={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
            </Form.Item>

            <Form.Item name="timeout" label="Timeout (seconds)">
              <InputNumber min={1} max={300} style={{ width: '100%' }} />
            </Form.Item>
          </>
        );

      case 'condition':
        return (
          <>
            <Form.Item
              name="expression"
              label="Condition Expression"
              rules={[{ required: true, message: 'Enter condition' }]}
              extra="Example: score > 0.8, status == 'approved'"
            >
              <Input.TextArea
                rows={3}
                placeholder="Enter expression that evaluates to true/false"
              />
            </Form.Item>

            <Form.Item
              name="true_label"
              label="True Branch Label"
              extra="Label for the output handle when condition is true"
            >
              <Input placeholder="Yes" />
            </Form.Item>

            <Form.Item
              name="false_label"
              label="False Branch Label"
              extra="Label for the output handle when condition is false"
            >
              <Input placeholder="No" />
            </Form.Item>
          </>
        );

      case 'parallel':
        return (
          <>
            <Form.Item
              name="branch_count"
              label="Number of Branches"
              rules={[{ required: true }]}
            >
              <InputNumber min={1} max={10} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="wait_for_all"
              label="Wait for All"
              valuePropName="checked"
              extra="If true, wait for all branches to complete"
            >
              <Select
                options={[
                  { value: true, label: 'Yes - Wait for all branches' },
                  { value: false, label: 'No - Continue on first completion' },
                ]}
              />
            </Form.Item>

            <Form.Item name="aggregation" label="Aggregation Strategy">
              <Select
                options={[
                  { value: 'all', label: 'Return all results' },
                  { value: 'first', label: 'Return first result' },
                  { value: 'merge', label: 'Merge results' },
                ]}
              />
            </Form.Item>
          </>
        );

      case 'loop':
        return (
          <>
            <Form.Item
              name="max_iterations"
              label="Max Iterations"
              rules={[{ required: true }]}
            >
              <InputNumber min={1} max={1000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="exit_condition"
              label="Exit Condition"
              extra="Optional: Expression to check for early exit"
            >
              <Input placeholder="e.g., result.done == true" />
            </Form.Item>

            <Form.Item
              name="loop_variable"
              label="Loop Variable Name"
              extra="Variable name to store iteration index"
            >
              <Input placeholder="i" />
            </Form.Item>

            <Form.Item name="collect_results" label="Collect Results" valuePropName="checked">
              <Select
                options={[
                  { value: true, label: 'Yes - Collect all iterations' },
                  { value: false, label: 'No - Keep only last result' },
                ]}
              />
            </Form.Item>
          </>
        );

      case 'http':
        return (
          <>
            <Form.Item
              name="url"
              label="URL"
              rules={[{ required: true, message: 'Enter URL' }]}
            >
              <Input placeholder="https://api.example.com/endpoint" />
            </Form.Item>

            <Form.Item
              name="method"
              label="Method"
              rules={[{ required: true }]}
            >
              <Select
                options={[
                  { value: 'GET', label: 'GET' },
                  { value: 'POST', label: 'POST' },
                  { value: 'PUT', label: 'PUT' },
                  { value: 'PATCH', label: 'PATCH' },
                  { value: 'DELETE', label: 'DELETE' },
                ]}
              />
            </Form.Item>

            <Form.Item name="headers" label="Headers">
              <Input.TextArea
                rows={3}
                placeholder='{"Authorization": "Bearer xxx"}'
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item name="body" label="Request Body (JSON)">
              <Input.TextArea
                rows={4}
                placeholder='{"key": "value"}'
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item name="timeout" label="Timeout (seconds)">
              <InputNumber min={1} max={300} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item name="auth_type" label="Authentication">
              <Select
                options={[
                  { value: 'none', label: 'None' },
                  { value: 'bearer', label: 'Bearer Token' },
                  { value: 'basic', label: 'Basic Auth' },
                  { value: 'api_key', label: 'API Key' },
                ]}
              />
            </Form.Item>
          </>
        );

      case 'human':
        return (
          <>
            <Form.Item
              name="message"
              label="Message to Human"
              rules={[{ required: true }]}
            >
              <Input.TextArea
                rows={4}
                placeholder="Instructions for human reviewer"
              />
            </Form.Item>

            <Form.Item name="timeout" label="Timeout (seconds)">
              <InputNumber min={60} max={86400} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="required_role"
              label="Required Role"
              extra="Optional: Require specific user role"
            >
              <Select
                options={[
                  { value: 'admin', label: 'Admin' },
                  { value: 'reviewer', label: 'Reviewer' },
                  { value: 'user', label: 'User' },
                ]}
                allowClear
              />
            </Form.Item>
          </>
        );

      case 'sub_workflow':
        return (
          <>
            <Form.Item
              name="workflow_id"
              label="Workflow"
              rules={[{ required: true, message: 'Select a workflow' }]}
            >
              <Select
                placeholder="Select workflow to execute"
                showSearch
                optionFilterProp="children"
                // Options would be loaded from API
                options={[]}
              />
            </Form.Item>

            <Form.Item
              name="input_mapping"
              label="Input Mapping"
              extra="Map current workflow variables to sub-workflow inputs"
            >
              <Input.TextArea
                rows={3}
                placeholder='{"input1": "{{parent.output1}}"}'
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item name="pass_context" label="Pass Full Context" valuePropName="checked">
              <Select
                options={[
                  { value: true, label: 'Yes - Pass entire context' },
                  { value: false, label: 'No - Pass only mapped values' },
                ]}
              />
            </Form.Item>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Drawer
      title={
        selectedNode ? (
          <Space>
            <span>{nodeConfig?.icon}</span>
            <span>Configure: {selectedNode.label}</span>
            <Tag color={nodeConfig?.color}>{nodeConfig?.label}</Tag>
          </Space>
        ) : (
          'Node Configuration'
        )
      }
      placement="right"
      width={450}
      open={visible}
      onClose={onClose}
      extra={
        <Button type="primary" onClick={handleSave}>
          Save
        </Button>
      }
    >
      {selectedNode ? (
        <Form form={form} layout="vertical">
          <Form.Item
            name="label"
            label="Node Label"
            rules={[{ required: true, message: 'Enter a label' }]}
          >
            <Input placeholder="Enter node label" />
          </Form.Item>

          <Divider orientation="left">Configuration</Divider>

          {renderConfigFields()}

          <Divider orientation="left">Advanced</Divider>

          <Form.Item name="retry_count" label="Retry Count">
            <InputNumber min={0} max={5} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="timeout" label="Timeout (seconds)">
            <InputNumber min={1} max={3600} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <Input.TextArea
              rows={2}
              placeholder="Optional description for this node"
            />
          </Form.Item>
        </Form>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          Select a node to configure
        </div>
      )}
    </Drawer>
  );
}
