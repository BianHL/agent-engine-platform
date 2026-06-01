'use client';
import React, { useState, useCallback, useEffect } from 'react';
import {
  Card, Typography, Row, Col, Space, Button, Tabs, message, Tag, Modal,
  Select, Statistic, Progress, Tooltip, Dropdown, Empty, Spin, Popconfirm,
} from 'antd';
import {
  ExperimentOutlined, BarChartOutlined, SwapOutlined, DownloadOutlined,
  PlayCircleOutlined, HistoryOutlined, DeleteOutlined, FileTextOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined, SettingOutlined,
} from '@ant-design/icons';
import api from '@/lib/api';
import EvalConfigPanel, { type EvalConfig } from '@/components/evaluations/EvalConfigPanel';
import EvalResultChart, { type MetricData } from '@/components/evaluations/EvalResultChart';
import EvalComparison, { type ComparisonRun } from '@/components/evaluations/EvalComparison';
import EvalMetricsTable, { type MetricRow } from '@/components/evaluations/EvalMetricsTable';
import TestQuestionEditor, { type TestQuestion } from '@/components/evaluations/TestQuestionEditor';

const { Title, Text, Paragraph } = Typography;

interface EvalRun {
  id: string;
  name: string;
  evaluation_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  summary?: {
    metric_averages?: Record<string, number>;
    total_cases?: number;
    error?: string;
  };
  created_at: string;
  completed_at?: string;
}

interface EvalResultItem {
  id: string;
  test_case_index: number;
  input_text: string;
  expected_output: string;
  actual_output: string;
  scores: Record<string, number>;
  latency_ms: number;
}

