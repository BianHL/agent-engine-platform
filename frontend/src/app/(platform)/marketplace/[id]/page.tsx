'use client';
import React, { useEffect, useState } from 'react';
import { Card, Button, Tag, Typography, Spin, Space, Rate, Tabs, Descriptions, message, Modal, Input, List, Avatar, Row, Col, Statistic } from 'antd';
import { CopyOutlined, PlayCircleOutlined, StarOutlined, ArrowLeftOutlined, UserOutlined } from '@ant-design/icons';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { MarketplaceItem, MarketplaceRating } from '@/types/marketplace';
import WhiteBoxView from '@/components/marketplace/WhiteBoxView';
import MarkdownRenderer from '@/components/MarkdownRenderer';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const ASSET_TYPE_LABELS: Record<string, string> = {
  agent: '智能体',
  knowledge_base: '知识库',
  workflow: '工作流',
};

export default function MarketplaceItemDetailPage() {
  const router = useRouter();
  const params = useParams();
  const itemId = params.id as string;

  const [item, setItem] = useState<MarketplaceItem | null>(null);
  const [ratings, setRatings] = useState<MarketplaceRating[]>([]);
  const [myRating, setMyRating] = useState<{ score: number; comment?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [ratingModalOpen, setRatingModalOpen] = useState(false);
  const [ratingScore, setRatingScore] = useState(5);
  const [ratingComment, setRatingComment] = useState('');
  const [cloning, setCloning] = useState(false);

  useEffect(() => {
    if (itemId) {
      loadItem();
      loadRatings();
    }
  }, [itemId]);

  const loadItem = async () => {
    try {
      const data = await api.getMarketplaceItem(itemId);
      setItem(data);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const loadRatings = async () => {
    try {
      const [ratingsData, myRatingData] = await Promise.all([
        api.getItemRatings(itemId, 1, 20),
        api.getMyRating(itemId).catch(() => null),
      ]);
      setRatings(ratingsData.items || []);
      if (myRatingData) {
        setMyRating(myRatingData);
        setRatingScore(myRatingData.score);
        setRatingComment(myRatingData.comment || '');
      }
    } catch {
      // ignore
    }
  };

  const handleTrial = async () => {
    try {
      const result = await api.createTrial(itemId);
      message.success('试用已启动');
      if (result.asset_type === 'agent') {
        router.push(`/agents/${result.asset_id}/chat`);
      }
    } catch {
      message.error('试用失败');
    }
  };

  const handleClone = async () => {
    setCloning(true);
    try {
      await api.cloneItem(itemId);
      message.success('克隆成功！已创建副本，可在列表中查看');
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '克隆失败');
    } finally {
      setCloning(false);
    }
  };

  const handleSubmitRating = async () => {
    try {
      await api.createRating(itemId, { score: ratingScore, comment: ratingComment });
      message.success('评价成功');
      setRatingModalOpen(false);
      loadRatings();
      loadItem();
    } catch {
      message.error('评价失败');
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!item) return <div>资产不存在</div>;

  return (
    <div style={{ padding: '0 4px' }}>
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={() => router.push('/marketplace')}
        style={{ marginBottom: 16 }}
      >
        返回市集
      </Button>

      <Card style={{ marginBottom: 24 }}>
        <Row gutter={24}>
          <Col flex="auto">
            <Space wrap style={{ marginBottom: 8 }}>
              <Tag color="blue">{ASSET_TYPE_LABELS[item.asset_type] || item.asset_type}</Tag>
              {item.category && <Tag>{item.category}</Tag>}
              {item.featured && <Tag color="green">精选</Tag>}
              {item.promoted_level === 'group' && <Tag color="gold">集团级</Tag>}
              {item.status === 'frozen' && <Tag color="red">已冻结</Tag>}
            </Space>
            <Title level={3} style={{ marginBottom: 8 }}>{item.title}</Title>
            <Paragraph type="secondary">{item.summary}</Paragraph>
            <Space size="large">
              <Statistic title="评分" value={item.avg_rating} suffix={`/ 5 (${item.rating_count}评)`} />
              <Statistic title="使用次数" value={item.usage_count} />
              <Statistic title="克隆次数" value={item.clone_count} />
            </Space>
          </Col>
          <Col>
            <Space direction="vertical" size="middle">
              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleTrial}
                disabled={item.status !== 'published' && item.status !== 'approved'}
              >
                立即试用
              </Button>
              <Button
                size="large"
                icon={<CopyOutlined />}
                onClick={handleClone}
                loading={cloning}
                disabled={item.status !== 'published' && item.status !== 'approved'}
              >
                克隆到我的
              </Button>
              <Button
                size="large"
                icon={<StarOutlined />}
                onClick={() => setRatingModalOpen(true)}
              >
                {myRating ? '修改评价' : '我要评价'}
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Tabs
          items={[
            {
              key: 'detail',
              label: '详情介绍',
              children: (
                <div style={{ minHeight: 200 }}>
                  {item.description ? (
                    <MarkdownRenderer content={item.description} />
                  ) : (
                    <Paragraph type="secondary">暂无详细介绍</Paragraph>
                  )}
                </div>
              ),
            },
            {
              key: 'whitebox',
              label: '编排逻辑',
              children: <WhiteBoxView item={item} />,
            },
            {
              key: 'ratings',
              label: `评价 (${item.rating_count})`,
              children: (
                <div style={{ minHeight: 200 }}>
                  {ratings.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <Paragraph type="secondary">暂无评价</Paragraph>
                      <Button type="primary" onClick={() => setRatingModalOpen(true)}>
                        成为第一个评价者
                      </Button>
                    </div>
                  ) : (
                    <List
                      dataSource={ratings}
                      renderItem={(rating) => (
                        <List.Item>
                          <List.Item.Meta
                            avatar={<Avatar icon={<UserOutlined />} />}
                            title={
                              <Space>
                                <Text>{rating.user_name || '匿名用户'}</Text>
                                <Rate disabled value={rating.score} style={{ fontSize: 12 }} />
                              </Space>
                            }
                            description={
                              <>
                                {rating.comment && <Paragraph>{rating.comment}</Paragraph>}
                                <Text type="secondary" style={{ fontSize: 12 }}>{rating.created_at}</Text>
                              </>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title={myRating ? '修改评价' : '评价资产'}
        open={ratingModalOpen}
        onOk={handleSubmitRating}
        onCancel={() => setRatingModalOpen(false)}
        okText="提交"
        cancelText="取消"
      >
        <div style={{ textAlign: 'center', margin: '16px 0' }}>
          <Rate value={ratingScore} onChange={setRatingScore} style={{ fontSize: 36 }} />
        </div>
        <TextArea
          value={ratingComment}
          onChange={(e) => setRatingComment(e.target.value)}
          placeholder="写下你的评价（可选）"
          rows={4}
        />
      </Modal>
    </div>
  );
}
