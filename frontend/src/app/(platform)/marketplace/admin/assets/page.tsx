'use client';
import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Typography, Space, message, Modal, Input, Select, Popconfirm } from 'antd';
import { LockOutlined, UnlockOutlined, ArrowDownOutlined, StarOutlined, StarFilled } from '@ant-design/icons';
import api from '@/lib/api';
import { MarketplaceItem } from '@/types/marketplace';

const { Title } = Typography;
const { TextArea } = Input;

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  pending_review: { color: 'processing', text: '审核中' },
  approved: { color: 'success', text: '已通过' },
  published: { color: 'success', text: '已发布' },
  rejected: { color: 'error', text: '已驳回' },
  frozen: { color: 'warning', text: '已冻结' },
  takedown: { color: 'error', text: '已下架' },
};

export default function AdminAssetsPage() {
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [keyword, setKeyword] = useState('');
  const [reasonModalOpen, setReasonModalOpen] = useState(false);
  const [reasonAction, setReasonAction] = useState('');
  const [reasonItemId, setReasonItemId] = useState('');
  const [reason, setReason] = useState('');

  useEffect(() => {
    loadItems();
  }, [page, statusFilter]);

  const loadItems = async () => {
    setLoading(true);
    try {
      const data = await api.listAdminItems({
        status: statusFilter,
        keyword,
        page,
        size: 20,
      });
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFreeze = async () => {
    try {
      await api.freezeItem(reasonItemId, reason);
      message.success('已冻结');
      setReasonModalOpen(false);
      setReason('');
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const handleTakedown = async () => {
    try {
      await api.takedownItem(reasonItemId, reason);
      message.success('已下架');
      setReasonModalOpen(false);
      setReason('');
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const handleUnfreeze = async (id: string) => {
    try {
      await api.unfreezeItem(id);
      message.success('已解冻');
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const handleToggleFeatured = async (id: string, featured: boolean) => {
    try {
      if (featured) {
        await api.setFeatured(id);
        message.success('已设为精选');
      } else {
        await api.unsetFeatured(id);
        message.success('已取消精选');
      }
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const handlePromote = async (id: string, level: string) => {
    try {
      await api.promoteItem(id, level);
      message.success('提级成功');
      loadItems();
    } catch {
      message.error('操作失败');
    }
  };

  const openReasonModal = (action: string, id: string) => {
    setReasonAction(action);
    setReasonItemId(id);
    setReasonModalOpen(true);
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
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
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const s = STATUS_MAP[status] || { color: 'default', text: status };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: '评分',
      key: 'rating',
      render: (_: any, r: MarketplaceItem) => r.rating_count > 0 ? `${r.avg_rating} (${r.rating_count})` : '-',
    },
    { title: '使用', dataIndex: 'usage_count', key: 'usage_count' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MarketplaceItem) => (
        <Space wrap>
          {record.status === 'published' && (
            <Button size="small" icon={<LockOutlined />} onClick={() => openReasonModal('freeze', record.id)}>
              冻结
            </Button>
          )}
          {record.status === 'frozen' && (
            <Popconfirm title="确定解冻？" onConfirm={() => handleUnfreeze(record.id)}>
              <Button size="small" icon={<UnlockOutlined />}>解冻</Button>
            </Popconfirm>
          )}
          {(record.status === 'published' || record.status === 'frozen') && (
            <Button size="small" danger icon={<ArrowDownOutlined />} onClick={() => openReasonModal('takedown', record.id)}>
              下架
            </Button>
          )}
          <Select
            size="small"
            placeholder="提级"
            style={{ width: 90 }}
            onChange={(v) => handlePromote(record.id, v)}
            value={record.promoted_level || undefined}
          >
            <Select.Option value="department">部门级</Select.Option>
            <Select.Option value="tenant">单位级</Select.Option>
            <Select.Option value="group">集团级</Select.Option>
          </Select>
          <Button
            size="small"
            icon={record.featured ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
            onClick={() => handleToggleFeatured(record.id, !record.featured)}
          >
            {record.featured ? '取消精选' : '设为精选'}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>资产管控</Title>
        <Space>
          <Input.Search
            placeholder="搜索资产"
            onSearch={(v) => { setKeyword(v); setPage(1); loadItems(); }}
            style={{ width: 200 }}
          />
          <Select
            value={statusFilter}
            onChange={(v) => { setStatusFilter(v); setPage(1); }}
            style={{ width: 120 }}
            allowClear
            placeholder="状态筛选"
          >
            {Object.entries(STATUS_MAP).map(([k, v]) => (
              <Select.Option key={k} value={k}>{v.text}</Select.Option>
            ))}
          </Select>
        </Space>
      </div>

      <Card>
        <Table
          dataSource={items}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            current: page,
            total,
            pageSize: 20,
            onChange: setPage,
          }}
        />
      </Card>

      <Modal
        title={reasonAction === 'freeze' ? '冻结原因' : '下架原因'}
        open={reasonModalOpen}
        onOk={reasonAction === 'freeze' ? handleFreeze : handleTakedown}
        onCancel={() => setReasonModalOpen(false)}
        okText="确认"
        cancelText="取消"
      >
        <TextArea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="请输入原因"
          rows={4}
        />
      </Modal>
    </div>
  );
}
