'use client';
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  Card, Table, Typography, Tag, Select, DatePicker, Space, message, Button, Empty, Modal,
} from 'antd';
import { DownloadOutlined, AuditOutlined, EyeOutlined } from '@ant-design/icons';
import api from '@/lib/api';
import { AuditLog } from '@/types';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const ACTION_COLORS: Record<string, string> = {
  create: 'success',
  update: 'processing',
  delete: 'error',
  execute: 'warning',
  login: 'blue',
  logout: 'default',
};

function JsonDiff({ before, after }: { before?: Record<string, any>; after?: Record<string, any> }) {
  if (!before && !after) {
    return <Text type="secondary">No change data available</Text>;
  }

  const allKeys = useMemo(() => {
    const keys = new Set<string>();
    if (before) Object.keys(before).forEach(keys.add, keys);
    if (after) Object.keys(after).forEach(keys.add, keys);
    return Array.from(keys).sort();
  }, [before, after]);

  return (
    <div style={{ display: 'flex', gap: 16, fontFamily: 'monospace', fontSize: 12 }}>
      <div style={{ flex: 1 }}>
        <Text strong style={{ display: 'block', marginBottom: 8 }}>Before:</Text>
        <pre style={{
          background: '#fff1f0',
          padding: 12,
          borderRadius: 6,
          maxHeight: 400,
          overflow: 'auto',
          margin: 0,
          border: '1px solid #ffa39e',
        }}>
          {before ? JSON.stringify(before, null, 2) : 'N/A'}
        </pre>
      </div>
      <div style={{ flex: 1 }}>
        <Text strong style={{ display: 'block', marginBottom: 8 }}>After:</Text>
        <pre style={{
          background: '#f6ffed',
          padding: 12,
          borderRadius: 6,
          maxHeight: 400,
          overflow: 'auto',
          margin: 0,
          border: '1px solid #b7eb8f',
        }}>
          {after ? JSON.stringify(after, null, 2) : 'N/A'}
        </pre>
      </div>
    </div>
  );
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<any>({});
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  // Detail modal
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = useCallback(() => {
    setLoading(true);
    api.listAuditLogs(filters, page, 50)
      .then((res) => {
        const items = Array.isArray(res) ? res : res?.items || [];
        setLogs(items);
        setTotal(res?.total || items.length);
      })
      .catch(() => message.error('Failed to load audit logs'))
      .finally(() => setLoading(false));
  }, [filters, page]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const handleViewDetail = (record: AuditLog) => {
    setSelectedLog(record);
    setDetailModalOpen(true);
  };

  const handleExportCsv = () => {
    const headers = ['ID', 'Action', 'Resource Type', 'Resource ID', 'User ID', 'IP Address', 'Time'];
    const rows = logs.map((log) => [
      log.id,
      log.action,
      log.resource_type,
      log.resource_id,
      log.user_id,
      log.ip_address || '',
      log.created_at,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    message.success('Exported CSV');
  };

  const columns = [
    {
      title: 'Action', dataIndex: 'action', key: 'action', width: 100,
      render: (a: string) => <Tag color={ACTION_COLORS[a] || 'default'}>{a}</Tag>,
    },
    { title: 'Resource', dataIndex: 'resource_type', key: 'resource_type', width: 120 },
    { title: 'Resource ID', dataIndex: 'resource_id', key: 'resource_id', ellipsis: true },
    { title: 'User ID', dataIndex: 'user_id', key: 'user_id', ellipsis: true },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip_address', width: 130 },
    {
      title: 'Time', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: 'Detail', key: 'detail', width: 80,
      render: (_: any, record: AuditLog) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record)}
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Audit Logs</Title>
        <Button
          icon={<DownloadOutlined />}
          onClick={handleExportCsv}
          disabled={logs.length === 0}
        >
          Export CSV
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="Action"
          allowClear
          style={{ width: 120 }}
          onChange={(v) => {
            setPage(1);
            setFilters((f: any) => ({ ...f, action: v }));
          }}
          options={[
            { value: 'create', label: 'Create' },
            { value: 'update', label: 'Update' },
            { value: 'delete', label: 'Delete' },
            { value: 'execute', label: 'Execute' },
            { value: 'login', label: 'Login' },
            { value: 'logout', label: 'Logout' },
          ]}
        />
        <Select
          placeholder="Resource Type"
          allowClear
          style={{ width: 150 }}
          onChange={(v) => {
            setPage(1);
            setFilters((f: any) => ({ ...f, resource_type: v }));
          }}
          options={[
            { value: 'agents', label: 'Agents' },
            { value: 'knowledge', label: 'Knowledge' },
            { value: 'workflows', label: 'Workflows' },
            { value: 'tools', label: 'Tools' },
            { value: 'conversations', label: 'Conversations' },
            { value: 'models', label: 'Models' },
          ]}
        />
        <Select
          placeholder="User"
          allowClear
          showSearch
          style={{ width: 180 }}
          onChange={(v) => {
            setPage(1);
            setFilters((f: any) => ({ ...f, user_id: v }));
          }}
          options={Array.from(new Set(logs.map((l) => l.user_id).filter(Boolean))).map((id) => ({
            value: id,
            label: id,
          }))}
        />
        <RangePicker
          onChange={(dates) => {
            setPage(1);
            if (dates && dates[0] && dates[1]) {
              setFilters((f: any) => ({
                ...f,
                date_start: dates[0]!.toISOString(),
                date_end: dates[1]!.toISOString(),
              }));
            } else {
              setFilters((f: any) => {
                const { date_start, date_end, ...rest } = f;
                return rest;
              });
            }
          }}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: 50,
          total,
          onChange: setPage,
          showSizeChanger: false,
          showTotal: (t) => `Total ${t} logs`,
        }}
        locale={{
          emptyText: (
            <Empty
              image={<AuditOutlined style={{ fontSize: 48, color: '#bbb' }} />}
              description="No audit logs found"
            />
          ),
        }}
      />

      {/* Detail Modal */}
      <Modal
        title={
          <Space>
            <Tag color={ACTION_COLORS[selectedLog?.action || ''] || 'default'}>
              {selectedLog?.action}
            </Tag>
            <span>Audit Log Detail</span>
          </Space>
        }
        open={detailModalOpen}
        onCancel={() => setDetailModalOpen(false)}
        footer={null}
        width={800}
      >
        {selectedLog && (
          <div>
            <Card size="small" style={{ marginBottom: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div><Text type="secondary">Resource Type:</Text> <Text strong>{selectedLog.resource_type}</Text></div>
                <div><Text type="secondary">Resource ID:</Text> <Text strong copyable>{selectedLog.resource_id}</Text></div>
                <div><Text type="secondary">User ID:</Text> <Text strong>{selectedLog.user_id}</Text></div>
                <div><Text type="secondary">IP Address:</Text> <Text strong>{selectedLog.ip_address || 'N/A'}</Text></div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <Text type="secondary">Time:</Text> <Text strong>
                    {selectedLog.created_at ? new Date(selectedLog.created_at).toLocaleString() : 'N/A'}
                  </Text>
                </div>
              </div>
            </Card>

            <Text strong style={{ display: 'block', marginBottom: 8 }}>Change Details:</Text>
            <JsonDiff before={selectedLog.before_data} after={selectedLog.after_data} />

            {selectedLog.detail && (
              <div style={{ marginTop: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Additional Detail:</Text>
                <pre style={{
                  background: '#f6f8fa',
                  padding: 12,
                  borderRadius: 6,
                  maxHeight: 200,
                  overflow: 'auto',
                  fontSize: 12,
                }}>
                  {JSON.stringify(selectedLog.detail, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
