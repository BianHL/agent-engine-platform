'use client';
import React, { useEffect, useState } from 'react';
import { Rate, List, Avatar, Typography, Space, Button, Input, message, Empty, Spin, Pagination } from 'antd';
import { UserOutlined, StarFilled } from '@ant-design/icons';
import api from '@/lib/api';
import type { ToolMarketplaceRating } from '@/types/marketplace';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ToolRatingProps {
  toolId: string;
  avgRating: number;
  ratingCount: number;
  onRatingSubmitted?: () => void;
}

export default function ToolRating({ toolId, avgRating, ratingCount, onRatingSubmitted }: ToolRatingProps) {
  const [ratings, setRatings] = useState<ToolMarketplaceRating[]>([]);
  const [myRating, setMyRating] = useState<{ score: number; comment?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [score, setScore] = useState(5);
  const [comment, setComment] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadRatings();
  }, [toolId, page]);

  const loadRatings = async () => {
    setLoading(true);
    try {
      const [ratingsData, myRatingData] = await Promise.all([
        api.getItemRatings(toolId, page, 10),
        api.getMyRating(toolId).catch(() => null),
      ]);
      setRatings(ratingsData.items || []);
      setTotal(ratingsData.total || 0);
      if (myRatingData) {
        setMyRating(myRatingData);
        setScore(myRatingData.score);
        setComment(myRatingData.comment || '');
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await api.createRating(toolId, { score, comment });
      message.success(myRating ? 'Rating updated' : 'Rating submitted');
      setShowForm(false);
      loadRatings();
      onRatingSubmitted?.();
    } catch {
      message.error('Failed to submit rating');
    } finally {
      setSubmitting(false);
    }
  };

  const ratingDistribution = [5, 4, 3, 2, 1].map((star) => {
    const count = ratings.filter((r) => r.score === star).length;
    return { star, count, pct: ratingCount > 0 ? (count / ratingCount) * 100 : 0 };
  });

  return (
    <div>
      {/* Summary */}
      <div style={{ display: 'flex', gap: 32, marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{ textAlign: 'center', minWidth: 120 }}>
          <div style={{ fontSize: 36, fontWeight: 700, lineHeight: 1 }}>{avgRating.toFixed(1)}</div>
          <Rate disabled value={avgRating} allowHalf style={{ fontSize: 14, margin: '8px 0' }} />
          <div><Text type="secondary">{ratingCount} ratings</Text></div>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          {ratingDistribution.map(({ star, pct }) => (
            <div key={star} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Text style={{ width: 16, textAlign: 'right' }}>{star}</Text>
              <StarFilled style={{ fontSize: 12, color: '#faad14' }} />
              <div style={{ flex: 1, height: 8, background: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: '#faad14', borderRadius: 4 }} />
              </div>
            </div>
          ))}
        </div>
        <div>
          <Button type="primary" onClick={() => setShowForm(!showForm)}>
            {myRating ? 'Edit Rating' : 'Rate This Tool'}
          </Button>
        </div>
      </div>

      {/* Rating Form */}
      {showForm && (
        <div style={{ background: '#fafafa', padding: 16, borderRadius: 8, marginBottom: 24 }}>
          <div style={{ textAlign: 'center', marginBottom: 12 }}>
            <Rate value={score} onChange={setScore} style={{ fontSize: 32 }} />
          </div>
          <TextArea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Share your experience with this tool (optional)"
            rows={3}
            style={{ marginBottom: 12 }}
          />
          <Space>
            <Button type="primary" loading={submitting} onClick={handleSubmit}>
              Submit
            </Button>
            <Button onClick={() => setShowForm(false)}>Cancel</Button>
          </Space>
        </div>
      )}

      {/* Ratings List */}
      {loading ? (
        <Spin style={{ display: 'block', margin: '40px auto' }} />
      ) : ratings.length === 0 ? (
        <Empty description="No ratings yet" />
      ) : (
        <>
          <List
            dataSource={ratings}
            renderItem={(rating) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar icon={<UserOutlined />} />}
                  title={
                    <Space>
                      <Text>{rating.user_name || 'Anonymous'}</Text>
                      <Rate disabled value={rating.score} style={{ fontSize: 12 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>{rating.created_at}</Text>
                    </Space>
                  }
                  description={rating.comment && <Paragraph style={{ marginBottom: 0 }}>{rating.comment}</Paragraph>}
                />
              </List.Item>
            )}
          />
          {total > 10 && (
            <Pagination
              current={page}
              total={total}
              pageSize={10}
              onChange={setPage}
              style={{ textAlign: 'center', marginTop: 16 }}
              size="small"
            />
          )}
        </>
      )}
    </div>
  );
}