export default function EvalPlaygroundPage() {
  // State
  const [questions, setQuestions] = useState<TestQuestion[]>([]);
  const [running, setRunning] = useState(false);
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
  const [currentResults, setCurrentResults] = useState<EvalResultItem[] | null>(null);
  const [currentRun, setCurrentRun] = useState<EvalRun | null>(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [chartType, setChartType] = useState<'radar' | 'bar' | 'gauge'>('radar');
  const [activeTab, setActiveTab] = useState('config');
  const [pollingId, setPollingId] = useState<string | null>(null);

  // Load existing runs
  const fetchRuns = useCallback(async () => {
    try {
      const data: any = await api.get('/evaluations');
      const items = data?.items || data || [];
      setRuns(items);
    } catch {
      // silent
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  // Poll for running evaluation
  useEffect(() => {
    if (!pollingId) return;
    const interval = setInterval(async () => {
      try {
        const runData = await api.get<any>(`/evaluations/${pollingId}/runs`);
        const runs = Array.isArray(runData) ? runData : [];
        const latestRun = runs[0];
        if (latestRun && (latestRun.status === 'completed' || latestRun.status === 'failed')) {
          clearInterval(interval);
          setPollingId(null);
          setRunning(false);
          if (latestRun.status === 'completed') {
            message.success('Evaluation completed!');
            fetchRuns();
            // Load results
            handleViewResults(latestRun);
          } else {
            message.error(`Evaluation failed: ${latestRun.summary?.error || 'Unknown error'}`);
          }
        }
      } catch {
        // continue polling
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [pollingId, fetchRuns]);

  // Run evaluation
  const handleRun = async (config: EvalConfig) => {
    if (questions.length === 0) {
      message.warning('Please add at least one test question');
      setActiveTab('questions');
      return;
    }

    setRunning(true);
    try {
      // Create evaluation
      const evalData = await api.post('/evaluations', {
        name: config.run_name,
        agent_id: config.agent_id,
        dataset: questions.map(q => ({
          question: q.question,
          ground_truth: q.ground_truth,
          contexts: q.contexts || [],
          answer: q.answer || '',
        })),
        metrics: config.metrics,
      });

      // Start run
      const runData = await api.post(`/evaluations/${evalData.id}/run`);
      message.info('Evaluation started...');
      setPollingId(evalData.id);
      setActiveTab('results');
    } catch (err: any) {
      message.error(`Failed to start evaluation: ${err?.response?.data?.detail || err.message}`);
      setRunning(false);
    }
  };

  // View results for a run
  const handleViewResults = async (run: EvalRun) => {
    try {
      setCurrentRun(run);
      const data = await api.get<any>(`/evaluations/runs/${run.id}/results`);
      const results = data?.results || data || [];
      setCurrentResults(results);
      setActiveTab('results');
    } catch {
      message.error('Failed to load results');
    }
  };

  // Delete a run
  const handleDeleteRun = async (id: string) => {
    try {
      await api.delete(`/evaluations/${id}`);
      message.success('Run deleted');
      fetchRuns();
      if (currentRun?.id === id) {
        setCurrentRun(null);
        setCurrentResults(null);
      }
    } catch {
      message.error('Failed to delete run');
    }
  };

  // Toggle run selection for comparison
  const toggleRunSelection = (id: string) => {
    setSelectedRuns(prev =>
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  // Get metric data for chart
  const getMetricData = (run: EvalRun | null): MetricData[] => {
    if (!run?.summary?.metric_averages) return [];
    return Object.entries(run.summary.metric_averages).map(([name, value]) => ({
      name,
      value,
    }));
  };

  // Get metrics for table
  const getMetricsTableData = (results: EvalResultItem[]): MetricRow[] => {
    if (!results || results.length === 0) return [];
    const metricNames = Object.keys(results[0].scores || {});
    return metricNames.map(name => {
      const scores = results.map(r => r.scores[name] || 0);
      return {
        metric: name,
        score: scores.reduce((a, b) => a + b, 0) / scores.length,
        min: Math.min(...scores),
        max: Math.max(...scores),
        count: scores.length,
      };
    });
  };

  // Get comparison data
  const getComparisonData = (): ComparisonRun[] => {
    return selectedRuns
      .map(id => runs.find(r => r.id === id))
      .filter(Boolean)
      .map(run => ({
        id: run!.id,
        name: run!.name || `Run ${run!.id.slice(0, 8)}`,
        metrics: run!.summary?.metric_averages || {},
        created_at: run!.created_at,
      }));
  };

  // Export report
  const handleExport = () => {
    if (!currentRun || !currentResults) {
      message.warning('No results to export');
      return;
    }

    const report = {
      run: {
        id: currentRun.id,
        name: currentRun.name,
        status: currentRun.status,
        created_at: currentRun.created_at,
        completed_at: currentRun.completed_at,
        summary: currentRun.summary,
      },
      results: currentResults,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eval-report-${currentRun.id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('Report exported');
  };

  const metricData = getMetricData(currentRun);
  const metricsTableData = currentResults ? getMetricsTableData(currentResults) : [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>
            <Space>
              <ExperimentOutlined />
              Evaluation Playground
            </Space>
          </Title>
          <Paragraph type="secondary" style={{ margin: '4px 0 0 0' }}>
            Configure, run, and analyze RAG evaluations with visual metrics
          </Paragraph>
        </div>
        <Space>
          {currentResults && (
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              Export Report
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={fetchRuns}>
            Refresh
          </Button>
        </Space>
      </div>

      {/* Stats Row */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Total Runs"
              value={runs.length}
              prefix={<ExperimentOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Completed"
              value={runs.filter(r => r.status === 'completed').length}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Test Questions"
              value={questions.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Avg Score"
              value={
                currentRun?.summary?.metric_averages
                  ? Object.values(currentRun.summary.metric_averages).reduce((a, b) => a + b, 0) /
                    Object.values(currentRun.summary.metric_averages).length * 100
                  : 0
              }
              suffix="%"
              precision={1}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'config',
            label: (
              <Space>
                <SettingOutlined />
                Configure & Run
              </Space>
            ),
            children: (
              <Row gutter={16}>
                <Col xs={24} lg={10}>
                  <EvalConfigPanel onRun={handleRun} running={running} />
                </Col>
                <Col xs={24} lg={14}>
                  <TestQuestionEditor value={questions} onChange={setQuestions} disabled={running} />
                </Col>
              </Row>
            ),
          },
          {
            key: 'results',
            label: (
              <Space>
                <BarChartOutlined />
                Results
                {running && <Tag color="processing">Running</Tag>}
              </Space>
            ),
            children: running ? (
              <Card>
                <div style={{ textAlign: 'center', padding: 60 }}>
                  <Spin size="large" />
                  <div style={{ marginTop: 16 }}>
                    <Text>Evaluation in progress...</Text>
                  </div>
                  <Progress percent={50} status="active" style={{ maxWidth: 400, margin: '16px auto' }} />
                </div>
              </Card>
            ) : currentResults && currentRun ? (
              <Space direction="vertical" style={{ width: '100%' }} size={16}>
                {/* Chart Type Toggle */}
                <Card size="small">
                  <Space>
                    <Text strong>Visualization:</Text>
                    <Button.Group>
                      <Button
                        type={chartType === 'radar' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => setChartType('radar')}
                      >
                        Radar
                      </Button>
                      <Button
                        type={chartType === 'bar' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => setChartType('bar')}
                      >
                        Bar
                      </Button>
                      <Button
                        type={chartType === 'gauge' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => setChartType('gauge')}
                      >
                        Gauge
                      </Button>
                    </Button.Group>
                    <Text type="secondary">
                      Run: {currentRun.name || currentRun.id.slice(0, 8)}
                    </Text>
                  </Space>
                </Card>

                <Row gutter={16}>
                  <Col xs={24} lg={12}>
                    <EvalResultChart
                      metrics={metricData}
                      title="Metric Overview"
                      type={chartType}
                      height={350}
                    />
                  </Col>
                  <Col xs={24} lg={12}>
                    <EvalMetricsTable metrics={metricsTableData} />
                  </Col>
                </Row>

                {/* Detailed Results */}
                <Card title="Test Case Results" size="small">
                  <Tabs
                    size="small"
                    items={currentResults.map((result, idx) => ({
                      key: result.id,
                      label: `Q${idx + 1} ${Object.values(result.scores).some(s => s >= 0.8) ? '✓' : Object.values(result.scores).some(s => s >= 0.6) ? '~' : '✗'}`,
                      children: (
                        <div>
                          <Row gutter={16}>
                            <Col span={12}>
                              <Card size="small" title="Question">
                                <Text>{result.input_text}</Text>
                              </Card>
                            </Col>
                            <Col span={12}>
                              <Card size="small" title="Expected Answer">
                                <Text>{result.expected_output || <Tag>Not specified</Tag>}</Text>
                              </Card>
                            </Col>
                          </Row>
                          <Card size="small" title="Actual Answer" style={{ marginTop: 12 }}>
                            <Text>{result.actual_output}</Text>
                          </Card>
                          <Card size="small" title="Scores" style={{ marginTop: 12 }}>
                            <Space wrap>
                              {Object.entries(result.scores).map(([metric, score]) => (
                                <Tag
                                  key={metric}
                                  color={score >= 0.8 ? 'success' : score >= 0.6 ? 'warning' : 'error'}
                                >
                                  {metric}: {(score * 100).toFixed(1)}%
                                </Tag>
                              ))}
                              {result.latency_ms > 0 && (
                                <Tag>Latency: {result.latency_ms}ms</Tag>
                              )}
                            </Space>
                          </Card>
                        </div>
                      ),
                    }))}
                  />
                </Card>
              </Space>
            ) : (
              <Card>
                <Empty description="Run an evaluation to see results" />
              </Card>
            ),
          },
          {
            key: 'compare',
            label: (
              <Space>
                <SwapOutlined />
                Compare
                {selectedRuns.length > 0 && <Tag>{selectedRuns.length}</Tag>}
              </Space>
            ),
            children: (
              <Row gutter={16}>
                <Col xs={24} lg={selectedRuns.length >= 2 ? 24 : 16}>
                  <EvalComparison runs={getComparisonData()} />
                </Col>
                <Col xs={24} lg={selectedRuns.length >= 2 ? 24 : 8}>
                  <Card title="Select Runs to Compare" size="small">
                    {runs.filter(r => r.status === 'completed').length === 0 ? (
                      <Empty description="No completed runs" />
                    ) : (
                      <Space direction="vertical" style={{ width: '100%' }}>
                        {runs
                          .filter(r => r.status === 'completed')
                          .map(run => (
                            <Card
                              key={run.id}
                              size="small"
                              hoverable
                              style={{
                                border: selectedRuns.includes(run.id) ? '2px solid #1890ff' : '1px solid #f0f0f0',
                                cursor: 'pointer',
                              }}
                              onClick={() => toggleRunSelection(run.id)}
                            >
                              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                                <Space>
                                  {selectedRuns.includes(run.id) && (
                                    <CheckCircleOutlined style={{ color: '#1890ff' }} />
                                  )}
                                  <div>
                                    <Text strong>{run.name || `Run ${run.id.slice(0, 8)}`}</Text>
                                    <br />
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                      {new Date(run.created_at).toLocaleString()}
                                    </Text>
                                  </div>
                                </Space>
                                <Space>
                                  {run.summary?.metric_averages && (
                                    <Tag color="blue">
                                      {(
                                        Object.values(run.summary.metric_averages).reduce((a, b) => a + b, 0) /
                                        Object.values(run.summary.metric_averages).length * 100
                                      ).toFixed(1)}% avg
                                    </Tag>
                                  )}
                                  <Button
                                    size="small"
                                    icon={<BarChartOutlined />}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleViewResults(run);
                                    }}
                                  >
                                    View
                                  </Button>
                                </Space>
                              </Space>
                            </Card>
                          ))}
                      </Space>
                    )}
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'history',
            label: (
              <Space>
                <HistoryOutlined />
                History
              </Space>
            ),
            children: (
              <Card>
                {loadingRuns ? (
                  <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
                ) : runs.length === 0 ? (
                  <Empty description="No evaluation runs yet" />
                ) : (
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    {runs.map(run => (
                      <Card key={run.id} size="small" hoverable>
                        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                          <Space>
                            <ExperimentOutlined />
                            <div>
                              <Text strong>{run.name || `Run ${run.id.slice(0, 8)}`}</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {new Date(run.created_at).toLocaleString()}
                              </Text>
                            </div>
                            <Tag color={
                              run.status === 'completed' ? 'success' :
                              run.status === 'running' ? 'processing' :
                              run.status === 'failed' ? 'error' : 'default'
                            }>
                              {run.status}
                            </Tag>
                          </Space>
                          <Space>
                            {run.summary?.metric_averages && (
                              <Tag color="blue">
                                {(
                                  Object.values(run.summary.metric_averages).reduce((a, b) => a + b, 0) /
                                  Object.values(run.summary.metric_averages).length * 100
                                ).toFixed(1)}% avg
                              </Tag>
                            )}
                            {run.status === 'completed' && (
                              <Button
                                size="small"
                                icon={<BarChartOutlined />}
                                onClick={() => handleViewResults(run)}
                              >
                                Results
                              </Button>
                            )}
                            <Button
                              size="small"
                              icon={<SwapOutlined />}
                              onClick={() => {
                                toggleRunSelection(run.id);
                                setActiveTab('compare');
                              }}
                            >
                              Compare
                            </Button>
                            <Popconfirm
                              title="Delete this run?"
                              onConfirm={() => handleDeleteRun(run.id)}
                            >
                              <Button size="small" danger icon={<DeleteOutlined />} />
                            </Popconfirm>
                          </Space>
                        </Space>
                      </Card>
                    ))}
                  </Space>
                )}
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
}
