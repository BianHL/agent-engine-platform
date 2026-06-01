'use client';
import React, { useState, useCallback } from 'react';
import { Card, Button, Input, Space, Table, Tag, Popconfirm, message, Tooltip, Upload, Typography } from 'antd';
import {
  PlusOutlined, DeleteOutlined, ImportOutlined, ExportOutlined,
  EditOutlined, CheckOutlined, CloseOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { TextArea } = Input;
const { Text } = Typography;

export interface TestQuestion {
  id: string;
  question: string;
  ground_truth: string;
  contexts?: string[];
  answer?: string;
}

interface TestQuestionEditorProps {
  value?: TestQuestion[];
  onChange?: (questions: TestQuestion[]) => void;
  disabled?: boolean;
}

let nextId = 1;
const genId = () => `q-${nextId++}-${Date.now()}`;

export default function TestQuestionEditor({ value = [], onChange, disabled }: TestQuestionEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editQuestion, setEditQuestion] = useState('');
  const [editGroundTruth, setEditGroundTruth] = useState('');
  const [addingNew, setAddingNew] = useState(false);
  const [newQuestion, setNewQuestion] = useState('');
  const [newGroundTruth, setNewGroundTruth] = useState('');

  const emit = useCallback((next: TestQuestion[]) => {
    onChange?.(next);
  }, [onChange]);

  const handleAdd = () => {
    if (!newQuestion.trim()) {
      message.warning('Question is required');
      return;
    }
    emit([...value, { id: genId(), question: newQuestion.trim(), ground_truth: newGroundTruth.trim() }]);
    setNewQuestion('');
    setNewGroundTruth('');
    setAddingNew(false);
  };

  const handleDelete = (id: string) => {
    emit(value.filter(q => q.id !== id));
  };

  const handleEdit = (record: TestQuestion) => {
    setEditingId(record.id);
    setEditQuestion(record.question);
    setEditGroundTruth(record.ground_truth);
  };

  const handleSaveEdit = () => {
    if (!editQuestion.trim()) {
      message.warning('Question is required');
      return;
    }
    emit(value.map(q => q.id === editingId ? { ...q, question: editQuestion.trim(), ground_truth: editGroundTruth.trim() } : q));
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
  };

  const handleImport: UploadProps['beforeUpload'] = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        let imported: TestQuestion[] = [];

        if (file.name.endsWith('.json')) {
          const data = JSON.parse(text);
          if (!Array.isArray(data)) throw new Error('JSON must be an array');
          imported = data.map((item: any) => ({
            id: genId(),
            question: item.question || '',
            ground_truth: item.ground_truth || item.expected_answer || '',
            contexts: item.contexts || [],
            answer: item.answer || '',
          }));
        } else if (file.name.endsWith('.csv')) {
          const lines = text.split('\n').filter(l => l.trim());
          if (lines.length < 2) throw new Error('CSV must have header + data rows');
          const header = lines[0].split(',').map(h => h.trim().toLowerCase());
          const qIdx = header.indexOf('question');
          const gIdx = header.indexOf('ground_truth');
          const eIdx = header.indexOf('expected_answer');
          if (qIdx === -1) throw new Error('CSV must have "question" column');
          for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',').map(c => c.trim());
            imported.push({
              id: genId(),
              question: cols[qIdx] || '',
              ground_truth: cols[gIdx] || cols[eIdx] || '',
            });
          }
        }

        if (imported.length === 0) throw new Error('No valid questions found');
        emit([...value, ...imported]);
        message.success(`Imported ${imported.length} questions`);
      } catch (err: any) {
        message.error(`Import failed: ${err.message}`);
      }
    };
    reader.readAsText(file);
    return false;
  };

  const handleExport = () => {
    if (value.length === 0) {
      message.warning('No questions to export');
      return;
    }
    const data = value.map(({ id, ...rest }) => rest);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'test-questions.json';
    a.click();
    URL.revokeObjectURL(url);
    message.success('Exported test questions');
  };

  const columns = [
    {
      title: '#',
      width: 50,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: 'Question',
      dataIndex: 'question',
      key: 'question',
      ellipsis: true,
      render: (text: string, record: TestQuestion) => {
        if (editingId === record.id) {
          return (
            <TextArea
              value={editQuestion}
              onChange={e => setEditQuestion(e.target.value)}
              autoSize={{ minRows: 1, maxRows: 4 }}
              size="small"
            />
          );
        }
        return <Text>{text}</Text>;
      },
    },
    {
      title: 'Ground Truth',
      dataIndex: 'ground_truth',
      key: 'ground_truth',
      ellipsis: true,
      render: (text: string, record: TestQuestion) => {
        if (editingId === record.id) {
          return (
            <TextArea
              value={editGroundTruth}
              onChange={e => setEditGroundTruth(e.target.value)}
              autoSize={{ minRows: 1, maxRows: 4 }}
              size="small"
            />
          );
        }
        return text ? <Text type="secondary">{text}</Text> : <Tag>empty</Tag>;
      },
    },
    {
      title: 'Actions',
      width: 120,
      render: (_: any, record: TestQuestion) => {
        if (editingId === record.id) {
          return (
            <Space>
              <Tooltip title="Save"><Button size="small" type="primary" icon={<CheckOutlined />} onClick={handleSaveEdit} /></Tooltip>
              <Tooltip title="Cancel"><Button size="small" icon={<CloseOutlined />} onClick={handleCancelEdit} /></Tooltip>
            </Space>
          );
        }
        return (
          <Space>
            <Tooltip title="Edit"><Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} disabled={disabled} /></Tooltip>
            <Popconfirm title="Delete this question?" onConfirm={() => handleDelete(record.id)}>
              <Tooltip title="Delete"><Button size="small" danger icon={<DeleteOutlined />} disabled={disabled} /></Tooltip>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <Card
      size="small"
      title={`Test Questions (${value.length})`}
      extra={
        <Space>
          <Upload accept=".json,.csv" showUploadList={false} beforeUpload={handleImport} disabled={disabled}>
            <Button size="small" icon={<ImportOutlined />} disabled={disabled}>Import</Button>
          </Upload>
          <Button size="small" icon={<ExportOutlined />} onClick={handleExport} disabled={disabled || value.length === 0}>
            Export
          </Button>
          <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => setAddingNew(true)} disabled={disabled}>
            Add
          </Button>
        </Space>
      }
    >
      {addingNew && (
        <div style={{ marginBottom: 12, padding: 12, background: '#fafafa', borderRadius: 6, border: '1px dashed #d9d9d9' }}>
          <Space direction="vertical" style={{ width: '100%' }} size={8}>
            <TextArea
              placeholder="Enter test question..."
              value={newQuestion}
              onChange={e => setNewQuestion(e.target.value)}
              autoSize={{ minRows: 1, maxRows: 3 }}
            />
            <TextArea
              placeholder="Enter expected answer (ground truth)..."
              value={newGroundTruth}
              onChange={e => setNewGroundTruth(e.target.value)}
              autoSize={{ minRows: 1, maxRows: 3 }}
            />
            <Space>
              <Button size="small" type="primary" onClick={handleAdd}>Add Question</Button>
              <Button size="small" onClick={() => { setAddingNew(false); setNewQuestion(''); setNewGroundTruth(''); }}>Cancel</Button>
            </Space>
          </Space>
        </div>
      )}
      <Table
        columns={columns}
        dataSource={value}
        rowKey="id"
        size="small"
        pagination={value.length > 10 ? { pageSize: 10 } : false}
        locale={{ emptyText: 'No test questions added. Click "Add" or "Import" to get started.' }}
      />
    </Card>
  );
}
