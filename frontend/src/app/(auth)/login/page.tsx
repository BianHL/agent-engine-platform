'use client';
import React, { useState, Suspense } from 'react';
import { Card, Form, Input, Button, Typography, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/auth';
import { useRouter, useSearchParams } from 'next/navigation';

const { Title } = Typography;

function LoginForm() {
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('Login successful');
      const redirect = searchParams.get('redirect') || '/agents';
      router.push(redirect);
    } catch {
      message.error('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      style={{
        width: 400,
        borderRadius: 12,
        border: '1px solid var(--ae-line)',
        boxShadow: 'var(--ae-shadow-ambient-medium)',
      }}
    >
      <div className="flex items-center justify-center gap-3 mb-8">
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            background: 'var(--ae-accent-gold)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'rgba(255,255,255,0.95)',
            fontSize: 16,
            fontWeight: 700,
          }}
        >
          AE
        </div>
        <Title
          level={3}
          style={{
            margin: 0,
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: '-0.01em',
            color: 'var(--ae-text)',
          }}
        >
          Agent Engine
        </Title>
      </div>
      <Form onFinish={onFinish}>
        <Form.Item
          name="username"
          rules={[{ required: true, message: 'Please input username' }]}
        >
          <Input
            prefix={<UserOutlined style={{ color: 'var(--ae-muted)' }} />}
            placeholder="Username"
            size="large"
            style={{ borderRadius: 6 }}
          />
        </Form.Item>
        <Form.Item
          name="password"
          rules={[{ required: true, message: 'Please input password' }]}
        >
          <Input.Password
            prefix={<LockOutlined style={{ color: 'var(--ae-muted)' }} />}
            placeholder="Password"
            size="large"
            style={{ borderRadius: 6 }}
          />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0 }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            size="large"
            style={{
              background: 'var(--ae-accent-gold)',
              borderColor: 'var(--ae-accent-gold)',
              borderRadius: 6,
              fontWeight: 500,
            }}
          >
            Login
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(255,255,255,0.5)',
      }}
    >
      <Suspense fallback={
        <Card style={{ width: 400, borderRadius: 12 }}>
          <div className="flex items-center justify-center gap-3 mb-8">
            <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--ae-accent-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.95)', fontSize: 16, fontWeight: 700 }}>AE</div>
            <Title level={3} style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Agent Engine</Title>
          </div>
          <div className="space-y-4">
            <div className="h-10 rounded-md bg-stone-01 animate-pulse" />
            <div className="h-10 rounded-md bg-stone-01 animate-pulse" />
            <div className="h-11 rounded-md bg-stone-01 animate-pulse" />
          </div>
        </Card>
      }>
        <LoginForm />
      </Suspense>
    </div>
  );
}
