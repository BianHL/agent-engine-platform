'use client';
import React from 'react';
import { Skeleton, Card, Space, Row, Col } from 'antd';

interface SkeletonLoaderProps {
  type?: 'card' | 'list' | 'table' | 'form' | 'dashboard' | 'custom';
  count?: number;
  columns?: number;
  animate?: boolean;
}

export default function SkeletonLoader({
  type = 'card',
  count = 3,
  columns = 3,
  animate = true,
}: SkeletonLoaderProps) {
  const pulse = animate ? { active: true } : {};

  if (type === 'card') {
    return (
      <Row gutter={[16, 16]}>
        {Array.from({ length: count }).map((_, i) => (
          <Col key={i} xs={24} sm={12} lg={8} xl={6}>
            <Card>
              <Skeleton avatar={{ size: 'large' }} paragraph={{ rows: 3 }} {...pulse} />
            </Card>
          </Col>
        ))}
      </Row>
    );
  }

  if (type === 'list') {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {Array.from({ length: count }).map((_, i) => (
          <Card key={i} size="small">
            <Skeleton avatar paragraph={{ rows: 2 }} {...pulse} />
          </Card>
        ))}
      </Space>
    );
  }

  if (type === 'table') {
    return (
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          {/* Header */}
          <div style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
            {Array.from({ length: columns }).map((_, i) => (
              <Skeleton.Input key={i} size="small" style={{ width: `${100 / columns}%`, height: 20 }} {...pulse} />
            ))}
          </div>
          {/* Rows */}
          {Array.from({ length: count }).map((_, rowIndex) => (
            <div key={rowIndex} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <Skeleton.Input
                  key={colIndex}
                  size="small"
                  style={{
                    width: `${100 / columns}%`,
                    height: 16,
                    opacity: 1 - (rowIndex * 0.1),
                  }}
                  {...pulse}
                />
              ))}
            </div>
          ))}
        </Space>
      </Card>
    );
  }

  if (type === 'form') {
    return (
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {Array.from({ length: count }).map((_, i) => (
            <div key={i}>
              <Skeleton.Input size="small" style={{ width: 120, height: 14, marginBottom: 8 }} {...pulse} />
              <Skeleton.Input style={{ width: '100%', height: 32 }} {...pulse} />
            </div>
          ))}
          <Skeleton.Button style={{ width: 120 }} {...pulse} />
        </Space>
      </Card>
    );
  }

  if (type === 'dashboard') {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Stats Row */}
        <Row gutter={[16, 16]}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Col key={i} xs={24} sm={12} lg={6}>
              <Card>
                <Skeleton.Input size="small" style={{ width: 100, height: 14, marginBottom: 8 }} {...pulse} />
                <Skeleton.Input style={{ width: 150, height: 32 }} {...pulse} />
              </Card>
            </Col>
          ))}
        </Row>

        {/* Charts Row */}
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card>
              <Skeleton.Input size="small" style={{ width: 150, height: 14, marginBottom: 16 }} {...pulse} />
              <div style={{ height: 200, background: '#f5f5f5', borderRadius: 8 }}>
                <Skeleton.Image style={{ width: '100%', height: '100%' }} {...pulse} />
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card>
              <Skeleton.Input size="small" style={{ width: 150, height: 14, marginBottom: 16 }} {...pulse} />
              <div style={{ height: 200, background: '#f5f5f5', borderRadius: 8 }}>
                <Skeleton.Image style={{ width: '100%', height: '100%' }} {...pulse} />
              </div>
            </Card>
          </Col>
        </Row>
      </Space>
    );
  }

  // Custom skeleton
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} paragraph={{ rows: 2 }} {...pulse} />
      ))}
    </Space>
  );
}

// Specific skeleton loaders for common patterns
export function AgentCardSkeleton() {
  return (
    <Row gutter={[16, 16]}>
      {Array.from({ length: 8 }).map((_, i) => (
        <Col key={i} xs={24} sm={12} lg={8} xl={6}>
          <Card hoverable>
            <Skeleton avatar={{ size: 'large', shape: 'square' }} paragraph={{ rows: 2 }} active />
            <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
              <Skeleton.Button size="small" active />
              <Skeleton.Button size="small" active />
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  );
}

export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return <SkeletonLoader type="table" count={rows} columns={columns} />;
}

export function FormSkeleton({ fields = 4 }: { fields?: number }) {
  return <SkeletonLoader type="form" count={fields} />;
}

export function DashboardSkeleton() {
  return <SkeletonLoader type="dashboard" />;
}
