'use client';
import React, { useState, Suspense, useEffect } from 'react';
import { Card, Form, Input, Button, Typography, message, Divider, Space } from 'antd';
import { UserOutlined, LockOutlined, GithubOutlined, GoogleOutlined, WechatOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';

const { Title, Text } = Typography;

interface SSOProvider {
  id: string;
  provider_name: string;
  enabled: boolean;
}

function LoginForm() {
  const [loading, setLoading] = useState(false);
  const [ssoProviders, setSsoProviders] = useState<SSOProvider[]>([]);
  const { login } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Load SSO providers
    api.get('/auth/sso/providers').then(setSsoProviders).catch(() => {});
  }, []);

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

  const handleSSO = async (providerName: string) => {
    try {
      if (providerName === 'wecom') {
        const data = await api.get('/auth/wecom/login');
        if (data.url) {
          window.location.href = data.url;
        }
      } else if (providerName === 'github' || providerName === 'google') {
        // Standard OAuth2 flow — redirect to backend
        window.location.href = `/api/v1/auth/${providerName}/login`;
      }
    } catch {
      message.error('SSO login failed');
    }
  };

  const enabledProviders = ssoProviders.filter(p => p.enabled);
  const hasSSO = enabledProviders.length > 0;

  const getProviderIcon = (name: string) => {
    if (name === 'github') return <GithubOutlined />;
    if (name === 'google') return <GoogleOutlined />;
    if (name === 'wecom') return <WechatOutlined />;
    return null;
  };

  const getProviderLabel = (name: string) => {
    const labels: Record<string, string> = {
      github: 'GitHub',
      google: 'Google',
      wecom: '企业微信',
    };
    return labels[name] || name;
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

      {/* SSO Buttons */}
      {hasSSO && (
        <>
          <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
            {enabledProviders.map(p => (
              <Button
                key={p.id}
                block
                size="large"
                icon={getProviderIcon(p.provider_name)}
                onClick={() => handleSSO(p.provider_name)}
                style={{ borderRadius: 6, textAlign: 'left' }}
              >
                Sign in with {getProviderLabel(p.provider_name)}
              </Button>
            ))}
          </Space>
          <Divider style={{ margin: '16px 0' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>or</Text>
          </Divider>
        </>
      )}

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
