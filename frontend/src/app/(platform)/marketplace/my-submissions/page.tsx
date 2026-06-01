'use client';
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Space, message, Popconfirm } from 'antd';
import { ArrowLeftOutlined, PlusOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { MarketplaceItem } from '@/types/marketplace';

const { Title } = Typography;

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  pending_review: { color: 'processing', text: '审核中' },
  approved: { color: 'success', text: '已通过' },
  published: { color: 'success', text: '已发布' },
  rejected: { color: 'error', text: '已驳回' },
  frozen: { color: 'warning', text: '已冻结' },
  takedown: { color: 'error', text: '已下架' },
};

export default function MySubmissionsPage() {
  const router = useRouter();
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadItems();
  }, [page]);

  const loadItems = async () => {
    setLoading(true);
    try {
      const data = await api.getMySubmissions(page, 20);
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await api.cancelSubmission(id);
      message.success('已撤回');
      loadItems();
    } catch {
      message.error('撤回失败');
    }
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const s = STATUS_MAP[status] || { color: 'default', text: status };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    { title: '分类', dataIndex: 'category', key: 'category' },
    {
      title: '评分',
      key: 'rating',
      render: (_: any, record: MarketplaceItem) =>
        record.rating_count > 0 ? `${record.avg_rating} (${record.rating_count}评)` : '-',
    },
    { title: '使用次数', dataIndex: 'usage_count', key: 'usage_count' },
    { title: '提交时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MarketplaceItem) => (
        <Space>
          {record.status === 'pending_review' && (
            <Popconfirm title="确定撤回？" onConfirm={() => handleCancel(record.id)}>
              <Button size="small">撤回</Button>
            </Popconfirm>
          )}
          {record.status === 'rejected' && record.reject_reason && (
            <Button size="small" onClick={() => message.info(`驳回原因: ${record.reject_reason}`)}>
              查看原因
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '0 4px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => router.push('/marketplace')}
          >
            返回市集
          </Button>
          <Title level={4} style={{ margin: 0 }}>我的提交</Title>
        </Space>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => router.push('/marketplace/submit')}
        >
          申请上架
        </Button>
      </div>

      <Card>
        <Table
          dataSource={items}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            total,
            pageSize: 20,
            onChange: setPage,
          }}
        />
      </Card>
    </div>
  );
}
