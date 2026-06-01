'use client';
import React, { useMemo, useState } from 'react';
import {
  Card, Col, Row, Typography, Skeleton, Space, Tag, Statistic,
  Descriptions, Drawer, Badge, Tooltip,
} from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined,
  ClusterOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ServiceMapData, ServiceNode } from '@/app/(platform)/observability/page';

const { Text } = Typography;

interface Props {
  data: ServiceMapData | null;
  loading: boolean;
}

const statusConfig: Record<string, { color: string; icon: React.ReactNode; badge: 'success' | 'error' | 'warning' }> = {
  healthy: { color: '#52c41a', icon: <CheckCircleOutlined />, badge: 'success' },
  degraded: { color: '#faad14', icon: <ExclamationCircleOutlined />, badge: 'warning' },
  down: { color: '#ff4d4f', icon: <CloseCircleOutlined />, badge: 'error' },
};

export default function ServiceMap({ data, loading }: Props) {
  const [selectedNode, setSelectedNode] = useState<ServiceNode | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const chartOption = useMemo(() => {
    if (!data) return {};

    const categories = [
      { name: 'healthy', itemStyle: { color: '#52c41a' } },
      { name: 'degraded', itemStyle: { color: '#faad14' } },
      { name: 'down', itemStyle: { color: '#ff4d4f' } },
    ];

    const categoryMap: Record<string, number> = { healthy: 0, degraded: 1, down: 2 };

    const nodes = data.nodes.map((node) => ({
      id: node.id,
      name: node.name,
      value: node.qps,
      category: categoryMap[node.status] ?? 0,
      symbolSize: Math.max(30, Math.min(60, 20 + node.qps * 2)),
      label: {
        show: true,
        position: 'bottom' as const,
        formatter: node.name,
        fontSize: 12,
      },
      itemStyle: {
        borderColor: statusConfig[node.status]?.color || '#999',
        borderWidth: 3,
      },
      tooltip: {
        formatter: () => `
          <div style="padding: 4px 0">
            <strong>${node.name}</strong><br/>
            Status: ${node.status}<br/>
            QPS: ${node.qps}<br/>
            Error Rate: ${node.error_rate}%<br/>
            Avg Latency: ${node.avg_latency}ms
          </div>
        `,
      },
    }));

    const edges = data.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      value: edge.qps,
      lineStyle: {
        width: Math.max(1, Math.min(6, edge.qps / 10)),
        color: edge.error_rate > 5 ? '#ff4d4f' : edge.error_rate > 1 ? '#faad14' : '#aaa',
        curveness: 0.2,
      },
      label: {
        show: edge.qps > 5,
        formatter: `${edge.qps} qps`,
        fontSize: 10,
      },
    }));

    return {
      tooltip: { trigger: 'item' as const },
      legend: {
        data: ['healthy', 'degraded', 'down'],
        bottom: 10,
        formatter: (name: string) => name.charAt(0).toUpperCase() + name.slice(1),
      },
      animationDuration: 800,
      animationEasingUpdate: 'quinticInOut' as const,
      series: [
        {
          type: 'graph',
          layout: 'force' as const,
          data: nodes,
          links: edges,
          categories,
          roam: true,
          draggable: true,
          force: {
            repulsion: 300,
            gravity: 0.1,
            edgeLength: [120, 250],
            layoutAnimation: true,
          },
          emphasis: {
            focus: 'adjacency' as const,
            lineStyle: { width: 4 },
          },
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: [0, 10],
        },
      ],
    };
  }, [data]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card bordered={false}><Skeleton active paragraph={{ rows: 3 }} /></Card>
          </Col>
          <Col span={24}>
            <Card bordered={false}><div style={{ height: 500 }} /></Card>
          </Col>
        </Row>
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div style={{ padding: 24 }}>
        <Card bordered={false}>
          <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
            <Space direction="vertical" align="center">
              <ClusterOutlined style={{ fontSize: 48, opacity: 0.3 }} />
              <Text type="secondary">No service topology data available</Text>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  const healthyCount = data.nodes.filter((n) => n.status === 'healthy').length;
  const degradedCount = data.nodes.filter((n) => n.status === 'degraded').length;
  const downCount = data.nodes.filter((n) => n.status === 'down').length;

  const handleChartClick = (params: any) => {
    if (params.dataType === 'node') {
      const node = data.nodes.find((n) => n.id === params.data.id);
      if (node) {
        setSelectedNode(node);
        setDrawerOpen(true);
      }
    }
  };

  const onEvents = { click: handleChartClick };

  // Find upstream and downstream connections for selected node
  const getConnections = (nodeId: string) => {
    const upstream = data.edges
      .filter((e) => e.target === nodeId)
      .map((e) => ({
        node: data.nodes.find((n) => n.id === e.source),
        edge: e,
      }));
    const downstream = data.edges
      .filter((e) => e.source === nodeId)
      .map((e) => ({
        node: data.nodes.find((n) => n.id === e.target),
        edge: e,
      }));
    return { upstream, downstream };
  };

  return (
    <div style={{ padding: 24 }}>
      {/* Summary */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="Total Services"
              value={data.nodes.length}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="Healthy / Degraded / Down"
              value={healthyCount}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <Text type="secondary" style={{ fontSize: 14 }}>
                  / <span style={{ color: '#faad14' }}>{degradedCount}</span> / <span style={{ color: '#ff4d4f' }}>{downCount}</span>
                </Text>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card bordered={false}>
            <Statistic
              title="Total Connections"
              value={data.edges.length}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Service List */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card bordered={false} title={<Text strong>Services</Text>} bodyStyle={{ paddingTop: 12 }}>
            <Space size={[8, 8]} wrap>
              {data.nodes.map((node) => {
                const cfg = statusConfig[node.status] || statusConfig.healthy;
                return (
                  <Tag
                    key={node.id}
                    color={cfg.color}
                    style={{ cursor: 'pointer', padding: '4px 12px' }}
                    onClick={() => { setSelectedNode(node); setDrawerOpen(true); }}
                  >
                    {cfg.icon} {node.name}
                  </Tag>
                );
              })}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Topology Graph */}
      <Card
        bordered={false}
        title={<Text strong>Service Dependency Map</Text>}
        extra={<Text type="secondary">Click a node for details. Drag to rearrange.</Text>}
      >
        <ReactECharts
          option={chartOption}
          style={{ height: 500 }}
          onEvents={onEvents}
          opts={{ renderer: 'canvas' }}
        />
      </Card>

      {/* Node Detail Drawer */}
      <Drawer
        title={
          selectedNode && (
            <Space>
              <Badge status={statusConfig[selectedNode.status]?.badge} />
              <Text strong>{selectedNode.name}</Text>
              <Tag>{selectedNode.type}</Tag>
            </Space>
          )
        }
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
      >
        {selectedNode && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Status" span={2}>
                <Badge
                  status={statusConfig[selectedNode.status]?.badge}
                  text={selectedNode.status}
                />
              </Descriptions.Item>
              <Descriptions.Item label="QPS">{selectedNode.qps}</Descriptions.Item>
              <Descriptions.Item label="Error Rate">
                <Text style={{ color: selectedNode.error_rate > 5 ? '#ff4d4f' : '#52c41a' }}>
                  {selectedNode.error_rate}%
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Avg Latency">{selectedNode.avg_latency}ms</Descriptions.Item>
              <Descriptions.Item label="Type">{selectedNode.type}</Descriptions.Item>
            </Descriptions>

            {(() => {
              const { upstream, downstream } = getConnections(selectedNode.id);
              return (
                <>
                  {upstream.length > 0 && (
                    <>
                      <Typography.Title level={5}>Upstream (calling {selectedNode.name})</Typography.Title>
                      {upstream.map(({ node, edge }) => node && (
                        <Card key={node.id} size="small" style={{ marginBottom: 8 }}>
                          <Space>
                            <Badge status={statusConfig[node.status]?.badge} />
                            <Text strong>{node.name}</Text>
                            <Tag>{edge.qps} qps</Tag>
                            {edge.error_rate > 0 && <Tag color="red">{edge.error_rate}% errors</Tag>}
                          </Space>
                        </Card>
                      ))}
                    </>
                  )}

                  {downstream.length > 0 && (
                    <>
                      <Typography.Title level={5}>Downstream ({selectedNode.name} calls)</Typography.Title>
                      {downstream.map(({ node, edge }) => node && (
                        <Card key={node.id} size="small" style={{ marginBottom: 8 }}>
                          <Space>
                            <Badge status={statusConfig[node.status]?.badge} />
                            <Text strong>{node.name}</Text>
                            <Tag>{edge.qps} qps</Tag>
                            {edge.error_rate > 0 && <Tag color="red">{edge.error_rate}% errors</Tag>}
                          </Space>
                        </Card>
                      ))}
                    </>
                  )}

                  {upstream.length === 0 && downstream.length === 0 && (
                    <Text type="secondary">No connections found</Text>
                  )}
                </>
              );
            })()}
          </>
        )}
      </Drawer>
    </div>
  );
}
