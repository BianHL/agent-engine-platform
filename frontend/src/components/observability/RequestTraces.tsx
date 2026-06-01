'use client';
import React, { useState } from 'react';
import {
  Card, Table, Tag, Typography, Skeleton, Input, Select, Space,
  Drawer, Timeline, Descriptions, Tooltip,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { SearchOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import type { Trace, TraceSpan, TimeRange } from '@/app/(platform)/observability/page';

const { Text } = Typography;

interface Props {
  traces: Trace[];
  loading: boolean;
  timeRange: TimeRange;
}

const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
  ok: { color: 'success', icon: <CheckCircleOutlined /> },
  error: { color: 'error', icon: <CloseCircleOutlined /> },
  timeout: { color: 'warning', icon: <ClockCircleOutlined /> },
};

function formatDuration(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
  return `${ms.toFixed(0)}ms`;
}

export default function RequestTraces({ traces, loading }: Props) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const filteredTraces = traces.filter((t) => {
    const matchSearch = !search ||
      t.trace_id.toLowerCase().includes(search.toLowerCase()) ||
      t.root_service.toLowerCase().includes(search.toLowerCase()) ||
      t.root_operation.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || t.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const openTraceDetail = (trace: Trace) => {
    setSelectedTrace(trace);
    setDrawerOpen(true);
  };

  const columns: ColumnsType<Trace> = [
    {
      title: 'Trace ID',
      dataIndex: 'trace_id',
      key: 'trace_id',
      width: 200,
      render: (id: string) => (
        <Tooltip title={id}>
          <Text code style={{ cursor: 'pointer', fontSize: 12 }}>
            {id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-8)}` : id}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Service',
      dataIndex: 'root_service',
      key: 'root_service',
      width: 140,
      render: (name: string) => <Tag color="blue">{name}</Tag>,
    },
    {
      title: 'Operation',
      dataIndex: 'root_operation',
      key: 'root_operation',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const cfg = statusConfig[status] || statusConfig.ok;
        return <Tag color={cfg.color} icon={cfg.icon}>{status}</Tag>;
      },
    },
    {
      title: 'Duration',
      dataIndex: 'total_duration',
      key: 'total_duration',
      width: 110,
      sorter: (a, b) => a.total_duration - b.total_duration,
      render: (ms: number) => (
        <Text style={{ color: ms > 2000 ? '#ff4d4f' : ms > 500 ? '#faad14' : '#52c41a' }}>
          {formatDuration(ms)}
        </Text>
      ),
    },
    {
      title: 'Spans',
      dataIndex: 'span_count',
      key: 'span_count',
      width: 80,
      align: 'center',
    },
    {
      title: 'Start Time',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      render: (t: string) => new Date(t).toLocaleString(),
    },
  ];

  const renderSpanTimeline = (spans: TraceSpan[]) => {
    const sorted = [...spans].sort((a, b) =>
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    );
    return (
      <Timeline
        items={sorted.map((span) => {
          const cfg = statusConfig[span.status] || statusConfig.ok;
          return {
            color: cfg.color === 'success' ? 'green' : cfg.color === 'error' ? 'red' : 'orange',
            children: (
              <div style={{ cursor: 'pointer' }} onClick={() => {}}>
                <Space>
                  <Tag color="geekblue" style={{ margin: 0 }}>{span.service}</Tag>
                  <Text strong>{span.operation}</Text>
                  <Text type="secondary">{formatDuration(span.duration)}</Text>
                </Space>
                {span.tags && Object.keys(span.tags).length > 0 && (
                  <div style={{ marginTop: 4 }}>
                    {Object.entries(span.tags).slice(0, 5).map(([k, v]) => (
                      <Tag key={k} style={{ fontSize: 11, marginTop: 2 }}>{k}={v}</Tag>
                    ))}
                  </div>
                )}
              </div>
            ),
          };
        })}
      />
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Card
        bordered={false}
        title={
          <Space>
            <Text strong>Request Traces</Text>
            <Text type="secondary">({filteredTraces.length} results)</Text>
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="Search trace ID or service..."
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 240 }}
              allowClear
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 120 }}
              options={[
                { value: 'all', label: 'All Status' },
                { value: 'ok', label: 'OK' },
                { value: 'error', label: 'Error' },
                { value: 'timeout', label: 'Timeout' },
              ]}
            />
          </Space>
        }
      >
        {loading ? (
          <Skeleton active paragraph={{ rows: 8 }} />
        ) : (
          <Table
            columns={columns}
            dataSource={filteredTraces}
            rowKey="trace_id"
            pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (t) => `Total ${t} traces` }}
            size="middle"
            onRow={(record) => ({
              onClick: () => openTraceDetail(record),
              style: { cursor: 'pointer' },
            })}
            scroll={{ x: 900 }}
          />
        )}
      </Card>

      <Drawer
        title={
          selectedTrace ? (
            <Space>
              <Text>Trace Detail</Text>
              <Tag color="blue">{selectedTrace.root_service}</Tag>
              <Tag color={statusConfig[selectedTrace.status]?.color}>
                {selectedTrace.status}
              </Tag>
            </Space>
          ) : 'Trace Detail'
        }
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={600}
      >
        {selectedTrace && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Trace ID" span={2}>
                <Text code copyable>{selectedTrace.trace_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Service">{selectedTrace.root_service}</Descriptions.Item>
              <Descriptions.Item label="Operation">{selectedTrace.root_operation}</Descriptions.Item>
              <Descriptions.Item label="Duration">{formatDuration(selectedTrace.total_duration)}</Descriptions.Item>
              <Descriptions.Item label="Spans">{selectedTrace.span_count}</Descriptions.Item>
              <Descriptions.Item label="Start Time" span={2}>
                {new Date(selectedTrace.start_time).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            <Typography.Title level={5}>Span Timeline</Typography.Title>
            {selectedTrace.spans?.length > 0 ? (
              renderSpanTimeline(selectedTrace.spans)
            ) : (
              <Text type="secondary">No span details available</Text>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
}
