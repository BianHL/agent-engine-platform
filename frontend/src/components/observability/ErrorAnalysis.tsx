'use client';
import React, { useState } from 'react';
import {
  Card, Col, Row, Table, Tag, Typography, Skeleton, Space,
  Input, Select, Statistic, Tooltip, Badge,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  SearchOutlined, WarningOutlined, BugOutlined,
  CloseCircleOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ErrorItem } from '@/app/(platform)/observability/page';

const { Text } = Typography;

interface Props {
  errors: ErrorItem[];
  loading: boolean;
}

export default function ErrorAnalysis({ errors, loading }: Props) {
  const [search, setSearch] = useState('');
  const [serviceFilter, setServiceFilter] = useState<string>('all');

  const services = Array.from(new Set(errors.map((e) => e.service)));

  const filteredErrors = errors.filter((e) => {
    const matchSearch = !search ||
      e.message.toLowerCase().includes(search.toLowerCase()) ||
      e.error_type.toLowerCase().includes(search.toLowerCase());
    const matchService = serviceFilter === 'all' || e.service === serviceFilter;
    return matchSearch && matchService;
  });

  const totalErrors = errors.reduce((sum, e) => sum + e.count, 0);
  const criticalErrors = errors.filter((e) => e.count > 100).length;
  const uniqueTypes = new Set(errors.map((e) => e.error_type)).size;

  // Error distribution by service - pie chart
  const errorsByService = services.map((svc) => ({
    name: svc,
    value: errors.filter((e) => e.service === svc).reduce((sum, e) => sum + e.count, 0),
  }));

  const pieChartOption = {
    tooltip: { trigger: 'item' as const, formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' as const },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' as const },
        },
        data: errorsByService,
      },
    ],
  };

  // Error trend over time - stacked area chart
  const allTimes = Array.from(
    new Set(errors.flatMap((e) => e.trend.map((t) => t.time)))
  ).sort();

  const trendChartOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { bottom: 0, type: 'scroll' as const },
    grid: { left: 50, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: 'category' as const,
      data: allTimes,
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Errors',
      axisLabel: { fontSize: 11 },
    },
    series: errors.slice(0, 5).map((err, idx) => {
      const colors = ['#ff4d4f', '#faad14', '#722ed1', '#13c2c2', '#eb2f96'];
      const timeMap = new Map(err.trend.map((t) => [t.time, t.count]));
      return {
        name: err.error_type,
        type: 'line' as const,
        stack: 'total',
        areaStyle: { opacity: 0.3 },
        smooth: true,
        showSymbol: false,
        itemStyle: { color: colors[idx % colors.length] },
        data: allTimes.map((t) => timeMap.get(t) || 0),
      };
    }),
  };

  const columns: ColumnsType<ErrorItem> = [
    {
      title: 'Severity',
      key: 'severity',
      width: 80,
      align: 'center',
      render: (_, record) => {
        if (record.count > 100) return <Badge status="error" text={<Text type="danger">Critical</Text>} />;
        if (record.count > 20) return <Badge status="warning" text={<Text type="warning">Warning</Text>} />;
        return <Badge status="default" text="Info" />;
      },
    },
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service',
      width: 130,
      render: (name: string) => <Tag color="blue">{name}</Tag>,
    },
    {
      title: 'Error Type',
      dataIndex: 'error_type',
      key: 'error_type',
      width: 180,
      render: (t: string) => <Tag color="red">{t}</Tag>,
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      width: 90,
      sorter: (a, b) => a.count - b.count,
      render: (count: number) => (
        <Text strong style={{ color: count > 100 ? '#ff4d4f' : count > 20 ? '#faad14' : '#333' }}>
          {count}
        </Text>
      ),
    },
    {
      title: 'Last Seen',
      dataIndex: 'last_seen',
      key: 'last_seen',
      width: 170,
      render: (t: string) => new Date(t).toLocaleString(),
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Row gutter={[16, 16]}>
          {[1, 2, 3].map((i) => (
            <Col xs={24} sm={8} key={i}>
              <Card bordered={false}><Skeleton active paragraph={{ rows: 2 }} /></Card>
            </Col>
          ))}
          <Col span={24}>
            <Card bordered={false}><Skeleton active paragraph={{ rows: 6 }} /></Card>
          </Col>
        </Row>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="Total Errors"
              value={totalErrors}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="Unique Error Types"
              value={uniqueTypes}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="Critical (>100 occurrences)"
              value={criticalErrors}
              prefix={<WarningOutlined />}
              valueStyle={{ color: criticalErrors > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={10}>
          <Card title="Errors by Service" bordered={false}>
            {errorsByService.length > 0 ? (
              <ReactECharts option={pieChartOption} style={{ height: 300 }} />
            ) : (
              <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                No error data
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="Error Trend" bordered={false}>
            {allTimes.length > 0 ? (
              <ReactECharts option={trendChartOption} style={{ height: 300 }} />
            ) : (
              <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                No trend data
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Error Table */}
      <Card
        bordered={false}
        title={<Text strong>Error Details</Text>}
        extra={
          <Space>
            <Input
              placeholder="Search errors..."
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 220 }}
              allowClear
            />
            <Select
              value={serviceFilter}
              onChange={setServiceFilter}
              style={{ width: 150 }}
              options={[
                { value: 'all', label: 'All Services' },
                ...services.map((s) => ({ value: s, label: s })),
              ]}
            />
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={filteredErrors}
          rowKey="id"
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `Total ${t} errors` }}
          size="middle"
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: '8px 0' }}>
                <Text strong>Full Message: </Text>
                <Text code style={{ whiteSpace: 'pre-wrap' }}>{record.message}</Text>
                {record.trend?.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <Text strong>Occurrence Timeline: </Text>
                    <div style={{ marginTop: 8 }}>
                      {record.trend.slice(-10).map((t, i) => (
                        <Tag key={i} style={{ marginBottom: 4 }}>
                          {new Date(t.time).toLocaleTimeString()}: {t.count}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ),
          }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
}
