'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Typography, Button, Space, Select, message, Row, Col,
  Statistic, Progress, Table, Descriptions, Spin, Empty,
} from 'antd';
import {
  SafetyOutlined, ReloadOutlined, WarningOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';

const { Title, Text } = Typography;

interface ComplianceScore {
  overall_score: number;
  factors: Record<string, number>;
  grade: string;
  recommendations: string[];
}

export default function CompliancePage() {
  const [score, setScore] = useState<ComplianceScore | null>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState('audit');
  const [days, setDays] = useState(30);

  const fetchScore = useCallback(async () => {
    try {
      const res = await api.get('/compliance/score');
      setScore(res);
    } catch { message.error('Failed to load compliance score'); }
  }, []);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/compliance/reports/${reportType}`, { params: { days } });
      setReport(res);
    } catch { message.error('Failed to load report'); } finally { setLoading(false); }
  }, [reportType, days]);

  useEffect(() => { fetchScore(); }, []);
  useEffect(() => { fetchReport(); }, [reportType, days]);

  const getScoreColor = (s: number) => s >= 0.9 ? '#52c41a' : s >= 0.8 ? '#1890ff' : s >= 0.7 ? '#faad14' : '#ff4d4f';
  const factorLabels: Record<string, string> = {
    authentication: 'Authentication', authorization: 'Authorization',
    data_protection: 'Data Protection', audit_logging: 'Audit Logging', access_control: 'Access Control',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={4}>Compliance Dashboard</Title>
        <Space>
          <Select value={reportType} onChange={setReportType} options={[
            { value: 'security', label: 'Security' }, { value: 'access', label: 'Access Control' },
            { value: 'data', label: 'Data Handling' }, { value: 'audit', label: 'Audit Trail' },
          ]} />
          <Select value={days} onChange={setDays} options={[
            { value: 7, label: 'Last 7 days' }, { value: 30, label: 'Last 30 days' }, { value: 90, label: 'Last 90 days' },
          ]} />
          <Button icon={<ReloadOutlined />} onClick={() => { fetchScore(); fetchReport(); }}>Refresh</Button>
        </Space>
      </div>

      {score && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} md={8}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <Progress type="dashboard" percent={Math.round(score.overall_score * 100)}
                  format={() => <div><div style={{ fontSize: 36, fontWeight: 'bold', color: getScoreColor(score.overall_score) }}>{score.grade}</div><div style={{ fontSize: 14 }}>{Math.round(score.overall_score * 100)}%</div></div>}
                  strokeColor={getScoreColor(score.overall_score)} />
                <Title level={5} style={{ marginTop: 16 }}>Overall Compliance Score</Title>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={16}>
            <Card title="Compliance Factors">
              <Row gutter={[16, 16]}>
                {Object.entries(score.factors).map(([factor, value]) => (
                  <Col key={factor} xs={12} sm={8}>
                    <div style={{ textAlign: 'center' }}>
                      <Progress type="circle" percent={Math.round(value * 100)} size={80} strokeColor={getScoreColor(value)} />
                      <div style={{ marginTop: 8, fontSize: 12 }}>{factorLabels[factor] || factor}</div>
                    </div>
                  </Col>
                ))}
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      {score?.recommendations && score.recommendations.length > 0 && (
        <Card title="Recommendations" style={{ marginBottom: 24 }}>
          {score.recommendations.map((rec, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <WarningOutlined style={{ color: '#faad14' }} /><Text>{rec}</Text>
            </div>
          ))}
        </Card>
      )}

      <Card title={`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report`}>
        {loading ? <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
        : report ? (
          <div>
            <Descriptions bordered column={{ xs: 1, sm: 2 }} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Report ID">{report.report_id}</Descriptions.Item>
              <Descriptions.Item label="Generated">{new Date(report.generated_at).toLocaleString()}</Descriptions.Item>
            </Descriptions>
            <Row gutter={[16, 16]}>
              {Object.entries(report.summary || {}).map(([key, value]) => (
                <Col key={key} xs={12} sm={8} md={6}>
                  <Card size="small">
                    <Statistic title={key.replace(/_/g, ' ')} value={typeof value === 'number' ? value : String(value)} />
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        ) : <Empty description="No report data" />}
      </Card>
    </div>
  );
}
