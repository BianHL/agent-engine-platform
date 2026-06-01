'use client';
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Space, message, Modal, Input, Tabs } from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import api from '@/lib/api';

const { Title } = Typography;
const { TextArea } = Input;

function ReviewTable({
  loadFn,
  approveLabel = '通过',
  rejectLabel = '驳回',
}: {
  loadFn: (page: number, size: number) => Promise<any>;
  approveLabel?: string;
  rejectLabel?: string;
}) {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectItemId, setRejectItemId] = useState('');
  const [rejectComment, setRejectComment] = useState('');

  useEffect(() => {
    loadItems();
  }, [page]);

  const loadItems = async () => {
    setLoading(true);
    try {
      const data = await loadFn(page, 20);
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const result = await api.approveReview(id);
      message.success(result.message || '审核通过');
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const handleReject = async () => {
    try {
      await api.rejectReview(rejectItemId, rejectComment);
      message.success('已驳回');
      setRejectModalOpen(false);
      setRejectComment('');
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    {
      title: '类型',
      dataIndex: 'asset_type',
      key: 'asset_type',
      render: (t: string) => {
        const map: Record<string, string> = { agent: '智能体', knowledge_base: '知识库', workflow: '工作流' };
        return <Tag>{map[t] || t}</Tag>;
      },
    },
    { title: '分类', dataIndex: 'category', key: 'category' },
    { title: '创建者', dataIndex: 'creator_id', key: 'creator_id' },
    { title: '提交时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleApprove(record.id)}
          >
            {approveLabel}
          </Button>
          <Button
            danger
            size="small"
            icon={<CloseOutlined />}
            onClick={() => {
              setRejectItemId(record.id);
              setRejectModalOpen(true);
            }}
          >
            {rejectLabel}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
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

      <Modal
        title="驳回原因"
        open={rejectModalOpen}
        onOk={handleReject}
        onCancel={() => setRejectModalOpen(false)}
        okText="确认驳回"
        cancelText="取消"
      >
        <TextArea
          value={rejectComment}
          onChange={(e) => setRejectComment(e.target.value)}
          placeholder="请输入驳回原因，将展示给提交者"
          rows={4}
        />
      </Modal>
    </>
  );
}

export default function AdminReviewsPage() {
  const tabItems = [
    {
      key: 'pending',
      label: '待审核',
      children: (
        <ReviewTable
          loadFn={(page, size) => api.listPendingReviews(page, size)}
        />
      ),
    },
    {
      key: 'promotion',
      label: '待复核',
      children: (
        <ReviewTable
          loadFn={(page, size) => api.listPendingPromotionReviews(page, size)}
          approveLabel="复核通过"
          rejectLabel="驳回"
        />
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>审核中心</Title>
      <Card>
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
}
