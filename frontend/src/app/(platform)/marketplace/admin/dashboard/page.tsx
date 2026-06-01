'use client';
import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Spin, Table, Tag } from 'antd';
import {
  ShopOutlined,
  StarOutlined,
  FireOutlined,
  CopyOutlined,
  BarChartOutlined,
  BankOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';
import { MarketplaceStats } from '@/types/marketplace';

const { Title } = Typography;

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.getMarketplaceStats();
      setStats(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!stats) return <div>加载失败</div>;

  const categoryData = Object.entries(stats.items_by_category).map(([name, count]) => ({
    name,
    count,
  }));

  const statusData = Object.entries(stats.items_by_status).map(([name, count]) => ({
    name,
    count,
  }));

  const tenantData = Object.entries(stats.items_by_tenant || {}).map(([name, count]) => ({
    name,
    count,
  }));

  return (
    <div>
      <Title level={4}>
        <BarChartOutlined style={{ marginRight: 8 }} />
        市集运营看板
      </Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总资产数"
              value={stats.total_items}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已发布"
              value={stats.published_items}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待审核"
              value={stats.pending_review_items}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均评分"
              value={stats.avg_rating}
              suffix="/ 5"
              prefix={<StarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总使用次数"
              value={stats.total_usage}
              prefix={<FireOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总评价数"
              value={stats.total_ratings}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总克隆次数"
              value={stats.total_clones}
              prefix={<CopyOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="覆盖组织"
              value={stats.covered_organizations ?? 0}
              prefix={<BankOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="覆盖用户"
              value={(stats as any).covered_users ?? 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card title="按分类统计">
            <Table
              dataSource={categoryData}
              columns={[
                { title: '分类', dataIndex: 'name', key: 'name' },
                { title: '数量', dataIndex: 'count', key: 'count' },
              ]}
              rowKey="name"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="按状态统计">
            <Table
              dataSource={statusData}
              columns={[
                {
                  title: '状态',
                  dataIndex: 'name',
                  key: 'name',
                  render: (s: string) => {
                    const map: Record<string, { color: string; text: string }> = {
                      draft: { color: 'default', text: '草稿' },
                      pending_review: { color: 'processing', text: '审核中' },
                      published: { color: 'success', text: '已发布' },
                      rejected: { color: 'error', text: '已驳回' },
                      frozen: { color: 'warning', text: '已冻结' },
                      takedown: { color: 'error', text: '已下架' },
                    };
                    const info = map[s] || { color: 'default', text: s };
                    return <Tag color={info.color}>{info.text}</Tag>;
                  },
                },
                { title: '数量', dataIndex: 'count', key: 'count' },
              ]}
              rowKey="name"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {tenantData.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24}>
            <Card title="按租户资产分布">
              <Table
                dataSource={tenantData}
                columns={[
                  { title: '租户名称', dataIndex: 'name', key: 'name' },
                  { title: '资产数量', dataIndex: 'count', key: 'count' },
                ]}
                rowKey="name"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
}
