'use client';
import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { Card, Row, Col, Typography, Spin, message, Tag } from 'antd';
import {
  ArrowUpOutlined, RobotOutlined, MessageOutlined,
  DollarOutlined, ThunderboltOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import api from '@/lib/api';
import { motion } from 'framer-motion';

const { Title, Text } = Typography;

interface UsageData {
  dates: string[];
  tokens: number[];
}

interface ModelCost {
  model: string;
  cost: number;
}

interface AgentActivity {
  agent_name: string;
  conversation_count: number;
}

interface FeedbackSummary {
  positive: number;
  negative: number;
}

// ─── Animated Counter ───
function AnimatedNumber({ value, formatter }: { value: number; formatter?: (n: number) => string }) {
  const [display, setDisplay] = useState('0');
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const duration = 800;
    const start = performance.now();
    const from = 0;
    const to = value;

    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4); // ease-out-quart
      const current = Math.round(from + (to - from) * eased);
      setDisplay(formatter ? formatter(current) : current.toLocaleString());
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [value, formatter]);

  return <span>{display}</span>;
}

// ─── Bento Metric Block ───
function MetricBlock({
  label,
  value,
  formatter,
  icon,
  accent,
  trend,
  large = false,
}: {
  label: string;
  value: number;
  formatter?: (n: number) => string;
  icon: React.ReactNode;
  accent: string;
  trend?: { value: number; positive: boolean };
  large?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
      className="flex flex-col justify-between h-full"
    >
      <div className="flex items-center gap-2 mb-3">
        <span
          className="inline-flex items-center justify-center w-6 h-6 rounded-md"
          style={{ background: `${accent}15`, color: accent }}
        >
          {icon}
        </span>
        <Text
          style={{
            fontSize: 12,
            fontWeight: 500,
            letterSpacing: '0.02em',
            textTransform: 'uppercase',
            color: 'var(--ae-muted)',
          }}
        >
          {label}
        </Text>
      </div>
      <div>
        <div
          style={{
            fontSize: large ? 40 : 28,
            fontWeight: 700,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            color: 'var(--ae-text)',
          }}
        >
          <AnimatedNumber value={value} formatter={formatter} />
        </div>
        {trend && (
          <div className="flex items-center gap-1 mt-2">
            <Tag
              style={{
                margin: 0,
                fontSize: 12,
                fontWeight: 500,
                borderRadius: 4,
                padding: '2px 8px',
                border: 'none',
                background: trend.positive ? 'rgba(111, 155, 124, 0.10)' : 'rgba(196, 122, 110, 0.10)',
                color: trend.positive ? 'var(--ae-success)' : 'var(--ae-danger)',
              }}
            >
              {trend.positive ? '+' : ''}{trend.value}%
            </Tag>
            <Text style={{ fontSize: 12, color: 'var(--ae-muted)' }}>vs last 7d</Text>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ─── Bento Chart Block ───
function ChartBlock({
  title,
  children,
  className = '',
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
      className={`flex flex-col h-full ${className}`}
    >
      <Text
        style={{
          fontSize: 12,
          fontWeight: 500,
          letterSpacing: '0.02em',
          textTransform: 'uppercase',
          color: 'var(--ae-muted)',
          marginBottom: 16,
        }}
      >
        {title}
      </Text>
      <div className="flex-1 min-h-0">{children}</div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [modelCosts, setModelCosts] = useState<ModelCost[]>([]);
  const [agentActivity, setAgentActivity] = useState<AgentActivity[]>([]);
  const [feedback, setFeedback] = useState<FeedbackSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const [totalTokens, setTotalTokens] = useState(0);
  const [totalCost, setTotalCost] = useState(0);
  const [totalConversations, setTotalConversations] = useState(0);

  const fetchDashboardData = useCallback(() => {
    setLoading(true);
    Promise.allSettled([
      api.get('/usage/daily'),
      api.get('/usage/models'),
      api.get('/usage/agents'),
      api.get('/usage/feedback'),
    ]).then(([usageRes, modelRes, agentRes, feedbackRes]) => {
      if (usageRes.status === 'fulfilled') {
        const data = usageRes.value;
        setUsage(data);
        if (data?.tokens) {
          setTotalTokens(data.tokens.reduce((sum: number, t: number) => sum + t, 0));
        }
      }
      if (modelRes.status === 'fulfilled') {
        const models = Array.isArray(modelRes.value) ? modelRes.value : [];
        setModelCosts(models);
        setTotalCost(models.reduce((sum: number, m: ModelCost) => sum + (m.cost || 0), 0));
      }
      if (agentRes.status === 'fulfilled') {
        const agents = Array.isArray(agentRes.value) ? agentRes.value : [];
        setAgentActivity(agents.slice(0, 10));
        setTotalConversations(agents.reduce((sum: number, a: AgentActivity) => sum + (a.conversation_count || 0), 0));
      }
      if (feedbackRes.status === 'fulfilled') {
        setFeedback(feedbackRes.value);
      }
    }).catch(() => {
      message.error('Failed to load dashboard data');
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchDashboardData(); }, [fetchDashboardData]);

  // ─── Chart Options ───
  const usageChartOption = useMemo(() => ({
    tooltip: { trigger: 'axis' as const, backgroundColor: 'var(--ae-panel-strong)', borderColor: 'var(--ae-line)', textStyle: { color: 'var(--ae-text)' } },
    grid: { left: 48, right: 16, top: 8, bottom: 24 },
    xAxis: {
      type: 'category' as const,
      data: usage?.dates || [],
      axisLine: { lineStyle: { color: 'var(--ae-line)' } },
      axisLabel: { color: 'var(--ae-muted)', fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value' as const,
      splitLine: { lineStyle: { color: 'var(--ae-line)', type: 'dashed' as const } },
      axisLabel: { color: 'var(--ae-muted)', fontSize: 11, formatter: (val: number) => val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val },
    },
    series: [{
      name: 'Tokens',
      type: 'line',
      data: usage?.tokens || [],
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: 'var(--ae-accent-gold)' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(217, 119, 6, 0.2)' },
            { offset: 1, color: 'rgba(217, 119, 6, 0)' },
          ],
        },
      },
    }],
  }), [usage]);

  const costChartOption = useMemo(() => ({
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: 'var(--ae-panel-strong)',
      borderColor: 'var(--ae-line)',
      textStyle: { color: 'var(--ae-text)' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        return `${p.name}: $${p.value.toFixed(4)}`;
      },
    },
    grid: { left: 56, right: 16, top: 8, bottom: 32 },
    xAxis: {
      type: 'category' as const,
      data: modelCosts.map((m) => m.model),
      axisLine: { lineStyle: { color: 'var(--ae-line)' } },
      axisLabel: { color: 'var(--ae-muted)', fontSize: 11, rotate: 15 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value' as const,
      splitLine: { lineStyle: { color: 'var(--ae-line)', type: 'dashed' as const } },
      axisLabel: { color: 'var(--ae-muted)', fontSize: 11, formatter: '${value}' },
    },
    series: [{
      name: 'Cost',
      type: 'bar',
      data: modelCosts.map((m) => m.cost),
      barMaxWidth: 40,
      itemStyle: {
        color: 'var(--ae-accent-olive)',
        borderRadius: [4, 4, 0, 0],
      },
    }],
  }), [modelCosts]);

  const agentChartOption = useMemo(() => ({
    tooltip: { trigger: 'axis' as const, backgroundColor: 'var(--ae-panel-strong)', borderColor: 'var(--ae-line)', textStyle: { color: 'var(--ae-text)' } },
    grid: { left: 120, right: 24, top: 8, bottom: 16 },
    xAxis: {
      type: 'value' as const,
      splitLine: { lineStyle: { color: 'var(--ae-line)', type: 'dashed' as const } },
      axisLabel: { color: 'var(--ae-muted)', fontSize: 11 },
    },
    yAxis: {
      type: 'category' as const,
      data: agentActivity.map((a) => a.agent_name).reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: 'var(--ae-muted)', fontSize: 11, width: 100, overflow: 'truncate' },
    },
    series: [{
      name: 'Conversations',
      type: 'bar',
      data: agentActivity.map((a) => a.conversation_count).reverse(),
      barMaxWidth: 24,
      itemStyle: {
        color: 'var(--ae-success)',
        borderRadius: [0, 4, 4, 0],
      },
    }],
  }), [agentActivity]);

  const feedbackChartOption = useMemo(() => ({
    tooltip: { trigger: 'item' as const, backgroundColor: 'var(--ae-panel-strong)', borderColor: 'var(--ae-line)', textStyle: { color: 'var(--ae-text)' } },
    legend: { bottom: 0, left: 'center', textStyle: { color: 'var(--ae-muted)', fontSize: 11 } },
    series: [{
      name: 'Feedback',
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: 'var(--ae-panel-strong)', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' as const, color: 'var(--ae-text)' },
      },
      data: [
        { name: 'Positive', value: feedback?.positive || 0, itemStyle: { color: 'var(--ae-success)' } },
        { name: 'Negative', value: feedback?.negative || 0, itemStyle: { color: 'var(--ae-danger)' } },
      ],
    }],
  }), [feedback]);

  if (loading) {
    return (
      <div className="space-y-4">
        {/* Header skeleton */}
        <div className="mb-8">
          <div className="h-8 w-48 rounded-md bg-stone-01 animate-pulse mb-2" />
          <div className="h-4 w-64 rounded-md bg-stone-01 animate-pulse" />
        </div>
        {/* Metric skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div className="lg:col-span-2 h-36 rounded-lg bg-stone-01 animate-pulse" />
          <div className="h-36 rounded-lg bg-stone-01 animate-pulse" />
          <div className="h-36 rounded-lg bg-stone-01 animate-pulse" />
        </div>
        {/* Chart skeletons */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <div className="h-80 rounded-lg bg-stone-01 animate-pulse" />
          <div className="h-80 rounded-lg bg-stone-01 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 h-72 rounded-lg bg-stone-01 animate-pulse" />
          <div className="h-72 rounded-lg bg-stone-01 animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.25, 1, 0.5, 1] }}
        className="mb-8"
      >
        <Title
          level={2}
          style={{
            margin: 0,
            fontSize: 28,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            color: 'var(--ae-text)',
            fontFamily: 'var(--ae-font-family-serif)',
          }}
        >
          Dashboard
        </Title>
        <Text style={{ color: 'var(--ae-muted)', fontSize: 14 }}>
          Platform overview and key metrics
        </Text>
      </motion.div>

      {/* ── Bento Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {/* Large metric: Total Tokens */}
        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24, height: '100%' }}
          className="lg:col-span-2"
        >
          <MetricBlock
            label="Total Tokens Used"
            value={totalTokens}
            formatter={(val) => val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toLocaleString()}
            icon={<ThunderboltOutlined />}
            accent="var(--ae-accent-gold)"
            trend={{ value: 12.5, positive: true }}
            large
          />
        </Card>

        {/* Metric: Cost */}
        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24, height: '100%' }}
        >
          <MetricBlock
            label="Estimated Cost"
            value={Math.round(totalCost * 100)}
            formatter={(val) => `$${(val / 100).toFixed(2)}`}
            icon={<DollarOutlined />}
            accent="var(--ae-accent-olive)"
          />
        </Card>

        {/* Metric: Conversations */}
        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24, height: '100%' }}
        >
          <MetricBlock
            label="Conversations"
            value={totalConversations}
            icon={<MessageOutlined />}
            accent="var(--ae-success)"
            trend={{ value: 8.3, positive: true }}
          />
        </Card>
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24 }}
        >
          <ChartBlock title="Usage Trend (Daily Tokens)">
            {usage?.dates?.length ? (
              <ReactECharts option={usageChartOption} style={{ height: 280 }} />
            ) : (
              <EmptyChartPlaceholder message="No usage data available" />
            )}
          </ChartBlock>
        </Card>

        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24 }}
        >
          <ChartBlock title="Cost by Model">
            {modelCosts.length > 0 ? (
              <ReactECharts option={costChartOption} style={{ height: 280 }} />
            ) : (
              <EmptyChartPlaceholder message="No cost data available" />
            )}
          </ChartBlock>
        </Card>
      </div>

      {/* ── Bottom Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24 }}
          className="lg:col-span-2"
        >
          <ChartBlock title="Top Agents Ranking">
            {agentActivity.length > 0 ? (
              <ReactECharts option={agentChartOption} style={{ height: 260 }} />
            ) : (
              <EmptyChartPlaceholder message="No agent activity data available" />
            )}
          </ChartBlock>
        </Card>

        <Card
          bordered={false}
          style={{
            background: 'var(--ae-panel-strong)',
            border: '1px solid var(--ae-line)',
            borderRadius: 'var(--ae-radius-lg)',
          }}
          bodyStyle={{ padding: 24 }}
        >
          <ChartBlock title="Feedback Summary">
            {feedback && (feedback.positive > 0 || feedback.negative > 0) ? (
              <ReactECharts option={feedbackChartOption} style={{ height: 260 }} />
            ) : (
              <EmptyChartPlaceholder message="No feedback data available" />
            )}
          </ChartBlock>
        </Card>
      </div>
    </div>
  );
}

function EmptyChartPlaceholder({ message }: { message: string }) {
  return (
    <div
      style={{
        height: 280,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--ae-muted)',
        fontSize: 14,
      }}
    >
      <ClockCircleOutlined style={{ marginRight: 8 }} />
      {message}
    </div>
  );
}
